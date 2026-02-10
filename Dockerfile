# Use official Python runtime as a parent image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies required for OpenCV
# libgl1-mesa-glx and libglib2.0-0 are critical for cv2 to work in Docker
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
# Using --no-cache-dir to keep image size down
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose port 8080 (Render's default)
EXPOSE 8080

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Run the app
CMD ["python", "main.py"]
