#!/bin/bash

# Update system and install Playwright dependencies (if any)
apt-get update -y

# Install additional dependencies for headless Chromium (in case Playwright needs them)
apt-get install -y \
    libnss3 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxi6 \
    libxtst6 \
    xdg-utils

# Install other Python dependencies
pip install -r requirements.txt

# Install Playwright browser binaries (Playwright will handle the installation of the browsers)
python -m playwright install

