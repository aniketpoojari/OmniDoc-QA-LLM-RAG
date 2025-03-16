# Use an official Python 3.11 runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port that Flask runs on
EXPOSE 5000

# Set environment variable to enable Flask to run in production mode
ENV FLASK_ENV=production

# Run the Flask app
CMD ["python", "app.py"]