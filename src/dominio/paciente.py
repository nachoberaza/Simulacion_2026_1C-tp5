from dataclasses import dataclass

from dominio.enums import NivelUrgencia, TipoPaciente


@dataclass
class Paciente:

    id_paciente: int
    tiempo_llegada: float
    nivel_urgencia: NivelUrgencia

    tiempo_inicio_atencion: float = None
    tiempo_salida: float = None
    tiempo_inicio_espera: float = None
    
    @property
    def tipo_paciente(self):

        if self.nivel_urgencia == NivelUrgencia.NIVEL_4:
            return TipoPaciente.CLINICO

        return TipoPaciente.ESPECIALISTA
