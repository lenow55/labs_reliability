from uuid import UUID
import ciw
from ciw import dists

from custom_schedule import RepairedFailureSchedule  # pyright: ignore[reportImplicitRelativeImport]
from repair_manager import (  # pyright: ignore[reportImplicitRelativeImport]
    RepairManager,
)


manager = RepairManager(dists.Deterministic(5.0), max_chanels=2)
sched1 = RepairedFailureSchedule(
    failure_dist=dists.Sequential([2.0, 8.0]),
    # failure_dist=dists.Sequential([6.0]),
    repair_mgr=manager,
    preemption="reroute",
)
sched1.srv_id = UUID("00000000-0000-0000-0000-000000000001")
sched2 = RepairedFailureSchedule(
    failure_dist=dists.Sequential([3.0, 6.0]),
    # failure_dist=dists.Sequential([6.0]),
    repair_mgr=manager,
    preemption="reroute",
)
sched2.srv_id = UUID("00000000-0000-0000-0000-000000000002")
sched3 = RepairedFailureSchedule(
    failure_dist=dists.Sequential([8.0, 4.0]),
    # failure_dist=dists.Sequential([6.0]),
    repair_mgr=manager,
    preemption="reroute",
)
sched3.srv_id = UUID("00000000-0000-0000-0000-000000000003")

N_schedule = ciw.create_network(
    arrival_distributions=[
        dists.Uniform(lower=7, upper=13),
        dists.Uniform(lower=7, upper=13),
        dists.Uniform(lower=7, upper=13),
    ],
    number_of_servers=[sched1, sched2, sched3],
    queue_capacities=[float("Inf"), float("Inf"), float("Inf")],
    service_distributions=[
        dists.Uniform(lower=7, upper=13),
        dists.Uniform(lower=7, upper=13),
        dists.Uniform(lower=7, upper=13),
    ],
    routing=ciw.routing.NetworkRouting(
        # После прохождения каждого из каналов сообщения покидают систему
        routers=[
            ciw.routing.Leave(),
            ciw.routing.Leave(),
            ciw.routing.Leave(),
        ]
    ),
)


def test_repair_schedule_double():
    Q = ciw.Simulation(N_schedule)
    Q.simulate_until_max_time(max_simulation_time=50.0)

    assert Q.transitive_nodes[0].schedule
    assert isinstance(Q.transitive_nodes[0].schedule, RepairedFailureSchedule)
    assert Q.transitive_nodes[1].schedule
    assert isinstance(Q.transitive_nodes[1].schedule, RepairedFailureSchedule)
    assert Q.transitive_nodes[2].schedule
    assert isinstance(Q.transitive_nodes[2].schedule, RepairedFailureSchedule)

    print("node1")
    print("start:", Q.transitive_nodes[0].schedule.start_dates)
    print("fail:", Q.transitive_nodes[0].schedule.failure_dates)
    print("repair_start:", Q.transitive_nodes[0].schedule.repair_start_date)

    print("node2")
    print("start:", Q.transitive_nodes[1].schedule.start_dates)
    print("fail:", Q.transitive_nodes[1].schedule.failure_dates)
    print("repair_start:", Q.transitive_nodes[1].schedule.repair_start_date)

    print("node3")
    print("start:", Q.transitive_nodes[2].schedule.start_dates)
    print("fail:", Q.transitive_nodes[2].schedule.failure_dates)
    print("repair_start:", Q.transitive_nodes[2].schedule.repair_start_date)

    # node 1
    assert Q.transitive_nodes[0].schedule.start_dates in [
        [
            0.0,
            7.0,
            20.0,
            27.0,
            42.0,
        ],
        [0.0, 7.0, 20.0, 29.0, 42.0],
        [0.0, 7.0, 20.0, 27.0, 40.0, 47.0],
    ]
    assert Q.transitive_nodes[0].schedule.failure_dates in [
        [
            2.0,
            15.0,
            22.0,
            35.0,
            44.0,
        ],
        [2.0, 15.0, 22.0, 37.0, 44.0],
        [2.0, 15.0, 22.0, 35.0, 42.0],
    ]
    assert Q.transitive_nodes[0].schedule.repair_start_date in [
        [
            2.0,
            15.0,
            22.0,
            37.0,
            46.0,
        ],
        [
            2.0,
            15.0,
            24.0,
            37.0,
            46.0,
        ],
        [2.0, 15.0, 22.0, 35.0, 42.0],
    ]

    # node 2
    assert Q.transitive_nodes[1].schedule.start_dates in [
        [
            0.0,
            8.0,
            19.0,
            29.0,
            40.0,
            48.0,
        ],
        [
            0.0,
            8.0,
            19.0,
            27.0,
            38.0,
            47.0,
        ],
        [0.0, 8.0, 19.0, 27.0, 38.0, 46.0],
        [0.0, 8.0, 19.0, 29.0, 42.0],
    ]
    assert Q.transitive_nodes[1].schedule.failure_dates in [
        [
            3.0,
            14.0,
            22.0,
            35.0,
            43.0,
        ],
        [3.0, 14.0, 22.0, 33.0, 41.0],
        [3.0, 14.0, 22.0, 35.0, 45.0],
    ]
    assert Q.transitive_nodes[1].schedule.repair_start_date in [
        [
            3.0,
            14.0,
            24.0,
            35.0,
            43.0,
        ],
        [
            3.0,
            14.0,
            22.0,
            33.0,
            42.0,
        ],
        [3.0, 14.0, 22.0, 33.0, 41.0],
        [3.0, 14.0, 24.0, 37.0, 46.0],
    ]

    # node 3
    assert Q.transitive_nodes[2].schedule.start_dates in [
        [0.0, 13.0, 24.0, 37.0, 46.0],
        [0.0, 13.0, 24.0, 37.0, 47.0],
    ]
    assert Q.transitive_nodes[2].schedule.failure_dates == [8.0, 17.0, 32.0, 41.0]
    assert Q.transitive_nodes[2].schedule.repair_start_date in [
        [8.0, 19.0, 32.0, 41.0],
        [8.0, 19.0, 32.0, 42.0],
    ]
