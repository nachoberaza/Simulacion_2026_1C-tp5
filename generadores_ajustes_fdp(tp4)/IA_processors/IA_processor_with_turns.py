# -*- coding: utf-8 -*-
"""
ia_min_analysis.py
==================
Análisis de la variable "Intervalo entre Arribos de Pacientes" (IA_min).
Incluye análisis global y segmentado por turno de atención.

Dataset requerido: Hospital ER_Data.csv
    - Columna clave: 'Patient Admission Date' (datetime parseable)

Turnos definidos (3 turnos de 8 horas):
    T1 — Mañana : 07:00 – 15:00
    T2 — Tarde  : 15:00 – 23:00
    T3 — Noche  : 23:00 – 07:00  (cruza la medianoche)

Pasos:
    1. Carga del CSV
    2. Cálculo de IA_min global (diferencia entre llegadas consecutivas, en minutos)
    3. Análisis exploratorio global (estadísticas + visualizaciones)
    4. Ajuste de FDP global con Fitter
    5. Fórmula matemática descriptiva de la FDP
    6. Reporte global (fórmula + gráfico ajuste)
    7. Segmentación por turnos + IA_min por turno
    8. Ajuste de FDP por turno + reporte individual
    9. Resumen final comparativo de las 3 FDPs
"""

# =============================================================================
# DEPENDENCIAS
# =============================================================================
# pip install fitter pandas numpy matplotlib scipy

from fitter import Fitter
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats


# =============================================================================
# CONFIGURACIÓN
# =============================================================================

PATH_CSV = "../CSV/Hospital_ER_Data2.csv"  # ← Ajustar según entorno local
DATE_COL = "Patient Admission Date"
BINS_HIST = 50
TOP_N_DISTRIBUTIONS = 10

# Turnos: cada entrada es (nombre_display, hora_inicio, hora_fin).
# hora_fin < hora_inicio indica que el turno cruza la medianoche.
TURNOS = {
    "T1": ("Mañana", 7,  15),
    "T2": ("Tarde",  15, 23),
    "T3": ("Noche",  23,  7),   # 23:00 → 07:00 (cruza medianoche)
}
COLORES_TURNOS = {"T1": "steelblue", "T2": "darkorange", "T3": "mediumpurple"}


# =============================================================================
# 1. CARGA DE DATOS
# =============================================================================

def cargar_datos(path: str) -> pd.DataFrame:
    """
    Lee el CSV y devuelve un DataFrame con la columna de fecha ya parseada
    y ordenada cronológicamente.
    """
    df = pd.read_csv(path)
    df["PatientAdmissionDate_dt"] = pd.to_datetime(df[DATE_COL])
    df = df.sort_values("PatientAdmissionDate_dt").reset_index(drop=True)
    print(f"[OK] Dataset cargado: {df.shape[0]} registros, {df.shape[1]} columnas.")
    return df


# =============================================================================
# 2. CÁLCULO DE IA_min
# =============================================================================

def calcular_ia_min(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula el intervalo entre llegadas consecutivas en minutos (IA_min)
    y preserva la hora de llegada de cada paciente para la segmentación
    por turnos posterior.

    La hora usada para asignar el turno es la del paciente ACTUAL
    (no el anterior), ya que ese paciente es el que "pertenece" a ese turno.

    Returns:
        DataFrame con columnas:
            - IA_min  : intervalo en minutos (float)
            - hora    : hora del día del paciente actual (int, 0–23)
    """
    ia = df["PatientAdmissionDate_dt"].diff().dt.total_seconds() / 60
    hora = df["PatientAdmissionDate_dt"].dt.hour

    resultado = pd.DataFrame({"IA_min": ia, "hora": hora})
    resultado = resultado.dropna(subset=["IA_min"])
    resultado = resultado[resultado["IA_min"] > 0].reset_index(drop=True)

    print(f"[OK] IA_min calculado: {len(resultado)} intervalos válidos.")
    return resultado


# =============================================================================
# 3. ANÁLISIS EXPLORATORIO
# =============================================================================

def estadisticas_descriptivas(ia: pd.Series, label: str = "global") -> None:
    """Imprime estadísticas descriptivas de una serie IA_min."""
    print(f"\n--- Estadísticas descriptivas: IA_min [{label}] (minutos) ---")
    print(ia.describe().round(4).to_string())
    print(f"  Skewness : {ia.skew():.4f}")
    print(f"  Kurtosis : {ia.kurt():.4f}")


def graficar_exploratorio(ia: pd.Series, label: str = "Global", color: str = "steelblue") -> None:
    """Genera histograma y boxplot de IA_min en una sola figura."""
    fig, axes = plt.subplots(1, 2, figsize=(13, 4))
    fig.suptitle(f"Análisis exploratorio — IA_min [{label}]", fontsize=13)

    axes[0].hist(ia, bins=BINS_HIST, color=color, edgecolor="white", alpha=0.85)
    axes[0].set_title("Histograma")
    axes[0].set_xlabel("Minutos entre llegadas")
    axes[0].set_ylabel("Frecuencia")

    axes[1].boxplot(ia, vert=True, patch_artist=True,
                    boxprops=dict(facecolor=color, alpha=0.6))
    axes[1].set_title("Boxplot")
    axes[1].set_ylabel("Minutos entre llegadas")

    plt.tight_layout()
    plt.show()


# =============================================================================
# 4. AJUSTE DE FDP
# =============================================================================

def ajustar_fdp(ia: pd.Series, label: str = "global", top_n: int = TOP_N_DISTRIBUTIONS) -> Fitter:
    """
    Ajusta múltiples distribuciones sobre una serie IA_min con Fitter.

    Args:
        ia    : Serie de intervalos en minutos.
        label : Etiqueta descriptiva (ej. 'global', 'T1 – Mañana').
        top_n : Cantidad de distribuciones a mostrar en el ranking.

    Returns:
        Objeto Fitter ya ajustado.
    """
    print(f"\n[...] Ajustando distribuciones para IA_min [{label}]...")
    f = Fitter(ia, bins=BINS_HIST)
    f.fit()
    print(f"\n=== Top {top_n} distribuciones — IA_min [{label}] ===")
    f.summary(top_n)
    return f


# =============================================================================
# 5. FÓRMULA MATEMÁTICA DE LA FDP
# =============================================================================

# Catálogo de distribuciones: fórmula en texto plano + parámetros con significado.
# Cada entrada tiene:
#   "formula"  → string con placeholders {param} para sustituir valores
#   "params"   → dict {nombre_scipy: (símbolo, descripción)}
#   "dominio"  → condición de validez sobre x
_CATALOGO_FDP = {
    "expon": {
        "formula": "f(x) = (1/{scale}) · exp(−(x − {loc}) / {scale})",
        "params": {
            "loc":   ("μ₀",  "desplazamiento (mínimo de la distribución)"),
            "scale": ("1/λ", "media del proceso = 1 / tasa de llegadas λ"),
        },
        "dominio": "x ≥ loc",
    },
    "gamma": {
        "formula": "f(x) = ((x − {loc})^({a}−1) · exp(−(x − {loc}) / {scale})) / ({scale}^{a} · Γ({a}))",
        "params": {
            "a":     ("α", "parámetro de forma (shape)"),
            "loc":   ("μ₀", "desplazamiento"),
            "scale": ("θ", "parámetro de escala (scale) = media / α"),
        },
        "dominio": "x ≥ loc",
    },
    "lognorm": {
        "formula": "f(x) = exp(−(ln(x − {loc}) − {s_mu})² / (2·{s}²)) / ((x − {loc}) · {s} · √(2π))",
        "params": {
            "s":     ("σ", "desviación estándar del logaritmo (shape)"),
            "loc":   ("μ₀", "desplazamiento"),
            "scale": ("exp(μ)", "exp(media del logaritmo) → scale = e^μ"),
        },
        "dominio": "x > loc",
    },
    "weibull_min": {
        "formula": "f(x) = ({c}/{scale}) · ((x − {loc}) / {scale})^({c}−1) · exp(−((x − {loc}) / {scale})^{c})",
        "params": {
            "c":     ("k", "parámetro de forma (shape): k<1 decreciente, k=1 exponencial, k>1 unimodal"),
            "loc":   ("μ₀", "desplazamiento"),
            "scale": ("λ", "parámetro de escala"),
        },
        "dominio": "x ≥ loc",
    },
    "lognorm": {
        "formula": "f(x) = exp(−(ln(x−{loc}) − ln({scale}))² / (2·{s}²)) / ((x−{loc})·{s}·√(2π))",
        "params": {
            "s":     ("σ", "desviación estándar del log (shape)"),
            "loc":   ("μ₀", "desplazamiento"),
            "scale": ("e^μ", "exponencial de la media del log"),
        },
        "dominio": "x > loc",
    },
    "burr12": {
        "formula": "f(x) = ({c}·{d} · (x−{loc})^({c}−1)) / ({scale}^{c} · (1 + ((x−{loc})/{scale})^{c})^({d}+1))",
        "params": {
            "c":     ("c", "primer parámetro de forma"),
            "d":     ("d", "segundo parámetro de forma"),
            "loc":   ("μ₀", "desplazamiento"),
            "scale": ("λ", "parámetro de escala"),
        },
        "dominio": "x ≥ loc",
    },
    "beta": {
        "formula": "f(x) = ((x−{loc})^({a}−1) · ({loc}+{scale}−x)^({b}−1)) / ({scale}^({a}+{b}−1) · B({a},{b}))",
        "params": {
            "a":     ("α", "primer parámetro de forma"),
            "b":     ("β", "segundo parámetro de forma"),
            "loc":   ("μ₀", "desplazamiento (inicio del soporte)"),
            "scale": ("rango", "amplitud del soporte"),
        },
        "dominio": "loc ≤ x ≤ loc + scale",
    },
    "norm": {
        "formula": "f(x) = exp(−(x − {loc})² / (2·{scale}²)) / ({scale} · √(2π))",
        "params": {
            "loc":   ("μ", "media"),
            "scale": ("σ", "desviación estándar"),
        },
        "dominio": "−∞ < x < +∞",
    },
    "uniform": {
        "formula": "f(x) = 1 / {scale}   para   {loc} ≤ x ≤ {loc} + {scale}",
        "params": {
            "loc":   ("a", "valor mínimo"),
            "scale": ("b−a", "amplitud del intervalo"),
        },
        "dominio": "loc ≤ x ≤ loc + scale",
    },
}


def describir_formula_fdp(nombre: str, params: dict) -> None:
    """
    Imprime la fórmula matemática de la FDP con los valores numéricos
    ya sustituidos, junto con el significado de cada parámetro.

    Si la distribución no está en el catálogo, muestra un resumen genérico.

    Args:
        nombre : nombre scipy de la distribución (ej. 'expon', 'gamma').
        params : dict de parámetros tal como lo devuelve Fitter.get_best().
    """
    sep = "─" * 58

    print(f"\n{sep}")
    print(f"  FÓRMULA FDP — {nombre.upper()}")
    print(sep)

    entrada = _CATALOGO_FDP.get(nombre)

    if entrada is None:
        # Distribución no catalogada: mostrar parámetros crudos con aviso
        print(f"  (distribución no catalogada — se muestran parámetros scipy)\n")
        for k, v in params.items():
            print(f"    {k:10s} = {v:.6f}")
        print(f"\n  Consultar: https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.{nombre}.html")
        print(sep)
        return

    # ── Sustituir valores en la fórmula ──────────────────────────────────────
    formula = entrada["formula"]
    for k, v in params.items():
        formula = formula.replace(f"{{{k}}}", f"{v:.4f}")
    # Reemplazo especial para lognorm (s_mu no es un param, es alias)
    formula = formula.replace("{s_mu}", f"{np.log(params.get('scale', 1)):.4f}")

    print(f"\n  f(x) definida para: {entrada['dominio']}\n")
    print(f"  {formula}\n")

    # ── Significado de cada parámetro ────────────────────────────────────────
    print("  Parámetros:")
    for k, v in params.items():
        simbolo, desc = entrada["params"].get(k, (k, "—"))
        print(f"    {k:8s} ({simbolo:6s}) = {v:12.6f}   →  {desc}")

    print(sep)


# =============================================================================
# 6. REPORTE Y VISUALIZACIÓN DEL AJUSTE
# =============================================================================

def reportar_mejor_fdp(f: Fitter, label: str = "IA_min Global", color: str = "steelblue") -> dict:
    """
    Extrae la mejor distribución, imprime su fórmula y grafica
    el histograma original junto con la FDP ajustada.

    Returns:
        dict con claves 'nombre' y 'params'.
    """
    best = f.get_best()
    nombre = list(best.keys())[0]
    params = best[nombre]

    print("\n" + "="*55)
    print(f"  MEJOR FDP — {label}")
    print("="*55)
    print(f"  Distribución : {nombre}")
    print(f"  Parámetros   : {params}")
    print("="*55)

    describir_formula_fdp(nombre, params)

    dist = getattr(stats, nombre)
    ia_vals = f.x
    pdf_fitted = dist.pdf(ia_vals, *params.values())

    fig, ax = plt.subplots(figsize=(9, 4))
    ax.hist(f._data, bins=BINS_HIST, density=True,
            color=color, edgecolor="white", alpha=0.6, label="Datos reales")
    ax.plot(ia_vals, pdf_fitted, color="tomato", lw=2,
            label=f"FDP ajustada: {nombre}")
    ax.set_title(f"{label} — Datos reales vs FDP ajustada")
    ax.set_xlabel("Minutos entre llegadas")
    ax.set_ylabel("Densidad")
    ax.legend()
    plt.tight_layout()
    plt.show()

    return {"nombre": nombre, "params": params}


# =============================================================================
# 7. SEGMENTACIÓN POR TURNOS
# =============================================================================

def asignar_turno(hora: int) -> str:
    """
    Devuelve el código de turno (T1/T2/T3) según la hora del día (0–23).

    T1 — Mañana : 07:00 ≤ hora < 15:00
    T2 — Tarde  : 15:00 ≤ hora < 23:00
    T3 — Noche  : hora ≥ 23:00  OR  hora < 07:00  (cruza medianoche)
    """
    if 7 <= hora < 15:
        return "T1"
    elif 15 <= hora < 23:
        return "T2"
    else:
        return "T3"


def segmentar_por_turno(df_ia: pd.DataFrame) -> dict[str, pd.Series]:
    """
    Agrega la columna 'turno' al DataFrame de IA y devuelve un dict
    con una Serie de IA_min por cada turno.

    Args:
        df_ia : DataFrame con columnas 'IA_min' y 'hora'
                (salida de calcular_ia_min).

    Returns:
        dict {"T1": Serie, "T2": Serie, "T3": Serie}
    """
    df_ia = df_ia.copy()
    df_ia["turno"] = df_ia["hora"].apply(asignar_turno)

    print("\n--- Distribución de intervalos por turno ---")
    for key, (nombre, h_ini, h_fin) in TURNOS.items():
        n = (df_ia["turno"] == key).sum()
        print(f"  {key} [{nombre:6s} {h_ini:02d}:00–{h_fin:02d}:00] : {n:5d} intervalos")

    return {key: df_ia.loc[df_ia["turno"] == key, "IA_min"].reset_index(drop=True)
            for key in TURNOS}


# =============================================================================
# 8. ANÁLISIS COMPLETO POR TURNO
# =============================================================================

def analizar_turno(key: str, ia_turno: pd.Series) -> dict:
    """
    Ejecuta el pipeline completo (EDA → ajuste → reporte) para un turno.

    Args:
        key      : Código del turno ("T1", "T2" o "T3").
        ia_turno : Serie de IA_min del turno.

    Returns:
        dict con 'turno', 'nombre_dist' y 'params'.
    """
    nombre_display, h_ini, h_fin = TURNOS[key]
    label  = f"{key} — {nombre_display} ({h_ini:02d}:00–{h_fin:02d}:00)"
    color  = COLORES_TURNOS[key]

    print(f"\n{'━'*55}")
    print(f"  TURNO {label}")
    print(f"{'━'*55}")

    estadisticas_descriptivas(ia_turno, label=label)
    graficar_exploratorio(ia_turno, label=label, color=color)

    fitter  = ajustar_fdp(ia_turno, label=label)
    resultado = reportar_mejor_fdp(fitter, label=f"IA_min {label}", color=color)

    return {"turno": label, **resultado}


# =============================================================================
# 9. RESUMEN COMPARATIVO FINAL
# =============================================================================

def resumen_comparativo(resultados_globales: dict, resultados_turnos: list[dict]) -> None:
    """
    Imprime una tabla comparativa de las FDPs obtenidas (global + 3 turnos)
    y genera una figura con los 3 histogramas de turnos superpuestos.

    Args:
        resultados_globales : dict {'nombre', 'params'} del análisis global.
        resultados_turnos   : lista de dicts por turno (salida de analizar_turno).
    """
    print("\n" + "="*65)
    print("  RESUMEN COMPARATIVO — FDPs IA_min por turno")
    print("="*65)
    print(f"  {'Segmento':<30} {'Distribución':<18} {'Parámetros'}")
    print(f"  {'-'*30} {'-'*18} {'-'*30}")

    # Fila global
    rg = resultados_globales
    print(f"  {'Global':<30} {rg['nombre']:<18} {rg['params']}")

    # Filas por turno
    for r in resultados_turnos:
        print(f"  {r['turno']:<30} {r['nombre']:<18} {r['params']}")

    print("="*65)

    # ── Gráfico: histogramas de los 3 turnos superpuestos ────────────────────
    fig, ax = plt.subplots(figsize=(11, 4))
    ax.set_title("IA_min por turno — distribuciones comparadas", fontsize=13)

    for r in resultados_turnos:
        # Recuperar el código de turno desde el label ("T1 — Mañana ...")
        key = r["turno"].split(" ")[0]
        nombre_display = TURNOS[key][0]
        color = COLORES_TURNOS[key]

        dist = getattr(stats, r["nombre"])
        x = np.linspace(0, 60, 300)
        y = dist.pdf(x, *r["params"].values())
        ax.plot(x, y, color=color, lw=2.5, label=f"{key} {nombre_display} — {r['nombre']}")

    ax.set_xlabel("Minutos entre llegadas")
    ax.set_ylabel("Densidad")
    ax.legend()
    plt.tight_layout()
    plt.show()

    print("\n[LISTO] FDPs por turno listas para la simulación (TP5).")
    for r in resultados_turnos:
        key = r["turno"].split(" ")[0]
        print(f"  {key}: scipy.stats.{r['nombre']}.rvs(**params_{key.lower()}, size=N_{key.lower()})")


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 55)
    print("  ANÁLISIS IA_min — Intervalo entre Arribos")
    print("  (Global + segmentado por turno)")
    print("=" * 55)

    # ── 1. Carga ──────────────────────────────────────────────────────────────
    df = cargar_datos(PATH_CSV)

    # ── 2. Cálculo de IA_min (devuelve DataFrame con hora) ───────────────────
    df_ia = calcular_ia_min(df)
    ia_global = df_ia["IA_min"]

    # ── 3. EDA global ─────────────────────────────────────────────────────────
    estadisticas_descriptivas(ia_global, label="global")
    graficar_exploratorio(ia_global, label="Global")

    # ── 4 & 6. Ajuste + reporte global ───────────────────────────────────────
    fitter_global   = ajustar_fdp(ia_global, label="global")
    resultado_global = reportar_mejor_fdp(fitter_global, label="IA_min Global")

    # ── 7. Segmentación por turnos ────────────────────────────────────────────
    series_por_turno = segmentar_por_turno(df_ia)

    # ── 8. Análisis individual por turno ──────────────────────────────────────
    resultados_turnos = []
    for key, ia_turno in series_por_turno.items():
        res = analizar_turno(key, ia_turno)
        resultados_turnos.append(res)

    # ── 9. Resumen comparativo ────────────────────────────────────────────────
    resumen_comparativo(resultado_global, resultados_turnos)

    return {"global": resultado_global, "turnos": resultados_turnos}


if __name__ == "__main__":
    main()