from fitter import Fitter
from scipy import stats
import pandas as pd
import json


# =============================================================================
# CONFIGURACIÓN
# =============================================================================

PATH_CSV = "../../CSV/Hospital_ER_Data2.csv"

WAIT_COL = "Patient Waittime"

CONFIG_OUTPUT = "../distribuciones/tiempo_atencion_config.json"

BINS_HIST = 50


# =============================================================================
# CLASE GENERADOR
# =============================================================================

class GeneradorTiempoAtencion:

    def __init__(self, nombre_dist, params):

        self.nombre_dist = nombre_dist
        self.params = params

        self.dist = getattr(stats, nombre_dist)

    def generar(self) -> float:

        valor = self.dist.rvs(**self.params)

        while valor <= 0:

            valor = self.dist.rvs(**self.params)

        return float(valor)

    def __str__(self):

        return (
            f"GeneradorTiempoAtencion("
            f"dist={self.nombre_dist}, "
            f"params={self.params})"
        )


# =============================================================================
# PREPROCESAMIENTO
# =============================================================================

def cargar_datos():

    df = pd.read_csv(PATH_CSV)

    print(f"[OK] Registros cargados: {len(df)}")

    print(f"[OK] Columnas disponibles: {list(df.columns)}")

    return df


def extraer_tiempos(df):

    col_tiempo = WAIT_COL

    if col_tiempo not in df.columns:

        raise ValueError(
            f"No existe la columna '{col_tiempo}'"
        )

    print(f"[OK] Columna usada: '{col_tiempo}'")

    tiempos = (
        df[col_tiempo]
        .dropna()
    )

    tiempos = tiempos[
        tiempos > 0
    ]

    tiempos = tiempos.reset_index(drop=True)

    print(f"[OK] Registros válidos: {len(tiempos)}")

    return tiempos


# =============================================================================
# AJUSTE FDP
# =============================================================================

def ajustar_distribucion(serie: pd.Series):

    print("\n[...] Ajustando distribución...")

    fitter = Fitter(
        serie,
        bins=BINS_HIST
    )

    fitter.fit()

    best = fitter.get_best()

    nombre = list(best.keys())[0]

    params = best[nombre]

    print("\n===================================")
    print("MEJOR DISTRIBUCIÓN")
    print("===================================")

    print(f"Distribución : {nombre}")

    print(f"Parámetros   : {params}")

    return nombre, params


# =============================================================================
# SERIALIZACIÓN
# =============================================================================

def guardar_configuracion(nombre, params):

    config = {
        "nombre_dist": nombre,
        "params": params
    }

    with open(CONFIG_OUTPUT, "w") as f:

        json.dump(
            config,
            f,
            indent=4
        )

    print(f"\n[OK] Configuración guardada en:")
    print(CONFIG_OUTPUT)


def cargar_generador_desde_json(path):

    with open(path, "r") as f:

        data = json.load(f)

    return GeneradorTiempoAtencion(
        nombre_dist=data["nombre_dist"],
        params=data["params"]
    )


# =============================================================================
# MAIN
# =============================================================================

def main():

    print("===================================")
    print("ANÁLISIS TIEMPO DE ATENCIÓN")
    print("===================================")

    # ---------------------------------------------------------
    # 1. CARGAR DATOS
    # ---------------------------------------------------------

    df = cargar_datos()

    # ---------------------------------------------------------
    # 2. EXTRAER TIEMPOS
    # ---------------------------------------------------------

    tiempos = extraer_tiempos(df)

    # ---------------------------------------------------------
    # 3. AJUSTAR FDP
    # ---------------------------------------------------------

    nombre, params = ajustar_distribucion(tiempos)

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

    generador = GeneradorTiempoAtencion(
        nombre_dist=nombre,
        params=params
    )

    print("\n===================================")
    print("EJEMPLOS DE GENERACIÓN")
    print("===================================")

    for i in range(10):

        valor = generador.generar()

        print(
            f"TA #{i+1}: "
            f"{valor:.4f} minutos"
        )


# =============================================================================
# EJECUCIÓN
# =============================================================================

if __name__ == "__main__":

    main()