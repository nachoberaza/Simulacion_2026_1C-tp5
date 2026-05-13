"""
Generador de Variables Aleatorias
Usa configs de IA separados por turno (ia_config_maniana/tarde/noche.json)
"""

import random
from dominio.enums import NivelUrgencia, Turno
from generadores.generador_IA import cargar_generador_desde_json as cargar_ia
from generadores.generador_triage import cargar_generador_desde_json as cargar_triage
from generadores.generador_tiempo_atencion import cargar_generador_desde_json as cargar_tiempo


class GeneradorVariablesAleatorias:

    def __init__(self, escenario: str, debug=False):
        self.debug = debug

        # Un generador IA por turno
        self._gen_ia = {
            Turno.MANIANA: cargar_ia("maniana", escenario),
            Turno.TARDE:   cargar_ia("tarde", escenario),
            Turno.NOCHE:   cargar_ia("noche", escenario),
        }

        self._gen_triage = cargar_triage(escenario)
        self._gen_tiempo = cargar_tiempo()

    # ==========================================================
    # Helper para imprimir logs
    # ==========================================================

    def _log(self, mensaje):
        if self.debug:
            print(mensaje)

    # ==========================================================
    # INTERVALO ENTRE ARRIBOS
    # ==========================================================

    def generar_intervalo_arribo(self, turno: Turno) -> float:
        valor = self._gen_ia[turno].generar()

        # Factor de congestión
        factor_congestion = 0.18

        valor = valor * factor_congestion

        #print(f"[IA] turno={turno.name:<8} original={valor/factor_congestion:.2f}  ajustado={valor:.2f}")
        
        return valor

    # ==========================================================
    # NIVEL DE URGENCIA
    # ==========================================================

    def generar_nivel_urgencia(self, turno: Turno) -> NivelUrgencia:
        nivel = self._gen_triage.generar(turno)

        #self._log(
        #    f"[TRIAGE] turno={turno.name:<8} "
        #    f"nivel={nivel.name}"
        #)

        return nivel

    # ==========================================================
    # TIEMPO DE ATENCIÓN
    # ==========================================================

    def generar_tiempo_atencion(self) -> float:
        valor = self._gen_tiempo.generar()

        #self._log(
        #    f"[TA] valor={valor:.2f}"
        #)

        return valor

    # ==========================================================
    # RANDOM UNIFORME (routing / abandono)
    # ==========================================================

    def generar_probabilidad_abandono(self) -> float:
        valor = random.random()

        self._log(
            f"[RAND] valor={valor:.4f}"
        )

        return valor