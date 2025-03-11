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

# Make the scripts executable
RUN chmod +x /app/copy_abi.sh /app/docker-entrypoint.sh

# Copy ABI files using the script
RUN /app/copy_abi.sh

# Expose the port the app runs on
EXPOSE 5000

# Use the entrypoint script
ENTRYPOINT ["/app/docker-entrypoint.sh"]