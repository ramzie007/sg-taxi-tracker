# Dockerfile for sg-taxi-tracker
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt dev-requirements.txt ./

# Install Python dependencies
RUN pip install --upgrade pip \
    && pip install -r requirements.txt \
    && pip install -r dev-requirements.txt

# Copy source code
COPY . .

# Entrypoint for running the app
CMD ["python", "main.py"]
