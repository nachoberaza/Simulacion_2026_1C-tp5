# =============================================================================
# GENERADOR IA_min
# =============================================================================
# Este componente:
#   1. Ajusta la mejor FDP usando Fitter
#   2. Guarda distribución + parámetros
#   3. Permite generar valores aleatorios
#      para usar directamente en la simulación
# =============================================================================
from pathlib import Path
from fitter import Fitter
from scipy import stats
import pandas as pd
import json


# =============================================================================
# CONFIGURACIÓN
# =============================================================================

PATH_CSV = "../../CSV/Hospital_ER_Data2.csv"
DATE_COL = "Patient Admission Date"

BINS_HIST = 50

CONFIG_PATH = Path(__file__).parent / "distribuciones" / "ia_config.json"


class GeneradorIA:

    def __init__(self, nombre_dist, params):

        self.nombre_dist = nombre_dist
        self.params = params

        # Obtiene la distribución scipy
        self.dist = getattr(stats, nombre_dist)

    def generar(self):

        """
        Genera un nuevo intervalo entre arribos
        usando la FDP ajustada.
        """

        valor = self.dist.rvs(**self.params)

        # Evitar valores inválidos
        while valor <= 0:
            valor = self.dist.rvs(**self.params)

        return valor

    def __str__(self):

        return (
            f"GeneradorIA("
            f"dist={self.nombre_dist}, "
            f"params={self.params})"
        )


# =============================================================================
# PREPROCESAMIENTO
# =============================================================================

def cargar_datos():

    df = pd.read_csv(PATH_CSV)

    df["PatientAdmissionDate_dt"] = pd.to_datetime(
        df[DATE_COL],
        format="mixed",
        dayfirst=True
    )

    df = (
        df
        .sort_values("PatientAdmissionDate_dt")
        .reset_index(drop=True)
    )

    return df

def calcular_ia(df):

    ia = (
        df["PatientAdmissionDate_dt"]
        .diff()
        .dt.total_seconds() / 60
    )

    ia = ia.dropna()

    # eliminar negativos y ceros
    ia = ia[ia > 0]

    return ia.reset_index(drop=True)

def ajustar_distribucion(ia):

    print("[...] Ajustando distribuciones...")

    fitter = Fitter(
        ia,
        bins=BINS_HIST
    )

    fitter.fit()

    best = fitter.get_best()

    nombre = list(best.keys())[0]

    params = best[nombre]

    print("\n===================================")
    print("MEJOR DISTRIBUCIÓN ENCONTRADA")
    print("===================================")

    print(f"Distribución: {nombre}")
    print(f"Parámetros : {params}")

    return nombre, params

def guardar_configuracion(nombre, params):

    config = {
        "nombre_dist": nombre,
        "params": params
    }

    with open(CONFIG_PATH, "w") as f:

        json.dump(
            config,
            f,
            indent=4
        )

    print(f"\n[OK] Configuración guardada en:")
    print(CONFIG_PATH)

def cargar_generador_desde_json(path=CONFIG_PATH):

    with open(path, "r") as f:

        data = json.load(f)

    return GeneradorIA(
        nombre_dist=data["nombre_dist"],
        params=data["params"]
    )


# =============================================================================
# MAIN
# =============================================================================

def main():

    print("===================================")
    print("ANÁLISIS IA_min")
    print("===================================")

    # ---------------------------------------------------------
    # 1. CARGAR DATOS
    # ---------------------------------------------------------

    df = cargar_datos()

    print(f"[OK] Registros cargados: {len(df)}")

    # ---------------------------------------------------------
    # 2. CALCULAR IA
    # ---------------------------------------------------------

    ia = calcular_ia(df)

    print(f"[OK] Intervalos calculados: {len(ia)}")

    # ---------------------------------------------------------
    # 3. AJUSTAR FDP
    # ---------------------------------------------------------

    nombre, params = ajustar_distribucion(ia)

    # ---------------------------------------------------------
    # 4. GUARDAR CONFIG
    # ---------------------------------------------------------

    guardar_configuracion(
        nombre,
        params
    )

    # ---------------------------------------------------------
    # 5. CREAR GENERADOR
    # ---------------------------------------------------------

    generador = GeneradorIA(
        nombre_dist=nombre,
        params=params
    )

    print("\n===================================")
    print("EJEMPLOS DE GENERACIÓN")
    print("===================================")

    for i in range(10):

        valor = generador.generar()

        print(
            f"IA #{i+1}: "
            f"{valor:.4f} minutos"
        )


# =============================================================================
# EJECUCIÓN
# =============================================================================

if __name__ == "__main__":

    main()