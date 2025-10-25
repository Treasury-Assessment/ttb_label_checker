# Next Steps - TTB Label Checker Setup

## ✅ Completed Setup

The Firebase project and repository structure have been initialized successfully!

### What's Been Created:

1. **Firebase Configuration**
   - `.firebaserc` - Project settings (ttb-label-checker)
   - `firebase.json` - Hosting and Functions configuration

2. **Frontend (Next.js 14)**
   - Complete Next.js App Router structure
   - TypeScript configuration (strict mode)
   - Tailwind CSS setup
   - Basic landing page
   - Type definitions for API

3. **Backend (Python Cloud Functions)**
   - `functions/main.py` - Cloud Function entry point
   - `functions/pyproject.toml` - Dependencies (uv)
   - Python 3.13 configuration

4. **CI/CD (GitHub Actions)**
   - `.github/workflows/ci.yml` - Continuous integration (testing & linting only)

5. **Documentation**
   - `README.md` - Project overview
   - `SETUP.md` - Detailed setup instructions
   - `CLAUDE.md` - AI assistant context
   - `NEXT_STEPS.md` - This file

---

## 🚀 Immediate Next Steps

### 1. Enable Firebase Services

In the Firebase Console, enable:

- ✅ **App Hosting** - For automatic deployments
- ✅ **Cloud Functions** - For backend API
- ✅ **Cloud Storage** - For image uploads
- ✅ **Upgrade to Blaze Plan** - Required for Cloud Functions (free tier: 2M invocations/month)

### 2. Connect GitHub to Firebase App Hosting

1. Go to [Firebase Console](https://console.firebase.google.com/) → ttb-label-checker
2. Navigate to **App Hosting** in the sidebar
3. Click **Get started**
4. Connect your GitHub repository
5. Configure automatic deployments from the `main` branch

### 3. Enable Google Cloud Vision API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your Firebase project (ttb-label-checker)
3. Navigate to APIs & Services → Library
4. Search for "Cloud Vision API" and enable it

### 4. Install Frontend Dependencies

```bash
cd frontend
npm install
```

### 5. Create Environment Variables

```bash
cd frontend
cp .env.local.example .env.local
# Edit .env.local with your Firebase config values
```

Get Firebase config values from:
- Firebase Console → Project Settings → General → Your apps → Web app

### 6. Test Local Development

**Frontend:**
```bash
cd frontend
npm run dev
```
Visit: http://localhost:3000

**Backend (Emulator):**
```bash
# From project root
firebase emulators:start --only functions
```

### 7. Commit Initial Setup

```bash
git add .
git commit -m "Initial Firebase App Hosting setup with Next.js and Python

- Configure Firebase App Hosting and Cloud Functions
- Set up Next.js 14 with TypeScript and Tailwind (standalone mode)
- Create Python 3.13 Cloud Functions with uv
- Add GitHub Actions for CI (testing & linting)
- Add comprehensive documentation"
```

### 8. Push to GitHub

```bash
# If you haven't set up a remote yet:
git remote add origin <your-github-repo-url>

# Push to GitHub
git push -u origin main
```

**Note**: Once you connect your GitHub repo to Firebase App Hosting, it will automatically deploy on every push to `main`.

---

## 📋 Development Roadmap

Once the initial setup is complete, here's the recommended development order:

### Phase 1: Core OCR Functionality
- [ ] Implement `functions/ocr.py` for Google Cloud Vision integration
- [ ] Add image upload to Firebase Storage
- [ ] Test OCR with sample label images

### Phase 2: Verification Logic
- [ ] Implement `functions/verification.py` for TTB compliance checks
- [ ] Add fuzzy string matching for government warning
- [ ] Implement conditional field validation

### Phase 3: Frontend Components
- [ ] Build `ImageUpload.tsx` component with drag-drop
- [ ] Build `Form.tsx` for product information
- [ ] Build `Results.tsx` for displaying verification results
- [ ] Add image highlighting for matched text

### Phase 4: Integration & Testing
- [ ] Connect frontend to Cloud Functions API
- [ ] Add error handling and loading states
- [ ] Test with real label images from `docs/sample-labels/`
- [ ] Write unit tests for verification logic

### Phase 5: Polish & Deploy
- [ ] Add analytics (optional)
- [ ] Optimize performance
- [ ] Final testing
- [ ] Production deployment

---

## 🔍 Testing the Setup

### Verify Firebase Authentication
```bash
firebase projects:list
# Should show: ttb-label-checker
```

### Verify Frontend Build
```bash
cd frontend
npm run build
# Should complete without errors
```

### Verify Python Environment
```bash
cd functions
uv venv .venv
source .venv/bin/activate
uv pip install -e .
python -c "import firebase_functions; print('OK')"
```

### Test Deployment (Optional)
```bash
# Deploy to Firebase (requires enabled services)
firebase deploy
```

---

## 📚 Key Resources

- **[SETUP.md](./SETUP.md)** - Detailed setup instructions
- **[CLAUDE.md](./CLAUDE.md)** - Development guidelines for AI assistants
- **[docs/prd.md](./docs/prd.md)** - Complete product requirements
- **[docs/regulatoryrequirements.md](./docs/regulatoryrequirements.md)** - TTB compliance rules

---

## 🆘 Troubleshooting

### Firebase Login Issues
```bash
firebase login --reauth
```

### GitHub Actions Deployment Fails
- Verify `FIREBASE_SERVICE_ACCOUNT` secret is added
- Check that Firebase services are enabled
- Ensure Blaze plan is activated

### Frontend Build Errors
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### Python Dependency Issues
```bash
cd functions
rm -rf .venv
uv venv .venv
source .venv/bin/activate
uv pip install -e .
```

---

## ✨ Success Criteria

You'll know the setup is complete when:

- ✅ `npm run dev` shows the landing page at localhost:3000
- ✅ `firebase deploy` successfully deploys to Firebase
- ✅ GitHub Actions workflow runs without errors
- ✅ Cloud Function responds at the deployed URL

---

## 💡 Development Tips

1. **Use uv for Python**: Never use `pip` directly, always use `uv pip`
2. **Type Safety**: Keep TypeScript strict mode enabled
3. **Documentation**: Update PRD when requirements change
4. **Git Commits**: Use conventional commits (feat:, fix:, docs:, etc.)
5. **Testing**: Test with real label images from TTB examples

---

## 🎯 Current Status

```
✅ Firebase project created: ttb-label-checker
✅ Repository structure initialized
✅ Frontend scaffolding complete
✅ Backend structure complete
✅ CI/CD workflows configured
✅ Documentation written

⏳ Pending: Firebase service account configuration
⏳ Pending: Firebase services enablement
⏳ Pending: Environment variables setup
⏳ Pending: Initial deployment

📝 TODO: Core feature implementation
```

---

**Ready to start development!** Follow the steps above to complete the setup and begin building the TTB Label Verification System.

Good luck! 🚀
