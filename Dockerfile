# Use an official Python runtime as a parent image
FROM python:3.9-slim
RUN apt-get update && apt-get install -y \
python3-dev \
build-essential    

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install Poetry
RUN pip install poetry

# Install project dependencies using Poetry
RUN poetry install

# Install libreoffice to use PPT loader
RUN apt-get --no-install-recommends install libreoffice -y
RUN apt-get install -y libreoffice-java-common

# Make port available to the world outside this container
EXPOSE 8080

# Command to run the main script
CMD ["poetry", "run", "python", "-m","buho_back.main"]