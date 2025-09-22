import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestConversionAPI:
    def test_get_supported_banks(self):
        response = client.get("/conversion/supported-banks")
        assert response.status_code == 200
        banks = response.json()
        assert isinstance(banks, list)
        assert "santander" in banks

    def test_convert_csv_to_mt940_success(self):
        csv_content = """2025-09-22,01-09-2025,'64 1500 1878 1018 7023 1577 0000,KAMIL GRYMUZA UL. BUKOWIŃSKA 24C/8 02-703 WARSZAWA,PLN,"-2317,82","-3681,08",1,
19-09-2025,19-09-2025,Opłata za odnowienie kred. w rach. pł.,,,"-500,00","-3681,08",1,"""

        files = {"file": ("test.csv", csv_content, "text/csv")}
        data = {"bank_name": "Santander"}

        response = client.post("/conversion/csv-to-mt940", files=files, data=data)

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/octet-stream"
        assert "attachment; filename=test.mt940" in response.headers["content-disposition"]

        # Check MT940 content structure
        content = response.content.decode('utf-8')
        lines = content.split('\n')
        assert lines[0].startswith(":20:")
        assert lines[-1] == "-"

    def test_convert_csv_invalid_bank(self):
        csv_content = "dummy,csv,content"
        files = {"file": ("test.csv", csv_content, "text/csv")}
        data = {"bank_name": "InvalidBank"}

        response = client.post("/conversion/csv-to-mt940", files=files, data=data)

        assert response.status_code == 400
        assert "Bank 'InvalidBank' not supported" in response.json()["detail"]

    def test_convert_non_csv_file(self):
        files = {"file": ("test.txt", "dummy content", "text/plain")}
        data = {"bank_name": "Santander"}

        response = client.post("/conversion/csv-to-mt940", files=files, data=data)

        assert response.status_code == 400
        assert "File must be a CSV file" in response.json()["detail"]

    def test_convert_invalid_csv_content(self):
        csv_content = "invalid,csv,format"
        files = {"file": ("test.csv", csv_content, "text/csv")}
        data = {"bank_name": "Santander"}

        response = client.post("/conversion/csv-to-mt940", files=files, data=data)

        assert response.status_code == 400
        assert "Parser error" in response.json()["detail"]

    def test_convert_empty_file(self):
        files = {"file": ("test.csv", "", "text/csv")}
        data = {"bank_name": "Santander"}

        response = client.post("/conversion/csv-to-mt940", files=files, data=data)

        assert response.status_code == 400
        assert "Parser error" in response.json()["detail"]

    def test_convert_malformed_csv(self):
        csv_content = """2025-09-22,01-09-2025,'64 1500 1878 1018 7023 1577 0000,KAMIL GRYMUZA,PLN,"-2317,82","-3681,08",1,
invalid,transaction,row"""

        files = {"file": ("test.csv", csv_content, "text/csv")}
        data = {"bank_name": "Santander"}

        response = client.post("/conversion/csv-to-mt940", files=files, data=data)

        assert response.status_code == 400
        assert "Parser error" in response.json()["detail"]