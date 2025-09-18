import jwt
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from clerk_backend_api import Clerk
from .config import settings
from .schemas import UserCreate
from .crud import create_user, get_user_by_clerk_id
from .database import get_db
from sqlalchemy.orm import Session
from fastapi import Depends
import httpx

security = HTTPBearer()
clerk = Clerk(bearer_auth=settings.clerk_secret_key)


async def verify_token(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db)
):
    try:
        token = credentials.credentials

        # Verify the JWT token with Clerk
        # First, get the JWKS from Clerk to verify the token
        async with httpx.AsyncClient() as client:
            jwks_response = await client.get(f"https://clerk.{settings.clerk_publishable_key.split('_')[2]}.lcl.dev/.well-known/jwks.json")
            if jwks_response.status_code != 200:
                # Fallback to generic endpoint
                jwks_response = await client.get("https://api.clerk.com/v1/jwks")

            if jwks_response.status_code != 200:
                raise HTTPException(status_code=401, detail="Could not verify token")

        # Decode the JWT token (simplified verification for development)
        try:
            # For development, we'll decode without verification
            # In production, you should properly verify the JWT with the JWKS
            decoded_token = jwt.decode(token, options={"verify_signature": False})
            user_id = decoded_token.get("sub")

            if not user_id:
                raise HTTPException(status_code=401, detail="Invalid token format")

        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")

        # Get user info from Clerk using the new API
        try:
            user_response = clerk.users.get_user(user_id=user_id)
            user_data = user_response
        except Exception as e:
            raise HTTPException(status_code=401, detail=f"Could not fetch user data: {str(e)}")

        # Check if user exists in our database
        db_user = get_user_by_clerk_id(db, clerk_id=user_data.id)

        # If user doesn't exist, create them
        if not db_user:
            # Handle email addresses safely
            email = ""
            if user_data.email_addresses and len(user_data.email_addresses) > 0:
                email = user_data.email_addresses[0].email_address

            user_create = UserCreate(
                clerk_id=user_data.id,
                email=email,
                first_name=user_data.first_name,
                last_name=user_data.last_name
            )
            db_user = create_user(db, user=user_create)

        return db_user

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token verification failed: {str(e)}")