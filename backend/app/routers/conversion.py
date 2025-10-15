from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import Response
from typing import List, Optional
from sqlalchemy.orm import Session
import logging
import io

from ..services import BankParserRegistry
from ..services.parsers.base import BankParserError
from ..services.mt940_converter import MT940Converter, MT940ConverterError
from ..services.claude_parser import ClaudeDocumentParser
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
        logger.info(f"Conversion tracked for user {current_user.id}")

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
        logger.error(f"Bank parser error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Parser error: {str(e)}")

    except MT940ConverterError as e:
        logger.error(f"MT940 converter error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Conversion error: {str(e)}")

    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File encoding not supported. Please use UTF-8.")

    except Exception as e:
        logger.error(f"Unexpected error during conversion: {str(e)}")
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

    try:
        # Read file content
        content = await file.read()
        file_stream = io.BytesIO(content)

        # Initialize Claude parser
        parser = ClaudeDocumentParser()

        # Parse document
        logger.info(f"Parsing document: {file.filename}")
        parsed_data = parser.parse_document(
            file_content=file_stream,
            filename=file.filename,
            account_number=account_number
        )

        # Convert to MT940
        logger.info(f"Converting to MT940 format")
        mt940_content = parser.convert_to_mt940(
            transactions_data=parsed_data,
            account_number=account_number
        )

        # Track conversion usage
        usage = ConversionUsageCreate(
            user_id=current_user.id,
            file_name=file.filename,
            bank_name="auto-detected"
        )
        crud.create_conversion_usage(db, usage)
        logger.info(f"Auto-conversion tracked for user {current_user.id}")

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

    except ValueError as e:
        logger.error(f"Value error during parsing: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(f"Unexpected error during auto-conversion: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Auto-conversion error: {str(e)}")