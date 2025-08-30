ARG PYTHON_VERSION=3.10
FROM python:${PYTHON_VERSION}-slim as python-base
WORKDIR /app
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential curl apt-utils gnupg2 && \
    rm -rf /var/lib/apt/lists/* && \
    pip install --upgrade pip

# Re-update apt packages after cleaning up in the previous step
RUN apt-get update

# Add the Microsoft repository GPG keys to the list of trusted keys
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -

# Add the Microsoft package repository to the system (Debian 11/bullseye)
RUN curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list

# Update apt-get with new sources from Microsoft
RUN apt-get update

# Install the Microsoft ODBC SQL Driver 18
RUN env ACCEPT_EULA=Y apt-get install -y msodbcsql18
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 80
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
