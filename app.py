#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===========================================================
👑 SAKIL BHAI - ENTERPRISE VIP MANAGEMENT PLATFORM v9.0
===========================================================
🔥 Multi-Role System (Owner · Admin · Reseller · VIP User)
📍 Device Limit Control · Custom Password Length
💰 Wallet · Subscription · Analytics · Branding
⚡ Powered By PRIYANGSHU
===========================================================
"""

from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for, flash, make_response
import datetime
import hashlib
import secrets
import json
import os
import re
import requests
import urllib.parse
import uuid
import time
from functools import wraps
from collections import defaultdict

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
app.permanent_session_lifetime = datetime.timedelta(days=7)

# ===========================================================
# FIREBASE CONFIG
# ===========================================================
FIREBASE_CONFIG = {
    "apiKey": "AIzaSyC74129by4J9ghwX7kCq_xamWVuaBkZvac",
    "authDomain": "sakil-paid-hack-sell-1342007.firebaseapp.com",
    "databaseURL": "https://sakil-paid-hack-sell-1342007-default-rtdb.firebaseio.com",
    "storageBucket": "sakil-paid-hack-sell-1342007.firebasestorage.app",
    "messagingSenderId": "1052436591563",
    "appId": "1:1052436591563:web:e267676720461e7f937c4e",
    "measurementId": "G-LPE7H20EY6"
}

FIREBASE_AVAILABLE = False
db = None

try:
    import pyrebase
    firebase = pyrebase.initialize_app(FIREBASE_CONFIG)
    db = firebase.database()
    try:
        db.child("test").shallow().get()
        FIREBASE_AVAILABLE = True
        print("✅ Firebase Connected")
    except:
        print("⚠️ Firebase connection timeout - using local fallback")
        FIREBASE_AVAILABLE = False
        db = None
except Exception as e:
    print(f"⚠️ Firebase error: {e} - using local fallback")
    FIREBASE_AVAILABLE = False
    db = None

USER_DATA_FILE = "enterprise_data.json"

def load_local_data():
    if os.path.exists(USER_DATA_FILE):
        try:
            with open(USER_DATA_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_local_data(data):
    try:
        with open(USER_DATA_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except:
        return False

def fb_get(path):
    if FIREBASE_AVAILABLE:
        try:
            data = db.child(path).get()
            if data.val():
                return data.val()
            return {}
        except:
            local = load_local_data()
            return local.get(path, {})
    else:
        local = load_local_data()
        return local.get(path, {})

def fb_set(path, data):
    if FIREBASE_AVAILABLE:
        try:
            db.child(path).set(data)
            return True
        except:
            local = load_local_data()
            local[path] = data
            return save_local_data(local)
    else:
        local = load_local_data()
        local[path] = data
        return save_local_data(local)

def fb_push(path, data):
    if FIREBASE_AVAILABLE:
        try:
            new_ref = db.child(path).push(data)
            return new_ref.name
        except:
            local = load_local_data()
            if path not in local:
                local[path] = {}
            key = str(uuid.uuid4())
            local[path][key] = data
            save_local_data(local)
            return key
    else:
        local = load_local_data()
        if path not in local:
            local[path] = {}
        key = str(uuid.uuid4())
        local[path][key] = data
        save_local_data(local)
        return key

def fb_update(path, data):
    if FIREBASE_AVAILABLE:
        try:
            db.child(path).update(data)
            return True
        except:
            local = load_local_data()
            if path not in local:
                local[path] = {}
            local[path].update(data)
            return save_local_data(local)
    else:
        local = load_local_data()
        if path not in local:
            local[path] = {}
        local[path].update(data)
        return save_local_data(local)

# ===========================================================
# DATA LAYER
# ===========================================================

def get_owners():
    owners = fb_get("owners")
    if not owners:
        owners = {
            "sakil2026": {
                "password": hashlib.sha256("sakil2026".encode()).hexdigest(),
                "role": "owner",
                "active": True,
                "created": datetime.datetime.utcnow().isoformat(),
                "full_name": "Sakil Bhai",
                "email": "sakil@premium.com",
                "phone": "+919242428894",
                "wallet": 0,
                "total_income": 0,
                "device_limit": 5,  # default device limit per user
                "min_password_length": 6,
                "max_password_length": 32,
                "custom_branding": {
                    "company_name": "SAKIL BHAI",
                    "logo": "https://i.postimg.cc/1VBJWPhR/IMG-20260724-232723-958.webp",
                    "theme_color": "#00ffff",
                    "powered_by": "PRIYANGSHU"
                },
                "settings": {
                    "session_timeout": 3600,
                    "allow_reseller_branding": True,
                    "maintenance_mode": False,
                    "default_device_limit": 5,
                    "default_password_length": 8
                }
            }
        }
        fb_set("owners", owners)
    return owners

def get_admins():
    return fb_get("admins") or {}

def get_resellers():
    return fb_get("resellers") or {}

def get_users():
    return fb_get("users") or {}

def get_subscriptions():
    return fb_get("subscriptions") or {}

def get_wallet_transactions():
    return fb_get("wallet_transactions") or {}

def get_login_history():
    return fb_get("login_history") or {}

def get_device_logs():
    return fb_get("device_logs") or {}

def get_settings():
    settings = fb_get("system_settings")
    if not settings:
        settings = {
            "expiry_utc": "2026-12-31T23:59:59+00:00",
            "redirect_url": "https://wa.me/919242428894",
            "default_device_limit": 5,
            "min_password_length": 6,
            "max_password_length": 32
        }
        fb_set("system_settings", settings)
    return settings

def save_settings(settings):
    return fb_set("system_settings", settings)

def get_remaining_seconds():
    settings = get_settings()
    expiry_str = settings.get("expiry_utc", "")
    if not expiry_str:
        return 0
    try:
        if expiry_str.endswith('+00:00') or expiry_str.endswith('Z'):
            expiry_str = expiry_str.replace('Z', '+00:00')
            if '+' in expiry_str:
                expiry_str = expiry_str.split('+')[0]
        expiry = datetime.datetime.fromisoformat(expiry_str)
        now = datetime.datetime.utcnow()
        diff = expiry - now
        return max(0, int(diff.total_seconds()))
    except:
        return 0

def is_expired():
    return get_remaining_seconds() <= 0

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, hashed):
    return hash_password(password) == hashed

def generate_session_id():
    return secrets.token_hex(32)

def get_device_count(username, role="user"):
    """Get current device count for a user"""
    logs = get_device_logs()
    count = 0
    for key, entry in logs.items():
        if entry.get("username") == username and entry.get("role") == role and entry.get("active", False):
            # Check if session is still valid (not expired)
            if entry.get("expires_at"):
                try:
                    expires = datetime.datetime.fromisoformat(entry["expires_at"])
                    if expires > datetime.datetime.utcnow():
                        count += 1
                except:
                    pass
            else:
                count += 1
    return count

def get_device_limit(username, role="user"):
    """Get device limit for a user based on role and owner settings"""
    owners = get_owners()
    owner = owners.get("sakil2026", {})
    default_limit = owner.get("settings", {}).get("default_device_limit", 5)
    
    if role == "owner":
        return 999999
    elif role == "admin":
        # Admins can have higher limit
        admins = get_admins()
        admin_data = admins.get(username, {})
        return admin_data.get("device_limit", default_limit * 2)
    elif role == "reseller":
        resellers = get_resellers()
        reseller_data = resellers.get(username, {})
        return reseller_data.get("device_limit", default_limit * 3)
    else:  # user
        users = get_users()
        user_data = users.get(username, {})
        return user_data.get("device_limit", default_limit)

def check_device_limit(username, role="user"):
    """Check if user can add a new device"""
    current = get_device_count(username, role)
    limit = get_device_limit(username, role)
    return current < limit

def register_device(username, role, device_id=None, ip=None, user_agent=None):
    """Register a new device for a user"""
    if not device_id:
        device_id = str(uuid.uuid4())
    
    logs = get_device_logs()
    
    # Check if device already exists for this user
    for key, entry in logs.items():
        if entry.get("username") == username and entry.get("device_id") == device_id:
            # Update existing device
            logs[key]["last_active"] = datetime.datetime.utcnow().isoformat()
            logs[key]["ip"] = ip or logs[key].get("ip")
            logs[key]["user_agent"] = user_agent or logs[key].get("user_agent")
            logs[key]["expires_at"] = (datetime.datetime.utcnow() + datetime.timedelta(days=7)).isoformat()
            fb_set("device_logs", logs)
            return key
    
    # Check device limit
    if not check_device_limit(username, role):
        return None
    
    # Create new device entry
    entry = {
        "username": username,
        "role": role,
        "device_id": device_id,
        "ip": ip or "",
        "user_agent": user_agent or "",
        "active": True,
        "created_at": datetime.datetime.utcnow().isoformat(),
        "last_active": datetime.datetime.utcnow().isoformat(),
        "expires_at": (datetime.datetime.utcnow() + datetime.timedelta(days=7)).isoformat()
    }
    
    key = fb_push("device_logs", entry)
    return key

def logout_device(username, device_id):
    """Deactivate a specific device"""
    logs = get_device_logs()
    for key, entry in logs.items():
        if entry.get("username") == username and entry.get("device_id") == device_id:
            logs[key]["active"] = False
            logs[key]["expires_at"] = datetime.datetime.utcnow().isoformat()
            fb_set("device_logs", logs)
            return True
    return False

def logout_all_devices(username):
    """Deactivate all devices for a user"""
    logs = get_device_logs()
    count = 0
    for key, entry in logs.items():
        if entry.get("username") == username:
            logs[key]["active"] = False
            logs[key]["expires_at"] = datetime.datetime.utcnow().isoformat()
            count += 1
    if count > 0:
        fb_set("device_logs", logs)
    return count

# ===========================================================
# ROLE DECORATORS
# ===========================================================

def owner_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get("role") == "owner" and session.get("authenticated"):
            return f(*args, **kwargs)
        return redirect(url_for('owner_login'))
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get("role") in ["owner", "admin"] and session.get("authenticated"):
            return f(*args, **kwargs)
        return redirect(url_for('admin_login'))
    return decorated

def reseller_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get("role") in ["owner", "admin", "reseller"] and session.get("authenticated"):
            return f(*args, **kwargs)
        return redirect(url_for('reseller_login'))
    return decorated

def user_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get("authenticated"):
            if is_expired():
                session.clear()
                return redirect('https://wa.me/919242428894')
            return f(*args, **kwargs)
        return redirect(url_for('login_page'))
    return decorated

def check_device_auth(f):
    """Check if device is authorized (device limit check)"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("authenticated"):
            return redirect(url_for('login_page'))
        
        username = session.get("username")
        role = session.get("role")
        device_id = session.get("device_id")
        
        if not device_id:
            # New device, register it
            device_id = str(uuid.uuid4())
            session["device_id"] = device_id
            
            if not check_device_limit(username, role):
                flash(f"Device limit exceeded! Max {get_device_limit(username, role)} devices allowed.", "error")
                session.clear()
                return redirect(url_for('login_page'))
            
            register_device(username, role, device_id, 
                           request.remote_addr, request.headers.get('User-Agent'))
        else:
            # Check if device is still valid
            logs = get_device_logs()
            valid = False
            for key, entry in logs.items():
                if entry.get("username") == username and entry.get("device_id") == device_id:
                    if entry.get("active", False):
                        expires = entry.get("expires_at")
                        if expires:
                            try:
                                exp_dt = datetime.datetime.fromisoformat(expires)
                                if exp_dt > datetime.datetime.utcnow():
                                    valid = True
                                    # Update last active
                                    logs[key]["last_active"] = datetime.datetime.utcnow().isoformat()
                                    fb_set("device_logs", logs)
                            except:
                                valid = True
                        else:
                            valid = True
                    break
            
            if not valid:
                # Device expired or deactivated
                session.clear()
                flash("Device session expired or deactivated. Please login again.", "error")
                return redirect(url_for('login_page'))
        
        return f(*args, **kwargs)
    return decorated

# ===========================================================
# LOGIN PAGES
# ===========================================================

# ---- OWNER LOGIN ----
OWNER_LOGIN_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>👑 OWNER · SAKIL BHAI</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;800;900&family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', sans-serif;
            background: #06060a;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            overflow: hidden;
        }
        .bg {
            position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            z-index: 0; overflow: hidden;
        }
        .bg .orb {
            position: absolute; border-radius: 50%; filter: blur(100px);
            animation: float 20s ease-in-out infinite;
        }
        .bg .orb:nth-child(1) { width: 400px; height: 400px; background: rgba(255,215,0,0.03); top: -100px; left: -100px; }
        .bg .orb:nth-child(2) { width: 500px; height: 500px; background: rgba(255,215,0,0.015); bottom: -150px; right: -150px; animation-delay: -5s; }
        @keyframes float { 0%,100%{transform:translate(0,0) scale(1)} 33%{transform:translate(30px,-30px) scale(1.1)} 66%{transform:translate(-20px,20px) scale(0.9)} }
        .box {
            position: relative; z-index: 1;
            background: rgba(6,6,12,0.95);
            border: 1px solid rgba(255,215,0,0.15);
            border-radius: 24px; padding: 40px 36px;
            max-width: 400px; width: 92%;
            backdrop-filter: blur(30px);
            box-shadow: 0 0 80px rgba(255,215,0,0.03);
        }
        .box .crown { text-align: center; font-size: 40px; color: #ffd700; opacity: 0.4; margin-bottom: 4px; }
        .box h1 { font-family: 'Orbitron', monospace; font-size: 22px; font-weight: 800; color: #fff; text-align: center; letter-spacing: 3px; }
        .box h1 .hl { color: #ffd700; }
        .box .sub { text-align: center; font-size: 8px; font-family: 'Orbitron', monospace; color: #ffd700; letter-spacing: 5px; text-transform: uppercase; margin-bottom: 20px; }
        .form-group { margin-bottom: 14px; }
        .form-group label { display: block; font-size: 8px; font-family: 'Orbitron', monospace; color: #ffd700; letter-spacing: 3px; margin-bottom: 4px; }
        .form-group label i { color: #ffd700; }
        .input-wrap {
            display: flex; align-items: center;
            background: rgba(0,0,0,0.2);
            border: 1px solid rgba(255,215,0,0.05);
            border-radius: 12px; transition: all 0.3s ease;
            overflow: hidden;
        }
        .input-wrap:focus-within { border-color: rgba(255,215,0,0.2); }
        .input-wrap .pre { padding: 10px 0 10px 14px; color: #ffd700; font-size: 13px; width: 36px; text-align: center; }
        .input-wrap input {
            flex: 1; padding: 10px 14px;
            background: transparent; border: none;
            color: #fff; font-size: 15px; outline: none;
            font-family: 'Inter', sans-serif;
        }
        .input-wrap input::placeholder { color: #ffd700; font-size: 13px; opacity: 0.3; }
        .btn {
            width: 100%; padding: 14px;
            background: rgba(255,215,0,0.05);
            border: 1px solid rgba(255,215,0,0.1);
            border-radius: 12px;
            color: #ffd700;
            font-family: 'Orbitron', monospace;
            font-size: 13px; letter-spacing: 4px;
            cursor: pointer; transition: all 0.3s ease;
            text-transform: uppercase;
            display: flex; justify-content: center; align-items: center; gap: 12px;
        }
        .btn:hover { border-color: rgba(255,215,0,0.3); color: #fff; }
        .error { color: #ff3355; font-size: 11px; font-family: 'Orbitron', monospace; text-align: center; padding: 4px 0; display: none; letter-spacing: 1px; }
        .error.show { display: block; animation: shake 0.4s ease; }
        @keyframes shake { 0%,100%{transform:translateX(0)} 25%{transform:translateX(-4px)} 75%{transform:translateX(4px)} }
        .footer { text-align: center; font-size: 6px; color: #ffd700; letter-spacing: 3px; margin-top: 14px; font-family: 'Orbitron', monospace; opacity: 0.3; }
    </style>
</head>
<body>
    <div class="bg"><div class="orb"></div><div class="orb"></div></div>
    <div class="box">
        <div class="crown"><i class="fas fa-crown"></i></div>
        <h1><span class="hl">OWNER</span> PANEL</h1>
        <div class="sub">enterprise · control</div>
        <form method="POST">
            <div class="form-group">
                <label><i class="fas fa-user"></i> username</label>
                <div class="input-wrap">
                    <div class="pre"><i class="fas fa-user"></i></div>
                    <input type="text" name="username" placeholder="owner username" required autofocus>
                </div>
            </div>
            <div class="form-group">
                <label><i class="fas fa-key"></i> password</label>
                <div class="input-wrap">
                    <div class="pre"><i class="fas fa-lock"></i></div>
                    <input type="password" name="password" placeholder="owner password" required>
                </div>
            </div>
            <div class="error" id="error">{{ error }}</div>
            <button type="submit" class="btn"><i class="fas fa-unlock-alt"></i> unlock</button>
        </form>
        <div class="footer">⚡ SAKIL BHAI · ENTERPRISE ⚡</div>
    </div>
    <script>
        document.querySelector('input[name="username"]').focus();
        {% if error %}document.getElementById('error').classList.add('show');{% endif %}
    </script>
</body>
</html>
'''

# ---- ADMIN LOGIN ----
ADMIN_LOGIN_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🛡 ADMIN · SAKIL BHAI</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;800;900&family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', sans-serif;
            background: #06060a;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            overflow: hidden;
        }
        .bg {
            position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            z-index: 0; overflow: hidden;
        }
        .bg .orb {
            position: absolute; border-radius: 50%; filter: blur(100px);
            animation: float 20s ease-in-out infinite;
        }
        .bg .orb:nth-child(1) { width: 400px; height: 400px; background: rgba(0,255,255,0.02); top: -100px; left: -100px; }
        .bg .orb:nth-child(2) { width: 500px; height: 500px; background: rgba(0,255,255,0.01); bottom: -150px; right: -150px; animation-delay: -5s; }
        @keyframes float { 0%,100%{transform:translate(0,0) scale(1)} 33%{transform:translate(30px,-30px) scale(1.1)} 66%{transform:translate(-20px,20px) scale(0.9)} }
        .box {
            position: relative; z-index: 1;
            background: rgba(6,6,12,0.95);
            border: 1px solid rgba(0,255,255,0.1);
            border-radius: 24px; padding: 36px 32px;
            max-width: 380px; width: 92%;
            backdrop-filter: blur(30px);
        }
        .box .icon { text-align: center; font-size: 34px; color: #00ffff; opacity: 0.4; margin-bottom: 4px; }
        .box h1 { font-family: 'Orbitron', monospace; font-size: 20px; font-weight: 700; color: #fff; text-align: center; letter-spacing: 2px; }
        .box h1 .hl { color: #00ffff; }
        .box .sub { text-align: center; font-size: 8px; font-family: 'Orbitron', monospace; color: #88ddff; letter-spacing: 4px; text-transform: uppercase; margin-bottom: 18px; }
        .form-group { margin-bottom: 12px; }
        .form-group label { display: block; font-size: 8px; font-family: 'Orbitron', monospace; color: #88ddff; letter-spacing: 2px; margin-bottom: 3px; }
        .input-wrap {
            display: flex; align-items: center;
            background: rgba(0,0,0,0.2);
            border: 1px solid rgba(0,255,255,0.05);
            border-radius: 10px; transition: all 0.3s ease;
            overflow: hidden;
        }
        .input-wrap:focus-within { border-color: rgba(0,255,255,0.15); }
        .input-wrap .pre { padding: 8px 0 8px 12px; color: #88ddff; font-size: 12px; width: 32px; text-align: center; }
        .input-wrap input {
            flex: 1; padding: 8px 12px;
            background: transparent; border: none;
            color: #fff; font-size: 14px; outline: none;
            font-family: 'Inter', sans-serif;
        }
        .input-wrap input::placeholder { color: #88ddff; font-size: 12px; opacity: 0.3; }
        .btn {
            width: 100%; padding: 10px;
            background: rgba(0,255,255,0.05);
            border: 1px solid rgba(0,255,255,0.05);
            border-radius: 10px;
            color: #88ddff;
            font-family: 'Orbitron', monospace;
            font-size: 11px; letter-spacing: 3px;
            cursor: pointer; transition: all 0.3s ease;
            text-transform: uppercase;
            display: flex; justify-content: center; align-items: center; gap: 8px;
        }
        .btn:hover { border-color: rgba(0,255,255,0.2); color: #00ffff; }
        .error { color: #ff3355; font-size: 10px; font-family: 'Orbitron', monospace; text-align: center; padding: 4px 0; display: none; letter-spacing: 1px; }
        .error.show { display: block; animation: shake 0.4s ease; }
        @keyframes shake { 0%,100%{transform:translateX(0)} 25%{transform:translateX(-4px)} 75%{transform:translateX(4px)} }
        .footer { text-align: center; font-size: 6px; color: #88ddff; letter-spacing: 3px; margin-top: 12px; font-family: 'Orbitron', monospace; opacity: 0.3; }
    </style>
</head>
<body>
    <div class="bg"><div class="orb"></div><div class="orb"></div></div>
    <div class="box">
        <div class="icon"><i class="fas fa-shield-halved"></i></div>
        <h1><span class="hl">ADMIN</span> PANEL</h1>
        <div class="sub">premium · management</div>
        <form method="POST">
            <div class="form-group">
                <label><i class="fas fa-user"></i> username</label>
                <div class="input-wrap">
                    <div class="pre"><i class="fas fa-user"></i></div>
                    <input type="text" name="username" placeholder="admin username" required autofocus>
                </div>
            </div>
            <div class="form-group">
                <label><i class="fas fa-key"></i> password</label>
                <div class="input-wrap">
                    <div class="pre"><i class="fas fa-lock"></i></div>
                    <input type="password" name="password" placeholder="admin password" required>
                </div>
            </div>
            <div class="error" id="error">{{ error }}</div>
            <button type="submit" class="btn"><i class="fas fa-unlock-alt"></i> unlock</button>
        </form>
        <div class="footer">⚡ SAKIL BHAI · ENTERPRISE ⚡</div>
    </div>
    <script>
        document.querySelector('input[name="username"]').focus();
        {% if error %}document.getElementById('error').classList.add('show');{% endif %}
    </script>
</body>
</html>
'''

# ---- RESELLER LOGIN ----
RESELLER_LOGIN_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>👑 RESELLER · SAKIL BHAI</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;800;900&family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', sans-serif;
            background: #06060a;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            overflow: hidden;
        }
        .bg {
            position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            z-index: 0; overflow: hidden;
        }
        .bg .orb {
            position: absolute; border-radius: 50%; filter: blur(100px);
            animation: float 20s ease-in-out infinite;
        }
        .bg .orb:nth-child(1) { width: 400px; height: 400px; background: rgba(0,255,102,0.02); top: -100px; left: -100px; }
        .bg .orb:nth-child(2) { width: 500px; height: 500px; background: rgba(0,255,102,0.01); bottom: -150px; right: -150px; animation-delay: -5s; }
        @keyframes float { 0%,100%{transform:translate(0,0) scale(1)} 33%{transform:translate(30px,-30px) scale(1.1)} 66%{transform:translate(-20px,20px) scale(0.9)} }
        .box {
            position: relative; z-index: 1;
            background: rgba(6,6,12,0.95);
            border: 1px solid rgba(0,255,102,0.1);
            border-radius: 24px; padding: 36px 32px;
            max-width: 380px; width: 92%;
            backdrop-filter: blur(30px);
        }
        .box .icon { text-align: center; font-size: 34px; color: #00ff66; opacity: 0.4; margin-bottom: 4px; }
        .box h1 { font-family: 'Orbitron', monospace; font-size: 20px; font-weight: 700; color: #fff; text-align: center; letter-spacing: 2px; }
        .box h1 .hl { color: #00ff66; }
        .box .sub { text-align: center; font-size: 8px; font-family: 'Orbitron', monospace; color: #88ddff; letter-spacing: 4px; text-transform: uppercase; margin-bottom: 18px; }
        .form-group { margin-bottom: 12px; }
        .form-group label { display: block; font-size: 8px; font-family: 'Orbitron', monospace; color: #88ddff; letter-spacing: 2px; margin-bottom: 3px; }
        .input-wrap {
            display: flex; align-items: center;
            background: rgba(0,0,0,0.2);
            border: 1px solid rgba(0,255,102,0.05);
            border-radius: 10px; transition: all 0.3s ease;
            overflow: hidden;
        }
        .input-wrap:focus-within { border-color: rgba(0,255,102,0.15); }
        .input-wrap .pre { padding: 8px 0 8px 12px; color: #88ddff; font-size: 12px; width: 32px; text-align: center; }
        .input-wrap input {
            flex: 1; padding: 8px 12px;
            background: transparent; border: none;
            color: #fff; font-size: 14px; outline: none;
            font-family: 'Inter', sans-serif;
        }
        .input-wrap input::placeholder { color: #88ddff; font-size: 12px; opacity: 0.3; }
        .btn {
            width: 100%; padding: 10px;
            background: rgba(0,255,102,0.05);
            border: 1px solid rgba(0,255,102,0.05);
            border-radius: 10px;
            color: #88ddff;
            font-family: 'Orbitron', monospace;
            font-size: 11px; letter-spacing: 3px;
            cursor: pointer; transition: all 0.3s ease;
            text-transform: uppercase;
            display: flex; justify-content: center; align-items: center; gap: 8px;
        }
        .btn:hover { border-color: rgba(0,255,102,0.2); color: #00ff66; }
        .error { color: #ff3355; font-size: 10px; font-family: 'Orbitron', monospace; text-align: center; padding: 4px 0; display: none; letter-spacing: 1px; }
        .error.show { display: block; animation: shake 0.4s ease; }
        @keyframes shake { 0%,100%{transform:translateX(0)} 25%{transform:translateX(-4px)} 75%{transform:translateX(4px)} }
        .footer { text-align: center; font-size: 6px; color: #88ddff; letter-spacing: 3px; margin-top: 12px; font-family: 'Orbitron', monospace; opacity: 0.3; }
    </style>
</head>
<body>
    <div class="bg"><div class="orb"></div><div class="orb"></div></div>
    <div class="box">
        <div class="icon"><i class="fas fa-store"></i></div>
        <h1><span class="hl">RESELLER</span> PANEL</h1>
        <div class="sub">premium · reseller</div>
        <form method="POST">
            <div class="form-group">
                <label><i class="fas fa-user"></i> username</label>
                <div class="input-wrap">
                    <div class="pre"><i class="fas fa-user"></i></div>
                    <input type="text" name="username" placeholder="reseller username" required autofocus>
                </div>
            </div>
            <div class="form-group">
                <label><i class="fas fa-key"></i> password</label>
                <div class="input-wrap">
                    <div class="pre"><i class="fas fa-lock"></i></div>
                    <input type="password" name="password" placeholder="reseller password" required>
                </div>
            </div>
            <div class="error" id="error">{{ error }}</div>
            <button type="submit" class="btn"><i class="fas fa-unlock-alt"></i> unlock</button>
        </form>
        <div class="footer">⚡ SAKIL BHAI · ENTERPRISE ⚡</div>
    </div>
    <script>
        document.querySelector('input[name="username"]').focus();
        {% if error %}document.getElementById('error').classList.add('show');{% endif %}
    </script>
</body>
</html>
'''

# ---- USER LOGIN ----
USER_LOGIN_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>👤 VIP · SAKIL BHAI</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;800;900&family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', sans-serif;
            background: #06060a;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            overflow: hidden;
        }
        .bg {
            position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            z-index: 0; overflow: hidden;
        }
        .bg .orb {
            position: absolute; border-radius: 50%; filter: blur(100px);
            animation: float 20s ease-in-out infinite;
        }
        .bg .orb:nth-child(1) { width: 400px; height: 400px; background: rgba(255,255,255,0.02); top: -100px; left: -100px; }
        .bg .orb:nth-child(2) { width: 500px; height: 500px; background: rgba(255,255,255,0.01); bottom: -150px; right: -150px; animation-delay: -5s; }
        @keyframes float { 0%,100%{transform:translate(0,0) scale(1)} 33%{transform:translate(30px,-30px) scale(1.1)} 66%{transform:translate(-20px,20px) scale(0.9)} }
        .box {
            position: relative; z-index: 1;
            background: rgba(6,6,12,0.95);
            border: 1px solid rgba(255,255,255,0.05);
            border-radius: 24px; padding: 36px 32px;
            max-width: 380px; width: 92%;
            backdrop-filter: blur(30px);
        }
        .box .icon { text-align: center; font-size: 34px; color: #88ddff; opacity: 0.4; margin-bottom: 4px; }
        .box h1 { font-family: 'Orbitron', monospace; font-size: 20px; font-weight: 700; color: #fff; text-align: center; letter-spacing: 2px; }
        .box h1 .hl { color: #00ffff; }
        .box .sub { text-align: center; font-size: 8px; font-family: 'Orbitron', monospace; color: #88ddff; letter-spacing: 4px; text-transform: uppercase; margin-bottom: 18px; }
        .form-group { margin-bottom: 12px; }
        .form-group label { display: block; font-size: 8px; font-family: 'Orbitron', monospace; color: #88ddff; letter-spacing: 2px; margin-bottom: 3px; }
        .input-wrap {
            display: flex; align-items: center;
            background: rgba(0,0,0,0.2);
            border: 1px solid rgba(255,255,255,0.05);
            border-radius: 10px; transition: all 0.3s ease;
            overflow: hidden;
        }
        .input-wrap:focus-within { border-color: rgba(255,255,255,0.1); }
        .input-wrap .pre { padding: 8px 0 8px 12px; color: #88ddff; font-size: 12px; width: 32px; text-align: center; }
        .input-wrap input {
            flex: 1; padding: 8px 12px;
            background: transparent; border: none;
            color: #fff; font-size: 14px; outline: none;
            font-family: 'Inter', sans-serif;
        }
        .input-wrap input::placeholder { color: #88ddff; font-size: 12px; opacity: 0.3; }
        .btn {
            width: 100%; padding: 10px;
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.05);
            border-radius: 10px;
            color: #88ddff;
            font-family: 'Orbitron', monospace;
            font-size: 11px; letter-spacing: 3px;
            cursor: pointer; transition: all 0.3s ease;
            text-transform: uppercase;
            display: flex; justify-content: center; align-items: center; gap: 8px;
        }
        .btn:hover { border-color: rgba(255,255,255,0.1); color: #fff; }
        .error { color: #ff3355; font-size: 10px; font-family: 'Orbitron', monospace; text-align: center; padding: 4px 0; display: none; letter-spacing: 1px; }
        .error.show { display: block; animation: shake 0.4s ease; }
        @keyframes shake { 0%,100%{transform:translateX(0)} 25%{transform:translateX(-4px)} 75%{transform:translateX(4px)} }
        .footer { text-align: center; font-size: 6px; color: #88ddff; letter-spacing: 3px; margin-top: 12px; font-family: 'Orbitron', monospace; opacity: 0.3; }
        .vip-badge { text-align: center; font-size: 7px; color: #ffd700; letter-spacing: 3px; margin-top: 8px; font-family: 'Orbitron', monospace; border: 1px solid rgba(255,215,0,0.05); padding: 4px; border-radius: 30px; }
    </style>
</head>
<body>
    <div class="bg"><div class="orb"></div><div class="orb"></div></div>
    <div class="box">
        <div class="icon"><i class="fas fa-gem"></i></div>
        <h1><span class="hl">VIP</span> LOGIN</h1>
        <div class="sub">premium · subscription</div>
        <form method="POST">
            <div class="form-group">
                <label><i class="fas fa-user"></i> username</label>
                <div class="input-wrap">
                    <div class="pre"><i class="fas fa-user"></i></div>
                    <input type="text" name="username" placeholder="vip username" required autofocus>
                </div>
            </div>
            <div class="form-group">
                <label><i class="fas fa-key"></i> password</label>
                <div class="input-wrap">
                    <div class="pre"><i class="fas fa-lock"></i></div>
                    <input type="password" name="password" placeholder="vip password" required>
                </div>
            </div>
            <div class="error" id="error">{{ error }}</div>
            <button type="submit" class="btn"><i class="fas fa-unlock-alt"></i> unlock</button>
        </form>
        <div class="vip-badge"><i class="fas fa-star"></i> VIP SUBSCRIPTION <i class="fas fa-star"></i></div>
        <div class="footer">⚡ SAKIL BHAI · ENTERPRISE ⚡</div>
    </div>
    <script>
        document.querySelector('input[name="username"]').focus();
        {% if error %}document.getElementById('error').classList.add('show');{% endif %}
    </script>
</body>
</html>
'''

# ===========================================================
# ROUTES
# ===========================================================

# ---- OWNER ----
@app.route('/owner', methods=['GET', 'POST'])
def owner_login():
    if session.get("role") == "owner" and session.get("authenticated"):
        return redirect(url_for('owner_dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        owners = get_owners()
        if username in owners and verify_password(password, owners[username].get("password", "")):
            if owners[username].get("active", True):
                session.permanent = True
                session["authenticated"] = True
                session["username"] = username
                session["role"] = "owner"
                session["device_id"] = str(uuid.uuid4())
                
                # Register device
                register_device(username, "owner", session["device_id"],
                              request.remote_addr, request.headers.get('User-Agent'))
                
                return redirect(url_for('owner_dashboard'))
            else:
                return render_template_string(OWNER_LOGIN_HTML, error="⚠️ Account suspended")
        else:
            return render_template_string(OWNER_LOGIN_HTML, error="❌ Invalid credentials")
    
    return render_template_string(OWNER_LOGIN_HTML, error="")

@app.route('/owner/dashboard')
@owner_required
@check_device_auth
def owner_dashboard():
    owners = get_owners()
    owner = owners.get(session.get("username"), {})
    admins = get_admins()
    resellers = get_resellers()
    users = get_users()
    devices = get_device_logs()
    transactions = get_wallet_transactions()
    
    # Stats
    total_users = len(users)
    total_resellers = len(resellers)
    total_admins = len(admins)
    
    active_users = sum(1 for u in users.values() if u.get("active", False))
    active_resellers = sum(1 for r in resellers.values() if r.get("active", False))
    active_admins = sum(1 for a in admins.values() if a.get("active", False))
    
    # Online users (active device sessions)
    online_users = 0
    online_resellers = 0
    online_admins = 0
    for key, entry in devices.items():
        if entry.get("active", False):
            expires = entry.get("expires_at")
            if expires:
                try:
                    exp_dt = datetime.datetime.fromisoformat(expires)
                    if exp_dt > datetime.datetime.utcnow():
                        role = entry.get("role", "")
                        if role == "user": online_users += 1
                        elif role == "reseller": online_resellers += 1
                        elif role == "admin": online_admins += 1
                except:
                    pass
    
    # Income
    total_income = 0
    today_income = 0
    monthly_income = 0
    today = datetime.datetime.utcnow().date()
    month_start = today.replace(day=1)
    
    for key, entry in transactions.items():
        if entry.get("type") == "income":
            amount = entry.get("amount", 0)
            total_income += amount
            try:
                created = datetime.datetime.fromisoformat(entry.get("created_at", ""))
                if created.date() == today:
                    today_income += amount
                if created.date() >= month_start:
                    monthly_income += amount
            except:
                pass
    
    stats = {
        "total_users": total_users,
        "total_resellers": total_resellers,
        "total_admins": total_admins,
        "active_users": active_users,
        "active_resellers": active_resellers,
        "active_admins": active_admins,
        "online_users": online_users,
        "online_resellers": online_resellers,
        "online_admins": online_admins,
        "total_income": total_income,
        "today_income": today_income,
        "monthly_income": monthly_income,
        "total_sales": len(transactions),
        "device_limit": owner.get("settings", {}).get("default_device_limit", 5)
    }
    
    return render_template_string(OWNER_DASHBOARD_HTML, 
                                 owner=owner, 
                                 stats=stats,
                                 admins=admins,
                                 resellers=resellers,
                                 users=users,
                                 devices=devices,
                                 remaining=get_remaining_seconds())

# ---- OWNER DASHBOARD HTML ----
OWNER_DASHBOARD_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>👑 OWNER · SAKIL BHAI</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;800;900&family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Inter', sans-serif; background: #06060a; min-height: 100vh; }
        .container { max-width: 1400px; margin: 0 auto; padding: 16px; }
        .header {
            background: rgba(6,6,12,0.95); border: 1px solid rgba(255,215,0,0.1);
            border-radius: 16px; padding: 16px 20px; margin-bottom: 16px;
            display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;
        }
        .header .brand { display: flex; align-items: center; gap: 12px; }
        .header .brand img { width: 40px; height: 40px; border-radius: 50%; border: 1px solid rgba(255,215,0,0.2); object-fit: cover; padding: 2px; background: rgba(0,0,0,0.3); }
        .header .brand h1 { font-family: 'Orbitron', monospace; font-size: 18px; font-weight: 700; color: #fff; }
        .header .brand h1 .hl { color: #ffd700; }
        .header .brand .sub { font-size: 7px; font-family: 'Orbitron', monospace; color: #ffd700; letter-spacing: 4px; }
        .header .actions { display: flex; gap: 8px; flex-wrap: wrap; }
        .header .actions a {
            font-size: 8px; font-family: 'Orbitron', monospace;
            color: #ffd700; text-decoration: none;
            padding: 4px 14px; border: 1px solid rgba(255,215,0,0.05);
            border-radius: 30px; letter-spacing: 2px; transition: all 0.3s ease;
        }
        .header .actions a:hover { border-color: rgba(255,215,0,0.2); color: #fff; }
        .header .actions a.logout { border-color: rgba(255,51,85,0.1); color: #ff3355; }
        .header .actions a.logout:hover { border-color: rgba(255,51,85,0.3); color: #ff3355; }
        .stats-grid {
            display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 10px; margin-bottom: 16px;
        }
        .stat-card {
            background: rgba(6,6,12,0.92); border: 1px solid rgba(255,255,255,0.03);
            border-radius: 12px; padding: 12px 14px; text-align: center;
        }
        .stat-card .num { font-family: 'Orbitron', monospace; font-size: 22px; font-weight: 700; color: #fff; }
        .stat-card .num.gold { color: #ffd700; }
        .stat-card .num.cyan { color: #00ffff; }
        .stat-card .num.green { color: #00ff66; }
        .stat-card .num.red { color: #ff3355; }
        .stat-card .label { font-size: 6px; font-family: 'Orbitron', monospace; color: #88ddff; letter-spacing: 2px; text-transform: uppercase; margin-top: 2px; }
        .card {
            background: rgba(6,6,12,0.92); border: 1px solid rgba(255,255,255,0.03);
            border-radius: 14px; padding: 16px 18px; margin-bottom: 14px;
        }
        .card .title {
            font-size: 8px; font-family: 'Orbitron', monospace;
            color: #88ddff; letter-spacing: 3px; text-transform: uppercase;
            margin-bottom: 12px; display: flex; align-items: center; gap: 8px;
        }
        .card .title i { color: #ffd700; font-size: 11px; }
        .table-wrap { overflow-x: auto; }
        table { width: 100%; border-collapse: collapse; font-size: 11px; }
        th { font-size: 7px; font-family: 'Orbitron', monospace; color: #88ddff; letter-spacing: 2px; text-transform: uppercase; padding: 6px 8px; border-bottom: 1px solid rgba(255,255,255,0.03); text-align: left; }
        td { color: #ccddff; padding: 6px 8px; border-bottom: 1px solid rgba(255,255,255,0.02); font-size: 10px; }
        .badge { font-size: 6px; font-family: 'Orbitron', monospace; padding: 1px 10px; border-radius: 30px; border: 1px solid rgba(255,255,255,0.03); color: #88ddff; }
        .badge.active { border-color: rgba(0,255,102,0.2); color: #00ff66; }
        .badge.inactive { border-color: rgba(255,51,85,0.2); color: #ff3355; }
        .badge.owner { border-color: rgba(255,215,0,0.2); color: #ffd700; }
        .badge.admin { border-color: rgba(0,255,255,0.2); color: #00ffff; }
        .badge.reseller { border-color: rgba(0,255,102,0.2); color: #00ff66; }
        .badge.user { border-color: rgba(255,255,255,0.05); color: #88ddff; }
        .actions-cell { display: flex; gap: 4px; flex-wrap: wrap; }
        .actions-cell a { font-size: 7px; font-family: 'Orbitron', monospace; color: #88ddff; text-decoration: none; padding: 1px 8px; border: 1px solid rgba(255,255,255,0.03); border-radius: 4px; transition: all 0.3s ease; }
        .actions-cell a:hover { border-color: rgba(255,255,255,0.1); color: #fff; }
        .actions-cell a.del:hover { border-color: rgba(255,51,85,0.2); color: #ff3355; }
        .add-form { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
        .add-form input, .add-form select {
            padding: 6px 12px; background: rgba(0,0,0,0.2);
            border: 1px solid rgba(255,215,0,0.05); border-radius: 8px;
            color: #fff; font-size: 12px; outline: none;
            font-family: 'Inter', sans-serif; flex: 1; min-width: 100px;
        }
        .add-form input:focus, .add-form select:focus { border-color: rgba(255,215,0,0.15); }
        .add-form input::placeholder { color: #88ddff; }
        .add-form select option { background: #0a0a1a; color: #fff; }
        .add-form .btn-add {
            padding: 6px 18px; background: rgba(255,215,0,0.03);
            border: 1px solid rgba(255,215,0,0.05); border-radius: 8px;
            color: #ffd700; font-family: 'Orbitron', monospace;
            font-size: 9px; letter-spacing: 2px; cursor: pointer;
            transition: all 0.3s ease;
        }
        .add-form .btn-add:hover { border-color: rgba(255,215,0,0.2); color: #fff; }
        .flash { padding: 8px 14px; border-radius: 8px; margin-bottom: 12px; font-size: 10px; font-family: 'Orbitron', monospace; letter-spacing: 1px; display: flex; align-items: center; gap: 8px; }
        .flash.success { background: rgba(0,255,102,0.02); border: 1px solid rgba(0,255,102,0.05); color: #00ff66; }
        .flash.error { background: rgba(255,51,85,0.02); border: 1px solid rgba(255,51,85,0.05); color: #ff3355; }
        .empty { text-align: center; color: #88ddff; padding: 16px; font-size: 10px; font-family: 'Orbitron', monospace; letter-spacing: 2px; }
        .footer { text-align: center; font-size: 6px; color: #88ddff; letter-spacing: 3px; margin-top: 10px; font-family: 'Orbitron', monospace; opacity: 0.3; }
        @media (max-width: 600px) {
            .stats-grid { grid-template-columns: repeat(2, 1fr); }
            .add-form { flex-direction: column; }
            .add-form input, .add-form select, .add-form .btn-add { width: 100%; }
            .header .brand h1 { font-size: 14px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="brand">
                <img src="https://i.postimg.cc/1VBJWPhR/IMG-20260724-232723-958.webp" alt="Sakil Bhai">
                <div>
                    <h1><span class="hl">👑 OWNER</span> PANEL</h1>
                    <div class="sub">enterprise · full control</div>
                </div>
            </div>
            <div class="actions">
                <a href="{{ url_for('owner_dashboard') }}"><i class="fas fa-sync"></i> refresh</a>
                <a href="{{ url_for('logout') }}" class="logout"><i class="fas fa-sign-out-alt"></i> logout</a>
            </div>
        </div>

        {% with messages = get_flashed_messages(with_categories=true) %}
            {% for category, message in messages %}
                <div class="flash {{ category }}"><i class="fas fa-{% if category == 'success' %}check-circle{% else %}exclamation-circle{% endif %}"></i> {{ message }}</div>
            {% endfor %}
        {% endwith %}

        <div class="stats-grid">
            <div class="stat-card"><div class="num gold">{{ stats.total_users }}</div><div class="label">total users</div></div>
            <div class="stat-card"><div class="num gold">{{ stats.total_resellers }}</div><div class="label">resellers</div></div>
            <div class="stat-card"><div class="num gold">{{ stats.total_admins }}</div><div class="label">admins</div></div>
            <div class="stat-card"><div class="num cyan">{{ stats.online_users }}</div><div class="label">online users</div></div>
            <div class="stat-card"><div class="num cyan">{{ stats.online_resellers }}</div><div class="label">online resellers</div></div>
            <div class="stat-card"><div class="num cyan">{{ stats.online_admins }}</div><div class="label">online admins</div></div>
            <div class="stat-card"><div class="num green">₹{{ stats.total_income }}</div><div class="label">total income</div></div>
            <div class="stat-card"><div class="num green">₹{{ stats.today_income }}</div><div class="label">today's income</div></div>
            <div class="stat-card"><div class="num green">₹{{ stats.monthly_income }}</div><div class="label">monthly income</div></div>
            <div class="stat-card"><div class="num">{{ stats.total_sales }}</div><div class="label">total sales</div></div>
        </div>

        <!-- Device Limit Settings -->
        <div class="card">
            <div class="title"><i class="fas fa-devices"></i> device limit settings</div>
            <form method="POST" action="{{ url_for('owner_update_settings') }}" class="add-form">
                <input type="number" name="default_device_limit" value="{{ stats.device_limit }}" min="1" max="999999" style="width:150px;">
                <input type="number" name="min_password_length" value="6" min="4" max="64" style="width:150px;">
                <input type="number" name="max_password_length" value="32" min="4" max="128" style="width:150px;">
                <button type="submit" class="btn-add"><i class="fas fa-save"></i> update</button>
            </form>
            <div style="font-size:8px; color:#88ddff; margin-top:6px; font-family:'Orbitron',monospace; letter-spacing:1px;">
                <i class="fas fa-info-circle"></i> Current device limit: <strong style="color:#ffd700;">{{ stats.device_limit }}</strong> devices per user
            </div>
        </div>

        <!-- Add Admin -->
        <div class="card">
            <div class="title"><i class="fas fa-user-shield"></i> add admin</div>
            <form method="POST" action="{{ url_for('owner_add_admin') }}" class="add-form">
                <input type="text" name="username" placeholder="admin username" required>
                <input type="password" name="password" placeholder="admin password" required>
                <input type="number" name="device_limit" placeholder="device limit" value="10" min="1" max="999999" style="width:120px;">
                <button type="submit" class="btn-add"><i class="fas fa-plus"></i> add</button>
            </form>
        </div>

        <!-- Add Reseller -->
        <div class="card">
            <div class="title"><i class="fas fa-store"></i> add reseller</div>
            <form method="POST" action="{{ url_for('owner_add_reseller') }}" class="add-form">
                <input type="text" name="username" placeholder="reseller username" required>
                <input type="password" name="password" placeholder="reseller password" required>
                <input type="number" name="device_limit" placeholder="device limit" value="15" min="1" max="999999" style="width:120px;">
                <input type="text" name="company_name" placeholder="company name" style="width:150px;">
                <button type="submit" class="btn-add"><i class="fas fa-plus"></i> add</button>
            </form>
        </div>

        <!-- Add User -->
        <div class="card">
            <div class="title"><i class="fas fa-user-plus"></i> add vip user</div>
            <form method="POST" action="{{ url_for('owner_add_user') }}" class="add-form">
                <input type="text" name="username" placeholder="username" required>
                <input type="password" name="password" placeholder="password" required>
                <input type="number" name="device_limit" placeholder="device limit" value="5" min="1" max="999999" style="width:120px;">
                <select name="reseller">
                    <option value="">— no reseller —</option>
                    {% for r in resellers.keys() %}
                    <option value="{{ r }}">{{ r }}</option>
                    {% endfor %}
                </select>
                <button type="submit" class="btn-add"><i class="fas fa-plus"></i> add</button>
            </form>
        </div>

        <!-- Admins List -->
        <div class="card">
            <div class="title"><i class="fas fa-shield-halved"></i> admins ({{ admins|length }})</div>
            <div class="table-wrap">
                {% if admins %}
                <table>
                    <thead><tr><th>username</th><th>device limit</th><th>status</th><th>actions</th></tr></thead>
                    <tbody>
                    {% for u, d in admins.items() %}
                    <tr>
                        <td>{{ u }}</td>
                        <td>{{ d.get('device_limit', 10) }}</td>
                        <td><span class="badge {{ 'active' if d.get('active', True) else 'inactive' }}">{{ 'active' if d.get('active', True) else 'inactive' }}</span></td>
                        <td class="actions-cell">
                            <a href="{{ url_for('owner_toggle_admin', username=u) }}"><i class="fas fa-{% if d.get('active', True) %}pause{% else %}play{% endif %}"></i></a>
                            <a href="{{ url_for('owner_reset_password', role='admin', username=u) }}"><i class="fas fa-key"></i></a>
                            <a href="{{ url_for('owner_delete_admin', username=u) }}" class="del" onclick="return confirm('Delete {{ u }}?')"><i class="fas fa-trash"></i></a>
                        </td>
                    </tr>
                    {% endfor %}
                    </tbody>
                </table>
                {% else %}<div class="empty">no admins</div>{% endif %}
            </div>
        </div>

        <!-- Resellers List -->
        <div class="card">
            <div class="title"><i class="fas fa-store"></i> resellers ({{ resellers|length }})</div>
            <div class="table-wrap">
                {% if resellers %}
                <table>
                    <thead><tr><th>username</th><th>company</th><th>device limit</th><th>status</th><th>actions</th></tr></thead>
                    <tbody>
                    {% for u, d in resellers.items() %}
                    <tr>
                        <td>{{ u }}</td>
                        <td style="color:#00ff66;">{{ d.get('company_name', 'N/A') }}</td>
                        <td>{{ d.get('device_limit', 15) }}</td>
                        <td><span class="badge {{ 'active' if d.get('active', True) else 'inactive' }}">{{ 'active' if d.get('active', True) else 'inactive' }}</span></td>
                        <td class="actions-cell">
                            <a href="{{ url_for('owner_toggle_reseller', username=u) }}"><i class="fas fa-{% if d.get('active', True) %}pause{% else %}play{% endif %}"></i></a>
                            <a href="{{ url_for('owner_reset_password', role='reseller', username=u) }}"><i class="fas fa-key"></i></a>
                            <a href="{{ url_for('owner_delete_reseller', username=u) }}" class="del" onclick="return confirm('Delete {{ u }}?')"><i class="fas fa-trash"></i></a>
                        </td>
                    </tr>
                    {% endfor %}
                    </tbody>
                </table>
                {% else %}<div class="empty">no resellers</div>{% endif %}
            </div>
        </div>

        <!-- Users List -->
        <div class="card">
            <div class="title"><i class="fas fa-users"></i> vip users ({{ users|length }})</div>
            <div class="table-wrap">
                {% if users %}
                <table>
                    <thead><tr><th>username</th><th>reseller</th><th>device limit</th><th>status</th><th>actions</th></tr></thead>
                    <tbody>
                    {% for u, d in users.items() %}
                    <tr>
                        <td>{{ u }}</td>
                        <td>{{ d.get('reseller', '—') }}</td>
                        <td>{{ d.get('device_limit', 5) }}</td>
                        <td><span class="badge {{ 'active' if d.get('active', True) else 'inactive' }}">{{ 'active' if d.get('active', True) else 'inactive' }}</span></td>
                        <td class="actions-cell">
                            <a href="{{ url_for('owner_toggle_user', username=u) }}"><i class="fas fa-{% if d.get('active', True) %}pause{% else %}play{% endif %}"></i></a>
                            <a href="{{ url_for('owner_reset_password', role='user', username=u) }}"><i class="fas fa-key"></i></a>
                            <a href="{{ url_for('owner_logout_user', username=u) }}" class="del"><i class="fas fa-sign-out-alt"></i></a>
                            <a href="{{ url_for('owner_delete_user', username=u) }}" class="del" onclick="return confirm('Delete {{ u }}?')"><i class="fas fa-trash"></i></a>
                        </td>
                    </tr>
                    {% endfor %}
                    </tbody>
                </table>
                {% else %}<div class="empty">no users</div>{% endif %}
            </div>
        </div>

        <!-- Device Logs -->
        <div class="card">
            <div class="title"><i class="fas fa-devices"></i> active devices</div>
            <div class="table-wrap">
                {% if devices %}
                <table>
                    <thead><tr><th>user</th><th>role</th><th>device</th><th>last active</th></tr></thead>
                    <tbody>
                    {% for key, entry in devices.items() %}
                    {% if entry.get('active', False) %}
                    <tr>
                        <td>{{ entry.get('username', '') }}</td>
                        <td><span class="badge {{ entry.get('role', 'user') }}">{{ entry.get('role', 'user') }}</span></td>
                        <td style="font-size:8px; color:#88ddff;">{{ entry.get('device_id', '')[:8] }}...</td>
                        <td style="font-size:8px; color:#88ddff;">{{ entry.get('last_active', '')[:16] }}</td>
                    </tr>
                    {% endif %}
                    {% endfor %}
                    </tbody>
                </table>
                {% else %}<div class="empty">no active devices</div>{% endif %}
            </div>
        </div>

        <div class="footer">⚡ SAKIL BHAI · ENTERPRISE PLATFORM ⚡</div>
    </div>
</body>
</html>
'''

# ---- OWNER ACTIONS ----
@app.route('/owner/update-settings', methods=['POST'])
@owner_required
def owner_update_settings():
    owners = get_owners()
    owner = owners.get(session.get("username"), {})
    
    default_limit = request.form.get('default_device_limit', 5)
    min_len = request.form.get('min_password_length', 6)
    max_len = request.form.get('max_password_length', 32)
    
    try:
        default_limit = int(default_limit)
        min_len = int(min_len)
        max_len = int(max_len)
    except:
        flash("Invalid values!", "error")
        return redirect(url_for('owner_dashboard'))
    
    if min_len > max_len:
        flash("Min password length cannot be greater than max!", "error")
        return redirect(url_for('owner_dashboard'))
    
    if "settings" not in owner:
        owner["settings"] = {}
    owner["settings"]["default_device_limit"] = default_limit
    owner["settings"]["min_password_length"] = min_len
    owner["settings"]["max_password_length"] = max_len
    
    owners[session.get("username")] = owner
    fb_set("owners", owners)
    flash(f"Settings updated! Device limit: {default_limit}, Password: {min_len}-{max_len}", "success")
    return redirect(url_for('owner_dashboard'))

@app.route('/owner/add-admin', methods=['POST'])
@owner_required
def owner_add_admin():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    device_limit = request.form.get('device_limit', 10)
    
    try:
        device_limit = int(device_limit)
    except:
        device_limit = 10
    
    if not username or not password:
        flash("Username and password required!", "error")
        return redirect(url_for('owner_dashboard'))
    
    admins = get_admins()
    if username in admins:
        flash("Admin already exists!", "error")
        return redirect(url_for('owner_dashboard'))
    
    admins[username] = {
        "password": hash_password(password),
        "role": "admin",
        "active": True,
        "created": datetime.datetime.utcnow().isoformat(),
        "device_limit": device_limit,
        "created_by": session.get("username")
    }
    fb_set("admins", admins)
    flash(f"Admin '{username}' created! Device limit: {device_limit}", "success")
    return redirect(url_for('owner_dashboard'))

@app.route('/owner/add-reseller', methods=['POST'])
@owner_required
def owner_add_reseller():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    device_limit = request.form.get('device_limit', 15)
    company_name = request.form.get('company_name', '').strip()
    
    try:
        device_limit = int(device_limit)
    except:
        device_limit = 15
    
    if not username or not password:
        flash("Username and password required!", "error")
        return redirect(url_for('owner_dashboard'))
    
    resellers = get_resellers()
    if username in resellers:
        flash("Reseller already exists!", "error")
        return redirect(url_for('owner_dashboard'))
    
    resellers[username] = {
        "password": hash_password(password),
        "role": "reseller",
        "active": True,
        "created": datetime.datetime.utcnow().isoformat(),
        "device_limit": device_limit,
        "company_name": company_name or username,
        "created_by": session.get("username"),
        "wallet": 0,
        "total_income": 0,
        "branding": {
            "company_name": company_name or username,
            "logo": "https://i.postimg.cc/1VBJWPhR/IMG-20260724-232723-958.webp",
            "theme_color": "#00ff66",
            "powered_by": "PRIYANGSHU"
        }
    }
    fb_set("resellers", resellers)
    flash(f"Reseller '{username}' created! Device limit: {device_limit}", "success")
    return redirect(url_for('owner_dashboard'))

@app.route('/owner/add-user', methods=['POST'])
@owner_required
def owner_add_user():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    device_limit = request.form.get('device_limit', 5)
    reseller = request.form.get('reseller', '').strip()
    
    try:
        device_limit = int(device_limit)
    except:
        device_limit = 5
    
    if not username or not password:
        flash("Username and password required!", "error")
        return redirect(url_for('owner_dashboard'))
    
    users = get_users()
    if username in users:
        flash("User already exists!", "error")
        return redirect(url_for('owner_dashboard'))
    
    users[username] = {
        "password": hash_password(password),
        "role": "user",
        "active": True,
        "created": datetime.datetime.utcnow().isoformat(),
        "device_limit": device_limit,
        "reseller": reseller if reseller else None,
        "created_by": session.get("username"),
        "subscription_expiry": (datetime.datetime.utcnow() + datetime.timedelta(days=30)).isoformat()
    }
    fb_set("users", users)
    flash(f"User '{username}' created! Device limit: {device_limit}", "success")
    return redirect(url_for('owner_dashboard'))

@app.route('/owner/toggle-admin/<username>')
@owner_required
def owner_toggle_admin(username):
    admins = get_admins()
    if username not in admins:
        flash("Admin not found!", "error")
        return redirect(url_for('owner_dashboard'))
    admins[username]["active"] = not admins[username].get("active", True)
    fb_set("admins", admins)
    status = "activated" if admins[username]["active"] else "suspended"
    flash(f"Admin {status}!", "success")
    return redirect(url_for('owner_dashboard'))

@app.route('/owner/toggle-reseller/<username>')
@owner_required
def owner_toggle_reseller(username):
    resellers = get_resellers()
    if username not in resellers:
        flash("Reseller not found!", "error")
        return redirect(url_for('owner_dashboard'))
    resellers[username]["active"] = not resellers[username].get("active", True)
    fb_set("resellers", resellers)
    status = "activated" if resellers[username]["active"] else "suspended"
    flash(f"Reseller {status}!", "success")
    return redirect(url_for('owner_dashboard'))

@app.route('/owner/toggle-user/<username>')
@owner_required
def owner_toggle_user(username):
    users = get_users()
    if username not in users:
        flash("User not found!", "error")
        return redirect(url_for('owner_dashboard'))
    users[username]["active"] = not users[username].get("active", True)
    fb_set("users", users)
    status = "activated" if users[username]["active"] else "suspended"
    flash(f"User {status}!", "success")
    return redirect(url_for('owner_dashboard'))

@app.route('/owner/reset-password/<role>/<username>')
@owner_required
def owner_reset_password(role, username):
    new_password = secrets.token_hex(6)
    hashed = hash_password(new_password)
    
    if role == "admin":
        admins = get_admins()
        if username not in admins:
            flash("Admin not found!", "error")
            return redirect(url_for('owner_dashboard'))
        admins[username]["password"] = hashed
        fb_set("admins", admins)
    elif role == "reseller":
        resellers = get_resellers()
        if username not in resellers:
            flash("Reseller not found!", "error")
            return redirect(url_for('owner_dashboard'))
        resellers[username]["password"] = hashed
        fb_set("resellers", resellers)
    else:  # user
        users = get_users()
        if username not in users:
            flash("User not found!", "error")
            return redirect(url_for('owner_dashboard'))
        users[username]["password"] = hashed
        fb_set("users", users)
    
    # Force logout all devices
    logout_all_devices(username)
    
    flash(f"Password reset for {username}! New password: {new_password}", "success")
    return redirect(url_for('owner_dashboard'))

@app.route('/owner/logout-user/<username>')
@owner_required
def owner_logout_user(username):
    count = logout_all_devices(username)
    flash(f"Forced logout {username}! {count} devices disconnected.", "success")
    return redirect(url_for('owner_dashboard'))

@app.route('/owner/delete-admin/<username>')
@owner_required
def owner_delete_admin(username):
    admins = get_admins()
    if username not in admins:
        flash("Admin not found!", "error")
        return redirect(url_for('owner_dashboard'))
    del admins[username]
    fb_set("admins", admins)
    logout_all_devices(username)
    flash(f"Admin '{username}' deleted!", "success")
    return redirect(url_for('owner_dashboard'))

@app.route('/owner/delete-reseller/<username>')
@owner_required
def owner_delete_reseller(username):
    resellers = get_resellers()
    if username not in resellers:
        flash("Reseller not found!", "error")
        return redirect(url_for('owner_dashboard'))
    del resellers[username]
    fb_set("resellers", resellers)
    logout_all_devices(username)
    flash(f"Reseller '{username}' deleted!", "success")
    return redirect(url_for('owner_dashboard'))

@app.route('/owner/delete-user/<username>')
@owner_required
def owner_delete_user(username):
    users = get_users()
    if username not in users:
        flash("User not found!", "error")
        return redirect(url_for('owner_dashboard'))
    del users[username]
    fb_set("users", users)
    logout_all_devices(username)
    flash(f"User '{username}' deleted!", "success")
    return redirect(url_for('owner_dashboard'))

# ---- ADMIN ----
@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if session.get("role") in ["owner", "admin"] and session.get("authenticated"):
        return redirect(url_for('admin_dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        # Check owners
        owners = get_owners()
        if username in owners and verify_password(password, owners[username].get("password", "")):
            if owners[username].get("active", True):
                session.permanent = True
                session["authenticated"] = True
                session["username"] = username
                session["role"] = "owner"
                session["device_id"] = str(uuid.uuid4())
                register_device(username, "owner", session["device_id"],
                              request.remote_addr, request.headers.get('User-Agent'))
                return redirect(url_for('owner_dashboard'))
        
        # Check admins
        admins = get_admins()
        if username in admins and verify_password(password, admins[username].get("password", "")):
            if admins[username].get("active", True):
                session.permanent = True
                session["authenticated"] = True
                session["username"] = username
                session["role"] = "admin"
                session["device_id"] = str(uuid.uuid4())
                register_device(username, "admin", session["device_id"],
                              request.remote_addr, request.headers.get('User-Agent'))
                return redirect(url_for('admin_dashboard'))
            else:
                return render_template_string(ADMIN_LOGIN_HTML, error="⚠️ Account suspended")
        
        return render_template_string(ADMIN_LOGIN_HTML, error="❌ Invalid credentials")
    
    return render_template_string(ADMIN_LOGIN_HTML, error="")

@app.route('/admin/dashboard')
@admin_required
@check_device_auth
def admin_dashboard():
    users = get_users()
    resellers = get_resellers()
    devices = get_device_logs()
    
    total_users = len(users)
    active_users = sum(1 for u in users.values() if u.get("active", False))
    expired_users = sum(1 for u in users.values() if not u.get("active", False))
    
    # Count users under this admin (if admin has specific scope)
    # For now, show all
    
    return render_template_string(ADMIN_DASHBOARD_HTML,
                                 users=users,
                                 resellers=resellers,
                                 total_users=total_users,
                                 active_users=active_users,
                                 expired_users=expired_users,
                                 devices=devices)

ADMIN_DASHBOARD_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🛡 ADMIN · SAKIL BHAI</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;800;900&family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Inter', sans-serif; background: #06060a; min-height: 100vh; }
        .container { max-width: 1200px; margin: 0 auto; padding: 16px; }
        .header {
            background: rgba(6,6,12,0.95); border: 1px solid rgba(0,255,255,0.1);
            border-radius: 16px; padding: 14px 18px; margin-bottom: 14px;
            display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;
        }
        .header .brand h1 { font-family: 'Orbitron', monospace; font-size: 18px; font-weight: 700; color: #fff; }
        .header .brand h1 .hl { color: #00ffff; }
        .header .brand .sub { font-size: 7px; font-family: 'Orbitron', monospace; color: #88ddff; letter-spacing: 4px; }
        .header .actions a {
            font-size: 8px; font-family: 'Orbitron', monospace;
            color: #88ddff; text-decoration: none;
            padding: 4px 14px; border: 1px solid rgba(255,255,255,0.03);
            border-radius: 30px; letter-spacing: 2px; transition: all 0.3s ease;
        }
        .header .actions a:hover { border-color: rgba(0,255,255,0.2); color: #00ffff; }
        .header .actions a.logout { border-color: rgba(255,51,85,0.1); color: #ff3355; }
        .header .actions a.logout:hover { border-color: rgba(255,51,85,0.3); color: #ff3355; }
        .stats-grid {
            display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 10px; margin-bottom: 14px;
        }
        .stat-card {
            background: rgba(6,6,12,0.92); border: 1px solid rgba(255,255,255,0.03);
            border-radius: 12px; padding: 12px 14px; text-align: center;
        }
        .stat-card .num { font-family: 'Orbitron', monospace; font-size: 20px; font-weight: 700; color: #fff; }
        .stat-card .num.cyan { color: #00ffff; }
        .stat-card .num.green { color: #00ff66; }
        .stat-card .num.red { color: #ff3355; }
        .stat-card .label { font-size: 6px; font-family: 'Orbitron', monospace; color: #88ddff; letter-spacing: 2px; text-transform: uppercase; margin-top: 2px; }
        .card {
            background: rgba(6,6,12,0.92); border: 1px solid rgba(255,255,255,0.03);
            border-radius: 14px; padding: 14px 16px; margin-bottom: 12px;
        }
        .card .title {
            font-size: 8px; font-family: 'Orbitron', monospace;
            color: #88ddff; letter-spacing: 3px; text-transform: uppercase;
            margin-bottom: 10px; display: flex; align-items: center; gap: 6px;
        }
        .card .title i { color: #00ffff; font-size: 11px; }
        .table-wrap { overflow-x: auto; }
        table { width: 100%; border-collapse: collapse; font-size: 11px; }
        th { font-size: 7px; font-family: 'Orbitron', monospace; color: #88ddff; letter-spacing: 2px; text-transform: uppercase; padding: 5px 8px; border-bottom: 1px solid rgba(255,255,255,0.03); text-align: left; }
        td { color: #ccddff; padding: 5px 8px; border-bottom: 1px solid rgba(255,255,255,0.02); font-size: 10px; }
        .badge { font-size: 6px; font-family: 'Orbitron', monospace; padding: 1px 10px; border-radius: 30px; border: 1px solid rgba(255,255,255,0.03); color: #88ddff; }
        .badge.active { border-color: rgba(0,255,102,0.2); color: #00ff66; }
        .badge.inactive { border-color: rgba(255,51,85,0.2); color: #ff3355; }
        .empty { text-align: center; color: #88ddff; padding: 14px; font-size: 10px; font-family: 'Orbitron', monospace; letter-spacing: 2px; }
        .footer { text-align: center; font-size: 6px; color: #88ddff; letter-spacing: 3px; margin-top: 10px; font-family: 'Orbitron', monospace; opacity: 0.3; }
        @media (max-width: 600px) {
            .stats-grid { grid-template-columns: repeat(2, 1fr); }
            .header .brand h1 { font-size: 14px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="brand">
                <h1><span class="hl">🛡 ADMIN</span> PANEL</h1>
                <div class="sub">premium · management</div>
            </div>
            <div class="actions">
                <a href="{{ url_for('logout') }}" class="logout"><i class="fas fa-sign-out-alt"></i> logout</a>
            </div>
        </div>

        <div class="stats-grid">
            <div class="stat-card"><div class="num cyan">{{ total_users }}</div><div class="label">total users</div></div>
            <div class="stat-card"><div class="num green">{{ active_users }}</div><div class="label">active</div></div>
            <div class="stat-card"><div class="num red">{{ expired_users }}</div><div class="label">expired</div></div>
        </div>

        <div class="card">
            <div class="title"><i class="fas fa-users"></i> user list</div>
            <div class="table-wrap">
                {% if users %}
                <table>
                    <thead><tr><th>username</th><th>reseller</th><th>device limit</th><th>status</th></tr></thead>
                    <tbody>
                    {% for u, d in users.items() %}
                    <tr>
                        <td>{{ u }}</td>
                        <td>{{ d.get('reseller', '—') }}</td>
                        <td>{{ d.get('device_limit', 5) }}</td>
                        <td><span class="badge {{ 'active' if d.get('active', True) else 'inactive' }}">{{ 'active' if d.get('active', True) else 'inactive' }}</span></td>
                    </tr>
                    {% endfor %}
                    </tbody>
                </table>
                {% else %}<div class="empty">no users</div>{% endif %}
            </div>
        </div>

        <div class="footer">⚡ SAKIL BHAI · ENTERPRISE ⚡</div>
    </div>
</body>
</html>
'''

# ---- RESELLER ----
@app.route('/reseller', methods=['GET', 'POST'])
def reseller_login():
    if session.get("role") in ["owner", "admin", "reseller"] and session.get("authenticated"):
        return redirect(url_for('reseller_dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        # Check owners
        owners = get_owners()
        if username in owners and verify_password(password, owners[username].get("password", "")):
            if owners[username].get("active", True):
                session.permanent = True
                session["authenticated"] = True
                session["username"] = username
                session["role"] = "owner"
                session["device_id"] = str(uuid.uuid4())
                register_device(username, "owner", session["device_id"],
                              request.remote_addr, request.headers.get('User-Agent'))
                return redirect(url_for('owner_dashboard'))
        
        # Check resellers
        resellers = get_resellers()
        if username in resellers and verify_password(password, resellers[username].get("password", "")):
            if resellers[username].get("active", True):
                session.permanent = True
                session["authenticated"] = True
                session["username"] = username
                session["role"] = "reseller"
                session["device_id"] = str(uuid.uuid4())
                register_device(username, "reseller", session["device_id"],
                              request.remote_addr, request.headers.get('User-Agent'))
                return redirect(url_for('reseller_dashboard'))
            else:
                return render_template_string(RESELLER_LOGIN_HTML, error="⚠️ Account suspended")
        
        return render_template_string(RESELLER_LOGIN_HTML, error="❌ Invalid credentials")
    
    return render_template_string(RESELLER_LOGIN_HTML, error="")

@app.route('/reseller/dashboard')
@reseller_required
@check_device_auth
def reseller_dashboard():
    username = session.get("username")
    resellers = get_resellers()
    reseller_data = resellers.get(username, {})
    users = get_users()
    
    # Users under this reseller
    my_users = {u: d for u, d in users.items() if d.get("reseller") == username}
    total = len(my_users)
    active = sum(1 for d in my_users.values() if d.get("active", False))
    expired = total - active
    
    branding = reseller_data.get("branding", {
        "company_name": username,
        "logo": "https://i.postimg.cc/1VBJWPhR/IMG-20260724-232723-958.webp",
        "theme_color": "#00ff66",
        "powered_by": "PRIYANGSHU"
    })
    
    return render_template_string(RESELLER_DASHBOARD_HTML,
                                 reseller=reseller_data,
                                 branding=branding,
                                 users=my_users,
                                 total=total,
                                 active=active,
                                 expired=expired,
                                 device_limit=reseller_data.get("device_limit", 15))

RESELLER_DASHBOARD_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>👑 RESELLER · {{ branding.company_name }}</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;800;900&family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Inter', sans-serif; background: #06060a; min-height: 100vh; }
        .container { max-width: 1200px; margin: 0 auto; padding: 16px; }
        .header {
            background: rgba(6,6,12,0.95); border: 1px solid rgba(0,255,102,0.1);
            border-radius: 16px; padding: 14px 18px; margin-bottom: 14px;
            display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;
        }
        .header .brand { display: flex; align-items: center; gap: 10px; }
        .header .brand img { width: 36px; height: 36px; border-radius: 50%; border: 1px solid rgba(0,255,102,0.2); object-fit: cover; padding: 2px; background: rgba(0,0,0,0.3); }
        .header .brand h1 { font-family: 'Orbitron', monospace; font-size: 16px; font-weight: 700; color: #fff; }
        .header .brand h1 .hl { color: #00ff66; }
        .header .brand .sub { font-size: 6px; font-family: 'Orbitron', monospace; color: #88ddff; letter-spacing: 3px; }
        .header .actions a {
            font-size: 8px; font-family: 'Orbitron', monospace;
            color: #88ddff; text-decoration: none;
            padding: 4px 14px; border: 1px solid rgba(255,255,255,0.03);
            border-radius: 30px; letter-spacing: 2px; transition: all 0.3s ease;
        }
        .header .actions a:hover { border-color: rgba(0,255,102,0.2); color: #00ff66; }
        .header .actions a.logout { border-color: rgba(255,51,85,0.1); color: #ff3355; }
        .header .actions a.logout:hover { border-color: rgba(255,51,85,0.3); color: #ff3355; }
        .stats-grid {
            display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 10px; margin-bottom: 14px;
        }
        .stat-card {
            background: rgba(6,6,12,0.92); border: 1px solid rgba(255,255,255,0.03);
            border-radius: 12px; padding: 12px 14px; text-align: center;
        }
        .stat-card .num { font-family: 'Orbitron', monospace; font-size: 20px; font-weight: 700; color: #fff; }
        .stat-card .num.green { color: #00ff66; }
        .stat-card .num.cyan { color: #00ffff; }
        .stat-card .num.red { color: #ff3355; }
        .stat-card .label { font-size: 6px; font-family: 'Orbitron', monospace; color: #88ddff; letter-spacing: 2px; text-transform: uppercase; margin-top: 2px; }
        .card {
            background: rgba(6,6,12,0.92); border: 1px solid rgba(255,255,255,0.03);
            border-radius: 14px; padding: 14px 16px; margin-bottom: 12px;
        }
        .card .title {
            font-size: 8px; font-family: 'Orbitron', monospace;
            color: #88ddff; letter-spacing: 3px; text-transform: uppercase;
            margin-bottom: 10px; display: flex; align-items: center; gap: 6px;
        }
        .card .title i { color: #00ff66; font-size: 11px; }
        .table-wrap { overflow-x: auto; }
        table { width: 100%; border-collapse: collapse; font-size: 11px; }
        th { font-size: 7px; font-family: 'Orbitron', monospace; color: #88ddff; letter-spacing: 2px; text-transform: uppercase; padding: 5px 8px; border-bottom: 1px solid rgba(255,255,255,0.03); text-align: left; }
        td { color: #ccddff; padding: 5px 8px; border-bottom: 1px solid rgba(255,255,255,0.02); font-size: 10px; }
        .badge { font-size: 6px; font-family: 'Orbitron', monospace; padding: 1px 10px; border-radius: 30px; border: 1px solid rgba(255,255,255,0.03); color: #88ddff; }
        .badge.active { border-color: rgba(0,255,102,0.2); color: #00ff66; }
        .badge.inactive { border-color: rgba(255,51,85,0.2); color: #ff3355; }
        .add-form { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
        .add-form input, .add-form select {
            padding: 5px 10px; background: rgba(0,0,0,0.2);
            border: 1px solid rgba(0,255,102,0.05); border-radius: 8px;
            color: #fff; font-size: 12px; outline: none;
            font-family: 'Inter', sans-serif; flex: 1; min-width: 80px;
        }
        .add-form input:focus, .add-form select:focus { border-color: rgba(0,255,102,0.15); }
        .add-form input::placeholder { color: #88ddff; }
        .add-form select option { background: #0a0a1a; color: #fff; }
        .add-form .btn-add {
            padding: 5px 16px; background: rgba(0,255,102,0.03);
            border: 1px solid rgba(0,255,102,0.05); border-radius: 8px;
            color: #00ff66; font-family: 'Orbitron', monospace;
            font-size: 8px; letter-spacing: 2px; cursor: pointer;
            transition: all 0.3s ease;
        }
        .add-form .btn-add:hover { border-color: rgba(0,255,102,0.2); color: #fff; }
        .actions-cell { display: flex; gap: 4px; flex-wrap: wrap; }
        .actions-cell a { font-size: 7px; font-family: 'Orbitron', monospace; color: #88ddff; text-decoration: none; padding: 1px 8px; border: 1px solid rgba(255,255,255,0.03); border-radius: 4px; transition: all 0.3s ease; }
        .actions-cell a:hover { border-color: rgba(0,255,102,0.2); color: #00ff66; }
        .actions-cell a.del:hover { border-color: rgba(255,51,85,0.2); color: #ff3355; }
        .powered { text-align: center; font-size: 7px; font-family: 'Orbitron', monospace; color: #ffd700; letter-spacing: 2px; margin-top: 8px; }
        .footer { text-align: center; font-size: 6px; color: #88ddff; letter-spacing: 3px; margin-top: 10px; font-family: 'Orbitron', monospace; opacity: 0.3; }
        @media (max-width: 600px) {
            .stats-grid { grid-template-columns: repeat(2, 1fr); }
            .add-form { flex-direction: column; }
            .add-form input, .add-form select, .add-form .btn-add { width: 100%; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="brand">
                <img src="{{ branding.logo }}" alt="Logo">
                <div>
                    <h1><span class="hl">👑</span> {{ branding.company_name }}</h1>
                    <div class="sub">reseller · premium</div>
                </div>
            </div>
            <div class="actions">
                <a href="{{ url_for('reseller_dashboard') }}"><i class="fas fa-sync"></i></a>
                <a href="{{ url_for('logout') }}" class="logout"><i class="fas fa-sign-out-alt"></i></a>
            </div>
        </div>

        <div class="stats-grid">
            <div class="stat-card"><div class="num green">{{ total }}</div><div class="label">total users</div></div>
            <div class="stat-card"><div class="num green">{{ active }}</div><div class="label">active</div></div>
            <div class="stat-card"><div class="num red">{{ expired }}</div><div class="label">expired</div></div>
            <div class="stat-card"><div class="num cyan">{{ device_limit }}</div><div class="label">device limit</div></div>
        </div>

        <div class="card">
            <div class="title"><i class="fas fa-user-plus"></i> create user</div>
            <form method="POST" action="{{ url_for('reseller_add_user') }}" class="add-form">
                <input type="text" name="username" placeholder="username" required>
                <input type="password" name="password" placeholder="password" required>
                <input type="number" name="device_limit" placeholder="device limit" value="{{ device_limit }}" min="1" max="999999" style="width:120px;">
                <button type="submit" class="btn-add"><i class="fas fa-plus"></i> add</button>
            </form>
        </div>

        <div class="card">
            <div class="title"><i class="fas fa-users"></i> my users ({{ users|length }})</div>
            <div class="table-wrap">
                {% if users %}
                <table>
                    <thead><tr><th>username</th><th>device limit</th><th>status</th><th>actions</th></tr></thead>
                    <tbody>
                    {% for u, d in users.items() %}
                    <tr>
                        <td>{{ u }}</td>
                        <td>{{ d.get('device_limit', 5) }}</td>
                        <td><span class="badge {{ 'active' if d.get('active', True) else 'inactive' }}">{{ 'active' if d.get('active', True) else 'inactive' }}</span></td>
                        <td class="actions-cell">
                            <a href="{{ url_for('reseller_toggle_user', username=u) }}"><i class="fas fa-{% if d.get('active', True) %}pause{% else %}play{% endif %}"></i></a>
                            <a href="{{ url_for('reseller_reset_password', username=u) }}"><i class="fas fa-key"></i></a>
                            <a href="{{ url_for('reseller_delete_user', username=u) }}" class="del" onclick="return confirm('Delete {{ u }}?')"><i class="fas fa-trash"></i></a>
                        </td>
                    </tr>
                    {% endfor %}
                    </tbody>
                </table>
                {% else %}<div class="empty" style="text-align:center;color:#88ddff;padding:14px;">no users created yet</div>{% endif %}
            </div>
        </div>

        <div class="powered"><i class="fas fa-star"></i> Powered By <strong style="color:#ffd700;">{{ branding.powered_by }}</strong> <i class="fas fa-star"></i></div>
        <div class="footer">⚡ SAKIL BHAI · ENTERPRISE ⚡</div>
    </div>
</body>
</html>
'''

# ---- RESELLER ACTIONS ----
@app.route('/reseller/add-user', methods=['POST'])
@reseller_required
def reseller_add_user():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    device_limit = request.form.get('device_limit', 5)
    
    try:
        device_limit = int(device_limit)
    except:
        device_limit = 5
    
    if not username or not password:
        flash("Username and password required!", "error")
        return redirect(url_for('reseller_dashboard'))
    
    users = get_users()
    if username in users:
        flash("User already exists!", "error")
        return redirect(url_for('reseller_dashboard'))
    
    # Check reseller's device limit (can't give more than own limit)
    reseller_data = get_resellers().get(session.get("username"), {})
    max_limit = reseller_data.get("device_limit", 15)
    if device_limit > max_limit:
        device_limit = max_limit
    
    users[username] = {
        "password": hash_password(password),
        "role": "user",
        "active": True,
        "created": datetime.datetime.utcnow().isoformat(),
        "device_limit": device_limit,
        "reseller": session.get("username"),
        "created_by": session.get("username"),
        "subscription_expiry": (datetime.datetime.utcnow() + datetime.timedelta(days=30)).isoformat()
    }
    fb_set("users", users)
    flash(f"User '{username}' created! Device limit: {device_limit}", "success")
    return redirect(url_for('reseller_dashboard'))

@app.route('/reseller/toggle-user/<username>')
@reseller_required
def reseller_toggle_user(username):
    users = get_users()
    if username not in users or users[username].get("reseller") != session.get("username"):
        flash("User not found or not yours!", "error")
        return redirect(url_for('reseller_dashboard'))
    
    users[username]["active"] = not users[username].get("active", True)
    fb_set("users", users)
    status = "activated" if users[username]["active"] else "suspended"
    flash(f"User {status}!", "success")
    return redirect(url_for('reseller_dashboard'))

@app.route('/reseller/reset-password/<username>')
@reseller_required
def reseller_reset_password(username):
    users = get_users()
    if username not in users or users[username].get("reseller") != session.get("username"):
        flash("User not found or not yours!", "error")
        return redirect(url_for('reseller_dashboard'))
    
    new_password = secrets.token_hex(6)
    users[username]["password"] = hash_password(new_password)
    fb_set("users", users)
    logout_all_devices(username)
    flash(f"Password reset! New password: {new_password}", "success")
    return redirect(url_for('reseller_dashboard'))

@app.route('/reseller/delete-user/<username>')
@reseller_required
def reseller_delete_user(username):
    users = get_users()
    if username not in users or users[username].get("reseller") != session.get("username"):
        flash("User not found or not yours!", "error")
        return redirect(url_for('reseller_dashboard'))
    
    del users[username]
    fb_set("users", users)
    logout_all_devices(username)
    flash(f"User '{username}' deleted!", "success")
    return redirect(url_for('reseller_dashboard'))

# ---- USER ----
@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if session.get("authenticated"):
        return redirect(url_for('user_dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        # Check all roles
        owners = get_owners()
        if username in owners and verify_password(password, owners[username].get("password", "")):
            if owners[username].get("active", True):
                session.permanent = True
                session["authenticated"] = True
                session["username"] = username
                session["role"] = "owner"
                session["device_id"] = str(uuid.uuid4())
                register_device(username, "owner", session["device_id"],
                              request.remote_addr, request.headers.get('User-Agent'))
                return redirect(url_for('owner_dashboard'))
        
        admins = get_admins()
        if username in admins and verify_password(password, admins[username].get("password", "")):
            if admins[username].get("active", True):
                session.permanent = True
                session["authenticated"] = True
                session["username"] = username
                session["role"] = "admin"
                session["device_id"] = str(uuid.uuid4())
                register_device(username, "admin", session["device_id"],
                              request.remote_addr, request.headers.get('User-Agent'))
                return redirect(url_for('admin_dashboard'))
            else:
                return render_template_string(USER_LOGIN_HTML, error="⚠️ Account suspended")
        
        resellers = get_resellers()
        if username in resellers and verify_password(password, resellers[username].get("password", "")):
            if resellers[username].get("active", True):
                session.permanent = True
                session["authenticated"] = True
                session["username"] = username
                session["role"] = "reseller"
                session["device_id"] = str(uuid.uuid4())
                register_device(username, "reseller", session["device_id"],
                              request.remote_addr, request.headers.get('User-Agent'))
                return redirect(url_for('reseller_dashboard'))
            else:
                return render_template_string(USER_LOGIN_HTML, error="⚠️ Account suspended")
        
        users = get_users()
        if username in users and verify_password(password, users[username].get("password", "")):
            if users[username].get("active", True):
                # Check device limit
                if not check_device_limit(username, "user"):
                    limit = get_device_limit(username, "user")
                    flash(f"Device limit exceeded! Max {limit} devices.", "error")
                    return render_template_string(USER_LOGIN_HTML, error=f"⚠️ Device limit ({limit}) exceeded")
                
                session.permanent = True
                session["authenticated"] = True
                session["username"] = username
                session["role"] = "user"
                session["device_id"] = str(uuid.uuid4())
                register_device(username, "user", session["device_id"],
                              request.remote_addr, request.headers.get('User-Agent'))
                return redirect(url_for('user_dashboard'))
            else:
                return render_template_string(USER_LOGIN_HTML, error="⚠️ Account suspended")
        
        return render_template_string(USER_LOGIN_HTML, error="❌ Invalid credentials")
    
    return render_template_string(USER_LOGIN_HTML, error="")

@app.route('/')
@user_required
@check_device_auth
def user_dashboard():
    username = session.get("username")
    users = get_users()
    user_data = users.get(username, {})
    devices = get_device_logs()
    
    # Get user's devices
    my_devices = []
    for key, entry in devices.items():
        if entry.get("username") == username and entry.get("role") == "user":
            my_devices.append(entry)
    
    # Subscription info
    expiry = user_data.get("subscription_expiry", "")
    days_left = 0
    if expiry:
        try:
            exp_dt = datetime.datetime.fromisoformat(expiry)
            days_left = max(0, (exp_dt - datetime.datetime.utcnow()).days)
        except:
            pass
    
    return render_template_string(USER_DASHBOARD_HTML,
                                 user=user_data,
                                 devices=my_devices,
                                 days_left=days_left,
                                 device_limit=user_data.get("device_limit", 5),
                                 current_device=session.get("device_id"))

USER_DASHBOARD_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>👤 VIP · SAKIL BHAI</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;800;900&family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Inter', sans-serif; background: #06060a; min-height: 100vh; }
        .container { max-width: 800px; margin: 0 auto; padding: 16px; }
        .card {
            background: rgba(6,6,12,0.95); border: 1px solid rgba(255,255,255,0.05);
            border-radius: 16px; padding: 20px 24px; margin-bottom: 14px;
        }
        .header {
            display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;
            border-bottom: 1px solid rgba(255,255,255,0.03); padding-bottom: 14px; margin-bottom: 14px;
        }
        .header .brand h1 { font-family: 'Orbitron', monospace; font-size: 20px; font-weight: 700; color: #fff; }
        .header .brand h1 .hl { color: #ffd700; }
        .header .brand .sub { font-size: 7px; font-family: 'Orbitron', monospace; color: #88ddff; letter-spacing: 4px; }
        .header .actions a {
            font-size: 8px; font-family: 'Orbitron', monospace;
            color: #88ddff; text-decoration: none;
            padding: 4px 14px; border: 1px solid rgba(255,255,255,0.03);
            border-radius: 30px; letter-spacing: 2px; transition: all 0.3s ease;
        }
        .header .actions a:hover { border-color: rgba(255,255,255,0.1); color: #fff; }
        .header .actions a.logout { border-color: rgba(255,51,85,0.1); color: #ff3355; }
        .header .actions a.logout:hover { border-color: rgba(255,51,85,0.3); color: #ff3355; }
        .info-grid {
            display: grid; grid-template-columns: 1fr 1fr;
            gap: 10px; margin-bottom: 14px;
        }
        .info-item { background: rgba(0,0,0,0.1); padding: 10px 14px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.02); }
        .info-item .label { font-size: 6px; font-family: 'Orbitron', monospace; color: #88ddff; letter-spacing: 2px; text-transform: uppercase; }
        .info-item .value { font-size: 16px; font-weight: 600; color: #fff; margin-top: 2px; }
        .info-item .value.gold { color: #ffd700; }
        .info-item .value.green { color: #00ff66; }
        .info-item .value.red { color: #ff3355; }
        .badge { font-size: 7px; font-family: 'Orbitron', monospace; padding: 2px 14px; border-radius: 30px; border: 1px solid rgba(255,255,255,0.05); display: inline-block; }
        .badge.active { border-color: rgba(0,255,102,0.2); color: #00ff66; }
        .badge.inactive { border-color: rgba(255,51,85,0.2); color: #ff3355; }
        .devices { margin-top: 10px; }
        .device-item { background: rgba(0,0,0,0.1); padding: 8px 14px; border-radius: 8px; margin-bottom: 6px; display: flex; justify-content: space-between; align-items: center; font-size: 10px; color: #88ddff; border: 1px solid rgba(255,255,255,0.02); }
        .device-item .id { font-family: 'Courier New', monospace; font-size: 9px; }
        .device-item .active-dot { width: 6px; height: 6px; border-radius: 50%; display: inline-block; }
        .device-item .active-dot.on { background: #00ff66; }
        .device-item .active-dot.off { background: #ff3355; }
        .device-item .current { color: #ffd700; font-size: 7px; font-family: 'Orbitron', monospace; }
        .footer { text-align: center; font-size: 6px; color: #88ddff; letter-spacing: 3px; margin-top: 10px; font-family: 'Orbitron', monospace; opacity: 0.3; }
        @media (max-width: 480px) {
            .info-grid { grid-template-columns: 1fr; }
            .header .brand h1 { font-size: 16px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <div class="header">
                <div class="brand">
                    <h1><span class="hl">👤 VIP</span> DASHBOARD</h1>
                    <div class="sub">premium · subscription</div>
                </div>
                <div class="actions">
                    <a href="{{ url_for('logout') }}" class="logout"><i class="fas fa-sign-out-alt"></i> logout</a>
                </div>
            </div>

            <div class="info-grid">
                <div class="info-item">
                    <div class="label"><i class="fas fa-user"></i> username</div>
                    <div class="value">{{ session.get('username') }}</div>
                </div>
                <div class="info-item">
                    <div class="label"><i class="fas fa-calendar-alt"></i> subscription</div>
                    <div class="value {% if days_left > 7 %}green{% elif days_left > 0 %}gold{% else %}red{% endif %}">
                        {% if days_left > 0 %}{{ days_left }} days left{% else %}expired{% endif %}
                    </div>
                </div>
                <div class="info-item">
                    <div class="label"><i class="fas fa-devices"></i> device limit</div>
                    <div class="value gold">{{ device_limit }}</div>
                </div>
                <div class="info-item">
                    <div class="label"><i class="fas fa-shield-alt"></i> status</div>
                    <div class="value"><span class="badge {{ 'active' if user.get('active', True) else 'inactive' }}">{{ 'ACTIVE' if user.get('active', True) else 'SUSPENDED' }}</span></div>
                </div>
            </div>

            <div class="devices">
                <div style="font-size:8px; font-family:'Orbitron',monospace; color:#88ddff; letter-spacing:2px; margin-bottom:8px;">
                    <i class="fas fa-devices"></i> active devices ({{ devices|length }})
                </div>
                {% if devices %}
                    {% for d in devices %}
                    <div class="device-item">
                        <span>
                            <span class="active-dot {{ 'on' if d.get('active', False) else 'off' }}"></span>
                            <span class="id">{{ d.get('device_id', '')[:12] }}...</span>
                        </span>
                        <span>
                            {% if d.get('device_id') == current_device %}
                            <span class="current"><i class="fas fa-check-circle"></i> current</span>
                            {% endif %}
                            <span style="font-size:7px; color:#88ddff;">{{ d.get('last_active', '')[:16] }}</span>
                        </span>
                    </div>
                    {% endfor %}
                {% else %}
                    <div style="color:#88ddff; font-size:10px; text-align:center; padding:10px;">no devices registered</div>
                {% endif %}
            </div>
        </div>

        <div class="footer">⚡ SAKIL BHAI · ENTERPRISE ⚡</div>
    </div>
</body>
</html>
'''

# ---- LOGOUT ----
@app.route('/logout')
def logout():
    username = session.get("username")
    device_id = session.get("device_id")
    if username and device_id:
        logout_device(username, device_id)
    session.clear()
    return redirect(url_for('login_page'))

# ---- API ----
@app.route('/api/device-status')
@user_required
def api_device_status():
    username = session.get("username")
    current = get_device_count(username, session.get("role", "user"))
    limit = get_device_limit(username, session.get("role", "user"))
    return jsonify({
        "username": username,
        "current_devices": current,
        "max_devices": limit,
        "can_add": current < limit
    })

# ===========================================================
# MAIN
# ===========================================================

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    print("="*70)
    print("👑 SAKIL BHAI - ENTERPRISE VIP MANAGEMENT PLATFORM v9.0")
    print("🔥 Multi-Role: Owner · Admin · Reseller · VIP User")
    print("📍 Device Limit Control · Custom Password Length")
    print("="*70)
    print(f"✅ Owner Panel:  http://0.0.0.0:{port}/owner")
    print(f"✅ Admin Panel:  http://0.0.0.0:{port}/admin")
    print(f"✅ Reseller:     http://0.0.0.0:{port}/reseller")
    print(f"✅ User Login:   http://0.0.0.0:{port}/login")
    print("="*70)
    print("🔑 Default Owner: sakil2026 / sakil2026")
    print("📁 Firebase: sakil-paid-hack-sell-1342007")
    print("="*70)
    
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
