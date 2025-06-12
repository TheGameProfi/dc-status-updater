FROM python:3.13-alpine

# Set the working directory
WORKDIR /app

# Copy the script into the container at /app
COPY ./main.py /app

# Install any needed packages specified in requirements.txt
RUN pip install --trusted-host pypi.python.org requests

ENV TOKEN=dummy
ENV INTERVAL=3600
VOLUME /app/quotes.txt

# Run app.py when the container launches
CMD ["python", "-u", "main.py"]
