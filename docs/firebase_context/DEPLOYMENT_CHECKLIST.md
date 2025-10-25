# Firebase Deployment Checklist

Use this checklist to ensure proper Firebase setup and deployment.

## ☐ Pre-Deployment Setup

### Firebase Console Configuration
- [ ] Firebase project created: `ttb-label-checker`
- [ ] Billing upgraded to **Blaze (Pay as you go)** plan
- [ ] **App Hosting** enabled
- [ ] **Cloud Functions** enabled
- [ ] **Cloud Storage** enabled and rules configured
- [ ] **Google Cloud Vision API** enabled in Google Cloud Console
- [ ] GitHub repository connected to Firebase App Hosting

### Environment Variables
- [ ] `frontend/.env.local` created from `.env.local.example`
- [ ] Firebase config values added to `.env.local`
- [ ] API endpoint URL configured

## ☐ Local Development Setup

### Prerequisites Installed
- [ ] Node.js 20+ installed
- [ ] Python 3.11+ installed
- [ ] uv package manager installed (`pip install uv`)
- [ ] Firebase CLI installed (`npm install -g firebase-tools`)
- [ ] Git configured

### Repository Setup
- [ ] Repository cloned
- [ ] Frontend dependencies installed (`cd frontend && npm install`)
- [ ] Backend venv created (`cd functions && uv venv .venv`)
- [ ] Backend dependencies installed (`uv pip install -e .`)

### Local Testing
- [ ] Frontend runs locally (`npm run dev` at localhost:3000)
- [ ] Frontend builds successfully (`npm run build`)
- [ ] Python imports work (`python -c "import firebase_functions"`)
- [ ] Firebase emulators start successfully

## ☐ GitHub Integration

### Repository Configuration
- [ ] GitHub repository created
- [ ] Remote added (`git remote add origin <url>`)
- [ ] Repository connected to Firebase App Hosting
- [ ] Branch protection rules configured (optional)

### Initial Commit
- [ ] All files staged (`git add .`)
- [ ] Initial commit created
- [ ] Changes pushed to `main` branch

### CI/CD Verification
- [ ] GitHub Actions CI workflow triggered on push
- [ ] CI workflow passes (lint + test + build)
- [ ] Firebase App Hosting automatically deploys
- [ ] App Hosting URL accessible

## ☐ Firebase Services Verification

### App Hosting
- [ ] App deployed successfully via App Hosting
- [ ] Site URL accessible
- [ ] Landing page displays correctly
- [ ] SSL certificate active
- [ ] Preview deployments work for PRs

### Cloud Functions
- [ ] Function deployed successfully
- [ ] Function URL accessible
- [ ] Function responds to test requests
- [ ] CORS configured correctly

### Cloud Storage
- [ ] Bucket created
- [ ] Storage rules configured
- [ ] Test file upload works

### Monitoring
- [ ] Firebase Console shows active services
- [ ] Function logs visible
- [ ] No error alerts

## ☐ Security & Best Practices

### Secrets Management
- [ ] No `.env` files committed to git
- [ ] Service account JSON not in repository
- [ ] API keys in environment variables only
- [ ] `.gitignore` configured properly

### Access Control
- [ ] Firebase security rules configured
- [ ] CORS policy set for Cloud Functions
- [ ] Storage bucket permissions configured

## ☐ Documentation

### Repository Documentation
- [ ] README.md reviewed and accurate
- [ ] SETUP.md contains correct project ID
- [ ] NEXT_STEPS.md followed
- [ ] API documentation updated

### Team Onboarding
- [ ] Setup instructions tested with fresh clone
- [ ] Environment variables documented
- [ ] Deployment process documented

## ☐ Post-Deployment Validation

### Functionality Tests
- [ ] Upload test image to frontend
- [ ] Verify OCR extraction works
- [ ] Check verification results display
- [ ] Test error handling

### Performance
- [ ] Page load time acceptable (<3s)
- [ ] Function cold start time acceptable (<10s)
- [ ] Image upload works for various sizes

### Monitoring & Alerts
- [ ] Firebase Console monitoring set up
- [ ] Error tracking configured
- [ ] Usage quotas reviewed

## ☐ Production Ready

- [ ] All above checklist items completed
- [ ] Test deployment successful
- [ ] Production deployment successful
- [ ] Rollback plan documented
- [ ] Team trained on deployment process

---

## Quick Reference Commands

### Automatic Deployment (Recommended)
```bash
git push origin main
# Firebase App Hosting automatically deploys!
```

### Manual Deploy Functions Only (if needed)
```bash
cd functions && uv pip compile pyproject.toml -o requirements.txt && cd .. && firebase deploy --only functions
```

### Local Development
```bash
# Frontend
cd frontend && npm run dev

# Run all emulators
firebase emulators:start
```

### View Logs
```bash
firebase functions:log
```

### Run CI Checks Locally
```bash
# Frontend
cd frontend
npm run lint
npm run build
npx tsc --noEmit

# Backend
cd functions
source .venv/bin/activate
ruff check .
pytest
```

---

## Troubleshooting

### App Hosting Deployment Fails
1. Check Firebase App Hosting build logs in Firebase Console
2. Verify GitHub repository is properly connected
3. Ensure Blaze plan is active
4. Check that `next.config.js` uses `standalone` output mode

### Function Errors
1. View logs: `firebase functions:log`
2. Test locally: `firebase emulators:start --only functions`
3. Verify requirements.txt is up to date: `uv pip compile pyproject.toml -o requirements.txt`
4. Check Python version is 3.13

### CI Workflow Fails
1. Check workflow file syntax in `.github/workflows/ci.yml`
2. Review GitHub Actions logs for specific errors
3. Ensure all tests pass locally before pushing
4. Verify requirements.txt is committed and up to date

---

**Status**: Ready for deployment after completing checklist items.
