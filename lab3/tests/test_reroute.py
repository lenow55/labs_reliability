from unittest.mock import MagicMock

import pytest
from ciw import Simulation
from ciw.exit_node import ExitNode
from ciw.individual import Individual
from ciw.node import Node
from reroute import (  # pyright: ignore[reportImplicitRelativeImport]
    ReservRerouting,
)


@pytest.fixture
def mock_simulation():
    # Создаем поддельную симуляцию с нодами
    sim = MagicMock(spec=Simulation)

    # Нода для обычного next_node
    node_to = MagicMock(spec=Node)

    # Нода для rerouting
    node_reroute = MagicMock(spec=Node)
    node_reroute.number_of_individuals = 0
    node_reroute.node_capacity = 2
    node_reroute.write_baulking_or_rejection_record = MagicMock()
    node_reroute.schedule = None

    # "Exit" нода
    exit_node = MagicMock(spec=ExitNode)

    # Заполняем список нод
    sim.nodes = [node_to, node_reroute, exit_node]
    return sim


@pytest.fixture
def individual():
    return MagicMock(spec=Individual)


def test_next_node_returns_correct_node(mock_simulation, individual):
    router = ReservRerouting(to=0, reroute_to=1)
    router.simulation = mock_simulation

    result = router.next_node(individual)
    assert result == mock_simulation.nodes[0]


def test_next_node_for_rerouting_when_space_available(mock_simulation, individual):
    router = ReservRerouting(to=0, reroute_to=1)
    router.simulation = mock_simulation

    mock_simulation.nodes[1].number_of_individuals = 1
    mock_simulation.nodes[1].node_capacity = 2

    result = router.next_node_for_rerouting(individual)
    mock_simulation.nodes[1].write_baulking_or_rejection_record.assert_not_called()
    assert result == mock_simulation.nodes[1]


def test_next_node_for_rerouting_when_full(mock_simulation, individual):
    router = ReservRerouting(to=0, reroute_to=1)
    router.simulation = mock_simulation

    mock_simulation.nodes[1].number_of_individuals = 2
    mock_simulation.nodes[1].node_capacity = 2

    result = router.next_node_for_rerouting(individual)
    assert result == mock_simulation.nodes[-1]
    mock_simulation.nodes[1].write_baulking_or_rejection_record.assert_called_once_with(
        individual, record_type="rejection"
    )


def test_next_node_for_rerouting_when_invalid_node(mock_simulation, individual):
    router = ReservRerouting(to=0, reroute_to=1)
    router.simulation = mock_simulation

    mock_simulation.nodes[1] = "not a node"  # подделка, не Node
    result = router.next_node_for_rerouting(individual)
    assert result == mock_simulation.nodes[-1]
