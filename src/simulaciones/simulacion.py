import os
import sys
from collections import deque

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dominio.enums import NivelUrgencia, Turno
from dominio.paciente import Paciente
from generadores.generador_var_aleatoria import GeneradorVariablesAleatorias

# ---------------------------------------------------------------------------
HV = float("inf")  # Hora Vacía


class SimulacionHospital:

    def __init__(self, tiempo_fin: float, npe: int, npc: int, turno_actual: Turno, escenario: str):

        self.TF = tiempo_fin
        self.turno_actual = turno_actual
        self.escenario = escenario
        self.gen = GeneradorVariablesAleatorias(escenario, debug=True)

        # -- Reloj --
        self.T = 0.0

        # -- Arrays TPSalida: HV = médico libre --
        self.TPSe: list[float] = [HV] * npe  # especialistas
        self.TPSc: list[float] = [HV] * npc  # clínicos

        # -- Primera llegada --
        self.TPLL: float = self.T + self.gen.generar_intervalo_arribo(self.turno_actual)

        # -- Colas --
        self.cola_especialistas: deque[Paciente] = deque()
        self.cola_clinicos: deque[Paciente] = deque()

        # -- Estado --
        self.NSE = 0  # pacientes actualmente en cola especialistas
        self.NSC = 0  # pacientes actualmente en cola clínicos

        # -- Acumuladores (variables del diagrama) --
        self.STSe = 0.0
        self.STSc = 0.0
        self.STLLe = 0.0
        self.STLLc = 0.0
        self.SEe = 0.0
        self.SEc = 0.0
        self.NEncoladosE = 0
        self.NEncoladosC = 0
        self.NTe = 0
        self.NTc = 0
        self.PD = 0
        self.NAb = 0

        self._id_paciente = 0

    # =========================================================================
    # HELPERS
    # =========================================================================

    def _Pe(self) -> int:
        return len(self.TPSe)

    def _Pc(self) -> int:
        return len(self.TPSc)

    def _min_TPSe(self) -> float:
        return min(self.TPSe) if self.TPSe else HV

    def _min_TPSc(self) -> float:
        return min(self.TPSc) if self.TPSc else HV

    def _idx_min_TPSe(self) -> int:
        return self.TPSe.index(self._min_TPSe())

    def _idx_min_TPSc(self) -> int:
        return self.TPSc.index(self._min_TPSc())

    def _medico_libre_especialista(self) -> int:
        """Retorna índice del primer especialista libre (TPSe == HV), o -1."""
        for i, t in enumerate(self.TPSe):
            if t == HV:
                return i
        return -1

    def _medico_libre_clinico(self) -> int:
        """Retorna índice del primer clínico libre (TPSc == HV), o -1."""
        for j, t in enumerate(self.TPSc):
            if t == HV:
                return j
        return -1

    def _nuevo_paciente(self) -> Paciente:
        self._id_paciente += 1
        nivel = self.gen.generar_nivel_urgencia(self.turno_actual)
        p = Paciente(
            id_paciente=self._id_paciente,
            tiempo_llegada=self.T,
            nivel_urgencia=nivel,
        )
        p.tiempo_inicio_espera = self.T
        return p

    def _debe_abandonar(self, longitud_cola: int) -> bool:
        """
        25% abandona si cola > 5.
        Del resto, 45% abandona si cola > 10.
        """
        if longitud_cola > 5:
            if self.gen.generar_probabilidad_abandono() < 0.25:
                return True
            if longitud_cola > 10:
                if self.gen.generar_probabilidad_abandono() < 0.45:
                    return True
        return False

    def _insertar_con_prioridad(self, cola: deque, paciente: Paciente):
        """
        FIFO con prioridad:
        Urgentes (NIVEL_1, NIVEL_2) van delante de los no-urgentes,
        pero detrás de los urgentes que ya estaban en la cola.
        """
        es_urgente = paciente.nivel_urgencia in (
            NivelUrgencia.NIVEL_1,
            NivelUrgencia.NIVEL_2,
        )
        if not es_urgente:
            cola.append(paciente)
            return

        lista = list(cola)
        pos = 0
        for k, p in enumerate(lista):
            if p.nivel_urgencia in (NivelUrgencia.NIVEL_1, NivelUrgencia.NIVEL_2):
                pos = k + 1
        lista.insert(pos, paciente)
        cola.clear()
        cola.extend(lista)

    # =========================================================================
    # EVENTO: LLEGADA
    # =========================================================================

    def _procesar_llegada(self):
        # T = TPLL
        self.T = self.TPLL

        # Generar próxima llegada
        self.TPLL = self.T + self.gen.generar_intervalo_arribo(self.turno_actual)

        # Generar paciente
        paciente = self._nuevo_paciente()

        # R1 > 0.55 → Especialista | R1 <= 0.55 → Clínico
        r1 = self.gen.generar_probabilidad_abandono()#?????

        if r1 > 0.55:
            self._llegada_especialista(paciente)
        else:
            self._llegada_clinico(paciente)

    # ------------------------------------------------------------------
    # Rama ESPECIALISTA
    # ------------------------------------------------------------------

    def _llegada_especialista(self, paciente):
        nu = paciente.nivel_urgencia
        i = self._medico_libre_especialista()

        if nu == NivelUrgencia.NIVEL_1:
            if i >= 0: # hay uno libre
                self.STLLe += self.T  # ← solo si es atendido
                ta = self.gen.generar_tiempo_atencion()
                self.NSE += 1
                self.NTe += 1
                self.TPSe[i] = self.T + ta
            else:
                self.PD += 1
        else:
            if i >= 0:
                self.STLLe += self.T  # ← solo si es atendido
                ta = self.gen.generar_tiempo_atencion()
                self.NSE += 1
                self.NTe += 1
                self.TPSe[i] = self.T + ta
            else:
                if self._debe_abandonar(self.NSE):
                    self.NAb += 1
                    return
                self.STLLe += self.T 
                paciente.tiempo_inicio_espera = self.T
                self._insertar_con_prioridad(self.cola_especialistas, paciente)
                self.NSE += 1
                self.NEncoladosE += 1

    # ------------------------------------------------------------------
    # Rama CLÍNICO
    # ------------------------------------------------------------------

    def _llegada_clinico(self, paciente: Paciente):

        nu = paciente.nivel_urgencia
        j = self._medico_libre_clinico()

        if nu == NivelUrgencia.NIVEL_1:
            if j >= 0:
                self.STLLc += self.T  # solo si es atendido directo
                ta = self.gen.generar_tiempo_atencion()
                self.NSC += 1
                self.NTc += 1

                self.TPSc[j] = self.T + ta
            else:
                self.PD += 1
        else:
            if j >= 0:
                self.STLLc += self.T  # solo si es atendido directo
                ta = self.gen.generar_tiempo_atencion()
                self.NSC += 1
                self.NTc += 1                
                #self.NEncoladosC += 1
                self.TPSc[j] = self.T + ta
            else:
                if self._debe_abandonar(self.NSC):
                    self.NAb += 1
                    return
                self.STLLc += self.T  # solo si es atendido directo
                paciente.tiempo_inicio_espera = self.T
                self._insertar_con_prioridad(self.cola_clinicos, paciente)
                self.NSC += 1
                self.NEncoladosC += 1

    # =========================================================================
    # EVENTO: SALIDA CLÍNICO
    # =========================================================================

    def _procesar_salida_clinico(self, j: int):
        self.T = self.TPSc[j]
        self.STSc += self.T
        self.NSC -= 1

        if self.NSC >= self._Pc():
            paciente = self.cola_clinicos.popleft()
            Ec = self.T - paciente.tiempo_inicio_espera
            self.SEc += Ec
            #self.STLLc += paciente.tiempo_llegada  # ← llegada real del encolado
            ta = self.gen.generar_tiempo_atencion()
            self.NTc += 1
            self.TPSc[j] = self.T + ta
        else:
            self.TPSc[j] = HV

    # =========================================================================
    # EVENTO: SALIDA ESPECIALISTA
    # =========================================================================

    def _procesar_salida_especialista(self, i):
        self.T = self.TPSe[i]
        self.STSe += self.T
        self.NSE -= 1

        if self.NSE >= self._Pe():
            paciente = self.cola_especialistas.popleft()
            Ee = self.T - paciente.tiempo_inicio_espera
            self.SEe += Ee
            #self.STLLe += paciente.tiempo_llegada  # ← tiempo de llegada real
            ta = self.gen.generar_tiempo_atencion()
            self.NTe += 1
            self.TPSe[i] = self.T + ta
        else:
            self.TPSe[i] = HV

    # =========================================================================
    # LOOP PRINCIPAL — sigue el diagrama exactamente
    # =========================================================================

    def correr(self):
        """
        CI → A
        A  → menor TPSe(i), menor TPSc(j)
           → TPLL <= min(TPSe, TPSc)?
               SÍ  → llegada
               NO  → salida clínico o especialista
           → T <= TF?
               SÍ  → NSE==0 y NSC==0? → fin / volver a A
               NO  → volver a A
        """

        iteracion = 0
        while True:

            iteracion += 1

            # Cada 1000 iteraciones imprime el estado
            if iteracion % 100000 == 0:
                print(
                    f"  [iter {iteracion}] T={self.T:.1f} | TPLL={self.TPLL:.1f} | NSE={self.NSE} | NSC={self.NSC} | NTe={self.NTe} | NTc={self.NTc}")

            # Calcular menores TPS (pasos iniciales del diagrama)
            min_TPSe = self._min_TPSe()
            min_TPSc = self._min_TPSc()
            min_TPS = min(min_TPSe, min_TPSc)

            # ── CORTE: no hay nada que procesar ──────────────────────────
            if self.TPLL == HV and min_TPS == HV:
                break
            # ── LLEGADA o SALIDA ──────────────────────────────────────────
            if self.TPLL <= min_TPS:
                # SÍ, llegada
                if self.TPLL <= self.TF:
                    self._procesar_llegada()
                else:
                    self.TPLL = HV  # no llegan más pacientes tras TF

            else:
                # NO, salida
                if min_TPS == HV:
                    break  # no hay más eventos

                # TPSc(i) <= TPSe(i) → salida clínico; si no → salida especialista
                if min_TPSc <= min_TPSe:
                    self._procesar_salida_clinico(self._idx_min_TPSc())
                else:
                    self._procesar_salida_especialista(self._idx_min_TPSe())

            # ── Condición de fin del diagrama ─────────────────────────────
            if self.T > self.TF:
                if self.NSE == 0 and self.NSC == 0:
                    break  # colas vacías → terminar
                else:
                    self.TPLL = HV  # seguir vaciando colas

    # =========================================================================
    # RESULTADOS — bloque final del diagrama
    # =========================================================================

    def obtener_resultados(self) -> dict:
        """
        TPEC = SEc  / NEncoladosC
        TPEE = SEe  / NEncoladosE
        PPSe = (STSe - STLLe) / NTe
        PPSc = (STSc - STLLc) / NTc
        """

        print(f"\n--- DEBUG ACUMULADORES ---")
        print(f"STSe={self.STSe:.2f}  STLLe={self.STLLe:.2f}  NTe={self.NTe}  NEncoladosE={self.NEncoladosE}")
        print(f"STSc={self.STSc:.2f}  STLLc={self.STLLc:.2f}  NTc={self.NTc}  NEncoladosC={self.NEncoladosC}")
        print(f"SEe={self.SEe:.2f}  SEc={self.SEc:.2f}")
        print(f"--------------------------\n")

        TPEE = self.SEe / self.NEncoladosE if self.NEncoladosE > 0 else 0.0
        TPEC = self.SEc / self.NEncoladosC if self.NEncoladosC > 0 else 0.0
        PPSe = (self.STSe - self.STLLe) / self.NTe if self.NTe > 0 else 0.0
        PPSc = (self.STSc - self.STLLc) / self.NTc if self.NTc > 0 else 0.0

        total = self.NTe + self.NTc + self.PD + self.NAb
        PA = (self.NAb / total * 100) if total > 0 else 0.0

        return {
            "turno": self.turno_actual.name,
            "escenario": self.escenario,
            "npe": self._Pe(),
            "npc": self._Pc(),
            "tpe_especialista": round(TPEE, 4),
            "tpe_clinico": round(TPEC, 4),
            "tpps_especialista": round(PPSe, 4),
            "tpps_clinico": round(PPSc, 4),
            "porcentaje_abandono": round(PA, 2),
            "pacientes_derivados": self.PD,
            "atendidos_especialista": self.NTe,
            "atendidos_clinico": self.NTc,
            "abandonos": self.NAb,
            "total_ingresados": total,
        }
