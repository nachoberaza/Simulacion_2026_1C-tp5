import csv
import os

from dominio.enums import Turno
from simulaciones.simulacion import SimulacionHospital
import matplotlib.pyplot as plt
import numpy as np


def comparar_metricas(resultados):

    turnos = ["MANIANA", "TARDE", "NOCHE"]

    fig, axs = plt.subplots(
        1,
        3,
        figsize=(20, 7),
        facecolor="none"
    )

    colores = {
        "tpe_esp": "#ff6b6b",
        "tpe_cli": "#4dabf7",
        "tpps_esp": "#51cf66",
        "tpps_cli": "#ffd43b"
    }

    texto = "white"
    grid = "#ffffff33"

    # =========================================================
    # ESCALA GLOBAL
    # =========================================================

    max_y = max(
        max(r["tpe_especialista"] for r in resultados),
        max(r["tpe_clinico"] for r in resultados),
        max(r["tpps_especialista"] for r in resultados),
        max(r["tpps_clinico"] for r in resultados),
    )

    max_y *= 1.15

    # =========================================================

    for idx, turno in enumerate(turnos):

        datos_turno = [
            r for r in resultados
            if r["turno"] == turno
        ]

        labels = [
            f"E{r['npe']}-C{r['npc']}"
            for r in datos_turno
        ]

        x = np.arange(len(labels))

        tpe_especialista = [
            r["tpe_especialista"]
            for r in datos_turno
        ]

        tpe_clinico = [
            r["tpe_clinico"]
            for r in datos_turno
        ]

        tpps_especialista = [
            r["tpps_especialista"]
            for r in datos_turno
        ]

        tpps_clinico = [
            r["tpps_clinico"]
            for r in datos_turno
        ]

        width = 0.2

        ax = axs[idx]

        ax.set_facecolor("none")

        bars1 = ax.bar(
            x - 1.5 * width,
            tpe_especialista,
            width,
            label="TPE Especialista",
            color=colores["tpe_esp"]
        )

        bars2 = ax.bar(
            x - 0.5 * width,
            tpe_clinico,
            width,
            label="TPE Clínico",
            color=colores["tpe_cli"]
        )

        bars3 = ax.bar(
            x + 0.5 * width,
            tpps_especialista,
            width,
            label="TPPS Especialista",
            color=colores["tpps_esp"]
        )

        bars4 = ax.bar(
            x + 1.5 * width,
            tpps_clinico,
            width,
            label="TPPS Clínico",
            color=colores["tpps_cli"]
        )

        ax.set_title(
            turno,
            fontsize=14,
            fontweight="bold",
            color=texto
        )

        ax.set_xticks(x)
        ax.set_xticklabels(labels, color=texto)

        ax.set_ylabel(
            "Minutos",
            color=texto
        )

        ax.set_ylim(0, max_y)

        ax.grid(
            axis="y",
            linestyle="--",
            alpha=0.3,
            color=grid
        )

        # COLOR EJES

        ax.tick_params(colors=texto)

        ax.spines["bottom"].set_color(texto)
        ax.spines["left"].set_color(texto)

        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        # =====================================================
        # VALORES ARRIBA DE LAS BARRAS
        # =====================================================

        for bars in [bars1, bars2, bars3, bars4]:

            for bar in bars:

                h = bar.get_height()

                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    h + 1,
                    f"{h:.1f}",
                    ha="center",
                    fontsize=7,
                    rotation=90,
                    color=texto
                )

    # =========================================================
    # LEYENDA
    # =========================================================

    handles, labels = axs[0].get_legend_handles_labels()

    legend = fig.legend(
        handles,
        labels,
        loc="upper center",
        bbox_to_anchor=(0.5, 0.95),
        ncol=4,
        fontsize=10,
        frameon=False
    )

    for text in legend.get_texts():
        text.set_color(texto)

    plt.tight_layout(rect=[0, 0, 1, 0.9])

    plt.savefig(
        "comparacion_metricas.png",
        dpi=250,
        transparent=True,
        bbox_inches="tight"
    )

    plt.close()

    print("Gráfico guardado: comparacion_metricas.png")

def graficar_resultado(resultado):

    fig, axs = plt.subplots(1, 2, figsize=(12, 5))

    # =========================================================
    # GRAFICO 1 -> TIEMPOS
    # =========================================================

    etiquetas_tiempo = [
        "TPE Esp.",
        "TPE Clín.",
        "TPPS Esp.",
        "TPPS Clín."
    ]

    valores_tiempo = [
        resultado["tpe_especialista"],
        resultado["tpe_clinico"],
        resultado["tpps_especialista"],
        resultado["tpps_clinico"],
    ]

    bars = axs[0].barh(
        etiquetas_tiempo,
        valores_tiempo
    )

    axs[0].set_title("Tiempos Promedio")
    axs[0].set_xlabel("Minutos")

    for bar in bars:

        ancho = bar.get_width()

        axs[0].text(
            ancho + 0.5,
            bar.get_y() + bar.get_height() / 2,
            f"{ancho:.2f}",
            va="center"
        )

    # =========================================================
    # GRAFICO 2 -> PORCENTAJES
    # =========================================================

    etiquetas_porcentaje = [
        "% Arrep.",
        "% Deriv."
    ]

    valores_porcentaje = [
        resultado["porcentaje_arrepentimiento"],
        resultado["porcentaje_derivados"]
    ]

    bars = axs[1].bar(
        etiquetas_porcentaje,
        valores_porcentaje
    )

    axs[1].set_title("Porcentajes")
    axs[1].set_ylabel("%")

    for bar in bars:

        alto = bar.get_height()

        axs[1].text(
            bar.get_x() + bar.get_width() / 2,
            alto + 0.3,
            f"{alto:.2f}%",
            ha="center"
        )

    # =========================================================

    fig.suptitle(
        f"Turno: {resultado['turno']} | "
        f"NPe={resultado['npe']} | "
        f"NPc={resultado['npc']}"
    )

    plt.tight_layout()

    nombre = (
        f"grafico_"
        f"{resultado['turno']}_"
        f"NPe{resultado['npe']}_"
        f"NPc{resultado['npc']}.png"
    )

    plt.savefig(nombre, dpi=200)

    plt.close()

    print(f"Gráfico guardado: {nombre}")


def comparar_porcentajes(resultados):

    turnos = ["MANIANA", "TARDE", "NOCHE"]

    fig, axs = plt.subplots(
        1,
        3,
        figsize=(18, 7),
        facecolor="none"
    )

    colores = {
        "arrep": "#ff6b6b",
        "deriv": "#4dabf7"
    }

    texto = "white"
    grid = "#ffffff33"

    # =========================================================
    # ESCALA GLOBAL
    # =========================================================

    max_y = max(
        max(r["porcentaje_arrepentimiento"] for r in resultados),
        max(r["porcentaje_derivados"] for r in resultados),
    )

    max_y *= 1.20

    # =========================================================

    for idx, turno in enumerate(turnos):

        datos_turno = [
            r for r in resultados
            if r["turno"] == turno
        ]

        labels = [
            f"E{r['npe']}-C{r['npc']}"
            for r in datos_turno
        ]

        x = np.arange(len(labels))

        arrep = [
            r["porcentaje_arrepentimiento"]
            for r in datos_turno
        ]

        deriv = [
            r["porcentaje_derivados"]
            for r in datos_turno
        ]

        width = 0.35

        ax = axs[idx]

        ax.set_facecolor("none")

        bars1 = ax.bar(
            x - width / 2,
            arrep,
            width,
            label="% Arrepentimiento",
            color=colores["arrep"]
        )

        bars2 = ax.bar(
            x + width / 2,
            deriv,
            width,
            label="% Derivados",
            color=colores["deriv"]
        )

        ax.set_title(
            turno,
            fontsize=14,
            fontweight="bold",
            color=texto
        )

        ax.set_xticks(x)
        ax.set_xticklabels(labels, color=texto)

        ax.set_ylabel(
            "Porcentaje (%)",
            color=texto
        )

        ax.set_ylim(0, max_y)

        ax.grid(
            axis="y",
            linestyle="--",
            alpha=0.3,
            color=grid
        )

        # COLOR EJES

        ax.tick_params(colors=texto)

        ax.spines["bottom"].set_color(texto)
        ax.spines["left"].set_color(texto)

        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        # =====================================================
        # VALORES ARRIBA DE LAS BARRAS
        # =====================================================

        for bars in [bars1, bars2]:

            for bar in bars:

                h = bar.get_height()

                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    h + 0.3,
                    f"{h:.1f}%",
                    ha="center",
                    fontsize=8,
                    color=texto
                )

    # =========================================================
    # LEYENDA
    # =========================================================

    handles, labels = axs[0].get_legend_handles_labels()

    legend = fig.legend(
        handles,
        labels,
        loc="upper center",
        bbox_to_anchor=(0.5, 0.95),
        ncol=2,
        fontsize=11,
        frameon=False
    )

    for text in legend.get_texts():
        text.set_color(texto)

    plt.tight_layout(rect=[0, 0, 1, 0.9])

    plt.savefig(
        "comparacion_porcentajes.png",
        dpi=250,
        transparent=True,
        bbox_inches="tight"
    )

    plt.close()

    print("Gráfico guardado: comparacion_porcentajes.png")



TIEMPO_FIN = 480  # 8 horas por turno, en minutos   
OUTPUT_PATH = "./resultados.csv"

escenarios = [
    {"turno": Turno.MANIANA, "npe": 1, "npc": 1, "tipo": "optimo"},
    {"turno": Turno.TARDE, "npe": 1, "npc": 1, "tipo": "optimo"},
    {"turno": Turno.NOCHE, "npe": 1, "npc": 1, "tipo": "optimo"},

    {"turno": Turno.MANIANA, "npe": 5, "npc": 5, "tipo": "optimo"},
    {"turno": Turno.TARDE, "npe": 5, "npc": 5, "tipo": "optimo"},
    {"turno": Turno.NOCHE, "npe": 5, "npc": 5, "tipo": "optimo"},

    {"turno": Turno.MANIANA, "npe": 2, "npc": 3, "tipo": "optimo"},
    {"turno": Turno.TARDE, "npe": 3, "npc": 4, "tipo": "optimo"},
    {"turno": Turno.NOCHE, "npe": 2, "npc": 2, "tipo": "optimo"},
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
        #graficar_resultado(resultado)
        comparar_metricas(resultados)
        comparar_porcentajes(resultados)

    # Persistir en CSV
    campos = list(resultados[0].keys())

    with open(OUTPUT_PATH, "x", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        writer.writerows(resultados)

    print(f"\nResultados guardados en: {os.path.abspath(OUTPUT_PATH)}")


import matplotlib.pyplot as plt
import numpy as np


