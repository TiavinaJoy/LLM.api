FROM python:3.12-slim
# Set workdir
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt


# Copy your app
COPY . .

# Default command (you can adjust this to run your main file)
CMD ["python", "main.py"]