import numpy as np
import pytest
from numpy.lib import format as npy_format

from ucmd_spec.npy import read_vec3_array
from ucmd_spec.report import Invalid


def write(path, array, version=None):
    with path.open("wb") as fh:
        npy_format.write_array(fh, array, version=version)
    return path


@pytest.mark.parametrize("version", [(1, 0), (2, 0)])
def test_accepts_npy_1_and_2(tmp_path, version) -> None:
    data = np.arange(12, dtype="<f8").reshape(4, 3)
    out = read_vec3_array(write(tmp_path / "a.npy", data, version), 4)
    assert np.array_equal(out, data)


@pytest.mark.parametrize(
    ("array", "code"),
    [
        (np.zeros((4, 3), dtype="<f4"), "E_ARRAY_FORMAT"),
        (np.zeros((4, 3), dtype=">f8"), "E_ARRAY_FORMAT"),
        (np.asfortranarray(np.zeros((4, 3))), "E_ARRAY_FORMAT"),
        (np.zeros((3, 4)), "E_ARRAY_FORMAT"),
        (np.array([[0, 0, 0], [0, np.inf, 0], [0, 0, 0], [0, 0, 0]], dtype=float), "E_NONFINITE"),
    ],
)
def test_rejects_wrong_arrays(tmp_path, array, code) -> None:
    with pytest.raises(Invalid) as info:
        read_vec3_array(write(tmp_path / "a.npy", array), 4)
    assert info.value.issue.code == code


def test_rejects_non_npy_and_truncated_and_missing(tmp_path) -> None:
    (tmp_path / "junk.npy").write_bytes(b"not an npy file")
    with pytest.raises(Invalid) as info:
        read_vec3_array(tmp_path / "junk.npy", 4)
    assert info.value.issue.code == "E_ARRAY_FORMAT"
    good = write(tmp_path / "t.npy", np.zeros((4, 3)))
    good.write_bytes(good.read_bytes()[:-8])
    with pytest.raises(Invalid) as info:
        read_vec3_array(good, 4)
    assert info.value.issue.code == "E_ARRAY_FORMAT"
    with pytest.raises(Invalid) as info:
        read_vec3_array(tmp_path / "missing.npy", 4)
    assert info.value.issue.code == "E_ARRAY_MISSING"
