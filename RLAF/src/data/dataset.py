from copy import copy
from collections.abc import Sequence as SequenceABC
from multiprocessing import Pool
import os
from pathlib import Path
from typing import Literal, Callable, Optional, Sequence
from glob import glob, has_magic

import numpy as np
import pandas as pd
import torch
from torch_geometric.data import HeteroData, Dataset
from pysat.formula import CNF
from tqdm import tqdm

from src.data.cnf import cnf_to_pyg
from src.solving.backbone import get_backbone_lits
from src.solving.core import get_core_vars


class LazyCNFList:
    """Indexable CNF view that loads DIMACS files on demand."""

    def __init__(self, files: Sequence[str], cache: bool = True):
        self.files = list(files)
        self.cache = bool(cache)
        self._cache: dict[int, CNF] = {}

    def __len__(self) -> int:
        return len(self.files)

    def __getitem__(self, idx: int) -> CNF:
        idx = int(idx)
        if self.cache and idx in self._cache:
            return self._cache[idx]
        cnf = CNF(from_file=self.files[idx])
        if self.cache:
            self._cache[idx] = cnf
        return cnf


class DimacsCNFDataset(Dataset):
    """
    This dataset class provides the functionality for:
    1. Loading a collection of DIMACS CNF formulas from a given path or glob pattern (e.g., "*.cnf").
    2. Converting each loaded CNF to a PyG graph.
    3. Applying an optional transform function to each PyG graph.
    """

    def __init__(
            self,
            path: str | os.PathLike[str] | Sequence[str | os.PathLike[str]],
            transform: Optional[Callable] = None,
            lazy: bool = False,
            lazy_cache: bool = True,
    ):
        """
        :param path: A pattern or directory path pointing to DIMACS CNF files.
        :param transform: An optional PyG transform to apply to each graph.
        """
        super().__init__()
        self.path = path
        self.transform = transform
        self.lazy = bool(lazy)
        self.lazy_cache = bool(lazy_cache)

        self.files = self._resolve_dimacs_files(self.path)
        self.id_to_file = {i: fn for i, fn in enumerate(self.files)}

        if self.lazy:
            self.cnf_dict = {}
            self.cnf_list = LazyCNFList(self.files, cache=self.lazy_cache)
            self.data_list = None
        else:
            # 1) Load CNFs from the specified path
            self.cnf_dict = self._load_dimacs_files(self.files)

            # 2) Convert CNFs to PyG data objects
            self.cnf_list = [self.cnf_dict[self.id_to_file[i]] for i in range(len(self.cnf_dict))]
            self.data_list = self._convert_to_pyg()

    def _resolve_dimacs_files(
            self,
            path: str | os.PathLike[str] | Sequence[str | os.PathLike[str]],
    ) -> list[str]:
        def path_string(item) -> str:
            if isinstance(item, str):
                return item
            if isinstance(item, os.PathLike):
                value = os.fspath(item)
                if isinstance(value, str):
                    return value
            raise TypeError("DIMACS path entries must be str or os.PathLike")

        if isinstance(path, (str, os.PathLike)):
            pattern = path_string(path)
            files = list(glob(pattern))
            if not files and not has_magic(pattern):
                files = [pattern]
        elif isinstance(path, SequenceABC):
            files = [path_string(item) for item in path]
        else:
            raise TypeError("DIMACS path entries must be str or os.PathLike")
        files.sort()
        if not files:
            raise ValueError(f"No DIMACS files found for path/pattern: {path}")

        resolved_files = []
        missing_files = []
        for file in files:
            source = Path(file)
            if source.is_file():
                resolved_files.append(str(source))
                continue

            candidate = None
            split_dir = source.parent.parent
            if (
                source.is_symlink()
                and source.suffix == ".cnf"
                and split_dir.name in {"train", "val"}
                and source.parent != split_dir
            ):
                candidate = split_dir.parent / "cnf" / source.parent.name / source.name
            if (
                candidate is not None
                and candidate.is_file()
                and not candidate.is_symlink()
            ):
                resolved_files.append(str(candidate))
            else:
                missing_files.append(str(source))

        if missing_files:
            limit = 10
            listed = "\n".join(f"  - {file}" for file in missing_files[:limit])
            remainder = len(missing_files) - limit
            suffix = f"\n  ... and {remainder} more" if remainder > 0 else ""
            raise FileNotFoundError(
                f"Missing DIMACS files after path preflight ({len(missing_files)}):\n"
                f"{listed}{suffix}"
            )

        files_by_identity = {}
        for source, resolved in zip(files, resolved_files):
            stat = Path(resolved).stat()
            identity = (stat.st_dev, stat.st_ino)
            record = files_by_identity.setdefault(
                identity,
                {"resolved_paths": [], "sources": []},
            )
            record["resolved_paths"].append(resolved)
            record["sources"].append(source)
        duplicates = {
            identity: record
            for identity, record in files_by_identity.items()
            if len(record["sources"]) > 1
        }
        if duplicates:
            identity, record = next(iter(duplicates.items()))
            raise ValueError(
                "Duplicate resolved DIMACS file: "
                f"identity={identity} resolved_paths={record['resolved_paths']} "
                f"sources={record['sources']}"
            )
        return sorted(resolved_files)

    def _load_dimacs_files(self, files: Sequence[str]) -> dict[str, CNF]:
        """ Loads .dimacs files from the given path or file list. """
        cnf_dict = {}
        for f in tqdm(files, desc="Loading validated DIMACS files"):
            cnf_dict[f] = CNF(from_file=f)
        return cnf_dict

    def _convert_to_pyg(self) -> list[HeteroData]:
        """ Converts each CNF in self.cnf_list into a PyG data object via cnf_to_pyg. """
        enumerated_cnfs = list(enumerate(self.cnf_list))

        data_list = []
        for i, cnf in tqdm(enumerated_cnfs, desc="Converting CNFs to PyG"):
            data = cnf_to_pyg(f=cnf.clauses, num_var=cnf.nv)
            # Optionally apply a transform
            if self.transform is not None:
                data = self.transform(data)
            # Store the index as a tensor
            data.cnf_id = torch.tensor(i, dtype=torch.long)
            data_list.append(data)
        return data_list

    def _convert_one_to_pyg(self, idx: int) -> HeteroData:
        cnf = self.cnf_list[int(idx)]
        data = cnf_to_pyg(f=cnf.clauses, num_var=cnf.nv)
        if self.transform is not None:
            data = self.transform(data)
        data.cnf_id = torch.tensor(int(idx), dtype=torch.long)
        return data

    def __getitem__(self, idx: int) -> HeteroData:
        if self.lazy:
            return self._convert_one_to_pyg(int(idx))
        return self.data_list[idx]

    def __len__(self) -> int:
        return len(self.id_to_file)

    def len(self) -> int:
        return self.__len__()

    def get(self, idx: int) -> HeteroData:
        return self.__getitem__(idx)


def _label_fn(args: tuple[str, str]) -> tuple[str, np.ndarray]:
    file, target = args
    if target == "backbone":
        lit_mask = get_backbone_lits(file, as_array=True, cache=True)
    elif target == "core":
        var_mask = get_core_vars(file, cache=True, keep_aux_files=False)
        lit_mask = np.repeat(var_mask, 2)
    else:
        raise ValueError(f"Unknown target label {target}")
    return file, lit_mask


class LabeledDataset(DimacsCNFDataset):
    """ Dataset for supervised training with backbone or unsat core labels"""

    def __init__(
            self,
            path: str,
            transform: Optional[Callable] = None,
            target: str = "backbone",
            num_workers: int = 0,
    ):
        """
        :param path: A pattern or directory path pointing to DIMACS CNF files.
        :param transform: An optional PyG transform to apply to each graph.
        :param target: Supervision target. Either "backbone" or "core". The labels will be added automatically.
        :param num_workers: Number of workers with which to compute labels.
        """
        super(LabeledDataset, self).__init__(path, transform)
        self.target = target
        self.num_workers = num_workers

        inputs = [(file, self.target) for file in self.id_to_file.values()]
        label_map = {}
        if self.num_workers <= 1:
            for args in tqdm(inputs, desc=f"Adding {target} target to data"):
                file, target = _label_fn(args)
                label_map[file] = target
        else:
            # Run in parallel via multiprocessing
            with Pool(self.num_workers) as pool:
                # imap is a lazy iterator, so we can wrap it in tqdm for progress
                results_iter = pool.imap(_label_fn, inputs)
                for file, target in tqdm(results_iter, total=len(inputs), desc=f"Adding {target} target to data"):
                    label_map[file] = target

        for i, data in enumerate(self.data_list):
            file = self.id_to_file[i]
            target = label_map[file]
            data["lit"].target = torch.tensor(target, dtype=torch.float32)


class RLTrainingDataset(Dataset):
    """
    This dataset class for RL-training with GRPO or DPO. Maintains a set of PyG graphs and associated cost measurements.
    """

    def __init__(
            self,
            solver_stats: pd.DataFrame,
            data_list: list[HeteroData],
            target_stat: str = "decisions",
            objective: Literal["minimize", "maximize"] = "minimize",
    ):
        """
        :param solver_stats: pandas.DataFrame containing solver statistics.
        :param data_list: list of HeteroData objects corresponding to the same CNF formulas as `solver_stats`.
        :param target_stat: Target metric to minimize or maximize.
        :param objective: Whether to minimize or maximize the target metric.
        """
        self.solver_stats = solver_stats.sort_values(by=["cnf_id", "sample_id"], ascending=[True, True])

        self.data = []
        for data in data_list:
            # copy to avoid side effects with original data objects
            data = copy(data)
            cnf_id = data.cnf_id.item()

            # convert target cost metric to tensor and add to the data objects
            cnf_stats = self.solver_stats[self.solver_stats["cnf_id"] == cnf_id]
            stats = torch.tensor(cnf_stats[target_stat].to_numpy())

            # Sort results and associated variable parameterizations according to the costs.
            # This is needed for DPO training.
            if objective == "minimize":
                idx = torch.argsort(-stats)
            else:
                idx = torch.argsort(stats)

            var_params = data["var"].var_params
            log_prob = data.log_prob

            # add ordered parameters, log_probs and costs to the data object.
            data["var"].var_params = var_params[:, idx]
            data.log_prob = log_prob[idx].unsqueeze(0)
            data.stats = stats[idx].unsqueeze(0)

            self.data.append(data)

        super(RLTrainingDataset, self).__init__()

    def __len__(self):
        return len(self.data)

    def __getitem__(self, item):
        return self.data[item]

    def len(self) -> int:
        return self.__len__()

    def get(self, idx: int) -> HeteroData:
        return self.__getitem__(idx)
