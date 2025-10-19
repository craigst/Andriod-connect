FROM python:3.11-slim

# Install system dependencies including ADB, OpenCV dependencies, and LibreOffice
RUN apt-get update && apt-get install -y \
    android-tools-adb \
    libgl1 \
    libglib2.0-0 \
    libreoffice \
    libreoffice-calc \
    libreoffice-writer \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY adb_manager.py .
COPY server.py .
COPY credentials_manager.py .
COPY screen_detector.py .
COPY screen_macros.py .
COPY init_screen_control_db.py .
COPY vehicle_lookup.py .
COPY templates/ templates/
COPY scripts/ scripts/
COPY signature/ signature/
COPY screen_templates/ screen_templates/

# Create necessary directories
RUN mkdir -p logs data apk templates static screenshots

# Expose port
EXPOSE 5020

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the server
CMD ["python", "server.py"]
