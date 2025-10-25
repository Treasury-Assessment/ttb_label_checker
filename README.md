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
- **Firebase Cloud Functions** (Python 3.11)
- **Google Cloud Vision API** for OCR
- **uv** package manager
- **Firebase Storage** for temporary image storage

### Infrastructure
- **Firebase Hosting** (frontend)
- **Firebase Cloud Functions** (backend)
- **GitHub Actions** (CI/CD)

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

### 2. Configure Environment

Copy `.env.local.example` to `.env.local` in the frontend directory and fill in your Firebase configuration:

```bash
cd frontend
cp .env.local.example .env.local
# Edit .env.local with your Firebase credentials
```

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

GitHub Actions workflows are configured for:

- ✅ **Continuous Integration**: Runs tests on every push and PR
- ✅ **Automatic Deployment**: Deploys to Firebase on push to `main`
- ✅ **Preview Deployments**: Creates preview URLs for pull requests

See [.github/workflows/](./.github/workflows/) for workflow configurations.

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
