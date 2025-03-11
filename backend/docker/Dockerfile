# Use Python 3.10 as the base image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create data directory for database
RUN mkdir -p /data && chmod 777 /data

# Create abi directory
RUN mkdir -p /app/abi

# Copy application code
COPY . .

# Make the scripts executable (if they exist)
RUN if [ -f "/app/copy_abi.sh" ]; then chmod +x /app/copy_abi.sh; fi && \
    if [ -f "/app/docker-entrypoint.sh" ]; then chmod +x /app/docker-entrypoint.sh; fi

# Copy ABI files (already done by prepare_docker_build.sh)

# Expose the port the app runs on
EXPOSE 5000

# Use the entrypoint script or fallback to python run.py
ENTRYPOINT ["sh", "-c", "if [ -f /app/docker-entrypoint.sh ]; then /app/docker-entrypoint.sh; else python /app/run.py; fi"]