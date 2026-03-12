FROM python:3.11-slim-bookworm

# === Install ODBC Driver 17 for SQL Server ===
RUN apt-get update && apt-get install -y \
    ca-certificates curl gnupg unixodbc unixodbc-dev \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /etc/apt/trusted.gpg.d/microsoft.gpg && \
    echo "deb [arch=amd64,arm64,armhf signed-by=/etc/apt/trusted.gpg.d/microsoft.gpg] https://packages.microsoft.com/debian/12/prod bookworm main" > /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && \
    ACCEPT_EULA=Y apt-get install -y msodbcsql17 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy code (secrets are NOT copied)
COPY . /app

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*
# Upgrade pip early (your log shows 25.0.1 → 26.0.1 is available)
RUN pip install --upgrade pip setuptools wheel
EXPOSE 8050

# Render automatically gives us $PORT — we bind to it
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-8050} --workers 2 --timeout 120 --log-level info providersubmission:server_wsgi"]