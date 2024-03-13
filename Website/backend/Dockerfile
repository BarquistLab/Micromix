# Use an official Python runtime as a base image
FROM python:3.8-slim

# Set the working directory in the container
WORKDIR /app

RUN echo "----testing----"

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
# Since there are lots of packages, we need to increase the timeout
#Otherwise users will have to re-run multiple times to install all the requirements
RUN pip install --no-cache-dir --default-timeout=920 -r requirements.txt

# Make port 8080 available to the world outside this container
EXPOSE 8080

# Define environment variable
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0

# Run app.py when the container launches
CMD ["flask", "run"]

