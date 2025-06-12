# Use official Python image
FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y build-essential libsqlite3-dev && rm -rf /var/lib/apt/lists/*
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# Create a valid empty SQLite database file
RUN python3 -c "import sqlite3; sqlite3.connect('./strings.db').close()"
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
