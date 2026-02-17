
## Issue
```
Error response from daemon: authentication required - email must be verified before using account
```


## Solutions


**Windows (PowerShell):**
```powershell

# Log back in (follow prompts for username/password)
```

Then try again:
```powershell
```


2. Go to **Settings** (top right menu)
4. Check email verification:
   - Click the verification link
   - Wait 10 seconds

### Option 3: Use Images Already Downloaded

If images are cached locally, force use of local copies:
```powershell
```


2. Go to **Resources**
3. Disable any proxy settings



---

## After Authentication is Fixed

Once you've re-authenticated, restart containers:

```powershell
# Stop current containers

# Start fresh

# Verify all services are healthy
```

---

## If Issues Persist


1. **Settings** → **Troubleshoot**
2. Click **Clean / Purge data** (⚠️ this removes all containers/images)
4. Restart your machine

---

## Verify Connection

After authentication works, test connectivity:

```powershell

# If successful, you'll see:
# Using default tag: latest
# latest: Pulling from library/alpine
# ...
# Status: Downloaded newer image for alpine:latest
```

Then try GRID again:
```powershell
```
