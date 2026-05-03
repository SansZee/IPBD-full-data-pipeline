# Simplified Docker Compose Setup

## Changes

### docker-compose.yml
- **Removed**: Redis, Flower, airflow-cli, airflow-dag-processor, airflow-triggerer, airflow-apiserver (CeleryExecutor services)
- **Changed**: `CeleryExecutor` → `LocalExecutor`
- **Added**: `metabase-data` volume untuk persist data Metabase
- **Changed**: Metabase DB dari `airflow_db` → `metabase_db` (terpisah)

### Remaining services (5 total)
1. **postgres** - PostgreSQL 16, exposed di port 5432, dengan `airflow_db`
2. **airflow-init** - Init container (db migrate + create user)
3. **airflow-webserver** - Airflow UI di port 8080
4. **airflow-scheduler** - Scheduler untuk DAGs
5. **metabase** - Metabase di port 3000, pakai DB `metabase_db`

### .env
No changes needed, tetap sama.

### Dockerfile
No changes needed, tetap sama.

## New docker-compose.yml content

```yaml
x-airflow-common:
  &airflow-common
  build: .
  env_file:
    - ${ENV_FILE_PATH:-.env}
  environment:
    &airflow-common-env
    AIRFLOW__CORE__EXECUTOR: LocalExecutor
    AIRFLOW__CORE__AUTH_MANAGER: airflow.providers.fab.auth_manager.fab_auth_manager.FabAuthManager
    AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql+psycopg2://admin:admin123@postgres/airflow_db
    AIRFLOW__CORE__FERNET_KEY: ${FERNET_KEY}
    AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION: 'true'
    AIRFLOW__CORE__LOAD_EXAMPLES: 'false'
    AIRFLOW__API_AUTH__JWT_SECRET: ${AIRFLOW__API_AUTH__JWT_SECRET:-airflow_jwt_secret}
  volumes:
    - ${AIRFLOW_PROJ_DIR:-.}/dags:/opt/airflow/dags
    - ${AIRFLOW_PROJ_DIR:-.}/logs:/opt/airflow/logs
    - ${AIRFLOW_PROJ_DIR:-.}/config:/opt/airflow/config
    - ${AIRFLOW_PROJ_DIR:-.}/plugins:/opt/airflow/plugins
  user: "${AIRFLOW_UID:-50000}:0"
  depends_on:
    &airflow-common-depends-on
    postgres:
      condition: service_healthy

services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_USER: admin
      POSTGRES_PASSWORD: admin123
      POSTGRES_DB: airflow_db
    volumes:
      - postgres-data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "admin"]
      interval: 10s
      retries: 5
      start_period: 5s
    restart: always

  airflow-init:
    <<: *airflow-common
    entrypoint: /bin/bash
    command:
      - -c
      - |
        if [[ -z "${AIRFLOW_UID}" ]]; then
          echo
          echo -e "\033[1;33mWARNING!!!: AIRFLOW_UID not set!\e[0m"
          echo "If you are on Linux, you SHOULD follow the instructions below to set "
          echo "AIRFLOW_UID environment variable, otherwise files will be owned by root."
          echo
          export AIRFLOW_UID=$$(id -u)
        fi
        echo "Creating missing opt dirs if missing:"
        mkdir -v -p /opt/airflow/{logs,dags,plugins,config}
        echo "Airflow version:"
        /entrypoint airflow version
        echo "Files in shared volumes:"
        ls -la /opt/airflow/{logs,dags,plugins,config}
        echo "Running airflow config list to create default config file if missing."
        /entrypoint airflow config list >/dev/null
        echo "Files in shared volumes:"
        ls -la /opt/airflow/{logs,dags,plugins,config}
        echo "Change ownership of files in /opt/airflow to ${AIRFLOW_UID}:0"
        chown -R "${AIRFLOW_UID}:0" /opt/airflow/
        echo "Change ownership of files in shared volumes to ${AIRFLOW_UID}:0"
        chown -v -R "${AIRFLOW_UID}:0" /opt/airflow/{logs,dags,plugins,config}
        echo "Files in shared volumes:"
        ls -la /opt/airflow/{logs,dags,plugins,config}
    environment:
      <<: *airflow-common-env
      _AIRFLOW_DB_MIGRATE: 'true'
      _AIRFLOW_WWW_USER_CREATE: 'true'
      _AIRFLOW_WWW_USER_USERNAME: ${_AIRFLOW_WWW_USER_USERNAME:-airflow}
      _AIRFLOW_WWW_USER_PASSWORD: ${_AIRFLOW_WWW_USER_PASSWORD:-airflow}
    user: "0:0"

  airflow-webserver:
    <<: *airflow-common
    command: webserver
    ports:
      - "8080:8080"
    healthcheck:
      test: ["CMD", "curl", "--fail", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 30s
    restart: always
    depends_on:
      <<: *airflow-common-depends-on
      airflow-init:
        condition: service_completed_successfully

  airflow-scheduler:
    <<: *airflow-common
    command: scheduler
    healthcheck:
      test: ["CMD", "curl", "--fail", "http://localhost:8974/health"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 30s
    restart: always
    depends_on:
      <<: *airflow-common-depends-on
      airflow-init:
        condition: service_completed_successfully

  metabase:
    image: metabase/metabase:latest
    ports:
      - "3000:3000"
    volumes:
      - metabase-data:/metabase-data
    environment:
      MB_DB_TYPE: postgres
      MB_DB_DBNAME: metabase_db
      MB_DB_PORT: 5432
      MB_DB_USER: admin
      MB_DB_PASS: admin123
      MB_DB_HOST: postgres
    depends_on:
      - postgres
    restart: always

volumes:
  postgres-data:
  metabase-data:
```

## Setup steps setelah apply

1. `docker compose up -d`
2. Access:
   - Airflow: http://localhost:8080 (user: airflow, pass: airflow)
   - Metabase: http://localhost:3000

## Tambahan: init script untuk metabase_db

Karena PostgreSQL image cuma auto-create `POSTGRES_DB` (airflow_db), perlu init script untuk buat `metabase_db`:

Buat file `config/init-metabase.sql`:
```sql
CREATE DATABASE metabase_db;
```

Lalu update postgres service di docker-compose.yml:
```yaml
  postgres:
    image: postgres:16
    environment:
      POSTGRES_USER: admin
      POSTGRES_PASSWORD: admin123
      POSTGRES_DB: airflow_db
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./config/init-metabase.sql:/docker-entrypoint-initdb.d/init-metabase.sql
```

## Catatan
- Metabase butuh DB `metabase_db` yang perlu dibuat terlebih dahulu. Bisa pakai init script di `/docker-entrypoint-initdb.d/` atau buat manual setelah PostgreSQL jalan.
