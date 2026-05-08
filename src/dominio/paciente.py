from dataclasses import dataclass

@dataclass
class Paciente:

    id_paciente: int
    tiempo_llegada: float
    nivel_urgencia: NivelUrgencia

    tiempo_inicio_atencion: float = None
    tiempo_salida: float = None

    @property
    def tipo_paciente(self):

        if self.nivel_urgencia == NivelUrgencia.NIVEL_4:
            return TipoPaciente.CLINICO

        return TipoPaciente.ESPECIALISTA
