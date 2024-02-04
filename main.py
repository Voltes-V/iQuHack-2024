# This is taken from the example file given by Quandela
# Code done with help from Yi Tan, Aparna Gupta, Barnald. 
import perceval as pcvl
from perceval.components import Circuit, Processor
from perceval.components.unitary_components import PS, BS, PERM
from perceval.components.component_catalog import CatalogItem, AsType
from perceval.components.port import Port, Encoding
import numpy as np

def get_CCZ() -> pcvl.Processor:

    return pcvl.catalog["postprocessed ccz"].build_processor()

class CS180(CatalogItem):

    # based on: https://github.com/Quandela/Perceval/blob/main/perceval/components/core_catalog/heralded_cz.py#L31C1-L31C47
    # apperently an additional factor of 2 should be used
    theta1 = 2*np.pi*54.74/180
    theta2 = 2*np.pi*17.63/180

    def __init__(self):
        super().__init__("CS180")
        self._default_opts['type'] = AsType.PROCESSOR

    def build_circuit(self, **kwargs) -> Circuit:
        return (Circuit(4, name="CS180")
                         .add(0, PS(phi=np.pi))
                         .add(1, PS(phi=np.pi))
                         .add((1, 2), PERM([1, 0]))
                         .add((0, 1), BS.H(theta=self.theta1))
                         .add((2, 3), BS.H(theta=self.theta1))
                         .add((1, 2), PERM([1, 0]))
                         .add((0, 1), BS.H(theta=-self.theta1))
                         .add((2, 3), BS.H(theta=self.theta2)))

    def build_processor(self, **kwargs) -> Processor:
        p = self._init_processor(**kwargs)
        return p.add_port(0, Port(Encoding.DUAL_RAIL, 'qubit')) \
            .add_herald(2, 1) \
            .add_herald(3,1)

class CCZ(CatalogItem):
    # Optimized by creating NOR Gates (Toffoli Gates + X Gates)
    # Not completed

    def __init__(self):
        super().__init__("CCZ")
        self._default_opts['type'] = AsType.PROCESSOR

    def build_circuit(self, **kwargs) -> Circuit:
        return (Circuit(4, name="CCZ")
                         .add(2, CNOT().build_circuit())
                         .add(4, T().build_circuit())  # need adjoint
                         .add((0, 1, 2, 3, 4, 5, 6, 7), PERM([2, 3, 0, 1, 4, 5, 6, 7]))
                         .add(2, CNOT().build_circuit())
                         .add(4, T().build_circuit())
                         .add((0, 1, 2, 3, 4, 5, 6, 7), PERM([2, 3, 0, 1, 4, 5, 6, 7]))
                         .add(2, CNOT().build_circuit())
                         .add(4, T().build_circuit())  # need adjoint
                         .add((0, 1, 2, 3, 4, 5, 6, 7), PERM([2, 3, 0, 1, 4, 5, 6, 7]))
                         .add(2, CNOT().build_circuit())
                         .add(4, T().build_circuit())
                         .add(0, T().build_circuit())
                         .add((0, 1, 2, 3, 4, 5, 6, 7), PERM([4, 5, 2, 3, 0, 1, 6, 7]))
                         .add(2, CNOT().build_circuit())
                         .add(4, T().build_circuit())  # need adjoint
                         .add(2, T().build_circuit())
                         .add(2, CNOT().build_circuit()))

    def build_processor(self, **kwargs) -> Processor:
        p = self._init_processor(**kwargs)
        return p.add_port(0, Port(Encoding.DUAL_RAIL, 'ctrl')) \
                .add_port(2, Port(Encoding.DUAL_RAIL, 'data'))
                
class Knill_CZ(CatalogItem):

    def __init__(self):
        super().__init__("Knill_CZ")
        self._default_opts['type'] = AsType.PROCESSOR

    def build_circuit(self, **kwargs) -> Circuit:
        return (Circuit(4, name="Knill_CZ")
                         .add(0, CS180().build_circuit()))

    def build_processor(self, **kwargs) -> Processor:
        p = self._init_processor(**kwargs)
        return p.add_port(0, Port(Encoding.DUAL_RAIL, 'ctrl')) \
                .add_port(2, Port(Encoding.DUAL_RAIL, 'data'))


ccz = get_CCZ()
cs180 = CS180().build_processor()
knill_cz = Knill_CZ().build_processor()
processor = pcvl.Processor("SLOS", 4)
processor.add(2, pcvl.BS.H())
processor.add(0, knill_cz)
processor.add(0, pcvl.catalog["heralded cz"].build_processor())
processor.add(2, pcvl.BS.H())

pcvl.pdisplay(cs180, recursive=True)

states = {
    pcvl.BasicState([1, 0, 1, 0]): "00",
    pcvl.BasicState([1, 0, 0, 1]): "01",
    pcvl.BasicState([0, 1, 1, 0]): "10",
    pcvl.BasicState([0, 1, 0, 1]): "11"
}

ca = pcvl.algorithm.Analyzer(processor, states)

truth_table = {"00": "00", "01": "01", "10": "11", "11": "10"}
ca.compute(expected=truth_table)

pcvl.pdisplay(ca)
print(f"performance = {pcvl.simple_float(ca.performance)[1]}, fidelity = {ca.fidelity.real}")