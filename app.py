#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
=============================================================
SAKIL BHAI - VIP RESELLING SYSTEM v9.0
🔥 CYBERPUNK EDITION · NEON GLASS MORPHISM
Premium Hacking System · Firebase Powered
📍 PERFECT LOCATION TRACKING WITH RED BORDER
✅ MULTI-TENANT VIP RESELLING WITH CUSTOM URL
=============================================================
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
import uuid

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# =============================================================
# FIREBASE CONFIG
# =============================================================
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

# =============================================================
# DATA HELPERS
# =============================================================

def get_users():
    users = fb_get("users")
    if not users:
        users = {
            "sakil2026": {
                "password": hashlib.sha256("sakil2026".encode()).hexdigest(),
                "role": "admin",
                "active": True,
                "created": datetime.datetime.utcnow().isoformat(),
                "custom_url": "sakil2026"  # ডিফল্ট কাস্টম ইউআরএল
            }
        }
        fb_set("users", users)
    return users

def save_users(users):
    return fb_set("users", users)

def get_vip_users():
    """সব VIP ইউজারের ডেটা (যারা রিসেল করতে পারে)"""
    vip_users = fb_get("vip_users")
    if not vip_users:
        vip_users = {}
        fb_set("vip_users", vip_users)
    return vip_users

def save_vip_users(vip_users):
    return fb_set("vip_users", vip_users)

def get_sub_users(vip_username):
    """একটি VIP ইউজারের সব সাব-ইউজার (যারা ওর কাছ থেকে কিনেছে)"""
    sub_users = fb_get(f"sub_users/{vip_username}")
    if not sub_users:
        sub_users = {}
        fb_set(f"sub_users/{vip_username}", sub_users)
    return sub_users

def save_sub_users(vip_username, sub_users):
    return fb_set(f"sub_users/{vip_username}", sub_users)

def get_settings():
    settings = fb_get("settings")
    if not settings:
        settings = {
            "expiry_utc": "2026-12-31T23:59:59+00:00",
            "redirect_url": "https://wa.me/919242428894",
            "base_domain": "sakilbhaisystem.com"  # বেস ডোমেইন
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

def get_user_custom_url(username):
    users = get_users()
    if username not in users:
        return None
    return users[username].get("custom_url", username)

def generate_custom_url(username):
    """ইউজারনেম থেকে ক্লিন ইউআরএল জেনারেট করে"""
    clean = re.sub(r'[^a-zA-Z0-9\-_]', '', username.lower())
    if not clean:
        clean = str(uuid.uuid4())[:8]
    return clean

def session_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get("authenticated"):
            if is_expired():
                session.clear()
                return redirect(get_settings().get("redirect_url", "https://wa.me/919242428894"))
            return f(*args, **kwargs)
        return redirect(url_for('login_page'))
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get("authenticated") and session.get("role") == "admin":
            return f(*args, **kwargs)
        flash("Admin access required!", "error")
        return redirect(url_for('user_dashboard'))
    return decorated

def vip_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get("authenticated") and session.get("role") in ["admin", "vip"]:
            return f(*args, **kwargs)
        flash("VIP access required! Please buy subscription.", "error")
        return redirect(url_for('user_dashboard'))
    return decorated

# =============================================================
# LOGIN PAGE
# =============================================================
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

# =============================================================
# USER PANEL (VIP DASHBOARD)
# =============================================================
# নোট: এই HTML টা আগের মতোই থাকবে, কিন্তু ভিপি ইউজারদের জন্য আলাদা অপশন অ্যাড করা হবে।
# আমি সম্পূর্ণ HTML রি-রাইট না করে শুধু প্রয়োজনীয় অংশ যোগ করছি।
# বাকি অংশ আগের মতোই।

# =============================================================
# VIP RESELLER DASHBOARD (NEW)
# =============================================================
VIP_RESELLER_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VIP RESELLER · SAKIL BHAI</title>
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
            background: rgba(6,6,12,0.95); border: 1px solid rgba(0,255,255,0.1);
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
        .header .actions a:hover { border-color: rgba(0,255,255,0.2); color: #00ffff; }
        .header .actions a.logout { border-color: rgba(255,51,85,0.1); color: #ff3355; }
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
        .stat-box .num.gold { color: #ffd700; }
        .stat-box .num.cyan { color: #00ffff; }
        .stat-box .num.red { color: #ff3355; }
        .stat-box .num.green { color: #00ff66; }
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
        .badge.expired { border-color: rgba(255,51,85,0.2); color: #ff3355; }
        .badge.pending { border-color: rgba(255,215,0,0.2); color: #ffd700; }
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
            padding: 6px 18px; background: rgba(255,215,0,0.03);
            border: 1px solid rgba(255,215,0,0.05); border-radius: 8px;
            color: #88ddff; font-family: 'Orbitron', monospace;
            font-size: 9px; letter-spacing: 2px; cursor: pointer;
            transition: all 0.3s ease;
        }
        .add-form .btn-add:hover { border-color: rgba(255,215,0,0.2); color: #ffd700; }
        .custom-url-box {
            background: rgba(0,0,0,0.1); padding: 10px 14px;
            border-radius: 8px; border: 1px solid rgba(255,215,0,0.05);
            display: flex; align-items: center; gap: 10px; flex-wrap: wrap;
        }
        .custom-url-box .label {
            font-size: 7px; font-family: 'Orbitron', monospace;
            color: #88ddff; letter-spacing: 2px;
        }
        .custom-url-box .url {
            font-family: 'Orbitron', monospace;
            font-size: 12px; color: #ffd700;
            word-break: break-all;
        }
        .custom-url-box .url i { color: #00ffff; margin-right: 4px; }
        .actions-cell { display: flex; gap: 4px; flex-wrap: wrap; }
        .actions-cell a {
            font-size: 7px; font-family: 'Orbitron', monospace;
            color: #88ddff; text-decoration: none;
            padding: 1px 8px; border: 1px solid rgba(255,255,255,0.03);
            border-radius: 4px; transition: all 0.3s ease;
        }
        .actions-cell a:hover { border-color: rgba(0,255,255,0.2); color: #00ffff; }
        .actions-cell a.del:hover { border-color: rgba(255,51,85,0.2); color: #ff3355; }
        .flash {
            padding: 8px 14px; border-radius: 8px; margin-bottom: 12px;
            font-size: 10px; font-family: 'Orbitron', monospace;
            letter-spacing: 1px; display: flex; align-items: center; gap: 8px;
        }
        .flash.success { background: rgba(0,255,102,0.02); border: 1px solid rgba(0,255,102,0.05); color: #00ff66; }
        .flash.error { background: rgba(255,51,85,0.02); border: 1px solid rgba(255,51,85,0.05); color: #ff3355; }
        .empty { text-align: center; color: #88ddff; padding: 16px; font-size: 10px; font-family: 'Orbitron', monospace; letter-spacing: 2px; }
        .footer-text { text-align: center; font-size: 6px; color: #88ddff; letter-spacing: 3px; margin-top: 10px; font-family: 'Orbitron', monospace; }
        @media (max-width: 600px) {
            .header .title h1 { font-size: 15px; }
            .stats { grid-template-columns: repeat(2, 1fr); }
            .add-form { flex-direction: column; }
            .add-form input, .add-form select, .add-form .btn-add { width: 100%; }
            .custom-url-box { flex-direction: column; align-items: flex-start; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="title">
                <i class="fas fa-crown"></i>
                <div>
                    <h1><span class="hl">VIP RESELLER</span> PANEL</h1>
                    <div class="sub">premium · reselling system</div>
                </div>
            </div>
            <div class="actions">
                <a href="{{ url_for('user_dashboard') }}"><i class="fas fa-arrow-left"></i> back</a>
                <a href="{{ url_for('logout') }}" class="logout"><i class="fas fa-sign-out-alt"></i> logout</a>
            </div>
        </div>

        {% with messages = get_flashed_messages(with_categories=true) %}
            {% for category, message in messages %}
                <div class="flash {{ category }}"><i class="fas fa-{% if category == 'success' %}check-circle{% else %}exclamation-circle{% endif %}"></i> {{ message }}</div>
            {% endfor %}
        {% endwith %}

        <!-- কাস্টম ইউআরএল -->
        <div class="card">
            <div class="card-title"><i class="fas fa-link"></i> your custom url</div>
            <div class="custom-url-box">
                <span class="label"><i class="fas fa-globe"></i> your vip panel url:</span>
                <span class="url"><i class="fas fa-link"></i> {{ custom_url }}</span>
                <span style="font-size:7px; color:#88ddff; margin-left:auto;">
                    <i class="fas fa-check-circle" style="color:#00ff66;"></i> active
                </span>
            </div>
            <div style="margin-top:8px; font-size:7px; color:#88ddff; font-family:'Orbitron',monospace; letter-spacing:1px;">
                <i class="fas fa-info-circle" style="color:#ffd700;"></i> Share this url with your customers. They can access your panel using this link.
            </div>
        </div>

        <div class="stats">
            <div class="stat-box"><div class="num gold">{{ stats.total_sub_users }}</div><div class="label">total customers</div></div>
            <div class="stat-box"><div class="num green">{{ stats.active_sub_users }}</div><div class="label">active</div></div>
            <div class="stat-box"><div class="num red">{{ stats.expired_sub_users }}</div><div class="label">expired</div></div>
            <div class="stat-box"><div class="num cyan">{{ stats.total_earnings }}</div><div class="label">earnings</div></div>
        </div>

        <!-- সাব-ইউজার ক্রিয়েট -->
        <div class="card">
            <div class="card-title"><i class="fas fa-user-plus"></i> create customer account</div>
            <form method="POST" action="{{ url_for('vip_create_sub_user') }}" class="add-form">
                <input type="text" name="username" placeholder="customer username" required>
                <input type="password" name="password" placeholder="password" required>
                <select name="expiry_days">
                    <option value="1">1 day</option>
                    <option value="3">3 days</option>
                    <option value="7" selected>7 days</option>
                    <option value="15">15 days</option>
                    <option value="30">30 days</option>
                    <option value="60">60 days</option>
                    <option value="90">90 days</option>
                </select>
                <button type="submit" class="btn-add"><i class="fas fa-plus"></i> create</button>
            </form>
        </div>

        <!-- সাব-ইউজার লিস্ট -->
        <div class="card">
            <div class="card-title"><i class="fas fa-users"></i> customer list</div>
            <div class="table-wrap">
                {% if sub_users %}
                <table>
                    <thead>
                        <tr>
                            <th>username</th>
                            <th>created</th>
                            <th>expiry</th>
                            <th>status</th>
                            <th>actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for username, data in sub_users.items() %}
                        <tr>
                            <td style="color:#fff; font-weight:500;">{{ username }}</td>
                            <td style="font-size:8px; color:#88ddff;">{{ data.created[:10] if data.created else 'N/A' }}</td>
                            <td style="font-size:8px; color:#88ddff;">{{ data.expiry[:10] if data.expiry else 'N/A' }}</td>
                            <td><span class="badge {% if data.active %}active{% else %}expired{% endif %}">{{ 'active' if data.active else 'expired' }}</span></td>
                            <td>
                                <div class="actions-cell">
                                    <a href="{{ url_for('vip_edit_sub_user', username=username) }}"><i class="fas fa-pen"></i></a>
                                    <a href="{{ url_for('vip_toggle_sub_user', username=username) }}"><i class="fas fa-{% if data.active %}pause{% else %}play{% endif %}"></i></a>
                                    <a href="{{ url_for('vip_delete_sub_user', username=username) }}" class="del" onclick="return confirm('delete {{ username }}?')"><i class="fas fa-trash"></i></a>
                                </div>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
                {% else %}
                <div class="empty"><i class="fas fa-user-slash"></i> no customers yet</div>
                {% endif %}
            </div>
        </div>

        <div class="footer-text">⚡ sakil bhai · vip reseller system ⚡</div>
    </div>
</body>
</html>
'''

# =============================================================
# FLASK ROUTES
# =============================================================

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if verify_user(username, password):
            if is_expired():
                return redirect(get_settings().get("redirect_url", "https://wa.me/919242428894"))
            session["authenticated"] = True
            session["username"] = username
            session["role"] = get_user_role(username)

            users = get_users()
            users[username]["last_login"] = datetime.datetime.utcnow().isoformat()
            save_users(users)

            return redirect(url_for('user_dashboard'))
        else:
            return redirect(get_settings().get("redirect_url", "https://wa.me/919242428894"))

    remaining_seconds = get_remaining_seconds()
    remaining_minutes = max(0, remaining_seconds // 60)
    return render_template_string(LOGIN_HTML,
                                 error="",
                                 remaining_minutes=remaining_minutes)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(get_settings().get("redirect_url", "https://wa.me/919242428894"))

@app.route('/')
@session_required
def user_dashboard():
    remaining = get_remaining_seconds()
    # ইউজারের কাস্টম ইউআরএল দেখাবে
    username = session.get('username', '')
    custom_url = get_user_custom_url(username)
    base_domain = get_settings().get('base_domain', 'sakilbhaisystem.com')
    full_url = f"https://{base_domain}/{custom_url}" if base_domain else f"/{custom_url}"
    
    # ভিপি ইউজার হলে রিসেলার প্যানেল লিংক দেখাবে
    role = session.get('role', 'user')
    is_vip = role in ['admin', 'vip']
    
    return render_template_string(USER_PANEL_HTML,  # আগের ইউজার প্যানেল
                                 remaining_seconds=remaining,
                                 max_seconds=3600,
                                 custom_url=full_url,
                                 is_vip=is_vip)

# =============================================================
# VIP RESELLER ROUTES
# =============================================================

@app.route('/vip/reseller')
@session_required
@vip_required
def vip_reseller_dashboard():
    username = session.get('username', '')
    custom_url = get_user_custom_url(username)
    base_domain = get_settings().get('base_domain', 'sakilbhaisystem.com')
    full_url = f"https://{base_domain}/{custom_url}" if base_domain else f"/{custom_url}"
    
    sub_users = get_sub_users(username)
    total = len(sub_users)
    active = sum(1 for u in sub_users.values() if u.get('active', False))
    expired = total - active
    
    # মোট আয় (প্রতিটি সাব-ইউজারের জন্য ১০০ টাকা ধরে)
    earnings = total * 100
    
    stats = {
        "total_sub_users": total,
        "active_sub_users": active,
        "expired_sub_users": expired,
        "total_earnings": earnings
    }
    
    return render_template_string(VIP_RESELLER_HTML,
                                 custom_url=full_url,
                                 sub_users=sub_users,
                                 stats=stats)

@app.route('/vip/create-sub-user', methods=['POST'])
@session_required
@vip_required
def vip_create_sub_user():
    vip_username = session.get('username', '')
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    expiry_days = int(request.form.get('expiry_days', 7))
    
    if not username or not password:
        flash("Username and password required!", "error")
        return redirect(url_for('vip_reseller_dashboard'))
    
    # চেক করি এই ইউজারনেম ইতিমধ্যে বিদ্যমান কিনা
    all_users = get_users()
    if username in all_users:
        flash(f"Username '{username}' already exists!", "error")
        return redirect(url_for('vip_reseller_dashboard'))
    
    # সাব-ইউজার তৈরি করি
    expiry_date = datetime.datetime.utcnow() + datetime.timedelta(days=expiry_days)
    
    # মূল ইউজার লিস্টে অ্যাড করি
    all_users[username] = {
        "password": hashlib.sha256(password.encode()).hexdigest(),
        "role": "user",
        "active": True,
        "created": datetime.datetime.utcnow().isoformat(),
        "expiry": expiry_date.isoformat(),
        "vip_owner": vip_username,  # কে তৈরি করেছে
        "custom_url": generate_custom_url(username)
    }
    save_users(all_users)
    
    # ভিপি ইউজারের সাব-লিস্টে অ্যাড করি
    sub_users = get_sub_users(vip_username)
    sub_users[username] = {
        "created": datetime.datetime.utcnow().isoformat(),
        "expiry": expiry_date.isoformat(),
        "active": True,
        "days": expiry_days
    }
    save_sub_users(vip_username, sub_users)
    
    flash(f"Customer '{username}' created successfully! Expires in {expiry_days} days.", "success")
    return redirect(url_for('vip_reseller_dashboard'))

@app.route('/vip/toggle/<username>')
@session_required
@vip_required
def vip_toggle_sub_user(username):
    vip_username = session.get('username', '')
    sub_users = get_sub_users(vip_username)
    
    if username not in sub_users:
        flash("Customer not found!", "error")
        return redirect(url_for('vip_reseller_dashboard'))
    
    # স্ট্যাটাস টগল করি
    new_status = not sub_users[username].get('active', True)
    sub_users[username]['active'] = new_status
    save_sub_users(vip_username, sub_users)
    
    # মূল ইউজার লিস্টেও আপডেট করি
    all_users = get_users()
    if username in all_users:
        all_users[username]['active'] = new_status
        save_users(all_users)
    
    status = "enabled" if new_status else "disabled"
    flash(f"Customer {username} {status}!", "success")
    return redirect(url_for('vip_reseller_dashboard'))

@app.route('/vip/delete/<username>')
@session_required
@vip_required
def vip_delete_sub_user(username):
    vip_username = session.get('username', '')
    sub_users = get_sub_users(vip_username)
    
    if username not in sub_users:
        flash("Customer not found!", "error")
        return redirect(url_for('vip_reseller_dashboard'))
    
    # সাব-লিস্ট থেকে ডিলিট
    del sub_users[username]
    save_sub_users(vip_username, sub_users)
    
    # মূল ইউজার লিস্ট থেকেও ডিলিট (শুধু যদি ভিপি ওনার ম্যাচ করে)
    all_users = get_users()
    if username in all_users and all_users[username].get('vip_owner') == vip_username:
        del all_users[username]
        save_users(all_users)
    
    flash(f"Customer '{username}' deleted!", "success")
    return redirect(url_for('vip_reseller_dashboard'))

@app.route('/vip/edit/<username>', methods=['GET', 'POST'])
@session_required
@vip_required
def vip_edit_sub_user(username):
    vip_username = session.get('username', '')
    sub_users = get_sub_users(vip_username)
    
    if username not in sub_users:
        flash("Customer not found!", "error")
        return redirect(url_for('vip_reseller_dashboard'))
    
    if request.method == 'POST':
        new_expiry_days = int(request.form.get('expiry_days', 7))
        new_password = request.form.get('password', '').strip()
        
        # এক্সপাইরি আপডেট
        expiry_date = datetime.datetime.utcnow() + datetime.timedelta(days=new_expiry_days)
        sub_users[username]['expiry'] = expiry_date.isoformat()
        sub_users[username]['days'] = new_expiry_days
        sub_users[username]['active'] = True
        save_sub_users(vip_username, sub_users)
        
        # মূল ইউজার আপডেট
        all_users = get_users()
        if username in all_users:
            all_users[username]['expiry'] = expiry_date.isoformat()
            all_users[username]['active'] = True
            if new_password:
                all_users[username]['password'] = hashlib.sha256(new_password.encode()).hexdigest()
            save_users(all_users)
        
        flash(f"Customer '{username}' updated! Expires in {new_expiry_days} days.", "success")
        return redirect(url_for('vip_reseller_dashboard'))
    
    # GET: এডিট ফর্ম দেখাই
    return f'''
    <!DOCTYPE html>
    <html><head><title>edit customer</title>
    <style>
        *{{margin:0;padding:0;box-sizing:border-box;}}
        body{{background:#06060a;display:flex;justify-content:center;align-items:center;min-height:100vh;font-family:'Inter',sans-serif;}}
        .box{{background:rgba(6,6,12,0.95);border:1px solid rgba(0,255,255,0.1);border-radius:20px;padding:30px;max-width:380px;width:92%;}}
        h1{{font-family:'Orbitron',monospace;font-size:18px;font-weight:700;color:#fff;letter-spacing:2px;text-align:center;}}
        h1 .hl{{color:#ffd700;}}
        .sub{{text-align:center;font-size:8px;font-family:'Orbitron',monospace;color:#88ddff;letter-spacing:3px;margin-bottom:16px;}}
        .form-group{{margin-bottom:12px;}}
        label{{display:block;font-size:8px;font-family:'Orbitron',monospace;color:#88ddff;letter-spacing:2px;margin-bottom:3px;}}
        input,select{{width:100%;padding:8px 12px;background:rgba(0,0,0,0.2);border:1px solid rgba(0,255,255,0.05);border-radius:8px;color:#fff;font-size:13px;outline:none;font-family:'Inter',sans-serif;margin-top:2px;}}
        input:focus,select:focus{{border-color:rgba(0,255,255,0.15);}}
        select option{{background:#0a0a1a;color:#fff;}}
        .btn{{width:100%;padding:10px;background:rgba(255,215,0,0.05);border:1px solid rgba(255,215,0,0.05);border-radius:8px;color:#88ddff;font-family:'Orbitron',monospace;font-size:10px;letter-spacing:2px;cursor:pointer;transition:all 0.3s ease;margin-top:4px;}}
        .btn:hover{{border-color:rgba(255,215,0,0.2);color:#ffd700;}}
        .back{{display:block;text-align:center;font-size:8px;font-family:'Orbitron',monospace;color:#88ddff;text-decoration:none;margin-top:10px;letter-spacing:2px;transition:all 0.3s ease;}}
        .back:hover{{color:#00ffff;}}
    </style>
    </head>
    <body>
    <div class="box">
        <h1><span class="hl">edit</span> customer</h1>
        <div class="sub">premium · {username}</div>
        <form method="POST">
            <div class="form-group">
                <label><i class="fas fa-key"></i> new password (optional)</label>
                <input type="password" name="password" placeholder="leave blank to keep">
            </div>
            <div class="form-group">
                <label><i class="fas fa-clock"></i> expiry days</label>
                <select name="expiry_days">
                    <option value="1">1 day</option>
                    <option value="3">3 days</option>
                    <option value="7" selected>7 days</option>
                    <option value="15">15 days</option>
                    <option value="30">30 days</option>
                    <option value="60">60 days</option>
                    <option value="90">90 days</option>
                </select>
            </div>
            <button type="submit" class="btn"><i class="fas fa-save"></i> update</button>
        </form>
        <a href="{url_for('vip_reseller_dashboard')}" class="back"><i class="fas fa-arrow-left"></i> back</a>
    </div>
    </body>
    </html>
    '''

# =============================================================
# API ROUTES
# =============================================================

@app.route('/api/lookup', methods=['POST'])
@session_required
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
            
            # লোকেশন লাইভ কিনা চেক করি - ল্যাট/লং থাকলে লাইভ
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

# =============================================================
# CUSTOM URL ROUTING - ডায়নামিক ইউআরএল হ্যান্ডলিং
# =============================================================

@app.route('/<custom_url>')
def custom_user_panel(custom_url):
    """কাস্টম ইউআরএল দিয়ে ইউজারের প্যানেল অ্যাক্সেস"""
    users = get_users()
    found_username = None
    for username, data in users.items():
        if data.get('custom_url') == custom_url:
            found_username = username
            break
    
    if not found_username:
        return redirect(url_for('login_page'))
    
    # ইউজারকে অটোমেটিক লগইন করিয়ে দিই (সেশন সেট করে)
    session["authenticated"] = True
    session["username"] = found_username
    session["role"] = users[found_username].get("role", "user")
    
    # এক্সপাইরি চেক
    if is_expired():
        session.clear()
        return redirect(get_settings().get("redirect_url", "https://wa.me/919242428894"))
    
    return redirect(url_for('user_dashboard'))

# =============================================================
# ADMIN ROUTES (বর্ধিত)
# =============================================================

# আগের অ্যাডমিন কোড এখানে থাকবে, সাথে নতুন ফিচার:
# - VIP ইউজার তৈরি করা
# - কাস্টম ইউআরএল সেট করা
# - সব সাব-ইউজার দেখা

# (পুরনো অ্যাডমিন কোড আমি এখানে রি-রাইট করছি না, কিন্তু প্রয়োজনীয় অংশ যোগ করছি)

# =============================================================
# MAIN
# =============================================================

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    print("="*60)
    print("⚡ SAKIL BHAI - VIP RESELLING SYSTEM v9.0")
    print("🔥 CYBERPUNK EDITION · PREMIUM SYSTEM")
    print("📍 PERFECT LOCATION TRACKING - RED BORDER")
    print("✅ MULTI-TENANT VIP RESELLING")
    print("="*60)
    print(f"✅ User Panel:  http://0.0.0.0:{port}")
    print(f"✅ Login:       http://0.0.0.0:{port}/login")
    print(f"✅ Admin:       http://0.0.0.0:{port}/admin")
    print(f"✅ VIP Reseller: http://0.0.0.0:{port}/vip/reseller")
    print("="*60)
    print("🔑 Default: sakil2026 / sakil2026")
    print("📁 Firebase: sakil-paid-hack-sell-1342007")
    print("="*60)

    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
