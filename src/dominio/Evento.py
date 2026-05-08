from dataclasses import dataclass

@dataclass(order=True)
class Evento:

    tiempo: float
    tipo: TipoEvento = field(compare=False)
    paciente: Paciente = field(default=None, compare=False)
