"""
Tests for chunking and data integrity in the Claude parser

These tests ensure that:
1. Files are correctly chunked into appropriate sizes
2. No data is lost during chunking and assembly
3. Metadata is correctly merged from multiple chunks
4. Transaction order is preserved
5. Token limits are respected
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from app.services.claude_parser import ClaudeDocumentParser


class TestChunkingLogic:
    """Test that files are correctly chunked"""

    def test_small_file_not_chunked(self):
        """Test that files under threshold are not chunked"""
        parser = ClaudeDocumentParser()

        # Create a small text content (100 lines)
        small_content = "\n".join([f"Line {i}" for i in range(100)])

        chunks = parser._chunk_text_by_lines(small_content, lines_per_chunk=100)

        # Should return single chunk
        assert len(chunks) == 1
        assert chunks[0] == small_content

    def test_large_file_is_chunked(self):
        """Test that files over threshold are chunked"""
        parser = ClaudeDocumentParser()

        # Create header (20 lines) + data (250 lines) = 270 total
        header = "\n".join([f"Header {i}" for i in range(20)])
        data = "\n".join([f"Data {i}" for i in range(250)])
        large_content = header + "\n" + data

        chunks = parser._chunk_text_by_lines(large_content, lines_per_chunk=100)

        # Should split into multiple chunks (250 data lines / 100 per chunk = 3 chunks)
        assert len(chunks) == 3

    def test_chunk_includes_header(self):
        """Test that each chunk includes the header lines"""
        parser = ClaudeDocumentParser()

        # Create header (20 lines) + data (250 lines)
        header = "\n".join([f"Header {i}" for i in range(20)])
        data = "\n".join([f"Data {i}" for i in range(250)])
        large_content = header + "\n" + data

        chunks = parser._chunk_text_by_lines(large_content, lines_per_chunk=100)

        # Every chunk should contain the header
        for chunk in chunks:
            assert "Header 0" in chunk
            assert "Header 19" in chunk

    def test_chunk_sizes_are_correct(self):
        """Test that chunks are approximately the right size"""
        parser = ClaudeDocumentParser()

        # Create header (20 lines) + data (250 lines)
        header = "\n".join([f"Header {i}" for i in range(20)])
        data = "\n".join([f"Data {i}" for i in range(250)])
        large_content = header + "\n" + data

        chunks = parser._chunk_text_by_lines(large_content, lines_per_chunk=100)

        # First two chunks should have header (20) + full data (100) = 120 lines
        # Last chunk should have header (20) + remaining data (50) = 70 lines
        assert len(chunks) == 3
        assert len(chunks[0].split('\n')) == 120, "First chunk should have 120 lines"
        assert len(chunks[1].split('\n')) == 120, "Second chunk should have 120 lines"
        assert len(chunks[2].split('\n')) == 70, "Last chunk should have 70 lines (partial)"

    def test_no_data_duplication_across_chunks(self):
        """Test that data lines appear in only one chunk"""
        parser = ClaudeDocumentParser()

        # Create unique data lines
        header = "\n".join([f"Header {i}" for i in range(20)])
        data_lines = [f"UniqueData_{i}" for i in range(250)]
        data = "\n".join(data_lines)
        large_content = header + "\n" + data

        chunks = parser._chunk_text_by_lines(large_content, lines_per_chunk=100)

        # Collect all data lines from all chunks (excluding header)
        found_data = []
        for chunk in chunks:
            lines = chunk.split('\n')
            # Skip first 20 lines (header)
            for line in lines[20:]:
                if line.startswith("UniqueData_"):
                    found_data.append(line)

        # Check no duplicates (each data line appears exactly once)
        assert len(found_data) == len(set(found_data)), "Found duplicate data lines across chunks"
        assert len(found_data) == 250, f"Expected 250 data lines, found {len(found_data)}"

    def test_chunking_preserves_all_data(self):
        """Test that no data is lost during chunking"""
        parser = ClaudeDocumentParser()

        # Create content with unique lines
        header = "\n".join([f"Header {i}" for i in range(20)])
        data_lines = [f"Data_{i}" for i in range(300)]
        data = "\n".join(data_lines)
        large_content = header + "\n" + data

        chunks = parser._chunk_text_by_lines(large_content, lines_per_chunk=100)

        # Verify all data lines are present across all chunks
        all_chunk_lines = []
        for chunk in chunks:
            all_chunk_lines.extend(chunk.split('\n'))

        # Check each unique data line exists
        for data_line in data_lines:
            assert data_line in all_chunk_lines, f"Data line '{data_line}' not found in any chunk"


class TestChunkProcessing:
    """Test the processing of chunks with mocked Claude API"""

    @patch.object(ClaudeDocumentParser, '_parse_single_chunk')
    def test_chunk_results_are_merged(self, mock_parse):
        """Test that results from multiple chunks are correctly merged"""
        parser = ClaudeDocumentParser()

        # Mock responses from different chunks
        mock_parse.side_effect = [
            {
                "transactions": [
                    {"date": "2024-01-01", "amount": -100.0, "description": "Txn 1", "transaction_type": "DEBIT"},
                    {"date": "2024-01-02", "amount": -200.0, "description": "Txn 2", "transaction_type": "DEBIT"}
                ],
                "metadata": {
                    "account_number": "123456",
                    "currency": "PLN",
                    "statement_start_date": "2024-01-01",
                    "statement_end_date": "2024-01-02",
                    "opening_balance": 1000.0,
                    "closing_balance": 700.0,
                    "input_tokens": 100,
                    "output_tokens": 50
                }
            },
            {
                "transactions": [
                    {"date": "2024-01-03", "amount": -300.0, "description": "Txn 3", "transaction_type": "DEBIT"},
                    {"date": "2024-01-04", "amount": -400.0, "description": "Txn 4", "transaction_type": "DEBIT"}
                ],
                "metadata": {
                    "account_number": "123456",
                    "currency": "PLN",
                    "statement_start_date": "2024-01-03",
                    "statement_end_date": "2024-01-04",
                    "closing_balance": 0.0,
                    "input_tokens": 100,
                    "output_tokens": 50
                }
            }
        ]

        # Create large content that will be chunked (need >100 data lines for 2 chunks)
        header = "\n".join([f"Header {i}" for i in range(20)])
        data = "\n".join([f"Data {i}" for i in range(250)])
        large_content = header + "\n" + data

        result = parser._parse_large_file_in_chunks(large_content, None)

        # Check transactions are merged
        assert len(result["transactions"]) == 4, "Should have 4 transactions from 2 chunks"
        assert result["transactions"][0]["description"] == "Txn 1"
        assert result["transactions"][3]["description"] == "Txn 4"

    @patch.object(ClaudeDocumentParser, '_parse_single_chunk')
    def test_metadata_dates_are_expanded(self, mock_parse):
        """Test that metadata date range expands across chunks"""
        parser = ClaudeDocumentParser()

        # Mock responses with different date ranges
        mock_parse.side_effect = [
            {
                "transactions": [{"date": "2024-01-15", "amount": -100.0, "description": "Txn", "transaction_type": "DEBIT"}],
                "metadata": {
                    "statement_start_date": "2024-01-15",
                    "statement_end_date": "2024-01-20",
                    "input_tokens": 100,
                    "output_tokens": 50
                }
            },
            {
                "transactions": [{"date": "2024-01-10", "amount": -200.0, "description": "Txn", "transaction_type": "DEBIT"}],
                "metadata": {
                    "statement_start_date": "2024-01-10",  # Earlier start
                    "statement_end_date": "2024-01-18",
                    "input_tokens": 100,
                    "output_tokens": 50
                }
            },
            {
                "transactions": [{"date": "2024-01-25", "amount": -300.0, "description": "Txn", "transaction_type": "DEBIT"}],
                "metadata": {
                    "statement_start_date": "2024-01-22",
                    "statement_end_date": "2024-01-25",  # Later end
                    "input_tokens": 100,
                    "output_tokens": 50
                }
            }
        ]

        header = "\n".join([f"Header {i}" for i in range(20)])
        data = "\n".join([f"Data {i}" for i in range(250)])
        large_content = header + "\n" + data

        result = parser._parse_large_file_in_chunks(large_content, None)

        # Date range should span from earliest to latest
        assert result["metadata"]["statement_start_date"] == "2024-01-10", "Should use earliest start date"
        assert result["metadata"]["statement_end_date"] == "2024-01-25", "Should use latest end date"

    @patch.object(ClaudeDocumentParser, '_parse_single_chunk')
    def test_token_usage_is_accumulated(self, mock_parse):
        """Test that token usage is summed across all chunks"""
        parser = ClaudeDocumentParser()

        # Mock responses with token usage
        mock_parse.side_effect = [
            {
                "transactions": [{"date": "2024-01-01", "amount": -100.0, "description": "Txn", "transaction_type": "DEBIT"}],
                "metadata": {"input_tokens": 1000, "output_tokens": 500}
            },
            {
                "transactions": [{"date": "2024-01-02", "amount": -200.0, "description": "Txn", "transaction_type": "DEBIT"}],
                "metadata": {"input_tokens": 1200, "output_tokens": 600}
            },
            {
                "transactions": [{"date": "2024-01-03", "amount": -300.0, "description": "Txn", "transaction_type": "DEBIT"}],
                "metadata": {"input_tokens": 1100, "output_tokens": 550}
            }
        ]

        header = "\n".join([f"Header {i}" for i in range(20)])
        data = "\n".join([f"Data {i}" for i in range(250)])
        large_content = header + "\n" + data

        result = parser._parse_large_file_in_chunks(large_content, None)

        # Token usage should be summed
        assert result["metadata"]["input_tokens"] == 3300, "Should sum input tokens"
        assert result["metadata"]["output_tokens"] == 1650, "Should sum output tokens"

    @patch.object(ClaudeDocumentParser, '_parse_single_chunk')
    def test_closing_balance_from_last_chunk(self, mock_parse):
        """Test that closing balance is taken from the last chunk"""
        parser = ClaudeDocumentParser()

        # Mock responses with different closing balances
        mock_parse.side_effect = [
            {
                "transactions": [{"date": "2024-01-01", "amount": -100.0, "description": "Txn", "transaction_type": "DEBIT"}],
                "metadata": {"opening_balance": 1000.0, "closing_balance": 900.0, "input_tokens": 100, "output_tokens": 50}
            },
            {
                "transactions": [{"date": "2024-01-02", "amount": -200.0, "description": "Txn", "transaction_type": "DEBIT"}],
                "metadata": {"closing_balance": 700.0, "input_tokens": 100, "output_tokens": 50}
            },
            {
                "transactions": [{"date": "2024-01-03", "amount": -300.0, "description": "Txn", "transaction_type": "DEBIT"}],
                "metadata": {"closing_balance": 400.0, "input_tokens": 100, "output_tokens": 50}  # Last chunk
            }
        ]

        header = "\n".join([f"Header {i}" for i in range(20)])
        data = "\n".join([f"Data {i}" for i in range(250)])
        large_content = header + "\n" + data

        result = parser._parse_large_file_in_chunks(large_content, None)

        # Should use closing balance from last chunk
        assert result["metadata"]["closing_balance"] == 400.0, "Should use closing balance from last chunk"
        # Should preserve opening balance from first chunk
        assert result["metadata"]["opening_balance"] == 1000.0, "Should use opening balance from first chunk"

    @patch.object(ClaudeDocumentParser, '_parse_single_chunk')
    def test_failed_chunk_continues_processing(self, mock_parse):
        """Test that if one chunk fails, others are still processed"""
        parser = ClaudeDocumentParser()

        # Mock responses where middle chunk fails
        mock_parse.side_effect = [
            {
                "transactions": [{"date": "2024-01-01", "amount": -100.0, "description": "Txn 1", "transaction_type": "DEBIT"}],
                "metadata": {"input_tokens": 100, "output_tokens": 50}
            },
            Exception("Claude API error"),  # Chunk 2 fails
            {
                "transactions": [{"date": "2024-01-03", "amount": -300.0, "description": "Txn 3", "transaction_type": "DEBIT"}],
                "metadata": {"input_tokens": 100, "output_tokens": 50}
            }
        ]

        header = "\n".join([f"Header {i}" for i in range(20)])
        data = "\n".join([f"Data {i}" for i in range(250)])
        large_content = header + "\n" + data

        result = parser._parse_large_file_in_chunks(large_content, None)

        # Should have transactions from successful chunks only
        assert len(result["transactions"]) == 2, "Should have transactions from 2 successful chunks"
        assert result["transactions"][0]["description"] == "Txn 1"
        assert result["transactions"][1]["description"] == "Txn 3"


class TestTransactionOrderPreservation:
    """Test that transaction order is preserved during chunking"""

    @patch.object(ClaudeDocumentParser, '_parse_single_chunk')
    def test_transaction_order_preserved(self, mock_parse):
        """Test that transactions maintain chronological order"""
        parser = ClaudeDocumentParser()

        # Mock responses with dated transactions
        mock_parse.side_effect = [
            {
                "transactions": [
                    {"date": "2024-01-01", "amount": -100.0, "description": "A", "transaction_type": "DEBIT"},
                    {"date": "2024-01-02", "amount": -200.0, "description": "B", "transaction_type": "DEBIT"}
                ],
                "metadata": {"input_tokens": 100, "output_tokens": 50}
            },
            {
                "transactions": [
                    {"date": "2024-01-03", "amount": -300.0, "description": "C", "transaction_type": "DEBIT"},
                    {"date": "2024-01-04", "amount": -400.0, "description": "D", "transaction_type": "DEBIT"}
                ],
                "metadata": {"input_tokens": 100, "output_tokens": 50}
            },
            {
                "transactions": [
                    {"date": "2024-01-05", "amount": -500.0, "description": "E", "transaction_type": "DEBIT"}
                ],
                "metadata": {"input_tokens": 100, "output_tokens": 50}
            }
        ]

        header = "\n".join([f"Header {i}" for i in range(20)])
        data = "\n".join([f"Data {i}" for i in range(250)])
        large_content = header + "\n" + data

        result = parser._parse_large_file_in_chunks(large_content, None)

        # Verify order is preserved
        descriptions = [txn["description"] for txn in result["transactions"]]
        assert descriptions == ["A", "B", "C", "D", "E"], "Transaction order should be preserved"


class TestChunkingThresholdDetection:
    """Test automatic chunking threshold detection"""

    def test_parse_with_claude_text_auto_chunks_large_files(self):
        """Test that large files automatically trigger chunking"""
        parser = ClaudeDocumentParser()

        # Create content that exceeds threshold (>120 lines)
        large_content = "\n".join([f"Line {i}" for i in range(150)])

        # Mock the chunking method to verify it's called
        with patch.object(parser, '_parse_large_file_in_chunks') as mock_chunk:
            mock_chunk.return_value = {"transactions": [], "metadata": {}}

            parser._parse_with_claude_text(large_content, None)

            # Should call chunking method
            mock_chunk.assert_called_once()

    def test_parse_with_claude_text_skips_chunking_small_files(self):
        """Test that small files skip chunking"""
        parser = ClaudeDocumentParser()

        # Create small content (<120 lines)
        small_content = "\n".join([f"Line {i}" for i in range(100)])

        # Mock the single chunk method
        with patch.object(parser, '_parse_single_chunk') as mock_single:
            mock_single.return_value = {"transactions": [], "metadata": {}}

            parser._parse_with_claude_text(small_content, None)

            # Should call single chunk method directly
            mock_single.assert_called_once()
            assert mock_single.call_args[0][0] == small_content


class TestCSVParsing:
    """Test the CSV response parsing with proper quoted field handling"""

    def test_parse_metadata_line(self):
        """Test parsing of METADATA line"""
        parser = ClaudeDocumentParser()

        response = """METADATA,PL12345678,PLN,2024-01-01,2024-01-31,1000.00,500.00
TXN,2024-01-15,-100.50,"Test transaction",DEBIT,REF123,899.50"""

        result = parser._parse_pipe_delimited_response(response)

        assert result["metadata"]["account_number"] == "PL12345678"
        assert result["metadata"]["currency"] == "PLN"
        assert result["metadata"]["statement_start_date"] == "2024-01-01"
        assert result["metadata"]["statement_end_date"] == "2024-01-31"
        assert result["metadata"]["opening_balance"] == 1000.00
        assert result["metadata"]["closing_balance"] == 500.00

    def test_parse_transaction_lines(self):
        """Test parsing of TXN lines"""
        parser = ClaudeDocumentParser()

        response = """METADATA,123,PLN,2024-01-01,2024-01-31,1000.00,500.00
TXN,2024-01-15,-100.50,"Test transaction",DEBIT,REF123,899.50
TXN,2024-01-20,50.00,"Credit transaction",CREDIT,REF456,949.50"""

        result = parser._parse_pipe_delimited_response(response)

        assert len(result["transactions"]) == 2

        # First transaction
        assert result["transactions"][0]["date"] == "2024-01-15"
        assert result["transactions"][0]["amount"] == -100.50
        assert result["transactions"][0]["description"] == "Test transaction"
        assert result["transactions"][0]["transaction_type"] == "DEBIT"
        assert result["transactions"][0]["reference"] == "REF123"
        assert result["transactions"][0]["balance"] == 899.50

        # Second transaction
        assert result["transactions"][1]["date"] == "2024-01-20"
        assert result["transactions"][1]["amount"] == 50.00
        assert result["transactions"][1]["transaction_type"] == "CREDIT"

    def test_parse_handles_missing_fields(self):
        """Test parsing handles missing optional fields"""
        parser = ClaudeDocumentParser()

        response = """METADATA,123,PLN,,,,,
TXN,2024-01-15,-100.50,"Test",DEBIT,,"""

        result = parser._parse_pipe_delimited_response(response)

        # Metadata with missing fields
        assert result["metadata"]["account_number"] == "123"
        assert result["metadata"]["currency"] == "PLN"
        assert result["metadata"]["opening_balance"] is None
        assert result["metadata"]["closing_balance"] is None

        # Transaction with missing fields
        assert result["transactions"][0]["reference"] is None
        assert result["transactions"][0]["balance"] is None

    def test_parse_skips_malformed_lines(self):
        """Test that malformed lines are skipped gracefully"""
        parser = ClaudeDocumentParser()

        response = """METADATA,123,PLN,2024-01-01,2024-01-31,1000.00,500.00
TXN,2024-01-15,-100.50,"Valid transaction",DEBIT,REF1,900.00
TXN,2024-01-16,INVALID_AMOUNT,"Bad transaction",DEBIT,REF2,800.00
TXN,2024-01-17,-50.00,"Another valid",DEBIT,REF3,750.00"""

        result = parser._parse_pipe_delimited_response(response)

        # Should have 2 valid transactions (skipped the malformed one)
        assert len(result["transactions"]) == 2
        assert result["transactions"][0]["date"] == "2024-01-15"
        assert result["transactions"][1]["date"] == "2024-01-17"

    def test_parse_allows_statements_without_transactions(self):
        """Test that parsing allows statements with no transactions (empty statements are valid)"""
        parser = ClaudeDocumentParser()

        response = """METADATA,123,PLN,2024-01-01,2024-01-31,1000.00,1000.00"""

        # Empty statements are valid as long as metadata is present
        result = parser._parse_pipe_delimited_response(response)

        assert len(result["transactions"]) == 0
        assert result["metadata"]["account_number"] == "123"
        assert result["metadata"]["currency"] == "PLN"
        assert result["metadata"]["opening_balance"] == 1000.00
        assert result["metadata"]["closing_balance"] == 1000.00

    def test_parse_handles_special_chars_in_quoted_description(self):
        """Test parsing when description contains special characters (pipes, commas)

        This should work correctly with CSV quoting.
        """
        parser = ClaudeDocumentParser()

        # Descriptions with pipes, commas, and quotes should work when properly quoted
        response = """METADATA,123,PLN,2024-01-01,2024-01-31,1000.00,500.00
TXN,2024-01-15,-100.50,"Description with | pipe and , comma",DEBIT,REF123,899.50
TXN,2024-01-16,-50.00,"Simple description",DEBIT,REF456,849.50"""

        result = parser._parse_pipe_delimited_response(response)

        # Both transactions should parse correctly
        assert len(result["transactions"]) == 2
        # First transaction with special chars
        assert result["transactions"][0]["description"] == "Description with | pipe and , comma"
        # Second normal transaction
        assert result["transactions"][1]["description"] == "Simple description"
