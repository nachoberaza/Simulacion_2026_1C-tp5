from collections import deque
import heapq

from dominio.evento import Evento
from dominio.paciente import Paciente
from dominio.recurso_medico import RecursoMedico
from dominio.enums import Turno, TipoEvento, TipoPaciente, NivelUrgencia
from generadores.generador_var_aleatoria import GeneradorVariablesAleatorias
from simulaciones.simulacion import SimulacionHospital

# =========================================================
# SIMULACION
# =========================================================

if __name__ == "__main__":

    simulacion = SimulacionHospital(
        tiempo_fin=1000
    )

    simulacion.correr()