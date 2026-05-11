import csv
import os

from dominio.enums import Turno
from simulaciones.simulacion import SimulacionHospital

TIEMPO_FIN = 480  # 8 horas por turno, en minutos
OUTPUT_PATH = "./resultados.csv"

escenarios = [
    {"turno": Turno.NOCHE, "npe": 1, "npc": 1, "tipo": "saturado"},
    {"turno": Turno.NOCHE, "npe": 1, "npc": 2, "tipo": "optimo"},
    {"turno": Turno.NOCHE, "npe": 2, "npc": 3, "tipo": "ocioso"},
]

if __name__ == "__main__":

    resultados = []

    for escenario in escenarios:
        simulacion = SimulacionHospital(
            tiempo_fin=TIEMPO_FIN,
            npe=escenario['npe'],
            npc=escenario['npc'],
            turno_actual=escenario['turno'],
            escenario=escenario['tipo'],
        )
        simulacion.correr()
        resultado = simulacion.obtener_resultados()
        resultados.append(resultado)
        print(f"OK — Turno: {resultado['turno']} | Escenario: {escenario['tipo']} | NPe: {resultado['npe']} | NPc: {resultado['npc']}")

    # Persistir en CSV
    campos = list(resultados[0].keys())

    with open(OUTPUT_PATH, "x", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        writer.writerows(resultados)

    print(f"\nResultados guardados en: {os.path.abspath(OUTPUT_PATH)}")
