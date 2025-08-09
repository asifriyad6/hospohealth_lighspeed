# Use Python base image
FROM python:3.11-slim

# Prevent interactive prompts during apt installs
ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    curl \
    gnupg \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# Install Google Chrome Stable
RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
    apt-get update && apt-get install -y ./google-chrome-stable_current_amd64.deb && \
    rm google-chrome-stable_current_amd64.deb

# Install ChromeDriver matching Chrome version
RUN CHROME_VERSION=$(google-chrome --version | awk '{print $3}') && \
    CHROME_DRIVER_VERSION=$(curl -s "https://googlechromelabs.github.io/chrome-for-testing/LATEST_RELEASE_${CHROME_VERSION%.*}") && \
    wget https://storage.googleapis.com/chrome-for-testing-public/${CHROME_DRIVER_VERSION}/linux64/chromedriver-linux64.zip && \
    unzip chromedriver-linux64.zip && \
    mv chromedriver-linux64/chromedriver /usr/local/bin/chromedriver && \
    chmod +x /usr/local/bin/chromedriver && \
    rm -rf chromedriver-linux64 chromedriver-linux64.zip

# Set display port for Chrome
ENV DISPLAY=:99

# Copy project files
WORKDIR /app
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Command to run your script
CMD ["python", "main.py"]
