# =============================================================================
# GENERADOR TIEMPO DE ATENCIÓN
# =============================================================================
# Este componente:
# 1. Ajusta la mejor FDP para TAE (tiempo atención especialista)
#    y TAC (tiempo atención clínico) usando Fitter
# 2. Guarda distribución + parámetros en distribuciones/tiempo_atencion_config.json
# 3. Permite generar valores aleatorios positivos para cada tipo
#
# Columnas del CSV usadas:
#   - "Patient Wait Time" : tiempo de espera en minutos (no lo usamos para TAE/TAC)
#   - "Department Referral" : para separar especialista vs clínico
#
# NOTA: El CSV de Hospital_ER_Data.csv tiene la columna "Patients Initial Assessment"
# que indica el tipo de triage, y podemos inferir el tipo de médico requerido.
# Si el CSV tiene una columna directa de duración de atención, se usa esa.
# En caso contrario, se usa "Patient Satisfaction Score" como proxy o se ajusta
# sobre "Patient Wait Time" diferenciando por tipo de paciente.
#
# Ajustamos sobre "Patient Wait Time" segmentado por TipoPaciente
# (especialista = niveles 1,2,3 / clínico = nivel 4).
# =============================================================================

from fitter import Fitter
from scipy import stats
import pandas as pd
import json

# =============================================================================
# CONFIGURACIÓN
# =============================================================================

PATH_CSV      = "../CSV/Hospital_ER_Data.csv"
DATE_COL      = "Patient Admission Date"
WAIT_COL      = "Patient Wait Time"          # minutos de espera (proxy para atención)
ACUITY_COL    = "Patient Initial Assessment" # columna de nivel de triage en este CSV
CONFIG_OUTPUT = "../distribuciones/tiempo_atencion_config.json"

BINS_HIST = 50

# Niveles del CSV que van a especialista (1,2,3) y clínico (4,5)
NIVELES_ESPECIALISTA = {1, 2, 3}
NIVELES_CLINICO      = {4, 5}


# =============================================================================
# CLASE GENERADOR
# =============================================================================

class GeneradorTiempoAtencion:
    """
    Genera tiempos de atención para especialistas y clínicos
    usando las FDP ajustadas desde los datos reales.

    Parámetros
    ----------
    nombre_dist_esp : str
        Nombre de la distribución scipy para especialistas.
    params_esp : dict
        Parámetros de la distribución de especialistas.
    nombre_dist_cli : str
        Nombre de la distribución scipy para clínicos.
    params_cli : dict
        Parámetros de la distribución de clínicos.
    """

    def __init__(self, nombre_dist_esp, params_esp, nombre_dist_cli, params_cli):
        self.nombre_dist_esp = nombre_dist_esp
        self.params_esp      = params_esp
        self.nombre_dist_cli = nombre_dist_cli
        self.params_cli      = params_cli

        self.dist_esp = getattr(stats, nombre_dist_esp)
        self.dist_cli = getattr(stats, nombre_dist_cli)

    def generar_especialista(self) -> float:
        """Genera un tiempo de atención de especialista (minutos, > 0)."""
        valor = self.dist_esp.rvs(**self.params_esp)
        while valor <= 0:
            valor = self.dist_esp.rvs(**self.params_esp)
        return float(valor)

    def generar_clinico(self) -> float:
        """Genera un tiempo de atención clínico (minutos, > 0)."""
        valor = self.dist_cli.rvs(**self.params_cli)
        while valor <= 0:
            valor = self.dist_cli.rvs(**self.params_cli)
        return float(valor)

    def __str__(self):
        return (
            f"GeneradorTiempoAtencion(\n"
            f"  especialista: dist={self.nombre_dist_esp}, params={self.params_esp}\n"
            f"  clínico     : dist={self.nombre_dist_cli}, params={self.params_cli}\n"
            f")"
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
    """
    Separa los tiempos de atención para especialistas y clínicos.

    Busca la columna de nivel de triage y la de tiempo de atención.
    Retorna dos Series con valores positivos.
    """
    # Detectar columna de nivel de triage (puede variar entre datasets)
    posibles_acuity = [
        "Patient Initial Assessment",
        "acuity",
        "Triage Level",
        "triage_level",
    ]
    col_acuity = None
    for col in posibles_acuity:
        if col in df.columns:
            col_acuity = col
            break

    # Detectar columna de tiempo de atención
    posibles_tiempo = [
        "Patient Wait Time",
        "wait_time",
        "Wait Time",
        "treatment_duration",
        "Treatment Duration",
    ]
    col_tiempo = None
    for col in posibles_tiempo:
        if col in df.columns:
            col_tiempo = col
            break

    if col_tiempo is None:
        raise ValueError(
            f"No se encontró columna de tiempo de atención. "
            f"Columnas disponibles: {list(df.columns)}"
        )

    print(f"[OK] Columna de triage usada : '{col_acuity}'")
    print(f"[OK] Columna de tiempo usada : '{col_tiempo}'")

    # Limpiar: eliminar nulos y valores <= 0
    df_clean = df[[col_acuity, col_tiempo]].dropna()
    df_clean = df_clean[df_clean[col_tiempo] > 0].copy()
    df_clean[col_acuity] = df_clean[col_acuity].astype(int)

    if col_acuity is not None:
        mask_esp = df_clean[col_acuity].isin(NIVELES_ESPECIALISTA)
        mask_cli = df_clean[col_acuity].isin(NIVELES_CLINICO)
        tiempos_esp = df_clean.loc[mask_esp, col_tiempo].reset_index(drop=True)
        tiempos_cli = df_clean.loc[mask_cli, col_tiempo].reset_index(drop=True)
    else:
        # Sin columna de triage: usar todos los registros para ambas distribuciones
        print("[AVISO] Sin columna de triage — ajustando misma distribución para ambos tipos.")
        tiempos_esp = df_clean[col_tiempo].reset_index(drop=True)
        tiempos_cli = df_clean[col_tiempo].reset_index(drop=True)

    print(f"[OK] Tiempos especialista : {len(tiempos_esp)} registros")
    print(f"[OK] Tiempos clínico      : {len(tiempos_cli)} registros")

    return tiempos_esp, tiempos_cli


def ajustar_distribucion(serie: pd.Series, label: str):
    """Ajusta la mejor FDP para la serie dada usando Fitter."""
    print(f"\n[...] Ajustando distribución para: {label}...")
    fitter = Fitter(serie, bins=BINS_HIST)
    fitter.fit()
    best = fitter.get_best()
    nombre = list(best.keys())[0]
    params = best[nombre]

    print(f"  Distribución : {nombre}")
    print(f"  Parámetros   : {params}")
    return nombre, params


def guardar_configuracion(
    nombre_esp, params_esp,
    nombre_cli, params_cli
):
    config = {
        "especialista": {
            "nombre_dist": nombre_esp,
            "params":      params_esp,
        },
        "clinico": {
            "nombre_dist": nombre_cli,
            "params":      params_cli,
        },
    }
    with open(CONFIG_OUTPUT, "w") as f:
        json.dump(config, f, indent=4)
    print(f"\n[OK] Configuración guardada en: {CONFIG_OUTPUT}")


def cargar_generador_desde_json(path: str) -> GeneradorTiempoAtencion:
    with open(path, "r") as f:
        data = json.load(f)
    return GeneradorTiempoAtencion(
        nombre_dist_esp = data["especialista"]["nombre_dist"],
        params_esp      = data["especialista"]["params"],
        nombre_dist_cli = data["clinico"]["nombre_dist"],
        params_cli      = data["clinico"]["params"],
    )


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("===================================")
    print("ANÁLISIS TIEMPOS DE ATENCIÓN")
    print("===================================")

    # 1. Cargar datos
    df = cargar_datos()

    # 2. Extraer tiempos por tipo
    tiempos_esp, tiempos_cli = extraer_tiempos(df)

    # 3. Ajustar distribuciones
    print("\n===================================")
    print("AJUSTE DE DISTRIBUCIONES")
    print("===================================")
    nombre_esp, params_esp = ajustar_distribucion(tiempos_esp, "Especialista (TAE)")
    nombre_cli, params_cli = ajustar_distribucion(tiempos_cli, "Clínico (TAC)")

    # 4. Guardar configuración
    guardar_configuracion(nombre_esp, params_esp, nombre_cli, params_cli)

    # 5. Crear generador y mostrar ejemplos
    generador = GeneradorTiempoAtencion(
        nombre_dist_esp=nombre_esp,
        params_esp=params_esp,
        nombre_dist_cli=nombre_cli,
        params_cli=params_cli,
    )

    print("\n===================================")
    print("EJEMPLOS DE GENERACIÓN")
    print("===================================")
    for i in range(5):
        tae = generador.generar_especialista()
        tac = generador.generar_clinico()
        print(f"  TAE #{i+1}: {tae:.4f} min   |   TAC #{i+1}: {tac:.4f} min")


if __name__ == "__main__":
    main()
