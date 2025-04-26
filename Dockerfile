# Use an official Python runtime as a parent image
FROM python:3.13.2-slim

# Set environment variables for Playwright installation
ENV PYTHONUNBUFFERED 1
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libnss3 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxi6 \
    libxtst6 \
    xdg-utils \
    wget \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Playwright dependencies
RUN pip install --upgrade pip
RUN pip install playwright

# Install Playwright browsers
RUN playwright install --with-deps

# Set the working directory in the container
WORKDIR /app

# Copy your project files into the container
COPY . /app

# Install Python dependencies
RUN pip install -r requirements.txt -v

# Expose the port your application will run on (e.g., 8000)
EXPOSE 8000

# Command to run your app using Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
