# -*- coding: utf-8 -*-
"""TP4.ipynb - Actualizado

# TP N°.4 - Generación de funciones de densidad de probabilidad

| # | Integrantes |
|---|---|
| 1 | Juan Martin Terrizzi |
| 2 | Ignacio Martinez Beraza |
| 3 | Yoel Ibarra |
| 4 | German Agustin Lechner |

## Objetivo
El trabajo propuesto consiste en que el grupo realice una selección de un set de datos de interés,
el procesamiento de datos del mismo, la obtención de una función de densidad de probabilidad que
ajuste dichos datos y la presentación del análisis realizado.

"""

# =============================================================================
# 1. CARGA DE BIBLIOTECAS
# =============================================================================

#pip install fitter

from fitter import Fitter
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from scipy import stats

# =============================================================================
# 2. PATHS Y CARGA DE DATOS
# =============================================================================

# ── Paths Google Colab (Drive)
PATH_CSV_MAIN_DRIVE    = '/content/drive/MyDrive/Colab Notebooks/TPs/TP4/Datos/Hospital ER_Data.csv'
PATH_CSV_TRIAGE_DRIVE  = '/content/drive/MyDrive/Colab Notebooks/TPs/TP4/Datos/triage.csv'
PATH_CSV_EDSTAYS_DRIVE = '/content/drive/MyDrive/Colab Notebooks/TPs/TP4/Datos/edstays.csv'

# ── Paths local
PATH_CSV_MAIN    = 'CSV/Hospital ER_Data.csv'
PATH_CSV_TRIAGE  = 'CSV/triage.csv'
PATH_CSV_EDSTAYS = 'CSV/edstays.csv'

# ── Carga de datasets (alternar entre Drive y local según entorno)
Atenciones_ER = pd.read_csv(PATH_CSV_MAIN)
df_triage     = pd.read_csv(PATH_CSV_TRIAGE)
df_edstays    = pd.read_csv(PATH_CSV_EDSTAYS)

# =============================================================================
# 3. ANÁLISIS EXPLORATORIO DE DATOS — Dataset principal (Hospital ER_Data.csv)
# =============================================================================

print("=== Hospital ER_Data.csv ===")
print(type(Atenciones_ER))
print(Atenciones_ER.head())
print(Atenciones_ER.columns.tolist())
print(Atenciones_ER['Department Referral'].value_counts())
print(Atenciones_ER.shape)
print(Atenciones_ER.dtypes)

# =============================================================================
# 4. PREPARACIÓN DE DATOS — Dataset principal (Hospital ER_Data.csv)
# =============================================================================

# ── Intervalo entre llegadas (IA_min) ─────────────────────────────────────────
# Convertimos la columna de fecha a datetime y ordenamos cronológicamente
Atenciones_ER['PatientAdmissionDate_dt'] = pd.to_datetime(
    Atenciones_ER['Patient Admission Date']
)
Atenciones_ER = Atenciones_ER.sort_values('PatientAdmissionDate_dt').reset_index(drop=True)

# .diff() calcula la diferencia entre fecha/hora consecutivas → intervalo entre llegadas
Atenciones_ER['IA_min'] = (
    Atenciones_ER['PatientAdmissionDate_dt'].diff().dt.total_seconds() / 60
)
Atenciones_ER = Atenciones_ER.dropna(subset=['IA_min'])

# Visualización IA
Atenciones_ER.hist('IA_min', bins=50)
plt.title('Histograma — Intervalo entre llegadas (IA_min)')
plt.xlabel('Minutos')
plt.tight_layout()
plt.show()

Atenciones_ER.boxplot('IA_min')
plt.title('Boxplot — Intervalo entre llegadas (IA_min)')
plt.tight_layout()
plt.show()

# ── Wait Time ─────────────────────────────────────────────────────────────────
Atenciones_ER.hist('Patient Waittime', bins=10)
plt.title('Histograma — Tiempo de espera')
plt.xlabel('Minutos')
plt.tight_layout()
plt.show()

Atenciones_ER.boxplot('Patient Waittime')
plt.title('Boxplot — Tiempo de espera')
plt.tight_layout()
plt.show()

# =============================================================================
# 4B. PREPARACIÓN DE DATOS — triage.csv
# =============================================================================
"""
El dataset triage.csv contiene la columna "acuity" con el nivel de triage asignado
a cada paciente (valores discretos, típicamente del 1 al 5 en la escala ESI/Manchester).
Se analiza su distribución para modelar la mezcla de pacientes en la simulación.
"""

print("\n=== triage.csv ===")
print(df_triage.head())
print(df_triage.dtypes)
print(df_triage['acuity'].value_counts().sort_index())

# Visualización de acuity
fig, ax = plt.subplots(figsize=(7, 4))
df_triage['acuity'].value_counts().sort_index().plot(kind='bar', ax=ax, color='steelblue')
ax.set_title('Distribución de niveles de Triage (acuity)')
ax.set_xlabel('Nivel de triage')
ax.set_ylabel('Frecuencia')
plt.tight_layout()
plt.show()

# =============================================================================
# 4C. PREPARACIÓN DE DATOS — edstays.csv → Tiempo de Estadía Total (TET)
# =============================================================================
"""
edstays.csv contiene las columnas "intime" y "outtime" con la hora de ingreso
y egreso de cada paciente en el área de emergencias.
TET (min) = outtime − intime  →  tiempo total que el paciente estuvo en la guardia.

Luego, unimos TET al dataset principal (por fecha de ingreso aproximada o como
distribución independiente) para obtener:
    TA (Tiempo de Atención) = TET − Wait Time
"""

print("\n=== edstays.csv ===")
print(df_edstays.head())
print(df_edstays.dtypes)

# Conversión a datetime
df_edstays['intime']  = pd.to_datetime(df_edstays['intime'])
df_edstays['outtime'] = pd.to_datetime(df_edstays['outtime'])

# Cálculo del TET en minutos
df_edstays['TET_min'] = (
    (df_edstays['outtime'] - df_edstays['intime']).dt.total_seconds() / 60
)

# Filtramos valores negativos o nulos (datos inconsistentes)
df_edstays = df_edstays[df_edstays['TET_min'] > 0].dropna(subset=['TET_min'])

print(f"\nTET_min — estadísticas descriptivas:")
print(df_edstays['TET_min'].describe())

# Visualización del TET
fig, axes = plt.subplots(1, 2, figsize=(12, 4))
axes[0].hist(df_edstays['TET_min'], bins=50, color='mediumseagreen', edgecolor='white')
axes[0].set_title('Histograma — TET (min)')
axes[0].set_xlabel('Minutos')
axes[0].set_ylabel('Frecuencia')
df_edstays.boxplot('TET_min', ax=axes[1])
axes[1].set_title('Boxplot — TET (min)')
plt.tight_layout()
plt.show()

# ── Cálculo de TA: unimos TET al dataset principal vía distribución ───────────
"""
Como edstays.csv y Hospital ER_Data.csv no comparten una clave directa,
usamos los parámetros de la FDP del TET para generar valores sintéticos de TET
y luego calcular TA = TET − Wait Time para cada registro del dataset principal.
Los valores de TA negativos (TET < Wait Time por redondeos) se descartan.
"""

# =============================================================================
# 5. AJUSTE DE FDPs
# =============================================================================

# ── 5.1 Patient Waittime ──────────────────────────────────────────────────────
fdp_WT = Fitter(Atenciones_ER['Patient Waittime'], bins=10)
fdp_WT.fit()
print("\n=== FDP — Patient Waittime (10 mejores) ===")
fdp_WT.summary(10)

# ── 5.2 Intervalo entre llegadas (IA_min) ─────────────────────────────────────
fdp_IA = Fitter(Atenciones_ER['IA_min'])
fdp_IA.fit()
print("\n=== FDP — IA_min (10 mejores) ===")
fdp_IA.summary(10)

# ── 5.3 Triage (acuity) ───────────────────────────────────────────────────────
"""
"acuity" es una variable discreta ordinal (p.ej. 1-5).
Ajustamos tanto distribuciones continuas (para comparar) como calculamos
las proporciones empíricas, que son el input directo para la simulación.
"""
acuity_values = df_triage['acuity'].dropna()

# Proporciones empíricas (uso directo en simulación con np.random.choice)
acuity_probs = acuity_values.value_counts(normalize=True).sort_index()
print("\n=== Proporciones de Triage (acuity) ===")
print(acuity_probs)

# Ajuste continuo como referencia
fdp_triage = Fitter(acuity_values, bins=5)
fdp_triage.fit()
print("\n=== FDP — Triage/acuity (10 mejores) ===")
fdp_triage.summary(10)

# ── 5.4 TET (Tiempo de Estadía Total) ────────────────────────────────────────
fdp_TET = Fitter(df_edstays['TET_min'], bins=50)
fdp_TET.fit()
print("\n=== FDP — TET_min (10 mejores) ===")
fdp_TET.summary(10)

# =============================================================================
# 6. CÁLCULO DE TA (Tiempo de Atención)
# =============================================================================

N = len(Atenciones_ER)
np.random.seed(42)

# Generamos TET sintético con la mejor distribución obtenida del ajuste
params_tet         = fdp_TET.get_best()
best_dist_tet_name = list(params_tet.keys())[0]
best_params_tet    = params_tet[best_dist_tet_name]
dist_tet           = getattr(stats, best_dist_tet_name)

TET_simulado = dist_tet.rvs(*best_params_tet.values(), size=N)

print(f"\nDistribución TET : {best_dist_tet_name}")
print(f"Parámetros       : {best_params_tet}")

# TA = TET − Wait Time  (descartamos valores ≤ 0)
Atenciones_ER['TET_sim'] = TET_simulado
Atenciones_ER['TA_min']  = Atenciones_ER['TET_sim'] - Atenciones_ER['Patient Waittime']
df_TA = Atenciones_ER[Atenciones_ER['TA_min'] > 0]['TA_min']

print(f"\nRegistros con TA > 0: {len(df_TA)} de {N}")
print(df_TA.describe())

# Visualización de TA
fig, axes = plt.subplots(1, 2, figsize=(12, 4))
axes[0].hist(df_TA, bins=50, color='darkorange', edgecolor='white')
axes[0].set_title('Histograma — TA (min)')
axes[0].set_xlabel('Minutos')
axes[0].set_ylabel('Frecuencia')
df_TA_df = df_TA.to_frame()
df_TA_df.boxplot('TA_min', ax=axes[1])
axes[1].set_title('Boxplot — TA (min)')
plt.tight_layout()
plt.show()

# ── 5.5 FDP para TA ───────────────────────────────────────────────────────────
fdp_TA = Fitter(df_TA, bins=50)
fdp_TA.fit()
print("\n=== FDP — TA_min (10 mejores) ===")
fdp_TA.summary(10)

# =============================================================================
# 7. SIMULACIÓN — Generación de datos con las FDPs obtenidas
# =============================================================================

np.random.seed(42)

# ── Mejor FDP para cada variable ──────────────────────────────────────────────

# Patient Waittime
params_wt          = fdp_WT.get_best()
best_dist_wt_name  = list(params_wt.keys())[0]
best_params_wt     = params_wt[best_dist_wt_name]
dist_wt            = getattr(stats, best_dist_wt_name)
datos_sim_wt       = dist_wt.rvs(*best_params_wt.values(), size=N)

print(f"Distribución WT  : {best_dist_wt_name}  |  Params: {best_params_wt}")

# IA_min
params_ia          = fdp_IA.get_best()
best_dist_ia_name  = list(params_ia.keys())[0]
best_params_ia     = params_ia[best_dist_ia_name]
dist_ia            = getattr(stats, best_dist_ia_name)
datos_sim_ia       = dist_ia.rvs(*best_params_ia.values(), size=N)

print(f"Distribución IA  : {best_dist_ia_name}  |  Params: {best_params_ia}")

# TA
params_ta          = fdp_TA.get_best()
best_dist_ta_name  = list(params_ta.keys())[0]
best_params_ta     = params_ta[best_dist_ta_name]
dist_ta            = getattr(stats, best_dist_ta_name)
datos_sim_ta       = dist_ta.rvs(*best_params_ta.values(), size=N)

print(f"Distribución TA  : {best_dist_ta_name}  |  Params: {best_params_ta}")

# Triage: variable discreta → usamos proporciones empíricas
niveles   = acuity_probs.index.tolist()
probs     = acuity_probs.values.tolist()
datos_sim_triage = np.random.choice(niveles, size=N, p=probs)

print(f"Triage simulado  : proporciones empíricas {dict(zip(niveles, [round(p,3) for p in probs]))}")

# =============================================================================
# 8. VERIFICACIÓN — Originales vs Simulados
# =============================================================================

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle("Comparación datos originales vs simulados", fontsize=14)

# WT
axes[0,0].hist(Atenciones_ER['Patient Waittime'], bins=10, density=True,
               alpha=0.5, color='steelblue', label='Original')
axes[0,0].hist(datos_sim_wt, bins=10, density=True,
               alpha=0.5, color='tomato', label='Simulado')
axes[0,0].set_title(f"Patient Waittime — {best_dist_wt_name}")
axes[0,0].set_xlabel("Minutos de espera")
axes[0,0].set_ylabel("Densidad")
axes[0,0].legend()

# IA
axes[0,1].hist(Atenciones_ER['IA_min'], bins=50, density=True,
               alpha=0.5, color='steelblue', label='Original')
axes[0,1].hist(datos_sim_ia, bins=50, density=True,
               alpha=0.5, color='tomato', label='Simulado')
axes[0,1].set_title(f"IA_min — {best_dist_ia_name}")
axes[0,1].set_xlabel("Minutos entre llegadas")
axes[0,1].set_ylabel("Densidad")
axes[0,1].legend()

# TA
axes[1,0].hist(df_TA, bins=50, density=True,
               alpha=0.5, color='steelblue', label='Original (derivado)')
axes[1,0].hist(datos_sim_ta, bins=50, density=True,
               alpha=0.5, color='tomato', label='Simulado')
axes[1,0].set_title(f"TA_min — {best_dist_ta_name}")
axes[1,0].set_xlabel("Minutos de atención")
axes[1,0].set_ylabel("Densidad")
axes[1,0].legend()

# Triage
axes[1,1].bar(niveles, probs, color='steelblue', alpha=0.6, label='Original')
unique, counts = np.unique(datos_sim_triage, return_counts=True)
axes[1,1].bar(unique, counts/counts.sum(), color='tomato', alpha=0.6, label='Simulado')
axes[1,1].set_title("Triage (acuity) — proporciones empíricas")
axes[1,1].set_xlabel("Nivel de triage")
axes[1,1].set_ylabel("Proporción")
axes[1,1].legend()

plt.tight_layout()
plt.show()

# =============================================================================
# 9. RESUMEN DE FDPs PARA LA SIMULACIÓN (TP5)
# =============================================================================
print("\n" + "="*60)
print("RESUMEN — FDPs listas para la simulación (TP5)")
print("="*60)
print(f"  IA (Intervalo entre Arribos) : {best_dist_ia_name}  {best_params_ia}")
print(f"  TA (Tiempo de Atención)      : {best_dist_ta_name}  {best_params_ta}")
print(f"  TET (Estadía Total)          : {best_dist_tet_name} {best_params_tet}")
print(f"  Triage / acuity              : Discreta empírica — {dict(zip(niveles, [round(p,3) for p in probs]))}")
print("="*60)

# =============================================================================
# 10. NOTA SOBRE LA SIMULACIÓN POR TURNOS (TP5) — ¿Qué más hace falta?
# =============================================================================
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  ANÁLISIS PARA SIMULACIÓN POR TURNOS — LO QUE FALTA                        ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  TURNOS PROPUESTOS (3 turnos de 8 horas):                                   ║
║    T1: 07:00 – 15:00  (mañana)                                              ║
║    T2: 15:00 – 23:00  (tarde)                                               ║
║    T3: 23:00 – 07:00  (noche)                                               ║
║                                                                              ║
║  FDPs YA DISPONIBLES (globales):                                            ║
║    ✔ IA_min   → intervalo entre llegadas                                    ║
║    ✔ TA_min   → tiempo de atención                                          ║
║    ✔ Triage   → nivel de urgencia (acuity)                                  ║
║                                                                              ║
║  FDPs / DATOS ADICIONALES NECESARIOS:                                       ║
║                                                                              ║
║  1. IA_min POR TURNO ← MÁS IMPORTANTE                                      ║
║     El flujo de pacientes no es homogéneo durante el día. Hay que:          ║
║     • Extraer la hora de ingreso de 'Patient Admission Date'                ║
║     • Segmentar el dataset en los 3 turnos                                  ║
║     • Ajustar una FDP de IA_min para cada turno por separado                ║
║     → Sin esto, la simulación ignora el pico de mañana/tarde                ║
║                                                                              ║
║  2. PROPORCIÓN Clínico / Especialista POR TURNO                             ║
║     De la columna 'Department Referral':                                    ║
║       General Practice  → Clínico                                           ║
║       Cualquier otro    → Especialista                                      ║
║     Hay que calcular esa proporción segmentada por turno                    ║
║     (puede variar: más especialistas de día, más generalistas de noche).    ║
║     → Distribución discreta Bernoulli/empírica, una por turno               ║
║                                                                              ║
║  3. TA_min POR TIPO DE PROFESIONAL (recomendado)                            ║
║     Un Especialista probablemente demora más que un Clínico.                ║
║     Si los datos lo permiten (hay registro de tipo de atención),            ║
║     conviene ajustar dos FDPs de TA: una para Clínicos, otra para          ║
║     Especialistas.                                                           ║
║                                                                              ║
║  4. TA_min POR TRIAGE (opcional, agrega realismo)                           ║
║     Pacientes con triage 1 (crítico) generalmente tienen TA más largo       ║
║     que triage 4-5. Si los datos lo soportan, ajustar FDP por nivel.        ║
║                                                                              ║
║  RESUMEN DE PASOS CONCRETOS PARA TP5:                                       ║
║    [1] Agregar columna 'Turno' al dataset principal (de la hora de ingreso) ║
║    [2] Ajustar FDP de IA_min para cada turno (3 distribuciones)             ║
║    [3] Calcular proporción Clínico/Especialista por turno                   ║
║    [4] (Opc.) Ajustar TA por tipo de profesional o nivel de triage          ║
║    [5] Usar Erlang-C o SimPy para modelar colas con servidores paralelos     ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""