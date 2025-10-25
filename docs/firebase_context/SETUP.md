# Firebase and GitHub Actions Setup Guide

This guide walks you through setting up Firebase with automatic deployments via Firebase App Hosting.

## Prerequisites

- ✅ Firebase CLI installed (`firebase --version` to verify)
- ✅ Firebase project created: `ttb-label-checker`
- ✅ Firebase CLI authenticated (`firebase login`)
- ✅ GitHub repository created and connected to Firebase

## Deployment Strategy

This project uses **Firebase App Hosting** for automatic deployments:
- **Frontend**: Deployed via Firebase App Hosting (automatic on push to main)
- **Backend**: Cloud Functions deployed with Firebase CLI or App Hosting
- **CI/CD**: GitHub Actions runs tests and linting only (no deployment)

## Enable Required Firebase Services

In the Firebase Console, enable the following services:

#### Hosting
1. Go to **Build** → **Hosting**
2. Click **Get started**
3. Follow the wizard (the CLI has already been initialized)

#### Cloud Functions
1. Go to **Build** → **Functions**
2. Enable the service
3. Upgrade to **Blaze (Pay as you go)** plan (required for Cloud Functions)
   - Don't worry: Free tier includes 2M invocations/month
   - You'll only pay if you exceed free tier limits

#### Cloud Storage
1. Go to **Build** → **Storage**
2. Click **Get started**
3. Choose production mode (or test mode for development)
4. Select a location (recommend: `us-central1` to match functions)

#### Google Cloud Vision API
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your Firebase project
3. Go to **APIs & Services** → **Library**
4. Search for "Cloud Vision API"
5. Click **Enable**

## Environment Variables

### Frontend Environment Variables

Create `frontend/.env.local`:

```bash
# Firebase Configuration
NEXT_PUBLIC_FIREBASE_API_KEY=your-api-key
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=ttb-label-checker.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=ttb-label-checker
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=ttb-label-checker.appspot.com
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=your-sender-id
NEXT_PUBLIC_FIREBASE_APP_ID=your-app-id

# API Endpoint
NEXT_PUBLIC_API_URL=https://us-central1-ttb-label-checker.cloudfunctions.net
```

To find these values:
1. Firebase Console → Project Settings → General
2. Scroll down to "Your apps"
3. Click "Add app" → Web (if not already created)
4. Copy the configuration values

### Backend Environment Variables

Firebase Functions automatically have access to:
- `GOOGLE_CLOUD_PROJECT` - Your project ID
- `FIREBASE_CONFIG` - Firebase configuration

Additional secrets can be set via:
```bash
firebase functions:secrets:set SECRET_NAME
```

## Local Development

### Frontend Development

```bash
cd frontend
npm install
npm run dev
```

Runs on http://localhost:3000

### Functions Development

```bash
cd functions
uv venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .
```

Run functions locally:
```bash
firebase emulators:start --only functions
```

## Deployment

### Automatic Deployment (Firebase App Hosting)

Firebase App Hosting automatically deploys your application:
- **Push to `main`**: Automatically deploys to production
- **Pull Requests**: Automatically creates preview deployments
- **No manual steps required** - Firebase handles builds and deployments

The backend is integrated into App Hosting and deploys automatically with the frontend.

### Manual Deployment (Optional)

If needed, you can manually deploy functions:

```bash
cd functions
uv pip compile pyproject.toml -o requirements.txt
cd ..
firebase deploy --only functions
```

### GitHub Actions (CI Only)

GitHub Actions runs on every push and pull request to:
1. Lint frontend and backend code
2. Run tests (when implemented)
3. Type check TypeScript
4. Build frontend to verify it compiles
5. Verify requirements.txt is up to date

**Note**: GitHub Actions does NOT deploy - Firebase App Hosting handles all deployments automatically.

## Troubleshooting

### "Error: HTTP Error: 403, Permission denied"

**Solution**: Ensure you've upgraded to the Blaze plan in Firebase Console.

### "Error: Failed to list Firebase projects"

**Solution**: Run `firebase login --reauth`

### "GitHub Actions CI workflow fails"

**Solution**: Check the workflow logs in GitHub Actions tab. Common issues:
- Frontend build errors: Run `npm run build` locally to diagnose
- Python dependency issues: Ensure `requirements.txt` is up to date with `uv pip compile`
- Type errors: Run `npx tsc --noEmit` in frontend directory

### "Module not found" errors in Functions

**Solution**:
```bash
cd functions
uv pip compile pyproject.toml -o requirements.txt
firebase deploy --only functions
```

### Functions deployment fails with Python version error

**Solution**: Ensure `functions/.python-version` contains `3.13` and `firebase.json` specifies `"runtime": "python313"`

## Next Steps

1. ✅ Enable required Firebase services (App Hosting, Functions, Storage)
2. ✅ Connect GitHub repository to Firebase App Hosting
3. ✅ Add environment variables to `frontend/.env.local`
4. ✅ Enable Google Cloud Vision API
5. 🚀 Start building the application!

## Useful Commands

```bash
# Check Firebase login status
firebase login:list

# View Firebase projects
firebase projects:list

# View function logs
firebase functions:log

# View hosting URLs
firebase hosting:sites:list

# Run emulators for local development
firebase emulators:start
```

## Resources

- [Firebase App Hosting Documentation](https://firebase.google.com/docs/app-hosting)
- [Firebase Documentation](https://firebase.google.com/docs)
- [Next.js Documentation](https://nextjs.org/docs)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Google Cloud Vision API](https://cloud.google.com/vision/docs)
