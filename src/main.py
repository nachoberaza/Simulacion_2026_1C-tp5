
from simulaciones.simulacion import SimulacionHospital

# =========================================================
# SIMULACION
# =========================================================

if __name__ == "__main__":

    simulacion = SimulacionHospital(
        tiempo_fin=1000
    )

    simulacion.correr()