#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
============================================
SAKIL BHAI - MULTI-PANEL SYSTEM v10.0
🔥 SEPARATE PANELS · SEPARATE LOGINS
📍 USER · RESELLER · MAIN ADMIN
============================================
"""

from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for, flash
import datetime
import hashlib
import secrets
import json
import os
import re
import requests
import urllib.parse
from functools import wraps
import time

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# ============================================
# FIREBASE CONFIG
# ============================================
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

USER_DATA_FILE = "user_firebase_fallback.json"

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

# ============================================
# DATA LAYER
# ============================================

def get_users():
    users = fb_get("users")
    if not users:
        users = {
            "sakil2026": {
                "password": hashlib.sha256("sakil2026".encode()).hexdigest(),
                "role": "main_admin",
                "active": True,
                "created": datetime.datetime.utcnow().isoformat(),
                "created_by": "system"
            }
        }
        fb_set("users", users)
    return users

def save_users(users):
    return fb_set("users", users)

def get_resellers():
    resellers = fb_get("resellers")
    if not resellers:
        resellers = {}
        fb_set("resellers", resellers)
    return resellers

def save_resellers(resellers):
    return fb_set("resellers", resellers)

def get_settings():
    settings = fb_get("settings")
    if not settings:
        settings = {
            "expiry_utc": "2026-12-31T23:59:59+00:00",
            "redirect_url": "https://wa.me/919242428894",
            "main_brand": "SAKIL BHAI"
        }
        fb_set("settings", settings)
    return settings

def save_settings(settings):
    return fb_set("settings", settings)

def get_user_expiry(username):
    users = get_users()
    if username not in users:
        return None
    expiry_str = users[username].get("expiry_utc")
    if not expiry_str:
        return None
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
        return None

def is_user_expired(username):
    rem = get_user_expiry(username)
    if rem is None:
        return False
    return rem <= 0

def get_system_remaining():
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

def is_system_expired():
    return get_system_remaining() <= 0

def verify_user(username, password):
    users = get_users()
    if username not in users:
        return False
    if not users[username].get("active", True):
        return False
    hashed = hashlib.sha256(password.encode()).hexdigest()
    return hashed == users[username].get("password", "")

def get_user_role(username):
    users = get_users()
    if username not in users:
        return None
    return users[username].get("role", "user")

def get_reseller_brand(reseller_username):
    resellers = get_resellers()
    if reseller_username in resellers:
        return resellers[reseller_username].get("brand_name", reseller_username.upper())
    return reseller_username.upper()

def get_brand_for_user(username):
    users = get_users()
    if username not in users:
        return "SAKIL BHAI"
    reseller_id = users[username].get("reseller_id")
    if reseller_id:
        return get_reseller_brand(reseller_id)
    settings = get_settings()
    return settings.get("main_brand", "SAKIL BHAI")

# ============================================
# DECORATORS
# ============================================

def user_session_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("user_auth"):
            return redirect(url_for('user_login_page'))
        username = session.get("user_username")
        if username and is_user_expired(username):
            session.clear()
            flash("Your subscription has expired.", "error")
            return redirect(url_for('user_login_page'))
        if is_system_expired():
            session.clear()
            return redirect(get_settings().get("redirect_url", "https://wa.me/919242428894"))
        return f(*args, **kwargs)
    return decorated

def reseller_session_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("reseller_auth"):
            return redirect(url_for('reseller_login_page'))
        username = session.get("reseller_username")
        if username and is_user_expired(username):
            session.clear()
            flash("Your reseller subscription has expired.", "error")
            return redirect(url_for('reseller_login_page'))
        if is_system_expired():
            session.clear()
            return redirect(get_settings().get("redirect_url", "https://wa.me/919242428894"))
        return f(*args, **kwargs)
    return decorated

def admin_session_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("admin_auth"):
            return redirect(url_for('admin_login_page'))
        if is_system_expired():
            session.clear()
            return redirect(get_settings().get("redirect_url", "https://wa.me/919242428894"))
        return f(*args, **kwargs)
    return decorated

# ============================================
# USER LOGIN PAGE
# ============================================
USER_LOGIN_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>USER LOGIN · SAKIL BHAI</title>
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
        .bg-animation {
            position: fixed;
            top: 0; left: 0; width: 100%; height: 100%;
            z-index: 0;
            overflow: hidden;
        }
        .bg-animation .orb {
            position: absolute;
            border-radius: 50%;
            filter: blur(80px);
            animation: orbFloat 20s ease-in-out infinite;
        }
        .bg-animation .orb:nth-child(1) {
            width: 400px; height: 400px;
            background: rgba(0, 255, 255, 0.03);
            top: -100px; left: -100px;
            animation-delay: 0s;
        }
        .bg-animation .orb:nth-child(2) {
            width: 500px; height: 500px;
            background: rgba(0, 255, 102, 0.02);
            bottom: -150px; right: -150px;
            animation-delay: -5s;
        }
        .bg-animation .orb:nth-child(3) {
            width: 300px; height: 300px;
            background: rgba(255, 0, 255, 0.015);
            top: 50%; left: 50%;
            transform: translate(-50%, -50%);
            animation-delay: -10s;
        }
        @keyframes orbFloat {
            0%, 100% { transform: translate(0, 0) scale(1); }
            33% { transform: translate(30px, -30px) scale(1.1); }
            66% { transform: translate(-20px, 20px) scale(0.9); }
        }
        .login-container {
            position: relative;
            z-index: 1;
            background: rgba(6, 6, 12, 0.92);
            border: 1px solid rgba(0, 255, 255, 0.15);
            border-radius: 24px;
            padding: 48px 40px;
            max-width: 420px;
            width: 92%;
            backdrop-filter: blur(40px);
            box-shadow: 0 0 80px rgba(0, 255, 255, 0.05), inset 0 0 80px rgba(0, 255, 255, 0.005);
            animation: containerIn 0.8s cubic-bezier(0.16, 1, 0.3, 1);
        }
        @keyframes containerIn {
            0% { opacity: 0; transform: translateY(30px) scale(0.96); }
            100% { opacity: 1; transform: translateY(0) scale(1); }
        }
        .login-container .brand-section {
            text-align: center;
            margin-bottom: 32px;
        }
        .login-container .brand-section .icon-wrap {
            display: inline-block;
            font-size: 32px;
            color: #00ffff;
            opacity: 0.5;
            margin-bottom: 4px;
        }
        .login-container .brand-section h1 {
            font-family: 'Orbitron', monospace;
            font-size: 22px;
            font-weight: 800;
            letter-spacing: 4px;
            color: #ffffff;
        }
        .login-container .brand-section h1 .highlight {
            color: #00ffff;
            text-shadow: 0 0 40px rgba(0, 255, 255, 0.2);
        }
        .login-container .brand-section .tagline {
            font-size: 9px;
            font-weight: 400;
            letter-spacing: 6px;
            color: #88ddff;
            text-transform: uppercase;
            margin-top: 2px;
            font-family: 'Orbitron', monospace;
        }
        .login-container .brand-section .divider {
            width: 40px;
            height: 1px;
            background: rgba(0, 255, 255, 0.3);
            margin: 10px auto 0;
        }
        .login-container .brand-section .panel-badge {
            display: inline-block;
            margin-top: 8px;
            font-size: 8px;
            font-family: 'Orbitron', monospace;
            color: #00ff66;
            letter-spacing: 4px;
            border: 1px solid rgba(0,255,102,0.2);
            padding: 2px 16px;
            border-radius: 30px;
        }
        .form-group { margin-bottom: 16px; }
        .form-group label {
            display: block;
            font-size: 9px;
            font-weight: 600;
            color: #88ddff;
            text-transform: uppercase;
            letter-spacing: 3px;
            margin-bottom: 6px;
            font-family: 'Orbitron', monospace;
        }
        .form-group label i { color: #00ffff; margin-right: 6px; }
        .form-group .input-wrap {
            display: flex;
            align-items: center;
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(0, 255, 255, 0.15);
            border-radius: 12px;
            transition: all 0.3s ease;
            overflow: hidden;
        }
        .form-group .input-wrap:focus-within {
            border-color: rgba(0, 255, 255, 0.6);
            box-shadow: 0 0 30px rgba(0, 255, 255, 0.05);
        }
        .form-group .input-wrap .prefix {
            padding: 12px 0 12px 16px;
            color: #88ddff;
            font-size: 13px;
            width: 38px;
            text-align: center;
            font-family: 'Orbitron', monospace;
        }
        .form-group .input-wrap .line {
            width: 1px;
            height: 20px;
            background: rgba(0, 255, 255, 0.1);
        }
        .form-group .input-wrap input {
            flex: 1;
            padding: 12px 16px;
            background: transparent;
            border: none;
            color: #ffffff;
            font-size: 15px;
            outline: none;
            font-family: 'Inter', sans-serif;
            font-weight: 400;
            letter-spacing: 0.5px;
        }
        .form-group .input-wrap input::placeholder {
            color: #88ddff;
            font-size: 13px;
            font-weight: 300;
        }
        .btn-login {
            width: 100%;
            padding: 14px;
            background: rgba(0, 255, 255, 0.05);
            border: 1px solid rgba(0, 255, 255, 0.2);
            border-radius: 12px;
            color: #88ddff;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            font-family: 'Orbitron', monospace;
            letter-spacing: 4px;
            transition: all 0.3s ease;
            text-transform: uppercase;
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 12px;
            margin-top: 4px;
        }
        .btn-login:hover {
            border-color: rgba(0, 255, 255, 0.5);
            color: #00ffff;
            box-shadow: 0 0 40px rgba(0, 255, 255, 0.05);
        }
        .btn-login i { font-size: 14px; color: #00ffff; }
        .error-text {
            color: #ff3355;
            font-size: 11px;
            padding: 6px 0;
            display: none;
            text-align: center;
            font-family: 'Orbitron', monospace;
            letter-spacing: 1px;
        }
        .error-text.show { display: block; animation: shake 0.4s ease; }
        @keyframes shake {
            0%, 100% { transform: translateX(0); }
            25% { transform: translateX(-4px); }
            75% { transform: translateX(4px); }
        }
        .status-bar {
            display: flex;
            justify-content: center;
            gap: 20px;
            margin-top: 18px;
            padding: 10px 14px;
            background: rgba(0, 0, 0, 0.15);
            border-radius: 10px;
            border: 1px solid rgba(0, 255, 255, 0.05);
        }
        .status-bar .item {
            font-size: 7px;
            font-weight: 400;
            color: #88ddff;
            letter-spacing: 2px;
            text-transform: uppercase;
            font-family: 'Orbitron', monospace;
            display: flex;
            align-items: center;
            gap: 4px;
        }
        .status-bar .item i { font-size: 8px; color: #00ffff; }
        .footer-text {
            text-align: center;
            font-size: 6px;
            color: #88ddff;
            letter-spacing: 3px;
            margin-top: 16px;
            font-family: 'Orbitron', monospace;
        }
        .flash-msg {
            padding: 8px 14px;
            border-radius: 8px;
            margin-bottom: 12px;
            font-size: 9px;
            font-family: 'Orbitron', monospace;
            letter-spacing: 1px;
            background: rgba(0, 255, 102, 0.02);
            border: 1px solid rgba(0, 255, 102, 0.05);
            color: #00ff66;
            text-align: center;
        }
        .flash-msg.error { border-color: rgba(255, 51, 85, 0.05); color: #ff3355; }
        .panel-links {
            margin-top: 14px;
            display: flex;
            justify-content: center;
            gap: 16px;
            flex-wrap: wrap;
        }
        .panel-links a {
            font-size: 7px;
            font-family: 'Orbitron', monospace;
            color: #88ddff;
            text-decoration: none;
            letter-spacing: 2px;
            padding: 3px 12px;
            border: 1px solid rgba(255,255,255,0.03);
            border-radius: 20px;
            transition: all 0.3s ease;
        }
        .panel-links a:hover {
            border-color: rgba(0,255,255,0.2);
            color: #00ffff;
        }
        .panel-links a.admin-link { border-color: rgba(255,215,0,0.05); color: #ffd700; }
        .panel-links a.admin-link:hover { border-color: rgba(255,215,0,0.2); color: #ffd700; }
        .panel-links a.reseller-link { border-color: rgba(0,255,102,0.05); color: #00ff66; }
        .panel-links a.reseller-link:hover { border-color: rgba(0,255,102,0.2); color: #00ff66; }
        @media (max-width: 480px) {
            .login-container { padding: 32px 22px; }
            .login-container .brand-section h1 { font-size: 18px; letter-spacing: 2px; }
            .status-bar { gap: 12px; flex-wrap: wrap; }
        }
    </style>
</head>
<body>
    <div class="bg-animation">
        <div class="orb"></div>
        <div class="orb"></div>
        <div class="orb"></div>
    </div>
    <div class="login-container">
        <div class="brand-section">
            <div class="icon-wrap"><i class="fas fa-user"></i></div>
            <h1><span class="highlight">USER</span> PANEL</h1>
            <div class="tagline">premium · number intelligence</div>
            <div class="panel-badge"><i class="fas fa-shield-halved"></i> user access</div>
            <div class="divider"></div>
        </div>
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% for category, message in messages %}
                <div class="flash-msg {{ category }}"><i class="fas fa-{% if category == 'error' %}exclamation-circle{% else %}check-circle{% endif %}"></i> {{ message }}</div>
            {% endfor %}
        {% endwith %}
        <form method="POST">
            <div class="form-group">
                <label><i class="fas fa-user"></i> username</label>
                <div class="input-wrap">
                    <div class="prefix"><i class="fas fa-user"></i></div>
                    <div class="line"></div>
                    <input type="text" name="username" placeholder="Enter username" required autofocus>
                </div>
            </div>
            <div class="form-group">
                <label><i class="fas fa-key"></i> password</label>
                <div class="input-wrap">
                    <div class="prefix"><i class="fas fa-lock"></i></div>
                    <div class="line"></div>
                    <input type="password" name="password" placeholder="Enter password" required>
                </div>
            </div>
            <div class="error-text" id="loginError">{{ error }}</div>
            <button type="submit" class="btn-login"><i class="fas fa-unlock-alt"></i> user login</button>
        </form>
        <div class="status-bar">
            <span class="item"><i class="fas fa-database"></i> firebase</span>
            <span class="item"><i class="fas fa-clock"></i> {{ remaining_minutes }}m</span>
            <span class="item"><i class="fas fa-shield-alt"></i> secure</span>
        </div>
        <div class="panel-links">
            <a href="{{ url_for('reseller_login_page') }}" class="reseller-link"><i class="fas fa-store"></i> reseller</a>
            <a href="{{ url_for('admin_login_page') }}" class="admin-link"><i class="fas fa-crown"></i> admin</a>
        </div>
        <div class="footer-text">⚡ sakil bhai · multi-panel system ⚡</div>
    </div>
    <script>
        document.querySelector('input[name="username"]').focus();
        document.querySelectorAll('input').forEach(el => {
            el.addEventListener('input', function() {
                document.getElementById('loginError').classList.remove('show');
            });
        });
    </script>
</body>
</html>
'''

# ============================================
# USER PANEL
# ============================================
USER_PANEL_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>{{ brand }} · USER PANEL</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;800;900&family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', sans-serif;
            background: #06060a;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            overflow-x: hidden;
            -webkit-user-select: none;
        }
        * { -webkit-user-select: none; -moz-user-select: none; -ms-user-select: none; user-select: none; }
        input, textarea { -webkit-user-select: text; -moz-user-select: text; -ms-user-select: text; user-select: text; }
        .bg-animation {
            position: fixed;
            top: 0; left: 0; width: 100%; height: 100%;
            z-index: 0;
            pointer-events: none;
            overflow: hidden;
        }
        .bg-animation .orb {
            position: absolute;
            border-radius: 50%;
            filter: blur(100px);
            animation: orbFloat 25s ease-in-out infinite;
        }
        .bg-animation .orb:nth-child(1) {
            width: 500px; height: 500px;
            background: rgba(0, 255, 255, 0.015);
            top: -150px; left: -150px;
        }
        .bg-animation .orb:nth-child(2) {
            width: 600px; height: 600px;
            background: rgba(0, 255, 102, 0.01);
            bottom: -200px; right: -200px;
            animation-delay: -8s;
        }
        .bg-animation .orb:nth-child(3) {
            width: 300px; height: 300px;
            background: rgba(255, 0, 255, 0.008);
            top: 50%; left: 50%;
            transform: translate(-50%, -50%);
            animation-delay: -15s;
        }
        @keyframes orbFloat {
            0%, 100% { transform: translate(0, 0) scale(1); }
            33% { transform: translate(40px, -40px) scale(1.1); }
            66% { transform: translate(-30px, 30px) scale(0.9); }
        }
        .session-bar {
            width: 100%; height: 2px; background: rgba(0,0,0,0.5);
            position: fixed; top: 0; left: 0; z-index: 1000;
        }
        .session-bar .fill {
            height: 100%; background: linear-gradient(90deg, #00ff66, #00ffff);
            width: 100%; transition: width 1s linear;
            box-shadow: 0 0 30px rgba(0,255,255,0.02);
        }
        .session-bar .fill.warning { background: linear-gradient(90deg, #FF9933, #ff3355); }
        .tricolor {
            width: 100%; height: 3px; display: flex;
            position: fixed; top: 2px; left: 0; z-index: 999;
        }
        .tricolor .saffron { width: 33.33%; background: #FF9933; }
        .tricolor .white { width: 33.33%; background: #FFFFFF; }
        .tricolor .green { width: 33.34%; background: #138808; }
        .top-bar {
            width: 100%; background: rgba(0,0,0,0.8); padding: 6px 0;
            margin-top: 5px; position: sticky; top: 5px; z-index: 100;
            border-bottom: 1px solid rgba(0,255,255,0.1);
            backdrop-filter: blur(20px);
        }
        .top-bar .container {
            max-width: 1200px; margin: 0 auto; padding: 0 16px;
            display: flex; justify-content: space-between; align-items: center;
            flex-wrap: wrap; gap: 6px;
        }
        .top-bar .left {
            font-size: 8px; font-family: 'Orbitron', monospace;
            color: #88ddff; letter-spacing: 3px;
        }
        .top-bar .left i { color: #00ffff; margin-right: 4px; }
        .top-bar .right {
            font-size: 8px; font-family: 'Orbitron', monospace;
            color: #88ddff; letter-spacing: 1px;
        }
        .top-bar .right i { color: #00ffff; margin-right: 4px; }
        .main-header {
            width: 100%; background: rgba(0,0,0,0.85); padding: 12px 0;
            border-bottom: 1px solid rgba(0,255,255,0.1);
            backdrop-filter: blur(20px);
        }
        .main-header .container {
            max-width: 1200px; margin: 0 auto; padding: 0 16px;
            display: flex; justify-content: space-between; align-items: center;
            flex-wrap: wrap; gap: 10px;
        }
        .main-header .brand {
            display: flex; align-items: center; gap: 12px;
        }
        .main-header .brand img {
            width: 40px; height: 40px; border-radius: 50%;
            border: 1px solid rgba(0,255,255,0.2);
            object-fit: cover; background: rgba(0,0,0,0.3);
            padding: 2px;
        }
        .main-header .brand .text h1 {
            font-family: 'Orbitron', monospace;
            font-size: 16px; font-weight: 700;
            color: #fff; letter-spacing: 2px;
        }
        .main-header .brand .text h1 .hl { color: #00ffff; }
        .main-header .brand .text .sub {
            font-size: 7px; font-family: 'Orbitron', monospace;
            color: #88ddff; letter-spacing: 4px;
            text-transform: uppercase;
        }
        .main-header .brand .text .sub i { color: #00ff66; font-size: 5px; margin-right: 3px; }
        .main-header .status {
            display: flex; align-items: center; gap: 10px;
            background: rgba(0,0,0,0.2); padding: 4px 14px;
            border-radius: 30px; border: 1px solid rgba(0,255,255,0.1);
        }
        .main-header .status .dot {
            width: 5px; height: 5px; border-radius: 50%;
            background: #00ff66; animation: pulse 1.5s infinite;
            box-shadow: 0 0 20px rgba(0,255,102,0.01);
        }
        @keyframes pulse { 0%,100%{opacity:1}50%{opacity:0.1} }
        .main-header .status span {
            font-size: 7px; font-family: 'Orbitron', monospace;
            color: #88ddff; letter-spacing: 2px;
        }
        .main-header .status .timer {
            font-size: 11px; font-weight: 600;
            color: #00ffff; font-family: 'Orbitron', monospace;
            padding: 1px 8px; border: 1px solid rgba(0,255,255,0.15);
            border-radius: 4px; background: rgba(0,255,255,0.05);
        }
        .main-header .status .role {
            font-size: 6px; font-family: 'Orbitron', monospace;
            padding: 1px 10px; border-radius: 30px;
            border: 1px solid rgba(255,255,255,0.05);
            color: #88ddff;
        }
        .main-header .status .role.user { border-color: rgba(0,255,102,0.2); color: #00ff66; }
        .main-container {
            max-width: 560px; width: 100%; padding: 18px 14px;
            margin: 16px 0 30px; position: relative; z-index: 1;
        }
        .card {
            background: rgba(6,6,12,0.94);
            border: 1px solid rgba(0,255,255,0.1);
            border-radius: 20px;
            overflow: hidden;
            backdrop-filter: blur(30px);
            box-shadow: 0 8px 60px rgba(0,0,0,0.6);
        }
        .card-header {
            padding: 18px 22px; text-align: center;
            border-bottom: 1px solid rgba(0,255,255,0.05);
            background: rgba(0,0,0,0.2);
        }
        .card-header .badge {
            font-size: 7px; font-family: 'Orbitron', monospace;
            color: #88ddff; letter-spacing: 4px;
            text-transform: uppercase;
            border: 1px solid rgba(0,255,255,0.1);
            padding: 2px 14px; border-radius: 30px;
            display: inline-block; margin-bottom: 6px;
        }
        .card-header .badge i { color: #ffd700; font-size: 6px; margin-right: 4px; }
        .card-header .credit-badge {
            font-size: 8px;
            font-family: 'Inter', sans-serif;
            color: #ffd700;
            letter-spacing: 2px;
            background: rgba(255, 215, 0, 0.05);
            border: 1px solid rgba(255, 215, 0, 0.1);
            padding: 4px 14px;
            border-radius: 30px;
            display: inline-block;
            margin-bottom: 8px;
        }
        .card-header .credit-badge i { color: #ffd700; margin-right: 6px; }
        .card-header img {
            width: 48px; height: 48px; border-radius: 50%;
            border: 1px solid rgba(0,255,255,0.1);
            object-fit: cover; margin: 0 auto 6px; display: block;
            background: rgba(0,0,0,0.3); padding: 2px;
        }
        .card-header h2 {
            font-family: 'Orbitron', monospace;
            font-size: 18px; font-weight: 700;
            color: #fff; letter-spacing: 2px;
        }
        .card-header h2 .hl { color: #00ffff; }
        .card-header .sub {
            font-size: 8px; font-family: 'Orbitron', monospace;
            color: #88ddff; letter-spacing: 4px;
            margin-top: 2px;
        }
        .card-header .sub i { color: #00ff66; font-size: 6px; margin-right: 4px; }
        .card-body { padding: 20px 22px; }
        .form-group { margin-bottom: 14px; }
        .form-group label {
            display: block; font-size: 8px; font-weight: 600;
            color: #88ddff; text-transform: uppercase;
            letter-spacing: 3px; margin-bottom: 4px;
            font-family: 'Orbitron', monospace;
        }
        .form-group label i { color: #00ffff; margin-right: 4px; font-size: 8px; }
        .input-wrap {
            display: flex; align-items: center;
            background: rgba(0,0,0,0.3);
            border: 1px solid rgba(0,255,255,0.1);
            border-radius: 12px; transition: all 0.3s ease;
            overflow: hidden;
        }
        .input-wrap:focus-within { border-color: rgba(0,255,255,0.4); }
        .input-wrap .code {
            padding: 10px 6px 10px 14px;
            color: #88ddff; font-size: 12px;
            font-family: 'Orbitron', monospace;
            border-right: 1px solid rgba(0,255,255,0.05);
        }
        .input-wrap input {
            flex: 1; padding: 10px 14px;
            background: transparent; border: none;
            color: #fff; font-size: 15px; outline: none;
            font-family: 'Inter', sans-serif; font-weight: 400;
            letter-spacing: 0.5px;
        }
        .input-wrap input::placeholder {
            color: #88ddff; font-size: 13px;
        }
        .status-line {
            display: flex; align-items: center; gap: 10px;
            padding: 2px 0 10px; font-size: 9px;
            color: #88ddff;
            font-family: 'Orbitron', monospace; letter-spacing: 1px;
        }
        .status-line .dot {
            width: 4px; height: 4px; border-radius: 50%;
            background: #00ff66; animation: pulse 1.5s infinite;
        }
        .status-line .dot.err { background: #ff3355; }
        .btn-execute {
            width: 100%; padding: 13px;
            background: rgba(0,255,255,0.05);
            border: 1px solid rgba(0,255,255,0.2);
            border-radius: 12px;
            color: #88ddff;
            font-size: 12px; font-weight: 600;
            cursor: pointer; font-family: 'Orbitron', monospace;
            letter-spacing: 4px; text-transform: uppercase;
            transition: all 0.3s ease;
            display: flex; justify-content: center; align-items: center;
            gap: 12px;
        }
        .btn-execute:hover {
            border-color: rgba(0,255,255,0.5);
            color: #00ffff;
        }
        .btn-execute:disabled { opacity: 0.2; cursor: not-allowed; }
        .btn-execute i { font-size: 13px; color: #00ffff; }
        .error-text {
            color: #ff3355;
            font-size: 10px; padding: 4px 0;
            display: none; font-family: 'Orbitron', monospace;
            letter-spacing: 1px;
        }
        .error-text.show { display: block; animation: shake 0.4s ease; }
        @keyframes shake { 0%,100%{transform:translateX(0)}25%{transform:translateX(-4px)}75%{transform:translateX(4px)} }
        .result-box {
            margin-top: 16px;
            border: 1px solid rgba(0,255,255,0.05);
            border-radius: 12px; overflow: hidden;
            display: none; background: rgba(0,0,0,0.1);
        }
        .result-box.show { display: block; animation: slideUp 0.4s ease; }
        @keyframes slideUp { 0%{opacity:0;transform:translateY(10px)}100%{opacity:1;transform:translateY(0)} }
        .result-header {
            padding: 8px 16px; display: flex;
            justify-content: space-between; align-items: center;
            border-bottom: 1px solid rgba(0,255,255,0.03);
            background: rgba(0,0,0,0.1);
        }
        .result-header .title {
            font-size: 8px; font-family: 'Orbitron', monospace;
            color: #88ddff; letter-spacing: 2px;
        }
        .result-header .title i { color: #00ffff; margin-right: 4px; }
        .result-header .count {
            font-size: 7px; font-family: 'Orbitron', monospace;
            color: #88ddff;
            background: rgba(0,0,0,0.1); padding: 1px 10px;
            border-radius: 20px;
        }
        .result-item {
            display: flex; padding: 8px 16px;
            border-bottom: 1px solid rgba(255,255,255,0.02);
        }
        .result-item:last-child { border-bottom: none; }
        .result-item .label {
            font-size: 8px; font-weight: 600; font-family: 'Orbitron', monospace;
            color: #88ddff; width: 30%;
            display: flex; align-items: center; gap: 6px;
            text-transform: uppercase; letter-spacing: 1px;
        }
        .result-item .label i { font-size: 10px; color: #00ffff; width: 14px; }
        .result-item .value {
            font-size: 12px; font-weight: 400;
            color: #ccddff; width: 70%;
            text-align: right; font-family: 'Inter', sans-serif;
            word-break: break-word;
        }
        .result-item .value.hl { color: #00ffff; font-weight: 500; }
        .result-item .value.gr { color: #00ff66; font-weight: 500; }
        .result-item .value.addr { font-size: 10px; color: #88ddff; line-height: 1.4; }
        .location-section {
            margin-top: 14px;
            border: 3px solid #00ff66;
            border-radius: 14px;
            overflow: hidden;
            display: none;
            background: rgba(0,0,0,0.1);
            box-shadow: 0 0 40px rgba(0, 255, 102, 0.08), inset 0 0 40px rgba(0, 255, 102, 0.02);
            transition: all 0.4s ease;
        }
        .location-section.show { display: block; animation: slideUp 0.5s ease; }
        .location-section.live { border-color: #ff0000 !important; box-shadow: 0 0 50px rgba(255, 0, 0, 0.15), inset 0 0 50px rgba(255, 0, 0, 0.03) !important; }
        .location-section.area { border-color: #ff0000 !important; box-shadow: 0 0 40px rgba(255, 0, 0, 0.08), inset 0 0 40px rgba(255, 0, 0, 0.02) !important; }
        .location-section .map-container {
            position: relative;
            width: 100%;
            padding-bottom: 56.25%;
            background: #0a0a1a;
            cursor: pointer;
        }
        .location-section .map-container iframe {
            position: absolute;
            top: 0; left: 0;
            width: 100%; height: 100%;
            border: none;
            border-radius: 0;
        }
        .location-section .map-container .location-badge {
            position: absolute;
            top: 12px;
            right: 12px;
            background: rgba(0,0,0,0.75);
            backdrop-filter: blur(10px);
            padding: 4px 14px;
            border-radius: 20px;
            font-size: 8px;
            font-family: 'Orbitron', monospace;
            color: #00ff66;
            border: 1px solid rgba(0,255,102,0.2);
            z-index: 10;
            letter-spacing: 1px;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .location-section .map-container .location-badge i { font-size: 10px; }
        .location-section .map-container .location-badge.live { color: #ff0000; border-color: rgba(255,0,0,0.3); animation: pulseBadge 1.5s ease-in-out infinite; }
        .location-section .map-container .location-badge.area { color: #ff0000; border-color: rgba(255,0,0,0.3); }
        @keyframes pulseBadge { 0%,100%{opacity:1}50%{opacity:0.6} }
        .location-section .map-label {
            padding: 8px 14px;
            font-size: 7px;
            font-family: 'Orbitron', monospace;
            color: #88ddff;
            letter-spacing: 2px;
            text-align: center;
            background: rgba(0,0,0,0.15);
            border-top: 1px solid rgba(0,255,255,0.03);
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 4px;
        }
        .location-section .map-label .hint i { color: #ff0000; margin-right: 4px; }
        .location-section .map-label .open-link {
            font-size: 7px;
            font-family: 'Orbitron', monospace;
            color: #00ffff;
            text-decoration: none;
            padding: 2px 12px;
            border: 1px solid rgba(0,255,255,0.1);
            border-radius: 20px;
            transition: all 0.3s ease;
        }
        .location-section .map-label .open-link:hover { background: rgba(0,255,255,0.05); border-color: rgba(0,255,255,0.3); }
        .result-item.location-item {
            border-left: 4px solid #00ff66;
            background: rgba(0,255,102,0.03);
            border-radius: 4px;
            margin: 2px 0;
            padding: 8px 16px;
        }
        .result-item.location-item .label i { color: #00ff66; }
        .result-item.location-item .value { color: #00ff66; font-weight: 500; }
        .result-item.location-item.live { border-left-color: #ff0000 !important; background: rgba(255,0,0,0.03) !important; }
        .result-item.location-item.live .label i { color: #ff0000 !important; }
        .result-item.location-item.live .value { color: #ff0000 !important; }
        .result-item.location-item.area { border-left-color: #ff0000 !important; background: rgba(255,0,0,0.03) !important; }
        .result-item.location-item.area .label i { color: #ff0000 !important; }
        .result-item.location-item.area .value { color: #ff0000 !important; }
        .badge-row {
            display: flex; justify-content: center; gap: 16px;
            padding: 10px 14px; margin-top: 12px;
            border: 1px solid rgba(0,255,255,0.03);
            border-radius: 10px; background: rgba(0,0,0,0.05);
            flex-wrap: wrap;
        }
        .badge-row .item {
            font-size: 7px; font-family: 'Orbitron', monospace;
            color: #88ddff; letter-spacing: 1px;
            display: flex; align-items: center; gap: 4px;
        }
        .badge-row .item i { font-size: 9px; color: #ff0000; }
        .social-row {
            margin-top: 12px; padding: 12px 16px;
            border: 1px solid rgba(0,255,255,0.05);
            border-radius: 10px; text-align: center;
            background: rgba(0,0,0,0.03);
        }
        .social-row .title {
            font-size: 7px; font-family: 'Orbitron', monospace;
            color: #88ddff; letter-spacing: 3px;
            text-transform: uppercase; margin-bottom: 8px;
        }
        .social-row .title i { color: #ffd700; font-size: 7px; margin-right: 4px; }
        .social-row .btns { display: flex; justify-content: center; gap: 10px; flex-wrap: wrap; }
        .social-row .btns a {
            font-size: 9px; font-family: 'Inter', sans-serif;
            color: #88ddff; text-decoration: none;
            padding: 4px 14px; border: 1px solid rgba(255,255,255,0.05);
            border-radius: 30px; transition: all 0.3s ease;
        }
        .social-row .btns a:hover { border-color: rgba(0,255,255,0.2); color: #00ffff; }
        .social-row .btns a i { margin-right: 4px; }
        .json-toggle {
            width: 100%; padding: 8px; margin-top: 10px;
            background: transparent; border: 1px solid rgba(255,255,255,0.05);
            border-radius: 8px; color: #88ddff;
            font-size: 7px; font-family: 'Orbitron', monospace;
            letter-spacing: 2px; cursor: pointer;
            transition: all 0.3s ease;
        }
        .json-toggle:hover { border-color: rgba(0,255,255,0.2); color: #00ffff; }
        .json-box {
            margin-top: 8px; background: rgba(0,0,0,0.2);
            border-radius: 8px; padding: 10px;
            font-family: 'Courier New', monospace; font-size: 8px;
            color: #88ddff; display: none;
            max-height: 150px; overflow: auto;
            white-space: pre-wrap; word-break: break-all;
            line-height: 1.5; border: 1px solid rgba(0,255,102,0.05);
        }
        .json-box.show { display: block; }
        .notice {
            margin-top: 10px; padding: 8px 12px;
            border: 1px solid rgba(255,215,0,0.05);
            border-radius: 8px; text-align: center;
            font-size: 6px; font-family: 'Orbitron', monospace;
            color: #88ddff; letter-spacing: 0.5px;
            line-height: 1.6; background: rgba(255,215,0,0.02);
        }
        .notice .w { color: #ff3355; }
        .notice .g { color: #ffd700; }
        .action-row {
            display: flex; justify-content: center; gap: 10px;
            margin-top: 12px; flex-wrap: wrap;
        }
        .action-row a {
            font-size: 8px; font-family: 'Orbitron', monospace;
            color: #88ddff; text-decoration: none;
            padding: 4px 16px; border: 1px solid rgba(255,255,255,0.05);
            border-radius: 30px; letter-spacing: 2px;
            transition: all 0.3s ease;
        }
        .action-row a:hover { border-color: rgba(0,255,255,0.2); color: #00ffff; }
        .action-row a.logout { border-color: rgba(255,51,85,0.1); color: #ff3355; }
        .action-row a.logout:hover { border-color: rgba(255,51,85,0.3); color: #ff3355; }
        .footer {
            width: 100%; background: rgba(0,0,0,0.85);
            border-top: 1px solid rgba(0,255,255,0.05);
            padding: 14px 0; margin-top: 10px;
            backdrop-filter: blur(20px);
        }
        .footer .container {
            max-width: 1200px; margin: 0 auto; padding: 0 16px;
            text-align: center;
        }
        .footer .links {
            display: flex; justify-content: center;
            gap: 16px; flex-wrap: wrap; margin-bottom: 8px;
        }
        .footer .links a {
            font-size: 7px; font-family: 'Orbitron', monospace;
            color: #88ddff; text-decoration: none;
            letter-spacing: 2px; transition: all 0.3s ease;
        }
        .footer .links a:hover { color: #00ffff; }
        .footer .links a i { margin-right: 3px; }
        .footer .copy {
            font-size: 6px; font-family: 'Orbitron', monospace;
            color: #88ddff; letter-spacing: 3px;
        }
        .footer .copy .b { color: #00ffff; }
        .footer .copy .gold { color: #ffd700; }
        .footer .tricolor {
            width: 100%; height: 2px; display: flex;
            margin-top: 10px;
        }
        .footer .tricolor .saffron { width: 33.33%; background: #FF9933; }
        .footer .tricolor .white { width: 33.33%; background: #FFFFFF; }
        .footer .tricolor .green { width: 33.34%; background: #138808; }
        ::-webkit-scrollbar { width: 3px; }
        ::-webkit-scrollbar-track { background: #06060a; }
        ::-webkit-scrollbar-thumb { background: rgba(0,255,255,0.05); border-radius: 10px; }
        @media (max-width: 480px) {
            .main-header .brand .text h1 { font-size: 13px; letter-spacing: 1px; }
            .main-header .brand img { width: 32px; height: 32px; }
            .main-header .status { padding: 3px 10px; }
            .main-header .status .timer { font-size: 9px; }
            .card-header h2 { font-size: 15px; }
            .card-body { padding: 14px 16px; }
            .result-item { flex-wrap: wrap; padding: 6px 12px; }
            .result-item .label { width: 100%; margin-bottom: 2px; }
            .result-item .value { width: 100%; text-align: left; }
            .main-container { padding: 12px 10px; }
            .badge-row { gap: 10px; }
            .location-section .map-container .location-badge {
                top: 8px; right: 8px;
                font-size: 6px;
                padding: 2px 10px;
            }
        }
    </style>
</head>
<body>
    <div class="session-bar"><div class="fill" id="sessionFill"></div></div>
    <div class="tricolor"><div class="saffron"></div><div class="white"></div><div class="green"></div></div>
    <div class="bg-animation"><div class="orb"></div><div class="orb"></div><div class="orb"></div></div>
    <div class="top-bar">
        <div class="container">
            <div class="left"><i class="fas fa-shield-halved"></i> DEV BY · {{ brand }}</div>
            <div class="right"><i class="fas fa-circle" style="color:#00ff66;font-size:5px;"></i> system active</div>
        </div>
    </div>
    <div class="main-header">
        <div class="container">
            <div class="brand">
                <img src="https://i.postimg.cc/1VBJWPhR/IMG-20260724-232723-958.webp" alt="{{ brand }}" draggable="false">
                <div class="text">
                    <h1><span class="hl">{{ brand }}</span></h1>
                    <div class="sub"><i class="fas fa-circle"></i> premium · number intelligence</div>
                </div>
            </div>
            <div class="status">
                <div class="dot"></div>
                <span>vip</span>
                <span class="timer" id="sessionTimer">--:--</span>
                <span class="role user">USER</span>
                <a href="{{ url_for('user_logout') }}" style="color:#88ddff; font-size:10px; text-decoration:none;">
                    <i class="fas fa-sign-out-alt"></i>
                </a>
            </div>
        </div>
    </div>
    <div class="main-container">
        <div class="card">
            <div class="card-header">
                <div class="badge"><i class="fas fa-crown"></i> premium · encrypted</div>
                <div class="credit-badge">
                    <i class="fas fa-star"></i> Powered by <strong style="color:#ffd700;">{{ brand }}</strong> <i class="fas fa-star"></i>
                </div>
                <img src="https://i.postimg.cc/1VBJWPhR/IMG-20260724-232723-958.webp" alt="{{ brand }}" draggable="false">
                <h2><span class="hl">number</span> information</h2>
                <div class="sub"><i class="fas fa-circle"></i> premium intelligence system</div>
            </div>
            <div class="card-body">
                <form id="trackForm">
                    <div class="form-group">
                        <label><i class="fas fa-phone"></i> enter 10-digit number</label>
                        <div class="input-wrap">
                            <span class="code">+91</span>
                            <input type="tel" id="phoneInput" placeholder="Enter phone number" maxlength="10" inputmode="numeric">
                        </div>
                    </div>
                    <div class="status-line">
                        <span class="dot" id="statusDot"></span>
                        <span id="statusText">system ready</span>
                    </div>
                    <div class="error-text" id="errorText">error</div>
                    <button type="submit" class="btn-execute" id="trackBtn">
                        <i class="fas fa-search"></i> execute search
                    </button>
                </form>
                <div class="result-box" id="resultBox">
                    <div class="result-header">
                        <span class="title"><i class="fas fa-file-alt"></i> intelligence data</span>
                        <span class="count"><i class="fas fa-database"></i> <span id="recordCount">0</span></span>
                    </div>
                    <div id="resultContent"></div>
                </div>
                <div class="location-section" id="locationSection">
                    <div class="map-container" id="mapContainer">
                        <iframe id="mapIframe" src="" allowfullscreen="" loading="lazy" referrerpolicy="no-referrer-when-downgrade"></iframe>
                        <div class="location-badge" id="locationBadge">
                            <i class="fas fa-satellite-dish"></i>
                            <span id="locationType">LIVE</span>
                        </div>
                    </div>
                    <div class="map-label">
                        <span class="hint"><i class="fas fa-map-pin"></i> <span id="locationLabel">Location</span></span>
                        <a href="#" id="openMapsLink" class="open-link" target="_blank">
                            <i class="fas fa-external-link-alt"></i> Google Maps
                        </a>
                    </div>
                </div>
                <div class="badge-row">
                    <span class="item"><i class="fas fa-lock"></i> ssl</span>
                    <span class="item"><i class="fas fa-shield-halved"></i> secure</span>
                    <span class="item"><i class="fas fa-check-circle"></i> verified</span>
                    <span class="item"><i class="fas fa-clock"></i> 24/7</span>
                </div>
                <div id="apiInfo" style="display:none; margin-top:10px; padding:8px 12px; background:rgba(0,0,0,0.05); border-radius:8px; display:flex; justify-content:center; gap:16px; flex-wrap:wrap; font-size:7px; color:#88ddff; border:1px solid rgba(255,255,255,0.03);"></div>
                <div class="social-row">
                    <div class="title"><i class="fas fa-share-alt"></i> connect with {{ brand }}</div>
                    <div class="btns">
                        <a href="https://youtube.com/@elitetv-vip-tv?si=Ye99V2pGV3zxfvXe" target="_blank"><i class="fab fa-youtube"></i> youtube</a>
                        <a href="https://www.instagram.com/__elite__sakil__20k7__?igsh=MXU4OWIyYXdnejFlMw==" target="_blank"><i class="fab fa-instagram"></i> instagram</a>
                        <a href="https://t.me/+r7naPOtOXOoxMGY1" target="_blank"><i class="fab fa-telegram-plane"></i> telegram</a>
                    </div>
                </div>
                <button class="json-toggle" onclick="toggleJson()">
                    <i class="fas fa-code"></i> view raw data
                </button>
                <div class="json-box" id="jsonBox"></div>
                <div class="notice">
                    <span class="w">⚠</span> this number information paid server hacking system is currently <span class="w">not working</span>.<br>
                    please <span class="g">buy new VIP subscription</span> to continue using this service.
                </div>
                <div class="action-row">
                    <a href="{{ url_for('user_logout') }}" class="logout"><i class="fas fa-sign-out-alt"></i> logout</a>
                </div>
            </div>
        </div>
    </div>
    <div class="footer">
        <div class="container">
            <div class="links">
                <a href="#"><i class="fas fa-shield-halved"></i> privacy</a>
                <a href="https://t.me/+r7naPOtOXOoxMGY1" target="_blank"><i class="fas fa-headset"></i> support</a>
                <a href="tel:+919242428894"><i class="fas fa-phone"></i> contact</a>
            </div>
            <div class="copy">⚡ 2026 <span class="b">{{ brand }}</span> · premium system ⚡</div>
            <div class="copy" style="font-size:5px; margin-top:4px; color:#ffd700; letter-spacing:2px;">
                <i class="fas fa-star"></i> exclusively powered by <strong>{{ brand }}</strong> <i class="fas fa-star"></i>
            </div>
            <div class="tricolor"><div class="saffron"></div><div class="white"></div><div class="green"></div></div>
        </div>
    </div>
    <script>
    let totalSeconds = {{ remaining_seconds }};
    let timerInterval = null;

    function formatTime(sec) {
        const m = Math.floor(sec / 60);
        const s = sec % 60;
        return String(m).padStart(2, '0') + ':' + String(s).padStart(2, '0');
    }

    function updateTimer() {
        const timerEl = document.getElementById('sessionTimer');
        const fillEl = document.getElementById('sessionFill');
        if (!timerEl) return;
        if (totalSeconds <= 0) {
            timerEl.textContent = 'expired';
            fillEl.style.width = '0%';
            fillEl.className = 'fill warning';
            window.location.href = 'https://wa.me/919242428894';
            return;
        }
        timerEl.textContent = formatTime(totalSeconds);
        const maxSec = 3600;
        const pct = Math.max(0, (totalSeconds / maxSec) * 100);
        fillEl.style.width = pct + '%';
        fillEl.className = pct < 20 ? 'fill warning' : 'fill';
        totalSeconds--;
    }

    if ({{ remaining_seconds }} > 0) {
        updateTimer();
        timerInterval = setInterval(updateTimer, 1000);
    } else {
        document.getElementById('sessionTimer').textContent = 'expired';
        window.location.href = 'https://wa.me/919242428894';
    }

    function toggleJson() {
        const box = document.getElementById('jsonBox');
        box.classList.toggle('show');
        if (box.classList.contains('show')) {
            box.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
    }

    function updateLocationMap(address, lat, lng, type) {
        const section = document.getElementById('locationSection');
        const iframe = document.getElementById('mapIframe');
        const label = document.getElementById('locationLabel');
        const openLink = document.getElementById('openMapsLink');
        const badge = document.getElementById('locationBadge');
        const locationType = document.getElementById('locationType');

        if (!address || address === 'N/A' || address === 'Unknown' || address === '') {
            section.classList.remove('show');
            section.classList.remove('live', 'area');
            return;
        }

        if (type === 'live') {
            locationType.textContent = '🔴 LIVE';
            badge.className = 'location-badge live';
            section.className = 'location-section show live';
        } else {
            locationType.textContent = '📍 AREA';
            badge.className = 'location-badge area';
            section.className = 'location-section show area';
        }

        let query = address;
        if (lat && lng) {
            query = `${lat},${lng}`;
        }
        const cleanAddress = encodeURIComponent(query);
        const mapUrl = `https://www.google.com/maps/embed/v1/place?key=AIzaSyBFw0Qbyq9zTFTd-tUY6dZWTgaQzuU17R8&q=${cleanAddress}&zoom=16&maptype=roadmap`;
        iframe.src = mapUrl;
        label.textContent = address.substring(0, 60) + (address.length > 60 ? '...' : '');
        openLink.href = `https://www.google.com/maps/search/?api=1&query=${cleanAddress}`;
        section.classList.add('show');
        setTimeout(() => {
            section.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }, 300);
    }

    async function callAPI(number) {
        try {
            const response = await fetch('/api/lookup', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ number: number })
            });
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return await response.json();
        } catch (error) {
            return { status: 'error', message: error.message };
        }
    }

    function displayResults(number, data) {
        const resultBox = document.getElementById('resultBox');
        const resultContent = document.getElementById('resultContent');
        const recordCount = document.getElementById('recordCount');
        const apiInfo = document.getElementById('apiInfo');
        const jsonBox = document.getElementById('jsonBox');
        const errorText = document.getElementById('errorText');
        const locationSection = document.getElementById('locationSection');

        locationSection.classList.remove('show', 'live', 'area');
        jsonBox.textContent = JSON.stringify(data, null, 2);

        if (data.status === 'error') {
            resultBox.classList.remove('show');
            errorText.textContent = '❌ ' + (data.message || 'API Error');
            errorText.classList.add('show');
            return;
        }

        if (data.result && data.result.length > 0) {
            const results = data.result;
            const totalRecords = results.length;
            recordCount.textContent = totalRecords;

            let html = '';
            const info = results[0];

            html += `<div class="result-item">
                <span class="label"><i class="fas fa-phone"></i> phone</span>
                <span class="value hl">${info.num || '+91 ' + number}</span>
            </div>`;
            html += `<div class="result-item">
                <span class="label"><i class="fas fa-user"></i> name</span>
                <span class="value hl">${info.name || 'N/A'}</span>
            </div>`;
            html += `<div class="result-item">
                <span class="label"><i class="fas fa-user-tie"></i> father</span>
                <span class="value">${info.fname || 'N/A'}</span>
            </div>`;
            html += `<div class="result-item">
                <span class="label"><i class="fas fa-id-card"></i> aadhaar</span>
                <span class="value gr">${info.aadhar || 'N/A'}</span>
            </div>`;

            const address = info.address || info.location || 'N/A';
            const hasLatLng = (info.lat && info.lng);
            const locationType = hasLatLng ? 'live' : 'area';
            const locationIcon = hasLatLng ? 'fa-satellite-dish' : 'fa-map-pin';
            const locationColor = '#ff0000';
            const locationClass = hasLatLng ? 'live' : 'area';

            html += `<div class="result-item location-item ${locationClass}">
                <span class="label"><i class="fas ${locationIcon}" style="color:${locationColor};"></i> location</span>
                <span class="value addr" id="addressValue">${address}</span>
                <span style="font-size:6px; font-family:'Orbitron',monospace; color:#ff0000; margin-left:8px; border:1px solid #ff000040; padding:1px 8px; border-radius:10px; background:#ff000010;">
                    ${hasLatLng ? '🔴 LIVE' : '📍 AREA'}
                </span>
            </div>`;

            html += `<div class="result-item">
                <span class="label"><i class="fas fa-signal"></i> circle</span>
                <span class="value">${info.circle || 'N/A'}</span>
            </div>`;
            if (info.alt) {
                html += `<div class="result-item">
                    <span class="label"><i class="fas fa-phone-plus"></i> alternate</span>
                    <span class="value">${info.alt}</span>
                </div>`;
            }
            if (info.email) {
                html += `<div class="result-item">
                    <span class="label"><i class="fas fa-envelope"></i> email</span>
                    <span class="value">${info.email}</span>
                </div>`;
            }

            resultContent.innerHTML = html;
            resultBox.classList.add('show');
            errorText.classList.remove('show');

            if (address && address !== 'N/A') {
                const lat = info.lat || null;
                const lng = info.lng || null;
                updateLocationMap(address, lat, lng, locationType);
            }

            let apiHtml = '';
            if (data.BUY_API) apiHtml += `<span><i class="fas fa-shopping-cart" style="color:#00ffff;"></i> buy: <strong style="color:#00ffff;">${data.BUY_API}</strong></span>`;
            if (data.SUPPORT) apiHtml += `<span><i class="fas fa-headset" style="color:#00ffff;"></i> support: <strong style="color:#00ffff;">${data.SUPPORT}</strong></span>`;
            if (apiHtml) {
                apiInfo.innerHTML = apiHtml;
                apiInfo.style.display = 'flex';
            }
        } else {
            resultBox.classList.remove('show');
            errorText.textContent = '❌ no data found';
            errorText.classList.add('show');
        }
    }

    async function searchNumber() {
        const input = document.getElementById('phoneInput');
        const number = input.value.trim();
        const statusText = document.getElementById('statusText');
        const statusDot = document.getElementById('statusDot');
        const trackBtn = document.getElementById('trackBtn');
        const errorText = document.getElementById('errorText');

        if (!number || number.length !== 10 || !/^[0-9]{10}$/.test(number)) {
            errorText.textContent = '⚠️ enter valid 10-digit number';
            errorText.classList.add('show');
            return;
        }

        errorText.classList.remove('show');
        trackBtn.disabled = true;
        trackBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> searching...';
        statusText.textContent = 'searching...';
        statusDot.className = 'dot';

        document.getElementById('resultBox').classList.remove('show');
        document.getElementById('apiInfo').style.display = 'none';
        document.getElementById('locationSection').classList.remove('show');
        document.getElementById('locationSection').classList.remove('live', 'area');

        try {
            const data = await callAPI(number);
            displayResults(number, data);

            if (data.status === 'success' && data.result && data.result.length > 0) {
                statusText.textContent = '✅ completed (' + data.result.length + ' records)';
                statusDot.className = 'dot';
            } else if (data.status === 'error') {
                statusText.textContent = '❌ api error';
                statusDot.className = 'dot err';
            } else {
                statusText.textContent = '❌ no data';
                statusDot.className = 'dot err';
            }
        } catch (error) {
            statusText.textContent = '❌ connection error';
            statusDot.className = 'dot err';
            errorText.textContent = '❌ network error. try again.';
            errorText.classList.add('show');
        }

        trackBtn.disabled = false;
        trackBtn.innerHTML = '<i class="fas fa-search"></i> execute search';
    }

    document.getElementById('trackForm').addEventListener('submit', function(e) {
        e.preventDefault();
        searchNumber();
    });

    document.getElementById('phoneInput').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') { e.preventDefault(); searchNumber(); }
    });

    document.getElementById('phoneInput').addEventListener('input', function(e) {
        this.value = this.value.replace(/[^0-9]/g, '');
    });

    document.addEventListener('contextmenu', function(e) { e.preventDefault(); return false; });
    document.addEventListener('keydown', function(e) {
        if (e.ctrlKey && ['c','v','s','p','u'].includes(e.key)) { e.preventDefault(); return false; }
        if (e.key === 'F12') { e.preventDefault(); return false; }
    });
    document.addEventListener('dragstart', function(e) { e.preventDefault(); return false; });

    document.addEventListener('DOMContentLoaded', function() {
        console.log('🔥 {{ brand }} USER SYSTEM READY');
        console.log('📱 Enter a 10-digit number and click search');
    });
    </script>
</body>
</html>
'''

# ============================================
# RESELLER LOGIN PAGE
# ============================================
RESELLER_LOGIN_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>RESELLER LOGIN · SAKIL BHAI</title>
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
        .bg-animation {
            position: fixed;
            top: 0; left: 0; width: 100%; height: 100%;
            z-index: 0;
            overflow: hidden;
        }
        .bg-animation .orb {
            position: absolute;
            border-radius: 50%;
            filter: blur(80px);
            animation: orbFloat 20s ease-in-out infinite;
        }
        .bg-animation .orb:nth-child(1) {
            width: 400px; height: 400px;
            background: rgba(255, 215, 0, 0.03);
            top: -100px; left: -100px;
            animation-delay: 0s;
        }
        .bg-animation .orb:nth-child(2) {
            width: 500px; height: 500px;
            background: rgba(255, 215, 0, 0.02);
            bottom: -150px; right: -150px;
            animation-delay: -5s;
        }
        .bg-animation .orb:nth-child(3) {
            width: 300px; height: 300px;
            background: rgba(255, 215, 0, 0.015);
            top: 50%; left: 50%;
            transform: translate(-50%, -50%);
            animation-delay: -10s;
        }
        @keyframes orbFloat {
            0%, 100% { transform: translate(0, 0) scale(1); }
            33% { transform: translate(30px, -30px) scale(1.1); }
            66% { transform: translate(-20px, 20px) scale(0.9); }
        }
        .login-container {
            position: relative;
            z-index: 1;
            background: rgba(6, 6, 12, 0.92);
            border: 1px solid rgba(255, 215, 0, 0.15);
            border-radius: 24px;
            padding: 48px 40px;
            max-width: 420px;
            width: 92%;
            backdrop-filter: blur(40px);
            box-shadow: 0 0 80px rgba(255, 215, 0, 0.05), inset 0 0 80px rgba(255, 215, 0, 0.005);
            animation: containerIn 0.8s cubic-bezier(0.16, 1, 0.3, 1);
        }
        @keyframes containerIn {
            0% { opacity: 0; transform: translateY(30px) scale(0.96); }
            100% { opacity: 1; transform: translateY(0) scale(1); }
        }
        .login-container .brand-section {
            text-align: center;
            margin-bottom: 32px;
        }
        .login-container .brand-section .icon-wrap {
            display: inline-block;
            font-size: 32px;
            color: #ffd700;
            opacity: 0.5;
            margin-bottom: 4px;
        }
        .login-container .brand-section h1 {
            font-family: 'Orbitron', monospace;
            font-size: 22px;
            font-weight: 800;
            letter-spacing: 4px;
            color: #ffffff;
        }
        .login-container .brand-section h1 .highlight {
            color: #ffd700;
            text-shadow: 0 0 40px rgba(255, 215, 0, 0.2);
        }
        .login-container .brand-section .tagline {
            font-size: 9px;
            font-weight: 400;
            letter-spacing: 6px;
            color: #88ddff;
            text-transform: uppercase;
            margin-top: 2px;
            font-family: 'Orbitron', monospace;
        }
        .login-container .brand-section .divider {
            width: 40px;
            height: 1px;
            background: rgba(255, 215, 0, 0.3);
            margin: 10px auto 0;
        }
        .login-container .brand-section .panel-badge {
            display: inline-block;
            margin-top: 8px;
            font-size: 8px;
            font-family: 'Orbitron', monospace;
            color: #ffd700;
            letter-spacing: 4px;
            border: 1px solid rgba(255,215,0,0.2);
            padding: 2px 16px;
            border-radius: 30px;
        }
        .form-group { margin-bottom: 16px; }
        .form-group label {
            display: block;
            font-size: 9px;
            font-weight: 600;
            color: #88ddff;
            text-transform: uppercase;
            letter-spacing: 3px;
            margin-bottom: 6px;
            font-family: 'Orbitron', monospace;
        }
        .form-group label i { color: #ffd700; margin-right: 6px; }
        .form-group .input-wrap {
            display: flex;
            align-items: center;
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(255, 215, 0, 0.15);
            border-radius: 12px;
            transition: all 0.3s ease;
            overflow: hidden;
        }
        .form-group .input-wrap:focus-within {
            border-color: rgba(255, 215, 0, 0.6);
            box-shadow: 0 0 30px rgba(255, 215, 0, 0.05);
        }
        .form-group .input-wrap .prefix {
            padding: 12px 0 12px 16px;
            color: #88ddff;
            font-size: 13px;
            width: 38px;
            text-align: center;
            font-family: 'Orbitron', monospace;
        }
        .form-group .input-wrap .line {
            width: 1px;
            height: 20px;
            background: rgba(255, 215, 0, 0.1);
        }
        .form-group .input-wrap input {
            flex: 1;
            padding: 12px 16px;
            background: transparent;
            border: none;
            color: #ffffff;
            font-size: 15px;
            outline: none;
            font-family: 'Inter', sans-serif;
            font-weight: 400;
            letter-spacing: 0.5px;
        }
        .form-group .input-wrap input::placeholder {
            color: #88ddff;
            font-size: 13px;
            font-weight: 300;
        }
        .btn-login {
            width: 100%;
            padding: 14px;
            background: rgba(255, 215, 0, 0.05);
            border: 1px solid rgba(255, 215, 0, 0.2);
            border-radius: 12px;
            color: #88ddff;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            font-family: 'Orbitron', monospace;
            letter-spacing: 4px;
            transition: all 0.3s ease;
            text-transform: uppercase;
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 12px;
            margin-top: 4px;
        }
        .btn-login:hover {
            border-color: rgba(255, 215, 0, 0.5);
            color: #ffd700;
            box-shadow: 0 0 40px rgba(255, 215, 0, 0.05);
        }
        .btn-login i { font-size: 14px; color: #ffd700; }
        .error-text {
            color: #ff3355;
            font-size: 11px;
            padding: 6px 0;
            display: none;
            text-align: center;
            font-family: 'Orbitron', monospace;
            letter-spacing: 1px;
        }
        .error-text.show { display: block; animation: shake 0.4s ease; }
        @keyframes shake {
            0%, 100% { transform: translateX(0); }
            25% { transform: translateX(-4px); }
            75% { transform: translateX(4px); }
        }
        .status-bar {
            display: flex;
            justify-content: center;
            gap: 20px;
            margin-top: 18px;
            padding: 10px 14px;
            background: rgba(0, 0, 0, 0.15);
            border-radius: 10px;
            border: 1px solid rgba(255, 215, 0, 0.05);
        }
        .status-bar .item {
            font-size: 7px;
            font-weight: 400;
            color: #88ddff;
            letter-spacing: 2px;
            text-transform: uppercase;
            font-family: 'Orbitron', monospace;
            display: flex;
            align-items: center;
            gap: 4px;
        }
        .status-bar .item i { font-size: 8px; color: #ffd700; }
        .footer-text {
            text-align: center;
            font-size: 6px;
            color: #88ddff;
            letter-spacing: 3px;
            margin-top: 16px;
            font-family: 'Orbitron', monospace;
        }
        .flash-msg {
            padding: 8px 14px;
            border-radius: 8px;
            margin-bottom: 12px;
            font-size: 9px;
            font-family: 'Orbitron', monospace;
            letter-spacing: 1px;
            background: rgba(0, 255, 102, 0.02);
            border: 1px solid rgba(0, 255, 102, 0.05);
            color: #00ff66;
            text-align: center;
        }
        .flash-msg.error { border-color: rgba(255, 51, 85, 0.05); color: #ff3355; }
        .panel-links {
            margin-top: 14px;
            display: flex;
            justify-content: center;
            gap: 16px;
            flex-wrap: wrap;
        }
        .panel-links a {
            font-size: 7px;
            font-family: 'Orbitron', monospace;
            color: #88ddff;
            text-decoration: none;
            letter-spacing: 2px;
            padding: 3px 12px;
            border: 1px solid rgba(255,255,255,0.03);
            border-radius: 20px;
            transition: all 0.3s ease;
        }
        .panel-links a:hover {
            border-color: rgba(255,215,0,0.2);
            color: #ffd700;
        }
        .panel-links a.user-link { border-color: rgba(0,255,255,0.05); color: #00ffff; }
        .panel-links a.user-link:hover { border-color: rgba(0,255,255,0.2); color: #00ffff; }
        .panel-links a.admin-link { border-color: rgba(255,215,0,0.05); color: #ffd700; }
        .panel-links a.admin-link:hover { border-color: rgba(255,215,0,0.2); color: #ffd700; }
        @media (max-width: 480px) {
            .login-container { padding: 32px 22px; }
            .login-container .brand-section h1 { font-size: 18px; letter-spacing: 2px; }
            .status-bar { gap: 12px; flex-wrap: wrap; }
        }
    </style>
</head>
<body>
    <div class="bg-animation">
        <div class="orb"></div>
        <div class="orb"></div>
        <div class="orb"></div>
    </div>
    <div class="login-container">
        <div class="brand-section">
            <div class="icon-wrap"><i class="fas fa-store"></i></div>
            <h1><span class="highlight">RESELLER</span> PANEL</h1>
            <div class="tagline">premium · reseller management</div>
            <div class="panel-badge"><i class="fas fa-shield-halved"></i> reseller access</div>
            <div class="divider"></div>
        </div>
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% for category, message in messages %}
                <div class="flash-msg {{ category }}"><i class="fas fa-{% if category == 'error' %}exclamation-circle{% else %}check-circle{% endif %}"></i> {{ message }}</div>
            {% endfor %}
        {% endwith %}
        <form method="POST">
            <div class="form-group">
                <label><i class="fas fa-user"></i> username</label>
                <div class="input-wrap">
                    <div class="prefix"><i class="fas fa-user"></i></div>
                    <div class="line"></div>
                    <input type="text" name="username" placeholder="Enter reseller username" required autofocus>
                </div>
            </div>
            <div class="form-group">
                <label><i class="fas fa-key"></i> password</label>
                <div class="input-wrap">
                    <div class="prefix"><i class="fas fa-lock"></i></div>
                    <div class="line"></div>
                    <input type="password" name="password" placeholder="Enter password" required>
                </div>
            </div>
            <div class="error-text" id="loginError">{{ error }}</div>
            <button type="submit" class="btn-login"><i class="fas fa-unlock-alt"></i> reseller login</button>
        </form>
        <div class="status-bar">
            <span class="item"><i class="fas fa-database"></i> firebase</span>
            <span class="item"><i class="fas fa-clock"></i> {{ remaining_minutes }}m</span>
            <span class="item"><i class="fas fa-shield-alt"></i> secure</span>
        </div>
        <div class="panel-links">
            <a href="{{ url_for('user_login_page') }}" class="user-link"><i class="fas fa-user"></i> user</a>
            <a href="{{ url_for('admin_login_page') }}" class="admin-link"><i class="fas fa-crown"></i> admin</a>
        </div>
        <div class="footer-text">⚡ sakil bhai · multi-panel system ⚡</div>
    </div>
    <script>
        document.querySelector('input[name="username"]').focus();
        document.querySelectorAll('input').forEach(el => {
            el.addEventListener('input', function() {
                document.getElementById('loginError').classList.remove('show');
            });
        });
    </script>
</body>
</html>
'''

# ============================================
# RESELLER PANEL
# ============================================
RESELLER_PANEL_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ brand }} · RESELLER PANEL</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;800;900&family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', sans-serif;
            background: #06060a;
            min-height: 100vh;
            padding: 16px;
        }
        .container { max-width: 1100px; margin: 0 auto; }
        .header {
            background: rgba(6,6,12,0.95); border: 1px solid rgba(255,215,0,0.1);
            border-radius: 16px; padding: 16px 20px; margin-bottom: 16px;
            display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;
            backdrop-filter: blur(20px);
        }
        .header .title { display: flex; align-items: center; gap: 10px; }
        .header .title i { font-size: 24px; color: #ffd700; opacity: 0.5; }
        .header .title h1 {
            font-family: 'Orbitron', monospace; font-size: 18px; font-weight: 700;
            color: #fff; letter-spacing: 2px;
        }
        .header .title h1 .hl { color: #ffd700; }
        .header .title .sub {
            font-size: 7px; font-family: 'Orbitron', monospace;
            color: #88ddff; letter-spacing: 3px;
        }
        .header .actions { display: flex; gap: 8px; }
        .header .actions a {
            font-size: 8px; font-family: 'Orbitron', monospace;
            color: #88ddff; text-decoration: none;
            padding: 4px 14px; border: 1px solid rgba(255,255,255,0.05);
            border-radius: 30px; letter-spacing: 2px; transition: all 0.3s ease;
        }
        .header .actions a:hover { border-color: rgba(255,215,0,0.2); color: #ffd700; }
        .header .actions a.logout { border-color: rgba(255,51,85,0.1); color: #ff3355; }
        .header .actions a.logout:hover { border-color: rgba(255,51,85,0.3); color: #ff3355; }
        .card {
            background: rgba(6,6,12,0.92); border: 1px solid rgba(255,255,255,0.03);
            border-radius: 14px; padding: 16px 20px; margin-bottom: 14px;
            backdrop-filter: blur(20px);
        }
        .card .card-title {
            font-size: 8px; font-family: 'Orbitron', monospace;
            color: #88ddff; letter-spacing: 3px;
            text-transform: uppercase; margin-bottom: 12px;
            display: flex; align-items: center; gap: 6px;
        }
        .card .card-title i { color: #ffd700; font-size: 11px; }
        .stats {
            display: grid; grid-template-columns: repeat(auto-fit, minmax(90px, 1fr));
            gap: 8px; margin-bottom: 14px;
        }
        .stat-box {
            background: rgba(0,0,0,0.15); border: 1px solid rgba(255,255,255,0.03);
            border-radius: 10px; padding: 10px 12px; text-align: center;
        }
        .stat-box .num {
            font-family: 'Orbitron', monospace; font-size: 20px;
            font-weight: 700; color: #fff;
        }
        .stat-box .num.green { color: #00ff66; }
        .stat-box .num.cyan { color: #00ffff; }
        .stat-box .num.gold { color: #ffd700; }
        .stat-box .num.red { color: #ff3355; }
        .stat-box .label {
            font-size: 6px; font-family: 'Orbitron', monospace;
            color: #88ddff; letter-spacing: 2px;
            text-transform: uppercase; margin-top: 2px;
        }
        .table-wrap { overflow-x: auto; }
        table { width: 100%; border-collapse: collapse; font-size: 11px; }
        thead th {
            font-size: 7px; font-family: 'Orbitron', monospace;
            color: #88ddff; letter-spacing: 2px;
            text-transform: uppercase; padding: 6px 8px;
            border-bottom: 1px solid rgba(255,255,255,0.03);
            text-align: left;
        }
        tbody td {
            color: #ccddff; padding: 6px 8px;
            border-bottom: 1px solid rgba(255,255,255,0.02);
            vertical-align: middle; font-size: 10px;
        }
        .badge {
            font-size: 6px; font-family: 'Orbitron', monospace;
            padding: 1px 10px; border-radius: 30px;
            border: 1px solid rgba(255,255,255,0.03);
            color: #88ddff;
        }
        .badge.active { border-color: rgba(0,255,102,0.2); color: #00ff66; }
        .badge.inactive { border-color: rgba(255,51,85,0.2); color: #ff3355; }
        .badge.expired { border-color: rgba(255,51,85,0.2); color: #ff3355; }
        .actions-cell { display: flex; gap: 4px; flex-wrap: wrap; }
        .actions-cell a {
            font-size: 7px; font-family: 'Orbitron', monospace;
            color: #88ddff; text-decoration: none;
            padding: 1px 8px; border: 1px solid rgba(255,255,255,0.03);
            border-radius: 4px; transition: all 0.3s ease;
        }
        .actions-cell a:hover { border-color: rgba(255,215,0,0.2); color: #ffd700; }
        .actions-cell a.del:hover { border-color: rgba(255,51,85,0.2); color: #ff3355; }
        .add-form { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
        .add-form input, .add-form select {
            padding: 6px 12px; background: rgba(0,0,0,0.2);
            border: 1px solid rgba(0,255,255,0.05); border-radius: 8px;
            color: #fff; font-size: 12px; outline: none;
            font-family: 'Inter', sans-serif; flex: 1; min-width: 100px;
        }
        .add-form input:focus, .add-form select:focus { border-color: rgba(255,215,0,0.15); }
        .add-form input::placeholder { color: #88ddff; }
        .add-form select option { background: #0a0a1a; color: #fff; }
        .add-form .btn-add {
            padding: 6px 18px; background: rgba(255,215,0,0.03);
            border: 1px solid rgba(255,215,0,0.05); border-radius: 8px;
            color: #88ddff; font-family: 'Orbitron', monospace;
            font-size: 9px; letter-spacing: 2px; cursor: pointer;
            transition: all 0.3s ease;
        }
        .add-form .btn-add:hover { border-color: rgba(255,215,0,0.2); color: #ffd700; }
        .brand-form { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
        .brand-form input {
            padding: 6px 12px; background: rgba(0,0,0,0.2);
            border: 1px solid rgba(255,215,0,0.05); border-radius: 8px;
            color: #fff; font-size: 12px; outline: none;
            font-family: 'Inter', sans-serif; flex: 1; min-width: 150px;
        }
        .brand-form input:focus { border-color: rgba(255,215,0,0.15); }
        .brand-form .btn-brand {
            padding: 6px 18px; background: rgba(255,215,0,0.03);
            border: 1px solid rgba(255,215,0,0.05); border-radius: 8px;
            color: #88ddff; font-family: 'Orbitron', monospace;
            font-size: 9px; letter-spacing: 2px; cursor: pointer;
            transition: all 0.3s ease;
        }
        .brand-form .btn-brand:hover { border-color: rgba(255,215,0,0.2); color: #ffd700; }
        .flash {
            padding: 8px 14px; border-radius: 8px; margin-bottom: 12px;
            font-size: 10px; font-family: 'Orbitron', monospace;
            letter-spacing: 1px; display: flex; align-items: center; gap: 8px;
        }
        .flash.success { background: rgba(0,255,102,0.02); border: 1px solid rgba(0,255,102,0.05); color: #00ff66; }
        .flash.error { background: rgba(255,51,85,0.02); border: 1px solid rgba(255,51,85,0.05); color: #ff3355; }
        .empty { text-align: center; color: #88ddff; padding: 16px; font-size: 10px; font-family: 'Orbitron', monospace; letter-spacing: 2px; }
        .footer-text { text-align: center; font-size: 6px; color: #88ddff; letter-spacing: 3px; margin-top: 10px; font-family: 'Orbitron', monospace; }
        .expiry-input { padding: 6px 12px; background: rgba(0,0,0,0.2); border: 1px solid rgba(0,255,255,0.05); border-radius: 8px; color: #fff; font-size: 11px; outline: none; font-family: 'Inter', sans-serif; }
        .expiry-input:focus { border-color: rgba(255,215,0,0.15); }
        @media (max-width: 600px) {
            .header .title h1 { font-size: 15px; }
            .stats { grid-template-columns: repeat(2, 1fr); }
            .add-form { flex-direction: column; }
            .add-form input, .add-form select, .add-form .btn-add { width: 100%; }
            .brand-form { flex-direction: column; }
            .brand-form input, .brand-form .btn-brand { width: 100%; }
            .card { padding: 12px 14px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="title">
                <i class="fas fa-store"></i>
                <div>
                    <h1><span class="hl">{{ brand }}</span> · RESELLER</h1>
                    <div class="sub">premium · reseller control panel</div>
                </div>
            </div>
            <div class="actions">
                <a href="{{ url_for('reseller_dashboard') }}"><i class="fas fa-arrow-left"></i> refresh</a>
                <a href="{{ url_for('reseller_logout') }}" class="logout"><i class="fas fa-sign-out-alt"></i> logout</a>
            </div>
        </div>

        {% with messages = get_flashed_messages(with_categories=true) %}
            {% for category, message in messages %}
                <div class="flash {{ category }}"><i class="fas fa-{% if category == 'success' %}check-circle{% else %}exclamation-circle{% endif %}"></i> {{ message }}</div>
            {% endfor %}
        {% endwith %}

        <div class="stats">
            <div class="stat-box"><div class="num green">{{ stats.total_users }}</div><div class="label">total users</div></div>
            <div class="stat-box"><div class="num cyan">{{ stats.active_users }}</div><div class="label">active</div></div>
            <div class="stat-box"><div class="num red">{{ stats.inactive_users }}</div><div class="label">inactive / expired</div></div>
            <div class="stat-box"><div class="num gold">{{ stats.online_users }}</div><div class="label">online now</div></div>
        </div>

        <!-- Brand Settings -->
        <div class="card">
            <div class="card-title"><i class="fas fa-tag"></i> brand settings</div>
            <form method="POST" action="{{ url_for('reseller_update_brand') }}" class="brand-form">
                <input type="text" name="brand_name" value="{{ brand }}" placeholder="Your brand name" required>
                <button type="submit" class="btn-brand"><i class="fas fa-pen"></i> update brand</button>
            </form>
            <div style="font-size:7px; color:#88ddff; margin-top:6px; font-family:'Orbitron',monospace; letter-spacing:1px;">
                <i class="fas fa-info-circle"></i> This name will appear on your users' panels
            </div>
        </div>

        <!-- Add User -->
        <div class="card">
            <div class="card-title"><i class="fas fa-user-plus"></i> create user</div>
            <form method="POST" action="{{ url_for('reseller_add_user') }}" class="add-form">
                <input type="text" name="username" placeholder="username" required>
                <input type="password" name="password" placeholder="password" required>
                <input type="datetime-local" name="expiry" class="expiry-input" placeholder="expiry (UTC)">
                <button type="submit" class="btn-add"><i class="fas fa-plus"></i> create</button>
            </form>
        </div>

        <!-- User List -->
        <div class="card">
            <div class="card-title"><i class="fas fa-users"></i> my users</div>
            <div class="table-wrap">
                {% if users %}
                <table>
                    <thead>
                        <tr>
                            <th>username</th>
                            <th>status</th>
                            <th>expiry</th>
                            <th>last login</th>
                            <th>actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for uname, udata in users.items() %}
                        <tr>
                            <td style="color:#fff; font-weight:500;">{{ uname }}</td>
                            <td>
                                {% if udata.active %}
                                    {% if udata.expiry_utc and is_user_expired(uname) %}
                                        <span class="badge expired">expired</span>
                                    {% else %}
                                        <span class="badge active">active</span>
                                    {% endif %}
                                {% else %}
                                    <span class="badge inactive">inactive</span>
                                {% endif %}
                            </td>
                            <td style="font-size:8px; color:#88ddff;">
                                {% if udata.expiry_utc %}
                                    {{ udata.expiry_utc[:10] }} {{ udata.expiry_utc[11:16] }}
                                {% else %}
                                    never
                                {% endif %}
                            </td>
                            <td style="font-size:8px; color:#88ddff;">
                                {{ udata.last_login[:10] if udata.last_login else 'never' }}
                            </td>
                            <td>
                                <div class="actions-cell">
                                    <a href="{{ url_for('reseller_edit_user', username=uname) }}"><i class="fas fa-pen"></i></a>
                                    <a href="{{ url_for('reseller_toggle_user', username=uname) }}"><i class="fas fa-{% if udata.active %}pause{% else %}play{% endif %}"></i></a>
                                    <a href="{{ url_for('reseller_delete_user', username=uname) }}" class="del" onclick="return confirm('delete {{ uname }}?')"><i class="fas fa-trash"></i></a>
                                </div>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
                {% else %}
                <div class="empty"><i class="fas fa-user-slash"></i> no users created yet</div>
                {% endif %}
            </div>
        </div>

        <div class="footer-text">⚡ {{ brand }} · reseller premium system ⚡</div>
    </div>
</body>
</html>
'''

# ============================================
# ADMIN LOGIN PAGE
# ============================================
ADMIN_LOGIN_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>ADMIN LOGIN · SAKIL BHAI</title>
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
        .bg-animation {
            position: fixed;
            top: 0; left: 0; width: 100%; height: 100%;
            z-index: 0;
            overflow: hidden;
        }
        .bg-animation .orb {
            position: absolute;
            border-radius: 50%;
            filter: blur(80px);
            animation: orbFloat 20s ease-in-out infinite;
        }
        .bg-animation .orb:nth-child(1) {
            width: 400px; height: 400px;
            background: rgba(0, 255, 255, 0.04);
            top: -100px; left: -100px;
            animation-delay: 0s;
        }
        .bg-animation .orb:nth-child(2) {
            width: 500px; height: 500px;
            background: rgba(0, 255, 255, 0.03);
            bottom: -150px; right: -150px;
            animation-delay: -5s;
        }
        .bg-animation .orb:nth-child(3) {
            width: 300px; height: 300px;
            background: rgba(255, 215, 0, 0.02);
            top: 50%; left: 50%;
            transform: translate(-50%, -50%);
            animation-delay: -10s;
        }
        @keyframes orbFloat {
            0%, 100% { transform: translate(0, 0) scale(1); }
            33% { transform: translate(30px, -30px) scale(1.1); }
            66% { transform: translate(-20px, 20px) scale(0.9); }
        }
        .login-container {
            position: relative;
            z-index: 1;
            background: rgba(6, 6, 12, 0.92);
            border: 1px solid rgba(0, 255, 255, 0.2);
            border-radius: 24px;
            padding: 48px 40px;
            max-width: 420px;
            width: 92%;
            backdrop-filter: blur(40px);
            box-shadow: 0 0 80px rgba(0, 255, 255, 0.08), inset 0 0 80px rgba(0, 255, 255, 0.01);
            animation: containerIn 0.8s cubic-bezier(0.16, 1, 0.3, 1);
        }
        @keyframes containerIn {
            0% { opacity: 0; transform: translateY(30px) scale(0.96); }
            100% { opacity: 1; transform: translateY(0) scale(1); }
        }
        .login-container .brand-section {
            text-align: center;
            margin-bottom: 32px;
        }
        .login-container .brand-section .icon-wrap {
            display: inline-block;
            font-size: 32px;
            color: #00ffff;
            opacity: 0.6;
            margin-bottom: 4px;
        }
        .login-container .brand-section h1 {
            font-family: 'Orbitron', monospace;
            font-size: 22px;
            font-weight: 800;
            letter-spacing: 4px;
            color: #ffffff;
        }
        .login-container .brand-section h1 .highlight {
            color: #00ffff;
            text-shadow: 0 0 40px rgba(0, 255, 255, 0.2);
        }
        .login-container .brand-section .tagline {
            font-size: 9px;
            font-weight: 400;
            letter-spacing: 6px;
            color: #88ddff;
            text-transform: uppercase;
            margin-top: 2px;
            font-family: 'Orbitron', monospace;
        }
        .login-container .brand-section .divider {
            width: 40px;
            height: 1px;
            background: rgba(0, 255, 255, 0.3);
            margin: 10px auto 0;
        }
        .login-container .brand-section .panel-badge {
            display: inline-block;
            margin-top: 8px;
            font-size: 8px;
            font-family: 'Orbitron', monospace;
            color: #00ffff;
            letter-spacing: 4px;
            border: 1px solid rgba(0,255,255,0.2);
            padding: 2px 16px;
            border-radius: 30px;
        }
        .form-group { margin-bottom: 16px; }
        .form-group label {
            display: block;
            font-size: 9px;
            font-weight: 600;
            color: #88ddff;
            text-transform: uppercase;
            letter-spacing: 3px;
            margin-bottom: 6px;
            font-family: 'Orbitron', monospace;
        }
        .form-group label i { color: #00ffff; margin-right: 6px; }
        .form-group .input-wrap {
            display: flex;
            align-items: center;
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(0, 255, 255, 0.15);
            border-radius: 12px;
            transition: all 0.3s ease;
            overflow: hidden;
        }
        .form-group .input-wrap:focus-within {
            border-color: rgba(0, 255, 255, 0.6);
            box-shadow: 0 0 30px rgba(0, 255, 255, 0.05);
        }
        .form-group .input-wrap .prefix {
            padding: 12px 0 12px 16px;
            color: #88ddff;
            font-size: 13px;
            width: 38px;
            text-align: center;
            font-family: 'Orbitron', monospace;
        }
        .form-group .input-wrap .line {
            width: 1px;
            height: 20px;
            background: rgba(0, 255, 255, 0.1);
        }
        .form-group .input-wrap input {
            flex: 1;
            padding: 12px 16px;
            background: transparent;
            border: none;
            color: #ffffff;
            font-size: 15px;
            outline: none;
            font-family: 'Inter', sans-serif;
            font-weight: 400;
            letter-spacing: 0.5px;
        }
        .form-group .input-wrap input::placeholder {
            color: #88ddff;
            font-size: 13px;
            font-weight: 300;
        }
        .btn-login {
            width: 100%;
            padding: 14px;
            background: rgba(0, 255, 255, 0.05);
            border: 1px solid rgba(0, 255, 255, 0.2);
            border-radius: 12px;
            color: #88ddff;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            font-family: 'Orbitron', monospace;
            letter-spacing: 4px;
            transition: all 0.3s ease;
            text-transform: uppercase;
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 12px;
            margin-top: 4px;
        }
        .btn-login:hover {
            border-color: rgba(0, 255, 255, 0.5);
            color: #00ffff;
            box-shadow: 0 0 40px rgba(0, 255, 255, 0.05);
        }
        .btn-login i { font-size: 14px; color: #00ffff; }
        .error-text {
            color: #ff3355;
            font-size: 11px;
            padding: 6px 0;
            display: none;
            text-align: center;
            font-family: 'Orbitron', monospace;
            letter-spacing: 1px;
        }
        .error-text.show { display: block; animation: shake 0.4s ease; }
        @keyframes shake {
            0%, 100% { transform: translateX(0); }
            25% { transform: translateX(-4px); }
            75% { transform: translateX(4px); }
        }
        .status-bar {
            display: flex;
            justify-content: center;
            gap: 20px;
            margin-top: 18px;
            padding: 10px 14px;
            background: rgba(0, 0, 0, 0.15);
            border-radius: 10px;
            border: 1px solid rgba(0, 255, 255, 0.05);
        }
        .status-bar .item {
            font-size: 7px;
            font-weight: 400;
            color: #88ddff;
            letter-spacing: 2px;
            text-transform: uppercase;
            font-family: 'Orbitron', monospace;
            display: flex;
            align-items: center;
            gap: 4px;
        }
        .status-bar .item i { font-size: 8px; color: #00ffff; }
        .footer-text {
            text-align: center;
            font-size: 6px;
            color: #88ddff;
            letter-spacing: 3px;
            margin-top: 16px;
            font-family: 'Orbitron', monospace;
        }
        .flash-msg {
            padding: 8px 14px;
            border-radius: 8px;
            margin-bottom: 12px;
            font-size: 9px;
            font-family: 'Orbitron', monospace;
            letter-spacing: 1px;
            background: rgba(0, 255, 102, 0.02);
            border: 1px solid rgba(0, 255, 102, 0.05);
            color: #00ff66;
            text-align: center;
        }
        .flash-msg.error { border-color: rgba(255, 51, 85, 0.05); color: #ff3355; }
        .panel-links {
            margin-top: 14px;
            display: flex;
            justify-content: center;
            gap: 16px;
            flex-wrap: wrap;
        }
        .panel-links a {
            font-size: 7px;
            font-family: 'Orbitron', monospace;
            color: #88ddff;
            text-decoration: none;
            letter-spacing: 2px;
            padding: 3px 12px;
            border: 1px solid rgba(255,255,255,0.03);
            border-radius: 20px;
            transition: all 0.3s ease;
        }
        .panel-links a:hover {
            border-color: rgba(0,255,255,0.2);
            color: #00ffff;
        }
        .panel-links a.user-link { border-color: rgba(0,255,255,0.05); color: #00ffff; }
        .panel-links a.user-link:hover { border-color: rgba(0,255,255,0.2); color: #00ffff; }
        .panel-links a.reseller-link { border-color: rgba(255,215,0,0.05); color: #ffd700; }
        .panel-links a.reseller-link:hover { border-color: rgba(255,215,0,0.2); color: #ffd700; }
        @media (max-width: 480px) {
            .login-container { padding: 32px 22px; }
            .login-container .brand-section h1 { font-size: 18px; letter-spacing: 2px; }
            .status-bar { gap: 12px; flex-wrap: wrap; }
        }
    </style>
</head>
<body>
    <div class="bg-animation">
        <div class="orb"></div>
        <div class="orb"></div>
        <div class="orb"></div>
    </div>
    <div class="login-container">
        <div class="brand-section">
            <div class="icon-wrap"><i class="fas fa-crown"></i></div>
            <h1><span class="highlight">ADMIN</span> PANEL</h1>
            <div class="tagline">main admin · full control</div>
            <div class="panel-badge"><i class="fas fa-shield-halved"></i> admin access</div>
            <div class="divider"></div>
        </div>
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% for category, message in messages %}
                <div class="flash-msg {{ category }}"><i class="fas fa-{% if category == 'error' %}exclamation-circle{% else %}check-circle{% endif %}"></i> {{ message }}</div>
            {% endfor %}
        {% endwith %}
        <form method="POST">
            <div class="form-group">
                <label><i class="fas fa-user"></i> username</label>
                <div class="input-wrap">
                    <div class="prefix"><i class="fas fa-user"></i></div>
                    <div class="line"></div>
                    <input type="text" name="username" placeholder="Enter admin username" required autofocus>
                </div>
            </div>
            <div class="form-group">
                <label><i class="fas fa-key"></i> password</label>
                <div class="input-wrap">
                    <div class="prefix"><i class="fas fa-lock"></i></div>
                    <div class="line"></div>
                    <input type="password" name="password" placeholder="Enter password" required>
                </div>
            </div>
            <div class="error-text" id="loginError">{{ error }}</div>
            <button type="submit" class="btn-login"><i class="fas fa-unlock-alt"></i> admin login</button>
        </form>
        <div class="status-bar">
            <span class="item"><i class="fas fa-database"></i> firebase</span>
            <span class="item"><i class="fas fa-clock"></i> {{ remaining_minutes }}m</span>
            <span class="item"><i class="fas fa-shield-alt"></i> secure</span>
        </div>
        <div class="panel-links">
            <a href="{{ url_for('user_login_page') }}" class="user-link"><i class="fas fa-user"></i> user</a>
            <a href="{{ url_for('reseller_login_page') }}" class="reseller-link"><i class="fas fa-store"></i> reseller</a>
        </div>
        <div class="footer-text">⚡ sakil bhai · multi-panel system ⚡</div>
    </div>
    <script>
        document.querySelector('input[name="username"]').focus();
        document.querySelectorAll('input').forEach(el => {
            el.addEventListener('input', function() {
                document.getElementById('loginError').classList.remove('show');
            });
        });
    </script>
</body>
</html>
'''

# ============================================
# ADMIN PANEL (Main Admin Dashboard)
# ============================================
ADMIN_PANEL_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SAKIL BHAI · MAIN ADMIN</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;800;900&family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', sans-serif;
            background: #06060a;
            min-height: 100vh;
            padding: 16px;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        .header {
            background: rgba(6,6,12,0.95); border: 1px solid rgba(0,255,255,0.15);
            border-radius: 16px; padding: 16px 20px; margin-bottom: 16px;
            display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;
            backdrop-filter: blur(20px);
        }
        .header .title { display: flex; align-items: center; gap: 10px; }
        .header .title i { font-size: 28px; color: #00ffff; opacity: 0.5; }
        .header .title h1 {
            font-family: 'Orbitron', monospace; font-size: 20px; font-weight: 700;
            color: #fff; letter-spacing: 2px;
        }
        .header .title h1 .hl { color: #00ffff; }
        .header .title .sub {
            font-size: 7px; font-family: 'Orbitron', monospace;
            color: #88ddff; letter-spacing: 3px;
        }
        .header .actions { display: flex; gap: 8px; }
        .header .actions a {
            font-size: 8px; font-family: 'Orbitron', monospace;
            color: #88ddff; text-decoration: none;
            padding: 4px 14px; border: 1px solid rgba(255,255,255,0.05);
            border-radius: 30px; letter-spacing: 2px; transition: all 0.3s ease;
        }
        .header .actions a:hover { border-color: rgba(0,255,255,0.2); color: #00ffff; }
        .header .actions a.logout { border-color: rgba(255,51,85,0.1); color: #ff3355; }
        .header .actions a.logout:hover { border-color: rgba(255,51,85,0.3); color: #ff3355; }
        .card {
            background: rgba(6,6,12,0.92); border: 1px solid rgba(255,255,255,0.03);
            border-radius: 14px; padding: 16px 20px; margin-bottom: 14px;
            backdrop-filter: blur(20px);
        }
        .card .card-title {
            font-size: 8px; font-family: 'Orbitron', monospace;
            color: #88ddff; letter-spacing: 3px;
            text-transform: uppercase; margin-bottom: 12px;
            display: flex; align-items: center; gap: 6px;
        }
        .card .card-title i { color: #00ffff; font-size: 11px; }
        .stats {
            display: grid; grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
            gap: 10px; margin-bottom: 14px;
        }
        .stat-box {
            background: rgba(0,0,0,0.15); border: 1px solid rgba(255,255,255,0.03);
            border-radius: 10px; padding: 12px 14px; text-align: center;
        }
        .stat-box .num {
            font-family: 'Orbitron', monospace; font-size: 22px;
            font-weight: 700; color: #fff;
        }
        .stat-box .num.green { color: #00ff66; }
        .stat-box .num.cyan { color: #00ffff; }
        .stat-box .num.gold { color: #ffd700; }
        .stat-box .num.red { color: #ff3355; }
        .stat-box .label {
            font-size: 6px; font-family: 'Orbitron', monospace;
            color: #88ddff; letter-spacing: 2px;
            text-transform: uppercase; margin-top: 2px;
        }
        .table-wrap { overflow-x: auto; }
        table { width: 100%; border-collapse: collapse; font-size: 11px; }
        thead th {
            font-size: 7px; font-family: 'Orbitron', monospace;
            color: #88ddff; letter-spacing: 2px;
            text-transform: uppercase; padding: 6px 8px;
            border-bottom: 1px solid rgba(255,255,255,0.03);
            text-align: left;
        }
        tbody td {
            color: #ccddff; padding: 6px 8px;
            border-bottom: 1px solid rgba(255,255,255,0.02);
            vertical-align: middle; font-size: 10px;
        }
        .badge {
            font-size: 6px; font-family: 'Orbitron', monospace;
            padding: 1px 10px; border-radius: 30px;
            border: 1px solid rgba(255,255,255,0.03);
            color: #88ddff;
        }
        .badge.main_admin { border-color: rgba(0,255,255,0.2); color: #00ffff; }
        .badge.reseller { border-color: rgba(255,215,0,0.2); color: #ffd700; }
        .badge.user { border-color: rgba(0,255,102,0.2); color: #00ff66; }
        .badge.active { border-color: rgba(0,255,102,0.2); color: #00ff66; }
        .badge.inactive { border-color: rgba(255,51,85,0.2); color: #ff3355; }
        .actions-cell { display: flex; gap: 4px; flex-wrap: wrap; }
        .actions-cell a {
            font-size: 7px; font-family: 'Orbitron', monospace;
            color: #88ddff; text-decoration: none;
            padding: 1px 8px; border: 1px solid rgba(255,255,255,0.03);
            border-radius: 4px; transition: all 0.3s ease;
        }
        .actions-cell a:hover { border-color: rgba(0,255,255,0.2); color: #00ffff; }
        .actions-cell a.del:hover { border-color: rgba(255,51,85,0.2); color: #ff3355; }
        .add-form { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
        .add-form input, .add-form select {
            padding: 6px 12px; background: rgba(0,0,0,0.2);
            border: 1px solid rgba(0,255,255,0.05); border-radius: 8px;
            color: #fff; font-size: 12px; outline: none;
            font-family: 'Inter', sans-serif; flex: 1; min-width: 100px;
        }
        .add-form input:focus, .add-form select:focus { border-color: rgba(0,255,255,0.15); }
        .add-form input::placeholder { color: #88ddff; }
        .add-form select option { background: #0a0a1a; color: #fff; }
        .add-form .btn-add {
            padding: 6px 18px; background: rgba(0,255,255,0.03);
            border: 1px solid rgba(0,255,255,0.05); border-radius: 8px;
            color: #88ddff; font-family: 'Orbitron', monospace;
            font-size: 9px; letter-spacing: 2px; cursor: pointer;
            transition: all 0.3s ease;
        }
        .add-form .btn-add:hover { border-color: rgba(0,255,255,0.2); color: #00ffff; }
        .expiry-form {
            display: flex; flex-wrap: wrap; gap: 10px; align-items: center;
            background: rgba(0,0,0,0.1); padding: 12px; border-radius: 10px;
            border: 1px solid rgba(0,255,255,0.05);
        }
        .expiry-form label {
            font-size: 8px; font-family: 'Orbitron', monospace;
            color: #88ddff; letter-spacing: 2px;
            text-transform: uppercase;
        }
        .expiry-form input[type="datetime-local"] {
            padding: 6px 12px; background: rgba(0,0,0,0.3);
            border: 1px solid rgba(0,255,255,0.1); border-radius: 8px;
            color: #fff; font-size: 12px; outline: none;
            font-family: 'Inter', sans-serif;
        }
        .expiry-form input[type="datetime-local"]:focus { border-color: rgba(0,255,255,0.3); }
        .expiry-form .btn-expiry {
            padding: 6px 18px; background: rgba(0,255,255,0.05);
            border: 1px solid rgba(0,255,255,0.1); border-radius: 8px;
            color: #88ddff; font-family: 'Orbitron', monospace;
            font-size: 9px; letter-spacing: 2px; cursor: pointer;
            transition: all 0.3s ease;
        }
        .expiry-form .btn-expiry:hover { border-color: rgba(0,255,255,0.3); color: #00ffff; }
        .expiry-display {
            font-size: 9px; color: #88ddff; margin-left: 5px;
            font-family: 'Orbitron', monospace; letter-spacing: 1px;
        }
        .expiry-display .hl { color: #00ff66; }
        .expiry-display .warn { color: #ff3355; }
        .flash {
            padding: 8px 14px; border-radius: 8px; margin-bottom: 12px;
            font-size: 10px; font-family: 'Orbitron', monospace;
            letter-spacing: 1px; display: flex; align-items: center; gap: 8px;
        }
        .flash.success { background: rgba(0,255,102,0.02); border: 1px solid rgba(0,255,102,0.05); color: #00ff66; }
        .flash.error { background: rgba(255,51,85,0.02); border: 1px solid rgba(255,51,85,0.05); color: #ff3355; }
        .empty { text-align: center; color: #88ddff; padding: 16px; font-size: 10px; font-family: 'Orbitron', monospace; letter-spacing: 2px; }
        .footer-text { text-align: center; font-size: 6px; color: #88ddff; letter-spacing: 3px; margin-top: 10px; font-family: 'Orbitron', monospace; }
        .expiry-input { padding: 6px 12px; background: rgba(0,0,0,0.2); border: 1px solid rgba(0,255,255,0.05); border-radius: 8px; color: #fff; font-size: 11px; outline: none; font-family: 'Inter', sans-serif; }
        .expiry-input:focus { border-color: rgba(0,255,255,0.15); }
        @media (max-width: 600px) {
            .header .title h1 { font-size: 16px; }
            .stats { grid-template-columns: repeat(2, 1fr); }
            .add-form { flex-direction: column; }
            .add-form input, .add-form select, .add-form .btn-add { width: 100%; }
            .expiry-form { flex-direction: column; align-items: stretch; }
            .expiry-form input[type="datetime-local"] { width: 100%; }
            .card { padding: 12px 14px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="title">
                <i class="fas fa-crown"></i>
                <div>
                    <h1><span class="hl">MAIN</span> ADMIN</h1>
                    <div class="sub">super admin · full control</div>
                </div>
            </div>
            <div class="actions">
                <a href="{{ url_for('admin_logout') }}" class="logout"><i class="fas fa-sign-out-alt"></i> logout</a>
            </div>
        </div>

        {% with messages = get_flashed_messages(with_categories=true) %}
            {% for category, message in messages %}
                <div class="flash {{ category }}"><i class="fas fa-{% if category == 'success' %}check-circle{% else %}exclamation-circle{% endif %}"></i> {{ message }}</div>
            {% endfor %}
        {% endwith %}

        <div class="stats">
            <div class="stat-box"><div class="num cyan">{{ stats.total_users }}</div><div class="label">total users</div></div>
            <div class="stat-box"><div class="num green">{{ stats.active_users }}</div><div class="label">active</div></div>
            <div class="stat-box"><div class="num red">{{ stats.inactive_users }}</div><div class="label">inactive</div></div>
            <div class="stat-box"><div class="num gold">{{ stats.total_resellers }}</div><div class="label">resellers</div></div>
            <div class="stat-box"><div class="num" style="color:#FF9933;">{{ stats.expiry_status }}</div><div class="label">system expiry</div></div>
        </div>

        <!-- System Expiry -->
        <div class="card">
            <div class="card-title"><i class="fas fa-clock"></i> system expiry</div>
            <div class="expiry-form">
                <label>set expiry (UTC):</label>
                <input type="datetime-local" id="expiryInput" value="{{ expiry_local }}">
                <button class="btn-expiry" onclick="setExpiry()"><i class="fas fa-save"></i> update</button>
                <span class="expiry-display">current: <span id="expiryDisplay" class="{% if stats.expiry_status == 'active' %}hl{% else %}warn{% endif %}">{{ stats.expiry_status }} ({{ remaining }}s)</span></span>
            </div>
            <div id="expiryMsg" style="margin-top:8px; font-size:9px; color:#88ddff;"></div>
        </div>

        <!-- Add Reseller -->
        <div class="card">
            <div class="card-title"><i class="fas fa-store"></i> create reseller</div>
            <form method="POST" action="{{ url_for('admin_add_reseller') }}" class="add-form">
                <input type="text" name="username" placeholder="reseller username" required>
                <input type="password" name="password" placeholder="password" required>
                <input type="text" name="brand_name" placeholder="brand name (e.g. PRIYANGSHU)" required>
                <input type="datetime-local" name="expiry" class="expiry-input" placeholder="expiry (UTC)">
                <button type="submit" class="btn-add"><i class="fas fa-plus"></i> create reseller</button>
            </form>
        </div>

        <!-- Add User (Main Admin can also add users) -->
        <div class="card">
            <div class="card-title"><i class="fas fa-user-plus"></i> add user (direct)</div>
            <form method="POST" action="{{ url_for('admin_add_user') }}" class="add-form">
                <input type="text" name="username" placeholder="username" required>
                <input type="password" name="password" placeholder="password" required>
                <select name="reseller_id">
                    <option value="">No reseller (direct)</option>
                    {% for r in resellers_list %}
                    <option value="{{ r }}">{{ r }} ({{ resellers_data[r].brand_name if resellers_data[r] else r }})</option>
                    {% endfor %}
                </select>
                <input type="datetime-local" name="expiry" class="expiry-input" placeholder="expiry (UTC)">
                <button type="submit" class="btn-add"><i class="fas fa-plus"></i> add user</button>
            </form>
        </div>

        <!-- All Resellers -->
        <div class="card">
            <div class="card-title"><i class="fas fa-users-cog"></i> all resellers</div>
            <div class="table-wrap">
                {% if resellers %}
                <table>
                    <thead>
                        <tr>
                            <th>username</th>
                            <th>brand</th>
                            <th>users</th>
                            <th>expiry</th>
                            <th>status</th>
                            <th>actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for rname, rdata in resellers.items() %}
                        <tr>
                            <td style="color:#ffd700; font-weight:500;">{{ rname }}</td>
                            <td style="color:#fff;">{{ rdata.brand_name }}</td>
                            <td style="color:#88ddff;">{{ rdata.user_count or 0 }}</td>
                            <td style="font-size:8px; color:#88ddff;">
                                {% if rdata.expiry_utc %}
                                    {{ rdata.expiry_utc[:10] }}
                                {% else %}
                                    never
                                {% endif %}
                            </td>
                            <td><span class="badge {% if rdata.active %}active{% else %}inactive{% endif %}">{{ 'active' if rdata.active else 'inactive' }}</span></td>
                            <td>
                                <div class="actions-cell">
                                    <a href="{{ url_for('admin_edit_reseller', username=rname) }}"><i class="fas fa-pen"></i></a>
                                    <a href="{{ url_for('admin_toggle_reseller', username=rname) }}"><i class="fas fa-{% if rdata.active %}pause{% else %}play{% endif %}"></i></a>
                                    <a href="{{ url_for('admin_delete_reseller', username=rname) }}" class="del" onclick="return confirm('delete reseller {{ rname }}?')"><i class="fas fa-trash"></i></a>
                                </div>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
                {% else %}
                <div class="empty"><i class="fas fa-store-slash"></i> no resellers</div>
                {% endif %}
            </div>
        </div>

        <!-- All Users -->
        <div class="card">
            <div class="card-title"><i class="fas fa-users"></i> all users</div>
            <div class="table-wrap">
                {% if all_users %}
                <table>
                    <thead>
                        <tr>
                            <th>username</th>
                            <th>role</th>
                            <th>reseller</th>
                            <th>status</th>
                            <th>expiry</th>
                            <th>actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for uname, udata in all_users.items() %}
                        <tr>
                            <td style="color:{% if udata.role == 'main_admin' %}#00ffff{% elif udata.role == 'reseller' %}#ffd700{% else %}#fff{% endif %}; font-weight:500;">
                                {{ uname }}
                                {% if udata.role == 'main_admin' %}<span style="color:#00ffff; font-size:7px;">👑</span>{% endif %}
                            </td>
                            <td><span class="badge {{ udata.role }}">{{ udata.role }}</span></td>
                            <td style="font-size:8px; color:#88ddff;">{{ udata.reseller_id or 'direct' }}</td>
                            <td><span class="badge {% if udata.active %}active{% else %}inactive{% endif %}">{{ 'active' if udata.active else 'inactive' }}</span></td>
                            <td style="font-size:8px; color:#88ddff;">
                                {% if udata.expiry_utc %}
                                    {{ udata.expiry_utc[:10] }}
                                {% else %}
                                    never
                                {% endif %}
                            </td>
                            <td>
                                <div class="actions-cell">
                                    <a href="{{ url_for('admin_edit_user', username=uname) }}"><i class="fas fa-pen"></i></a>
                                    <a href="{{ url_for('admin_toggle_user', username=uname) }}"><i class="fas fa-{% if udata.active %}pause{% else %}play{% endif %}"></i></a>
                                    {% if uname != 'sakil2026' %}
                                    <a href="{{ url_for('admin_delete_user', username=uname) }}" class="del" onclick="return confirm('delete {{ uname }}?')"><i class="fas fa-trash"></i></a>
                                    {% endif %}
                                </div>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
                {% else %}
                <div class="empty"><i class="fas fa-user-slash"></i> no users</div>
                {% endif %}
            </div>
        </div>

        <div class="footer-text">⚡ sakil bhai · main admin super system ⚡</div>
    </div>

    <script>
        function setExpiry() {
            const input = document.getElementById('expiryInput');
            const val = input.value;
            if (!val) {
                document.getElementById('expiryMsg').innerHTML = '<span style="color:#ff3355;">⚠️ please select a date/time</span>';
                return;
            }
            const iso = new Date(val).toISOString();
            fetch('/admin/set-expiry', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ expiry: iso })
            })
            .then(res => res.json())
            .then(data => {
                if (data.status === 'success') {
                    document.getElementById('expiryMsg').innerHTML = '<span style="color:#00ff66;">✅ expiry updated successfully</span>';
                    document.getElementById('expiryDisplay').textContent = data.expiry_status + ' (' + data.remaining + 's)';
                    document.getElementById('expiryDisplay').className = data.expiry_status === 'active' ? 'hl' : 'warn';
                } else {
                    document.getElementById('expiryMsg').innerHTML = '<span style="color:#ff3355;">❌ ' + data.message + '</span>';
                }
            })
            .catch(err => {
                document.getElementById('expiryMsg').innerHTML = '<span style="color:#ff3355;">❌ error: ' + err.message + '</span>';
            });
        }
    </script>
</body>
</html>
'''

# ============================================
# FLASK ROUTES
# ============================================

# ===== USER ROUTES =====
@app.route('/user-login', methods=['GET', 'POST'])
def user_login_page():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if verify_user(username, password):
            role = get_user_role(username)
            if role not in ['user', 'reseller', 'main_admin']:
                flash("Invalid user type", "error")
                return redirect(url_for('user_login_page'))
            
            if is_system_expired():
                flash("System expired.", "error")
                return redirect(url_for('user_login_page'))
            if is_user_expired(username):
                flash("Your subscription has expired.", "error")
                return redirect(url_for('user_login_page'))

            session["user_auth"] = True
            session["user_username"] = username
            session["user_role"] = role

            users = get_users()
            users[username]["last_login"] = datetime.datetime.utcnow().isoformat()
            save_users(users)

            return redirect(url_for('user_dashboard'))
        else:
            flash("Invalid credentials", "error")
            return redirect(url_for('user_login_page'))

    remaining_seconds = get_system_remaining()
    remaining_minutes = max(0, remaining_seconds // 60)
    return render_template_string(USER_LOGIN_HTML, error="", remaining_minutes=remaining_minutes)

@app.route('/user-logout')
def user_logout():
    session.pop("user_auth", None)
    session.pop("user_username", None)
    session.pop("user_role", None)
    return redirect(url_for('user_login_page'))

@app.route('/user-dashboard')
@user_session_required
def user_dashboard():
    username = session.get("user_username")
    remaining = get_system_remaining()
    user_remaining = get_user_expiry(username)
    if user_remaining is not None and user_remaining < remaining:
        remaining = user_remaining
    brand = get_brand_for_user(username)
    return render_template_string(USER_PANEL_HTML,
                                 remaining_seconds=remaining,
                                 max_seconds=3600,
                                 brand=brand)

# ===== RESELLER ROUTES =====
@app.route('/reseller-login', methods=['GET', 'POST'])
def reseller_login_page():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if verify_user(username, password):
            role = get_user_role(username)
            if role not in ['reseller', 'main_admin']:
                flash("Reseller access required", "error")
                return redirect(url_for('reseller_login_page'))
            
            if is_system_expired():
                flash("System expired.", "error")
                return redirect(url_for('reseller_login_page'))
            if is_user_expired(username):
                flash("Your reseller subscription has expired.", "error")
                return redirect(url_for('reseller_login_page'))

            session["reseller_auth"] = True
            session["reseller_username"] = username
            session["reseller_role"] = role

            users = get_users()
            users[username]["last_login"] = datetime.datetime.utcnow().isoformat()
            save_users(users)

            return redirect(url_for('reseller_dashboard'))
        else:
            flash("Invalid credentials", "error")
            return redirect(url_for('reseller_login_page'))

    remaining_seconds = get_system_remaining()
    remaining_minutes = max(0, remaining_seconds // 60)
    return render_template_string(RESELLER_LOGIN_HTML, error="", remaining_minutes=remaining_minutes)

@app.route('/reseller-logout')
def reseller_logout():
    session.pop("reseller_auth", None)
    session.pop("reseller_username", None)
    session.pop("reseller_role", None)
    return redirect(url_for('reseller_login_page'))

@app.route('/reseller-dashboard')
@reseller_session_required
def reseller_dashboard():
    username = session.get("reseller_username")
    resellers = get_resellers()
    if username not in resellers and session.get("reseller_role") != "main_admin":
        flash("Reseller panel not found", "error")
        return redirect(url_for('reseller_login_page'))

    brand = resellers.get(username, {}).get("brand_name", username.upper())
    users = get_users()
    my_users = {u: d for u, d in users.items() if d.get("reseller_id") == username}

    total = len(my_users)
    active = 0
    for uname, udata in my_users.items():
        if udata.get("active"):
            if udata.get("expiry_utc"):
                if not is_user_expired(uname):
                    active += 1
            else:
                active += 1
    inactive = total - active
    online = 0
    now = datetime.datetime.utcnow()
    for udata in my_users.values():
        if udata.get("last_login"):
            try:
                last = datetime.datetime.fromisoformat(udata["last_login"])
                if (now - last).seconds < 300:
                    online += 1
            except:
                pass

    stats = {
        "total_users": total,
        "active_users": active,
        "inactive_users": inactive,
        "online_users": online
    }

    return render_template_string(RESELLER_PANEL_HTML,
                                 brand=brand,
                                 users=my_users,
                                 stats=stats,
                                 is_user_expired=is_user_expired)

@app.route('/reseller/update-brand', methods=['POST'])
@reseller_session_required
def reseller_update_brand():
    username = session.get("reseller_username")
    brand_name = request.form.get('brand_name', '').strip()
    if not brand_name:
        flash("Brand name required", "error")
        return redirect(url_for('reseller_dashboard'))

    resellers = get_resellers()
    if username not in resellers:
        flash("Reseller not found", "error")
        return redirect(url_for('reseller_dashboard'))

    resellers[username]["brand_name"] = brand_name
    if save_resellers(resellers):
        flash(f"Brand updated to '{brand_name}'", "success")
    else:
        flash("Error updating brand", "error")
    return redirect(url_for('reseller_dashboard'))

@app.route('/reseller/add-user', methods=['POST'])
@reseller_session_required
def reseller_add_user():
    reseller_username = session.get("reseller_username")
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    expiry_str = request.form.get('expiry', '')

    if not username or not password:
        flash("Username and password required", "error")
        return redirect(url_for('reseller_dashboard'))

    users = get_users()
    if username in users:
        flash("Username already exists", "error")
        return redirect(url_for('reseller_dashboard'))

    users[username] = {
        "password": hashlib.sha256(password.encode()).hexdigest(),
        "role": "user",
        "active": True,
        "created": datetime.datetime.utcnow().isoformat(),
        "created_by": reseller_username,
        "reseller_id": reseller_username
    }

    if expiry_str:
        try:
            dt = datetime.datetime.fromisoformat(expiry_str)
            users[username]["expiry_utc"] = dt.strftime('%Y-%m-%dT%H:%M:%S+00:00')
        except:
            flash("Invalid expiry format", "error")
            return redirect(url_for('reseller_dashboard'))

    if save_users(users):
        resellers = get_resellers()
        if reseller_username in resellers:
            resellers[reseller_username]["user_count"] = len([u for u, d in users.items() if d.get("reseller_id") == reseller_username and d.get("active")])
            save_resellers(resellers)
        flash(f"User '{username}' created", "success")
    else:
        flash("Error creating user", "error")

    return redirect(url_for('reseller_dashboard'))

@app.route('/reseller/toggle/<username>')
@reseller_session_required
def reseller_toggle_user(username):
    reseller_username = session.get("reseller_username")
    users = get_users()
    if username not in users:
        flash("User not found", "error")
        return redirect(url_for('reseller_dashboard'))
    if users[username].get("reseller_id") != reseller_username:
        flash("Not your user", "error")
        return redirect(url_for('reseller_dashboard'))

    users[username]["active"] = not users[username].get("active", True)
    if save_users(users):
        flash(f"User {'enabled' if users[username]['active'] else 'disabled'}", "success")
    else:
        flash("Error toggling", "error")
    return redirect(url_for('reseller_dashboard'))

@app.route('/reseller/delete/<username>')
@reseller_session_required
def reseller_delete_user(username):
    reseller_username = session.get("reseller_username")
    users = get_users()
    if username not in users:
        flash("User not found", "error")
        return redirect(url_for('reseller_dashboard'))
    if users[username].get("reseller_id") != reseller_username:
        flash("Not your user", "error")
        return redirect(url_for('reseller_dashboard'))

    del users[username]
    if save_users(users):
        flash(f"User '{username}' deleted", "success")
    else:
        flash("Error deleting", "error")
    return redirect(url_for('reseller_dashboard'))

@app.route('/reseller/edit/<username>', methods=['GET', 'POST'])
@reseller_session_required
def reseller_edit_user(username):
    reseller_username = session.get("reseller_username")
    users = get_users()
    if username not in users:
        flash("User not found", "error")
        return redirect(url_for('reseller_dashboard'))
    if users[username].get("reseller_id") != reseller_username:
        flash("Not your user", "error")
        return redirect(url_for('reseller_dashboard'))

    if request.method == 'POST':
        new_password = request.form.get('password', '').strip()
        expiry_str = request.form.get('expiry', '')

        if new_password:
            users[username]["password"] = hashlib.sha256(new_password.encode()).hexdigest()
        if expiry_str:
            try:
                dt = datetime.datetime.fromisoformat(expiry_str)
                users[username]["expiry_utc"] = dt.strftime('%Y-%m-%dT%H:%M:%S+00:00')
            except:
                flash("Invalid expiry format", "error")
                return redirect(url_for('reseller_edit_user', username=username))
        else:
            users[username]["expiry_utc"] = None

        if save_users(users):
            flash("User updated", "success")
        else:
            flash("Error saving", "error")
        return redirect(url_for('reseller_dashboard'))

    expiry_local = ""
    if users[username].get("expiry_utc"):
        try:
            dt = datetime.datetime.fromisoformat(users[username]["expiry_utc"].replace('Z', '+00:00'))
            expiry_local = dt.strftime('%Y-%m-%dT%H:%M')
        except:
            pass

    return f'''
    <!DOCTYPE html>
    <html><head><title>edit user</title>
    <style>
        *{{margin:0;padding:0;box-sizing:border-box;}}
        body{{background:#06060a;display:flex;justify-content:center;align-items:center;min-height:100vh;font-family:'Inter',sans-serif;}}
        .box{{background:rgba(6,6,12,0.95);border:1px solid rgba(255,215,0,0.1);border-radius:20px;padding:30px;max-width:380px;width:92%;}}
        h1{{font-family:'Orbitron',monospace;font-size:18px;font-weight:700;color:#fff;letter-spacing:2px;text-align:center;}}
        h1 .hl{{color:#ffd700;}}
        .sub{{text-align:center;font-size:8px;font-family:'Orbitron',monospace;color:#88ddff;letter-spacing:3px;margin-bottom:16px;}}
        .form-group{{margin-bottom:12px;}}
        label{{display:block;font-size:8px;font-family:'Orbitron',monospace;color:#88ddff;letter-spacing:2px;margin-bottom:3px;}}
        input{{width:100%;padding:8px 12px;background:rgba(0,0,0,0.2);border:1px solid rgba(255,215,0,0.05);border-radius:8px;color:#fff;font-size:13px;outline:none;font-family:'Inter',sans-serif;margin-top:2px;}}
        input:focus{{border-color:rgba(255,215,0,0.15);}}
        .btn{{width:100%;padding:10px;background:rgba(255,215,0,0.03);border:1px solid rgba(255,215,0,0.05);border-radius:8px;color:#88ddff;font-family:'Orbitron',monospace;font-size:10px;letter-spacing:2px;cursor:pointer;transition:all 0.3s ease;margin-top:4px;}}
        .btn:hover{{border-color:rgba(255,215,0,0.2);color:#ffd700;}}
        .back{{display:block;text-align:center;font-size:8px;font-family:'Orbitron',monospace;color:#88ddff;text-decoration:none;margin-top:10px;letter-spacing:2px;transition:all 0.3s ease;}}
        .back:hover{{color:#ffd700;}}
    </style>
    </head>
    <body>
    <div class="box">
        <h1><span class="hl">edit</span> user</h1>
        <div class="sub">reseller · {username}</div>
        <form method="POST">
            <div class="form-group">
                <label><i class="fas fa-key"></i> new password (optional)</label>
                <input type="password" name="password" placeholder="leave blank to keep">
            </div>
            <div class="form-group">
                <label><i class="fas fa-clock"></i> expiry (UTC)</label>
                <input type="datetime-local" name="expiry" value="{expiry_local}">
                <span style="font-size:7px; color:#88ddff;">leave empty = never expires</span>
            </div>
            <button type="submit" class="btn"><i class="fas fa-save"></i> update</button>
        </form>
        <a href="{url_for('reseller_dashboard')}" class="back"><i class="fas fa-arrow-left"></i> back</a>
    </div>
    </body>
    </html>
    '''

# ===== ADMIN ROUTES =====
@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login_page():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if verify_user(username, password):
            role = get_user_role(username)
            if role != "main_admin":
                flash("Main admin access required", "error")
                return redirect(url_for('admin_login_page'))
            
            if is_system_expired():
                flash("System expired.", "error")
                return redirect(url_for('admin_login_page'))

            session["admin_auth"] = True
            session["admin_username"] = username

            users = get_users()
            users[username]["last_login"] = datetime.datetime.utcnow().isoformat()
            save_users(users)

            return redirect(url_for('admin_dashboard'))
        else:
            flash("Invalid credentials", "error")
            return redirect(url_for('admin_login_page'))

    remaining_seconds = get_system_remaining()
    remaining_minutes = max(0, remaining_seconds // 60)
    return render_template_string(ADMIN_LOGIN_HTML, error="", remaining_minutes=remaining_minutes)

@app.route('/admin-logout')
def admin_logout():
    session.pop("admin_auth", None)
    session.pop("admin_username", None)
    return redirect(url_for('admin_login_page'))

@app.route('/admin-dashboard')
@admin_session_required
def admin_dashboard():
    users = get_users()
    resellers = get_resellers()

    total = len(users)
    active = sum(1 for u in users.values() if u.get("active"))
    inactive = total - active
    total_resellers = len(resellers)

    remaining = get_system_remaining()
    expiry_status = "active" if remaining > 0 else "expired"

    settings = get_settings()
    expiry_utc = settings.get("expiry_utc", "")
    if expiry_utc:
        try:
            dt = datetime.datetime.fromisoformat(expiry_utc.replace('Z', '+00:00'))
            expiry_local = dt.strftime('%Y-%m-%dT%H:%M')
        except:
            expiry_local = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M')
    else:
        expiry_local = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M')

    stats = {
        "total_users": total,
        "active_users": active,
        "inactive_users": inactive,
        "total_resellers": total_resellers,
        "expiry_status": expiry_status
    }

    return render_template_string(ADMIN_PANEL_HTML,
                                 all_users=users,
                                 resellers=resellers,
                                 resellers_list=list(resellers.keys()),
                                 resellers_data=resellers,
                                 stats=stats,
                                 remaining=remaining,
                                 expiry_local=expiry_local)

@app.route('/admin/set-expiry', methods=['POST'])
@admin_session_required
def admin_set_expiry():
    data = request.get_json()
    expiry_str = data.get('expiry', '')
    if not expiry_str:
        return jsonify({"status": "error", "message": "expiry required"}), 400
    try:
        dt = datetime.datetime.fromisoformat(expiry_str.replace('Z', '+00:00'))
        expiry_utc = dt.strftime('%Y-%m-%dT%H:%M:%S+00:00')
        settings = get_settings()
        settings["expiry_utc"] = expiry_utc
        if save_settings(settings):
            remaining = get_system_remaining()
            status = "active" if remaining > 0 else "expired"
            return jsonify({
                "status": "success",
                "expiry_utc": expiry_utc,
                "remaining": remaining,
                "expiry_status": status
            })
        else:
            return jsonify({"status": "error", "message": "failed to save"}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/admin/add-reseller', methods=['POST'])
@admin_session_required
def admin_add_reseller():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    brand_name = request.form.get('brand_name', '').strip()
    expiry_str = request.form.get('expiry', '')

    if not username or not password or not brand_name:
        flash("All fields required", "error")
        return redirect(url_for('admin_dashboard'))

    users = get_users()
    if username in users:
        flash("Username already exists", "error")
        return redirect(url_for('admin_dashboard'))

    users[username] = {
        "password": hashlib.sha256(password.encode()).hexdigest(),
        "role": "reseller",
        "active": True,
        "created": datetime.datetime.utcnow().isoformat(),
        "created_by": "main_admin"
    }

    if expiry_str:
        try:
            dt = datetime.datetime.fromisoformat(expiry_str)
            users[username]["expiry_utc"] = dt.strftime('%Y-%m-%dT%H:%M:%S+00:00')
        except:
            flash("Invalid expiry format", "error")
            return redirect(url_for('admin_dashboard'))

    save_users(users)

    resellers = get_resellers()
    resellers[username] = {
        "brand_name": brand_name,
        "created": datetime.datetime.utcnow().isoformat(),
        "active": True,
        "user_count": 0,
        "expiry_utc": users[username].get("expiry_utc")
    }
    save_resellers(resellers)

    flash(f"Reseller '{username}' created with brand '{brand_name}'", "success")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/toggle-reseller/<username>')
@admin_session_required
def admin_toggle_reseller(username):
    resellers = get_resellers()
    if username not in resellers:
        flash("Reseller not found", "error")
        return redirect(url_for('admin_dashboard'))

    resellers[username]["active"] = not resellers[username].get("active", True)
    if save_resellers(resellers):
        flash(f"Reseller {'enabled' if resellers[username]['active'] else 'disabled'}", "success")
    else:
        flash("Error toggling", "error")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete-reseller/<username>')
@admin_session_required
def admin_delete_reseller(username):
    resellers = get_resellers()
    if username not in resellers:
        flash("Reseller not found", "error")
        return redirect(url_for('admin_dashboard'))

    users = get_users()
    to_delete = [u for u, d in users.items() if d.get("reseller_id") == username]
    for u in to_delete:
        del users[u]
    save_users(users)

    del resellers[username]
    save_resellers(resellers)
    flash(f"Reseller '{username}' and all their users deleted", "success")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/edit-reseller/<username>', methods=['GET', 'POST'])
@admin_session_required
def admin_edit_reseller(username):
    resellers = get_resellers()
    if username not in resellers:
        flash("Reseller not found", "error")
        return redirect(url_for('admin_dashboard'))
    users = get_users()

    if request.method == 'POST':
        brand_name = request.form.get('brand_name', '').strip()
        new_password = request.form.get('password', '').strip()
        expiry_str = request.form.get('expiry', '')

        if brand_name:
            resellers[username]["brand_name"] = brand_name
        if new_password:
            if username in users:
                users[username]["password"] = hashlib.sha256(new_password.encode()).hexdigest()
                save_users(users)
        if expiry_str:
            try:
                dt = datetime.datetime.fromisoformat(expiry_str)
                resellers[username]["expiry_utc"] = dt.strftime('%Y-%m-%dT%H:%M:%S+00:00')
                if username in users:
                    users[username]["expiry_utc"] = resellers[username]["expiry_utc"]
                    save_users(users)
            except:
                flash("Invalid expiry format", "error")
                return redirect(url_for('admin_edit_reseller', username=username))
        else:
            resellers[username]["expiry_utc"] = None
            if username in users:
                users[username]["expiry_utc"] = None
                save_users(users)

        save_resellers(resellers)
        flash("Reseller updated", "success")
        return redirect(url_for('admin_dashboard'))

    brand_name = resellers[username].get("brand_name", username.upper())
    expiry_local = ""
    if resellers[username].get("expiry_utc"):
        try:
            dt = datetime.datetime.fromisoformat(resellers[username]["expiry_utc"].replace('Z', '+00:00'))
            expiry_local = dt.strftime('%Y-%m-%dT%H:%M')
        except:
            pass

    return f'''
    <!DOCTYPE html>
    <html><head><title>edit reseller</title>
    <style>
        *{{margin:0;padding:0;box-sizing:border-box;}}
        body{{background:#06060a;display:flex;justify-content:center;align-items:center;min-height:100vh;font-family:'Inter',sans-serif;}}
        .box{{background:rgba(6,6,12,0.95);border:1px solid rgba(0,255,255,0.1);border-radius:20px;padding:30px;max-width:380px;width:92%;}}
        h1{{font-family:'Orbitron',monospace;font-size:18px;font-weight:700;color:#fff;letter-spacing:2px;text-align:center;}}
        h1 .hl{{color:#00ffff;}}
        .sub{{text-align:center;font-size:8px;font-family:'Orbitron',monospace;color:#88ddff;letter-spacing:3px;margin-bottom:16px;}}
        .form-group{{margin-bottom:12px;}}
        label{{display:block;font-size:8px;font-family:'Orbitron',monospace;color:#88ddff;letter-spacing:2px;margin-bottom:3px;}}
        input{{width:100%;padding:8px 12px;background:rgba(0,0,0,0.2);border:1px solid rgba(0,255,255,0.05);border-radius:8px;color:#fff;font-size:13px;outline:none;font-family:'Inter',sans-serif;margin-top:2px;}}
        input:focus{{border-color:rgba(0,255,255,0.15);}}
        .btn{{width:100%;padding:10px;background:rgba(0,255,255,0.03);border:1px solid rgba(0,255,255,0.05);border-radius:8px;color:#88ddff;font-family:'Orbitron',monospace;font-size:10px;letter-spacing:2px;cursor:pointer;transition:all 0.3s ease;margin-top:4px;}}
        .btn:hover{{border-color:rgba(0,255,255,0.2);color:#00ffff;}}
        .back{{display:block;text-align:center;font-size:8px;font-family:'Orbitron',monospace;color:#88ddff;text-decoration:none;margin-top:10px;letter-spacing:2px;transition:all 0.3s ease;}}
        .back:hover{{color:#00ffff;}}
    </style>
    </head>
    <body>
    <div class="box">
        <h1><span class="hl">edit</span> reseller</h1>
        <div class="sub">{username}</div>
        <form method="POST">
            <div class="form-group">
                <label><i class="fas fa-tag"></i> brand name</label>
                <input type="text" name="brand_name" value="{brand_name}" placeholder="Brand name">
            </div>
            <div class="form-group">
                <label><i class="fas fa-key"></i> new password (optional)</label>
                <input type="password" name="password" placeholder="leave blank to keep">
            </div>
            <div class="form-group">
                <label><i class="fas fa-clock"></i> expiry (UTC)</label>
                <input type="datetime-local" name="expiry" value="{expiry_local}">
                <span style="font-size:7px; color:#88ddff;">leave empty = never expires</span>
            </div>
            <button type="submit" class="btn"><i class="fas fa-save"></i> update</button>
        </form>
        <a href="{url_for('admin_dashboard')}" class="back"><i class="fas fa-arrow-left"></i> back</a>
    </div>
    </body>
    </html>
    '''

@app.route('/admin/add-user', methods=['POST'])
@admin_session_required
def admin_add_user():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    reseller_id = request.form.get('reseller_id', '').strip()
    expiry_str = request.form.get('expiry', '')

    if not username or not password:
        flash("Username and password required", "error")
        return redirect(url_for('admin_dashboard'))

    users = get_users()
    if username in users:
        flash("Username already exists", "error")
        return redirect(url_for('admin_dashboard'))

    users[username] = {
        "password": hashlib.sha256(password.encode()).hexdigest(),
        "role": "user",
        "active": True,
        "created": datetime.datetime.utcnow().isoformat(),
        "created_by": "main_admin"
    }

    if reseller_id:
        resellers = get_resellers()
        if reseller_id in resellers:
            users[username]["reseller_id"] = reseller_id
            users[username]["created_by"] = reseller_id

    if expiry_str:
        try:
            dt = datetime.datetime.fromisoformat(expiry_str)
            users[username]["expiry_utc"] = dt.strftime('%Y-%m-%dT%H:%M:%S+00:00')
        except:
            flash("Invalid expiry format", "error")
            return redirect(url_for('admin_dashboard'))

    if save_users(users):
        if reseller_id:
            resellers = get_resellers()
            if reseller_id in resellers:
                resellers[reseller_id]["user_count"] = len([u for u, d in users.items() if d.get("reseller_id") == reseller_id and d.get("active")])
                save_resellers(resellers)
        flash(f"User '{username}' created", "success")
    else:
        flash("Error creating user", "error")

    return redirect(url_for('admin_dashboard'))

@app.route('/admin/toggle/<username>')
@admin_session_required
def admin_toggle_user(username):
    users = get_users()
    if username not in users:
        flash("User not found", "error")
        return redirect(url_for('admin_dashboard'))
    if username == "sakil2026":
        flash("Cannot toggle main admin", "error")
        return redirect(url_for('admin_dashboard'))

    users[username]["active"] = not users[username].get("active", True)
    save_users(users)
    flash(f"User {'enabled' if users[username]['active'] else 'disabled'}", "success")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete/<username>')
@admin_session_required
def admin_delete_user(username):
    users = get_users()
    if username not in users:
        flash("User not found", "error")
        return redirect(url_for('admin_dashboard'))
    if username == "sakil2026":
        flash("Cannot delete main admin", "error")
        return redirect(url_for('admin_dashboard'))

    del users[username]
    save_users(users)
    flash(f"User '{username}' deleted", "success")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/edit/<username>', methods=['GET', 'POST'])
@admin_session_required
def admin_edit_user(username):
    users = get_users()
    if username not in users:
        flash("User not found", "error")
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        new_password = request.form.get('password', '').strip()
        role = request.form.get('role', 'user')
        expiry_str = request.form.get('expiry', '')
        reseller_id = request.form.get('reseller_id', '').strip()

        if new_password:
            users[username]["password"] = hashlib.sha256(new_password.encode()).hexdigest()
        users[username]["role"] = role
        if expiry_str:
            try:
                dt = datetime.datetime.fromisoformat(expiry_str)
                users[username]["expiry_utc"] = dt.strftime('%Y-%m-%dT%H:%M:%S+00:00')
            except:
                flash("Invalid expiry format", "error")
                return redirect(url_for('admin_edit_user', username=username))
        else:
            users[username]["expiry_utc"] = None

        if reseller_id:
            resellers = get_resellers()
            if reseller_id in resellers:
                users[username]["reseller_id"] = reseller_id
            else:
                users[username]["reseller_id"] = None
        else:
            users[username]["reseller_id"] = None

        save_users(users)
        flash("User updated", "success")
        return redirect(url_for('admin_dashboard'))

    expiry_local = ""
    if users[username].get("expiry_utc"):
        try:
            dt = datetime.datetime.fromisoformat(users[username]["expiry_utc"].replace('Z', '+00:00'))
            expiry_local = dt.strftime('%Y-%m-%dT%H:%M')
        except:
            pass

    resellers = get_resellers()
    reseller_options = ""
    for r in resellers:
        selected = "selected" if users[username].get("reseller_id") == r else ""
        reseller_options += f'<option value="{r}" {selected}>{r} ({resellers[r]["brand_name"]})</option>'

    return f'''
    <!DOCTYPE html>
    <html><head><title>edit user</title>
    <style>
        *{{margin:0;padding:0;box-sizing:border-box;}}
        body{{background:#06060a;display:flex;justify-content:center;align-items:center;min-height:100vh;font-family:'Inter',sans-serif;}}
        .box{{background:rgba(6,6,12,0.95);border:1px solid rgba(0,255,255,0.1);border-radius:20px;padding:30px;max-width:400px;width:92%;}}
        h1{{font-family:'Orbitron',monospace;font-size:18px;font-weight:700;color:#fff;letter-spacing:2px;text-align:center;}}
        h1 .hl{{color:#00ffff;}}
        .sub{{text-align:center;font-size:8px;font-family:'Orbitron',monospace;color:#88ddff;letter-spacing:3px;margin-bottom:16px;}}
        .form-group{{margin-bottom:12px;}}
        label{{display:block;font-size:8px;font-family:'Orbitron',monospace;color:#88ddff;letter-spacing:2px;margin-bottom:3px;}}
        input,select{{width:100%;padding:8px 12px;background:rgba(0,0,0,0.2);border:1px solid rgba(0,255,255,0.05);border-radius:8px;color:#fff;font-size:13px;outline:none;font-family:'Inter',sans-serif;margin-top:2px;}}
        input:focus,select:focus{{border-color:rgba(0,255,255,0.15);}}
        select option{{background:#0a0a1a;color:#fff;}}
        .btn{{width:100%;padding:10px;background:rgba(0,255,255,0.03);border:1px solid rgba(0,255,255,0.05);border-radius:8px;color:#88ddff;font-family:'Orbitron',monospace;font-size:10px;letter-spacing:2px;cursor:pointer;transition:all 0.3s ease;margin-top:4px;}}
        .btn:hover{{border-color:rgba(0,255,255,0.2);color:#00ffff;}}
        .back{{display:block;text-align:center;font-size:8px;font-family:'Orbitron',monospace;color:#88ddff;text-decoration:none;margin-top:10px;letter-spacing:2px;transition:all 0.3s ease;}}
        .back:hover{{color:#00ffff;}}
    </style>
    </head>
    <body>
    <div class="box">
        <h1><span class="hl">edit</span> user</h1>
        <div class="sub">{username}</div>
        <form method="POST">
            <div class="form-group">
                <label><i class="fas fa-key"></i> new password (optional)</label>
                <input type="password" name="password" placeholder="leave blank to keep">
            </div>
            <div class="form-group">
                <label><i class="fas fa-user-tag"></i> role</label>
                <select name="role">
                    <option value="user" {"selected" if users[username].get("role")=="user" else ""}>user</option>
                    <option value="reseller" {"selected" if users[username].get("role")=="reseller" else ""}>reseller</option>
                    <option value="main_admin" {"selected" if users[username].get("role")=="main_admin" else ""}>main_admin</option>
                </select>
            </div>
            <div class="form-group">
                <label><i class="fas fa-store"></i> reseller id</label>
                <select name="reseller_id">
                    <option value="">none (direct)</option>
                    {reseller_options}
                </select>
            </div>
            <div class="form-group">
                <label><i class="fas fa-clock"></i> expiry (UTC)</label>
                <input type="datetime-local" name="expiry" value="{expiry_local}">
                <span style="font-size:7px; color:#88ddff;">leave empty = never expires</span>
            </div>
            <button type="submit" class="btn"><i class="fas fa-save"></i> update</button>
        </form>
        <a href="{url_for('admin_dashboard')}" class="back"><i class="fas fa-arrow-left"></i> back</a>
    </div>
    </body>
    </html>
    '''

# ============================================
# API ROUTES
# ============================================

@app.route('/api/lookup', methods=['POST'])
def lookup():
    try:
        data = request.get_json()
        number = data.get('number', '').strip()

        if not number:
            return jsonify({"status": "error", "message": "Phone number required"})

        clean_number = re.sub(r'[\+\s\-]', '', number)
        params = {'key': 'anish-exploits', 'type': 'number', 'num': clean_number}

        response = requests.get('https://exploitsindia.site/osint/api.php', params=params, timeout=30)
        response.raise_for_status()
        api_data = response.json()

        if api_data.get('status') == 'error':
            return jsonify(api_data)

        result = api_data.get('result', [])
        if result and len(result) > 0:
            info = result[0]
            address = info.get('address', info.get('location', ''))
            if 'lat' not in info and 'lng' not in info and address and address != 'N/A':
                try:
                    geocode_url = f"https://maps.googleapis.com/maps/api/geocode/json?address={urllib.parse.quote(address)}&key=AIzaSyBFw0Qbyq9zTFTd-tUY6dZWTgaQzuU17R8"
                    geo_response = requests.get(geocode_url, timeout=10)
                    geo_data = geo_response.json()
                    if geo_data['status'] == 'OK' and len(geo_data['results']) > 0:
                        loc = geo_data['results'][0]['geometry']['location']
                        info['lat'] = loc['lat']
                        info['lng'] = loc['lng']
                except:
                    pass

        return jsonify({
            "status": "success",
            "result": result
        })

    except requests.exceptions.Timeout:
        return jsonify({"status": "error", "message": "API timeout"})
    except requests.exceptions.RequestException as e:
        return jsonify({"status": "error", "message": f"API error: {str(e)}"})
    except Exception as e:
        return jsonify({"status": "error", "message": f"Server error: {str(e)}"})

@app.route('/api/expiry-status')
def api_expiry_status():
    remaining = get_system_remaining()
    settings = get_settings()
    return jsonify({
        "remaining_seconds": remaining,
        "expiry_utc": settings.get("expiry_utc", ""),
        "is_active": remaining > 0,
        "redirect_url": settings.get("redirect_url", "https://wa.me/919242428894")
    })

# ============================================
# REDIRECTS & MAIN
# ============================================

@app.route('/')
def index():
    return redirect(url_for('user_login_page'))

@app.route('/admin')
def admin_redirect():
    return redirect(url_for('admin_login_page'))

@app.route('/reseller')
def reseller_redirect():
    return redirect(url_for('reseller_login_page'))

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    print("="*60)
    print("⚡ SAKIL BHAI - MULTI-PANEL SYSTEM v10.0")
    print("🔥 SEPARATE PANELS · SEPARATE LOGINS")
    print("📍 PERFECT LOCATION TRACKING - RED BORDER")
    print("="*60)
    print(f"✅ User Login:     http://0.0.0.0:{port}/user-login")
    print(f"✅ User Panel:     http://0.0.0.0:{port}/user-dashboard")
    print(f"✅ Reseller Login: http://0.0.0.0:{port}/reseller-login")
    print(f"✅ Reseller Panel: http://0.0.0.0:{port}/reseller-dashboard")
    print(f"✅ Admin Login:    http://0.0.0.0:{port}/admin-login")
    print(f"✅ Admin Panel:    http://0.0.0.0:{port}/admin-dashboard")
    print("="*60)
    print("🔑 Default Main Admin: sakil2026 / sakil2026")
    print("📁 Firebase: sakil-paid-hack-sell-1342007")
    print("="*60)
    print("💡 Separate Panel System:")
    print("   - Each panel has its own login page")
    print("   - Users see reseller's brand name")
    print("   - Resellers manage their own users")
    print("   - Main admin controls everything")
    print("   - Sessions are independent per panel")
    print("="*60)

    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)    "messagingSenderId": "1052436591563",
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
                "device_limit": 999999,
                "settings": {
                    "default_device_limit": 5
                }
            }
        }
        fb_set("owners", owners)
    return owners

def get_resellers():
    return fb_get("resellers") or {}

def get_users():
    return fb_get("users") or {}

def get_device_logs():
    return fb_get("device_logs") or {}

def get_settings():
    settings = fb_get("settings")
    if not settings:
        settings = {
            "expiry_utc": "2026-12-31T23:59:59+00:00",
            "redirect_url": "https://wa.me/919242428894",
            "default_device_limit": 5
        }
        fb_set("settings", settings)
    return settings

def save_settings(settings):
    return fb_set("settings", settings)

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

# ---- DEVICE LIMIT ----
def get_device_count(username, role="user"):
    logs = get_device_logs()
    count = 0
    for key, entry in logs.items():
        if entry.get("username") == username and entry.get("role") == role and entry.get("active", False):
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
    if role == "owner":
        return 999999
    elif role == "reseller":
        resellers = get_resellers()
        data = resellers.get(username, {})
        return data.get("device_limit", 15)
    else:  # user
        users = get_users()
        data = users.get(username, {})
        return data.get("device_limit", 5)

def check_device_limit(username, role="user"):
    current = get_device_count(username, role)
    limit = get_device_limit(username, role)
    return current < limit

def register_device(username, role, device_id=None, ip=None, user_agent=None):
    if not device_id:
        device_id = str(uuid.uuid4())
    logs = get_device_logs()
    for key, entry in logs.items():
        if entry.get("username") == username and entry.get("device_id") == device_id:
            logs[key]["last_active"] = datetime.datetime.utcnow().isoformat()
            logs[key]["ip"] = ip or logs[key].get("ip")
            logs[key]["user_agent"] = user_agent or logs[key].get("user_agent")
            logs[key]["expires_at"] = (datetime.datetime.utcnow() + datetime.timedelta(days=7)).isoformat()
            fb_set("device_logs", logs)
            return key
    if not check_device_limit(username, role):
        return None
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
    logs = get_device_logs()
    for key, entry in logs.items():
        if entry.get("username") == username and entry.get("device_id") == device_id:
            logs[key]["active"] = False
            logs[key]["expires_at"] = datetime.datetime.utcnow().isoformat()
            fb_set("device_logs", logs)
            return True
    return False

def logout_all_devices(username):
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
# DECORATORS
# ===========================================================

def owner_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get("role") == "owner" and session.get("authenticated"):
            return f(*args, **kwargs)
        return redirect(url_for('login_page'))
    return decorated

def reseller_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get("role") in ["owner", "reseller"] and session.get("authenticated"):
            return f(*args, **kwargs)
        return redirect(url_for('login_page'))
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
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("authenticated"):
            return redirect(url_for('login_page'))
        username = session.get("username")
        role = session.get("role")
        device_id = session.get("device_id")
        if not device_id:
            device_id = str(uuid.uuid4())
            session["device_id"] = device_id
            if not check_device_limit(username, role):
                flash(f"Device limit exceeded! Max {get_device_limit(username, role)} devices.", "error")
                session.clear()
                return redirect(url_for('login_page'))
            register_device(username, role, device_id, request.remote_addr, request.headers.get('User-Agent'))
        else:
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
                                    logs[key]["last_active"] = datetime.datetime.utcnow().isoformat()
                                    fb_set("device_logs", logs)
                            except:
                                valid = True
                        else:
                            valid = True
                    break
            if not valid:
                session.clear()
                flash("Device session expired. Please login again.", "error")
                return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated

# ===========================================================
# LOGIN PAGE (UNIFIED)
# ===========================================================
LOGIN_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>DEV BY :- · SAKIL BHAI</title>
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
        .bg-animation {
            position: fixed;
            top: 0; left: 0; width: 100%; height: 100%;
            z-index: 0;
            overflow: hidden;
        }
        .bg-animation .orb {
            position: absolute;
            border-radius: 50%;
            filter: blur(80px);
            animation: orbFloat 20s ease-in-out infinite;
        }
        .bg-animation .orb:nth-child(1) {
            width: 400px; height: 400px;
            background: rgba(0, 255, 255, 0.03);
            top: -100px; left: -100px;
            animation-delay: 0s;
        }
        .bg-animation .orb:nth-child(2) {
            width: 500px; height: 500px;
            background: rgba(0, 255, 102, 0.02);
            bottom: -150px; right: -150px;
            animation-delay: -5s;
        }
        .bg-animation .orb:nth-child(3) {
            width: 300px; height: 300px;
            background: rgba(255, 0, 255, 0.015);
            top: 50%; left: 50%;
            transform: translate(-50%, -50%);
            animation-delay: -10s;
        }
        @keyframes orbFloat {
            0%, 100% { transform: translate(0, 0) scale(1); }
            33% { transform: translate(30px, -30px) scale(1.1); }
            66% { transform: translate(-20px, 20px) scale(0.9); }
        }
        .login-container {
            position: relative;
            z-index: 1;
            background: rgba(6, 6, 12, 0.92);
            border: 1px solid rgba(0, 255, 255, 0.15);
            border-radius: 24px;
            padding: 48px 40px;
            max-width: 420px;
            width: 92%;
            backdrop-filter: blur(40px);
            box-shadow: 0 0 80px rgba(0, 255, 255, 0.05), inset 0 0 80px rgba(0, 255, 255, 0.005);
            animation: containerIn 0.8s cubic-bezier(0.16, 1, 0.3, 1);
        }
        @keyframes containerIn {
            0% { opacity: 0; transform: translateY(30px) scale(0.96); }
            100% { opacity: 1; transform: translateY(0) scale(1); }
        }
        .login-container .brand-section {
            text-align: center;
            margin-bottom: 32px;
        }
        .login-container .brand-section .icon-wrap {
            display: inline-block;
            font-size: 32px;
            color: #00ffff;
            opacity: 0.5;
            margin-bottom: 4px;
        }
        .login-container .brand-section h1 {
            font-family: 'Orbitron', monospace;
            font-size: 22px;
            font-weight: 800;
            letter-spacing: 4px;
            color: #ffffff;
        }
        .login-container .brand-section h1 .highlight {
            color: #00ffff;
            text-shadow: 0 0 40px rgba(0, 255, 255, 0.2);
        }
        .login-container .brand-section .tagline {
            font-size: 9px;
            font-weight: 400;
            letter-spacing: 6px;
            color: #88ddff;
            text-transform: uppercase;
            margin-top: 2px;
            font-family: 'Orbitron', monospace;
        }
        .login-container .brand-section .divider {
            width: 40px;
            height: 1px;
            background: rgba(0, 255, 255, 0.3);
            margin: 10px auto 0;
        }
        .form-group { margin-bottom: 16px; }
        .form-group label {
            display: block;
            font-size: 9px;
            font-weight: 600;
            color: #88ddff;
            text-transform: uppercase;
            letter-spacing: 3px;
            margin-bottom: 6px;
            font-family: 'Orbitron', monospace;
        }
        .form-group label i { color: #00ffff; margin-right: 6px; }
        .form-group .input-wrap {
            display: flex;
            align-items: center;
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(0, 255, 255, 0.15);
            border-radius: 12px;
            transition: all 0.3s ease;
            overflow: hidden;
        }
        .form-group .input-wrap:focus-within {
            border-color: rgba(0, 255, 255, 0.6);
            box-shadow: 0 0 30px rgba(0, 255, 255, 0.05);
        }
        .form-group .input-wrap .prefix {
            padding: 12px 0 12px 16px;
            color: #88ddff;
            font-size: 13px;
            width: 38px;
            text-align: center;
            font-family: 'Orbitron', monospace;
        }
        .form-group .input-wrap .line {
            width: 1px;
            height: 20px;
            background: rgba(0, 255, 255, 0.1);
        }
        .form-group .input-wrap input {
            flex: 1;
            padding: 12px 16px;
            background: transparent;
            border: none;
            color: #ffffff;
            font-size: 15px;
            outline: none;
            font-family: 'Inter', sans-serif;
            font-weight: 400;
            letter-spacing: 0.5px;
        }
        .form-group .input-wrap input::placeholder {
            color: #88ddff;
            font-size: 13px;
            font-weight: 300;
        }
        .btn-login {
            width: 100%;
            padding: 14px;
            background: rgba(0, 255, 255, 0.05);
            border: 1px solid rgba(0, 255, 255, 0.2);
            border-radius: 12px;
            color: #88ddff;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            font-family: 'Orbitron', monospace;
            letter-spacing: 4px;
            transition: all 0.3s ease;
            text-transform: uppercase;
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 12px;
            margin-top: 4px;
        }
        .btn-login:hover {
            border-color: rgba(0, 255, 255, 0.5);
            color: #00ffff;
            box-shadow: 0 0 40px rgba(0, 255, 255, 0.05);
        }
        .btn-login i { font-size: 14px; color: #00ffff; }
        .error-text {
            color: #ff3355;
            font-size: 11px;
            padding: 6px 0;
            display: none;
            text-align: center;
            font-family: 'Orbitron', monospace;
            letter-spacing: 1px;
        }
        .error-text.show { display: block; animation: shake 0.4s ease; }
        @keyframes shake {
            0%, 100% { transform: translateX(0); }
            25% { transform: translateX(-4px); }
            75% { transform: translateX(4px); }
        }
        .status-bar {
            display: flex;
            justify-content: center;
            gap: 20px;
            margin-top: 18px;
            padding: 10px 14px;
            background: rgba(0, 0, 0, 0.15);
            border-radius: 10px;
            border: 1px solid rgba(0, 255, 255, 0.05);
        }
        .status-bar .item {
            font-size: 7px;
            font-weight: 400;
            color: #88ddff;
            letter-spacing: 2px;
            text-transform: uppercase;
            font-family: 'Orbitron', monospace;
            display: flex;
            align-items: center;
            gap: 4px;
        }
        .status-bar .item i { font-size: 8px; color: #00ffff; }
        .footer-text {
            text-align: center;
            font-size: 6px;
            color: #88ddff;
            letter-spacing: 3px;
            margin-top: 16px;
            font-family: 'Orbitron', monospace;
        }
        .notice-box {
            margin-top: 14px;
            padding: 8px 12px;
            background: rgba(255, 215, 0, 0.03);
            border: 1px solid rgba(255, 215, 0, 0.1);
            border-radius: 8px;
            text-align: center;
            font-size: 7px;
            font-family: 'Orbitron', monospace;
            letter-spacing: 0.5px;
            color: #88ddff;
            line-height: 1.6;
        }
        .notice-box .warn { color: #ff3355; }
        .notice-box .gold { color: #ffd700; }
        @media (max-width: 480px) {
            .login-container { padding: 32px 22px; }
            .login-container .brand-section h1 { font-size: 18px; letter-spacing: 2px; }
            .status-bar { gap: 12px; flex-wrap: wrap; }
        }
    </style>
</head>
<body>
    <div class="bg-animation">
        <div class="orb"></div>
        <div class="orb"></div>
        <div class="orb"></div>
    </div>
    <div class="login-container">
        <div class="brand-section">
            <div class="icon-wrap"><i class="fas fa-shield-halved"></i></div>
            <h1><span class="highlight">SAKIL</span> BHAI</h1>
            <div class="tagline">premium · hacking · system</div>
            <div class="divider"></div>
        </div>
        <form method="POST" action="{{ url_for('login_page') }}">
            <div class="form-group">
                <label><i class="fas fa-user"></i> username</label>
                <div class="input-wrap">
                    <div class="prefix"><i class="fas fa-user"></i></div>
                    <div class="line"></div>
                    <input type="text" name="username" placeholder="Enter username" required autofocus>
                </div>
            </div>
            <div class="form-group">
                <label><i class="fas fa-key"></i> password</label>
                <div class="input-wrap">
                    <div class="prefix"><i class="fas fa-lock"></i></div>
                    <div class="line"></div>
                    <input type="password" name="password" placeholder="Enter password" required>
                </div>
            </div>
            <div class="error-text" id="loginError">{{ error }}</div>
            <button type="submit" class="btn-login"><i class="fas fa-unlock-alt"></i> unlock system</button>
        </form>
        <div class="status-bar">
            <span class="item"><i class="fas fa-database"></i> firebase</span>
            <span class="item"><i class="fas fa-clock"></i> {{ remaining_minutes }}m</span>
            <span class="item"><i class="fas fa-shield-alt"></i> secure</span>
        </div>
        <div class="notice-box">
            <span class="warn">⚠</span> This Number Information Paid Server Hacking System is currently <span class="warn">not working</span>.<br>
            Please <span style="color:#00ffff;">buy new VIP subscription</span> to continue.
        </div>
        <div class="footer-text">⚡ sakil bhai · premium system ⚡</div>
    </div>
    <script>
        document.querySelector('input[name="username"]').focus();
        document.querySelectorAll('input').forEach(el => {
            el.addEventListener('input', function() {
                document.getElementById('loginError').classList.remove('show');
            });
        });
    </script>
</body>
</html>
'''

# ===========================================================
# USER PANEL (v8.0 FULL - 100% SAME)
# ===========================================================
USER_PANEL_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>SAKIL BHAI · PREMIUM SYSTEM</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;800;900&family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', sans-serif;
            background: #06060a;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            overflow-x: hidden;
            -webkit-user-select: none;
        }
        * { -webkit-user-select: none; -moz-user-select: none; -ms-user-select: none; user-select: none; }
        input, textarea { -webkit-user-select: text; -moz-user-select: text; -ms-user-select: text; user-select: text; }
        .bg-animation {
            position: fixed;
            top: 0; left: 0; width: 100%; height: 100%;
            z-index: 0;
            pointer-events: none;
            overflow: hidden;
        }
        .bg-animation .orb {
            position: absolute;
            border-radius: 50%;
            filter: blur(100px);
            animation: orbFloat 25s ease-in-out infinite;
        }
        .bg-animation .orb:nth-child(1) {
            width: 500px; height: 500px;
            background: rgba(0, 255, 255, 0.015);
            top: -150px; left: -150px;
        }
        .bg-animation .orb:nth-child(2) {
            width: 600px; height: 600px;
            background: rgba(0, 255, 102, 0.01);
            bottom: -200px; right: -200px;
            animation-delay: -8s;
        }
        .bg-animation .orb:nth-child(3) {
            width: 300px; height: 300px;
            background: rgba(255, 0, 255, 0.008);
            top: 50%; left: 50%;
            transform: translate(-50%, -50%);
            animation-delay: -15s;
        }
        @keyframes orbFloat {
            0%, 100% { transform: translate(0, 0) scale(1); }
            33% { transform: translate(40px, -40px) scale(1.1); }
            66% { transform: translate(-30px, 30px) scale(0.9); }
        }
        .session-bar {
            width: 100%; height: 2px; background: rgba(0,0,0,0.5);
            position: fixed; top: 0; left: 0; z-index: 1000;
        }
        .session-bar .fill {
            height: 100%; background: linear-gradient(90deg, #00ff66, #00ffff);
            width: 100%; transition: width 1s linear;
            box-shadow: 0 0 30px rgba(0,255,255,0.02);
        }
        .session-bar .fill.warning { background: linear-gradient(90deg, #FF9933, #ff3355); }
        .tricolor {
            width: 100%; height: 3px; display: flex;
            position: fixed; top: 2px; left: 0; z-index: 999;
        }
        .tricolor .saffron { width: 33.33%; background: #FF9933; }
        .tricolor .white { width: 33.33%; background: #FFFFFF; }
        .tricolor .green { width: 33.34%; background: #138808; }
        .top-bar {
            width: 100%; background: rgba(0,0,0,0.8); padding: 6px 0;
            margin-top: 5px; position: sticky; top: 5px; z-index: 100;
            border-bottom: 1px solid rgba(0,255,255,0.1);
            backdrop-filter: blur(20px);
        }
        .top-bar .container {
            max-width: 1200px; margin: 0 auto; padding: 0 16px;
            display: flex; justify-content: space-between; align-items: center;
            flex-wrap: wrap; gap: 6px;
        }
        .top-bar .left {
            font-size: 8px; font-family: 'Orbitron', monospace;
            color: #88ddff; letter-spacing: 3px;
        }
        .top-bar .left i { color: #00ffff; margin-right: 4px; }
        .top-bar .right {
            font-size: 8px; font-family: 'Orbitron', monospace;
            color: #88ddff; letter-spacing: 1px;
        }
        .top-bar .right i { color: #00ffff; margin-right: 4px; }
        .main-header {
            width: 100%; background: rgba(0,0,0,0.85); padding: 12px 0;
            border-bottom: 1px solid rgba(0,255,255,0.1);
            backdrop-filter: blur(20px);
        }
        .main-header .container {
            max-width: 1200px; margin: 0 auto; padding: 0 16px;
            display: flex; justify-content: space-between; align-items: center;
            flex-wrap: wrap; gap: 10px;
        }
        .main-header .brand {
            display: flex; align-items: center; gap: 12px;
        }
        .main-header .brand img {
            width: 40px; height: 40px; border-radius: 50%;
            border: 1px solid rgba(0,255,255,0.2);
            object-fit: cover; background: rgba(0,0,0,0.3);
            padding: 2px;
        }
        .main-header .brand .text h1 {
            font-family: 'Orbitron', monospace;
            font-size: 16px; font-weight: 700;
            color: #fff; letter-spacing: 2px;
        }
        .main-header .brand .text h1 .hl { color: #00ffff; }
        .main-header .brand .text .sub {
            font-size: 7px; font-family: 'Orbitron', monospace;
            color: #88ddff; letter-spacing: 4px;
            text-transform: uppercase;
        }
        .main-header .brand .text .sub i { color: #00ff66; font-size: 5px; margin-right: 3px; }
        .main-header .status {
            display: flex; align-items: center; gap: 10px;
            background: rgba(0,0,0,0.2); padding: 4px 14px;
            border-radius: 30px; border: 1px solid rgba(0,255,255,0.1);
        }
        .main-header .status .dot {
            width: 5px; height: 5px; border-radius: 50%;
            background: #00ff66; animation: pulse 1.5s infinite;
            box-shadow: 0 0 20px rgba(0,255,102,0.01);
        }
        @keyframes pulse { 0%,100%{opacity:1}50%{opacity:0.1} }
        .main-header .status span {
            font-size: 7px; font-family: 'Orbitron', monospace;
            color: #88ddff; letter-spacing: 2px;
        }
        .main-header .status .timer {
            font-size: 11px; font-weight: 600;
            color: #00ffff; font-family: 'Orbitron', monospace;
            padding: 1px 8px; border: 1px solid rgba(0,255,255,0.15);
            border-radius: 4px; background: rgba(0,255,255,0.05);
        }
        .main-header .status .role {
            font-size: 6px; font-family: 'Orbitron', monospace;
            padding: 1px 10px; border-radius: 30px;
            border: 1px solid rgba(255,255,255,0.05);
            color: #88ddff;
        }
        .main-header .status .role.admin { border-color: rgba(0,255,102,0.2); color: #00ff66; }
        .main-container {
            max-width: 560px; width: 100%; padding: 18px 14px;
            margin: 16px 0 30px; position: relative; z-index: 1;
        }
        .card {
            background: rgba(6,6,12,0.94);
            border: 1px solid rgba(0,255,255,0.1);
            border-radius: 20px;
            overflow: hidden;
            backdrop-filter: blur(30px);
            box-shadow: 0 8px 60px rgba(0,0,0,0.6);
        }
        .card-header {
            padding: 18px 22px; text-align: center;
            border-bottom: 1px solid rgba(0,255,255,0.05);
            background: rgba(0,0,0,0.2);
        }
        .card-header .badge {
            font-size: 7px; font-family: 'Orbitron', monospace;
            color: #88ddff; letter-spacing: 4px;
            text-transform: uppercase;
            border: 1px solid rgba(0,255,255,0.1);
            padding: 2px 14px; border-radius: 30px;
            display: inline-block; margin-bottom: 6px;
        }
        .card-header .badge i { color: #ffd700; font-size: 6px; margin-right: 4px; }
        .card-header .credit-badge {
            font-size: 8px;
            font-family: 'Inter', sans-serif;
            color: #ffd700;
            letter-spacing: 2px;
            background: rgba(255, 215, 0, 0.05);
            border: 1px solid rgba(255, 215, 0, 0.1);
            padding: 4px 14px;
            border-radius: 30px;
            display: inline-block;
            margin-bottom: 8px;
        }
        .card-header .credit-badge i { color: #ffd700; margin-right: 6px; }
        .card-header img {
            width: 48px; height: 48px; border-radius: 50%;
            border: 1px solid rgba(0,255,255,0.1);
            object-fit: cover; margin: 0 auto 6px; display: block;
            background: rgba(0,0,0,0.3); padding: 2px;
        }
        .card-header h2 {
            font-family: 'Orbitron', monospace;
            font-size: 18px; font-weight: 700;
            color: #fff; letter-spacing: 2px;
        }
        .card-header h2 .hl { color: #00ffff; }
        .card-header .sub {
            font-size: 8px; font-family: 'Orbitron', monospace;
            color: #88ddff; letter-spacing: 4px;
            margin-top: 2px;
        }
        .card-header .sub i { color: #00ff66; font-size: 6px; margin-right: 4px; }
        .card-body { padding: 20px 22px; }
        .form-group { margin-bottom: 14px; }
        .form-group label {
            display: block; font-size: 8px; font-weight: 600;
            color: #88ddff; text-transform: uppercase;
            letter-spacing: 3px; margin-bottom: 4px;
            font-family: 'Orbitron', monospace;
        }
        .form-group label i { color: #00ffff; margin-right: 4px; font-size: 8px; }
        .input-wrap {
            display: flex; align-items: center;
            background: rgba(0,0,0,0.3);
            border: 1px solid rgba(0,255,255,0.1);
            border-radius: 12px; transition: all 0.3s ease;
            overflow: hidden;
        }
        .input-wrap:focus-within { border-color: rgba(0,255,255,0.4); }
        .input-wrap .code {
            padding: 10px 6px 10px 14px;
            color: #88ddff; font-size: 12px;
            font-family: 'Orbitron', monospace;
            border-right: 1px solid rgba(0,255,255,0.05);
        }
        .input-wrap input {
            flex: 1; padding: 10px 14px;
            background: transparent; border: none;
            color: #fff; font-size: 15px; outline: none;
            font-family: 'Inter', sans-serif; font-weight: 400;
            letter-spacing: 0.5px;
        }
        .input-wrap input::placeholder {
            color: #88ddff; font-size: 13px;
        }
        .status-line {
            display: flex; align-items: center; gap: 10px;
            padding: 2px 0 10px; font-size: 9px;
            color: #88ddff;
            font-family: 'Orbitron', monospace; letter-spacing: 1px;
        }
        .status-line .dot {
            width: 4px; height: 4px; border-radius: 50%;
            background: #00ff66; animation: pulse 1.5s infinite;
        }
        .status-line .dot.err { background: #ff3355; }
        .btn-execute {
            width: 100%; padding: 13px;
            background: rgba(0,255,255,0.05);
            border: 1px solid rgba(0,255,255,0.2);
            border-radius: 12px;
            color: #88ddff;
            font-size: 12px; font-weight: 600;
            cursor: pointer; font-family: 'Orbitron', monospace;
            letter-spacing: 4px; text-transform: uppercase;
            transition: all 0.3s ease;
            display: flex; justify-content: center; align-items: center;
            gap: 12px;
        }
        .btn-execute:hover {
            border-color: rgba(0,255,255,0.5);
            color: #00ffff;
        }
        .btn-execute:disabled { opacity: 0.2; cursor: not-allowed; }
        .btn-execute i { font-size: 13px; color: #00ffff; }
        .error-text {
            color: #ff3355;
            font-size: 10px; padding: 4px 0;
            display: none; font-family: 'Orbitron', monospace;
            letter-spacing: 1px;
        }
        .error-text.show { display: block; animation: shake 0.4s ease; }
        @keyframes shake { 0%,100%{transform:translateX(0)}25%{transform:translateX(-4px)}75%{transform:translateX(4px)} }
        .result-box {
            margin-top: 16px;
            border: 1px solid rgba(0,255,255,0.05);
            border-radius: 12px; overflow: hidden;
            display: none; background: rgba(0,0,0,0.1);
        }
        .result-box.show { display: block; animation: slideUp 0.4s ease; }
        @keyframes slideUp { 0%{opacity:0;transform:translateY(10px)}100%{opacity:1;transform:translateY(0)} }
        .result-header {
            padding: 8px 16px; display: flex;
            justify-content: space-between; align-items: center;
            border-bottom: 1px solid rgba(0,255,255,0.03);
            background: rgba(0,0,0,0.1);
        }
        .result-header .title {
            font-size: 8px; font-family: 'Orbitron', monospace;
            color: #88ddff; letter-spacing: 2px;
        }
        .result-header .title i { color: #00ffff; margin-right: 4px; }
        .result-header .count {
            font-size: 7px; font-family: 'Orbitron', monospace;
            color: #88ddff;
            background: rgba(0,0,0,0.1); padding: 1px 10px;
            border-radius: 20px;
        }
        .result-item {
            display: flex; padding: 8px 16px;
            border-bottom: 1px solid rgba(255,255,255,0.02);
        }
        .result-item:last-child { border-bottom: none; }
        .result-item .label {
            font-size: 8px; font-weight: 600; font-family: 'Orbitron', monospace;
            color: #88ddff; width: 30%;
            display: flex; align-items: center; gap: 6px;
            text-transform: uppercase; letter-spacing: 1px;
        }
        .result-item .label i { font-size: 10px; color: #00ffff; width: 14px; }
        .result-item .value {
            font-size: 12px; font-weight: 400;
            color: #ccddff; width: 70%;
            text-align: right; font-family: 'Inter', sans-serif;
            word-break: break-word;
        }
        .result-item .value.hl { color: #00ffff; font-weight: 500; }
        .result-item .value.gr { color: #00ff66; font-weight: 500; }
        .result-item .value.addr { font-size: 10px; color: #88ddff; line-height: 1.4; }

        /* ============================================
           LOCATION SECTION - PERFECT BORDER STYLES
           ============================================ */
        .location-section {
            margin-top: 14px;
            border: 3px solid #00ff66;
            border-radius: 14px;
            overflow: hidden;
            display: none;
            background: rgba(0,0,0,0.1);
            box-shadow: 0 0 40px rgba(0, 255, 102, 0.08), inset 0 0 40px rgba(0, 255, 102, 0.02);
            transition: all 0.4s ease;
        }
        .location-section.show { 
            display: block; 
            animation: slideUp 0.5s ease;
        }
        /* LIVE লোকেশন হলে বর্ডার লাল হবে */
        .location-section.live {
            border-color: #ff0000 !important;
            box-shadow: 0 0 50px rgba(255, 0, 0, 0.15), inset 0 0 50px rgba(255, 0, 0, 0.03) !important;
        }
        /* AREA লোকেশন হলে বর্ডার লাল হবে (রেড বর্ডার) */
        .location-section.area {
            border-color: #ff0000 !important;
            box-shadow: 0 0 40px rgba(255, 0, 0, 0.08), inset 0 0 40px rgba(255, 0, 0, 0.02) !important;
        }
        .location-section .map-container {
            position: relative;
            width: 100%;
            padding-bottom: 56.25%;
            background: #0a0a1a;
            cursor: pointer;
        }
        .location-section .map-container iframe {
            position: absolute;
            top: 0; left: 0;
            width: 100%; height: 100%;
            border: none;
            border-radius: 0;
        }
        .location-section .map-container .location-badge {
            position: absolute;
            top: 12px;
            right: 12px;
            background: rgba(0,0,0,0.75);
            backdrop-filter: blur(10px);
            padding: 4px 14px;
            border-radius: 20px;
            font-size: 8px;
            font-family: 'Orbitron', monospace;
            color: #00ff66;
            border: 1px solid rgba(0,255,102,0.2);
            z-index: 10;
            letter-spacing: 1px;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .location-section .map-container .location-badge i {
            font-size: 10px;
        }
        .location-section .map-container .location-badge.live { 
            color: #ff0000; 
            border-color: rgba(255,0,0,0.3);
            animation: pulseBadge 1.5s ease-in-out infinite;
        }
        .location-section .map-container .location-badge.area { 
            color: #ff0000; 
            border-color: rgba(255,0,0,0.3);
        }
        @keyframes pulseBadge {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.6; }
        }

        .location-section .map-label {
            padding: 8px 14px;
            font-size: 7px;
            font-family: 'Orbitron', monospace;
            color: #88ddff;
            letter-spacing: 2px;
            text-align: center;
            background: rgba(0,0,0,0.15);
            border-top: 1px solid rgba(0,255,255,0.03);
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 4px;
        }
        .location-section .map-label .hint {
            color: #88ddff;
        }
        .location-section .map-label .hint i {
            color: #ff0000;
            margin-right: 4px;
        }
        .location-section .map-label .open-link {
            font-size: 7px;
            font-family: 'Orbitron', monospace;
            color: #00ffff;
            text-decoration: none;
            padding: 2px 12px;
            border: 1px solid rgba(0,255,255,0.1);
            border-radius: 20px;
            transition: all 0.3s ease;
        }
        .location-section .map-label .open-link:hover {
            background: rgba(0,255,255,0.05);
            border-color: rgba(0,255,255,0.3);
        }
        .result-item.location-item {
            border-left: 4px solid #00ff66;
            background: rgba(0,255,102,0.03);
            border-radius: 4px;
            margin: 2px 0;
            padding: 8px 16px;
        }
        .result-item.location-item .label i { color: #00ff66; }
        .result-item.location-item .value { color: #00ff66; font-weight: 500; }
        /* LIVE হলে লেফট বর্ডার লাল হবে */
        .result-item.location-item.live {
            border-left-color: #ff0000 !important;
            background: rgba(255,0,0,0.03) !important;
        }
        .result-item.location-item.live .label i { color: #ff0000 !important; }
        .result-item.location-item.live .value { color: #ff0000 !important; }
        /* AREA হলে লেফট বর্ডার লাল হবে */
        .result-item.location-item.area {
            border-left-color: #ff0000 !important;
            background: rgba(255,0,0,0.03) !important;
        }
        .result-item.location-item.area .label i { color: #ff0000 !important; }
        .result-item.location-item.area .value { color: #ff0000 !important; }

        .badge-row {
            display: flex; justify-content: center; gap: 16px;
            padding: 10px 14px; margin-top: 12px;
            border: 1px solid rgba(0,255,255,0.03);
            border-radius: 10px; background: rgba(0,0,0,0.05);
            flex-wrap: wrap;
        }
        .badge-row .item {
            font-size: 7px; font-family: 'Orbitron', monospace;
            color: #88ddff; letter-spacing: 1px;
            display: flex; align-items: center; gap: 4px;
        }
        .badge-row .item i { font-size: 9px; color: #ff0000; }
        .social-row {
            margin-top: 12px; padding: 12px 16px;
            border: 1px solid rgba(0,255,255,0.05);
            border-radius: 10px; text-align: center;
            background: rgba(0,0,0,0.03);
        }
        .social-row .title {
            font-size: 7px; font-family: 'Orbitron', monospace;
            color: #88ddff; letter-spacing: 3px;
            text-transform: uppercase; margin-bottom: 8px;
        }
        .social-row .title i { color: #ffd700; font-size: 7px; margin-right: 4px; }
        .social-row .btns { display: flex; justify-content: center; gap: 10px; flex-wrap: wrap; }
        .social-row .btns a {
            font-size: 9px; font-family: 'Inter', sans-serif;
            color: #88ddff; text-decoration: none;
            padding: 4px 14px; border: 1px solid rgba(255,255,255,0.05);
            border-radius: 30px; transition: all 0.3s ease;
        }
        .social-row .btns a:hover { border-color: rgba(0,255,255,0.2); color: #00ffff; }
        .social-row .btns a i { margin-right: 4px; }
        .json-toggle {
            width: 100%; padding: 8px; margin-top: 10px;
            background: transparent; border: 1px solid rgba(255,255,255,0.05);
            border-radius: 8px; color: #88ddff;
            font-size: 7px; font-family: 'Orbitron', monospace;
            letter-spacing: 2px; cursor: pointer;
            transition: all 0.3s ease;
        }
        .json-toggle:hover { border-color: rgba(0,255,255,0.2); color: #00ffff; }
        .json-box {
            margin-top: 8px; background: rgba(0,0,0,0.2);
            border-radius: 8px; padding: 10px;
            font-family: 'Courier New', monospace; font-size: 8px;
            color: #88ddff; display: none;
            max-height: 150px; overflow: auto;
            white-space: pre-wrap; word-break: break-all;
            line-height: 1.5; border: 1px solid rgba(0,255,102,0.05);
        }
        .json-box.show { display: block; }
        .notice {
            margin-top: 10px; padding: 8px 12px;
            border: 1px solid rgba(255,215,0,0.05);
            border-radius: 8px; text-align: center;
            font-size: 6px; font-family: 'Orbitron', monospace;
            color: #88ddff; letter-spacing: 0.5px;
            line-height: 1.6; background: rgba(255,215,0,0.02);
        }
        .notice .w { color: #ff3355; }
        .notice .g { color: #ffd700; }
        .action-row {
            display: flex; justify-content: center; gap: 10px;
            margin-top: 12px; flex-wrap: wrap;
        }
        .action-row a {
            font-size: 8px; font-family: 'Orbitron', monospace;
            color: #88ddff; text-decoration: none;
            padding: 4px 16px; border: 1px solid rgba(255,255,255,0.05);
            border-radius: 30px; letter-spacing: 2px;
            transition: all 0.3s ease;
        }
        .action-row a:hover { border-color: rgba(0,255,255,0.2); color: #00ffff; }
        .action-row a.admin { border-color: rgba(0,255,102,0.1); color: #00ff66; }
        .action-row a.admin:hover { border-color: rgba(0,255,102,0.3); color: #00ff66; }
        .action-row a.logout { border-color: rgba(255,51,85,0.1); color: #ff3355; }
        .action-row a.logout:hover { border-color: rgba(255,51,85,0.3); color: #ff3355; }
        .footer {
            width: 100%; background: rgba(0,0,0,0.85);
            border-top: 1px solid rgba(0,255,255,0.05);
            padding: 14px 0; margin-top: 10px;
            backdrop-filter: blur(20px);
        }
        .footer .container {
            max-width: 1200px; margin: 0 auto; padding: 0 16px;
            text-align: center;
        }
        .footer .links {
            display: flex; justify-content: center;
            gap: 16px; flex-wrap: wrap; margin-bottom: 8px;
        }
        .footer .links a {
            font-size: 7px; font-family: 'Orbitron', monospace;
            color: #88ddff; text-decoration: none;
            letter-spacing: 2px; transition: all 0.3s ease;
        }
        .footer .links a:hover { color: #00ffff; }
        .footer .links a i { margin-right: 3px; }
        .footer .copy {
            font-size: 6px; font-family: 'Orbitron', monospace;
            color: #88ddff; letter-spacing: 3px;
        }
        .footer .copy .b { color: #00ffff; }
        .footer .copy .gold { color: #ffd700; }
        .footer .tricolor {
            width: 100%; height: 2px; display: flex;
            margin-top: 10px;
        }
        .footer .tricolor .saffron { width: 33.33%; background: #FF9933; }
        .footer .tricolor .white { width: 33.33%; background: #FFFFFF; }
        .footer .tricolor .green { width: 33.34%; background: #138808; }
        ::-webkit-scrollbar { width: 3px; }
        ::-webkit-scrollbar-track { background: #06060a; }
        ::-webkit-scrollbar-thumb { background: rgba(0,255,255,0.05); border-radius: 10px; }
        @media (max-width: 480px) {
            .main-header .brand .text h1 { font-size: 13px; letter-spacing: 1px; }
            .main-header .brand img { width: 32px; height: 32px; }
            .main-header .status { padding: 3px 10px; }
            .main-header .status .timer { font-size: 9px; }
            .card-header h2 { font-size: 15px; }
            .card-body { padding: 14px 16px; }
            .result-item { flex-wrap: wrap; padding: 6px 12px; }
            .result-item .label { width: 100%; margin-bottom: 2px; }
            .result-item .value { width: 100%; text-align: left; }
            .main-container { padding: 12px 10px; }
            .badge-row { gap: 10px; }
            .location-section .map-container .location-badge {
                top: 8px; right: 8px;
                font-size: 6px;
                padding: 2px 10px;
            }
        }
    </style>
</head>
<body>
    <div class="session-bar"><div class="fill" id="sessionFill"></div></div>
    <div class="tricolor"><div class="saffron"></div><div class="white"></div><div class="green"></div></div>
    <div class="bg-animation"><div class="orb"></div><div class="orb"></div><div class="orb"></div></div>
    <div class="top-bar">
        <div class="container">
            <div class="left"><i class="fas fa-shield-halved"></i> DEV BY · || SAKIL BHAI ||</div>
            <div class="right"><i class="fas fa-circle" style="color:#00ff66;font-size:5px;"></i> system active</div>
        </div>
    </div>
    <div class="main-header">
        <div class="container">
            <div class="brand">
                <img src="https://i.postimg.cc/1VBJWPhR/IMG-20260724-232723-958.webp" alt="Sakil Bhai" draggable="false">
                <div class="text">
                    <h1><span class="hl">SAKIL</span> BHAI</h1>
                    <div class="sub"><i class="fas fa-circle"></i> premium · hacking · system</div>
                </div>
            </div>
            <div class="status">
                <div class="dot"></div>
                <span>vip</span>
                <span class="timer" id="sessionTimer">--:--</span>
                <span class="role {{ session.get('role', 'user') }}">{{ session.get('role', 'user')|upper }}</span>
                <a href="{{ url_for('logout') }}" style="color:#88ddff; font-size:10px; text-decoration:none;">
                    <i class="fas fa-sign-out-alt"></i>
                </a>
            </div>
        </div>
    </div>
    <div class="main-container">
        <div class="card">
            <div class="card-header">
                <div class="badge"><i class="fas fa-crown"></i> premium · encrypted</div>
                <div class="credit-badge">
                    <i class="fas fa-star"></i> Powered by <strong style="color:#ffd700;">PRIYANGSU</strong> <i class="fas fa-star"></i>
                </div>
                <img src="https://i.postimg.cc/1VBJWPhR/IMG-20260724-232723-958.webp" alt="Sakil Bhai" draggable="false">
                <h2><span class="hl">number</span> information</h2>
                <div class="sub"><i class="fas fa-circle"></i> premium intelligence system</div>
            </div>
            <div class="card-body">
                <form id="trackForm">
                    <div class="form-group">
                        <label><i class="fas fa-phone"></i> enter 10-digit number</label>
                        <div class="input-wrap">
                            <span class="code">+91</span>
                            <input type="tel" id="phoneInput" placeholder="Enter phone number" maxlength="10" inputmode="numeric">
                        </div>
                    </div>
                    <div class="status-line">
                        <span class="dot" id="statusDot"></span>
                        <span id="statusText">system ready</span>
                    </div>
                    <div class="error-text" id="errorText">error</div>
                    <button type="submit" class="btn-execute" id="trackBtn">
                        <i class="fas fa-search"></i> execute search
                    </button>
                </form>
                <div class="result-box" id="resultBox">
                    <div class="result-header">
                        <span class="title"><i class="fas fa-file-alt"></i> intelligence data</span>
                        <span class="count"><i class="fas fa-database"></i> <span id="recordCount">0</span></span>
                    </div>
                    <div id="resultContent"></div>
                </div>

                <!-- ============================================
                📍 LOCATION MAP SECTION - RED BORDER
                ============================================ -->
                <div class="location-section" id="locationSection">
                    <div class="map-container" id="mapContainer">
                        <iframe id="mapIframe"
                            src=""
                            allowfullscreen=""
                            loading="lazy"
                            referrerpolicy="no-referrer-when-downgrade">
                        </iframe>
                        <div class="location-badge" id="locationBadge">
                            <i class="fas fa-satellite-dish"></i>
                            <span id="locationType">LIVE</span>
                        </div>
                    </div>
                    <div class="map-label">
                        <span class="hint"><i class="fas fa-map-pin"></i> <span id="locationLabel">Location</span></span>
                        <a href="#" id="openMapsLink" class="open-link" target="_blank">
                            <i class="fas fa-external-link-alt"></i> Google Maps
                        </a>
                    </div>
                </div>

                <div class="badge-row">
                    <span class="item"><i class="fas fa-lock"></i> ssl</span>
                    <span class="item"><i class="fas fa-shield-halved"></i> secure</span>
                    <span class="item"><i class="fas fa-check-circle"></i> verified</span>
                    <span class="item"><i class="fas fa-clock"></i> 24/7</span>
                </div>
                <div id="apiInfo" style="display:none; margin-top:10px; padding:8px 12px; background:rgba(0,0,0,0.05); border-radius:8px; display:flex; justify-content:center; gap:16px; flex-wrap:wrap; font-size:7px; color:#88ddff; border:1px solid rgba(255,255,255,0.03);"></div>
                <div class="social-row">
                    <div class="title"><i class="fas fa-share-alt"></i> connect with sakil bhai</div>
                    <div class="btns">
                        <a href="https://youtube.com/@elitetv-vip-tv?si=Ye99V2pGV3zxfvXe" target="_blank"><i class="fab fa-youtube"></i> youtube</a>
                        <a href="https://www.instagram.com/__elite__sakil__20k7__?igsh=MXU4OWIyYXdnejFlMw==" target="_blank"><i class="fab fa-instagram"></i> instagram</a>
                        <a href="https://t.me/+r7naPOtOXOoxMGY1" target="_blank"><i class="fab fa-telegram-plane"></i> telegram</a>
                    </div>
                </div>
                <button class="json-toggle" onclick="toggleJson()">
                    <i class="fas fa-code"></i> view raw data
                </button>
                <div class="json-box" id="jsonBox"></div>
                <div class="notice">
                    <span class="w">⚠</span> this number information paid server hacking system is currently <span class="w">not working</span>.<br>
                    please <span class="g">buy new vip subscription</span> to continue using this service.
                </div>
                <div class="action-row">
                    {% if session.get('role') == 'owner' or session.get('role') == 'reseller' %}
                    <a href="{{ url_for('reseller_dashboard') }}" class="admin"><i class="fas fa-store"></i> reseller panel</a>
                    {% endif %}
                    <a href="{{ url_for('logout') }}" class="logout"><i class="fas fa-sign-out-alt"></i> logout</a>
                </div>
            </div>
        </div>
    </div>
    <div class="footer">
        <div class="container">
            <div class="links">
                <a href="#"><i class="fas fa-shield-halved"></i> privacy</a>
                <a href="https://t.me/+r7naPOtOXOoxMGY1" target="_blank"><i class="fas fa-headset"></i> support</a>
                <a href="tel:+919242428894"><i class="fas fa-phone"></i> contact</a>
            </div>
            <div class="copy">⚡ 2026 <span class="b">sakil bhai</span> · premium system ⚡</div>
            <div class="copy" style="font-size:5px; margin-top:4px; color:#ffd700; letter-spacing:2px;">
                <i class="fas fa-star"></i> exclusively powered by <strong>PRIYANGSU</strong> <i class="fas fa-star"></i>
            </div>
            <div class="tricolor"><div class="saffron"></div><div class="white"></div><div class="green"></div></div>
        </div>
    </div>

    <script>
    // ===== SESSION TIMER =====
    let totalSeconds = {{ remaining_seconds }};
    let timerInterval = null;

    function formatTime(sec) {
        const m = Math.floor(sec / 60);
        const s = sec % 60;
        return String(m).padStart(2, '0') + ':' + String(s).padStart(2, '0');
    }

    function updateTimer() {
        const timerEl = document.getElementById('sessionTimer');
        const fillEl = document.getElementById('sessionFill');
        if (!timerEl) return;

        if (totalSeconds <= 0) {
            timerEl.textContent = 'expired';
            fillEl.style.width = '0%';
            fillEl.className = 'fill warning';
            window.location.href = 'https://wa.me/919242428894';
            return;
        }

        timerEl.textContent = formatTime(totalSeconds);
        const maxSec = 3600;
        const pct = Math.max(0, (totalSeconds / maxSec) * 100);
        fillEl.style.width = pct + '%';
        fillEl.className = pct < 20 ? 'fill warning' : 'fill';
        totalSeconds--;
    }

    if ({{ remaining_seconds }} > 0) {
        updateTimer();
        timerInterval = setInterval(updateTimer, 1000);
    } else {
        document.getElementById('sessionTimer').textContent = 'expired';
        window.location.href = 'https://wa.me/919242428894';
    }

    function toggleJson() {
        const box = document.getElementById('jsonBox');
        box.classList.toggle('show');
        if (box.classList.contains('show')) {
            box.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
    }

    // ============================================
    // 📍 LOCATION FUNCTIONS - RED BORDER
    // ============================================

    function updateLocationMap(address, lat, lng, type) {
        const section = document.getElementById('locationSection');
        const iframe = document.getElementById('mapIframe');
        const label = document.getElementById('locationLabel');
        const openLink = document.getElementById('openMapsLink');
        const badge = document.getElementById('locationBadge');
        const locationType = document.getElementById('locationType');

        if (!address || address === 'N/A' || address === 'Unknown' || address === '') {
            section.classList.remove('show');
            section.classList.remove('live', 'area');
            return;
        }

        if (type === 'live') {
            locationType.textContent = '🔴 LIVE';
            badge.className = 'location-badge live';
            section.className = 'location-section show live';
        } else {
            locationType.textContent = '📍 AREA';
            badge.className = 'location-badge area';
            section.className = 'location-section show area';
        }

        let query = address;
        if (lat && lng) {
            query = `${lat},${lng}`;
        }

        const cleanAddress = encodeURIComponent(query);
        const mapUrl = `https://www.google.com/maps/embed/v1/place?key=AIzaSyBFw0Qbyq9zTFTd-tUY6dZWTgaQzuU17R8&q=${cleanAddress}&zoom=16&maptype=roadmap`;

        iframe.src = mapUrl;
        label.textContent = address.substring(0, 60) + (address.length > 60 ? '...' : '');
        openLink.href = `https://www.google.com/maps/search/?api=1&query=${cleanAddress}`;
        section.classList.add('show');

        setTimeout(() => {
            section.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }, 300);
    }

    // ============================================
    // API CALL
    // ============================================

    async function callAPI(number) {
        try {
            const response = await fetch('/api/lookup', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ number: number })
            });
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return await response.json();
        } catch (error) {
            return { status: 'error', message: error.message };
        }
    }

    function displayResults(number, data) {
        const resultBox = document.getElementById('resultBox');
        const resultContent = document.getElementById('resultContent');
        const recordCount = document.getElementById('recordCount');
        const apiInfo = document.getElementById('apiInfo');
        const jsonBox = document.getElementById('jsonBox');
        const errorText = document.getElementById('errorText');
        const locationSection = document.getElementById('locationSection');

        locationSection.classList.remove('show', 'live', 'area');

        jsonBox.textContent = JSON.stringify(data, null, 2);

        if (data.status === 'error') {
            resultBox.classList.remove('show');
            errorText.textContent = '❌ ' + (data.message || 'API Error');
            errorText.classList.add('show');
            return;
        }

        if (data.result && data.result.length > 0) {
            const results = data.result;
            const totalRecords = results.length;
            recordCount.textContent = totalRecords;

            let html = '';
            const info = results[0];

            html += `<div class="result-item">
                <span class="label"><i class="fas fa-phone"></i> phone</span>
                <span class="value hl">${info.num || '+91 ' + number}</span>
            </div>`;
            html += `<div class="result-item">
                <span class="label"><i class="fas fa-user"></i> name</span>
                <span class="value hl">${info.name || 'N/A'}</span>
            </div>`;
            html += `<div class="result-item">
                <span class="label"><i class="fas fa-user-tie"></i> father</span>
                <span class="value">${info.fname || 'N/A'}</span>
            </div>`;
            html += `<div class="result-item">
                <span class="label"><i class="fas fa-id-card"></i> aadhaar</span>
                <span class="value gr">${info.aadhar || 'N/A'}</span>
            </div>`;
            
            const address = info.address || info.location || 'N/A';
            const hasLatLng = (info.lat && info.lng);
            const locationType = hasLatLng ? 'live' : 'area';
            const locationIcon = hasLatLng ? 'fa-satellite-dish' : 'fa-map-pin';
            const locationColor = '#ff0000';
            const locationClass = hasLatLng ? 'live' : 'area';
            
            html += `<div class="result-item location-item ${locationClass}">
                <span class="label"><i class="fas ${locationIcon}" style="color:${locationColor};"></i> location</span>
                <span class="value addr" id="addressValue">${address}</span>
                <span style="font-size:6px; font-family:'Orbitron',monospace; color:#ff0000; margin-left:8px; border:1px solid #ff000040; padding:1px 8px; border-radius:10px; background:#ff000010;">
                    ${hasLatLng ? '🔴 LIVE' : '📍 AREA'}
                </span>
            </div>`;
            
            html += `<div class="result-item">
                <span class="label"><i class="fas fa-signal"></i> circle</span>
                <span class="value">${info.circle || 'N/A'}</span>
            </div>`;
            if (info.alt) {
                html += `<div class="result-item">
                    <span class="label"><i class="fas fa-phone-plus"></i> alternate</span>
                    <span class="value">${info.alt}</span>
                </div>`;
            }
            if (info.email) {
                html += `<div class="result-item">
                    <span class="label"><i class="fas fa-envelope"></i> email</span>
                    <span class="value">${info.email}</span>
                </div>`;
            }

            resultContent.innerHTML = html;
            resultBox.classList.add('show');
            errorText.classList.remove('show');

            if (address && address !== 'N/A') {
                const lat = info.lat || null;
                const lng = info.lng || null;
                updateLocationMap(address, lat, lng, locationType);
            }

            let apiHtml = '';
            if (data.BUY_API) apiHtml += `<span><i class="fas fa-shopping-cart" style="color:#00ffff;"></i> buy: <strong style="color:#00ffff;">${data.BUY_API}</strong></span>`;
            if (data.SUPPORT) apiHtml += `<span><i class="fas fa-headset" style="color:#00ffff;"></i> support: <strong style="color:#00ffff;">${data.SUPPORT}</strong></span>`;
            if (apiHtml) {
                apiInfo.innerHTML = apiHtml;
                apiInfo.style.display = 'flex';
            }
        } else {
            resultBox.classList.remove('show');
            errorText.textContent = '❌ no data found';
            errorText.classList.add('show');
        }
    }

    async function searchNumber() {
        const input = document.getElementById('phoneInput');
        const number = input.value.trim();
        const statusText = document.getElementById('statusText');
        const statusDot = document.getElementById('statusDot');
        const trackBtn = document.getElementById('trackBtn');
        const errorText = document.getElementById('errorText');

        if (!number || number.length !== 10 || !/^[0-9]{10}$/.test(number)) {
            errorText.textContent = '⚠️ enter valid 10-digit number';
            errorText.classList.add('show');
            return;
        }

        errorText.classList.remove('show');
        trackBtn.disabled = true;
        trackBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> searching...';
        statusText.textContent = 'searching...';
        statusDot.className = 'dot';

        document.getElementById('resultBox').classList.remove('show');
        document.getElementById('apiInfo').style.display = 'none';
        document.getElementById('locationSection').classList.remove('show');
        document.getElementById('locationSection').classList.remove('live', 'area');

        try {
            const data = await callAPI(number);
            displayResults(number, data);

            if (data.status === 'success' && data.result && data.result.length > 0) {
                statusText.textContent = '✅ completed (' + data.result.length + ' records)';
                statusDot.className = 'dot';
            } else if (data.status === 'error') {
                statusText.textContent = '❌ api error';
                statusDot.className = 'dot err';
            } else {
                statusText.textContent = '❌ no data';
                statusDot.className = 'dot err';
            }
        } catch (error) {
            statusText.textContent = '❌ connection error';
            statusDot.className = 'dot err';
            errorText.textContent = '❌ network error. try again.';
            errorText.classList.add('show');
        }

        trackBtn.disabled = false;
        trackBtn.innerHTML = '<i class="fas fa-search"></i> execute search';
    }

    document.getElementById('trackForm').addEventListener('submit', function(e) {
        e.preventDefault();
        searchNumber();
    });

    document.getElementById('phoneInput').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') { e.preventDefault(); searchNumber(); }
    });

    document.getElementById('phoneInput').addEventListener('input', function(e) {
        this.value = this.value.replace(/[^0-9]/g, '');
    });

    document.addEventListener('contextmenu', function(e) { e.preventDefault(); return false; });
    document.addEventListener('keydown', function(e) {
        if (e.ctrlKey && ['c','v','s','p','u'].includes(e.key)) { e.preventDefault(); return false; }
        if (e.key === 'F12') { e.preventDefault(); return false; }
    });
    document.addEventListener('dragstart', function(e) { e.preventDefault(); return false; });

    document.addEventListener('DOMContentLoaded', function() {
        console.log('🔥 SAKIL BHAI SYSTEM READY');
        console.log('📱 Enter a 10-digit number and click search');
    });
    </script>
</body>
</html>
'''

# ===========================================================
# RESELLER DASHBOARD
# ===========================================================
RESELLER_DASHBOARD_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>👑 RESELLER · SAKIL BHAI</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;800;900&family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Inter', sans-serif; background: #06060a; min-height: 100vh; }
        .container { max-width: 1100px; margin: 0 auto; padding: 16px; }
        .header {
            background: rgba(6,6,12,0.95); border: 1px solid rgba(0,255,102,0.1);
            border-radius: 16px; padding: 16px 20px; margin-bottom: 16px;
            display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;
        }
        .header .brand { display: flex; align-items: center; gap: 12px; }
        .header .brand img { width: 40px; height: 40px; border-radius: 50%; border: 1px solid rgba(0,255,102,0.2); object-fit: cover; padding: 2px; background: rgba(0,0,0,0.3); }
        .header .brand h1 { font-family: 'Orbitron', monospace; font-size: 18px; font-weight: 700; color: #fff; }
        .header .brand h1 .hl { color: #00ff66; }
        .header .brand .sub { font-size: 7px; font-family: 'Orbitron', monospace; color: #88ddff; letter-spacing: 4px; }
        .header .actions { display: flex; gap: 8px; flex-wrap: wrap; }
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
            gap: 10px; margin-bottom: 16px;
        }
        .stat-card {
            background: rgba(6,6,12,0.92); border: 1px solid rgba(255,255,255,0.03);
            border-radius: 12px; padding: 12px 14px; text-align: center;
        }
        .stat-card .num { font-family: 'Orbitron', monospace; font-size: 22px; font-weight: 700; color: #fff; }
        .stat-card .num.green { color: #00ff66; }
        .stat-card .num.cyan { color: #00ffff; }
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
        .card .title i { color: #00ff66; font-size: 11px; }
        .table-wrap { overflow-x: auto; }
        table { width: 100%; border-collapse: collapse; font-size: 11px; }
        th { font-size: 7px; font-family: 'Orbitron', monospace; color: #88ddff; letter-spacing: 2px; text-transform: uppercase; padding: 6px 8px; border-bottom: 1px solid rgba(255,255,255,0.03); text-align: left; }
        td { color: #ccddff; padding: 6px 8px; border-bottom: 1px solid rgba(255,255,255,0.02); font-size: 10px; }
        .badge { font-size: 6px; font-family: 'Orbitron', monospace; padding: 1px 10px; border-radius: 30px; border: 1px solid rgba(255,255,255,0.03); color: #88ddff; }
        .badge.active { border-color: rgba(0,255,102,0.2); color: #00ff66; }
        .badge.inactive { border-color: rgba(255,51,85,0.2); color: #ff3355; }
        .actions-cell { display: flex; gap: 4px; flex-wrap: wrap; }
        .actions-cell a { font-size: 7px; font-family: 'Orbitron', monospace; color: #88ddff; text-decoration: none; padding: 1px 8px; border: 1px solid rgba(255,255,255,0.03); border-radius: 4px; transition: all 0.3s ease; }
        .actions-cell a:hover { border-color: rgba(0,255,102,0.2); color: #00ff66; }
        .actions-cell a.del:hover { border-color: rgba(255,51,85,0.2); color: #ff3355; }
        .add-form { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
        .add-form input, .add-form select {
            padding: 6px 12px; background: rgba(0,0,0,0.2);
            border: 1px solid rgba(0,255,102,0.05); border-radius: 8px;
            color: #fff; font-size: 12px; outline: none;
            font-family: 'Inter', sans-serif; flex: 1; min-width: 100px;
        }
        .add-form input:focus, .add-form select:focus { border-color: rgba(0,255,102,0.15); }
        .add-form input::placeholder { color: #88ddff; }
        .add-form select option { background: #0a0a1a; color: #fff; }
        .add-form .btn-add {
            padding: 6px 18px; background: rgba(0,255,102,0.03);
            border: 1px solid rgba(0,255,102,0.05); border-radius: 8px;
            color: #88ddff; font-family: 'Orbitron', monospace;
            font-size: 9px; letter-spacing: 2px; cursor: pointer;
            transition: all 0.3s ease;
        }
        .add-form .btn-add:hover { border-color: rgba(0,255,102,0.2); color: #00ff66; }
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
                    <h1><span class="hl">👑 RESELLER</span> PANEL</h1>
                    <div class="sub">manage your vip users</div>
                </div>
            </div>
            <div class="actions">
                <a href="{{ url_for('user_dashboard') }}"><i class="fas fa-arrow-left"></i> user panel</a>
                {% if session.get('role') == 'owner' %}
                <a href="{{ url_for('owner_dashboard') }}" style="color:#ffd700;border-color:rgba(255,215,0,0.2);"><i class="fas fa-crown"></i> owner</a>
                {% endif %}
                <a href="{{ url_for('logout') }}" class="logout"><i class="fas fa-sign-out-alt"></i> logout</a>
            </div>
        </div>

        {% with messages = get_flashed_messages(with_categories=true) %}
            {% for category, message in messages %}
                <div class="flash {{ category }}"><i class="fas fa-{% if category == 'success' %}check-circle{% else %}exclamation-circle{% endif %}"></i> {{ message }}</div>
            {% endfor %}
        {% endwith %}

        <div class="stats-grid">
            <div class="stat-card"><div class="num green">{{ stats.total }}</div><div class="label">total users</div></div>
            <div class="stat-card"><div class="num cyan">{{ stats.active }}</div><div class="label">active</div></div>
            <div class="stat-card"><div class="num red">{{ stats.inactive }}</div><div class="label">inactive</div></div>
            <div class="stat-card"><div class="num" style="color:#ffd700;">{{ reseller_data.get('device_limit', 15) }}</div><div class="label">device limit</div></div>
        </div>

        <!-- Add User -->
        <div class="card">
            <div class="title"><i class="fas fa-user-plus"></i> create vip user</div>
            <form method="POST" action="{{ url_for('reseller_add_user') }}" class="add-form">
                <input type="text" name="username" placeholder="username" required>
                <input type="password" name="password" placeholder="password" required>
                <input type="number" name="device_limit" placeholder="device limit" value="5" min="1" max="999999" style="width:120px;">
                <button type="submit" class="btn-add"><i class="fas fa-plus"></i> add</button>
            </form>
        </div>

        <!-- Users List -->
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
                {% else %}<div class="empty"><i class="fas fa-user-slash"></i> no users created yet</div>{% endif %}
            </div>
        </div>

        <div class="footer">⚡ SAKIL BHAI · ENTERPRISE ⚡</div>
    </div>
</body>
</html>
'''

# ===========================================================
# OWNER DASHBOARD
# ===========================================================
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
        .container { max-width: 1200px; margin: 0 auto; padding: 16px; }
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
        .badge.reseller { border-color: rgba(0,255,102,0.2); color: #00ff66; }
        .badge.user { border-color: rgba(255,255,255,0.05); color: #88ddff; }
        .actions-cell { display: flex; gap: 4px; flex-wrap: wrap; }
        .actions-cell a { font-size: 7px; font-family: 'Orbitron', monospace; color: #88ddff; text-decoration: none; padding: 1px 8px; border: 1px solid rgba(255,255,255,0.03); border-radius: 4px; transition: all 0.3s ease; }
        .actions-cell a:hover { border-color: rgba(255,215,0,0.2); color: #ffd700; }
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
                <a href="{{ url_for('user_dashboard') }}"><i class="fas fa-arrow-left"></i> user panel</a>
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
            <div class="stat-card"><div class="num green">{{ stats.active_users }}</div><div class="label">active users</div></div>
            <div class="stat-card"><div class="num cyan">{{ stats.online_users }}</div><div class="label">online</div></div>
            <div class="stat-card"><div class="num" style="color:#ffd700;">{{ stats.device_limit }}</div><div class="label">default limit</div></div>
        </div>

        <!-- Add Reseller -->
        <div class="card">
            <div class="title"><i class="fas fa-store"></i> add reseller</div>
            <form method="POST" action="{{ url_for('owner_add_reseller') }}" class="add-form">
                <input type="text" name="username" placeholder="reseller username" required>
                <input type="password" name="password" placeholder="password" required>
                <input type="number" name="device_limit" placeholder="device limit" value="15" min="1" max="999999" style="width:120px;">
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

        <!-- Resellers List -->
        <div class="card">
            <div class="title"><i class="fas fa-store"></i> resellers ({{ resellers|length }})</div>
            <div class="table-wrap">
                {% if resellers %}
                <table>
                    <thead><tr><th>username</th><th>device limit</th><th>status</th><th>actions</th></tr></thead>
                    <tbody>
                    {% for u, d in resellers.items() %}
                    <tr>
                        <td>{{ u }}</td>
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
                            <a href="{{ url_for('owner_delete_user', username=u) }}" class="del" onclick="return confirm('Delete {{ u }}?')"><i class="fas fa-trash"></i></a>
                        </td>
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

# ===========================================================
# FLASK ROUTES
# ===========================================================

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        # Check Owner
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
            else:
                return render_template_string(LOGIN_HTML, error="⚠️ Account suspended", remaining_minutes=0)

        # Check Reseller
        resellers = get_resellers()
        if username in resellers and verify_password(password, resellers[username].get("password", "")):
            if resellers[username].get("active", True):
                # Check device limit
                if not check_device_limit(username, "reseller"):
                    limit = get_device_limit(username, "reseller")
                    return render_template_string(LOGIN_HTML, error=f"⚠️ Device limit ({limit}) exceeded", remaining_minutes=0)
                session.permanent = True
                session["authenticated"] = True
                session["username"] = username
                session["role"] = "reseller"
                session["device_id"] = str(uuid.uuid4())
                register_device(username, "reseller", session["device_id"],
                              request.remote_addr, request.headers.get('User-Agent'))
                return redirect(url_for('reseller_dashboard'))
            else:
                return render_template_string(LOGIN_HTML, error="⚠️ Account suspended", remaining_minutes=0)

        # Check User
        users = get_users()
        if username in users and verify_password(password, users[username].get("password", "")):
            if users[username].get("active", True):
                if is_expired():
                    return redirect('https://wa.me/919242428894')
                if not check_device_limit(username, "user"):
                    limit = get_device_limit(username, "user")
                    return render_template_string(LOGIN_HTML, error=f"⚠️ Device limit ({limit}) exceeded", remaining_minutes=0)
                session.permanent = True
                session["authenticated"] = True
                session["username"] = username
                session["role"] = "user"
                session["device_id"] = str(uuid.uuid4())
                register_device(username, "user", session["device_id"],
                              request.remote_addr, request.headers.get('User-Agent'))
                return redirect(url_for('user_dashboard'))
            else:
                return render_template_string(LOGIN_HTML, error="⚠️ Account suspended", remaining_minutes=0)

        return render_template_string(LOGIN_HTML, error="❌ Invalid credentials", remaining_minutes=0)

    remaining_seconds = get_remaining_seconds()
    remaining_minutes = max(0, remaining_seconds // 60)
    return render_template_string(LOGIN_HTML, error="", remaining_minutes=remaining_minutes)

@app.route('/logout')
def logout():
    username = session.get("username")
    device_id = session.get("device_id")
    if username and device_id:
        logout_device(username, device_id)
    session.clear()
    return redirect(url_for('login_page'))

@app.route('/')
@user_required
@check_device_auth
def user_dashboard():
    remaining = get_remaining_seconds()
    return render_template_string(USER_PANEL_HTML,
                                 remaining_seconds=remaining,
                                 max_seconds=3600)

# ===========================================================
# OWNER ROUTES
# ===========================================================

@app.route('/owner/dashboard')
@owner_required
@check_device_auth
def owner_dashboard():
    resellers = get_resellers()
    users = get_users()
    devices = get_device_logs()

    total_users = len(users)
    total_resellers = len(resellers)
    active_users = sum(1 for u in users.values() if u.get("active", False))
    
    # Online users
    online_users = 0
    for key, entry in devices.items():
        if entry.get("active", False):
            expires = entry.get("expires_at")
            if expires:
                try:
                    exp_dt = datetime.datetime.fromisoformat(expires)
                    if exp_dt > datetime.datetime.utcnow():
                        if entry.get("role") == "user":
                            online_users += 1
                except:
                    pass

    owners = get_owners()
    owner = owners.get("sakil2026", {})
    default_limit = owner.get("settings", {}).get("default_device_limit", 5)

    stats = {
        "total_users": total_users,
        "total_resellers": total_resellers,
        "active_users": active_users,
        "online_users": online_users,
        "device_limit": default_limit
    }

    return render_template_string(OWNER_DASHBOARD_HTML,
                                 resellers=resellers,
                                 users=users,
                                 stats=stats)

@app.route('/owner/add-reseller', methods=['POST'])
@owner_required
def owner_add_reseller():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    device_limit = request.form.get('device_limit', 15)

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
        "created_by": session.get("username")
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
        "created_by": session.get("username")
    }
    fb_set("users", users)
    flash(f"User '{username}' created! Device limit: {device_limit}", "success")
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

    if role == "reseller":
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

    logout_all_devices(username)
    flash(f"Password reset for {username}! New password: {new_password}", "success")
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

# ===========================================================
# RESELLER ROUTES
# ===========================================================

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
    inactive = total - active

    stats = {
        "total": total,
        "active": active,
        "inactive": inactive
    }

    return render_template_string(RESELLER_DASHBOARD_HTML,
                                 reseller_data=reseller_data,
                                 users=my_users,
                                 stats=stats)

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

    # Check reseller's own device limit (can't give more than own limit)
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
        "created_by": session.get("username")
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

# ===========================================================
# API ROUTES (v8.0 FULL - 100% SAME)
# ===========================================================

@app.route('/api/lookup', methods=['POST'])
def lookup():
    try:
        data = request.get_json()
        number = data.get('number', '').strip()

        if not number:
            return jsonify({"status": "error", "message": "Phone number required"})

        clean_number = re.sub(r'[\+\s\-]', '', number)
        params = {'key': 'anish-exploits', 'type': 'number', 'num': clean_number}

        response = requests.get('https://exploitsindia.site/osint/api.php', params=params, timeout=30)
        response.raise_for_status()
        api_data = response.json()

        if api_data.get('status') == 'error':
            return jsonify(api_data)

        result = api_data.get('result', [])
        if result and len(result) > 0:
            info = result[0]
            address = info.get('address', info.get('location', ''))
            
            if 'lat' not in info and 'lng' not in info and address and address != 'N/A':
                try:
                    geocode_url = f"https://maps.googleapis.com/maps/api/geocode/json?address={urllib.parse.quote(address)}&key=AIzaSyBFw0Qbyq9zTFTd-tUY6dZWTgaQzuU17R8"
                    geo_response = requests.get(geocode_url, timeout=10)
                    geo_data = geo_response.json()
                    if geo_data['status'] == 'OK' and len(geo_data['results']) > 0:
                        loc = geo_data['results'][0]['geometry']['location']
                        info['lat'] = loc['lat']
                        info['lng'] = loc['lng']
                except:
                    pass

        return jsonify({
            "status": "success",
            "result": result
        })

    except requests.exceptions.Timeout:
        return jsonify({"status": "error", "message": "API timeout"})
    except requests.exceptions.RequestException as e:
        return jsonify({"status": "error", "message": f"API error: {str(e)}"})
    except Exception as e:
        return jsonify({"status": "error", "message": f"Server error: {str(e)}"})

@app.route('/api/expiry-status')
def api_expiry_status():
    remaining = get_remaining_seconds()
    settings = get_settings()
    return jsonify({
        "remaining_seconds": remaining,
        "expiry_utc": settings.get("expiry_utc", ""),
        "is_active": remaining > 0,
        "redirect_url": settings.get("redirect_url", "https://wa.me/919242428894")
    })

# ===========================================================
# MAIN
# ===========================================================

if __name__ == '__main__':
    import os
    import uuid
    port = int(os.environ.get('PORT', 5000))
    print("="*70)
    print("👑 SAKIL BHAI - ENTERPRISE VIP MANAGEMENT v9.0")
    print("🔥 Owner → Reseller → User Hierarchy")
    print("📍 Device Limit Control (Custom per user/reseller)")
    print("⚡ All v8.0 Features 100% Working")
    print("="*70)
    print(f"✅ Login:       http://0.0.0.0:{port}/login")
    print(f"✅ User Panel:  http://0.0.0.0:{port}/")
    print(f"✅ Reseller:    http://0.0.0.0:{port}/reseller/dashboard")
    print(f"✅ Owner:       http://0.0.0.0:{port}/owner/dashboard")
    print("="*70)
    print("🔑 Default Owner: sakil2026 / sakil2026")
    print("📁 Firebase: sakil-paid-hack-sell-1342007")
    print("="*70)

    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)    "apiKey": "AIzaSyC74129by4J9ghwX7kCq_xamWVuaBkZvac",
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
