# Project Overview

This is a web app allowing for conversion of bank statements from CSV/PDF/Excel formats to Swift MT940 format.
It uses Claude AI API to infer the details of the CSV/Excel file structure and Claude Vision AI API to parse whole PDF documents.

This is a monorepo containing:
- **Backend**: FastAPI (Python) - deployed to Railway
- **Frontend**: React.js - deployed to Vercel
- **Local Dev**: Docker Compose

## Project Structure
```
/backend    - FastAPI application
/frontend   - React.js application
```