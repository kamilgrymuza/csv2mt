# Using the CLI Tool with Local Files

This guide shows you how to convert documents stored on your local machine using the Docker-based CLI tool.

## 🎯 Quick Start (Easiest Method)

Use the provided helper script:

```bash
# Make it executable (first time only)
chmod +x convert.sh

# Convert a local file
./convert.sh ~/Downloads/statement.pdf

# With options
./convert.sh ~/Downloads/statement.csv --json --output result.mt940
```

The script automatically:
- Copies your file into the Docker container
- Runs the conversion
- Shows where the output is saved
- Lists all files in the statements folder

## 📁 How It Works

The Docker container already has `./backend` mounted as `/app`, so any file you put in the `backend` directory is immediately accessible inside the container.

### Folder Structure

```
csv2mt/
├── backend/
│   ├── statements/          ← Put your files here!
│   │   ├── statement.pdf
│   │   ├── january.csv
│   │   └── result.mt940
│   ├── convert_document.py
│   └── ...
└── convert.sh               ← Helper script
```

## 🔧 Manual Methods

### Method 1: Using the statements folder (Recommended)

```bash
# 1. Create the statements folder
mkdir -p backend/statements

# 2. Copy your file
cp ~/Downloads/bank_statement.pdf backend/statements/

# 3. Run conversion
docker-compose exec backend python convert_document.py \
  /app/statements/bank_statement.pdf

# 4. Output is already saved locally!
# Access it at: backend/statements/
```

### Method 2: Direct copy to backend folder

```bash
# Copy file to backend directory
cp ~/Downloads/statement.pdf backend/

# Convert it
docker-compose exec backend python convert_document.py /app/statement.pdf

# Result is in backend/ directory
```

### Method 3: Using docker cp (for one-off conversions)

```bash
# Copy file INTO container
docker cp ~/Downloads/statement.pdf csv2mt-backend-1:/tmp/statement.pdf

# Convert it
docker-compose exec backend python convert_document.py /tmp/statement.pdf \
  --output /tmp/result.mt940

# Copy result OUT of container
docker cp csv2mt-backend-1:/tmp/result.mt940 ./result.mt940
```

## 📝 Complete Examples

### Example 1: Simple PDF Conversion

```bash
# Copy PDF to statements folder
cp ~/Downloads/january_statement.pdf backend/statements/

# Convert and view output
docker-compose exec backend python convert_document.py \
  /app/statements/january_statement.pdf
```

### Example 2: CSV with Account Number and Save Output

```bash
# Using helper script
./convert.sh ~/Documents/transactions.csv \
  --account-number DE89370400440532013000 \
  --output transactions.mt940

# Or manually
cp ~/Documents/transactions.csv backend/statements/
docker-compose exec backend python convert_document.py \
  /app/statements/transactions.csv \
  --account-number DE89370400440532013000 \
  --output /app/statements/transactions.mt940
```

### Example 3: Debug Mode with JSON Output

```bash
./convert.sh ~/Downloads/statement.xlsx --json

# View the JSON structure, then save if needed
./convert.sh ~/Downloads/statement.xlsx --json --output statement.mt940
```

### Example 4: Batch Convert Multiple Files

```bash
# Copy all statements
cp ~/Downloads/statements/*.pdf backend/statements/

# Convert each one
for file in backend/statements/*.pdf; do
    filename=$(basename "$file")
    docker-compose exec backend python convert_document.py \
        "/app/statements/$filename" \
        --output "/app/statements/${filename%.pdf}.mt940"
done

# Results are in backend/statements/
ls -la backend/statements/*.mt940
```

## 🔍 Accessing Results

All output files are immediately available on your local machine:

```bash
# List all files
ls -la backend/statements/

# View MT940 content
cat backend/statements/result.mt940

# Open in editor
code backend/statements/result.mt940

# Copy to another location
cp backend/statements/*.mt940 ~/Documents/converted/
```

## 🛡️ Security Note

The `.gitignore` file is configured to exclude all statement files and MT940 outputs from git, keeping your financial data private:

```gitignore
# Bank statements and MT940 files (sensitive data)
backend/statements/
*.mt940
*.pdf
*.csv
*.xls
*.xlsx
```

## 💡 Tips

### Tip 1: Create an alias

Add to your `.bashrc` or `.zshrc`:

```bash
alias convert='bash /path/to/csv2mt/convert.sh'
```

Then use it anywhere:
```bash
convert ~/Downloads/statement.pdf
```

### Tip 2: Watch for file changes

If you're testing repeatedly, use watch:

```bash
watch -n 2 'ls -lh backend/statements/'
```

### Tip 3: Clean up old files

```bash
# Remove all MT940 files
rm backend/statements/*.mt940

# Remove all statements
rm backend/statements/*
# (but keeps the folder)
```

### Tip 4: Process from any directory

The helper script works from anywhere:

```bash
# From project root
./convert.sh ~/Downloads/statement.pdf

# From another directory
/path/to/csv2mt/convert.sh ~/Downloads/statement.pdf
```

## 🐛 Troubleshooting

### Container not running

```bash
# Check if containers are running
docker-compose ps

# Start if needed
docker-compose up -d
```

### File not found error

Make sure you use the `/app/` prefix inside the container:

```bash
# ❌ Wrong
docker-compose exec backend python convert_document.py statements/file.pdf

# ✅ Correct
docker-compose exec backend python convert_document.py /app/statements/file.pdf
```

### Permission denied

```bash
# Make helper script executable
chmod +x convert.sh

# Fix file permissions in statements folder
chmod -R 755 backend/statements/
```

### Container can't access the file

Verify the mount is working:

```bash
# Create a test file
echo "test" > backend/test.txt

# Check it exists in container
docker-compose exec backend ls -la /app/test.txt

# Should show the file
```

## 📚 Related Documentation

- [CLI_TOOL_README.md](backend/CLI_TOOL_README.md) - Full CLI documentation
- [CLI_QUICK_START.md](backend/CLI_QUICK_START.md) - Quick reference
- [README.md](README.md) - Project overview
