# -*- coding: utf-8 -*-
"""
triage_analysis.py
==================
Análisis de la variable "Nivel de Triage" (acuity).
Modelado mediante proporciones empíricas discretas, segmentadas por turno.

Datasets requeridos:
    - triage.csv          → columna 'acuity' (niveles 1–5, variable discreta)
    - Hospital ER_Data.csv → columna 'Patient Admission Date' (para asignar turno)

Estrategia de join:
    Ambos datasets no comparten una clave directa. Se alinean por índice
    de orden cronológico: el registro N de triage.csv corresponde al
    registro N de Hospital ER_Data.csv (mismo orden de llegada).
    Se usa el mínimo de filas entre ambos para el join.

Turnos definidos (3 turnos de 8 horas):
    T1 — Mañana : 07:00 – 15:00
    T2 — Tarde  : 15:00 – 23:00
    T3 — Noche  : 23:00 – 07:00  (cruza la medianoche)

Pasos:
    1. Carga de datasets
    2. Join por índice + asignación de turno
    3. Análisis exploratorio global (frecuencias + gráficos)
    4. Proporciones empíricas globales
    5. Análisis por turno: proporciones empíricas + gráficos
    6. Resumen comparativo final
"""

# =============================================================================
# DEPENDENCIAS
# =============================================================================
# pip install pandas numpy matplotlib

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker


# =============================================================================
# CONFIGURACIÓN
# =============================================================================

PATH_CSV_TRIAGE = "../CSV/triage.csv"               # ← Ajustar según entorno local
PATH_CSV_MAIN   = "../CSV/Hospital_ER_Data.csv"      # ← Ajustar según entorno local
DATE_COL        = "Patient Admission Date"
ACUITY_COL      = "acuity"
NIVELES_TRIAGE  = [1, 2, 3, 4, 5]               # Escala ESI/Manchester

# Turnos: (nombre_display, hora_inicio, hora_fin)
TURNOS = {
    "T1": ("Mañana", 7,  15),
    "T2": ("Tarde",  15, 23),
    "T3": ("Noche",  23,  7),
}
COLORES_TURNOS  = {"T1": "steelblue", "T2": "darkorange", "T3": "mediumpurple"}

# Colores por nivel de triage (1=crítico → rojo, 5=leve → verde)
COLORES_NIVELES = {1: "#d62728", 2: "#ff7f0e", 3: "#ffdd57", 4: "#2ca02c", 5: "#1f77b4"}


# =============================================================================
# 1. CARGA DE DATOS
# =============================================================================

def cargar_datos() -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Carga triage.csv y Hospital ER_Data.csv.
    Parsea y ordena cronológicamente el dataset principal.

    Returns:
        (df_triage, df_main) — DataFrames crudos listos para el join.
    """
    df_triage = pd.read_csv(PATH_CSV_TRIAGE)
    df_triage = df_triage.dropna(subset=[ACUITY_COL]).reset_index(drop=True)
    df_triage[ACUITY_COL] = df_triage[ACUITY_COL].astype(int)

    df_main = pd.read_csv(PATH_CSV_MAIN)
    df_main["PatientAdmissionDate_dt"] = pd.to_datetime(df_main[DATE_COL])
    df_main = df_main.sort_values("PatientAdmissionDate_dt").reset_index(drop=True)

    print(f"[OK] triage.csv cargado        : {len(df_triage)} registros")
    print(f"[OK] Hospital ER_Data.csv cargado: {len(df_main)} registros")
    return df_triage, df_main


# =============================================================================
# 2. JOIN POR ÍNDICE + ASIGNACIÓN DE TURNO
# =============================================================================

def asignar_turno(hora: int) -> str:
    """
    Devuelve el código de turno según la hora del día (0–23).
    T3 cruza la medianoche: hora ≥ 23 OR hora < 7.
    """
    if 7 <= hora < 15:
        return "T1"
    elif 15 <= hora < 23:
        return "T2"
    else:
        return "T3"


def construir_dataset(df_triage: pd.DataFrame, df_main: pd.DataFrame) -> pd.DataFrame:
    """
    Alinea triage y admisiones por índice de orden cronológico y agrega
    la columna 'turno' derivada de la hora de ingreso.

    El join se hace sobre las primeras N filas de cada dataset, siendo
    N = min(len(df_triage), len(df_main)).

    Returns:
        DataFrame con columnas: 'acuity', 'hora', 'turno'.
    """
    n = min(len(df_triage), len(df_main))
    if len(df_triage) != len(df_main):
        print(f"[AVISO] Tamaños distintos — usando primeros {n} registros de cada dataset.")

    df = pd.DataFrame({
        ACUITY_COL: df_triage[ACUITY_COL].iloc[:n].values,
        "hora":     df_main["PatientAdmissionDate_dt"].dt.hour.iloc[:n].values,
    })
    df["turno"] = df["hora"].apply(asignar_turno)

    print(f"[OK] Dataset combinado: {len(df)} registros con acuity + turno.")
    print(f"\n--- Distribución de registros por turno ---")
    for key, (nombre, h_ini, h_fin) in TURNOS.items():
        n_t = (df["turno"] == key).sum()
        print(f"  {key} [{nombre:6s} {h_ini:02d}:00–{h_fin:02d}:00] : {n_t:5d} registros")

    return df


# =============================================================================
# 3. ANÁLISIS EXPLORATORIO GLOBAL
# =============================================================================

def estadisticas_descriptivas(serie: pd.Series, label: str = "global") -> None:
    """Imprime frecuencias absolutas, relativas y estadísticas de acuity."""
    print(f"\n--- Estadísticas descriptivas: acuity [{label}] ---")
    conteo = serie.value_counts().sort_index()
    props  = serie.value_counts(normalize=True).sort_index().mul(100)

    tabla = pd.DataFrame({"Frecuencia": conteo, "Porcentaje (%)": props.round(2)})
    print(tabla.to_string())
    print(f"\n  Media    : {serie.mean():.4f}")
    print(f"  Mediana  : {serie.median():.1f}")
    print(f"  Moda     : {serie.mode().values}")
    print(f"  Std      : {serie.std():.4f}")


def graficar_exploratorio_global(serie: pd.Series) -> None:
    """
    Genera tres gráficos globales en una figura:
        - Barras de frecuencia absoluta con colores por nivel
        - Barras de proporción (%)
        - Boxplot
    """
    conteo = serie.value_counts().sort_index()
    props  = serie.value_counts(normalize=True).sort_index().mul(100)
    colores = [COLORES_NIVELES.get(n, "gray") for n in conteo.index]

    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    fig.suptitle("Análisis exploratorio — Nivel de Triage (acuity) [Global]", fontsize=13)

    # Frecuencia absoluta
    axes[0].bar(conteo.index, conteo.values, color=colores, edgecolor="white", alpha=0.85)
    axes[0].set_title("Frecuencia absoluta")
    axes[0].set_xlabel("Nivel de triage")
    axes[0].set_ylabel("Cantidad de pacientes")
    axes[0].set_xticks(NIVELES_TRIAGE)
    for i, v in zip(conteo.index, conteo.values):
        axes[0].text(i, v + conteo.max() * 0.01, str(v), ha="center", fontsize=9)

    # Proporción (%)
    axes[1].bar(props.index, props.values, color=colores, edgecolor="white", alpha=0.85)
    axes[1].set_title("Proporción (%)")
    axes[1].set_xlabel("Nivel de triage")
    axes[1].set_ylabel("Porcentaje (%)")
    axes[1].set_xticks(NIVELES_TRIAGE)
    axes[1].yaxis.set_major_formatter(mticker.FormatStrFormatter("%.1f%%"))
    for i, v in zip(props.index, props.values):
        axes[1].text(i, v + props.max() * 0.01, f"{v:.1f}%", ha="center", fontsize=9)

    # Boxplot
    axes[2].boxplot(serie, vert=True, patch_artist=True,
                    boxprops=dict(facecolor="steelblue", alpha=0.6))
    axes[2].set_title("Boxplot")
    axes[2].set_ylabel("Nivel de triage")
    axes[2].set_yticks(NIVELES_TRIAGE)

    plt.tight_layout()
    plt.show()


# =============================================================================
# 4. PROPORCIONES EMPÍRICAS
# =============================================================================

def calcular_proporciones(serie: pd.Series, label: str = "global") -> pd.Series:
    """
    Calcula las proporciones empíricas de cada nivel de triage.
    Garantiza que todos los niveles 1–5 estén presentes (con 0 si faltan).

    Returns:
        Serie indexada 1–5 con las probabilidades (suma = 1).
    """
    props = serie.value_counts(normalize=True).reindex(NIVELES_TRIAGE, fill_value=0.0)
    props = props.sort_index()

    print(f"\n--- Proporciones empíricas: acuity [{label}] ---")
    for nivel, p in props.items():
        barra = "█" * int(p * 40)
        print(f"  Nivel {nivel} : {p:.4f} ({p*100:5.2f}%)  {barra}")
    print(f"  Suma total : {props.sum():.6f}")

    return props


# =============================================================================
# 5. ANÁLISIS POR TURNO
# =============================================================================

def graficar_proporciones_turno(proporciones: pd.Series, label: str, color: str) -> None:
    """
    Genera un gráfico de barras de proporciones empíricas para un turno.
    """
    colores_barras = [COLORES_NIVELES.get(n, "gray") for n in proporciones.index]

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(proporciones.index, proporciones.values, color=colores_barras,
           edgecolor="white", alpha=0.85, width=0.6)
    ax.set_title(f"Proporciones empíricas de Triage — {label}")
    ax.set_xlabel("Nivel de triage")
    ax.set_ylabel("Proporción")
    ax.set_xticks(NIVELES_TRIAGE)
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.2f"))
    for nivel, p in proporciones.items():
        ax.text(nivel, p + proporciones.max() * 0.01, f"{p*100:.1f}%",
                ha="center", fontsize=9)
    plt.tight_layout()
    plt.show()


def analizar_turno(key: str, df_turno: pd.DataFrame) -> dict:
    """
    Calcula proporciones empíricas de triage para un turno y las grafica.

    Args:
        key      : Código del turno ("T1", "T2" o "T3").
        df_turno : Subconjunto del dataset combinado para ese turno.

    Returns:
        dict con 'turno' y 'proporciones'.
    """
    nombre_display, h_ini, h_fin = TURNOS[key]
    label = f"{key} — {nombre_display} ({h_ini:02d}:00–{h_fin:02d}:00)"
    color = COLORES_TURNOS[key]
    serie = df_turno[ACUITY_COL]

    print(f"\n{'━'*55}")
    print(f"  TURNO {label}  (n={len(serie)})")
    print(f"{'━'*55}")

    estadisticas_descriptivas(serie, label=label)
    proporciones = calcular_proporciones(serie, label=label)
    graficar_proporciones_turno(proporciones, label=label, color=color)

    return {"turno": label, "proporciones": proporciones}


# =============================================================================
# 6. RESUMEN COMPARATIVO FINAL
# =============================================================================

def resumen_comparativo(props_global: pd.Series, resultados_turnos: list[dict]) -> None:
    """
    Imprime tabla comparativa de proporciones por nivel y turno,
    y genera una figura con barras agrupadas y stacked bars.

    Args:
        props_global      : Proporciones empíricas globales.
        resultados_turnos : Lista de dicts por turno (salida de analizar_turno).
    """
    # ── Tabla de proporciones ─────────────────────────────────────────────────
    print("\n" + "="*70)
    print("  RESUMEN COMPARATIVO — Proporciones de Triage por Turno")
    print("="*70)
    header = f"  {'Nivel':<8}" + f"{'Global':>10}" + "".join(
        f"{r['turno'].split('—')[0].strip():>14}" for r in resultados_turnos
    )
    print(header)
    print("  " + "-"*68)
    for nivel in NIVELES_TRIAGE:
        fila = f"  Nivel {nivel}  {props_global.get(nivel, 0):>9.4f}"
        for r in resultados_turnos:
            fila += f"  {r['proporciones'].get(nivel, 0):>12.4f}"
        print(fila)
    print("  " + "-"*68)
    fila_suma = f"  {'SUMA':8}  {props_global.sum():>9.4f}"
    for r in resultados_turnos:
        fila_suma += f"  {r['proporciones'].sum():>12.4f}"
    print(fila_suma)
    print("="*70)

    # ── Gráfico: barras agrupadas + stacked bars ──────────────────────────────
    fig, axes = plt.subplots(1, 2, figsize=(15, 5))
    fig.suptitle("Triage (acuity) — Comparación de proporciones por turno", fontsize=13)

    # Panel izquierdo: barras agrupadas por nivel
    x      = np.array(NIVELES_TRIAGE)
    ancho  = 0.2
    offset = [-0.3, 0, 0.3]

    for idx, r in enumerate(resultados_turnos):
        key   = r["turno"].split(" ")[0]
        color = COLORES_TURNOS[key]
        vals  = [r["proporciones"].get(n, 0) for n in NIVELES_TRIAGE]
        axes[0].bar(x + offset[idx], vals, width=ancho, color=color,
                    alpha=0.8, label=r["turno"].split("—")[0].strip(), edgecolor="white")

    axes[0].set_title("Proporciones por nivel y turno")
    axes[0].set_xlabel("Nivel de triage")
    axes[0].set_ylabel("Proporción")
    axes[0].set_xticks(NIVELES_TRIAGE)
    axes[0].legend()
    axes[0].yaxis.set_major_formatter(mticker.FormatStrFormatter("%.2f"))

    # Panel derecho: stacked bars — composición por turno
    bottom       = np.zeros(3)
    turno_labels = [r["turno"].split("—")[0].strip() for r in resultados_turnos]
    for nivel in NIVELES_TRIAGE:
        vals = [r["proporciones"].get(nivel, 0) for r in resultados_turnos]
        axes[1].bar(turno_labels, vals, bottom=bottom,
                    color=COLORES_NIVELES[nivel], label=f"Nivel {nivel}",
                    edgecolor="white", alpha=0.85)
        bottom += np.array(vals)

    axes[1].set_title("Composición de triage por turno (apilado)")
    axes[1].set_xlabel("Turno")
    axes[1].set_ylabel("Proporción acumulada")
    axes[1].legend(title="Nivel", bbox_to_anchor=(1.01, 1), loc="upper left")

    plt.tight_layout()
    plt.show()

    # ── Mensaje final para simulación ─────────────────────────────────────────
    print("\n[LISTO] Proporciones listas para la simulación (TP5).")
    print("  Uso: np.random.choice(niveles, size=N, p=proporciones_turno)\n")
    for r in resultados_turnos:
        key   = r["turno"].split(" ")[0]
        probs = {n: round(r["proporciones"].get(n, 0), 4) for n in NIVELES_TRIAGE}
        print(f"  {key}: {probs}")


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 55)
    print("  ANÁLISIS TRIAGE — Nivel de Acuity")
    print("  (Global + segmentado por turno)")
    print("=" * 55)

    # ── 1. Carga ──────────────────────────────────────────────────────────────
    df_triage, df_main = cargar_datos()

    # ── 2. Join + turno ───────────────────────────────────────────────────────
    df = construir_dataset(df_triage, df_main)

    # ── 3. EDA global ─────────────────────────────────────────────────────────
    estadisticas_descriptivas(df[ACUITY_COL], label="global")
    graficar_exploratorio_global(df[ACUITY_COL])

    # ── 4. Proporciones empíricas globales ────────────────────────────────────
    props_global = calcular_proporciones(df[ACUITY_COL], label="global")

    # ── 5. Análisis por turno ─────────────────────────────────────────────────
    resultados_turnos = []
    for key in TURNOS:
        df_turno = df[df["turno"] == key]
        res = analizar_turno(key, df_turno)
        resultados_turnos.append(res)

    # ── 6. Resumen comparativo ────────────────────────────────────────────────
    resumen_comparativo(props_global, resultados_turnos)

    return {"global": props_global, "turnos": resultados_turnos}


if __name__ == "__main__":
    main()