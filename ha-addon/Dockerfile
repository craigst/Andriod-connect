ARG BUILD_FROM
FROM $BUILD_FROM

# Install system dependencies including ADB and OpenCV dependencies
RUN apk add --no-cache \
    python3 \
    py3-pip \
    android-tools \
    libstdc++ \
    && rm -rf /var/cache/apk/*

# Set working directory
WORKDIR /app

# Copy application files from rootfs
COPY rootfs/app/ /app/

# Install build dependencies, Python packages, then remove build deps
RUN apk add --no-cache --virtual .build-deps \
    gcc \
    g++ \
    musl-dev \
    python3-dev \
    linux-headers \
    && pip3 install --no-cache-dir --break-system-packages -r /app/requirements.txt \
    && apk del .build-deps \
    && rm -rf /var/cache/apk/*

# Create necessary directories for runtime
RUN mkdir -p /data/logs \
    /data/apk \
    /data/screenshots \
    /data/paperwork \
    /share/adb-manager

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Expose port (internal only, Ingress will handle external access)
EXPOSE 5020

# Run the server
CMD ["python3", "/app/server.py"]
