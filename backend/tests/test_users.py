import pytest
import sys
from pathlib import Path

# Add tests directory to path for conftest import
sys.path.insert(0, str(Path(__file__).parent))

from app import crud, schemas
from conftest import override_get_db


def test_create_user(client):
    """Test creating a user in the test database"""
    db = next(override_get_db())
    try:
        user_data = schemas.UserCreate(
            clerk_id="test_clerk_id",
            email="test@example.com",
            first_name="Test",
            last_name="User"
        )
        user = crud.create_user(db=db, user=user_data)
        assert user.email == "test@example.com"
        assert user.clerk_id == "test_clerk_id"
        assert user.first_name == "Test"
        assert user.last_name == "User"
        assert user.is_active is True
    finally:
        db.close()


def test_get_user_by_clerk_id(client):
    """Test retrieving a user by clerk_id"""
    db = next(override_get_db())
    try:
        user_data = schemas.UserCreate(
            clerk_id="test_clerk_id_2",
            email="test2@example.com",
            first_name="Test2",
            last_name="User2"
        )
        created_user = crud.create_user(db=db, user=user_data)
        retrieved_user = crud.get_user_by_clerk_id(db=db, clerk_id="test_clerk_id_2")
        assert retrieved_user.id == created_user.id
        assert retrieved_user.email == "test2@example.com"
    finally:
        db.close()
