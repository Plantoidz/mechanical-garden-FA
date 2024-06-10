# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /usr/src/app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y \
    portaudio19-dev \
    python3-dev \
    build-essential \
    pulseaudio \
    libpulse-dev \
    ffmpeg \
    python3-gi \
    gir1.2-gstreamer-1.0 \
    gir1.2-gst-plugins-base-1.0 \
    libcairo2-dev \
    gobject-introspection \
    libgirepository1.0-dev \
    alsa-utils \
    alsa-oss \
    alsa-tools && \
    rm -rf /var/lib/apt/lists/*

# Copy the current directory contents into the container at /usr/src/app
COPY . .

# Copy PulseAudio configuration file
COPY default.pa /etc/pulse/default.pa

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install pygobject

# Expose ports for WebSocket communication
EXPOSE 7777
EXPOSE 8888

# Set environment variable to detect Docker
ENV RUNNING_IN_DOCKER true

# Set up PulseAudio to run in the background
RUN pulseaudio --daemonize

# Run mechanical_garden.py when the container launches
CMD ["python", "mechanical_garden.py"]
