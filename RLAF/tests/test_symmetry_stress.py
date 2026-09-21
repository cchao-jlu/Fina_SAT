import random
import unittest

from src.data.symmetry import (
    SAT,
    UNSAT,
    complete_graph_coloring_cnf,
    default_symmetry_instances,
    dominating_set_hex_cnf,
    even_colouring_torus_cnf,
    infer_num_vars,
    pigeonhole_cnf,
    pigeonhole_with_emergency_exit_cnf,
    random_variable_permutation,
    renamed_variant,
    subset_cardinality_fixed_bandwidth_cnf,
    transform_orbits,
    vertex_cover_torus_ladder_instances,
)


class SymmetryStressTest(unittest.TestCase):
    def test_pigeonhole_formula_has_expected_clause_counts_and_orbits(self):
        instance = pigeonhole_cnf(4, 3)

        self.assertEqual(instance.expected_result, UNSAT)
        self.assertEqual(instance.num_vars, 12)
        self.assertEqual(infer_num_vars(instance.clauses), 12)
        self.assertEqual(len(instance.clauses), 4 + 4 * 3 + 3 * 6)
        self.assertEqual(set(instance.variable_orbits.values()), {"pigeon_hole_assignment"})

    def test_emergency_exit_php_is_satisfiable_stress_variant(self):
        single = pigeonhole_with_emergency_exit_cnf(5, 4, exit_mode="single")
        all_exits = pigeonhole_with_emergency_exit_cnf(5, 4, exit_mode="all")

        self.assertEqual(single.expected_result, SAT)
        self.assertEqual(all_exits.expected_result, SAT)
        self.assertIn("emergency_exit", set(single.variable_orbits.values()))
        self.assertIn("exit_pigeon_assignment", set(single.variable_orbits.values()))
        self.assertIn("regular_pigeon_assignment", set(single.variable_orbits.values()))
        self.assertEqual(single.num_vars, 21)
        self.assertEqual(all_exits.num_vars, 25)

    def test_complete_graph_coloring_is_symmetric_assignment_formula(self):
        instance = complete_graph_coloring_cnf(4, 3)

        self.assertEqual(instance.expected_result, UNSAT)
        self.assertEqual(instance.num_vars, 12)
        self.assertGreater(len(instance.clauses), 0)
        self.assertEqual(set(instance.variable_orbits.values()), {"vertex_color_assignment"})

    def test_subset_cardinality_has_refined_orbits(self):
        instance = subset_cardinality_fixed_bandwidth_cnf(8)

        self.assertEqual(instance.expected_result, UNSAT)
        self.assertGreater(instance.num_vars, 0)
        orbit_sizes = sorted(
            list(instance.variable_orbits.values()).count(orbit)
            for orbit in set(instance.variable_orbits.values())
        )
        self.assertEqual(orbit_sizes, [1, 4, 4, 12, 12])
        self.assertTrue(all(orbit.startswith("subset_cardinality_refined_") for orbit in instance.variable_orbits.values()))

    def test_split_even_colouring_has_refined_edge_orbits(self):
        instance = even_colouring_torus_cnf(4, 5)

        orbit_sizes = sorted(
            list(instance.variable_orbits.values()).count(orbit)
            for orbit in set(instance.variable_orbits.values())
        )
        self.assertIn(1, orbit_sizes)
        self.assertGreaterEqual(len(orbit_sizes), 10)
        self.assertTrue(all(orbit.startswith("even_colouring_refined_") for orbit in instance.variable_orbits.values()))

    def test_hex_dominating_set_has_boundary_refined_orbits(self):
        instance = dominating_set_hex_cnf(4, 7)

        orbit_sizes = sorted(
            list(instance.variable_orbits.values()).count(orbit)
            for orbit in set(instance.variable_orbits.values())
        )
        self.assertEqual(orbit_sizes, [2] * 14)
        self.assertTrue(all(orbit.startswith("dominating_set_hex_refined_") for orbit in instance.variable_orbits.values()))

    def test_three_row_hex_ladder_has_middle_row_singletons(self):
        instance = dominating_set_hex_cnf(3, 5)

        orbit_sizes = sorted(
            list(instance.variable_orbits.values()).count(orbit)
            for orbit in set(instance.variable_orbits.values())
        )
        self.assertEqual(orbit_sizes, [1, 1, 1, 1, 1, 2, 2, 2, 2, 2])

    def test_vertex_cover_torus_ladder_has_event_sized_instances_and_stress_case(self):
        instances = vertex_cover_torus_ladder_instances()

        self.assertEqual(len(instances), 5)
        self.assertEqual(instances[-1].instance_id, "vertex_cover_torus_4x5_norat")
        event_instances = instances[:-1]
        self.assertTrue(all(instance.metadata["version"] == "event" for instance in event_instances))
        self.assertTrue(all(len(instance.clauses) < 10000 for instance in event_instances))
        self.assertEqual({instance.variable_orbits[1] for instance in instances}, {"torus_vertex"})

    def test_renamed_variant_preserves_clause_shape_and_transforms_orbits(self):
        instance = pigeonhole_cnf(4, 3)
        renamed = renamed_variant(instance, seed=123)

        self.assertEqual(renamed.num_vars, instance.num_vars)
        self.assertEqual(len(renamed.clauses), len(instance.clauses))
        self.assertEqual(infer_num_vars(renamed.clauses), instance.num_vars)
        self.assertEqual(set(renamed.variable_orbits.values()), set(instance.variable_orbits.values()))
        self.assertNotEqual(renamed.clauses, instance.clauses)

    def test_transform_orbits_follows_variable_permutation(self):
        rng = random.Random(7)
        permutation = random_variable_permutation(4, rng)
        orbits = {1: "a", 2: "b", 3: "b", 4: "a"}
        transformed = transform_orbits(orbits, permutation)

        for old_var, orbit in orbits.items():
            self.assertEqual(transformed[permutation[old_var]], orbit)

    def test_default_symmetry_instances_are_nonempty(self):
        instances = default_symmetry_instances()

        self.assertGreaterEqual(len(instances), 8)
        for instance in instances:
            self.assertGreater(instance.num_vars, 0)
            self.assertGreater(len(instance.clauses), 0)
            self.assertEqual(infer_num_vars(instance.clauses), instance.num_vars)


if __name__ == "__main__":
    unittest.main()
