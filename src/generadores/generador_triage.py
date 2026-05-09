# =============================================================================
# GENERADOR TRIAGE
# =============================================================================
# Este componente:
# 1. Calcula proporciones empíricas de NivelUrgencia por turno
#    a partir de los datasets del tp4 (triage.csv + Hospital_ER_Data.csv)
# 2. Guarda las proporciones en distribuciones/triage_config.json
# 3. Permite generar un NivelUrgencia aleatorio según el turno actual
#
# Mapeo de niveles CSV (escala ESI 1-5) → dominio (4 niveles):
#   CSV 1 → NIVEL_1 (Crítico)
#   CSV 2 → NIVEL_2 (Grave)
#   CSV 3 → NIVEL_3 (Complicado)
#   CSV 4 → NIVEL_4 (Normal)
#   CSV 5 → NIVEL_4 (Normal)  ← fusionado
#
# Turnos definidos (igual que triage_processor.py del tp4):
#   T1 — Mañana : 07:00 – 15:00
#   T2 — Tarde  : 15:00 – 23:00
#   T3 — Noche  : 23:00 – 07:00
# =============================================================================
from pathlib import Path
import pandas as pd
import numpy as np
import json
from dominio.enums import NivelUrgencia, Turno

# =============================================================================
# CONFIGURACIÓN
# =============================================================================

PATH_CSV_TRIAGE = "../../CSV/triage.csv"
PATH_CSV_MAIN   = "../../CSV/Hospital_ER_Data2.csv"
DATE_COL        = "Patient Admission Date"
ACUITY_COL      = "acuity"

CONFIG_PATH = Path(__file__).parent / "distribuciones" / "triage_config.json"

# Niveles en el CSV (ESI 1-5)
NIVELES_CSV = [1, 2, 3, 4, 5]

# Mapeo CSV → NivelUrgencia del dominio
MAPEO_NIVELES = {
    1: NivelUrgencia.NIVEL_1,
    2: NivelUrgencia.NIVEL_2,
    3: NivelUrgencia.NIVEL_3,
    4: NivelUrgencia.NIVEL_4,
    5: NivelUrgencia.NIVEL_4,   # fusionado
}

# Mapeo Turno del dominio → clave de turno interno
TURNO_A_CLAVE = {
    Turno.MANIANA: "T1",
    Turno.TARDE:   "T2",
    Turno.NOCHE:   "T3",
}

# Niveles del dominio en orden
NIVELES_DOMINIO = [
    NivelUrgencia.NIVEL_1,
    NivelUrgencia.NIVEL_2,
    NivelUrgencia.NIVEL_3,
    NivelUrgencia.NIVEL_4,
]


# =============================================================================
# CLASE GENERADOR
# =============================================================================

class GeneradorTriage:
    """
    Genera un NivelUrgencia aleatorio según las proporciones empíricas
    calculadas para el turno actual del sistema.

    Parámetros
    ----------
    proporciones_por_turno : dict
        Clave: código de turno ("T1", "T2", "T3")
        Valor: dict { nivel_int: probabilidad }
                donde nivel_int es 1..4 (niveles del dominio)
    """

    def __init__(self, proporciones_por_turno: dict):
        self.proporciones_por_turno = proporciones_por_turno

    def generar(self, turno: Turno) -> NivelUrgencia:
        """
        Genera un NivelUrgencia para el turno dado.

        Parámetros
        ----------
        turno : Turno
            Turno actual del sistema (Turno.MANIANA, TARDE o NOCHE)

        Retorna
        -------
        NivelUrgencia
        """
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
    """Devuelve código de turno según la hora (0-23)."""
    if 7 <= hora < 15:
        return "T1"
    elif 15 <= hora < 23:
        return "T2"
    else:
        return "T3"


def _mapear_nivel_csv_a_dominio(nivel_csv: int) -> int:
    """Convierte nivel ESI (1-5) al entero del NivelUrgencia del dominio (1-4)."""
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

    # Mapeo 5→4 y conversión a nivel dominio
    df["nivel_dominio"] = df["nivel_csv"].apply(_mapear_nivel_csv_a_dominio)
    df["turno"]         = df["hora"].apply(_asignar_turno)

    print(f"[OK] Dataset combinado: {len(df)} registros")
    return df


def calcular_proporciones_por_turno(df) -> dict:
    """
    Calcula proporciones empíricas de NivelUrgencia (1-4) por turno.

    Retorna
    -------
    dict: { "T1": {"1": p, "2": p, "3": p, "4": p}, "T2": ..., "T3": ... }
    """
    niveles_dominio_int = [1, 2, 3, 4]
    proporciones = {}

    for clave in ["T1", "T2", "T3"]:
        serie = df[df["turno"] == clave]["nivel_dominio"]
        props = (
            serie.value_counts(normalize=True)
                 .reindex(niveles_dominio_int, fill_value=0.0)
                 .sort_index()
        )
        # Guardar con claves string (necesario para JSON)
        proporciones[clave] = {str(k): float(v) for k, v in props.items()}

        print(f"\n  Turno {clave} (n={len(serie)}):")
        for nivel, p in proporciones[clave].items():
            barra = "█" * int(float(p) * 40)
            print(f"    Nivel {nivel}: {float(p):.4f} ({float(p)*100:5.2f}%) {barra}")

    return proporciones


def guardar_configuracion(proporciones: dict):
    config = {"proporciones_por_turno": proporciones}
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=4)
    print(f"\n[OK] Configuración guardada en: {CONFIG_PATH}")


def cargar_generador_desde_json(path=CONFIG_PATH) -> GeneradorTriage:
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

    # 1. Cargar datos
    df_triage, df_main = cargar_datos()

    # 2. Construir dataset combinado con mapeo y turno
    df = construir_dataset(df_triage, df_main)

    # 3. Calcular proporciones por turno
    print("\n--- Proporciones empíricas por turno ---")
    proporciones = calcular_proporciones_por_turno(df)

    # 4. Guardar configuración
    guardar_configuracion(proporciones)

    # 5. Crear generador y mostrar ejemplos
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
