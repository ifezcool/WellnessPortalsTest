FROM python:3.11-slim-bookworm

# === Install system dependencies and build tools first ===
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl gnupg \
    unixodbc unixodbc-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# === Install ODBC Driver 17 for SQL Server ===
RUN curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /etc/apt/trusted.gpg.d/microsoft.gpg && \
    echo "deb [arch=amd64,arm64,armhf signed-by=/etc/apt/trusted.gpg.d/microsoft.gpg] https://packages.microsoft.com/debian/12/prod bookworm main" > /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && \
    ACCEPT_EULA=Y apt-get install -y msodbcsql17 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . /app

# Upgrade pip+setuptools+wheel AND install requirements in one RUN so the
# upgraded setuptools is present in every isolated build env pip creates
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

EXPOSE 8050

CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-8050} --workers 2 --timeout 120 --log-level info providersubmission:server_wsgi"]