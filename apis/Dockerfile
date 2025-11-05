# Use an official Python image
FROM python:3.10-slim

# Set a working directory inside the container
WORKDIR /app

# Copy requirements.txt first to leverage Docker cache
COPY requirements.txt /app/

# Install all dependencies from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project into the container
COPY . /app

# Expose port 8000 so the container can serve it
EXPOSE 8000

# Command to run the FastAPI app (fast_api.py not fastapi.py)
CMD ["uvicorn", "apis.fast_api:app", "--host", "0.0.0.0", "--port", "8000"]