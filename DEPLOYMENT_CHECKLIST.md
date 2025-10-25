# Firebase Deployment Checklist

Use this checklist to ensure proper Firebase setup and deployment.

## ☐ Pre-Deployment Setup

### Firebase Console Configuration
- [ ] Firebase project created: `ttb-label-checker`
- [ ] Billing upgraded to **Blaze (Pay as you go)** plan
- [ ] **Hosting** enabled
- [ ] **Cloud Functions** enabled  
- [ ] **Cloud Storage** enabled and rules configured
- [ ] **Google Cloud Vision API** enabled in Google Cloud Console

### Service Account & Secrets
- [ ] Firebase service account JSON generated
- [ ] `FIREBASE_SERVICE_ACCOUNT` added to GitHub repository secrets
- [ ] Service account has required permissions

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
- [ ] `FIREBASE_SERVICE_ACCOUNT` secret added to GitHub
- [ ] Branch protection rules configured (optional)

### Initial Commit
- [ ] All files staged (`git add .`)
- [ ] Initial commit created
- [ ] Changes pushed to `main` branch

### CI/CD Verification
- [ ] GitHub Actions workflow triggered on push
- [ ] CI workflow passes (lint + test)
- [ ] Deployment workflow succeeds
- [ ] Firebase hosting URL accessible

## ☐ Firebase Services Verification

### Hosting
- [ ] Site URL accessible: `https://ttb-label-checker.web.app`
- [ ] Landing page displays correctly
- [ ] SSL certificate active

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

### Deploy Everything
```bash
firebase deploy
```

### Deploy Hosting Only
```bash
cd frontend && npm run build && cd .. && firebase deploy --only hosting
```

### Deploy Functions Only
```bash
cd functions && uv pip compile pyproject.toml -o requirements.txt && cd .. && firebase deploy --only functions
```

### View Logs
```bash
firebase functions:log
```

### Run Emulators
```bash
firebase emulators:start
```

---

## Troubleshooting

### Deployment Fails
1. Check Firebase CLI is authenticated: `firebase login:list`
2. Verify project ID in `.firebaserc` matches console
3. Ensure Blaze plan is active
4. Check GitHub Actions logs for errors

### Function Errors
1. View logs: `firebase functions:log`
2. Test locally: `firebase emulators:start --only functions`
3. Verify requirements.txt is up to date
4. Check Python version matches runtime

### CI/CD Fails
1. Verify `FIREBASE_SERVICE_ACCOUNT` secret exists
2. Check workflow file syntax
3. Review GitHub Actions logs
4. Ensure all tests pass locally

---

**Status**: Ready for deployment after completing checklist items.
