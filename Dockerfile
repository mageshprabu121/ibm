# Use an official Python runtime as the base image
FROM python:3.11-slim

RUN apt-get update --fix-missing && apt-get install -y --fix-missing build-essential poppler-utils 

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file to the working directory
COPY requirements.txt .

# Install the required packages
RUN pip install --no-cache-dir -r requirements.txt

# Update apt and install Tesseract
RUN apt-get update && apt-get install -y tesseract-ocr

# Copy the streamlit application code to the container
COPY . .

# Expose the port on which the Flask application will run
EXPOSE 8080

# # Set the environment variable for Flask
# ENV STREAMLIT_APP=app.py

# Run the fastapi application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]