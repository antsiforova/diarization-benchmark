FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml ./
COPY run_and_save.py ./
COPY test_ami_files.py ./
COPY test_sequestered.py ./
COPY src/ ./src/
COPY config/ ./config/
COPY data/ ./data/
COPY scripts/ ./scripts/
COPY dashboard/ ./dashboard/

# Install Python dependencies (including dev dependencies for testing)
RUN pip install --no-cache-dir -e ".[dev]"

# Install Node.js for dashboard (if needed)
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

# Install dashboard dependencies
WORKDIR /app/dashboard
RUN npm install

WORKDIR /app

# Copy entrypoint
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["python", "run_and_save.py"]