# The Impossible Challenge

A 7-step web challenge that requires creative thinking, browser knowledge, and multiple attack techniques to solve. Designed to be extremely difficult for AI to solve automatically.

## Challenge Overview

**Difficulty:** IMPOSSIBLE  
**Steps:** 7  
**Time Limit:** None (but individual steps have timeouts)  
**Flag Format:** `UITCTF{y0u_f0und_th3_h1dd3n_p13c3s_t0g3th3r_w3ll_d0n3!}`

## Challenge Info

| Field | Value |
|-------|-------|
| **Title** | The Impossible Challenge |
| **Category** | Web / Multi-Technique |
| **Difficulty** | Expert/Impossible |
| **Author** | Nexus Corp |
| **Flag** | `UITCTF{y0u_f0und_th3_h1dd3n_p13c3s_t0g3th3r_w3ll_d0n3!}` |
| **Description** | A corporate website with hidden secrets. Can you uncover all 7 layers of security? |

## Prerequisites

- Python 3.8+
- pip (Python package manager)
- Google Chrome (for extension)

## Installation

1. Navigate to the challenge directory:
   ```bash
   cd ImpossibleChal
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Package the browser extension:
   ```bash
   cd extension
   python package_extension.py
   cd ..
   ```

4. Start the server:
   ```bash
   python server.py
   ```

5. Open your browser and navigate to:
   ```
   http://localhost:9999
   ```

## Deployment to Render

1. Push this code to your GitHub repository
2. Run the deployment script:
   - **Windows:** Double-click `deploy.bat`
   - **Linux/Mac:** Run `bash deploy.sh`
3. Enter your Render service URL when prompted
4. Follow the instructions to create the Web Service on Render

### Render Configuration
- **Name:** impossible-challenge
- **Runtime:** Python
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `gunicorn --worker-class eventlet -w 1 server:app`
- **Environment Variable:** `BASE_URL` = your Render URL (e.g., `https://impossible-challenge.onrender.com`)

## The 7 Steps

### Step 1: Reconnaissance
**Skill:** Information Gathering  
**Difficulty:** Easy

- Find the hidden endpoint by checking standard files
- Clue: "robots.txt tells the truth"
- Hidden endpoint reveals a token and encoded hint

**Solution hints:**
- Check `/robots.txt`
- Look for `Disallow:` entries
- The hidden endpoint is `/the-hidden-sanctum`

---

### Step 2: Decode
**Skill:** Encoding/Decoding  
**Difficulty:** Easy-Medium

- Decode Base64 encoded messages in HTML source
- Multiple encoded values hidden in comments
- Must decode to find the extension endpoint

**Solution hints:**
- View HTML source code (Ctrl+U)
- Look for HTML comments (`<!-- -->`)
- Find and decode Base64 strings
- The decoded path is `/api/extension-secret`

---

### Step 3: Browser Extension
**Skill:** Browser Security, Extension Analysis  
**Difficulty:** Medium

- Download and analyze a Chrome extension
- Extension contains hardcoded API key
- Must understand extension architecture

**Solution hints:**
- Download the extension ZIP from `/static/extension/impossible_ext.zip`
- Extract and examine `manifest.json`
- Look at `background.js` for API configuration
- API Key: `IMPOSSIBLE_EXT_2024`
- Must call `/api/extension-secret` with proper headers

---

### Step 4: WebSocket Challenge
**Skill:** Real-time Communication, WebSocket Protocol  
**Difficulty:** Medium-Hard

- Connect to WebSocket server with extension token
- Solve math challenges under time pressure
- Must respond within 5 seconds

**Solution hints:**
- Connect to WebSocket endpoint
- Send authentication message with token
- Solve math problems as fast as possible
- WebSocket must be used (HTTP won't work)

---

### Step 5: Race Condition
**Skill:** Concurrency, Timing Attacks  
**Difficulty:** Hard

- Exploit a race condition in lock/unlock mechanism
- Must acquire lock AND unlock within 100ms
- Requires concurrent requests

**Solution hints:**
- Use Python threading or async requests
- Send POST to `/api/race/lock` and `/api/race/unlock` simultaneously
- Timing window is 100 milliseconds
- Both requests must complete before timeout

---

### Step 6: State Management
**Skill:** Browser State, localStorage  
**Difficulty:** Medium

- Collect values from 3 different pages
- Values stored in localStorage
- Must combine and validate all values

**Solution hints:**
- Visit `/step6/page1`, `/step6/page2`, `/step6/page3`
- Each page stores a value in localStorage
- Check Developer Tools (F12 → Application → localStorage)
- Values: `alpha=PHOENIX`, `beta=DRAGON`, `gamma=UNICORN`

---

### Step 7: The Vault
**Skill:** Token Assembly, Final Challenge  
**Difficulty:** Hard

- Combine all 6 tokens from previous steps
- Submit to unlock the vault
- Receive the flag

**Solution hints:**
- Collect tokens from each step (stored in localStorage)
- Enter all tokens in the vault form
- Tokens are validated server-side
- All 6 tokens required to unlock

---

## Technical Architecture

### Server Components
- **Flask** - Web framework
- **Flask-SocketIO** - WebSocket support
- **eventlet** - Async networking

### Security Features
- Time-limited tokens (5-minute expiry)
- Single-use tokens
- Session-based state management
- Origin validation for extension
- Race condition with 100ms window

### File Structure
```
ImpossibleChal/
├── server.py              # Main Flask server
├── requirements.txt       # Python dependencies
├── Procfile               # Render deployment
├── render.yaml            # Render configuration
├── deploy.sh              # Linux deployment script
├── deploy.bat             # Windows deployment script
├── README.md              # This file
├── templates/             # HTML templates
│   ├── index.html         # Main page (Nexus Corp)
│   ├── step1.html         # Step 1: Dashboard
│   ├── step2.html         # Step 2: Documentation
│   ├── step3.html         # Step 3: Downloads
│   ├── step4.html         # Step 4: WebSocket
│   ├── step5.html         # Step 5: Race
│   ├── step6_page1.html   # Step 6: Config Alpha
│   ├── step6_page2.html   # Step 6: Config Beta
│   ├── step6_page3.html   # Step 6: Config Gamma
│   ├── step6_combine.html # Step 6: Verify
│   └── step7_vault.html   # Step 7: Vault
├── static/
│   ├── css/
│   │   └── style.css      # Corporate styling
│   └── extension/
│       └── impossible_ext.zip  # Browser extension
└── extension/             # Extension source
    ├── manifest.json      # Extension manifest
    ├── background.js      # Service worker
    ├── popup.html         # Extension popup
    ├── popup.js           # Popup script
    ├── content.js         # Content script
    └── content.css        # Content styles
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Main challenge page |
| `/robots.txt` | GET | Step 1: Contains hidden endpoint |
| `/the-hidden-sanctum` | GET | Step 1: Hidden endpoint |
| `/step2` | GET | Step 2: Decode challenge |
| `/api/check-step2` | POST | Step 2: Validate answer |
| `/api/extension-secret` | POST | Step 3: Extension authentication |
| `/ws` | WebSocket | Step 4: Real-time challenge |
| `/api/race/lock` | POST | Step 5: Race condition (lock) |
| `/api/race/unlock` | POST | Step 5: Race condition (unlock) |
| `/api/race/complete` | POST | Step 5: Race condition (complete) |
| `/step6/page1-3` | GET | Step 6: State collection |
| `/step6/combine` | GET | Step 6: Combine values |
| `/api/state/validate` | POST | Step 6: Validate state |
| `/the-vault` | GET | Step 7: Final vault |
| `/api/vault/unlock` | POST | Step 7: Unlock vault |

## WebSocket Messages

### Client → Server
```json
{
    "type": "authenticate",
    "token": "extension_token_here"
}

{
    "type": "solve_challenge",
    "answer": 42
}
```

### Server → Client
```json
{
    "type": "authenticated",
    "message": "WebSocket authenticated!",
    "ws_token": "token"
}

{
    "type": "challenge",
    "id": "challenge_id",
    "problem": "23 + 45",
    "time_limit_ms": 5000
}

{
    "type": "challenge_solved",
    "message": "Speed challenge complete!",
    "elapsed_ms": 1234.56,
    "next_token": "step4_token"
}
```

## Why AI Struggles

This challenge is specifically designed to be difficult for AI:

1. **Requires real browser interaction** - Extensions, WebSockets, localStorage
2. **Creative exploration needed** - No obvious path, must investigate
3. **Timing-sensitive** - Race conditions and speed challenges
4. **Multi-step context switching** - Each step builds on previous
5. **Domain-specific knowledge** - Browser security, extension APIs
6. **Anti-pattern detection** - Intentionally unusual security patterns

## Troubleshooting

### Extension won't load
- Ensure Developer mode is enabled in Chrome
- Check console for errors
- Verify all extension files are present

### WebSocket connection fails
- Check if server is running
- Ensure no firewall blocking WebSocket
- Try disabling browser extensions

### Race condition fails
- Ensure using concurrent requests (not sequential)
- Check network latency
- Try running locally for fastest response

## License

This is a CTF challenge for educational purposes only.
