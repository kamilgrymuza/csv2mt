#!/bin/bash
#
# Helper script to add a new E2E test case
#
# Usage:
#   ./add_e2e_test.sh <test_name> <statement_file> <expected_mt940>
#
# Example:
#   ./add_e2e_test.sh mbank_jan_2024 ~/Downloads/statement.pdf ~/Downloads/bank.mt940
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check arguments
if [ "$#" -ne 3 ]; then
    echo -e "${RED}Error: Wrong number of arguments${NC}"
    echo ""
    echo "Usage:"
    echo "  $0 <test_name> <statement_file> <expected_mt940>"
    echo ""
    echo "Example:"
    echo "  $0 mbank_jan_2024 ~/Downloads/statement.pdf ~/Downloads/bank.mt940"
    echo ""
    exit 1
fi

TEST_NAME="$1"
STATEMENT_FILE="$2"
EXPECTED_MT940="$3"

# Validate test name (alphanumeric, underscore, hyphen only)
if ! [[ "$TEST_NAME" =~ ^[a-zA-Z0-9_-]+$ ]]; then
    echo -e "${RED}Error: Test name can only contain letters, numbers, underscores, and hyphens${NC}"
    exit 1
fi

# Check if files exist
if [ ! -f "$STATEMENT_FILE" ]; then
    echo -e "${RED}Error: Statement file not found: $STATEMENT_FILE${NC}"
    exit 1
fi

if [ ! -f "$EXPECTED_MT940" ]; then
    echo -e "${RED}Error: Expected MT940 file not found: $EXPECTED_MT940${NC}"
    exit 1
fi

# Get file extension
STATEMENT_EXT="${STATEMENT_FILE##*.}"
if [[ ! "$STATEMENT_EXT" =~ ^(pdf|csv|xlsx|xls)$ ]]; then
    echo -e "${YELLOW}Warning: Unexpected statement file extension: $STATEMENT_EXT${NC}"
    echo -e "${YELLOW}Expected: pdf, csv, xlsx, or xls${NC}"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Create test case directory
TEST_DIR="backend/tests/fixtures/e2e/$TEST_NAME"
echo -e "${GREEN}Creating test case directory...${NC}"
mkdir -p "$TEST_DIR"

# Copy files
echo -e "${GREEN}Copying statement file...${NC}"
cp "$STATEMENT_FILE" "$TEST_DIR/statement.$STATEMENT_EXT"

echo -e "${GREEN}Copying expected MT940...${NC}"
cp "$EXPECTED_MT940" "$TEST_DIR/expected.mt940"

# Verify files
echo ""
echo -e "${GREEN}✓ Test case created successfully!${NC}"
echo ""
echo "Test case location: $TEST_DIR"
echo "Files:"
ls -lh "$TEST_DIR"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo ""
echo "1. Run the test with Docker:"
echo -e "   ${GREEN}docker-compose exec backend pytest tests/test_e2e_bank_comparison.py --run-e2e -v${NC}"
echo ""
echo "2. Or run just your test case:"
echo -e "   ${GREEN}docker-compose exec backend pytest tests/test_e2e_bank_comparison.py::TestEndToEndBankComparison::test_pdf_to_mt940_matches_bank[$TEST_NAME] --run-e2e -v${NC}"
echo ""
echo "3. Review the generated MT940:"
echo -e "   ${GREEN}cat $TEST_DIR/generated.mt940${NC}"
echo ""
echo -e "${YELLOW}Note: These tests consume Claude API credits!${NC}"
