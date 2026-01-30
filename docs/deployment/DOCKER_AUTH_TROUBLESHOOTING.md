# Docker Authentication Troubleshooting

## Issue
```
Error response from daemon: authentication required - email must be verified before using account
```

This occurs when Docker Desktop is trying to pull images from Docker Hub but your account authentication is invalid or unverified.

## Solutions

### Option 1: Re-authenticate Docker (Recommended for Quick Fix)

**Windows (PowerShell):**
```powershell
# Log out from Docker Hub
docker logout

# Log back in (follow prompts for username/password)
docker login
```

Then try again:
```powershell
docker-compose up -d
```

### Option 2: Verify Docker Desktop Account

1. **Open Docker Desktop** from system tray or Start menu
2. Go to **Settings** (top right menu)
3. Click **Sign in / Create Docker ID**
4. Check email verification:
   - If unverified, Docker sends a link to your email
   - Click the verification link
   - Wait 2-3 minutes for Docker Hub to sync
5. Restart Docker Desktop completely:
   - Click menu → **Quit Docker Desktop**
   - Wait 10 seconds
   - Reopen Docker Desktop
6. Try again: `docker-compose up -d`

### Option 3: Use Images Already Downloaded

If images are cached locally, force use of local copies:
```powershell
docker-compose up -d --no-pull
```

### Option 4: Offline Mode (Docker Desktop)

1. Open Docker Desktop Settings
2. Go to **Resources**
3. Disable any proxy settings
4. Restart Docker Desktop

### Option 5: Check Docker Hub Status

Visit https://www.docker.com/status to verify Docker Hub is online.

---

## After Authentication is Fixed

Once you've re-authenticated, restart containers:

```powershell
# Stop current containers
docker-compose down

# Start fresh
docker-compose up -d

# Verify all services are healthy
docker-compose ps
```

---

## If Issues Persist

**Reset Docker Desktop completely:**

1. **Settings** → **Troubleshoot**
2. Click **Clean / Purge data** (⚠️ this removes all containers/images)
3. Click **Reset Docker to factory defaults**
4. Restart your machine
5. Open Docker Desktop and authenticate again
6. Try: `docker-compose up -d`

---

## Verify Connection

After authentication works, test connectivity:

```powershell
# Test Docker Hub access
docker pull alpine

# If successful, you'll see:
# Using default tag: latest
# latest: Pulling from library/alpine
# ...
# Status: Downloaded newer image for alpine:latest
```

Then try GRID again:
```powershell
docker-compose up -d
docker-compose ps
```
