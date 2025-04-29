from uuid import UUID
import ciw
from ciw import dists

from custom_schedule import RepairedFailureSchedule  # pyright: ignore[reportImplicitRelativeImport]
from repair_manager import (  # pyright: ignore[reportImplicitRelativeImport]
    RepairManager,
)

ciw.seed(11)
manager = RepairManager(dists.Sequential([5.0, 4.0, 8.0, 9.0]), max_chanels=1)
sched1 = RepairedFailureSchedule(
    failure_dist=dists.Sequential([2.0, 8.0]),
    repair_mgr=manager,
    preemption="reroute",
)
sched1.srv_id = UUID("00000000-0000-0000-0000-000000000001")
sched2 = RepairedFailureSchedule(
    failure_dist=dists.Sequential([3.0, 6.0]),
    repair_mgr=manager,
    preemption="reroute",
)
sched2.srv_id = UUID("00000000-0000-0000-0000-000000000002")

N_schedule = ciw.create_network(
    arrival_distributions=[
        dists.Uniform(lower=7, upper=13),  # Сообщения А -> B
        dists.Uniform(lower=7, upper=13),  # Сообщения B -> A
    ],
    number_of_servers=[sched1, sched2],
    queue_capacities=[float("Inf"), float("Inf")],
    service_distributions=[
        dists.Uniform(lower=7, upper=13),  # Сообщения А -> B
        dists.Uniform(lower=7, upper=13),  # Сообщения B -> A
    ],
    routing=ciw.routing.NetworkRouting(
        # После прохождения каждого из каналов сообщения покидают систему
        routers=[
            ciw.routing.Leave(),
            ciw.routing.Leave(),
        ]
    ),
)


def test_repair_schedule_single():
    Q = ciw.Simulation(N_schedule)
    Q.simulate_until_max_time(max_simulation_time=40.0)

    # node 1
    assert Q.transitive_nodes[0].schedule
    assert isinstance(Q.transitive_nodes[0].schedule, RepairedFailureSchedule)
    assert Q.transitive_nodes[0].schedule.start_dates == [0.0, 7.0, 23.0, 37.0]
    assert Q.transitive_nodes[0].schedule.failure_dates == [2.0, 15.0, 25.0]
    assert Q.transitive_nodes[0].schedule.repair_start_date == [2.0, 15.0, 32.0]
    print("start:", Q.transitive_nodes[0].schedule.start_dates)
    print("fail:", Q.transitive_nodes[0].schedule.failure_dates)
    print("repair_start:", Q.transitive_nodes[0].schedule.repair_start_date)

    # node 2
    assert Q.transitive_nodes[1].schedule
    assert isinstance(Q.transitive_nodes[1].schedule, RepairedFailureSchedule)
    assert Q.transitive_nodes[1].schedule.start_dates == [0.0, 11.0, 32.0]
    assert Q.transitive_nodes[1].schedule.failure_dates == [3.0, 17.0, 35.0]
    assert Q.transitive_nodes[1].schedule.repair_start_date == [7.0, 23.0, 37.0]
    print("start:", Q.transitive_nodes[1].schedule.start_dates)
    print("fail:", Q.transitive_nodes[1].schedule.failure_dates)
    print("repair_start:", Q.transitive_nodes[1].schedule.repair_start_date)
