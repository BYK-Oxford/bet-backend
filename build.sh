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


# Install other Python dependencies
pip install -r requirements.txt
