# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    unixodbc-dev \
    unixodbc \
    libsqlite3-dev \
    g++ \
    curl \
    gnupg \
    && apt-get clean

# Modern way to add Microsoft's GPG key and repository for Debian 12
RUN curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg \
    && curl -sSL https://packages.microsoft.com/config/debian/12/prod.list > /etc/apt/sources.list.d/mssql-release.list \
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
# Ensure 'providersubmission' matches your filename and 'server' matches your app.server variable
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "providersubmission:server"]