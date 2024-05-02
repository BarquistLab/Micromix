# Use an official Python runtime as a base image
FROM python:3.8-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 3000 available to the world outside this container
EXPOSE 3000

# Define environment variables
ENV FLASK_APP=app.py

# make accessable from outside the container
ENV FLASK_RUN_HOST=0.0.0.0

# Run app.py when the container launches
# (0.0.0.0 again to make accessable outside container)
CMD ["flask", "run", "--host=0.0.0.0", "--port=3000"]
