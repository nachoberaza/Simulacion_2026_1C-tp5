# =============================================================================
# GENERADOR TRIAGE
# =============================================================================
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import json
from dominio.enums import NivelUrgencia, Turno
from generadores.generador_IA import ESCENARIO_DEFAULT

# =============================================================================
# CONFIGURACIÓN
# =============================================================================

# Antes
PATH_CSV_TRIAGE = "../../CSV/triage.csv"
PATH_CSV_MAIN   = "../../CSV/Hospital_ER_Data2.csv"

# Después
_BASE = Path(__file__).parent.parent.parent  # sube hasta la raíz del proyecto
PATH_CSV_TRIAGE = _BASE / "CSV" / "triage.csv"
PATH_CSV_MAIN   = _BASE / "CSV" / "Hospital_ER_Data2.csv"

DATE_COL        = "Patient Admission Date"
ACUITY_COL      = "acuity"

DIST_DIR = Path(__file__).parent / "distribuciones"

NIVELES_CSV = [1, 2, 3, 4, 5]

MAPEO_NIVELES = {
    1: NivelUrgencia.NIVEL_1,
    2: NivelUrgencia.NIVEL_2,
    3: NivelUrgencia.NIVEL_3,
    4: NivelUrgencia.NIVEL_4,
    5: NivelUrgencia.NIVEL_4,
}

TURNO_A_CLAVE = {
    Turno.MANIANA: "T1",
    Turno.TARDE:   "T2",
    Turno.NOCHE:   "T3",
}

NIVELES_DOMINIO = [
    NivelUrgencia.NIVEL_1,
    NivelUrgencia.NIVEL_2,
    NivelUrgencia.NIVEL_3,
    NivelUrgencia.NIVEL_4,
]

# Estilo oscuro con fondo transparente (se aplica una sola vez)
plt.rcParams.update({
    "figure.facecolor": "none",
    "axes.facecolor":   "none",
    "axes.edgecolor":   "#FFFFFF44",
    "axes.labelcolor":  "#CCCCCC",
    "text.color":       "#FFFFFF",
    "xtick.color":      "#CCCCCC",
    "ytick.color":      "#CCCCCC",
    "grid.color":       "#FFFFFF22",
    "grid.linestyle":   "--",
    "legend.facecolor": "#00000099",
    "legend.edgecolor": "#FFFFFF44",
})


# =============================================================================
# CLASE GENERADOR
# =============================================================================

class GeneradorTriage:

    def __init__(self, proporciones_por_turno: dict):
        self.proporciones_por_turno = proporciones_por_turno

    def generar(self, turno: Turno) -> NivelUrgencia:
        clave = TURNO_A_CLAVE[turno]
        props = self.proporciones_por_turno[clave]

        niveles  = [int(k) for k in props.keys()]
        probs    = [props[str(k)] for k in niveles]

        nivel_int = int(np.random.choice(niveles, p=probs))
        return NivelUrgencia(nivel_int)

    def __str__(self):
        lines = ["GeneradorTriage(proporciones por turno):"]
        for clave, props in self.proporciones_por_turno.items():
            lines.append(f"  {clave}: { {k: round(v,4) for k,v in props.items()} }")
        return "\n".join(lines)


# =============================================================================
# PREPROCESAMIENTO
# =============================================================================

def _asignar_turno(hora: int) -> str:
    if 7 <= hora < 15:
        return "T1"
    elif 15 <= hora < 23:
        return "T2"
    else:
        return "T3"


def _mapear_nivel_csv_a_dominio(nivel_csv: int) -> int:
    return MAPEO_NIVELES[nivel_csv].value


def cargar_datos():
    df_triage = pd.read_csv(PATH_CSV_TRIAGE)
    df_triage = df_triage.dropna(subset=[ACUITY_COL]).reset_index(drop=True)
    df_triage[ACUITY_COL] = df_triage[ACUITY_COL].astype(int)

    df_main = pd.read_csv(PATH_CSV_MAIN)
    df_main["PatientAdmissionDate_dt"] = pd.to_datetime(
        df_main[DATE_COL], format="mixed", dayfirst=True
    )
    df_main = df_main.sort_values("PatientAdmissionDate_dt").reset_index(drop=True)

    print(f"[OK] triage.csv          : {len(df_triage)} registros")
    print(f"[OK] Hospital_ER_Data.csv: {len(df_main)} registros")
    return df_triage, df_main


def construir_dataset(df_triage, df_main):
    n = min(len(df_triage), len(df_main))
    if len(df_triage) != len(df_main):
        print(f"[AVISO] Tamaños distintos — usando primeros {n} registros de cada dataset.")

    df = pd.DataFrame({
        "nivel_csv":  df_triage[ACUITY_COL].iloc[:n].values,
        "hora":       df_main["PatientAdmissionDate_dt"].dt.hour.iloc[:n].values,
    })

    df["nivel_dominio"] = df["nivel_csv"].apply(_mapear_nivel_csv_a_dominio)
    df["turno"]         = df["hora"].apply(_asignar_turno)

    print(f"[OK] Dataset combinado: {len(df)} registros")
    return df


def calcular_proporciones_por_turno(df) -> dict:
    niveles_dominio_int = [1, 2, 3, 4]
    proporciones = {}

    for clave in ["T1", "T2", "T3"]:
        serie = df[df["turno"] == clave]["nivel_dominio"]
        props = (
            serie.value_counts(normalize=True)
                 .reindex(niveles_dominio_int, fill_value=0.0)
                 .sort_index()
        )
        proporciones[clave] = {str(k): float(v) for k, v in props.items()}

        print(f"\n  Turno {clave} (n={len(serie)}):")
        for nivel, p in proporciones[clave].items():
            barra = "█" * int(float(p) * 40)
            print(f"    Nivel {nivel}: {float(p):.4f} ({float(p)*100:5.2f}%) {barra}")

    _graficar_proporciones(proporciones)

    return proporciones


def _graficar_proporciones(proporciones: dict):
    turnos  = ["T1", "T2", "T3"]
    niveles = ["1", "2", "3", "4"]
    labels  = ["T1 — Mañana", "T2 — Tarde", "T3 — Noche"]
    colores = ["#E05C7A", "#4A90D9", "#4DCC8A", "#FFD700"]

    x     = np.arange(len(turnos))
    ancho = 0.18

    fig, ax = plt.subplots(figsize=(8, 4.5))

    for i, nivel in enumerate(niveles):
        vals = [proporciones[t][nivel] for t in turnos]
        ax.bar(
            x + i * ancho,
            vals,
            ancho,
            label=f"Nivel {nivel}",
            color=colores[i],
            alpha=0.85,
        )

    ax.set_xticks(x + ancho * 1.5)
    ax.set_xticklabels(labels)
    ax.set_ylabel("Proporción empírica")
    ax.set_title("Distribución de NivelUrgencia por Turno", fontweight="bold")
    ax.legend()
    ax.grid(axis="y")

    plt.tight_layout()
    plt.savefig(DIST_DIR / "fdp_triage.png", dpi=180, transparent=True, bbox_inches="tight")
    plt.show()


# =============================================================================
# SERIALIZACIÓN
# =============================================================================

def guardar_configuracion(proporciones: dict, escenario: str):
    config = {"proporciones_por_turno": proporciones}
    path = DIST_DIR / f"triage_config_{escenario}.json"

    with open(path, "w") as f:
        json.dump(config, f, indent=4)
    print(f"\n[OK] Configuración guardada en: {path}")


def cargar_generador_desde_json(escenario) -> GeneradorTriage:
    file = f"triage_config_{escenario}.json"
    path = DIST_DIR / file

    with open(path, "r") as f:
        data = json.load(f)
    return GeneradorTriage(data["proporciones_por_turno"])


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("===================================")
    print("ANÁLISIS TRIAGE — NivelUrgencia")
    print("===================================")

    df_triage, df_main = cargar_datos()

    df = construir_dataset(df_triage, df_main)

    print("\n--- Proporciones empíricas por turno ---")
    proporciones = calcular_proporciones_por_turno(df)

    guardar_configuracion(proporciones, ESCENARIO_DEFAULT)

    generador = GeneradorTriage(proporciones)
    print("\n===================================")
    print("EJEMPLOS DE GENERACIÓN")
    print("===================================")
    for turno in [Turno.MANIANA, Turno.TARDE, Turno.NOCHE]:
        for i in range(3):
            nivel = generador.generar(turno)
            print(f"  Turno {turno.name:<8} → {nivel.name}")


if __name__ == "__main__":
    main()