from queue import Empty
from unittest.mock import MagicMock
from uuid import uuid4

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
    srv_id = uuid4()
    result, _ = manager(srv_id=srv_id, current_time=0, nearest_id=None)
    assert isinstance(result, RepairRecord)
    assert result.id == srv_id
    assert result.next_event_time == 5.0


def test_repair_manager_unlimited_mode_nearest_id_passed(mock_dist):
    manager = RepairManager(dist=mock_dist, max_chanels=None)
    srv_id = uuid4()
    nearest_id = uuid4()
    result, _ = manager(srv_id=srv_id, current_time=0, nearest_id=nearest_id)
    assert result is None


def test_repair_manager_limited_mode_adds_to_in_progress(mock_dist):
    manager = RepairManager(dist=mock_dist, max_chanels=2)
    srv_id = uuid4()
    result, _ = manager(srv_id=srv_id, current_time=0, nearest_id=None)
    assert isinstance(result, RepairRecord)
    assert srv_id in manager.repair_in_progress


def test_repair_manager_limited_mode_queue_when_full(mock_dist):
    manager = RepairManager(dist=mock_dist, max_chanels=1)
    srv_id1 = uuid4()
    srv_id2 = uuid4()
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
    srv_id1 = uuid4()
    srv_id2 = uuid4()

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
    srv_id = uuid4()
    with pytest.raises(RuntimeError):
        _ = manager(srv_id=srv_id, current_time=1, nearest_id=srv_id)


def test_repair_manager_no_waiters_after_finish(mock_dist):
    manager = RepairManager(dist=mock_dist, max_chanels=1)
    srv_id = uuid4()

    _ = manager(srv_id=srv_id, current_time=1, nearest_id=None)

    # симулируем, что очередь пуста
    manager.repair_in_wait = MagicMock()
    manager.repair_in_wait.get_nowait.side_effect = Empty

    # заканчиваем обработку
    _ = manager(srv_id=srv_id, current_time=1, nearest_id=srv_id)

    # nearest_srv должен быть минимальным или None
    assert isinstance(manager.nearest_srv, RepairRecord) or manager.nearest_srv is None


# @pytest.mark.parametrize(
#     argnames=["dist", "max_chanels", "input_ids", "output_ids"],
#     argvalues=[
#         pytest.param(
#             Sequential([5.0, 4.0, 3.0]),
#             2,
#             [
#                 UUID("5ad8b223-4abc-4a35-8af9-0795d19d2640"),
#                 UUID("cde19881-d198-4512-8e19-22fa37f2a129"),
#                 UUID("7665298d-8007-4d3f-9a62-474c59f9ad4b"),
#             ],
#             [
#                 UUID("5ad8b223-4abc-4a35-8af9-0795d19d2640"),
#                 UUID("cde19881-d198-4512-8e19-22fa37f2a129"),
#                 UUID("7665298d-8007-4d3f-9a62-474c59f9ad4b"),
#             ],
#         )
#     ],
# )
# def test_repair_manager_processing_nearest_srv(
#     dist: Distribution,
#     max_chanels: int,
#     input_order: list[UUID],
#     output_order: list[UUID],
# ):
#     manager = RepairManager(dist=dist, max_chanels=max_chanels)
#
#     # первый пошел на ремонт
#     first = manager(srv_id=srv_id1, nearest_id=None)
#     assert manager.nearest_srv
#     assert manager.nearest_srv.id == srv_id1
#
#     # второй стал в очередь
#     manager(srv_id=srv_id2, nearest_id=None)
#     assert manager.repair_in_wait.qsize() == 1
#
#     # обрабатываем завершение ремонта первого
#     result = manager(srv_id=srv_id1, nearest_id=srv_id1)
#
#     # должен взять второго из очереди
#     assert manager.nearest_srv
#     assert manager.nearest_srv.id == srv_id2
#     assert srv_id2 in manager.repair_in_progress
#     assert result is None
