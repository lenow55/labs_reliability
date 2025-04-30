from functools import partial
from itertools import zip_longest
from uuid import UUID

import ciw
from ciw import dists
from custom_arrival_node import (  # pyright: ignore[reportImplicitRelativeImport]
    CustomArrivalNode,
)
from custom_schedule import (  # pyright: ignore[reportImplicitRelativeImport]
    RepairedFailureSchedule,
)
from repair_manager import (  # pyright: ignore[reportImplicitRelativeImport]
    RepairManager,
)
from reroute import ReservRerouting  # pyright: ignore[reportImplicitRelativeImport]

CustomPartialArrivalClass = partial(CustomArrivalNode, node_bypass_index=3)
manager = RepairManager(dist=dists.Deterministic(value=3.0), max_chanels=1)


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
            ReservRerouting(to=-1, reroute_to=3),
            ReservRerouting(to=-1, reroute_to=3),
            ciw.routing.Leave(),
        ]
    ),
    number_of_servers=[
        RepairedFailureSchedule(
            failure_dist=dists.Sequential([20, 25, 5]),
            repair_mgr=manager,
            preemption="reroute",
            id=0,
        ),
        RepairedFailureSchedule(
            failure_dist=dists.Sequential([20, 30]),
            repair_mgr=manager,
            preemption="reroute",
            id=1,
        ),
        # RepairedFailureSchedule(
        #     failure_dist=dists.Sequential([100, 150]),
        #     repair_mgr=manager,
        #     preemption="reroute",
        #     id=2,
        # ),
        1,
    ],
    # У дуплексного канала с двух сторон по два слота для ожидания
    # у спутниковой линии очереди нет
    # При чём буферный регист должен быть занят даже во время
    # передачи сообщения каналом (так работают регистры и об этом в условии написано)
    # по этой причине реальная очередь перед каналами = 1
    queue_capacities=[1, 1, 0],
)


def test_repair_schedule_inet_net():
    Q = ciw.Simulation(
        N,
        arrival_node_class=CustomPartialArrivalClass,
    )
    Q.simulate_until_max_customers(max_customers=50, progress_bar=True, method="Finish")
    T = ciw.Simulation(
        N,
        arrival_node_class=CustomPartialArrivalClass,
    )
    # T.transitive_nodes[0].schedule.srv_id = UUID("00000000-0000-0000-0000-000000000001")
    # T.transitive_nodes[1].schedule.srv_id = UUID("00000000-0000-0000-0000-000000000002")
    T.simulate_until_max_time(max_simulation_time=100, progress_bar=True)

    for node in T.transitive_nodes:
        schedule = node.schedule
        if not isinstance(schedule, RepairedFailureSchedule):
            continue
        print(str(node))
        for start, fail, repair in zip_longest(
            schedule.start_dates,
            schedule.failure_dates,
            schedule.repair_start_date,
            fillvalue=None,
        ):
            print(start, fail, repair)
