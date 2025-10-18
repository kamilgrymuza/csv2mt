from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import Response, JSONResponse
from typing import List, Optional
from sqlalchemy.orm import Session
import logging
import io

from ..services import BankParserRegistry
from ..services.parsers.base import BankParserError
from ..services.mt940_converter import MT940Converter, MT940ConverterError
from ..services.claude_parser import ClaudeDocumentParser, EmptyStatementError
from ..dependencies import get_current_user_with_usage_check
from ..database import get_db
from ..models import User
from ..schemas import ConversionUsageCreate
from .. import crud

router = APIRouter(prefix="/conversion", tags=["conversion"])
logger = logging.getLogger(__name__)


@router.get("/supported-banks")
async def get_supported_banks() -> List[str]:
    return BankParserRegistry.get_supported_banks()


@router.post("/csv-to-mt940")
async def convert_csv_to_mt940(
    file: UploadFile = File(...),
    bank_name: str = Form(...),
    current_user: User = Depends(get_current_user_with_usage_check),
    db: Session = Depends(get_db)
) -> Response:
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV file")

    try:
        # Read file content
        content = await file.read()
        csv_content = content.decode('utf-8')

        # Get the appropriate parser
        parser = BankParserRegistry.get_parser(bank_name)

        # Parse the CSV
        bank_statement = parser.validate_and_parse(csv_content)

        # Convert to MT940
        mt940_content = MT940Converter.convert(bank_statement)

        # Track conversion usage (after successful conversion)
        usage = ConversionUsageCreate(
            user_id=current_user.id,
            file_name=file.filename,
            bank_name=bank_name
        )
        crud.create_conversion_usage(db, usage)
        logger.info("Conversion tracked for user %s", current_user.id)

        # Return MT940 file (encode as UTF-8)
        filename = f"{file.filename.rsplit('.', 1)[0]}.mt940"

        return Response(
            content=mt940_content.encode('utf-8'),
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Type": "text/plain; charset=utf-8"
            }
        )

    except BankParserError as e:
        logger.error("Bank parser error: %s", str(e))
        raise HTTPException(status_code=400, detail=f"Parser error: {str(e)}")

    except MT940ConverterError as e:
        logger.error("MT940 converter error: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Conversion error: {str(e)}")

    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File encoding not supported. Please use UTF-8.")

    except Exception as e:
        logger.error("Unexpected error during conversion: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal server error during conversion")


@router.post("/auto-convert")
async def auto_convert_document(
    file: UploadFile = File(...),
    account_number: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user_with_usage_check),
    db: Session = Depends(get_db)
) -> Response:
    """
    Automatically convert documents (CSV, PDF, XLS/XLSX) to MT940 using Claude AI.

    This endpoint uses AI to automatically detect and extract transaction data
    from various document formats without requiring bank-specific parsers.
    """
    # Validate file type
    filename = file.filename.lower()
    allowed_extensions = ['.csv', '.pdf', '.xls', '.xlsx']

    if not any(filename.endswith(ext) for ext in allowed_extensions):
        raise HTTPException(
            status_code=400,
            detail=f"File must be one of: {', '.join(allowed_extensions)}"
        )

    usage_record = None  # Track the usage record for error updates

    try:
        # Read file content
        content = await file.read()
        file_stream = io.BytesIO(content)

        # Initialize Claude parser
        parser = ClaudeDocumentParser()

        # Parse document
        logger.info("Parsing document: %s", file.filename)
        parsed_data = parser.parse_document(
            file_content=file_stream,
            filename=file.filename,
            account_number=account_number
        )

        # Extract format specification for debugging (if available in metadata)
        metadata = parsed_data.get("metadata", {})
        format_spec_json = None

        # Try to get format_specification (successful) or failed_format_specification (fell back to AI)
        format_spec = metadata.get("format_specification") or metadata.get("failed_format_specification")

        if format_spec:
            import json
            try:
                format_spec_json = json.dumps(format_spec)
                spec_type = "format_specification" if "format_specification" in metadata else "failed_format_specification"
                logger.info("%s stored for file %s (%d chars)", spec_type, file.filename, len(format_spec_json))
            except (TypeError, ValueError) as e:
                logger.warning("Failed to serialize format specification for file %s: %s", file.filename, e)

        # Track conversion usage AFTER parsing succeeds (even if MT940 conversion fails)
        # This ensures empty/invalid statements count towards usage since parsing consumed AI tokens
        usage = ConversionUsageCreate(
            user_id=current_user.id,
            file_name=file.filename,
            bank_name="auto-detected",
            input_tokens=metadata.get("input_tokens"),
            output_tokens=metadata.get("output_tokens"),
            format_specification=format_spec_json,
            parsing_method=metadata.get("parsing_method")
        )
        usage_record = crud.create_conversion_usage(db, usage)
        logger.info("Auto-conversion tracked for user %s (input: %s, output: %s, method: %s)",
                   current_user.id, usage.input_tokens, usage.output_tokens, usage.parsing_method)

        # Convert to MT940
        logger.info("Converting to MT940 format")
        mt940_content = parser.convert_to_mt940(
            transactions_data=parsed_data,
            account_number=account_number
        )

        # Return MT940 file (encode as UTF-8)
        output_filename = f"{file.filename.rsplit('.', 1)[0]}.mt940"

        return Response(
            content=mt940_content.encode('utf-8'),
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f"attachment; filename={output_filename}",
                "Content-Type": "text/plain; charset=utf-8"
            }
        )

    except EmptyStatementError as e:
        # Expected error: file contains no valid transaction data
        # Don't log to Sentry - this is a user input issue, not a bug
        logger.info("Empty statement detected for file %s: %s", file.filename, str(e))

        # Update usage record with error information
        if usage_record:
            usage_record.error_code = "EMPTY_STATEMENT"
            usage_record.error_message = str(e)
            db.commit()

        return JSONResponse(
            status_code=400,
            content={
                "error": {
                    "code": "EMPTY_STATEMENT",
                    "message": str(e),
                    "details": "The uploaded file does not contain valid transaction data or statement dates."
                }
            }
        )

    except ValueError as e:
        # Other validation errors
        logger.warning("Validation error for file %s: %s", file.filename, str(e))

        # Update usage record with error information
        if usage_record:
            usage_record.error_code = "VALIDATION_ERROR"
            usage_record.error_message = str(e)
            db.commit()

        return JSONResponse(
            status_code=400,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": str(e)
                }
            }
        )

    except Exception as e:
        # Unexpected errors - these WILL be logged to Sentry
        logger.error("Unexpected error during auto-conversion for file %s: %s", file.filename, str(e))

        # Update usage record with error information
        if usage_record:
            usage_record.error_code = "INTERNAL_ERROR"
            usage_record.error_message = str(e)
            db.commit()

        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred during conversion. Please try again later."
                }
            }
        )