# Use an official Python runtime as a parent image
FROM python:3.8-slim-buster

# Set the working directory in the container
WORKDIR /usr/src/app

# Install git
RUN apt-get update && apt-get install -y git

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Clone Sherlock into /app/sherlock
RUN git clone https://github.com/sherlock-project/sherlock.git /usr/src/app/sherlock || echo "Git clone failed"

# Install Sherlock's dependencies
RUN pip install --no-cache-dir -r /usr/src/app/sherlock/requirements.txt

# install dependencies
RUN pip install --upgrade pip
COPY ./requirements.txt /usr/src/app/requirements.txt
RUN pip install -r requirements.txt

# Copy project
COPY . /usr/src/app/