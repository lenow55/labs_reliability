import ciw
from typing import override


class CustomArrivalNode(ciw.ArrivalNode):
    @override
    def __init__(self, simulation, node_bypass_index: int):
        self.node_bypass_index = node_bypass_index
        super().__init__(simulation)

    @override
    def release_individual(self, next_node, next_individual):
        """
        Either rejects the next_individual die to lack of capacity,
        or sends that individual to baulk or not.
        """
        if (next_node.number_of_individuals >= next_node.node_capacity) or (
            self.simulation.number_of_individuals >= self.system_capacity
        ):
            bypass_node = self.simulation.nodes[self.node_bypass_index]
            if (bypass_node.number_of_individuals >= bypass_node.node_capacity) or (
                self.simulation.number_of_individuals >= self.system_capacity
            ):
                self.record_rejection(next_node, next_individual)
                self.simulation.nodes[-1].accept(next_individual, completed=False)
            else:
                self.decide_baulk(
                    self.simulation.nodes[self.node_bypass_index], next_individual
                )
        else:
            self.decide_baulk(next_node, next_individual)