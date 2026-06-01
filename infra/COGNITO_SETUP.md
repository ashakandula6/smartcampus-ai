# AWS Cognito Setup Guide

Follow these steps EXACTLY to set up Cognito for free-tier auth.

## Step 1 — Create User Pool

1. Go to AWS Console → Cognito → "Create user pool"
2. **Step 1 - Configure sign-in experience**
   - Sign-in options: ✅ Email
   - Click Next

3. **Step 2 - Configure security requirements**
   - Password policy: Cognito defaults (fine for now)
   - MFA: No MFA (keep it simple for dev)
   - Click Next

4. **Step 3 - Configure sign-up experience**
   - Self-registration: ✅ Enable
   - Required attributes: ✅ email, ✅ name
   - Click Next

5. **Step 4 - Configure message delivery**
   - Email provider: "Send email with Cognito" (free tier)
   - Click Next

6. **Step 5 - Integrate your app**
   - User pool name: `smartcampus-users`
   - App client name: `smartcampus-web`
   - ❌ DON'T generate a client secret (React apps can't use it)
   - Click Next → Create user pool

## Step 2 — Get your IDs

After creation, note:
- **User Pool ID**: looks like `us-east-1_XXXXXXXXX`
- **Client ID**: Under "App clients" tab, find `smartcampus-web`

## Step 3 — Update your .env files

Backend `/backend/.env`:
```
COGNITO_USER_POOL_ID=us-east-1_XXXXXXXXX
COGNITO_CLIENT_ID=your-client-id
COGNITO_REGION=us-east-1
```

Frontend `/frontend/.env`:
```
VITE_COGNITO_USER_POOL_ID=us-east-1_XXXXXXXXX
VITE_COGNITO_CLIENT_ID=your-client-id
```

## Step 4 — Callback URLs (for hosted UI, optional)

Under App Client → Edit:
- Allowed callback URLs: `http://localhost:3000`, `https://your-vercel-url.vercel.app`
- Allowed sign-out URLs: same

## Free Tier Notes
- Cognito is FREE for up to 50,000 MAUs (Monthly Active Users)
- More than enough for your project
