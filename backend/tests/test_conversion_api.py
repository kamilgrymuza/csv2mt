import pytest
import sys
from pathlib import Path

# Add tests directory to path for conftest import
sys.path.insert(0, str(Path(__file__).parent))

from fastapi.testclient import TestClient
from app.main import app
from app.dependencies import get_current_user_with_usage_check
from app.models import User
from app import crud, schemas
from conftest import override_get_db


@pytest.fixture
def client_with_auth(client):
    """Client with authentication dependency overridden and test database"""
    # Create a mock user in the test database
    db = next(override_get_db())
    try:
        # Create the mock user
        user_data = schemas.UserCreate(
            clerk_id="mock_api_test_clerk_id",
            email="mock_api_test@example.com",
            first_name="MockAPI",
            last_name="TestUser"
        )
        mock_user = crud.create_user(db=db, user=user_data)

        # Create a function that returns this specific user
        def get_mock_user():
            return mock_user

        # Override the authentication dependency
        app.dependency_overrides[get_current_user_with_usage_check] = get_mock_user

        yield client
    finally:
        app.dependency_overrides.clear()
        db.close()


class TestConversionAPI:
    def test_get_supported_banks(self):
        """Test getting supported banks (no auth required)"""
        client = TestClient(app)
        response = client.get("/conversion/supported-banks")
        assert response.status_code == 200
        banks = response.json()
        assert isinstance(banks, list)
        assert "santander" in banks

    def test_convert_csv_to_mt940_success(self, client_with_auth):
        """Test successful CSV to MT940 conversion"""
        csv_content = """2025-09-22,01-09-2025,'64 1500 1878 1018 7023 1577 0000,KAMIL GRYMUZA UL. BUKOWIŃSKA 24C/8 02-703 WARSZAWA,PLN,"-2317,82","-3681,08",1,
19-09-2025,19-09-2025,Opłata za odnowienie kred. w rach. pł.,,,"-500,00","-3681,08",1,"""

        files = {"file": ("test.csv", csv_content, "text/csv")}
        data = {"bank_name": "Santander"}

        response = client_with_auth.post("/conversion/csv-to-mt940", files=files, data=data)

        assert response.status_code == 200
        # Content-Type header includes charset=utf-8
        assert "text/plain" in response.headers["content-type"]
        assert "charset=utf-8" in response.headers["content-type"]
        assert "attachment; filename=test.mt940" in response.headers["content-disposition"]

        # Check MT940 content structure
        content = response.content.decode('utf-8')
        lines = content.split('\n')
        assert lines[0].startswith(":20:")
        assert lines[-1] == "-"

    def test_convert_csv_invalid_bank(self, client_with_auth):
        """Test conversion with invalid bank name"""
        csv_content = "dummy,csv,content"
        files = {"file": ("test.csv", csv_content, "text/csv")}
        data = {"bank_name": "InvalidBank"}

        response = client_with_auth.post("/conversion/csv-to-mt940", files=files, data=data)

        assert response.status_code == 400
        assert "Bank 'InvalidBank' not supported" in response.json()["detail"]

    def test_convert_non_csv_file(self, client_with_auth):
        """Test conversion with non-CSV file"""
        files = {"file": ("test.txt", "dummy content", "text/plain")}
        data = {"bank_name": "Santander"}

        response = client_with_auth.post("/conversion/csv-to-mt940", files=files, data=data)

        assert response.status_code == 400
        assert "File must be a CSV file" in response.json()["detail"]

    def test_convert_invalid_csv_content(self, client_with_auth):
        """Test conversion with invalid CSV content"""
        csv_content = "invalid,csv,format"
        files = {"file": ("test.csv", csv_content, "text/csv")}
        data = {"bank_name": "Santander"}

        response = client_with_auth.post("/conversion/csv-to-mt940", files=files, data=data)

        assert response.status_code == 400
        assert "Parser error" in response.json()["detail"]

    def test_convert_empty_file(self, client_with_auth):
        """Test conversion with empty file"""
        files = {"file": ("test.csv", "", "text/csv")}
        data = {"bank_name": "Santander"}

        response = client_with_auth.post("/conversion/csv-to-mt940", files=files, data=data)

        assert response.status_code == 400
        assert "Parser error" in response.json()["detail"]

    def test_convert_malformed_csv(self, client_with_auth):
        """Test conversion with malformed CSV"""
        csv_content = """2025-09-22,01-09-2025,'64 1500 1878 1018 7023 1577 0000,KAMIL GRYMUZA,PLN,"-2317,82","-3681,08",1,
invalid,transaction,row"""

        files = {"file": ("test.csv", csv_content, "text/csv")}
        data = {"bank_name": "Santander"}

        response = client_with_auth.post("/conversion/csv-to-mt940", files=files, data=data)

        assert response.status_code == 400
        assert "Parser error" in response.json()["detail"]
