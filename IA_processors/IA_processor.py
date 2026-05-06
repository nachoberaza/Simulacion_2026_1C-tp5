# -*- coding: utf-8 -*-
"""
ia_min_analysis.py
==================
Análisis de la variable "Intervalo entre Arribos de Pacientes" (IA_min).

Dataset requerido: Hospital ER_Data.csv
    - Columna clave: 'Patient Admission Date' (datetime parseable)

Pasos:
    1. Carga del CSV
    2. Cálculo de IA_min (diferencia entre llegadas consecutivas, en minutos)
    3. Análisis exploratorio (estadísticas + visualizaciones)
    4. Ajuste de FDP con Fitter
    5. Reporte final con los parámetros de la mejor distribución
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

PATH_CSV = "../CSV/Hospital_ER_Data.csv"  # ← Ajustar según entorno local
DATE_COL = "Patient Admission Date"
BINS_HIST = 50
TOP_N_DISTRIBUTIONS = 10


# =============================================================================
# 1. CARGA DE DATOS
# =============================================================================

def cargar_datos(path: str) -> pd.DataFrame:
    """
    Lee el CSV y devuelve un DataFrame con la columna de fecha ya parseada
    y ordenada cronológicamente.
    """
    df = pd.read_csv(path)
    df["PatientAdmissionDate_dt"] = pd.to_datetime(df[DATE_COL], dayfirst=True)
    df = df.sort_values("PatientAdmissionDate_dt").reset_index(drop=True)
    print(f"[OK] Dataset cargado: {df.shape[0]} registros, {df.shape[1]} columnas.")
    return df


# =============================================================================
# 2. CÁLCULO DE IA_min
# =============================================================================

def calcular_ia_min(df: pd.DataFrame) -> pd.Series:
    """
    Calcula el intervalo entre llegadas consecutivas en minutos (IA_min).
    Elimina el primer registro (NaN por .diff()) y valores negativos/nulos.

    Returns:
        Serie con los intervalos válidos en minutos.
    """
    ia = df["PatientAdmissionDate_dt"].diff().dt.total_seconds() / 60
    ia = ia.dropna()
    ia = ia[ia > 0]
    print(f"[OK] IA_min calculado: {len(ia)} intervalos válidos.")
    return ia.reset_index(drop=True)


# =============================================================================
# 3. ANÁLISIS EXPLORATORIO
# =============================================================================

def estadisticas_descriptivas(ia: pd.Series) -> None:
    """Imprime estadísticas descriptivas de IA_min."""
    print("\n--- Estadísticas descriptivas: IA_min (minutos) ---")
    print(ia.describe().round(4).to_string())
    print(f"  Skewness : {ia.skew():.4f}")
    print(f"  Kurtosis : {ia.kurt():.4f}")


def graficar_exploratorio(ia: pd.Series) -> None:
    """Genera histograma y boxplot de IA_min en una sola figura."""
    fig, axes = plt.subplots(1, 2, figsize=(13, 4))
    fig.suptitle("Análisis exploratorio — Intervalo entre Arribos (IA_min)", fontsize=13)

    # Histograma
    axes[0].hist(ia, bins=BINS_HIST, color="steelblue", edgecolor="white", alpha=0.85)
    axes[0].set_title("Histograma")
    axes[0].set_xlabel("Minutos entre llegadas")
    axes[0].set_ylabel("Frecuencia")

    # Boxplot
    axes[1].boxplot(ia, vert=True, patch_artist=True,
                    boxprops=dict(facecolor="steelblue", alpha=0.6))
    axes[1].set_title("Boxplot")
    axes[1].set_ylabel("Minutos entre llegadas")

    plt.tight_layout()
    plt.show()


# =============================================================================
# 4. AJUSTE DE FDP
# =============================================================================

def ajustar_fdp(ia: pd.Series, top_n: int = TOP_N_DISTRIBUTIONS) -> Fitter:
    """
    Ajusta múltiples distribuciones sobre IA_min con Fitter y muestra
    un resumen de las mejores según la métrica SSE.

    Returns:
        Objeto Fitter ya ajustado.
    """
    print(f"\n[...] Ajustando distribuciones (puede tardar unos segundos)...")
    f = Fitter(ia, bins=BINS_HIST)
    f.fit()
    print(f"\n=== Top {top_n} distribuciones — IA_min ===")
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

def reportar_mejor_fdp(f: Fitter) -> dict:  # sección 6
    """
    Extrae la mejor distribución y sus parámetros, los imprime y
    grafica el histograma original junto con la FDP ajustada.

    Returns:
        dict con claves 'nombre' y 'params'.
    """
    best = f.get_best()
    nombre = list(best.keys())[0]
    params = best[nombre]

    print("\n" + "="*55)
    print("  MEJOR FDP — IA_min (Intervalo entre Arribos)")
    print("="*55)
    print(f"  Distribución : {nombre}")
    print(f"  Parámetros   : {params}")
    print("="*55)

    # Fórmula matemática con valores sustituidos
    describir_formula_fdp(nombre, params)

    # Gráfico: datos reales vs FDP ajustada
    dist = getattr(stats, nombre)
    ia_vals = f.x                          # puntos del histograma (eje x)
    pdf_fitted = dist.pdf(ia_vals, *params.values())

    fig, ax = plt.subplots(figsize=(9, 4))
    ax.hist(f._data, bins=BINS_HIST, density=True,
            color="steelblue", edgecolor="white", alpha=0.6, label="Datos reales")
    ax.plot(ia_vals, pdf_fitted, color="tomato", lw=2,
            label=f"FDP ajustada: {nombre}")
    ax.set_title("IA_min — Datos reales vs FDP ajustada")
    ax.set_xlabel("Minutos entre llegadas")
    ax.set_ylabel("Densidad")
    ax.legend()
    plt.tight_layout()
    plt.show()

    return {"nombre": nombre, "params": params}


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 55)
    print("  ANÁLISIS IA_min — Intervalo entre Arribos")
    print("=" * 55)

    # 1. Carga
    df = cargar_datos(PATH_CSV)

    # 2. Cálculo
    ia = calcular_ia_min(df)

    # 3. EDA
    estadisticas_descriptivas(ia)
    graficar_exploratorio(ia)

    # 4. Ajuste
    fitter = ajustar_fdp(ia)

    # 5. Reporte
    resultado = reportar_mejor_fdp(fitter)

    print("\n[LISTO] FDP lista para usar en simulación (TP5):")
    print(f"  scipy.stats.{resultado['nombre']}.rvs(**params, size=N)")
    return resultado


if __name__ == "__main__":
    main()