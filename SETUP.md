# Firebase and GitHub Actions Setup Guide

This guide walks you through setting up Firebase and configuring GitHub Actions for continuous deployment.

## Prerequisites

- ✅ Firebase CLI installed (`firebase --version` to verify)
- ✅ Firebase project created: `ttb-label-checker`
- ✅ Firebase CLI authenticated (`firebase login`)
- ✅ GitHub repository created

## Firebase Service Account Setup

To enable GitHub Actions to deploy to Firebase, you need to create a service account and add it as a GitHub secret.

### Step 1: Generate Firebase Service Account Key

1. Go to the [Firebase Console](https://console.firebase.google.com/)
2. Select your project: **ttb-label-checker**
3. Click the gear icon ⚙️ → **Project settings**
4. Navigate to the **Service accounts** tab
5. Click **Generate new private key**
6. Save the JSON file securely (DO NOT commit this file!)

### Step 2: Add Service Account to GitHub Secrets

1. Go to your GitHub repository
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Name: `FIREBASE_SERVICE_ACCOUNT`
5. Value: Copy and paste the **entire contents** of the service account JSON file
6. Click **Add secret**

### Step 3: Enable Required Firebase Services

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

### Manual Deployment

Deploy everything:
```bash
firebase deploy
```

Deploy only hosting:
```bash
firebase deploy --only hosting
```

Deploy only functions:
```bash
cd functions
uv pip compile pyproject.toml -o requirements.txt
cd ..
firebase deploy --only functions
```

### Automatic Deployment (GitHub Actions)

Automatic deployment is configured for:
- **Push to `main`**: Deploys to production
- **Pull Requests**: Creates preview deployments

The workflow will:
1. Run tests on both frontend and functions
2. Build the frontend
3. Generate Python requirements
4. Deploy to Firebase

## Troubleshooting

### "Error: HTTP Error: 403, Permission denied"

**Solution**: Ensure you've upgraded to the Blaze plan in Firebase Console.

### "Error: Failed to list Firebase projects"

**Solution**: Run `firebase login --reauth`

### "GitHub Actions: FirebaseServiceAccount not found"

**Solution**: Verify you've added `FIREBASE_SERVICE_ACCOUNT` secret in GitHub repo settings.

### "Module not found" errors in Functions

**Solution**:
```bash
cd functions
uv pip compile pyproject.toml -o requirements.txt
firebase deploy --only functions
```

### Functions deployment fails with Python version error

**Solution**: Ensure `functions/.python-version` contains `3.11` and `firebase.json` specifies `"runtime": "python311"`

## Next Steps

1. ✅ Set up Firebase service account in GitHub secrets
2. ✅ Enable required Firebase services
3. ✅ Add environment variables to `frontend/.env.local`
4. 🚀 Start building the application!

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

- [Firebase Documentation](https://firebase.google.com/docs)
- [Next.js Documentation](https://nextjs.org/docs)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Google Cloud Vision API](https://cloud.google.com/vision/docs)
