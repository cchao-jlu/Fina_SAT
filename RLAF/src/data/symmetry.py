from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations, product
import json
import random
from pathlib import Path
from typing import Sequence


SAT = "SATISFIABLE"
UNSAT = "UNSATISFIABLE"
UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class SymmetryCNF:
    family: str
    instance_id: str
    clauses: list[list[int]]
    num_vars: int
    expected_result: str = UNKNOWN
    variable_orbits: dict[int, str] = field(default_factory=dict)
    metadata: dict[str, object] = field(default_factory=dict)


def infer_num_vars(clauses: Sequence[Sequence[int]]) -> int:
    return max((abs(lit) for clause in clauses for lit in clause), default=0)


def normalize_clauses(clauses: Sequence[Sequence[int]]) -> list[list[int]]:
    normalized: list[list[int]] = []
    for clause in clauses:
        cleaned = [int(lit) for lit in clause if int(lit) != 0]
        if not cleaned:
            raise ValueError("Empty clauses are not supported by this generator.")
        normalized.append(cleaned)
    return normalized


def write_dimacs(path: Path, clauses: Sequence[Sequence[int]], num_vars: int | None = None) -> None:
    clauses = normalize_clauses(clauses)
    num_vars = infer_num_vars(clauses) if num_vars is None else int(num_vars)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        handle.write(f"p cnf {num_vars} {len(clauses)}\n")
        for clause in clauses:
            handle.write(" ".join(str(lit) for lit in clause))
            handle.write(" 0\n")


def write_orbits_json(path: Path, variable_orbits: dict[int, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {str(int(var)): str(orbit) for var, orbit in sorted(variable_orbits.items())}
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_orbits_json(path: Path, num_vars: int | None = None) -> dict[int, str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    orbits = {int(var): str(orbit) for var, orbit in payload.items()}
    if num_vars is not None:
        for var in range(1, int(num_vars) + 1):
            orbits.setdefault(var, f"singleton:{var}")
    return orbits


def orbit_validity(orbit: object, orbit_size: int, min_orbit_size: int = 2) -> tuple[bool, str]:
    orbit_label = str(orbit)
    if orbit_label.startswith("singleton:"):
        return False, "singleton_label"
    if int(orbit_size) < int(min_orbit_size):
        return False, "orbit_size_below_min"
    return True, "valid"


def random_variable_permutation(num_vars: int, rng: random.Random) -> list[int]:
    target_vars = list(range(1, int(num_vars) + 1))
    rng.shuffle(target_vars)
    return [0, *target_vars]


def random_sign_flips(num_vars: int, rng: random.Random, flip_probability: float = 0.5) -> list[int]:
    return [
        1,
        *[
            -1 if rng.random() < float(flip_probability) else 1
            for _ in range(int(num_vars))
        ],
    ]


def permute_cnf(
    clauses: Sequence[Sequence[int]],
    permutation: Sequence[int],
    sign_flips: Sequence[int] | None = None,
) -> list[list[int]]:
    sign_flips = sign_flips or [1] * len(permutation)
    transformed: list[list[int]] = []
    for clause in clauses:
        new_clause = []
        for lit in clause:
            old_var = abs(int(lit))
            if old_var <= 0 or old_var >= len(permutation):
                raise ValueError(f"Literal {lit} is outside permutation domain.")
            sign = 1 if lit > 0 else -1
            sign *= int(sign_flips[old_var])
            new_clause.append(sign * int(permutation[old_var]))
        transformed.append(new_clause)
    return transformed


def transform_orbits(variable_orbits: dict[int, str], permutation: Sequence[int]) -> dict[int, str]:
    return {
        int(permutation[int(old_var)]): str(orbit)
        for old_var, orbit in variable_orbits.items()
    }


def _orbit_labels_from_groups(groups: Sequence[Sequence[int]], prefix: str) -> dict[int, str]:
    labels: dict[int, str] = {}
    ordered_groups = sorted(
        (sorted(int(var) for var in group) for group in groups),
        key=lambda group: (group[0] if group else 0, len(group)),
    )
    for group_index, group in enumerate(ordered_groups, start=1):
        label = f"{prefix}_o{group_index:02d}_size{len(group)}"
        for var in group:
            labels[int(var)] = label
    return labels


def _orbits_from_variable_maps(
    variables: Sequence[int],
    maps: Sequence[dict[int, int]],
    prefix: str,
) -> dict[int, str]:
    variables = [int(var) for var in variables]
    parent = {var: var for var in variables}

    def find(var: int) -> int:
        while parent[var] != var:
            parent[var] = parent[parent[var]]
            var = parent[var]
        return var

    def union(left: int, right: int) -> None:
        left_root = find(int(left))
        right_root = find(int(right))
        if left_root == right_root:
            return
        if left_root > right_root:
            left_root, right_root = right_root, left_root
        parent[right_root] = left_root

    variable_set = set(variables)
    for mapping in maps:
        for source, target in mapping.items():
            if int(source) in variable_set and int(target) in variable_set:
                union(int(source), int(target))

    groups: dict[int, list[int]] = {}
    for var in variables:
        groups.setdefault(find(var), []).append(var)
    return _orbit_labels_from_groups(list(groups.values()), prefix=prefix)


def wl_refined_variable_orbits(
    clauses: Sequence[Sequence[int]],
    num_vars: int,
    base_orbits: dict[int, str],
    prefix: str,
    rounds: int = 4,
) -> dict[int, str]:
    """Lightweight CNF-incidence WL refinement used only for stress labels."""
    colors: dict[tuple[str, int], object] = {
        ("v", var): ("var", str(base_orbits.get(var, f"singleton:{var}")))
        for var in range(1, int(num_vars) + 1)
    }
    adjacency: dict[tuple[str, int], list[tuple[tuple[str, int], str]]] = {
        ("v", var): []
        for var in range(1, int(num_vars) + 1)
    }
    for clause_index, clause in enumerate(normalize_clauses(clauses)):
        node = ("c", clause_index)
        positive = sum(1 for lit in clause if int(lit) > 0)
        negative = len(clause) - positive
        colors[node] = ("clause", len(clause), positive, negative)
        adjacency[node] = []
        for lit in clause:
            var_node = ("v", abs(int(lit)))
            sign = "+" if int(lit) > 0 else "-"
            adjacency[var_node].append((node, sign))
            adjacency[node].append((var_node, sign))

    for _ in range(int(rounds)):
        keys = {
            node: (
                colors[node],
                tuple(sorted((edge_color, colors[neighbor]) for neighbor, edge_color in adjacency[node])),
            )
            for node in colors
        }
        palette = {
            key: index
            for index, key in enumerate(sorted(set(keys.values()), key=repr))
        }
        colors = {node: palette[keys[node]] for node in colors}

    groups: dict[object, list[int]] = {}
    for var in range(1, int(num_vars) + 1):
        groups.setdefault(colors[("v", var)], []).append(var)
    return _orbit_labels_from_groups(list(groups.values()), prefix=prefix)


def renamed_variant(
    instance: SymmetryCNF,
    seed: int,
    include_sign_flips: bool = False,
    flip_probability: float = 0.5,
) -> SymmetryCNF:
    rng = random.Random(int(seed))
    permutation = random_variable_permutation(instance.num_vars, rng)
    sign_flips = (
        random_sign_flips(instance.num_vars, rng, flip_probability=flip_probability)
        if include_sign_flips
        else [1] * (instance.num_vars + 1)
    )
    suffix = f"perm{seed}"
    if include_sign_flips:
        suffix += "_signed"
    metadata = dict(instance.metadata)
    metadata.update(
        {
            "base_instance_id": instance.instance_id,
            "transform_seed": int(seed),
            "include_sign_flips": bool(include_sign_flips),
            "permutation": permutation[1:],
            "sign_flips": sign_flips[1:],
        }
    )
    return SymmetryCNF(
        family=instance.family,
        instance_id=f"{instance.instance_id}_{suffix}",
        clauses=permute_cnf(instance.clauses, permutation=permutation, sign_flips=sign_flips),
        num_vars=instance.num_vars,
        expected_result=instance.expected_result,
        variable_orbits=transform_orbits(instance.variable_orbits, permutation=permutation),
        metadata=metadata,
    )


def at_most_k_clauses(variables: Sequence[int], k: int) -> list[list[int]]:
    variables = [int(var) for var in variables]
    k = int(k)
    if k < 0:
        return [[]]
    if k >= len(variables):
        return []
    return [[-var for var in subset] for subset in combinations(variables, k + 1)]


def at_least_k_clauses(variables: Sequence[int], k: int) -> list[list[int]]:
    variables = [int(var) for var in variables]
    k = int(k)
    if k <= 0:
        return []
    if k > len(variables):
        return [[]]
    forbid_false_count = len(variables) - k + 1
    return [[var for var in subset] for subset in combinations(variables, forbid_false_count)]


def exactly_k_clauses(variables: Sequence[int], k: int) -> list[list[int]]:
    return [*at_most_k_clauses(variables, k), *at_least_k_clauses(variables, k)]


def pigeonhole_cnf(pigeons: int, holes: int, functional: bool = True) -> SymmetryCNF:
    if pigeons <= 0 or holes <= 0:
        raise ValueError("pigeons and holes must be positive.")

    def var_id(pigeon: int, hole: int) -> int:
        return pigeon * holes + hole + 1

    clauses: list[list[int]] = []
    for pigeon in range(pigeons):
        clauses.append([var_id(pigeon, hole) for hole in range(holes)])
        if functional:
            for left, right in combinations(range(holes), 2):
                clauses.append([-var_id(pigeon, left), -var_id(pigeon, right)])
    for hole in range(holes):
        for left, right in combinations(range(pigeons), 2):
            clauses.append([-var_id(left, hole), -var_id(right, hole)])

    num_vars = pigeons * holes
    return SymmetryCNF(
        family="php",
        instance_id=f"php_p{pigeons}_h{holes}",
        clauses=clauses,
        num_vars=num_vars,
        expected_result=UNSAT if pigeons > holes else SAT,
        variable_orbits={var: "pigeon_hole_assignment" for var in range(1, num_vars + 1)},
        metadata={"pigeons": pigeons, "holes": holes, "functional": bool(functional)},
    )


def pigeonhole_with_emergency_exit_cnf(
    pigeons: int,
    holes: int,
    exit_mode: str = "all",
) -> SymmetryCNF:
    if exit_mode not in {"single", "all"}:
        raise ValueError("exit_mode must be either 'single' or 'all'.")

    def hole_var(pigeon: int, hole: int) -> int:
        return pigeon * holes + hole + 1

    base_var_count = pigeons * holes
    exit_vars = {}
    if exit_mode == "single":
        exit_vars[0] = base_var_count + 1
    else:
        for pigeon in range(pigeons):
            exit_vars[pigeon] = base_var_count + pigeon + 1

    clauses: list[list[int]] = []
    for pigeon in range(pigeons):
        pigeon_clause = [hole_var(pigeon, hole) for hole in range(holes)]
        if pigeon in exit_vars:
            pigeon_clause.append(exit_vars[pigeon])
        clauses.append(pigeon_clause)
        for left, right in combinations(range(holes), 2):
            clauses.append([-hole_var(pigeon, left), -hole_var(pigeon, right)])

    for hole in range(holes):
        for left, right in combinations(range(pigeons), 2):
            clauses.append([-hole_var(left, hole), -hole_var(right, hole)])

    if exit_mode == "all":
        clauses.extend(at_most_k_clauses(list(exit_vars.values()), 1))

    num_vars = base_var_count + len(exit_vars)
    orbits = {}
    for pigeon in range(pigeons):
        label = (
            "exit_pigeon_assignment"
            if exit_mode == "single" and pigeon in exit_vars
            else "regular_pigeon_assignment"
        )
        if exit_mode == "all":
            label = "pigeon_hole_assignment"
        for hole in range(holes):
            orbits[hole_var(pigeon, hole)] = label
    for var in exit_vars.values():
        orbits[var] = "emergency_exit"
    return SymmetryCNF(
        family=f"php_exit_{exit_mode}",
        instance_id=f"php_exit_{exit_mode}_p{pigeons}_h{holes}",
        clauses=clauses,
        num_vars=num_vars,
        expected_result=SAT,
        variable_orbits=orbits,
        metadata={"pigeons": pigeons, "holes": holes, "exit_mode": exit_mode},
    )


def subset_cardinality_fixed_bandwidth_cnf(size: int = 8) -> SymmetryCNF:
    if size < 5:
        raise ValueError("subset cardinality stress instances require size >= 5.")
    positions: set[tuple[int, int]] = set()
    for row in range(size):
        for offset in (-2, 0, 2, 4):
            positions.add((row, (row + offset) % size))
    positions.add((0, size - 1))
    ordered = sorted(positions)
    var_by_pos = {pos: idx + 1 for idx, pos in enumerate(ordered)}

    clauses: list[list[int]] = []
    row_orbits = {}
    for row in range(size):
        variables = [var_by_pos[(row, col)] for col in range(size) if (row, col) in var_by_pos]
        clauses.extend(at_least_k_clauses(variables, (len(variables) + 1) // 2))
        for var in variables:
            row_orbits[var] = "exception_row" if row == 0 else "regular_row"
    for col in range(size):
        variables = [var_by_pos[(row, col)] for row in range(size) if (row, col) in var_by_pos]
        clauses.extend(at_most_k_clauses(variables, len(variables) // 2))

    return SymmetryCNF(
        family="subset_cardinality",
        instance_id=f"subset_cardinality_bw{size}",
        clauses=clauses,
        num_vars=len(ordered),
        expected_result=UNSAT,
        variable_orbits=wl_refined_variable_orbits(
            clauses,
            num_vars=len(ordered),
            base_orbits=row_orbits,
            prefix="subset_cardinality_refined",
        ),
        metadata={
            "size": int(size),
            "matrix": "fixed_bandwidth_plus_corner",
            "orbit_refinement": "cnf_incidence_wl4_from_row_labels",
        },
    )


def torus_grid_edges(rows: int, cols: int, split_one_edge: bool = False) -> tuple[int, list[tuple[int, int]]]:
    if rows <= 0 or cols <= 0:
        raise ValueError("rows and cols must be positive.")
    edges = set()

    def vid(row: int, col: int) -> int:
        return row * cols + col

    for row in range(rows):
        for col in range(cols):
            current = vid(row, col)
            edges.add(tuple(sorted((current, vid(row, (col + 1) % cols)))))
            edges.add(tuple(sorted((current, vid((row + 1) % rows, col)))))
    edge_list = sorted(edges)
    vertex_count = rows * cols
    if split_one_edge:
        first = edge_list.pop(0)
        split_vertex = vertex_count
        vertex_count += 1
        edge_list.append(tuple(sorted((first[0], split_vertex))))
        edge_list.append(tuple(sorted((split_vertex, first[1]))))
        edge_list = sorted(edge_list)
    return vertex_count, edge_list


def even_colouring_torus_cnf(rows: int = 4, cols: int = 5) -> SymmetryCNF:
    vertex_count, edges = torus_grid_edges(rows, cols, split_one_edge=True)
    edge_var = {edge: idx + 1 for idx, edge in enumerate(edges)}
    clauses: list[list[int]] = []
    for vertex in range(vertex_count):
        incident = [var for edge, var in edge_var.items() if vertex in edge]
        clauses.extend(parity_constraint_clauses(incident, rhs=0))
    split_vertex = vertex_count - 1
    vertex_identity = {vertex: vertex for vertex in range(vertex_count)}
    horizontal_reflection = {}
    vertical_reflection = {}
    half_turn = {}

    def old_vertex(row: int, col: int) -> int:
        return row * cols + col

    for row in range(rows):
        for col in range(cols):
            source = old_vertex(row, col)
            horizontal_reflection[source] = old_vertex(row, (1 - col) % cols)
            vertical_reflection[source] = old_vertex((-row) % rows, col)
            half_turn[source] = old_vertex((-row) % rows, (1 - col) % cols)
    horizontal_reflection[split_vertex] = split_vertex
    vertical_reflection[split_vertex] = split_vertex
    half_turn[split_vertex] = split_vertex

    vertex_maps = [vertex_identity, horizontal_reflection, vertical_reflection, half_turn]
    edge_maps = []
    for vertex_map in vertex_maps:
        mapped_edges = {}
        for edge, var in edge_var.items():
            mapped_edge = tuple(sorted((vertex_map[edge[0]], vertex_map[edge[1]])))
            mapped_edges[var] = edge_var[mapped_edge]
        edge_maps.append(mapped_edges)
    orbits = _orbits_from_variable_maps(
        list(edge_var.values()),
        maps=edge_maps,
        prefix="even_colouring_refined",
    )
    return SymmetryCNF(
        family="even_colouring",
        instance_id=f"even_colouring_torus_{rows}x{cols}_split",
        clauses=clauses,
        num_vars=len(edges),
        expected_result=SAT,
        variable_orbits=orbits,
        metadata={
            "rows": int(rows),
            "cols": int(cols),
            "graph": "split_torus_grid",
            "orbit_refinement": "split_edge_stabilizer_vertex_automorphisms",
        },
    )


def complete_graph_coloring_cnf(vertices: int, colors: int) -> SymmetryCNF:
    if vertices <= 0 or colors <= 0:
        raise ValueError("vertices and colors must be positive.")

    def var_id(vertex: int, color: int) -> int:
        return vertex * colors + color + 1

    clauses: list[list[int]] = []
    for vertex in range(vertices):
        clauses.append([var_id(vertex, color) for color in range(colors)])
        for left, right in combinations(range(colors), 2):
            clauses.append([-var_id(vertex, left), -var_id(vertex, right)])
    for u, v in combinations(range(vertices), 2):
        for color in range(colors):
            clauses.append([-var_id(u, color), -var_id(v, color)])

    num_vars = vertices * colors
    return SymmetryCNF(
        family="complete_coloring",
        instance_id=f"k{vertices}_color{colors}",
        clauses=clauses,
        num_vars=num_vars,
        expected_result=SAT if vertices <= colors else UNSAT,
        variable_orbits={var: "vertex_color_assignment" for var in range(1, num_vars + 1)},
        metadata={"vertices": vertices, "colors": colors},
    )


def vertex_cover_torus_cnf(
    rows: int = 4,
    cols: int = 5,
    version: str = "norat",
    cover_size: int | None = None,
) -> SymmetryCNF:
    if version not in {"hard", "easy", "norat", "norat_even", "event"}:
        raise ValueError("Unknown vertex-cover version.")
    vertex_count, edges = torus_grid_edges(rows, cols, split_one_edge=False)
    explicit_cover_size = cover_size is not None
    if cover_size is None:
        if version == "hard":
            cover_size = rows * ((cols + 1) // 2) - 1
        elif version == "easy":
            cover_size = (rows * cols) // 2
        else:
            cover_size = rows * (cols // 2) - 1
    else:
        cover_size = int(cover_size)
    if cover_size < 0 or cover_size >= vertex_count:
        raise ValueError("cover_size must be in [0, rows * cols).")
    variables = list(range(1, vertex_count + 1))
    clauses = [[u + 1, v + 1] for u, v in edges]
    clauses.extend(at_most_k_clauses(variables, cover_size))
    suffix = f"k{cover_size}_{version}" if explicit_cover_size else version
    return SymmetryCNF(
        family="vertex_cover_torus",
        instance_id=f"vertex_cover_torus_{rows}x{cols}_{suffix}",
        clauses=clauses,
        num_vars=vertex_count,
        expected_result=UNSAT,
        variable_orbits={var: "torus_vertex" for var in variables},
        metadata={"rows": int(rows), "cols": int(cols), "version": version, "cover_size": int(cover_size)},
    )


def vertex_cover_torus_ladder_instances() -> list[SymmetryCNF]:
    return [
        vertex_cover_torus_cnf(3, 4, version="event", cover_size=4),
        vertex_cover_torus_cnf(3, 4, version="event", cover_size=5),
        vertex_cover_torus_cnf(3, 5, version="event", cover_size=5),
        vertex_cover_torus_cnf(3, 5, version="event", cover_size=6),
        vertex_cover_torus_cnf(4, 5, version="norat"),
    ]


def brick_wall_hex_edges(rows: int, cols: int) -> tuple[int, list[tuple[int, int]]]:
    if rows <= 0 or cols <= 0:
        raise ValueError("rows and cols must be positive.")

    def vid(row: int, col: int) -> int:
        return row * cols + col

    edges = set()
    for row in range(rows):
        for col in range(cols):
            current = vid(row, col)
            if col + 1 < cols:
                edges.add(tuple(sorted((current, vid(row, col + 1)))))
            if row + 1 < rows:
                down_col = col if row % 2 == 0 else col - 1
                if 0 <= down_col < cols:
                    edges.add(tuple(sorted((current, vid(row + 1, down_col)))))
                alt_col = col + 1 if row % 2 == 0 else col
                if 0 <= alt_col < cols:
                    edges.add(tuple(sorted((current, vid(row + 1, alt_col)))))
    return rows * cols, sorted(edges)


def dominating_set_hex_cnf(rows: int = 4, cols: int = 7) -> SymmetryCNF:
    vertex_count, edges = brick_wall_hex_edges(rows, cols)
    neighbors = {vertex: set() for vertex in range(vertex_count)}
    for u, v in edges:
        neighbors[u].add(v)
        neighbors[v].add(u)
    variables = list(range(1, vertex_count + 1))
    clauses = []
    for vertex in range(vertex_count):
        closed = [vertex + 1, *[neighbor + 1 for neighbor in sorted(neighbors[vertex])]]
        clauses.append(closed)
    dominate_size = vertex_count // 4
    clauses.extend(at_most_k_clauses(variables, dominate_size))
    if rows % 2 == 1:
        reverse_map = {
            row * cols + col + 1: (rows - 1 - row) * cols + col + 1
            for row in range(rows)
            for col in range(cols)
        }
        orbit_refinement = "brick_wall_row_reflection"
    else:
        reverse_map = {
            row * cols + col + 1: (rows - 1 - row) * cols + (cols - 1 - col) + 1
            for row in range(rows)
            for col in range(cols)
        }
        orbit_refinement = "brick_wall_180_degree_rotation"
    return SymmetryCNF(
        family="dominating_set_hex",
        instance_id=f"dominating_set_hex_{rows}x{cols}_s{dominate_size}",
        clauses=clauses,
        num_vars=vertex_count,
        expected_result=UNKNOWN,
        variable_orbits=_orbits_from_variable_maps(
            variables,
            maps=[{var: var for var in variables}, reverse_map],
            prefix="dominating_set_hex_refined",
        ),
        metadata={
            "rows": int(rows),
            "cols": int(cols),
            "dominate_size": int(dominate_size),
            "orbit_refinement": orbit_refinement,
        },
    )


def dominating_set_hex_ladder_instances() -> list[SymmetryCNF]:
    return [
        dominating_set_hex_cnf(3, 5),
        dominating_set_hex_cnf(3, 6),
        dominating_set_hex_cnf(4, 5),
    ]


def parity_constraint_clauses(variables: Sequence[int], rhs: int) -> list[list[int]]:
    variables = [int(var) for var in variables]
    rhs = int(rhs) & 1
    clauses: list[list[int]] = []
    for assignment in product([0, 1], repeat=len(variables)):
        if sum(assignment) % 2 == rhs:
            continue
        clauses.append([
            -var if bit else var
            for var, bit in zip(variables, assignment)
        ])
    return clauses


def complete_graph_tseitin_cnf(vertices: int, odd_charge: bool = False) -> SymmetryCNF:
    if vertices < 3:
        raise ValueError("Tseitin complete graph requires at least three vertices.")
    edges = list(combinations(range(vertices), 2))
    edge_var = {edge: idx + 1 for idx, edge in enumerate(edges)}
    charges = [0] * vertices
    if odd_charge:
        charges[0] = 1

    clauses: list[list[int]] = []
    for vertex in range(vertices):
        incident = [
            var
            for (u, v), var in edge_var.items()
            if u == vertex or v == vertex
        ]
        clauses.extend(parity_constraint_clauses(incident, rhs=charges[vertex]))

    if odd_charge:
        orbits = {}
        for (u, v), var in edge_var.items():
            orbit = "incident_to_charged_vertex" if 0 in {u, v} else "away_from_charged_vertex"
            orbits[var] = orbit
    else:
        orbits = {var: "edge_variable" for var in edge_var.values()}

    return SymmetryCNF(
        family="tseitin_complete",
        instance_id=f"tseitin_k{vertices}_{'odd' if odd_charge else 'even'}",
        clauses=clauses,
        num_vars=len(edges),
        expected_result=UNSAT if odd_charge else SAT,
        variable_orbits=orbits,
        metadata={"vertices": vertices, "odd_charge": bool(odd_charge)},
    )


def random_3sat_control_cnf(num_vars: int, num_clauses: int, seed: int) -> SymmetryCNF:
    if num_vars < 3:
        raise ValueError("random 3-SAT controls require at least three variables.")
    if num_clauses <= 0:
        raise ValueError("random 3-SAT controls require at least one clause.")
    rng = random.Random(int(seed))
    variables = list(range(1, int(num_vars) + 1))
    for _ in range(100):
        clauses: set[tuple[int, int, int]] = set()
        while len(clauses) < int(num_clauses):
            selected = rng.sample(variables, 3)
            lits = [
                var if rng.random() < 0.5 else -var
                for var in selected
            ]
            clauses.add(tuple(sorted(lits, key=lambda lit: (abs(lit), lit < 0))))
        seen = {abs(lit) for clause in clauses for lit in clause}
        if seen == set(variables):
            break
    else:
        raise RuntimeError("Failed to generate a random 3-SAT control covering all variables.")
    ordered_clauses = [list(clause) for clause in sorted(clauses)]
    return SymmetryCNF(
        family="random_3sat_control",
        instance_id=f"random_3sat_control_v{num_vars}_c{num_clauses}_seed{seed}",
        clauses=ordered_clauses,
        num_vars=int(num_vars),
        expected_result=UNKNOWN,
        variable_orbits={var: f"singleton:{var}" for var in variables},
        metadata={
            "num_vars": int(num_vars),
            "num_clauses": int(num_clauses),
            "seed": int(seed),
            "control": "random_3sat",
            "symmetry_strength": "none",
        },
    )


def random_3sat_control_instances() -> list[SymmetryCNF]:
    return [
        random_3sat_control_cnf(20, 85, seed=1901),
        random_3sat_control_cnf(30, 128, seed=1902),
        random_3sat_control_cnf(40, 170, seed=1903),
    ]


def default_symmetry_instances() -> list[SymmetryCNF]:
    return [
        pigeonhole_cnf(4, 3),
        pigeonhole_cnf(5, 4),
        pigeonhole_with_emergency_exit_cnf(5, 4, exit_mode="single"),
        pigeonhole_with_emergency_exit_cnf(6, 5, exit_mode="single"),
        pigeonhole_with_emergency_exit_cnf(5, 4, exit_mode="all"),
        subset_cardinality_fixed_bandwidth_cnf(8),
        even_colouring_torus_cnf(4, 5),
        *vertex_cover_torus_ladder_instances(),
        *dominating_set_hex_ladder_instances(),
        dominating_set_hex_cnf(4, 7),
        complete_graph_coloring_cnf(4, 3),
        complete_graph_coloring_cnf(5, 4),
        complete_graph_tseitin_cnf(5, odd_charge=False),
        complete_graph_tseitin_cnf(5, odd_charge=True),
        *random_3sat_control_instances(),
    ]


def runtime_benchmark_v2_extra_instances() -> list[SymmetryCNF]:
    return [
        random_3sat_control_cnf(35, 149, seed=1911),
        random_3sat_control_cnf(60, 180, seed=1912),
        random_3sat_control_cnf(80, 340, seed=1913),
        random_3sat_control_cnf(100, 600, seed=1914),
        subset_cardinality_fixed_bandwidth_cnf(10),
        subset_cardinality_fixed_bandwidth_cnf(12),
        even_colouring_torus_cnf(4, 6),
        even_colouring_torus_cnf(5, 5),
        pigeonhole_with_emergency_exit_cnf(7, 6, exit_mode="single"),
        pigeonhole_with_emergency_exit_cnf(6, 5, exit_mode="all"),
        dominating_set_hex_cnf(4, 6),
        vertex_cover_torus_cnf(4, 5, version="event", cover_size=6),
        vertex_cover_torus_cnf(4, 5, version="event", cover_size=8),
    ]


def runtime_benchmark_v2_instances() -> list[SymmetryCNF]:
    return [
        *default_symmetry_instances(),
        *runtime_benchmark_v2_extra_instances(),
    ]
