# SAP - Solana Analytics Platform

<p align="center">
  <img src="https://raw.githubusercontent.com/mobr-ai/sap-frontend/refs/heads/main/public/icons/logo.svg" width="180" />
</p>

<p align="center">
  <b>Solana Analytics Platform Powered by Grounded AI</b><br/>
  Semantic Knowledge Graph • Natural Language Analytics • Explainable Insights • Interactive Dashboards
</p>

**SAP** is the backend and analytics engine for the **Solana Analytics Platform**,
focused on grounded natural-language exploration of Solana data, semantic querying,
explainable insight generation, and artifact-oriented analytics workflows.

This repository provides the backend services, APIs, data access layer,
orchestration logic, and supporting infrastructure for SAP.

## Related Repository

- **SAP Frontend:** https://github.com/mobr-ai/sap-frontend

The frontend repository contains the React/Vite SPA that connects to this backend.

---

## What SAP Provides

SAP backend is responsible for:

- serving the API consumed by SAP Frontend
- orchestrating natural-language analytics workflows
- grounding results in structured and semantic data sources
- managing artifact generation and reusable analytics outputs
- supporting authenticated product flows
- exposing health, monitoring, and debugging surfaces

---

## Platform Direction

SAP is focused on a **Solana-first analytics architecture** centered on:

- natural-language investigation
- semantic knowledge graph exploration
- explainable analytics results
- artifact-driven dashboards
- grounded AI workflows for complex Solana data

The platform is being developed incrementally while keeping the system buildable
and operable throughout the migration and productization process.

---

## Prerequisites

Before running SAP, ensure you have the following installed:

- **Python 3.11+**
- **Docker & Docker Compose**
- **Virtualenv** or **venv**
- **Git**

---

## Environment Setup

### macOS

1. Install Homebrew if needed:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"


2. Install dependencies:

```bash
brew install python@3.11 docker docker-compose
```

3. Start Docker:

```bash
open -a Docker
```

### Linux (Ubuntu)

1. Update system and install dependencies:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3.11 python3.11-venv python3-pip docker.io docker-compose -y
```

2. Start Docker:

```bash
sudo systemctl start docker
sudo systemctl enable docker
```

### Windows (WSL2)

> **Disclaimer:** WSL2 is not the primary target environment. It may work, but
> Docker, networking, GPU, and volume behavior may require additional tuning.

1. Enable WSL2 and install Ubuntu
2. Install dependencies inside WSL:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3.11 python3.11-venv python3-pip docker.io docker-compose -y
```

3. Start Docker inside WSL if needed:

```bash
sudo systemctl start docker
```

---

## Environment Variables

Create a local environment file from the example:

```bash
cp .env.example .env
```

Adjust values to match your local machine and desired runtime.

Typical variables may include:

```env
POSTGRES_DB=sap
POSTGRES_USER=postgres
POSTGRES_PASSWORD=mysecretpassword
REDIS_URL=redis://redis:6379/0
QLEVER_PASSWORD=mysecretpassword
CUDA_VISIBLE_DEVICES=0
```

If you are running through Docker Compose, keep hostnames aligned with service
names such as `postgres`, `redis`, `qlever`, and other containers defined in
your compose file.

---

## Running SAP Locally

### 1. Set up Python environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install -U pip
poetry install
```

### 2. Start supporting services

You can either run dependencies manually or use Docker Compose.

### 3. Run the SAP API

Adjust the module path below if your backend package name differs.

```bash
uvicorn src.sap.main:app --host 0.0.0.0 --port 8000
```

Once running, the API should be available at:

* **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
* **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## Running SAP with Docker Compose

### 1. Prepare the environment file

```bash
cp .env.example .env
```

### 2. Review compose-specific settings

Make sure your `docker-compose.yml` is aligned with SAP-specific names, paths,
database values, and application module paths.

Recommended adjustments include:

* `container_name: sap_server`
* `container_name: sap_postgres`
* `container_name: sap_redis`
* host paths such as `/home/sap/data/...`
* database bootstrap file such as `./ops/sql/init-sap.sql`
* `POSTGRES_DB=sap`
* application command:

  ```bash
  uvicorn src.sap.main:app --host 0.0.0.0 --port 8000
  ```

### 3. Build and start services

```bash
docker compose up -d
```

### 4. Inspect logs

```bash
docker compose logs -f
```

For a specific service:

```bash
docker compose logs -f api
docker compose logs -f postgres
docker compose logs -f qlever
```

### 5. Stop services

```bash
docker compose down
```

### 6. Stop services and remove volumes

```bash
docker compose down -v
```

---

## Suggested Compose Service Layout

A typical local SAP stack may include services such as:

* `api`
* `postgres`
* `redis`
* `qlever`
* `jaeger`
* `vllm`

Adjust service definitions, ports, and volumes according to your local
infrastructure and deployment strategy.

---

## Development

### API Documentation

Once SAP is running, access:

* **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
* **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

### Monitoring and Tracing

If Jaeger is enabled in Docker Compose, tracing can be inspected at:

* **Jaeger UI:** [http://localhost:16688](http://localhost:16688)

### Query / Semantic Engine

If QLever is enabled in Docker Compose, its interfaces are typically exposed at:

* **QLever UI:** [http://localhost:7001](http://localhost:7001)
* **SPARQL Endpoint:** [http://localhost:7000](http://localhost:7000)

Adjust ports if your local compose file differs.

---

## Testing

With SAP and its dependencies running:

```bash
source venv/bin/activate
poetry install --with dev
pytest -v
```

Run a specific file:

```bash
pytest -v src/tests/test_api.py
```

Run a specific test:

```bash
pytest -s src/tests/test_integration.py::test_full_graph_lifecycle
```

Run with coverage:

```bash
pytest --cov=src/sap
```

Adjust the coverage path if your package layout differs.

---

## Contributing

Contributions are welcome, especially around:

* Solana-oriented analytics workflows
* semantic querying and grounded reasoning
* backend reliability and observability
* auth and user-facing integration support
* artifact generation and dashboard APIs

When contributing:

1. Create a feature branch
2. Keep changes scoped and buildable
3. Run tests before opening a PR
4. Document meaningful backend or infra changes

---

## License

Licensed under the GNU GPLv3.

You may use, modify, and distribute the software under the same license.

```
```
