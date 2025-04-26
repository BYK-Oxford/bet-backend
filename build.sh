#!/bin/bash

# Update and install Chromium dependencies
apt-get update -y
apt-get install -y \
    chromium \
    chromium-driver \
    fonts-liberation \
    libappindicator3-1 \
    libasound2 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxi6 \
    libxtst6 \
    xdg-utils


# Check if chromedriver is installed and print its location
CHROMEDRIVER_PATH=$(which chromedriver)

if [ -z "$CHROMEDRIVER_PATH" ]; then
    echo "Chromedriver is not installed."
else
    echo "Chromedriver is installed at: $CHROMEDRIVER_PATH"
fi

# Check if chromium is installed and print its location
CHROMIUM_PATH=$(which chromium)

if [ -z "$CHROMIUM_PATH" ]; then
    echo "Chromium is not installed."
else
    echo "Chromium is installed at: $CHROMIUM_PATH"
fi


# Install other Python dependencies
pip install -r requirements.txt
