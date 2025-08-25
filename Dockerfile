FROM python:3.11-slim

# Install dependencies for Chrome + ChromeDriver
RUN apt-get update && apt-get install -y \
    wget unzip curl gnupg \
    chromium chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Set ENV vars for Selenium
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

# Install Python deps
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .

# Expose Railway port
ENV PORT=8000
CMD ["python", "main.py"]