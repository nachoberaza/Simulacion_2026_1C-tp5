# =============================================================================
# GENERADOR DE VARIABLES ALEATORIAS
# =============================================================================
# Interfaz única que usa la simulación para obtener todos los valores aleatorios.
# Conecta los generadores reales cargados desde sus JSON de configuración.
#
# Flujo de uso:
#   1. Correr generador_IA.py           → genera distribuciones/ia_config.json
#   2. Correr generador_triage.py       → genera distribuciones/triage_config.json
#   3. Correr generador_tiempo_atencion.py → genera distribuciones/tiempo_atencion_config.json
#   4. La simulación instancia este objeto y llama a sus métodos
# =============================================================================

import random
from dominio.enums import NivelUrgencia, Turno

from generadores.generador_IA import cargar_generador_desde_json as cargar_ia
from generadores.generador_triage import cargar_generador_desde_json as cargar_triage
from generadores.generador_tiempo_atencion import cargar_generador_desde_json as cargar_tiempo

# Paths a los JSON generados por cada generador
PATH_IA             = "../distribuciones/ia_config.json"
PATH_TRIAGE         = "../distribuciones/triage_config.json"
PATH_TIEMPO_ATENCION = "../distribuciones/tiempo_atencion_config.json"


class GeneradorVariablesAleatorias:

    def __init__(self):
        self._gen_ia      = cargar_ia(PATH_IA)
        self._gen_triage  = cargar_triage(PATH_TRIAGE)
        self._gen_tiempo  = cargar_tiempo(PATH_TIEMPO_ATENCION)

    # ------------------------------------------------------------------
    # INTERVALO ENTRE ARRIBOS
    # ------------------------------------------------------------------

    def generar_intervalo_arribo(self) -> float:
        """
        Genera el intervalo entre llegadas sucesivas de pacientes (minutos).
        Usa la FDP ajustada en generador_IA.py.
        """
        return self._gen_ia.generar()

    # ------------------------------------------------------------------
    # NIVEL DE URGENCIA (TRIAGE)
    # ------------------------------------------------------------------

    def generar_nivel_urgencia(self, turno: Turno) -> NivelUrgencia:
        """
        Genera el nivel de urgencia (triage) del paciente según el turno actual.
        Usa proporciones empíricas por turno ajustadas en generador_triage.py.

        Parámetros
        ----------
        turno : Turno
            Turno actual del sistema (Turno.MANIANA, TARDE o NOCHE).
        """
        return self._gen_triage.generar(turno)

    # ------------------------------------------------------------------
    # TIEMPOS DE ATENCIÓN
    # ------------------------------------------------------------------

    def generar_tiempo_atencion_especialista(self) -> float:
        """
        Genera un tiempo de atención para especialista (minutos).
        Usa la FDP ajustada en generador_tiempo_atencion.py.
        """
        return self._gen_tiempo.generar_especialista()

    def generar_tiempo_atencion_clinico(self) -> float:
        """
        Genera un tiempo de atención clínico (minutos).
        Usa la FDP ajustada en generador_tiempo_atencion.py.
        """
        return self._gen_tiempo.generar_clinico()

    # ------------------------------------------------------------------
    # PROBABILIDAD DE ABANDONO
    # ------------------------------------------------------------------

    def generar_probabilidad_abandono(self) -> float:
        """
        Genera un número uniforme [0, 1) para evaluar abandono.
        La simulación lo compara contra los umbrales definidos en el enunciado
        (25% si cola > 5, 45% si cola > 10).
        """
        return random.random()
