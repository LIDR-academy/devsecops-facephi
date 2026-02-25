# Load Tests — Locust

Suite de tests de estrés para la API AI4Devs (backend Node.js/Express).

## Requisitos

- Python 3.9+
- Docker & Docker Compose (para ejecución integrada)

## Instalación local

```bash
cd load-tests
pip install -r requirements.txt
```

## Ejecución

### Modo interactivo (UI web en http://localhost:8089)

```bash
locust -f locustfile.py --host http://localhost:8080
```

Con Docker Compose (arranca backend + locust juntos):

```bash
docker compose --profile load-test up
# Abre http://localhost:8089 en el navegador
```

### Modo headless (automatizado)

```bash
locust -f load-tests/locustfile.py \
  --headless \
  --users 50 \
  --spawn-rate 5 \
  --run-time 60s \
  --host http://localhost:8080 \
  --html load-tests/report.html
```

## Escenarios

| Clase         | Peso | Descripción                                          |
|---------------|------|------------------------------------------------------|
| `ReadUser`    | 7    | Simula reclutador consultando posiciones y candidatos |
| `WriteUser`   | 2    | Simula HR creando y actualizando candidatos           |
| `UploadUser`  | 1    | Simula subida de CV (PDF)                             |

## Umbrales de calidad

El test falla si se supera alguno de estos umbrales:

- Tasa de error > 1%
- Latencia P95 > 2000 ms

## Estructura

```
load-tests/
├── locustfile.py              # Punto de entrada
├── scenarios/
│   ├── read_scenarios.py      # GET endpoints
│   ├── write_scenarios.py     # POST/PUT endpoints
│   └── upload_scenarios.py   # POST /upload
├── data/
│   └── sample.pdf             # Fichero de prueba para /upload
├── requirements.txt
└── README.md
```
