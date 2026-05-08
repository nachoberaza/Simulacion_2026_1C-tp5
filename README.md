# Estructura del proyecto

```
proyecto/
│
├── src/
│    └── dominio/ --> clases propias del dominio de la simulacion
│       ├── enums.py
│       ├── evento.py
│       ├── paciente.py
│       └── recurso_medico.py
│
│    └── generadores/ --> componentes para generar los valores de las V.A.
│       └── generador_IA.py
│       └── generador_triage.py
│
│    └── simulaciones/
│       └── simulacion.py
│
├── distribuciones/ --> Valores de distribuciones persistidos para cada V.A.
│   ├── ia.json
│   ├── triage.json
│   └── tiempo_atencion.json
│
└── CSV/
```

