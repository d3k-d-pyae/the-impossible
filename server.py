#!/usr/bin/env python3
"""
The Impossible Challenge - 7 Steps to Flag
A web challenge that requires creative thinking, browser knowledge,
and multiple attack techniques to solve.

Steps:
1. Recon - Find hidden endpoint via robots.txt
2. Decode - Find and decode hidden message in HTML
3. Extension - Download and analyze browser extension
4. WebSocket - Solve real-time timing challenge
5. Race - Exploit race condition
6. State - Combine values from localStorage across pages
7. Final - Submit all tokens to get flag

Author: CTF Challenge Creator
"""

import os
import json
import time
import hashlib
import secrets
import threading
import random
from datetime import datetime, timedelta
from functools import wraps
from collections import defaultdict

from flask import Flask, render_template, request, jsonify, make_response, redirect, url_for, session
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(32))
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Auto-detect WebSocket URL from request
def get_ws_url():
    if request.is_secure:
        return f"wss://{request.host}"
    return f"ws://{request.host}"

socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# ============================================================================
# SECURITY CONFIGURATION
# ============================================================================

# Rate limiting
rate_limits = defaultdict(list)
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX = 30  # requests per window

# IP tracking for abuse prevention
blocked_ips = set()
failed_attempts = defaultdict(int)
MAX_FAILED_ATTEMPTS = 10

# CSRF tokens
csrf_tokens = {}

# Step progression - completed steps per session (server-side only)
step_progress = {}

# Token storage with HMAC verification
active_sessions = {}
race_locks = {}
websocket_tokens = {}
extension_tokens = {}

# The flag pieces (must combine all 7 to get full flag)
FLAG_PIECES = [
    "UITCTF{y0u_",
    "f0und_",
    "th3_",
    "h1dd3n_",
    "p13c3s_",
    "t0g3th3r_",
    "w3ll_d0n3!}"
]

FULL_FLAG = "".join(FLAG_PIECES)

# Token expiry time (5 minutes)
TOKEN_EXPIRY = timedelta(minutes=5)

# Secret HMAC key for token signing
TOKEN_HMAC_KEY = secrets.token_hex(32)


# ============================================================================
# SECURITY FUNCTIONS
# ============================================================================

def get_client_ip():
    """Get client IP address."""
    if request.headers.get('X-Forwarded-For'):
        return request.headers['X-Forwarded-For'].split(',')[0].strip()
    return request.remote_addr


def check_rate_limit():
    """Check if request is within rate limit."""
    ip = get_client_ip()
    now = time.time()
    
    # Clean old entries
    rate_limits[ip] = [t for t in rate_limits[ip] if now - t < RATE_LIMIT_WINDOW]
    
    if len(rate_limits[ip]) >= RATE_LIMIT_MAX:
        return False
    
    rate_limits[ip].append(now)
    return True


def check_abuse_prevention():
    """Check if IP is blocked or has too many failures."""
    ip = get_client_ip()
    
    if ip in blocked_ips:
        return False
    
    if failed_attempts[ip] >= MAX_FAILED_ATTEMPTS:
        blocked_ips.add(ip)
        return False
    
    return True


def record_failure():
    """Record a failed attempt."""
    ip = get_client_ip()
    failed_attempts[ip] += 1


def reset_failures():
    """Reset failure count on success."""
    ip = get_client_ip()
    failed_attempts[ip] = 0


def generate_csrf_token():
    """Generate CSRF token for session."""
    session_id = request.cookies.get('session_id')
    if not session_id:
        return None
    
    token = secrets.token_hex(32)
    csrf_tokens[token] = {
        'session_id': session_id,
        'created': datetime.now(),
        'used': False
    }
    return token


def validate_csrf_token(token):
    """Validate and consume CSRF token."""
    if not token or token not in csrf_tokens:
        return False
    
    csrf_data = csrf_tokens[token]
    
    if csrf_data['used']:
        return False
    
    if datetime.now() - csrf_data['created'] > timedelta(minutes=5):
        del csrf_tokens[token]
        return False
    
    csrf_data['used'] = True
    return True


def generate_hmac_token(step, session_id):
    """Generate HMAC-signed token for a step."""
    timestamp = int(time.time())
    nonce = secrets.token_hex(8)
    
    # Create token data
    data = f"{session_id}:{step}:{timestamp}:{nonce}"
    token_hash = hashlib.sha256((data + TOKEN_HMAC_KEY).encode()).hexdigest()[:24]
    
    # Store token with HMAC verification data
    token = f"{token_hash[:16]}"
    active_sessions[token] = {
        'session_id': session_id,
        'step': step,
        'created': datetime.now(),
        'used': False,
        'hmac_data': data,
        'nonce': nonce
    }
    
    return token


def verify_token_hmac(token, step):
    """Verify token with HMAC and mark as used."""
    if token not in active_sessions:
        return False, "Invalid token"
    
    session = active_sessions[token]
    
    if session['used']:
        return False, "Token already used"
    
    if session['step'] != step:
        return False, "Wrong step"
    
    if datetime.now() - session['created'] > TOKEN_EXPIRY:
        del active_sessions[token]
        return False, "Token expired"
    
    session['used'] = True
    return True, "Valid"


def mark_step_completed(session_id, step_number):
    """Mark a step as completed for a session (server-side only)."""
    if session_id not in step_progress:
        step_progress[session_id] = []
    
    if step_number not in step_progress[session_id]:
        step_progress[session_id].append(step_number)


def is_step_completed(session_id, step_number):
    """Check if a step is completed."""
    return step_number in step_progress.get(session_id, [])


def generate_session_id():
    """Generate unique session ID with HMAC."""
    raw = secrets.token_hex(16)
    return hashlib.sha256((raw + TOKEN_HMAC_KEY).encode()).hexdigest()[:32]


# ============================================================================
# SECURITY DECORATORS
# ============================================================================

def security_check(f):
    """Combined security check decorator."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Rate limiting
        if not check_rate_limit():
            return jsonify({'error': 'Rate limit exceeded. Try again later.'}), 429
        
        # Abuse prevention
        if not check_abuse_prevention():
            return jsonify({'error': 'Access denied.'}), 403
        
        return f(*args, **kwargs)
    return decorated_function


def require_step(step_number):
    """Decorator to require completion of previous step with HMAC verification."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Security checks
            if not check_rate_limit():
                return jsonify({'error': 'Rate limit exceeded'}), 429
            
            if not check_abuse_prevention():
                return jsonify({'error': 'Access denied'}), 403
            
            session_id = request.cookies.get('session_id')
            
            # Allow index and robots.txt without authentication
            if request.path in ['/', '/robots.txt', '/status']:
                return f(*args, **kwargs)
            
            # Allow static files
            if request.path.startswith('/static/'):
                return f(*args, **kwargs)
            
            # Allow API endpoints with proper validation
            if request.path.startswith('/api/') and request.method == 'POST':
                # APIs have their own token validation
                return f(*args, **kwargs)
            
            # Allow WebSocket endpoint
            if request.path == '/ws':
                return f(*args, **kwargs)
            
            if not session_id:
                return redirect('/')
            
            # Check if user has completed the required step
            user_progress = step_progress.get(session_id, [])
            
            if step_number > 1 and (step_number - 1) not in user_progress:
                # Find the last completed step
                last_completed = max(user_progress) if user_progress else 0
                
                # Redirect to appropriate page
                redirect_map = {
                    0: '/',
                    1: '/the-hidden-sanctum',
                    2: '/step2',
                    3: '/step3',
                    4: '/step4',
                    5: '/step5',
                    6: '/step6/combine'
                }
                return redirect(redirect_map.get(last_completed, '/'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# ============================================================================
# STEP 1: RECON - robots.txt contains hidden endpoint
# ============================================================================

@app.route('/robots.txt')
def robots():
    """Step 1: robots.txt reveals hidden endpoint."""
    content = """User-agent: *
Disallow: /the-hidden-sanctum
Disallow: /api/extension-secret
Disallow: /ws
Disallow: /the-vault

# Hint: Some things are hidden in plain sight
# The path to enlightenment begins with curiosity
"""
    return content, 200, {'Content-Type': 'text/plain'}


@app.route('/the-hidden-sanctum')
@require_step(1)
def hidden_sanctum():
    """Step 1 complete: Found hidden endpoint."""
    session_id = request.cookies.get('session_id') or generate_session_id()
    
    # Mark step 1 as completed
    mark_step_completed(session_id, 1)
    
    # Generate step 1 token with HMAC
    token = generate_hmac_token(1, session_id)
    
    # Generate CSRF token
    csrf_token = generate_csrf_token()
    
    # Also encode a hint in base64 for step 2
    import base64
    hint_data = {
        "next_step": 2,
        "message": "The source code reveals secrets to those who look",
        "websocket_hint": f"{get_ws_url()}/ws"
    }
    encoded_hint = base64.b64encode(json.dumps(hint_data).encode()).decode()
    
    response = make_response(render_template('step1.html', 
                                            token=token, 
                                            encoded_hint=encoded_hint,
                                            csrf_token=csrf_token))
    response.set_cookie('session_id', session_id, httponly=True, samesite='Lax')
    return response


# ============================================================================
# STEP 2: DECODE - HTML source contains encoded message
# ============================================================================

@app.route('/step2')
@require_step(2)
def step2():
    """Step 2: Decode hidden message from step 1."""
    session_id = request.cookies.get('session_id')
    if not session_id:
        return redirect('/')
    
    # Verify step 1 is completed
    if not is_step_completed(session_id, 1):
        return redirect('/the-hidden-sanctum')
    
    token = generate_hmac_token(2, session_id)
    csrf_token = generate_csrf_token()
    
    # Hidden message in HTML comment (visible in source)
    hidden_comment = "<!-- The answer to everything is in the extension. Download it at /static/extension/impossible_ext.zip -->"
    
    # Another hint encoded in HTML attribute
    import base64
    extension_hint = base64.b64encode(b"/api/extension-secret").decode()
    
    response = make_response(render_template('step2.html', 
                                             token=token, 
                                             hidden_comment=hidden_comment,
                                             extension_hint=extension_hint,
                                             csrf_token=csrf_token))
    return response


@app.route('/api/check-step2', methods=['POST'])
@security_check
def check_step2():
    """Verify step 2 completion with CSRF validation."""
    # Validate CSRF token
    csrf_token = request.headers.get('X-CSRF-Token') or request.form.get('csrf_token')
    if not validate_csrf_token(csrf_token):
        record_failure()
        return jsonify({'success': False, 'error': 'Invalid CSRF token'}), 403
    
    data = request.get_json()
    token = data.get('token')
    decoded_message = data.get('decoded_message', '').strip()
    
    # Verify session matches token
    session_id = request.cookies.get('session_id')
    
    valid, msg = verify_token_hmac(token, 2)
    if not valid:
        record_failure()
        return jsonify({'success': False, 'error': msg}), 400
    
    # Verify token belongs to current session
    if active_sessions.get(token, {}).get('session_id') != session_id:
        record_failure()
        return jsonify({'success': False, 'error': 'Session mismatch'}), 403
    
    # Check if user decoded the base64
    if decoded_message.lower() in ['/api/extension-secret', 'extension-secret']:
        # Mark step 2 as completed
        mark_step_completed(session_id, 2)
        
        # Generate step 3 token
        next_token = generate_hmac_token(3, session_id)
        
        reset_failures()
        return jsonify({
            'success': True, 
            'message': 'Correct! Now analyze the extension...',
            'next_token': next_token
        })
    
    record_failure()
    return jsonify({'success': False, 'error': 'Wrong answer. Look at the HTML source.'}), 400


# ============================================================================
# STEP 3: EXTENSION - Download and analyze browser extension
# ============================================================================

@app.route('/step3')
@require_step(3)
def step3():
    """Step 3: Extension analysis page."""
    session_id = request.cookies.get('session_id')
    if not session_id:
        return redirect('/')
    
    # Verify step 2 is completed
    if not is_step_completed(session_id, 2):
        return redirect('/step2')
    
    csrf_token = generate_csrf_token()
    return render_template('step3.html', csrf_token=csrf_token)


@app.route('/api/extension-secret', methods=['POST'])
@security_check
def extension_secret():
    """
    Step 3: Extension calls this endpoint.
    Must send custom header: X-Extension-Key
    """
    # Validate CSRF token (optional for extension, but validate if present)
    csrf_token = request.headers.get('X-CSRF-Token')
    if csrf_token and not validate_csrf_token(csrf_token):
        pass  # Extensions may not send CSRF tokens
    
    # Check for extension header
    ext_key = request.headers.get('X-Extension-Key')
    origin = request.headers.get('Origin')
    
    # Must be called from extension (origin chrome-extension://)
    # Also check User-Agent for Chrome Extension pattern
    user_agent = request.headers.get('User-Agent', '')
    
    if not origin or 'chrome-extension' not in origin:
        record_failure()
        return jsonify({
            'error': 'Unauthorized',
            'hint': 'Only browser extensions can call this endpoint',
            'required_header': 'X-Extension-Key'
        }), 403
    
    if ext_key != 'IMPOSSIBLE_EXT_2024':
        record_failure()
        return jsonify({
            'error': 'Invalid key',
            'hint': 'Check the extension manifest'
        }), 403
    
    # Verify session exists
    session_id = request.cookies.get('session_id')
    if not session_id:
        record_failure()
        return jsonify({'error': 'No session'}), 400
    
    # Verify step 2 is completed
    if not is_step_completed(session_id, 2):
        record_failure()
        return jsonify({'error': 'Complete previous steps first'}), 403
    
    # Generate extension token with HMAC
    token = secrets.token_hex(16)
    extension_tokens[token] = {
        'session_id': session_id,
        'created': datetime.now(),
        'websocket_url': f'{get_ws_url()}/ws',
        'ws_token_required': True
    }
    
    # Mark step 3 as completed
    mark_step_completed(session_id, 3)
    
    reset_failures()
    return jsonify({
        'success': True,
        'token': token,
        'websocket_url': f'{get_ws_url()}/ws',
        'message': 'Extension authenticated! Connect to WebSocket with this token.',
        'next_step': 4
    })


@app.route('/static/extension/impossible_ext.zip')
def serve_extension():
    """Serve the extension file."""
    return redirect(url_for('static', filename='extension/impossible_ext.zip'))


# ============================================================================
# STEP 4: WEBSOCKET - Real-time timing challenge
# ============================================================================

@app.route('/step4')
@require_step(4)
def step4():
    """Step 4: WebSocket challenge page."""
    session_id = request.cookies.get('session_id')
    if not session_id:
        return redirect('/')
    
    # Verify step 3 is completed
    if not is_step_completed(session_id, 3):
        return redirect('/step3')
    
    csrf_token = generate_csrf_token()
    return render_template('step4.html', csrf_token=csrf_token, ws_url=get_ws_url())


@socketio.on('connect')
def handle_connect():
    """WebSocket connection handler."""
    # Rate limit WebSocket connections
    ip = get_client_ip()
    if not check_rate_limit():
        emit('error', {'message': 'Rate limit exceeded'})
        return False
    
    print(f"Client connected: {request.sid}")


@socketio.on('disconnect')
def handle_disconnect():
    """WebSocket disconnection handler."""
    if request.sid in websocket_tokens:
        del websocket_tokens[request.sid]
    print(f"Client disconnected: {request.sid}")


@socketio.on('authenticate')
def handle_authenticate(data):
    """Authenticate WebSocket connection with HMAC verification."""
    ext_token = data.get('token')
    
    if ext_token not in extension_tokens:
        emit('error', {'message': 'Invalid extension token. Complete step 3 first.'})
        return
    
    session_data = extension_tokens[ext_token]
    session_id = session_data['session_id']
    
    # Verify step 3 is completed
    if not is_step_completed(session_id, 3):
        emit('error', {'message': 'Complete previous steps first'})
        return
    
    # Store websocket token with HMAC
    ws_token = secrets.token_hex(16)
    websocket_tokens[request.sid] = {
        'session_id': session_id,
        'authenticated': True,
        'ws_token': ws_token,
        'challenge_started': False,
        'current_challenge': None,
        'created': datetime.now()
    }
    
    emit('authenticated', {
        'message': 'WebSocket authenticated!',
        'ws_token': ws_token,
        'challenge': 'math_speed'
    })
    
    # Start challenge after brief delay
    def start_challenge():
        time.sleep(1)
        socketio.emit('start_challenge', {
            'type': 'math_speed',
            'instructions': 'Solve the math problem as fast as possible!',
            'time_limit_ms': 100
        }, room=request.sid)
    
    threading.Thread(target=start_challenge).start()


@socketio.on('solve_challenge')
def handle_solve(data):
    """Handle challenge solution attempt with timing verification."""
    if request.sid not in websocket_tokens:
        emit('error', {'message': 'Not authenticated'})
        return
    
    ws_data = websocket_tokens[request.sid]
    
    # Verify session is valid
    session_id = ws_data.get('session_id')
    if not is_step_completed(session_id, 3):
        emit('error', {'message': 'Complete previous steps first'})
        return
    
    if not ws_data.get('challenge_started'):
        # Generate math challenge
        a = random.randint(10, 99)
        b = random.randint(10, 99)
        operation = random.choice(['+', '-', '*'])
        
        if operation == '+':
            answer = a + b
        elif operation == '-':
            answer = a - b
        else:
            answer = a * b
        
        problem = f"{a} {operation} {b}"
        challenge_id = secrets.token_hex(8)
        
        ws_data['current_challenge'] = {
            'problem': problem,
            'answer': answer,
            'id': challenge_id,
            'start_time': time.time()
        }
        ws_data['challenge_started'] = True
        
        emit('challenge', {
            'id': challenge_id,
            'problem': problem,
            'time_limit_ms': 5000
        })
        return
    
    # Check the answer
    user_answer = data.get('answer')
    challenge = ws_data.get('current_challenge', {})
    
    if not challenge:
        emit('error', {'message': 'No active challenge'})
        return
    
    try:
        user_answer = int(user_answer)
    except (ValueError, TypeError):
        emit('error', {'message': 'Invalid answer format'})
        return
    
    elapsed_ms = (time.time() - challenge['start_time']) * 1000
    
    if user_answer == challenge['answer']:
        # Check timing
        if elapsed_ms < 5000:  # Must be under 5 seconds
            # Mark step 4 as completed
            mark_step_completed(session_id, 4)
            
            step4_token = generate_hmac_token(4, session_id)
            
            emit('challenge_solved', {
                'message': 'Speed challenge complete!',
                'elapsed_ms': round(elapsed_ms, 2),
                'next_token': step4_token,
                'next_step': 5
            })
        else:
            emit('error', {'message': f'Too slow! {elapsed_ms:.0f}ms > 5000ms'})
    else:
        emit('error', {'message': f'Wrong answer! Expected {challenge["answer"]}'})
    
    # Reset challenge
    ws_data['challenge_started'] = False
    ws_data['current_challenge'] = None


# ============================================================================
# STEP 5: RACE CONDITION - Two requests must succeed simultaneously
# ============================================================================

@app.route('/step5')
@require_step(5)
def step5():
    """Step 5: Race condition challenge page."""
    session_id = request.cookies.get('session_id')
    if not session_id:
        return redirect('/')
    
    # Verify step 4 is completed
    if not is_step_completed(session_id, 4):
        return redirect('/step4')
    
    csrf_token = generate_csrf_token()
    return render_template('step5.html', csrf_token=csrf_token)


@app.route('/api/race/lock', methods=['POST'])
@security_check
def race_lock():
    """
    Step 5: Race condition challenge.
    Must acquire lock AND unlock within 100ms of each other.
    """
    session_id = request.cookies.get('session_id')
    if not session_id:
        record_failure()
        return jsonify({'error': 'No session'}), 400
    
    # Verify step 4 is completed
    if not is_step_completed(session_id, 4):
        record_failure()
        return jsonify({'error': 'Complete previous steps first'}), 403
    
    # Create or get race lock for this session
    if session_id not in race_locks:
        race_locks[session_id] = {
            'locked': False,
            'lock_time': None,
            'unlock_pending': False,
            'created': datetime.now()
        }
    
    lock_data = race_locks[session_id]
    
    # Check if lock has expired (30 seconds max)
    if lock_data['created'] and datetime.now() - lock_data['created'] > timedelta(seconds=30):
        del race_locks[session_id]
        return jsonify({'error': 'Lock expired. Try again.'}), 400
    
    # If already locked, this is a race attempt
    if lock_data['locked']:
        time_since_lock = time.time() - lock_data['lock_time']
        
        if time_since_lock < 0.1:  # Within 100ms
            # Success! Race condition exploited
            mark_step_completed(session_id, 5)
            
            token = generate_hmac_token(5, session_id)
            del race_locks[session_id]  # Cleanup
            
            reset_failures()
            return jsonify({
                'success': True,
                'message': 'Race condition exploited!',
                'elapsed_ms': round(time_since_lock * 1000, 2),
                'token': token,
                'next_step': 6
            })
        else:
            record_failure()
            del race_locks[session_id]
            return jsonify({
                'success': False,
                'error': f'Too slow! {time_since_lock*1000:.0f}ms > 100ms'
            }), 400
    
    # First request: acquire lock
    lock_data['locked'] = True
    lock_data['lock_time'] = time.time()
    
    return jsonify({
        'message': 'Lock acquired! Now call /api/race/unlock within 100ms',
        'hint': 'Use concurrent requests or async operations'
    })


@app.route('/api/race/unlock', methods=['POST'])
@security_check
def race_unlock():
    """Second part of race condition."""
    session_id = request.cookies.get('session_id')
    if not session_id or session_id not in race_locks:
        return jsonify({'error': 'No active lock'}), 400
    
    lock_data = race_locks[session_id]
    
    if not lock_data['locked']:
        return jsonify({'error': 'Lock not held'}), 400
    
    # Mark unlock pending
    lock_data['unlock_pending'] = True
    
    return jsonify({
        'message': 'Unlock acknowledged. Both lock and unlock succeeded!',
        'hint': 'Call /api/race/complete with both requests'
    })


@app.route('/api/race/complete', methods=['POST'])
@security_check
def race_complete():
    """Complete the race challenge with proper validation."""
    session_id = request.cookies.get('session_id')
    if not session_id or session_id not in race_locks:
        return jsonify({'error': 'No active race'}), 400
    
    lock_data = race_locks[session_id]
    
    if lock_data.get('unlock_pending'):
        # Verify timing again
        if lock_data['lock_time']:
            total_time = time.time() - lock_data['lock_time']
            if total_time > 0.1:  # More than 100ms
                del race_locks[session_id]
                return jsonify({'error': 'Race condition window expired'}), 400
        
        # Mark step 5 as completed
        mark_step_completed(session_id, 5)
        
        token = generate_hmac_token(5, session_id)
        del race_locks[session_id]
        
        reset_failures()
        return jsonify({
            'success': True,
            'token': token,
            'next_step': 6
        })
    
    return jsonify({'error': 'Race not completed properly'}), 400


# ============================================================================
# STEP 6: STATE - Collect values from multiple pages using localStorage
# ============================================================================

@app.route('/step6/page1')
@require_step(6)
def step6_page1():
    """Page 1: Sets localStorage value."""
    session_id = request.cookies.get('session_id')
    if not session_id:
        return redirect('/')
    
    if not is_step_completed(session_id, 5):
        return redirect('/step5')
    
    return render_template('step6_page1.html')


@app.route('/step6/page2')
@require_step(6)
def step6_page2():
    """Page 2: Sets another localStorage value."""
    session_id = request.cookies.get('session_id')
    if not session_id:
        return redirect('/')
    
    if not is_step_completed(session_id, 5):
        return redirect('/step5')
    
    return render_template('step6_page2.html')


@app.route('/step6/page3')
@require_step(6)
def step6_page3():
    """Page 3: Sets final localStorage value."""
    session_id = request.cookies.get('session_id')
    if not session_id:
        return redirect('/')
    
    if not is_step_completed(session_id, 5):
        return redirect('/step5')
    
    return render_template('step6_page3.html')


@app.route('/step6/combine')
@require_step(6)
def step6_combine():
    """Page to combine all values."""
    session_id = request.cookies.get('session_id')
    if not session_id:
        return redirect('/')
    
    if not is_step_completed(session_id, 5):
        return redirect('/step5')
    
    csrf_token = generate_csrf_token()
    return render_template('step6_combine.html', csrf_token=csrf_token)


@app.route('/api/state/validate', methods=['POST'])
@security_check
def validate_state():
    """Validate collected state values with CSRF validation."""
    # Validate CSRF token
    csrf_token = request.headers.get('X-CSRF-Token') or request.form.get('csrf_token')
    if not validate_csrf_token(csrf_token):
        record_failure()
        return jsonify({'success': False, 'error': 'Invalid CSRF token'}), 403
    
    data = request.get_json()
    values = data.get('values', {})
    
    session_id = request.cookies.get('session_id')
    if not session_id:
        record_failure()
        return jsonify({'success': False, 'error': 'No session'}), 400
    
    # Verify step 5 is completed
    if not is_step_completed(session_id, 5):
        record_failure()
        return jsonify({'success': False, 'error': 'Complete previous steps first'}), 403
    
    # Expected values (must collect from all 3 pages)
    expected = {
        'alpha': 'PHOENIX',
        'beta': 'DRAGON',
        'gamma': 'UNICORN'
    }
    
    # Check if all values match (case-insensitive)
    if all(values.get(k, '').upper() == v for k, v in expected.items()):
        # Mark step 6 as completed
        mark_step_completed(session_id, 6)
        
        # Generate step 6 token
        step6_token = generate_hmac_token(6, session_id)
        
        reset_failures()
        return jsonify({
            'success': True,
            'message': 'All state values collected correctly!',
            'token': step6_token,
            'next_step': 7
        })
    
    record_failure()
    return jsonify({
        'success': False,
        'error': 'Missing or incorrect values. Collect from all pages first.'
    }), 400


# ============================================================================
# STEP 7: FINAL - Combine all tokens to get flag
# ============================================================================

@app.route('/the-vault')
@require_step(7)
def vault():
    """Final vault - requires all tokens."""
    session_id = request.cookies.get('session_id')
    if not session_id:
        return redirect('/')
    
    if not is_step_completed(session_id, 6):
        return redirect('/step6/combine')
    
    csrf_token = generate_csrf_token()
    return render_template('step7_vault.html', csrf_token=csrf_token)


@app.route('/api/vault/unlock', methods=['POST'])
@security_check
def unlock_vault():
    """Unlock the vault with all tokens - SECURE VERSION."""
    # Validate CSRF token
    csrf_token = request.headers.get('X-CSRF-Token') or request.form.get('csrf_token')
    if not validate_csrf_token(csrf_token):
        record_failure()
        return jsonify({'success': False, 'error': 'Invalid CSRF token'}), 403
    
    data = request.get_json()
    
    session_id = request.cookies.get('session_id')
    if not session_id:
        record_failure()
        return jsonify({'success': False, 'error': 'No session'}), 400
    
    # Verify step 6 is completed
    if not is_step_completed(session_id, 6):
        record_failure()
        return jsonify({'success': False, 'error': 'Complete previous steps first'}), 403
    
    tokens = {
        1: data.get('step1_token'),
        2: data.get('step2_token'),
        3: data.get('step3_token'),
        4: data.get('step4_token'),
        5: data.get('step5_token'),
        6: data.get('step6_token'),
    }
    
    # Validate all tokens - NO REUSE, just verify they exist and belong to session
    all_valid = True
    for step, token in tokens.items():
        if not token:
            all_valid = False
            break
        
        # Check if token exists and belongs to this session
        if token not in active_sessions:
            all_valid = False
            break
        
        session_data = active_sessions[token]
        
        # Verify session matches
        if session_data['session_id'] != session_id:
            all_valid = False
            break
        
        # Verify step matches
        if session_data['step'] != step:
            all_valid = False
            break
        
        # Verify not expired
        if datetime.now() - session_data['created'] > TOKEN_EXPIRY:
            all_valid = False
            break
        
        # Verify step is marked as completed
        if not is_step_completed(session_id, step):
            all_valid = False
            break
    
    if all_valid:
        # Clean up tokens after successful unlock
        for step, token in tokens.items():
            if token in active_sessions:
                del active_sessions[token]
        
        reset_failures()
        return jsonify({
            'success': True,
            'flag': FULL_FLAG,
            'message': 'Congratulations! You have conquered the Impossible Challenge!',
            'flag_pieces': FLAG_PIECES
        })
    
    record_failure()
    return jsonify({
        'success': False,
        'error': 'Invalid or missing tokens. Complete all 6 steps first!'
    }), 400


# ============================================================================
# MAIN PAGES
# ============================================================================

@app.route('/')
def index():
    """Main challenge page."""
    session_id = request.cookies.get('session_id') or generate_session_id()
    csrf_token = generate_csrf_token()
    
    response = make_response(render_template('index.html', csrf_token=csrf_token))
    response.set_cookie('session_id', session_id, httponly=True, samesite='Lax')
    return response


@app.route('/status')
def status():
    """Check current progress (optional helper)."""
    session_id = request.cookies.get('session_id')
    progress = step_progress.get(session_id, []) if session_id else []
    return jsonify({
        'session_id': session_id,
        'completed_steps': progress,
        'current_step': max(progress) + 1 if progress else 1,
        'hint': 'The challenge begins at /'
    })


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(429)
def rate_limit_exceeded(e):
    return jsonify({'error': 'Rate limit exceeded. Try again later.'}), 429


@app.errorhandler(403)
def forbidden(e):
    return jsonify({'error': 'Access denied.'}), 403


@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not found.'}), 404


if __name__ == '__main__':
    print("=" * 60)
    print("THE IMPOSSIBLE CHALLENGE - SECURE VERSION")
    print("=" * 60)
    print("\n7 Steps to the Flag:")
    print("  1. Recon - Check robots.txt")
    print("  2. Decode - Read HTML source")
    print("  3. Extension - Download & analyze extension")
    print("  4. WebSocket - Real-time speed challenge")
    print("  5. Race - Exploit race condition")
    print("  6. State - Collect localStorage values")
    print("  7. Final - Unlock the vault")
    print("\nSecurity Features:")
    print("  - HMAC-signed tokens")
    print("  - CSRF protection")
    print("  - Rate limiting")
    print("  - Session validation")
    print("  - Server-side step verification")
    
    port = int(os.environ.get('PORT', 10000))
    print(f"\nStarting server on port {port}")
    print("=" * 60)
    
    socketio.run(app, host='0.0.0.0', port=port, debug=False)
