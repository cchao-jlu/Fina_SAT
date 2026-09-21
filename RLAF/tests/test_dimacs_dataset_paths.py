import os
from collections import UserList
from pathlib import Path

import pytest

from src.data.dataset import DimacsCNFDataset


ROOT = Path(__file__).resolve().parents[1]


def _write_cnf(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("p cnf 1 1\n1 0\n", encoding="utf-8")
    return path


def _broken_symlink(path: Path, target: str = "/old/linux/root/missing.cnf") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.symlink_to(target)
    except (NotImplementedError, OSError) as exc:
        pytest.skip(f"symlinks unavailable: {exc}")
    assert path.is_symlink()
    assert not path.exists()
    return path


def _hardlink(source: Path, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.link(source, destination)
    except (NotImplementedError, OSError) as exc:
        pytest.skip(f"hardlinks unavailable: {exc}")
    return destination


def test_existing_dimacs_file_keeps_original_path(tmp_path: Path):
    source = _write_cnf(tmp_path / "plain" / "sample.cnf")

    dataset = DimacsCNFDataset(str(source), lazy=True)

    assert dataset.files == [str(source)]


def test_pathlike_is_treated_as_single_pattern(tmp_path: Path):
    source = _write_cnf(tmp_path / "plain" / "pathlike.cnf")

    dataset = DimacsCNFDataset(source, lazy=True)

    assert dataset.files == [str(source)]


@pytest.mark.parametrize("split", ["train", "val"])
def test_broken_canonical_split_symlink_uses_portable_cnf_sibling(
    tmp_path: Path,
    split: str,
):
    candidate = _write_cnf(tmp_path / "canonical" / "cnf" / "family" / "sample.cnf")
    link = _broken_symlink(
        tmp_path / "canonical" / split / "family" / "sample.cnf"
    )

    dataset = DimacsCNFDataset(str(link), lazy=True)

    assert dataset.files == [str(candidate)]
    assert Path(dataset.files[0]).is_file()


def test_list_input_preflights_and_sorts_normal_and_fallback_files(tmp_path: Path):
    normal = _write_cnf(tmp_path / "canonical" / "cnf" / "a" / "normal.cnf")
    candidate = _write_cnf(tmp_path / "canonical" / "cnf" / "b" / "portable.cnf")
    link = _broken_symlink(
        tmp_path / "canonical" / "train" / "b" / "portable.cnf"
    )

    dataset = DimacsCNFDataset([str(link), str(normal)], lazy=True)

    assert dataset.files == sorted([str(normal), str(candidate)])


def test_general_sequence_and_path_entries_are_supported(tmp_path: Path):
    first = _write_cnf(tmp_path / "plain" / "first.cnf")
    second = _write_cnf(tmp_path / "plain" / "second.cnf")

    dataset = DimacsCNFDataset(UserList([second, str(first)]), lazy=True)

    assert dataset.files == sorted([str(first), str(second)])


@pytest.mark.parametrize("bad_path", [["valid.cnf", 7], 7])
def test_invalid_path_api_elements_raise_clear_type_error(bad_path):
    with pytest.raises(
        TypeError,
        match="DIMACS path entries must be str or os.PathLike",
    ):
        DimacsCNFDataset(bad_path, lazy=True)


@pytest.mark.parametrize(
    "build_path",
    [
        lambda root: root / "ordinary" / "missing.cnf",
        lambda root: _broken_symlink(
            root / "canonical" / "train" / "family" / "missing.cnf"
        ),
    ],
    ids=["ordinary-missing", "broken-symlink-without-candidate"],
)
def test_missing_files_fail_during_lazy_dataset_construction(tmp_path: Path, build_path):
    source = build_path(tmp_path)

    with pytest.raises(FileNotFoundError, match="Missing DIMACS files") as exc_info:
        DimacsCNFDataset([str(source)], lazy=True)

    assert str(source) in str(exc_info.value)


@pytest.mark.parametrize("candidate_kind", ["directory", "broken_symlink"])
def test_fallback_candidate_must_be_a_real_file(tmp_path: Path, candidate_kind: str):
    candidate = tmp_path / "canonical" / "cnf" / "family" / "sample.cnf"
    if candidate_kind == "directory":
        candidate.mkdir(parents=True)
    else:
        _broken_symlink(candidate)
    link = _broken_symlink(
        tmp_path / "canonical" / "val" / "family" / "sample.cnf"
    )

    with pytest.raises(FileNotFoundError, match="Missing DIMACS files"):
        DimacsCNFDataset(str(link), lazy=True)


def test_duplicate_files_created_by_portable_fallback_are_rejected(tmp_path: Path):
    candidate = _write_cnf(tmp_path / "canonical" / "cnf" / "family" / "same.cnf")
    train_link = _broken_symlink(
        tmp_path / "canonical" / "train" / "family" / "same.cnf"
    )
    val_link = _broken_symlink(
        tmp_path / "canonical" / "val" / "family" / "same.cnf"
    )

    with pytest.raises(ValueError, match="Duplicate resolved DIMACS file") as exc_info:
        DimacsCNFDataset([str(train_link), str(val_link)], lazy=True)

    assert str(candidate) in str(exc_info.value)


def test_two_hardlinks_in_one_dataset_are_rejected_by_file_identity(tmp_path: Path):
    source = _write_cnf(tmp_path / "source" / "same.cnf")
    first = _hardlink(source, tmp_path / "links" / "first.cnf")
    second = _hardlink(source, tmp_path / "links" / "second.cnf")

    with pytest.raises(ValueError, match="Duplicate resolved DIMACS file") as exc_info:
        DimacsCNFDataset([first, second], lazy=True)

    message = str(exc_info.value)
    assert str(first) in message
    assert str(second) in message
    assert "sources" in message


def test_train_val_style_hardlinks_are_rejected_by_file_identity(tmp_path: Path):
    source = _write_cnf(tmp_path / "canonical" / "cnf" / "family" / "same.cnf")
    train = _hardlink(
        source,
        tmp_path / "canonical" / "train" / "family" / "same.cnf",
    )
    val = _hardlink(
        source,
        tmp_path / "canonical" / "val" / "family" / "same.cnf",
    )

    with pytest.raises(ValueError, match="Duplicate resolved DIMACS file") as exc_info:
        DimacsCNFDataset([train, val], lazy=True)

    message = str(exc_info.value)
    assert str(train) in message
    assert str(val) in message


def test_non_lazy_dataset_preflights_only_once_and_preserves_file_order(
    tmp_path: Path,
    monkeypatch,
):
    first = _write_cnf(tmp_path / "plain" / "a.cnf")
    second = _write_cnf(tmp_path / "plain" / "b.cnf")
    calls = []
    original = DimacsCNFDataset._resolve_dimacs_files

    def spy(self, path):
        calls.append(path)
        return original(self, path)

    monkeypatch.setattr(DimacsCNFDataset, "_resolve_dimacs_files", spy)
    monkeypatch.setattr(DimacsCNFDataset, "_convert_to_pyg", lambda self: [])

    dataset = DimacsCNFDataset([second, first], lazy=False)

    assert len(calls) == 1
    assert dataset.files == [str(first), str(second)]
    assert list(dataset.cnf_dict) == dataset.files


def test_real_canonical_splits_resolve_portably_without_overlap():
    canonical = ROOT / "data" / "echosat_symmetry_grpo_v1_canonical"
    train = DimacsCNFDataset(str(canonical / "train" / "*" / "*.cnf"), lazy=True)
    val = DimacsCNFDataset(str(canonical / "val" / "*" / "*.cnf"), lazy=True)

    assert len(train) == 1124
    assert len(val) == 275
    assert all(Path(path).is_file() for path in train.files)
    assert all(Path(path).is_file() for path in val.files)
    assert {Path(path).name for path in train.files}.isdisjoint(
        {Path(path).name for path in val.files}
    )
