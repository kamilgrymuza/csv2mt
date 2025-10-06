# Railway Deployment Guide

This guide will help you deploy your Micro-SaaS application to Railway.

## Prerequisites

1. **Railway Account**: Sign up at [railway.app](https://railway.app)
2. **GitHub Repository**: Your code should be pushed to GitHub
3. **Clerk Account**: Set up at [clerk.com](https://clerk.com) with your API keys

## Step-by-Step Deployment

### 1. Prepare Your Repository

First, ensure your code is committed and pushed to GitHub:

```bash
# From your project root
git add .
git commit -m "Prepare for Railway deployment"
git push origin main
```

### 2. Deploy Database (PostgreSQL)

1. **Login to Railway**: Go to [railway.app](https://railway.app) and sign in
2. **Create New Project**: Click "New Project"
3. **Add PostgreSQL**:
   - Click "Add Service"
   - Select "Database"
   - Choose "PostgreSQL"
4. **Note Database URL**: Railway will provide a `DATABASE_URL` - you'll need this for the backend

### 3. Deploy Backend (FastAPI)

1. **Add Backend Service**:
   - In your Railway project, click "Add Service"
   - Select "GitHub Repo"
   - Connect your repository
   - Choose your repository

2. **Configure Backend Settings**:
   - **Root Directory**: Set to `backend`
   - **Build Command**: Leave empty (Nixpacks will handle this)
   - **Start Command**: Will use the railway.toml configuration

3. **Set Environment Variables**:
   ```
   DATABASE_URL=postgresql://[from your PostgreSQL service]
   SECRET_KEY=your-super-secret-key-here
   CLERK_SECRET_KEY=sk_test_your_clerk_secret_key
   CLERK_PUBLISHABLE_KEY=pk_test_your_clerk_publishable_key
   ENVIRONMENT=production
   ```

4. **Deploy**: Click "Deploy" - Railway will build and deploy your backend

### 4. Frontend Deployment Options

#### Option A: Deploy Frontend to Railway

1. **Add Frontend Service**:
   - Click "Add Service" → "GitHub Repo"
   - Select the same repository
   - Set **Root Directory** to `frontend`

2. **Set Environment Variables**:
   ```
   VITE_CLERK_PUBLISHABLE_KEY=pk_test_your_clerk_publishable_key
   VITE_API_URL=https://your-backend-service.railway.app
   ```

#### Option B: Deploy Frontend to Vercel (Recommended)

1. **Connect to Vercel**:
   - Go to [vercel.com](https://vercel.com)
   - Import your GitHub repository
   - Set **Root Directory** to `frontend`

2. **Set Environment Variables in Vercel**:
   ```
   VITE_CLERK_PUBLISHABLE_KEY=pk_test_your_clerk_publishable_key
   VITE_API_URL=https://your-backend-service.railway.app
   ```

## Environment Variables Setup

### Backend Environment Variables (Railway)

```env
DATABASE_URL=postgresql://postgres:password@host:port/dbname
SECRET_KEY=your-super-secret-key-minimum-32-characters-long
CLERK_SECRET_KEY=sk_test_your_actual_clerk_secret_key
CLERK_PUBLISHABLE_KEY=pk_test_your_actual_clerk_publishable_key
ENVIRONMENT=production
```

### Frontend Environment Variables (Railway/Vercel)

```env
VITE_CLERK_PUBLISHABLE_KEY=pk_test_your_actual_clerk_publishable_key
VITE_API_URL=https://your-backend-railway-url.railway.app
```

## Post-Deployment Steps

### 1. Test Your Deployment

1. **Backend Health Check**: Visit `https://your-backend-url.railway.app/health/`
2. **API Documentation**: Visit `https://your-backend-url.railway.app/docs`
3. **Frontend**: Visit your frontend URL and test authentication

### 2. Update CORS Settings

If you encounter CORS issues, update your backend's `main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3000",
        "https://your-frontend-domain.vercel.app",  # Add your production frontend URL
        "https://your-frontend-domain.railway.app"  # If using Railway for frontend
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 3. Configure Clerk for Production

1. **Add Production URLs to Clerk**:
   - In your Clerk dashboard, go to "Domains"
   - Add your production frontend URL
   - Update redirect URLs if needed

## Troubleshooting

### Common Issues

1. **Database Connection Issues**:
   - Verify DATABASE_URL is correctly set
   - Check if PostgreSQL service is running

2. **Build Failures**:
   - Check Railway build logs
   - Ensure all dependencies are in requirements.txt

3. **Authentication Issues**:
   - Verify Clerk keys are correct
   - Check CORS settings
   - Ensure frontend API_URL points to backend

4. **Environment Variables**:
   - Double-check all environment variables are set
   - Restart services after changing environment variables

### Railway CLI (Optional)

Install Railway CLI for easier management:

```bash
npm install -g @railway/cli
railway login
railway link  # Link to your project
railway logs  # View logs
```

## Scaling Considerations

1. **Database**: Consider upgrading PostgreSQL plan for production traffic
2. **Backend**: Railway auto-scales based on usage
3. **Monitoring**: Use Railway's built-in monitoring and logs

## Security Checklist

- [ ] All environment variables are set correctly
- [ ] SECRET_KEY is strong and unique
- [ ] Clerk keys are production keys (not test keys for production)
- [ ] Database credentials are secure
- [ ] CORS is properly configured
- [ ] HTTPS is enabled (Railway provides this automatically)

Your Micro-SaaS application should now be successfully deployed to Railway! 🚀