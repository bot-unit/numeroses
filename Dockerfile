# syntax=docker/dockerfile:1
# Use the official Python 3.13 image from the Docker Hub
# https://hub.docker.com/hardened-images/catalog/dhi/python
FROM python@sha256:e81548ac35b07a3bd4805f275107592ef458b1e893c0e04d45aedaa19416cca5

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /app

# Copy the requirements.txt file into the container at /app
COPY requirements.txt /app/requirements.txt

# Install the required packages specified in requirements.txt
RUN pip install --trusted-host pypi.python.org --no-cache-dir -r /app/requirements.txt

# Copy the rest of your application into the container at /app
COPY src /app/src
COPY runme.py /app/runme.py

# Copy .env file into the container
# COPY .env /app/.env
# Export environment variables from .env file
# RUN export $(grep -v '^#' .env | xargs)

# Or set environment variables
#ENV BOT_TOKEN=
#ENV HOST=185.
#ENV PORT=
#ENV POSTGRES_DB=dev
#ENV POSTGRES_PASSWORD=
#ENV POSTGRES_USER=
# ENV DEBUG=False

# Expose a port if needed (uncomment if your bot needs it)
# EXPOSE 8000

# Set the default command to run your entry script
CMD ["python", "runme.py"]