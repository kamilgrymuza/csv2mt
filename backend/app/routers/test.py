from fastapi import APIRouter

router = APIRouter(
    prefix="/test",
    tags=["test"]
)


@router.get("/public")
async def test_public():
    """Public endpoint that doesn't require authentication"""
    return {
        "message": "This is a public endpoint - no authentication required!",
        "status": "success"
    }


@router.get("/auth-info")
async def auth_info():
    """Information about authentication setup"""
    return {
        "message": "To test authenticated endpoints, you need to:",
        "steps": [
            "1. Create a Clerk account at https://clerk.com",
            "2. Create a new application in Clerk dashboard",
            "3. Get your publishable key (starts with pk_test_...)",
            "4. Get your secret key (starts with sk_test_...)",
            "5. Update .env file with CLERK_SECRET_KEY=your_secret_key",
            "6. Update frontend/.env.local with VITE_CLERK_PUBLISHABLE_KEY=your_publishable_key",
            "7. Restart docker-compose services",
            "8. Sign up/in via the frontend and test the protected dashboard"
        ],
        "current_setup": "Authentication is configured but needs real Clerk credentials"
    }