# CLI Tool Quick Start

## Installation Check
```bash
# Check if rich is installed
docker-compose exec backend python -c "import rich; print('✓ Rich installed')"
```

## Quick Examples

### 1. Basic Conversion
```bash
docker-compose exec backend python convert_document.py sample_statement.csv
```

### 2. With Account Number
```bash
docker-compose exec backend python convert_document.py sample_statement.csv \
  --account-number DE89370400440532013000
```

### 3. Debug Mode (Show JSON)
```bash
docker-compose exec backend python convert_document.py sample_statement.csv --json
```

### 4. Save to File
```bash
docker-compose exec backend python convert_document.py sample_statement.csv \
  --output /app/output.mt940
```

### 5. Full Featured
```bash
docker-compose exec backend python convert_document.py sample_statement.csv \
  --account-number 123456789 \
  --json \
  --output /app/result.mt940
```

## File Access

### Copy file into Docker container
```bash
docker cp /path/to/your/statement.pdf csv2mt-backend-1:/app/statement.pdf
```

### Copy result out of Docker container
```bash
docker cp csv2mt-backend-1:/app/result.mt940 ./result.mt940
```

### Use volume mount (easier)
```bash
# Add to docker-compose.yml under backend service:
volumes:
  - ./statements:/app/statements

# Then use:
docker-compose exec backend python convert_document.py /app/statements/your_file.pdf
```

## Troubleshooting

### Module not found: rich
```bash
docker-compose exec backend pip install rich
```

### API key not set
Check `.env` file has:
```
ANTHROPIC_API_KEY=your-key-here
```

### File not found
Use absolute paths inside container:
```bash
# Wrong
docker-compose exec backend python convert_document.py statement.csv

# Correct
docker-compose exec backend python convert_document.py /app/statement.csv
```

## Color Output

If colors don't display correctly, try:
```bash
docker-compose exec -e TERM=xterm-256color backend python convert_document.py sample_statement.csv
```

Or disable colors:
```bash
docker-compose exec backend python convert_document.py sample_statement.csv --no-color
```
