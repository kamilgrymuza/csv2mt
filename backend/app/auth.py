import jwt
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx
from .config import settings
from .schemas import UserCreate
from .crud import create_user, get_user_by_clerk_id
from .database import get_db
from sqlalchemy.orm import Session
from fastapi import Depends

security = HTTPBearer()


async def verify_token(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db)
):
    try:
        token = credentials.credentials

        # Verify the JWT token with Clerk by calling their verify endpoint
        async with httpx.AsyncClient() as client:
            verify_response = await client.get(
                f"https://api.clerk.com/v1/sessions/{token}/verify",
                headers={
                    "Authorization": f"Bearer {settings.clerk_secret_key}",
                    "Content-Type": "application/json"
                }
            )

            if verify_response.status_code == 200:
                session_data = verify_response.json()
                user_id = session_data.get("user_id")
            else:
                # Try to decode JWT directly as fallback
                try:
                    decoded_token = jwt.decode(token, options={"verify_signature": False})
                    user_id = decoded_token.get("sub")
                    if not user_id:
                        raise HTTPException(status_code=401, detail="No user ID in token")
                except jwt.InvalidTokenError:
                    raise HTTPException(status_code=401, detail="Invalid token")

        if not user_id:
            raise HTTPException(status_code=401, detail="Could not extract user ID from token")

        # Get user info from Clerk's Users API
        async with httpx.AsyncClient() as client:
            user_response = await client.get(
                f"https://api.clerk.com/v1/users/{user_id}",
                headers={
                    "Authorization": f"Bearer {settings.clerk_secret_key}",
                    "Content-Type": "application/json"
                }
            )

            if user_response.status_code != 200:
                raise HTTPException(status_code=401, detail="Could not fetch user data from Clerk")

            user_data = user_response.json()

        # Check if user exists in our database
        db_user = get_user_by_clerk_id(db, clerk_id=user_data["id"])

        # If user doesn't exist, create them
        if not db_user:
            # Handle email addresses safely
            email = ""
            if user_data.get("email_addresses") and len(user_data["email_addresses"]) > 0:
                email = user_data["email_addresses"][0]["email_address"]

            user_create = UserCreate(
                clerk_id=user_data["id"],
                email=email,
                first_name=user_data.get("first_name"),
                last_name=user_data.get("last_name")
            )
            db_user = create_user(db, user=user_create)

        return db_user

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token verification failed: {str(e)}")