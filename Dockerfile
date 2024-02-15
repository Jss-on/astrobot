# Use the official Selenium Chrome image
FROM selenium/standalone-chrome:latest

# Set the working directory inside the container
WORKDIR /usr/src/app

# Copy project files into the container
COPY . .

# Install Python and pip
USER root
RUN apt-get update && \
    apt-get install -y python3 python3-pip && \
    pip3 install --no-cache-dir -r server_requirements.txt

# Make sure the chromedriver is executable
#RUN chmod +x chromedriver

# Run the webactions.py when the container launches
CMD ["python3", "webactions.py"]
