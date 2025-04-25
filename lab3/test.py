from functools import partial

import ciw
import numpy as np
from ciw import dists
from custom_arrival_node import (
    CustomArrivalNode,  # pyright: ignore[reportImplicitRelativeImport]
)
from custom_schedule import (
    ExponentialFailureSchedule,  # pyright: ignore[reportImplicitRelativeImport]
)
from numpy.random import PCG64


def build_exp_generator(lambda_: float):
    generator = np.random.Generator(PCG64(42))
    while True:
        yield generator.exponential(1 / lambda_)


fail_gen = build_exp_generator(lambda_=0.5)
recovery_gen = build_exp_generator(lambda_=0.5)

CustomPartialArrivalClass = partial(CustomArrivalNode, node_bypass_index=3)


N = ciw.create_network(
    arrival_distributions=[
        dists.Uniform(lower=7, upper=13),  # Сообщения А -> B
        dists.Uniform(lower=7, upper=13),  # Сообщения B -> A
        None,  # Сообщения на спутниковую линию приходят только при занятости каналов 1, 2
    ],
    service_distributions=[
        dists.Deterministic(value=10.0),  # Передача сообщения A -> B
        dists.Deterministic(value=10.0),  # Передача сообщения B -> A
        # Передача по спутниковой линии (полудуплекс - 1 сообщение в каждую сторону)
        dists.Uniform(lower=5, upper=15),
    ],
    routing=ciw.routing.NetworkRouting(
        # После прохождения каждого из каналов сообщения покидают систему
        routers=[
            ciw.routing.Leave(),
            ciw.routing.Leave(),
            ciw.routing.Leave(),
        ]
    ),
    number_of_servers=[
        ExponentialFailureSchedule(
            failure_gen=fail_gen, recovery_gen=recovery_gen, preemption="restart"
        ),
        # ciw.Schedule(
        #     numbers_of_servers=[1, 0, 1],
        #     shift_end_dates=[10.5, 30.5, 100],
        #     preemption=False,
        # ),
        1,
        1,
    ],
    # У дуплексного канала с двух сторон по два слота для ожидания
    # у спутниковой линии очереди нет
    # При чём буферный регист должен быть занят даже во время
    # передачи сообщения каналом (так работают регистры и об этом в условии написано)
    # по этой причине реальная очередь перед каналами = 1
    queue_capacities=[1, 1, 0],
)

max_time = 600

Q = ciw.Simulation(N, arrival_node_class=CustomPartialArrivalClass)
# Q.simulate_until_max_time(max_simulation_time=max_time, progress_bar=True)
Q.simulate_until_max_customers(max_customers=60, progress_bar=True, method="Arrive")

recs = Q.get_all_records()
print(len([r for r in recs if r.node == 1 and r.record_type == "interrupted service"]))
