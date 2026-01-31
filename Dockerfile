# Use a lightweight Python image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies for pandas/numpy
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc python3-dev && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements and install
# We install directly to save space
RUN pip install --no-cache-dir pyTelegramBotAPI pandas requests numpy flask

# Copy your bot code
COPY . .

# Port for Render/Koyeb health checks
EXPOSE 8080

# Run the bot
CMD ["python", "bot.py"]
