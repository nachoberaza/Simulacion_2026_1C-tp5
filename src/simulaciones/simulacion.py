import heapq
from collections import deque

from dominio.enums import Turno, TipoEvento, TipoPaciente, NivelUrgencia
from dominio.evento import Evento
from dominio.paciente import Paciente
from dominio.recurso_medico import RecursoMedico
from generadores.generador_var_aleatoria import GeneradorVariablesAleatorias


class SimulacionHospital:

    def __init__(self, tiempo_fin, npe, npc, turno_actual):

        self.tiempo_actual = 0
        self.tiempo_fin = tiempo_fin

        self.generador_va = GeneradorVariablesAleatorias()

        # -------------------------------------------------
        # TURNO ACTUAL
        # -------------------------------------------------

        self.turno_actual = turno_actual

        # -------------------------------------------------
        # RECURSOS
        # -------------------------------------------------

        self.especialistas = RecursoMedico(cantidad=npe)
        self.clinicos = RecursoMedico(cantidad=npc)

        # -------------------------------------------------
        # COLAS
        # -------------------------------------------------

        self.cola_especialistas = deque()
        self.cola_clinicos = deque()

        # -------------------------------------------------
        # LISTA EVENTOS FUTUROS
        # -------------------------------------------------

        self.lista_eventos = []

        # -------------------------------------------------
        # CONTADORES
        # -------------------------------------------------

        self.id_paciente = 0

        self.pacientes_derivados = 0
        self.pacientes_abandonan = 0

        self.tiempo_espera_especialista = 0
        self.tiempo_espera_clinico = 0

        self.pacientes_atendidos_especialista = 0
        self.pacientes_atendidos_clinico = 0

        self.tiempo_permanencia_especialista = 0
        self.tiempo_permanencia_clinico = 0

    # =====================================================
    # INICIALIZACION
    # =====================================================

    def inicializar(self):

        self.programar_proxima_llegada()

    # =====================================================
    # EVENTOS
    # =====================================================

    def programar_evento(self, evento):

        heapq.heappush(self.lista_eventos, evento)

    def obtener_proximo_evento(self):

        return heapq.heappop(self.lista_eventos)

    # =====================================================
    # LLEGADAS
    # =====================================================

    def programar_proxima_llegada(self):

        intervalo = self.generador_va.generar_intervalo_arribo()

        tiempo_llegada = self.tiempo_actual + intervalo

        paciente = Paciente(
            id_paciente=self.id_paciente,
            tiempo_llegada=tiempo_llegada,
            nivel_urgencia=self.generador_va.generar_nivel_urgencia(self.turno_actual)
        )

        self.id_paciente += 1

        evento = Evento(
            tiempo=tiempo_llegada,
            tipo=TipoEvento.LLEGADA,
            paciente=paciente
        )

        self.programar_evento(evento)

    def procesar_llegada(self, evento):

        paciente = evento.paciente

        self.programar_proxima_llegada()

        if paciente.tipo_paciente == TipoPaciente.ESPECIALISTA:
            self.procesar_llegada_especialista(paciente)

        else:
            self.procesar_llegada_clinico(paciente)

    # =====================================================
    # ESPECIALISTAS
    # =====================================================

    def procesar_llegada_especialista(self, paciente):

        if self.especialistas.hay_disponible():

            self.iniciar_atencion_especialista(paciente)

        else:

            # NIVEL 1 NO ESPERA
            if paciente.nivel_urgencia == NivelUrgencia.NIVEL_1:

                self.pacientes_derivados += 1
                return

            # ABANDONO
            if self.debe_abandonar(len(self.cola_especialistas)):

                self.pacientes_abandonan += 1
                return

            # PRIORIDAD
            if paciente.nivel_urgencia == NivelUrgencia.NIVEL_2:

                self.insertar_prioridad_especialista(paciente)

            else:

                self.cola_especialistas.append(paciente)

    def iniciar_atencion_especialista(self, paciente):

        self.especialistas.ocupar()

        paciente.tiempo_inicio_atencion = self.tiempo_actual

        espera = (
            paciente.tiempo_inicio_atencion -
            paciente.tiempo_llegada
        )

        self.tiempo_espera_especialista += espera

        tiempo_atencion = (
            self.generador_va
            .generar_tiempo_atencion_especialista()
        )

        evento_salida = Evento(
            tiempo=self.tiempo_actual + tiempo_atencion,
            tipo=TipoEvento.SALIDA_ESPECIALISTA,
            paciente=paciente
        )

        self.programar_evento(evento_salida)

    def insertar_prioridad_especialista(self, paciente):

        posicion = 0

        for p in self.cola_especialistas:

            if p.nivel_urgencia != NivelUrgencia.NIVEL_2:
                break

            posicion += 1

        self.cola_especialistas.insert(posicion, paciente)

    # =====================================================
    # CLINICOS
    # =====================================================

    def procesar_llegada_clinico(self, paciente):

        if self.clinicos.hay_disponible():

            self.iniciar_atencion_clinico(paciente)

        else:

            if self.debe_abandonar(len(self.cola_clinicos)):

                self.pacientes_abandonan += 1
                return

            self.cola_clinicos.append(paciente)

    def iniciar_atencion_clinico(self, paciente):

        self.clinicos.ocupar()

        paciente.tiempo_inicio_atencion = self.tiempo_actual

        espera = (
            paciente.tiempo_inicio_atencion -
            paciente.tiempo_llegada
        )

        self.tiempo_espera_clinico += espera

        tiempo_atencion = (
            self.generador_va
            .generar_tiempo_atencion_clinico()
        )

        evento_salida = Evento(
            tiempo=self.tiempo_actual + tiempo_atencion,
            tipo=TipoEvento.SALIDA_CLINICO,
            paciente=paciente
        )

        self.programar_evento(evento_salida)

    # =====================================================
    # SALIDAS
    # =====================================================

    def procesar_salida_especialista(self, evento):

        self.pacientes_atendidos_especialista += 1
        evento.paciente.tiempo_salida = self.tiempo_actual
        self.tiempo_permanencia_especialista += (
                evento.paciente.tiempo_salida - evento.paciente.tiempo_llegada
        )

        if len(self.cola_especialistas) > 0:

            paciente = self.cola_especialistas.popleft()

            self.iniciar_atencion_especialista(paciente)

        else:

            self.especialistas.liberar()

    def procesar_salida_clinico(self, evento):

        self.pacientes_atendidos_clinico += 1
        evento.paciente.tiempo_salida = self.tiempo_actual
        self.tiempo_permanencia_clinico += (
                evento.paciente.tiempo_salida - evento.paciente.tiempo_llegada
        )

        if len(self.cola_clinicos) > 0:

            paciente = self.cola_clinicos.popleft()

            self.iniciar_atencion_clinico(paciente)

        else:

            self.clinicos.liberar()

    # =====================================================
    # ABANDONO
    # =====================================================

    def debe_abandonar(self, longitud_cola):

        probabilidad = (
            self.generador_va
            .generar_probabilidad_abandono()
        )

        if longitud_cola > 10:
            return probabilidad <= 0.45

        if longitud_cola > 5:
            return probabilidad <= 0.25

        return False

    # =====================================================
    # LOOP PRINCIPAL
    # =====================================================

    def correr(self):

        self.inicializar()

        while (
            self.lista_eventos and
            self.tiempo_actual < self.tiempo_fin
        ):

            evento = self.obtener_proximo_evento()

            self.tiempo_actual = evento.tiempo

            if evento.tipo == TipoEvento.LLEGADA:

                self.procesar_llegada(evento)

            elif evento.tipo == TipoEvento.SALIDA_ESPECIALISTA:

                self.procesar_salida_especialista(evento)

            elif evento.tipo == TipoEvento.SALIDA_CLINICO:

                self.procesar_salida_clinico(evento)

        self.obtener_resultados()

    # =====================================================
    # RESULTADOS
    # =====================================================

    def obtener_resultados(self):
        promedio_espera_esp = (
            self.tiempo_espera_especialista / self.pacientes_atendidos_especialista
            if self.pacientes_atendidos_especialista > 0 else 0
        )
        promedio_espera_cli = (
            self.tiempo_espera_clinico / self.pacientes_atendidos_clinico
            if self.pacientes_atendidos_clinico > 0 else 0
        )
        promedio_perm_esp = (
            self.tiempo_permanencia_especialista / self.pacientes_atendidos_especialista
            if self.pacientes_atendidos_especialista > 0 else 0
        )
        promedio_perm_cli = (
            self.tiempo_permanencia_clinico / self.pacientes_atendidos_clinico
            if self.pacientes_atendidos_clinico > 0 else 0
        )

        return {
            "turno": self.turno_actual.name,
            "npe": self.especialistas.cantidad_total,
            "npc": self.clinicos.cantidad_total,
            "tpe_especialista": round(promedio_espera_esp, 2),
            "tpe_clinico": round(promedio_espera_cli, 2),
            "tpps_especialista": round(promedio_perm_esp, 2),
            "tpps_clinico": round(promedio_perm_cli, 2),
            "pacientes_derivados": self.pacientes_derivados,
            "pacientes_abandonan": self.pacientes_abandonan,
            "atendidos_especialista": self.pacientes_atendidos_especialista,
            "atendidos_clinico": self.pacientes_atendidos_clinico,
        }
