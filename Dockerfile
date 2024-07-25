# Use an official Python runtime as a parent image
FROM python:3.12.4

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3-dev \
    build-essential \
    libreoffice \
    libreoffice-java-common

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install Poetry
RUN pip install poetry

# Configure Poetry to not create a virtual environment
RUN poetry config virtualenvs.create false

# Install project dependencies using Poetry
RUN poetry install

# Make port 8080 available to the world outside this container
EXPOSE 8080

# Command to run the main script
CMD ["poetry", "run", "python", "-m", "buho_back.main"]