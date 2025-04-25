from collections.abc import Generator

from ciw import Schedule

# TODO: надо сделать возможным передавать сюда класс, отвечающий за каналы восстановления
# то есть чтобы перед восстановлением нужно было занимать лок в объекте очереди


class ExponentialFailureSchedule(Schedule):
    failure_generator: Generator[float, None, None]
    recovery_generator: Generator[float, None, None]

    def __init__(
        self,
        failure_gen: Generator[float, None, None],
        recovery_gen: Generator[float, None, None],
        preemption: bool | str = False,
        offset: float = 0.0,
    ):
        """
        Initializes the ExponentialFailureSchedule instance.

        Parameters
        ----------
        failure_rate : float
            Rate (lambda) of the exponential distribution for failure times.
        recovery_rate : float
            Rate (lambda) of the exponential distribution for recovery times.
        preemption : Union[bool, str], optional
            Pre-emption behavior. Default is False.
        offset : float, optional
            Time offset to start the schedule from. Default is 0.0.
        """
        self.schedule_type: str = "exponential_failure_recovery"
        self.failure_generator = failure_gen
        self.recovery_generator = recovery_gen
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
        is_up = True

        while True:
            if is_up:
                # Time until failure
                duration = self.failure_generator.__next__()
                current_time += duration
                yield current_time, 0  # servers go down
                is_up = False
            else:
                # Time until recovery
                duration = self.recovery_generator.__next__()
                current_time += duration
                yield current_time, 1  # servers come back up
                is_up = True
