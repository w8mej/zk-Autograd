# Syntax version for Dockerfile features
# syntax=docker/dockerfile:1

# Base image: Python 3.10 slim version for a smaller footprint
FROM python:3.10-slim

# Set working directory to /app
WORKDIR /app

# Install system dependencies required for building Python packages
# - build-essential: for compiling C extensions
# - curl: for downloading files
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy project files into the container
COPY . /app

# Install Python dependencies
# - ezkl: for ZK proof generation
# - torch: for PyTorch model execution
# - fastapi/uvicorn: for the prover service API
RUN pip install --no-cache-dir ezkl torch fastapi uvicorn

# Expose port 8000 for the prover service
EXPOSE 8000

# Command to run the prover service using uvicorn
CMD ["uvicorn", "prover.service:app", "--host", "0.0.0.0", "--port", "8000"]
