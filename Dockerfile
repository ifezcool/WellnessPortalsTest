# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Install system dependencies for pyodbc and MS SQL Server
RUN apt-get update && apt-get install -y \
    unixodbc-dev \
    unixodbc \
    libsqlite3-dev \
    g++ \
    curl \
    gnupg \
    && curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql17

# Set the working directory
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn

# Expose the port Render uses
EXPOSE 10000

# Run the app using Gunicorn
# Note: 'providersubmission' matches your filename, 'server' matches your 'server = app.server' line
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "providersubmission:server"]