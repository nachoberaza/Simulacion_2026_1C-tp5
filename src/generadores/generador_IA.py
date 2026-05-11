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

DIST_DIR = Path(__file__).parent / "distribuciones"

# Turnos y sus rangos horarios
TURNOS = {
    "maniana": (7, 15),   # 07:00 – 15:00
    "tarde":   (15, 23),  # 15:00 – 23:00
    "noche":   None,      # 23:00 – 07:00 (resto)
}


# =============================================================================
# CLASE GENERADOR
# =============================================================================

class GeneradorIA:

    def __init__(self, nombre_dist, params):
        self.nombre_dist = nombre_dist
        self.params      = params
        self.dist        = getattr(stats, nombre_dist)

    def generar(self) -> float:
        valor = self.dist.rvs(**self.params)
        while valor <= 0:
            valor = self.dist.rvs(**self.params)
        return float(valor)

    def __str__(self):
        return f"GeneradorIA(dist={self.nombre_dist}, params={self.params})"


# =============================================================================
# PREPROCESAMIENTO
# =============================================================================

def cargar_datos():
    df = pd.read_csv(PATH_CSV)
    df["dt"] = pd.to_datetime(df[DATE_COL], format="mixed", dayfirst=True)
    df = df.sort_values("dt").reset_index(drop=True)
    return df


def filtrar_por_turno(df: pd.DataFrame, turno: str) -> pd.Series:
    hora = df["dt"].dt.hour
    if turno == "maniana":
        mask = (hora >= 7) & (hora < 15)
    elif turno == "tarde":
        mask = (hora >= 15) & (hora < 23)
    else:
        mask = (hora >= 23) | (hora < 7)

    df_turno = df[mask].copy().reset_index(drop=True)
    
    # Calcular IA solo entre pacientes del mismo día y turno
    df_turno["fecha"] = df_turno["dt"].dt.date
    
    ias = []
    for fecha, grupo in df_turno.groupby("fecha"):
        grupo = grupo.sort_values("dt")
        diff = grupo["dt"].diff().dt.total_seconds() / 60
        diff = diff.dropna()
        diff = diff[diff > 0]
        ias.extend(diff.tolist())
    
    return pd.Series(ias)


def ajustar_distribucion(ia: pd.Series, turno: str):
    print(f"\n[...] Ajustando distribución para turno {turno} ({len(ia)} intervalos)...")
    fitter = Fitter(ia, bins=BINS_HIST)
    fitter.fit()
    best   = fitter.get_best()
    nombre = list(best.keys())[0]
    params = best[nombre]
    print(f"  Mejor distribución: {nombre}")
    print(f"  Parámetros        : {params}")
    return nombre, params


def guardar_config(turno: str, escenario: str, nombre: str, params: dict):
    path = DIST_DIR / f"ia_config_{turno}_{escenario}.json"
    config = {"nombre_dist": nombre, "params": params}
    with open(path, "w") as f:
        json.dump(config, f, indent=4)
    print(f"  [OK] Guardado en: {path}")


# =============================================================================
# CARGA DE GENERADORES
# =============================================================================

def cargar_generador_desde_json(turno: str, escenario: str) -> GeneradorIA:
    file = f"ia_config_{turno}_{escenario}.json"
    path = DIST_DIR / file

    with open(path, "r") as f:
        data = json.load(f)

    return GeneradorIA(nombre_dist=data["nombre_dist"], params=data["params"])


# =============================================================================
# MAIN — genera los 3 configs
# =============================================================================

def main():
    print("=" * 50)
    print("AJUSTE IA POR TURNO — Hospital_ER_Data2.csv")
    print("=" * 50)

    df = cargar_datos()
    print(f"[OK] Registros cargados: {len(df)}")

    for turno in ["maniana", "tarde", "noche"]:
        ia = filtrar_por_turno(df, turno)
        if len(ia) < 10:
            print(f"[AVISO] Turno {turno}: muy pocos datos ({len(ia)}), se omite.")
            continue
        nombre, params = ajustar_distribucion(ia, turno)
        guardar_config(turno, nombre, params)

    print("\n[OK] Configs generados para los 3 turnos.")
    print("\nEjemplos de generación:")
    for turno in ["maniana", "tarde", "noche"]:
        gen = cargar_generador_desde_json(turno)
        vals = [round(gen.generar(), 2) for _ in range(5)]
        print(f"  {turno}: {vals}")


if __name__ == "__main__":
    main()