# =========================================================
# ENUMS
# =========================================================
from enum import Enum


class TipoPaciente(Enum):
    ESPECIALISTA = 1
    CLINICO = 2


class NivelUrgencia(Enum):
    NIVEL_1 = 1
    NIVEL_2 = 2
    NIVEL_3 = 3
    NIVEL_4 = 4


class TipoEvento(Enum):
    LLEGADA = 1
    SALIDA_ESPECIALISTA = 2
    SALIDA_CLINICO = 3
    CAMBIO_TURNO = 4


class Turno(Enum):
    MANIANA = 1
    TARDE = 2
    NOCHE = 3
