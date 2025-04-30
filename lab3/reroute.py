from ciw import routing, Simulation
from ciw.individual import Individual
from ciw.node import Node


class ReservRerouting(routing.NodeRouting):
    simulation: Simulation

    def __init__(self, to: int, reroute_to: int) -> None:
        """
        Initialises the routing object.

        Takes:
            - to: a the node index to send to.
        """
        self.to: int = to
        self.reroute_to: int = reroute_to

    def next_node(self, ind: Individual):
        """
        Chooses the node 'to' with probability 1.
        """
        return self.simulation.nodes[self.to]

    def next_node_for_rerouting(self, ind: Individual):
        """
        Послать посетителя в указанную ноду, если
        у обработчика есть место
        Иначе на выход
        """
        next_node = self.simulation.nodes[self.reroute_to]
        if not isinstance(next_node, Node):
            return self.simulation.nodes[-1]
        if next_node.number_of_individuals >= next_node.node_capacity:
            next_node.write_baulking_or_rejection_record(ind, record_type="rejection")
            return self.simulation.nodes[-1]
        else:
            return next_node
