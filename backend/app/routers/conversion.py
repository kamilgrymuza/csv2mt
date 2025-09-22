from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import Response
from typing import List
import logging

from ..services import BankParserRegistry
from ..services.parsers.base import BankParserError
from ..services.mt940_converter import MT940Converter, MT940ConverterError

router = APIRouter(prefix="/conversion", tags=["conversion"])
logger = logging.getLogger(__name__)


@router.get("/supported-banks")
async def get_supported_banks() -> List[str]:
    return BankParserRegistry.get_supported_banks()


@router.post("/csv-to-mt940")
async def convert_csv_to_mt940(
    file: UploadFile = File(...),
    bank_name: str = Form(...)
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

        # Return MT940 file
        filename = f"{file.filename.rsplit('.', 1)[0]}.mt940"

        return Response(
            content=mt940_content,
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
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