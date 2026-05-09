from dataclasses import dataclass, field

from dominio.enums import TipoEvento
from dominio.paciente import Paciente


@dataclass(order=True)
class Evento:

    tiempo: float
    tipo: TipoEvento = field(compare=False)
    paciente: Paciente = field(default=None, compare=False)
