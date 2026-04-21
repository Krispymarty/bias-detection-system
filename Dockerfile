# Use official Python lightweight image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONUNBUFFERED=True
ENV PORT=8080

# Create and set the working directory
WORKDIR /app

# Install system dependencies for fairlearn and xgboost if needed
RUN apt-get update && apt-get install -y libgomp1 && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the required Cloud Run port
EXPOSE $PORT

# Command to run the FastAPI application
# Google Cloud Run expects the server to listen on 0.0.0.0:$PORT
CMD exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}
