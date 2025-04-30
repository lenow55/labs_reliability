import pytest

from repair_manager import (  # pyright: ignore[reportImplicitRelativeImport]
    RepairRecord,
)  # замени your_module на имя файла


def test_repair_record_lt():
    r1 = RepairRecord(id=0, next_event_time=5.0)
    r2 = RepairRecord(id=1, next_event_time=10.0)
    assert r1 < r2


def test_repair_record_lt_wrong_type():
    r1 = RepairRecord(id=1, next_event_time=5.0)
    with pytest.raises(NotImplementedError):
        _ = r1 < 5
