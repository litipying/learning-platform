FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Expose the port for Streamlit
EXPOSE 8501

# Command to run both the cron job and the Streamlit app
CMD ["sh", "-c", "python main.py & streamlit run app.py --server.port 8501 --server.address 0.0.0.0"]