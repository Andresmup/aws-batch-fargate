# Use the official Python for ECR AWS Docs
FROM public.ecr.aws/docker/library/python:3.9.19-alpine3.20

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install dependencies specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Default command
ENTRYPOINT ["python", "main.py"]