# Creating a Reusable SaaS Template from This Project

This guide explains how to turn this project into a reusable template for future SaaS projects with Stripe subscriptions.

## Approach 1: Git Branch Template (Recommended)

This is the simplest approach - create a clean branch that can be used as a starting point for new projects.

### Steps:

1. **Create a template branch:**
   ```bash
   # From your main branch
   git checkout -b saas-template-with-stripe
   ```

2. **Remove project-specific code:**

   Keep:
   - All subscription infrastructure
   - Authentication setup
   - Database models and migrations
   - Stripe integration
   - Frontend subscription components

   Remove/Generalize:
   - CSV conversion specific code
   - Bank parser logic
   - Project-specific UI components
   - Any business logic specific to this app

3. **Create a generic "action" endpoint:**

   Replace the conversion endpoint with a generic action endpoint that can be customized:

   ```python
   # backend/app/routers/actions.py
   @router.post("/perform-action")
   async def perform_action(
       current_user: User = Depends(get_current_user_with_usage_check),
       db: Session = Depends(get_db)
   ):
       """
       Generic action endpoint - customize this for your use case
       This endpoint:
       - Checks usage limits automatically
       - Tracks usage in the database
       - Can be renamed/customized for your needs
       """
       # TODO: Add your business logic here

       # Track usage
       usage = ConversionUsageCreate(  # Rename this model as needed
           user_id=current_user.id
       )
       crud.create_conversion_usage(db, usage)

       return {"message": "Action completed"}
   ```

4. **Update documentation:**
   ```bash
   # Create a new README for the template
   cp README.md TEMPLATE_README.md

   # Edit TEMPLATE_README.md to remove CSV-specific content
   # Add instructions for customizing the template
   ```

5. **Commit the template:**
   ```bash
   git add .
   git commit -m "Create SaaS template with Stripe subscription"
   git push origin saas-template-with-stripe
   ```

6. **For future projects:**
   ```bash
   # Clone the repo
   git clone your-repo.git new-saas-project
   cd new-saas-project

   # Start from the template branch
   git checkout saas-template-with-stripe
   git checkout -b main

   # Customize for your new project
   # Update project name, add your business logic, etc.
   ```

## Approach 2: GitHub Template Repository

Create a separate template repository that can be used to generate new projects.

### Steps:

1. **Create new GitHub repository:**
   - Name it something like `saas-stripe-template`
   - Make it a template repository in GitHub settings

2. **Copy essential files:**
   ```bash
   # Backend structure
   backend/
   ├── app/
   │   ├── __init__.py
   │   ├── config.py
   │   ├── database.py
   │   ├── models.py (with subscription models)
   │   ├── schemas.py (with subscription schemas)
   │   ├── crud.py (with subscription CRUD)
   │   ├── auth.py
   │   ├── dependencies.py
   │   ├── main.py
   │   ├── routers/
   │   │   ├── __init__.py
   │   │   ├── subscription.py
   │   │   ├── users.py
   │   │   └── actions.py (generic action endpoint)
   │   └── services/
   │       └── stripe_service.py
   ├── alembic/
   ├── requirements.txt
   └── .env.example

   # Frontend structure
   frontend/
   ├── src/
   │   ├── components/
   │   │   └── ProtectedRoute.tsx
   │   ├── pages/
   │   │   ├── Home.tsx
   │   │   ├── SignInPage.tsx
   │   │   ├── SignUpPage.tsx
   │   │   ├── Dashboard.tsx (generic)
   │   │   └── SubscriptionPage.tsx
   │   ├── App.tsx
   │   └── main.tsx
   ├── package.json
   └── .env.example

   # Documentation
   ├── README.md (template instructions)
   ├── SETUP_STRIPE_GUIDE.md
   ├── SUBSCRIPTION_ARCHITECTURE.md
   └── CUSTOMIZATION_GUIDE.md
   ```

3. **Create template variables:**

   Use placeholders that are easy to find and replace:

   ```python
   # config.py
   app_name = os.getenv("APP_NAME", "{{APP_NAME}}")

   # models.py - rename usage tracking model
   class UsageTracking(Base):  # Generic name
       __tablename__ = "usage_tracking"
       # ... fields
   ```

4. **Use the template:**
   - Click "Use this template" on GitHub
   - Clone the new repository
   - Run a setup script to replace placeholders

## Approach 3: Monorepo with Shared Packages

Create a monorepo structure where subscription logic is a shared package.

### Structure:
```
saas-projects/
├── packages/
│   ├── stripe-subscription-backend/  # Reusable Python package
│   │   ├── setup.py
│   │   └── stripe_subscription/
│   │       ├── models.py
│   │       ├── services.py
│   │       ├── routers.py
│   │       └── dependencies.py
│   └── stripe-subscription-frontend/  # Reusable React components
│       ├── package.json
│       └── src/
│           ├── hooks/
│           ├── components/
│           └── pages/
├── projects/
│   ├── csv-converter/
│   ├── project-two/
│   └── project-three/
└── README.md
```

Install shared package in each project:
```bash
pip install -e ../../packages/stripe-subscription-backend
```

## Recommended: Create a Setup Script

Create a script that automates the customization process:

```bash
#!/bin/bash
# setup-new-project.sh

echo "🚀 Setting up new SaaS project with Stripe"
echo ""

read -p "Project name: " PROJECT_NAME
read -p "Database name: " DB_NAME
read -p "Free tier action limit: " ACTION_LIMIT

# Replace placeholders
find . -type f -name "*.py" -exec sed -i '' "s/{{APP_NAME}}/$PROJECT_NAME/g" {} +
find . -type f -name "*.tsx" -exec sed -i '' "s/{{APP_NAME}}/$PROJECT_NAME/g" {} +

# Update config
sed -i '' "s/{{DB_NAME}}/$DB_NAME/g" backend/.env.example
sed -i '' "s/{{ACTION_LIMIT}}/$ACTION_LIMIT/g" backend/app/config.py

echo "✅ Project customized!"
echo ""
echo "Next steps:"
echo "1. Copy .env.example to .env and add your API keys"
echo "2. Follow SETUP_STRIPE_GUIDE.md to configure Stripe"
echo "3. Run 'alembic upgrade head' to create database tables"
echo "4. Customize the action endpoint in backend/app/routers/actions.py"
echo "5. Start building your app!"
```

Make it executable:
```bash
chmod +x setup-new-project.sh
```

## What to Keep Reusable vs What to Customize

### ✅ Keep Reusable (Don't Touch):

1. **Backend:**
   - `services/stripe_service.py` - All Stripe logic
   - `dependencies.py` - Usage check middleware
   - `routers/subscription.py` - Subscription endpoints
   - Subscription, User models (relationships only)
   - Subscription CRUD operations
   - Database migration structure

2. **Frontend:**
   - `pages/SubscriptionPage.tsx` - Full subscription UI
   - Stripe integration hooks
   - Authentication flow
   - Protected routes

### 🔧 Customize for Each Project:

1. **Backend:**
   - Action endpoints (rename from "conversion")
   - Usage tracking model (rename from "ConversionUsage")
   - Business logic
   - Pricing tiers
   - Free tier limits

2. **Frontend:**
   - Main application pages
   - Branding and styling
   - Feature descriptions in subscription page
   - Usage display components (adapt to your actions)

## File Checklist for Template

Create this checklist in your template:

- [ ] Authentication configured (Clerk/Auth0/etc)
- [ ] Database connected
- [ ] Stripe API keys added
- [ ] Webhook endpoint configured
- [ ] Product and Price created in Stripe
- [ ] Usage tracking model customized
- [ ] Action endpoints renamed/customized
- [ ] Frontend branding updated
- [ ] Pricing displayed correctly
- [ ] Free tier limit configured
- [ ] Email notifications configured
- [ ] Error monitoring set up
- [ ] Database migrations applied
- [ ] All tests passing

## Best Practices for Template Maintenance

1. **Version the template:**
   - Use semantic versioning
   - Tag releases: `v1.0.0-template`
   - Document changes between versions

2. **Keep documentation updated:**
   - Update guides when Stripe API changes
   - Add new features to docs
   - Include migration guides for breaking changes

3. **Test the template regularly:**
   - Create test projects from the template monthly
   - Verify all setup steps work
   - Update dependencies

4. **Gather feedback:**
   - Keep notes on pain points when using the template
   - Improve based on what takes the most time to customize
   - Add more automation

## Example: Quick Start from Template

Your ideal workflow should be:

```bash
# 1. Create new project from template
git clone template-repo.git my-new-saas
cd my-new-saas

# 2. Run setup script
./setup-new-project.sh

# 3. Configure environment
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
# Edit .env files with your keys

# 4. Set up database
cd backend
alembic upgrade head

# 5. Start coding your unique features
# The subscription system is already working!
```

## Maintaining Multiple Projects

Once you have several projects using this template:

### Update Strategy:

1. **Keep template updated in original repo**
2. **Cherry-pick updates to existing projects:**
   ```bash
   # In your existing project
   git remote add template /path/to/template-repo
   git fetch template

   # Cherry-pick specific updates
   git cherry-pick <commit-hash>
   ```

3. **Use a shared package (Approach 3) for critical updates:**
   - Update the package version
   - Update `requirements.txt` in all projects
   - Run tests

## Alternative: Use a Code Generator

Create a Cookiecutter template:

```bash
pip install cookiecutter

# Create from template
cookiecutter gh:your-username/saas-stripe-template
```

The cookiecutter.json would ask for project details and generate customized code.

## Conclusion

**For Your Use Case:**

I recommend **Approach 1 (Git Branch Template)** because:

1. ✅ Simple to maintain
2. ✅ Easy to update across projects
3. ✅ No additional tools required
4. ✅ Full version control
5. ✅ Can cherry-pick improvements

**Next Steps:**

1. Create the template branch now
2. Use it for your next 2-3 projects
3. Refine based on what you keep changing
4. Consider extracting to a shared package if you have 5+ projects

The subscription architecture you have now is very reusable - you've done the hard part! 🎉
