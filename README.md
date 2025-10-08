# Micro-SaaS MVP

A full-stack Micro-SaaS application built with FastAPI (Python) backend and React (TypeScript) frontend, featuring Clerk authentication and ready for deployment on Railway and Vercel.

## Features

- **Backend**: FastAPI with SQLAlchemy, Alembic, and Pydantic
- **Frontend**: React with TypeScript, Vite, and Tanstack Query
- **Authentication**: Clerk integration for both frontend and backend
- **Database**: PostgreSQL with automatic migrations
- **AI-Powered Parsing**: Claude AI for automatic document transaction extraction
- **Multi-Format Support**: CSV, PDF, XLS, and XLSX files
- **Stripe Integration**: Subscription management and payment processing
- **Error Tracking**: Sentry integration for both frontend and backend
- **Testing**: Pytest for backend, Vitest for frontend
- **Development**: Docker Compose for local development
- **Deployment**: Railway (backend) and Vercel (frontend) ready

## Project Structure

```
micro-saas-mvp/
├── backend/
│   ├── app/
│   │   ├── routers/
│   │   │   ├── health.py
│   │   │   └── users.py
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── config.py
│   │   ├── crud.py
│   │   ├── database.py
│   │   ├── main.py
│   │   ├── models.py
│   │   └── schemas.py
│   ├── alembic/
│   ├── tests/
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── railway.toml
│   └── Procfile
├── frontend/
│   ├── src/
│   │   ├── test/
│   │   ├── App.tsx
│   │   ├── App.css
│   │   ├── index.css
│   │   └── main.tsx
│   ├── package.json
│   ├── vite.config.ts
│   ├── Dockerfile
│   └── vercel.json
├── docker-compose.yml
├── .gitignore
└── README.md
```

## Getting Started

### Prerequisites

- Node.js 18+
- Python 3.11+
- Docker and Docker Compose
- Clerk account (for authentication)

### Environment Setup

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd micro-saas-mvp
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   cp backend/.env.example backend/.env
   cp frontend/.env.local frontend/.env.local
   ```

3. **Configure required API keys**

   **Clerk Authentication:**
   - Create a Clerk application at [clerk.com](https://clerk.com)
   - Add to `.env` and `backend/.env`: `CLERK_SECRET_KEY` and `CLERK_PUBLISHABLE_KEY`
   - Add to `frontend/.env.local`: `VITE_CLERK_PUBLISHABLE_KEY`

   **Anthropic Claude AI:**
   - Get an API key from [console.anthropic.com](https://console.anthropic.com)
   - Add to `.env` and `backend/.env`: `ANTHROPIC_API_KEY=your-key-here`

   **Stripe (Optional - for subscriptions):**
   - Create account at [stripe.com](https://stripe.com)
   - Add to `.env` and `backend/.env`:
     - `STRIPE_SECRET_KEY`
     - `STRIPE_PUBLISHABLE_KEY`
     - `STRIPE_WEBHOOK_SECRET`
     - `STRIPE_PRICE_ID`

   **Sentry (Optional - for error tracking):**
   - Create account at [sentry.io](https://sentry.io)
   - Add to `.env`: `SENTRY_DSN`
   - Add to `frontend/.env.local`: `VITE_SENTRY_DSN`

### Development with Docker Compose

1. **Start all services**
   ```bash
   docker-compose up -d
   ```

2. **Access the applications**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

3. **Run database migrations**
   ```bash
   docker-compose exec backend alembic upgrade head
   ```

4. **Stop services**
   ```bash
   docker-compose down
   ```

### Local Development (Alternative)

#### Backend Setup

1. **Navigate to backend directory**
   ```bash
   cd backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\\Scripts\\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up PostgreSQL database**
   ```bash
   # Install PostgreSQL and create database
   createdb micro_saas_db
   ```

5. **Run migrations**
   ```bash
   alembic upgrade head
   ```

6. **Start the server**
   ```bash
   uvicorn app.main:app --reload
   ```

#### Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Start the development server**
   ```bash
   npm run dev
   ```

## Testing

### Backend Tests

```bash
cd backend
pytest
pytest --cov=app  # With coverage
```

### Frontend Tests

```bash
cd frontend
npm test
npm run test:coverage  # With coverage
```

## Deployment

### Backend Deployment (Railway)

1. **Connect your repository to Railway**
2. **Set environment variables in Railway dashboard:**
   - `DATABASE_URL` (Railway will provide PostgreSQL)
   - `SECRET_KEY`
   - `CLERK_SECRET_KEY`
   - `CLERK_PUBLISHABLE_KEY`
   - `ENVIRONMENT=production`

3. **Deploy**
   Railway will automatically detect the `railway.toml` configuration and deploy your backend.

### Frontend Deployment (Vercel)

1. **Connect your repository to Vercel**
2. **Set environment variables in Vercel dashboard:**
   - `VITE_CLERK_PUBLISHABLE_KEY`
   - `VITE_API_URL` (your Railway backend URL)

3. **Deploy**
   Vercel will automatically detect the framework and deploy your frontend.

## API Endpoints

### Health Check
- `GET /health/` - Health check endpoint

### Users
- `GET /users/me` - Get current user (requires authentication)
- `PUT /users/me` - Update current user (requires authentication)
- `GET /users/` - List users (requires authentication)

### Conversion
- `GET /conversion/supported-banks` - List supported banks (legacy)
- `POST /conversion/csv-to-mt940` - Convert CSV to MT940 (legacy bank-specific)
- `POST /conversion/auto-convert` - AI-powered auto-conversion (CSV, PDF, XLS, XLSX)

### Subscription
- `GET /subscription/status` - Get user subscription status
- `POST /subscription/create-checkout-session` - Create Stripe checkout session
- `POST /subscription/create-portal-session` - Create Stripe customer portal session
- `POST /subscription/webhook` - Stripe webhook handler (public endpoint)

## Authentication Flow

1. User signs in through Clerk on the frontend
2. Frontend receives JWT token from Clerk
3. Frontend sends requests with `Authorization: Bearer <token>` header
4. Backend verifies token with Clerk and creates/updates user in database
5. Backend returns user data or performs requested operations

## Database Schema

### Users Table
- `id`: Primary key
- `clerk_id`: Unique identifier from Clerk
- `email`: User email
- `first_name`: User's first name
- `last_name`: User's last name
- `is_active`: Boolean flag
- `created_at`: Timestamp
- `updated_at`: Timestamp

## Development Commands

### Backend
- `alembic revision --autogenerate -m "description"` - Create new migration
- `alembic upgrade head` - Run migrations
- `pytest` - Run tests
- `uvicorn app.main:app --reload` - Start development server

### Frontend
- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm test` - Run tests
- `npm run lint` - Run linting

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License.