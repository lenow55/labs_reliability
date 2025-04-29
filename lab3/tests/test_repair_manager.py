from queue import Empty
from unittest.mock import MagicMock

import pytest
from repair_manager import (  # pyright: ignore[reportImplicitRelativeImport]
    RepairManager,
    RepairRecord,
)


@pytest.fixture
def mock_dist():
    dist = MagicMock()
    dist.sample.return_value = 5.0
    return dist


def test_repair_manager_init_with_invalid_max_channels(mock_dist):
    with pytest.raises(ValueError):
        RepairManager(dist=mock_dist, max_chanels=0)


def test_repair_manager_unlimited_mode_creates_record(mock_dist):
    manager = RepairManager(dist=mock_dist, max_chanels=None)
    srv_id = 0
    result, flag = manager(srv_id=srv_id, current_time=0, nearest_id=None)
    assert isinstance(result, RepairRecord)
    assert result.id == srv_id
    assert result.next_event_time == 5.0
    assert flag


def test_repair_manager_unlimited_mode_nearest_id_passed(mock_dist):
    manager = RepairManager(dist=mock_dist, max_chanels=None)
    srv_id = 0
    nearest_id = None
    result, flag = manager(srv_id=srv_id, current_time=0, nearest_id=nearest_id)
    assert result == RepairRecord(id=0, next_event_time=5.0)
    assert flag


def test_repair_manager_limited_mode_adds_to_in_progress(mock_dist):
    manager = RepairManager(dist=mock_dist, max_chanels=2)
    srv_id = 0
    result, flag = manager(srv_id=srv_id, current_time=0, nearest_id=None)
    assert isinstance(result, RepairRecord)
    assert srv_id in manager.repair_in_progress
    assert flag


def test_repair_manager_limited_mode_queue_when_full(mock_dist):
    manager = RepairManager(dist=mock_dist, max_chanels=1)
    srv_id1 = 0
    srv_id2 = 1
    _ = manager(
        srv_id=srv_id1, current_time=0, nearest_id=None
    )  # первый сервер — в прогресс
    result = manager(
        srv_id=srv_id2, current_time=1, nearest_id=None
    )  # второй — в очередь
    assert srv_id2 not in manager.repair_in_progress
    assert result is not None
    assert manager.repair_in_wait.qsize() == 1


def test_repair_manager_processing_nearest_srv(mock_dist):
    manager = RepairManager(dist=mock_dist, max_chanels=1)
    srv_id1 = 0
    srv_id2 = 1

    # первый пошел на ремонт
    _ = manager(srv_id=srv_id1, current_time=0, nearest_id=None)
    assert manager.nearest_srv
    assert manager.nearest_srv.id == srv_id1

    # второй стал в очередь
    _ = manager(srv_id=srv_id2, current_time=1, nearest_id=None)
    assert manager.repair_in_wait.qsize() == 1

    # обрабатываем завершение ремонта первого
    result, _ = manager(srv_id=srv_id1, current_time=2, nearest_id=srv_id1)

    # должен взять второго из очереди
    assert manager.nearest_srv
    assert manager.nearest_srv.id == srv_id2
    assert srv_id2 in manager.repair_in_progress
    assert result is None


def test_repair_manager_runtime_error_on_missing_nearest(mock_dist):
    manager = RepairManager(dist=mock_dist, max_chanels=1)
    srv_id = 0
    with pytest.raises(RuntimeError):
        _ = manager(srv_id=srv_id, current_time=1, nearest_id=srv_id)


def test_repair_manager_no_waiters_after_finish(mock_dist):
    manager = RepairManager(dist=mock_dist, max_chanels=1)
    srv_id = 0

    _ = manager(srv_id=srv_id, current_time=1, nearest_id=None)

    # симулируем, что очередь пуста
    manager.repair_in_wait = MagicMock()
    manager.repair_in_wait.get_nowait.side_effect = Empty

    # заканчиваем обработку
    _ = manager(srv_id=srv_id, current_time=1, nearest_id=srv_id)

    # nearest_srv должен быть минимальным или None
    assert isinstance(manager.nearest_srv, RepairRecord) or manager.nearest_srv is None
