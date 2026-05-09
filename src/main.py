import csv
import os
from simulaciones.simulacion import SimulacionHospital
from dominio.enums import Turno

TIEMPO_FIN = 14040  # 8 horas por turno, en minutos
OUTPUT_PATH = "./resultados.csv"

escenarios = [
    {"turno": Turno.MANIANA, "npe": 2, "npc": 1},
    {"turno": Turno.MANIANA, "npe": 3, "npc": 1},
    {"turno": Turno.TARDE,   "npe": 2, "npc": 1},
    {"turno": Turno.TARDE,   "npe": 3, "npc": 1},
    {"turno": Turno.NOCHE,   "npe": 2, "npc": 1},
    {"turno": Turno.NOCHE,   "npe": 3, "npc": 1},
]

if __name__ == "__main__":

    resultados = []

    for escenario in escenarios:
        simulacion = SimulacionHospital(
            tiempo_fin=TIEMPO_FIN,
            npe=escenario["npe"],
            npc=escenario["npc"],
            turno_actual=escenario["turno"]
        )
        simulacion.correr()
        resultado = simulacion.obtener_resultados()
        resultados.append(resultado)
        print(f"OK — Turno: {resultado['turno']} | NPe: {resultado['npe']} | NPc: {resultado['npc']}")

    # Persistir en CSV
    campos = list(resultados[0].keys())

    with open(OUTPUT_PATH, "x", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        writer.writerows(resultados)

    print(f"\nResultados guardados en: {os.path.abspath(OUTPUT_PATH)}")