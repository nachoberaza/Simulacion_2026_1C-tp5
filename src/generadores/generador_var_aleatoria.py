"""
Generador de Variables Aleatorias
Usa configs de IA separados por turno (ia_config_maniana/tarde/noche.json)
"""

import random
from dominio.enums import NivelUrgencia, Turno
from generadores.generador_IA import cargar_generador_desde_json as cargar_ia
from generadores.generador_triage import cargar_generador_desde_json as cargar_triage
from generadores.generador_tiempo_atencion import cargar_generador_desde_json as cargar_tiempo

# Mapeo Turno del dominio → clave de archivo
TURNO_A_CLAVE = {
    Turno.MANIANA: "maniana",
    Turno.TARDE:   "tarde",
    Turno.NOCHE:   "noche",
}


class GeneradorVariablesAleatorias:

    def __init__(self):
        # Un generador de IA por turno
        self._gen_ia = {
            Turno.MANIANA: cargar_ia("maniana"),
            Turno.TARDE:   cargar_ia("tarde"),
            Turno.NOCHE:   cargar_ia("noche"),
        }
        self._gen_triage = cargar_triage()
        self._gen_tiempo = cargar_tiempo()

    # ------------------------------------------------------------------
    # INTERVALO ENTRE ARRIBOS — depende del turno
    # ------------------------------------------------------------------

    def generar_intervalo_arribo(self, turno: Turno) -> float:
        return self._gen_ia[turno].generar()

    # ------------------------------------------------------------------
    # NIVEL DE URGENCIA (TRIAGE)
    # ------------------------------------------------------------------

    def generar_nivel_urgencia(self, turno: Turno) -> NivelUrgencia:
        return self._gen_triage.generar(turno)

    # ------------------------------------------------------------------
    # TIEMPO DE ATENCIÓN
    # ------------------------------------------------------------------

    def generar_tiempo_atencion(self) -> float:
        return self._gen_tiempo.generar()

    # ------------------------------------------------------------------
    # PROBABILIDAD DE ABANDONO / R1
    # ------------------------------------------------------------------

    def generar_probabilidad_abandono(self) -> float:
        return random.random()