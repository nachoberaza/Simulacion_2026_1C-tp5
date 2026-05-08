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


# Como usar el entorno virtual (Solo si es la primera vez)

## 1. Para crearlo

### Windows
```sh
python -m venv venv
```

### Linux
```sh
python3 -m venv venv
```

## 2. Para activarlo
### Windows
```sh
.\venv\Scripts\Activate.ps1
```

### Linux
```sh
source venv/bin/activate
```

## 3. Instalar librerias
Con el entorno virtual activado
```sh
pip install pandas numpy scipy matplotlib seaborn scikit-learn
```

## 4. Para guardar el estado del entorno
Primero guardamos el estado del entorno 
```sh
pip freeze > requirements.txt
```

Luego lo reproducimos en otra pc
```sh
pip install -r requirements.txt
```

## 5. Para desactivar el entorno
```sh
deactivate
```

