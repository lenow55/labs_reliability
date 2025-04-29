import queue
from dataclasses import dataclass
from queue import Queue
from typing import Any
from uuid import UUID

from ciw.dists import Distribution


@dataclass
class RepairRecord:
    id: UUID
    next_event_time: float

    def __lt__(self, other: Any) -> bool:
        if not isinstance(other, RepairRecord):
            raise NotImplementedError
        return self.next_event_time < other.next_event_time


class RepairManager:
    repair_in_progress: dict[UUID, RepairRecord]
    max_chanels: int | None
    repair_in_wait: Queue[UUID]
    nearest_srv: RepairRecord | None = None
    repair_dist: Distribution  # распределение времени восстановления

    def __init__(self, dist: Distribution, max_chanels: int | None = None) -> None:
        self.repair_in_progress = {}
        if isinstance(max_chanels, int):
            if max_chanels < 1:
                raise ValueError("max_chanels can't be non positive")

        self.repair_dist = dist
        self.max_chanels = max_chanels
        self.repair_in_wait = Queue()

    def initialise(self):
        """
        Initializes the object at the beginning of a simulation.
        """
        self.repair_in_progress = {}
        self.repair_in_wait = Queue()
        self.nearest_srv = None

    def __call__(
        self, srv_id: UUID, current_time: float, nearest_id: UUID | None
    ) -> tuple[RepairRecord | None, bool]:
        # когда у нас не ограничена очередь
        if not self.max_chanels:
            if not nearest_id:
                # считаем время восстановления и возвращаем
                repair_time: float = self.repair_dist.sample()  # pyright: ignore[reportAssignmentType]
                record = RepairRecord(
                    id=srv_id, next_event_time=repair_time + current_time
                )
                return record, True
            # nearest_id стоит, значит сервер уже прошёл восстановление
            # возвращаем None, чтобы он продолжил работу
            return None, True

        if not nearest_id:
            # пришёл новый сервис на восстановление
            if len(self.repair_in_progress) < self.max_chanels:
                # свободное место в очереди
                repair_time: float = self.repair_dist.sample()  # pyright: ignore[reportAssignmentType]
                record = RepairRecord(
                    id=srv_id, next_event_time=repair_time + current_time
                )
                self.repair_in_progress[record.id] = record
                self.nearest_srv = min(self.repair_in_progress.values())
                return record, True
            else:
                # мест в очереди нет
                self.repair_in_wait.put(srv_id, block=False)
                return self.nearest_srv, False

        # дальше обработка перепланировки, так как приходит сервис с уже
        # известным минимальным временем

        # общие действия
        if not self.nearest_srv:
            # тут просто обязан быть nearest_srv
            raise RuntimeError("Nearest srv must presence")
        if self.nearest_srv.id == nearest_id:
            # пришёл первый из ожидающих текущего в обработке
            # значит надо завершить текущий и перепланировать
            _ = self.repair_in_progress.pop(self.nearest_srv.id)
            try:
                next2process = self.repair_in_wait.get_nowait()
                repair_time: float = self.repair_dist.sample()  # pyright: ignore[reportAssignmentType]
                record = RepairRecord(
                    id=next2process, next_event_time=repair_time + current_time
                )
                self.repair_in_progress[record.id] = record
            except queue.Empty:
                pass
            self.nearest_srv = min(self.repair_in_progress.values(), default=None)
        if srv_id == nearest_id:
            # который был обоработан только что
            return None, True
        # если пришёл сервер:
        # - который только что поставлен в обработку: srv_id in self.repair_in_progress
        if srv_id in self.repair_in_progress.keys():
            return self.repair_in_progress[srv_id], True

        # - просто пришёл ожидающий сервер из очереди: nearest_id != self.nearest_srv.id
        return self.nearest_srv, False
