# TTB Label Verification System

AI-powered web application to verify alcohol beverage labels against TTB (Alcohol and Tobacco Tax and Trade Bureau) regulatory requirements.

## Overview

This system provides a simplified compliance pre-check for alcohol beverage labels using OCR (Optical Character Recognition) and AI-powered verification. It is **NOT an official TTB certification tool**, but rather a development tool to help identify potential compliance issues before submission.

### Key Features

- 📷 **Image Upload**: Drag-and-drop label image upload
- 🔍 **OCR Extraction**: Automatic text extraction using Google Cloud Vision API
- ✅ **Compliance Verification**: Field-by-field verification against TTB requirements (27 CFR)
- 📊 **Visual Results**: Highlighted results showing compliance status
- 🚀 **Fast Processing**: Optimized for quick feedback

### Supported Product Types

- Distilled Spirits (27 CFR Part 5)
- Wine (27 CFR Part 4)
- Beer & Malt Beverages (27 CFR Part 7)

## Tech Stack

### Frontend
- **Next.js 14** (App Router)
- **TypeScript 5.x**
- **Tailwind CSS**
- **React Hook Form** + Zod validation
- **Framer Motion** for animations

### Backend
- **Firebase Cloud Functions** (Python 3.13)
- **Google Cloud Vision API** for OCR
- **uv** package manager
- **Firebase Storage** for temporary image storage

### Infrastructure
- **Firebase App Hosting** (frontend - auto-deploy on push)
- **Firebase Cloud Functions** (backend)
- **GitHub Actions** (CI - testing and linting only)

## Project Structure

```
ttb-label-checker/
├── docs/
│   ├── prd.md                          # Product Requirements Document
│   ├── instructions.md                 # Original assignment
│   ├── regulatoryrequirements.md       # TTB regulatory checklist
│   └── sample-labels/                  # Test label images
├── frontend/
│   ├── src/
│   │   ├── app/                        # Next.js App Router pages
│   │   ├── components/                 # React components
│   │   ├── lib/                        # Utilities
│   │   └── types/                      # TypeScript interfaces
│   ├── package.json
│   └── tsconfig.json
├── functions/
│   ├── main.py                         # Cloud Function entry point
│   ├── ocr.py                          # OCR processing (TODO)
│   ├── verification.py                 # Verification logic (TODO)
│   ├── pyproject.toml                  # uv dependencies
│   └── requirements.txt                # Generated requirements
├── .github/
│   └── workflows/                      # CI/CD workflows
├── firebase.json                       # Firebase configuration
├── .firebaserc                         # Firebase project settings
├── CLAUDE.md                           # AI assistant context
├── SETUP.md                            # Detailed setup guide
└── README.md                           # This file
```

## Quick Start

### Prerequisites

- Node.js 20+
- Python 3.11+
- [uv](https://github.com/astral-sh/uv) package manager
- [Firebase CLI](https://firebase.google.com/docs/cli)
- Firebase project with Blaze plan

### 1. Clone and Install

```bash
git clone <repository-url>
cd ttb-label-checker

# Install frontend dependencies
cd frontend
npm install

# Install backend dependencies
cd ../functions
uv venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .
```

### 2. Configure Environment Variables

#### Frontend Environment (.env.local)

Copy `.env.local.example` to `.env.local` in the frontend directory:

```bash
cd frontend
cp .env.local.example .env.local
```

Edit `.env.local` with your Firebase configuration:

```bash
# Firebase Configuration (Get these from Firebase Console > Project Settings)
NEXT_PUBLIC_FIREBASE_API_KEY=your-api-key-here
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=ttb-label-checker.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=ttb-label-checker
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=ttb-label-checker.appspot.com
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=your-sender-id
NEXT_PUBLIC_FIREBASE_APP_ID=your-app-id

# API Endpoint (Development: use emulator, Production: use Cloud Functions URL)
NEXT_PUBLIC_API_URL=http://localhost:5001/ttb-label-checker/us-central1
# Production: NEXT_PUBLIC_API_URL=https://us-central1-ttb-label-checker.cloudfunctions.net
```

#### Backend Environment (.env)

Copy `.env.example` to `.env` in the functions directory:

```bash
cd functions
cp .env.example .env
```

Edit `.env` with your configuration:

```bash
# Google Cloud Project
GOOGLE_CLOUD_PROJECT_ID=ttb-label-checker
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json

# Firebase
FIREBASE_STORAGE_BUCKET=ttb-label-checker.appspot.com

# OCR Configuration
OCR_CONFIDENCE_THRESHOLD=0.7
```

**Important Security Notes:**
- ✅ `.env.local.example` and `.env.example` are committed to git (templates only)
- ❌ `.env.local` and `.env` are in `.gitignore` (NEVER commit these)
- ❌ Service account JSON files are in `.gitignore` (NEVER commit these)
- 🔐 For production, use [Firebase Secrets](https://firebase.google.com/docs/functions/config-env#secret-manager) instead of .env files

#### Getting Firebase Credentials

1. **Firebase Configuration** (for frontend):
   - Go to [Firebase Console](https://console.firebase.google.com/)
   - Select your project → Settings (⚙️) → General
   - Scroll to "Your apps" → Web app → Copy configuration values

2. **Service Account** (for backend):
   - Go to [Firebase Console](https://console.firebase.google.com/)
   - Select your project → Settings (⚙️) → Service Accounts
   - Click "Generate new private key"
   - Save as `service-account.json` in functions directory (it's gitignored)
   - Set `GOOGLE_APPLICATION_CREDENTIALS` to the full path

3. **Enable APIs**:
   - Cloud Vision API: [Enable here](https://console.cloud.google.com/apis/library/vision.googleapis.com)
   - Cloud Functions: Enabled automatically with Firebase
   - Cloud Storage: Enabled automatically with Firebase

### 3. Run Locally

**Frontend:**
```bash
cd frontend
npm run dev
```
Visit http://localhost:3000

**Backend (Firebase Emulator):**
```bash
# From project root
firebase emulators:start --only functions
```

### 4. Deploy to Firebase

See [SETUP.md](./SETUP.md) for detailed deployment instructions.

```bash
# Build frontend
cd frontend
npm run build

# Generate requirements.txt
cd ../functions
uv pip compile pyproject.toml -o requirements.txt

# Deploy everything
cd ..
firebase deploy
```

## Development

### Frontend Development

```bash
cd frontend
npm run dev          # Start dev server
npm run build        # Build for production
npm run lint         # Run ESLint
npm run type-check   # TypeScript type checking
```

### Backend Development

```bash
cd functions
uv venv .venv
source .venv/bin/activate

# Install dependencies
uv pip install -e .

# Add new dependency
uv pip install package-name

# Generate requirements.txt for deployment
uv pip compile pyproject.toml -o requirements.txt

# Run tests (when implemented)
pytest
```

### Code Style

- **TypeScript**: Strict mode, PascalCase for components, camelCase for functions
- **Python**: Type hints required, snake_case naming, Google-style docstrings
- **Package Management**: **ALWAYS use uv for Python**, never pip directly

See [CLAUDE.md](./CLAUDE.md) for detailed coding standards.

## Regulatory Compliance

This system verifies labels against TTB requirements including:

- ✅ Brand name
- ✅ Product class/type
- ✅ Alcohol content (ABV)
- ✅ Net contents (standards of fill)
- ✅ Government warning statement (exact text)
- ✅ Country of origin (if imported)
- ✅ Bottler/producer information
- ✅ Age statements (conditional)
- ✅ Sulfite declarations (conditional)

### Important Limitations

The following requirements **CANNOT** be verified due to OCR limitations:

- ❌ Same field of vision (spatial positioning)
- ❌ Visual separation requirements
- ❌ Font styling (bold, italic)
- ❌ Font sizes
- ❌ Color requirements

See [docs/prd.md](./docs/prd.md) Section 16.3 for details.

## CI/CD

### Continuous Integration (GitHub Actions)

GitHub Actions runs on every push and pull request to:

- ✅ **Lint**: ESLint for frontend, Ruff for Python
- ✅ **Test**: Run all unit and integration tests
- ✅ **Type Check**: TypeScript strict mode verification
- ✅ **Build**: Verify frontend builds successfully
- ✅ **Verify**: Ensure requirements.txt is up to date

See [.github/workflows/ci.yml](./.github/workflows/ci.yml) for configuration.

### Automatic Deployment (Firebase App Hosting)

Firebase App Hosting automatically deploys on every push to `main`:

- 🚀 **Production**: Automatic deployment from `main` branch
- 🔍 **Previews**: Automatic preview deployments for pull requests
- ⚡ **Fast**: Built on Cloud Run for serverless scaling
- 🔄 **Integrated**: Frontend and backend deployed together

No manual deployment steps required - Firebase handles everything automatically.

## Testing

### Frontend Tests
```bash
cd frontend
npm test
```

### Backend Tests
```bash
cd functions
source .venv/bin/activate
pytest
```

### Test Labels

Store test label images in `docs/sample-labels/` for manual testing.

## Documentation

- **[SETUP.md](./SETUP.md)** - Detailed Firebase and GitHub Actions setup
- **[CLAUDE.md](./CLAUDE.md)** - Technical context for AI assistants
- **[docs/prd.md](./docs/prd.md)** - Complete product requirements
- **[docs/regulatoryrequirements.md](./docs/regulatoryrequirements.md)** - TTB compliance checklist

## API Documentation

### POST /verify-label

**Request:**
```json
{
  "product_type": "spirits",
  "form_data": {
    "brand_name": "Example Whiskey",
    "product_class": "Bourbon",
    "alcohol_content": 40.0
  },
  "image": "base64_encoded_image"
}
```

**Response:**
```json
{
  "status": "success",
  "overall_match": true,
  "confidence_score": 0.95,
  "results": [
    {
      "field_name": "brand_name",
      "status": "match",
      "expected": "Example Whiskey",
      "found": "Example Whiskey",
      "confidence": 0.98
    }
  ]
}
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## License

MIT License - See LICENSE file for details

## Resources

- [TTB Regulations (27 CFR)](https://www.ecfr.gov/current/title-27)
- [Firebase Documentation](https://firebase.google.com/docs)
- [Next.js Documentation](https://nextjs.org/docs)
- [Google Cloud Vision API](https://cloud.google.com/vision/docs)

## Support

For issues and questions:
- Open an issue in GitHub
- Refer to documentation in `docs/`
- Check [SETUP.md](./SETUP.md) for common troubleshooting

---

**Disclaimer**: This is a development tool for preliminary compliance checking only. It is NOT an official TTB certification service. Always consult with TTB directly for official label approval.
