from collections.abc import Generator
from uuid import UUID, uuid4

from ciw import Schedule
from ciw.dists import Distribution
from repair_manager import (  # pyright: ignore[reportImplicitRelativeImport]
    RepairManager,
    RepairRecord,
)

# TODO: надо сделать возможным передавать сюда класс, отвечающий за каналы восстановления
# то есть чтобы перед восстановлением нужно было занимать лок в объекте очереди


class RepairedFailureSchedule(Schedule):
    failure_dist: Distribution
    repair_manager: RepairManager
    srv_id: UUID = uuid4()
    start_dates: list[float] = []
    failure_dates: list[float] = []
    repair_start_date: list[float] = []

    def __init__(
        self,
        failure_dist: Distribution,
        repair_mgr: RepairManager,
        preemption: bool | str = False,
        offset: float = 0.0,
    ):
        """
        Initializes the ExponentialFailureSchedule instance.

        Parameters
        ----------
        failure_dist : Distribution
            Ciw расределение возникновения ошибок, относительное время
        recovery_rate : float
            Rate (lambda) of the exponential distribution for recovery times.
        preemption : Union[bool, str], optional
            Pre-emption behavior. Default is False.
        offset : float, optional
            Time offset to start the schedule from. Default is 0.0.
        """
        self.schedule_type: str = "exponential_failure_recovery"
        self.failure_dist = failure_dist
        self.repair_manager = repair_mgr
        super().__init__([1, 0], [0.0, float("inf")], preemption, offset)

    def initialise(self):  # pyright: ignore[reportIncompatibleMethodOverride]
        """
        Initializes the generator object at the beginning of a simulation.
        """
        self.c = 0
        self.next_shift_change_date = self.offset
        self.next_c = self.numbers_of_servers[0]
        self.schedule_generator = self.get_schedule_generator(
            self.shift_end_dates, self.numbers_of_servers, self.offset
        )
        self.start_dates = []
        self.failure_dates = []
        self.repair_start_date = []
        self.repair_manager.initialise()

    def get_schedule_generator(
        self, boundaries: list[float], values: list[int], offset: float
    ) -> Generator[tuple[float, int], None, None]:
        """
        A generator that yields alternating up/down times using exponential distributions.

        Parameters
        ----------
        boundaries : List[float]
            Ignored.
        values : List[int]
            Ignored.
        offset : float
            Time offset to start from.

        Yields
        ------
        Tuple[float, int]
            Time and number of available servers (1 for up, 0 for down).
        """
        current_time = offset
        is_init = True
        nearest_id: UUID | None = None

        while True:
            if is_init:
                self.start_dates.append(current_time)
                # Time until failure
                duration: float = self.failure_dist.sample()  # pyright: ignore[reportAssignmentType]
                current_time += duration
                yield current_time, 0  # servers go down
                self.failure_dates.append(current_time)
                is_init = False

            # Time until recovery
            record, flag = self.repair_manager(
                srv_id=self.srv_id, current_time=current_time, nearest_id=nearest_id
            )
            if isinstance(record, RepairRecord):
                # сразу возвращает абсолютное время до события
                if flag:
                    self.repair_start_date.append(current_time)
                current_time = record.next_event_time
                nearest_id = record.id
                yield current_time, int(flag)  # servers continious down
            else:
                # вернул none, значит можно поднимать сразу
                nearest_id = None
                self.start_dates.append(current_time)
                # генерируем время нормальной работы
                duration: float = self.failure_dist.sample()  # pyright: ignore[reportAssignmentType]
                current_time += duration
                yield current_time, 0  # servers go up
                self.failure_dates.append(current_time)
