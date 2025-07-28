# Use official slim Python image
FROM python:3.11-slim

# Set working directory in the container
WORKDIR /app

# Install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy your project files into the container
COPY . .

# Set environment variable (optional)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Run the app
CMD ["python", "app.py"]
