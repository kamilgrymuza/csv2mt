#!/bin/bash
#
# Helper script to convert documents to MT940 using Docker
# Usage: ./convert.sh <file> [options]
#

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if file argument provided
if [ $# -eq 0 ]; then
    echo -e "${RED}Error: No file specified${NC}"
    echo "Usage: ./convert.sh <file> [options]"
    echo ""
    echo "Options:"
    echo "  --account-number <number>  Set account number"
    echo "  --json                     Show JSON debug output"
    echo "  --output <file>            Save MT940 to file"
    echo ""
    echo "Examples:"
    echo "  ./convert.sh ~/Downloads/statement.pdf"
    echo "  ./convert.sh statement.csv --json"
    echo "  ./convert.sh bank.xlsx --account-number 123456789 --output result.mt940"
    exit 1
fi

# Get the input file
INPUT_FILE="$1"
shift

# Check if file exists
if [ ! -f "$INPUT_FILE" ]; then
    echo -e "${RED}Error: File not found: $INPUT_FILE${NC}"
    exit 1
fi

# Get filename
FILENAME=$(basename "$INPUT_FILE")

# Create statements directory if it doesn't exist
mkdir -p backend/statements

# Copy file to backend/statements
echo -e "${GREEN}→${NC} Copying file to Docker container..."
cp "$INPUT_FILE" "backend/statements/$FILENAME"

# Build docker command
DOCKER_CMD="docker-compose exec backend python convert_document.py /app/statements/$FILENAME"

# Process additional arguments
SAVE_OUTPUT=false
OUTPUT_FILE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --output|-o)
            SAVE_OUTPUT=true
            OUTPUT_FILE="$2"
            DOCKER_CMD="$DOCKER_CMD --output /app/statements/${OUTPUT_FILE##*/}"
            shift 2
            ;;
        --account-number|-a)
            DOCKER_CMD="$DOCKER_CMD --account-number $2"
            shift 2
            ;;
        --json|-j)
            DOCKER_CMD="$DOCKER_CMD --json"
            shift
            ;;
        *)
            DOCKER_CMD="$DOCKER_CMD $1"
            shift
            ;;
    esac
done

# Run conversion
echo -e "${GREEN}→${NC} Running conversion..."
echo -e "${YELLOW}Command:${NC} $DOCKER_CMD"
echo ""

eval $DOCKER_CMD

# Show result location
echo ""
if [ "$SAVE_OUTPUT" = true ]; then
    echo -e "${GREEN}✓${NC} MT940 file saved to: ${GREEN}backend/statements/${OUTPUT_FILE##*/}${NC}"
else
    echo -e "${GREEN}✓${NC} Conversion complete!"
fi
echo ""
echo "Files in statements folder:"
ls -lh backend/statements/
