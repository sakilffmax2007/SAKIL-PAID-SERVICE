#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
============================================
SAKIL BHAI - USER PANEL v8.0 VIP PREMIUM
🔥 CYBERPUNK EDITION · NEON GLASS MORPHISM
Premium Hacking System · Firebase Powered
📍 PERFECT LOCATION TRACKING WITH BORDER
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

def get_users():
    users = fb_get("users")
    if not users:
        users = {
            "sakil2026": {
                "password": hashlib.sha256("sakil2026".encode()).hexdigest(),
                "role": "admin",
                "active": True,
                "created": datetime.datetime.utcnow().isoformat()
            }
        }
        fb_set("users", users)
    return users

def save_users(users):
    return fb_set("users", users)

def get_settings():
    settings = fb_get("settings")
    if not settings:
        settings = {
            "expiry_utc": "2026-12-31T23:59:59+00:00",
            "redirect_url": "https://wa.me/919242428894"
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

def session_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get("authenticated"):
            if is_expired():
                session.clear()
                return redirect('https://wa.me/919242428894')
            return f(*args, **kwargs)
        return redirect(url_for('login_page'))
    return decorated

# ============================================
# LOGIN PAGE
# ============================================
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

# ============================================
# USER DASHBOARD - PERFECT LOCATION WITH BORDER
# ============================================
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
                    {% if session.get('role') == 'admin' %}
                    <a href="{{ url_for('admin_dashboard') }}" class="admin"><i class="fas fa-crown"></i> admin panel</a>
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
    // 📍 LOCATION FUNCTIONS - FULL AREA VIEW (RED BORDER)
    // ============================================

    function parseAreaName(address) {
        if (!address || address === 'N/A' || address === 'Unknown' || address === '') {
            return null;
        }
        
        // Clean messy format: "!!.INARAYANPUR North 24 Parganas!!NORTH 24 PARGANAS!!North 24 Parganas!!West Bengal!!743234"
        let cleaned = address.replace(/!!\.?/g, '').replace(/!!/g, '!');
        let parts = cleaned.split('!').filter(p => p.trim().length > 0);
        
        if (parts.length > 0) {
            let area = parts[0].trim();
            if (parts.length > 1) {
                let second = parts[1].trim();
                if (/[A-Za-z]/.test(second) && second.length > 3) {
                    if (!area.includes(second) && !second.includes(area)) {
                        area = area + ', ' + second;
                    }
                }
            }
            return area;
        }
        
        return address.substring(0, 35);
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

        // লোকেশন টাইপ সেট করি
        if (type === 'live' && lat && lng) {
            locationType.textContent = '🔴 LIVE';
            badge.className = 'location-badge live';
            section.className = 'location-section show live';
        } else {
            locationType.textContent = '📍 AREA';
            badge.className = 'location-badge area';
            section.className = 'location-section show area';
        }

        // পুরো এলাকা দেখানোর জন্য এলাকার নাম পার্স করি
        let areaName = parseAreaName(address);
        if (!areaName) {
            areaName = address.substring(0, 35);
        }

        // 🔥 ক্রিটিক্যাল চেঞ্জ: place এর বদলে search ব্যবহার করি, zoom 13 (পুরো এলাকা দেখাবে)
        let query = areaName;
        if (lat && lng) {
            query = `${lat},${lng}`;
        }

        const cleanQuery = encodeURIComponent(query);
        
        // embed/v1/search ব্যবহার করি - এটা পুরো এলাকা দেখায়, শুধু পিন পয়েন্ট না
        const mapUrl = `https://www.google.com/maps/embed/v1/search?key=AIzaSyBFw0Qbyq9zTFTd-tUY6dZWTgaQzuU17R8&q=${cleanQuery}&zoom=13&maptype=roadmap`;

        iframe.src = mapUrl;
        label.textContent = areaName.substring(0, 60) + (areaName.length > 60 ? '...' : '');
        openLink.href = `https://www.google.com/maps/search/?api=1&query=${cleanQuery}`;
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
            
            // ===== লোকেশন - লাইভ নাকি এরিয়া (উভয় ক্ষেত্রেই রেড বর্ডার) =====
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

            // 📍 লোকেশন ম্যাপ আপডেট করো - রেড বর্ডার সহ
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

# ============================================
# ADMIN DASHBOARD
# ============================================
ADMIN_DASHBOARD_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SAKIL BHAI · ADMIN</title>
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
        .header .title i { font-size: 24px; color: #00ffff; opacity: 0.5; }
        .header .title h1 {
            font-family: 'Orbitron', monospace; font-size: 18px; font-weight: 700;
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
        .badge.admin { border-color: rgba(0,255,102,0.2); color: #00ff66; }
        .badge.user { border-color: rgba(0,255,255,0.1); color: #88ddff; }
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
            padding: 6px 18px; background: rgba(0,255,102,0.03);
            border: 1px solid rgba(0,255,102,0.05); border-radius: 8px;
            color: #88ddff; font-family: 'Orbitron', monospace;
            font-size: 9px; letter-spacing: 2px; cursor: pointer;
            transition: all 0.3s ease;
        }
        .add-form .btn-add:hover { border-color: rgba(0,255,102,0.2); color: #00ff66; }
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
        .expiry-form input[type="datetime-local"]:focus {
            border-color: rgba(0,255,255,0.3);
        }
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
        @media (max-width: 600px) {
            .header .title h1 { font-size: 15px; }
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
                    <h1><span class="hl">ADMIN</span> DASHBOARD</h1>
                    <div class="sub">premium · system control</div>
                </div>
            </div>
            <div class="actions">
                <a href="{{ url_for('user_dashboard') }}"><i class="fas fa-arrow-left"></i> back</a>
                <a href="{{ url_for('admin_logout') }}" class="logout"><i class="fas fa-sign-out-alt"></i> logout</a>
            </div>
        </div>

        {% with messages = get_flashed_messages(with_categories=true) %}
            {% for category, message in messages %}
                <div class="flash {{ category }}"><i class="fas fa-{% if category == 'success' %}check-circle{% else %}exclamation-circle{% endif %}"></i> {{ message }}</div>
            {% endfor %}
        {% endwith %}

        <div class="stats">
            <div class="stat-box"><div class="num green">{{ stats.total_users }}</div><div class="label">users</div></div>
            <div class="stat-box"><div class="num cyan">{{ stats.active_users }}</div><div class="label">active</div></div>
            <div class="stat-box"><div class="num red">{{ stats.inactive_users }}</div><div class="label">inactive</div></div>
            <div class="stat-box"><div class="num" style="color:#FF9933;">{{ stats.expiry_status }}</div><div class="label">expiry</div></div>
        </div>

        <!-- Expiry Management -->
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

        <div class="card">
            <div class="card-title"><i class="fas fa-user-plus"></i> add vip user</div>
            <form method="POST" action="{{ url_for('admin_add_user') }}" class="add-form">
                <input type="text" name="username" placeholder="username" required>
                <input type="password" name="password" placeholder="password" required>
                <select name="role">
                    <option value="user">user</option>
                    <option value="admin">admin</option>
                </select>
                <button type="submit" class="btn-add"><i class="fas fa-plus"></i> add</button>
            </form>
        </div>

        <div class="card">
            <div class="card-title"><i class="fas fa-users"></i> vip user list</div>
            <div class="table-wrap">
                {% if users %}
                <table>
                    <thead>
                        <tr>
                            <th>username</th>
                            <th>role</th>
                            <th>status</th>
                            <th>created</th>
                            <th>actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for username, data in users.items() %}
                        <tr>
                            <td style="color:{% if username == 'sakil2026' %}#00ffff{% else %}#fff{% endif %}; font-weight:500;">
                                {{ username }}
                                {% if username == 'sakil2026' %}<span style="color:#ffd700; font-size:7px;">⭐</span>{% endif %}
                            </td>
                            <td><span class="badge {{ data.role }}">{{ data.role }}</span></td>
                            <td><span class="badge {% if data.active %}active{% else %}inactive{% endif %}">{{ 'active' if data.active else 'inactive' }}</span></td>
                            <td style="font-size:8px; color:#88ddff;">{{ data.created[:10] if data.created else 'N/A' }}</td>
                            <td>
                                <div class="actions-cell">
                                    <a href="{{ url_for('admin_edit_user', username=username) }}"><i class="fas fa-pen"></i></a>
                                    <a href="{{ url_for('admin_toggle_user', username=username) }}"><i class="fas fa-{% if data.active %}pause{% else %}play{% endif %}"></i></a>
                                    {% if username != 'sakil2026' %}
                                    <a href="{{ url_for('admin_delete_user', username=username) }}" class="del" onclick="return confirm('delete {{ username }}?')"><i class="fas fa-trash"></i></a>
                                    {% endif %}
                                </div>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
                {% else %}
                <div class="empty"><i class="fas fa-user-slash"></i> no vip users</div>
                {% endif %}
            </div>
        </div>

        <div class="footer-text">⚡ sakil bhai · premium admin system ⚡</div>
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
# ADMIN LOGIN PAGE
# ============================================
ADMIN_LOGIN_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SAKIL BHAI · ADMIN</title>
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
        }
        .box {
            background: rgba(6,6,12,0.95);
            border: 1px solid rgba(0,255,255,0.1);
            border-radius: 20px;
            padding: 36px 32px;
            max-width: 360px;
            width: 92%;
            backdrop-filter: blur(20px);
            animation: fadeIn 0.6s ease;
        }
        @keyframes fadeIn { 0%{opacity:0;transform:translateY(20px)}100%{opacity:1;transform:translateY(0)} }
        .box .icon { text-align: center; font-size: 30px; color: #00ffff; opacity: 0.5; margin-bottom: 4px; }
        .box h1 { font-family: 'Orbitron', monospace; font-size: 18px; font-weight: 700; color: #fff; text-align: center; letter-spacing: 2px; }
        .box h1 .hl { color: #00ffff; }
        .box .sub { text-align: center; font-size: 8px; font-family: 'Orbitron', monospace; color: #88ddff; letter-spacing: 4px; margin-bottom: 20px; text-transform: uppercase; }
        .form-group { margin-bottom: 12px; }
        .form-group label { display: block; font-size: 8px; font-family: 'Orbitron', monospace; color: #88ddff; letter-spacing: 2px; margin-bottom: 3px; }
        .form-group label i { color: #00ffff; }
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
        .input-wrap input::placeholder { color: #88ddff; font-size: 12px; }
        .btn {
            width: 100%; padding: 10px;
            background: rgba(0,255,255,0.05);
            border: 1px solid rgba(0,255,255,0.05);
            border-radius: 10px;
            color: #88ddff;
            font-family: 'Orbitron', monospace;
            font-size: 11px; letter-spacing: 3px;
            cursor: pointer; transition: all 0.3s ease;
            text-transform: uppercase; display: flex;
            justify-content: center; align-items: center; gap: 8px;
        }
        .btn:hover { border-color: rgba(0,255,255,0.2); color: #00ffff; }
        .error { color: #ff3355; font-size: 10px; font-family: 'Orbitron', monospace; text-align: center; padding: 4px 0; display: none; letter-spacing: 1px; }
        .error.show { display: block; animation: shake 0.4s ease; }
        @keyframes shake { 0%,100%{transform:translateX(0)}25%{transform:translateX(-4px)}75%{transform:translateX(4px)} }
        .footer { text-align: center; font-size: 6px; color: #88ddff; letter-spacing: 3px; margin-top: 12px; font-family: 'Orbitron', monospace; }
        @media (max-width: 480px) {
            .box { padding: 28px 20px; }
            .box h1 { font-size: 15px; }
        }
    </style>
</head>
<body>
    <div class="box">
        <div class="icon"><i class="fas fa-crown"></i></div>
        <h1><span class="hl">admin</span> panel</h1>
        <div class="sub">premium · system control</div>
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
            <div class="error" id="adminError">{{ error }}</div>
            <button type="submit" class="btn"><i class="fas fa-unlock-alt"></i> unlock</button>
        </form>
        <div class="footer">⚡ sakil bhai · premium admin ⚡</div>
    </div>
    <script>
        document.querySelector('input[name="username"]').focus();
        document.querySelectorAll('input').forEach(el => {
            el.addEventListener('input', function() {
                document.getElementById('adminError').classList.remove('show');
            });
        });
        {% if error %}
        document.getElementById('adminError').classList.add('show');
        {% endif %}
    </script>
</body>
</html>
'''

# ============================================
# FLASK ROUTES
# ============================================

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if verify_user(username, password):
            if is_expired():
                return redirect('https://wa.me/919242428894')
            session["authenticated"] = True
            session["username"] = username
            session["role"] = get_user_role(username)

            users = get_users()
            users[username]["last_login"] = datetime.datetime.utcnow().isoformat()
            save_users(users)

            return redirect(url_for('user_dashboard'))
        else:
            return redirect('https://wa.me/919242428894')

    remaining_seconds = get_remaining_seconds()
    remaining_minutes = max(0, remaining_seconds // 60)
    return render_template_string(LOGIN_HTML,
                                 error="",
                                 remaining_minutes=remaining_minutes)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('https://wa.me/919242428894')

@app.route('/')
@session_required
def user_dashboard():
    remaining = get_remaining_seconds()
    return render_template_string(USER_PANEL_HTML,
                                 remaining_seconds=remaining,
                                 max_seconds=3600)

# ============================================
# ADMIN ROUTES
# ============================================

@app.route('/admin', methods=['GET', 'POST'])
@app.route('/ad', methods=['GET', 'POST'])
def admin_login():
    if session.get("admin_auth"):
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        settings = get_settings()
        admin_user = settings.get("admin_username", "sakil2026")
        admin_pass_hash = settings.get("admin_password", hashlib.sha256("sakil2026".encode()).hexdigest())

        if username == admin_user and hashlib.sha256(password.encode()).hexdigest() == admin_pass_hash:
            session["admin_auth"] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template_string(ADMIN_LOGIN_HTML, error="invalid admin credentials")

    return render_template_string(ADMIN_LOGIN_HTML, error="")

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get("admin_auth"):
        return redirect(url_for('admin_login'))

    users = get_users()
    total = len(users)
    active = sum(1 for u in users.values() if u.get("active", True))
    inactive = total - active
    remaining = get_remaining_seconds()
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
        "expiry_status": expiry_status
    }

    return render_template_string(ADMIN_DASHBOARD_HTML,
                                 users=users,
                                 stats=stats,
                                 remaining=remaining,
                                 expiry_local=expiry_local)

@app.route('/admin/set-expiry', methods=['POST'])
def admin_set_expiry():
    if not session.get("admin_auth"):
        return jsonify({"status": "error", "message": "unauthorized"}), 401

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
            remaining = get_remaining_seconds()
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

@app.route('/admin/add-user', methods=['POST'])
def admin_add_user():
    if not session.get("admin_auth"):
        return redirect(url_for('admin_login'))

    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    role = request.form.get('role', 'user')

    if not username or not password:
        flash("username and password required!", "error")
        return redirect(url_for('admin_dashboard'))

    users = get_users()
    if username in users:
        flash("username already exists!", "error")
        return redirect(url_for('admin_dashboard'))

    users[username] = {
        "password": hashlib.sha256(password.encode()).hexdigest(),
        "role": role,
        "active": True,
        "created": datetime.datetime.utcnow().isoformat()
    }
    if save_users(users):
        flash(f"vip user '{username}' created!", "success")
    else:
        flash("error creating user!", "error")

    return redirect(url_for('admin_dashboard'))

@app.route('/admin/edit/<username>', methods=['GET', 'POST'])
def admin_edit_user(username):
    if not session.get("admin_auth"):
        return redirect(url_for('admin_login'))

    if username == "sakil2026":
        flash("cannot edit default admin!", "error")
        return redirect(url_for('admin_dashboard'))

    users = get_users()
    if username not in users:
        flash("user not found!", "error")
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        new_password = request.form.get('password', '').strip()
        new_role = request.form.get('role', 'user')

        users[username]["role"] = new_role
        if new_password:
            users[username]["password"] = hashlib.sha256(new_password.encode()).hexdigest()
            flash("password updated!", "success")

        if save_users(users):
            flash("user updated!", "success")
        else:
            flash("error saving!", "error")

        return redirect(url_for('admin_dashboard'))

    return f'''
    <!DOCTYPE html>
    <html><head><title>edit user</title>
    <style>
        *{{margin:0;padding:0;box-sizing:border-box;}}
        body{{background:#06060a;display:flex;justify-content:center;align-items:center;min-height:100vh;font-family:'Inter',sans-serif;}}
        .box{{background:rgba(6,6,12,0.95);border:1px solid rgba(0,255,255,0.1);border-radius:20px;padding:30px;max-width:380px;width:92%;}}
        h1{{font-family:'Orbitron',monospace;font-size:18px;font-weight:700;color:#fff;letter-spacing:2px;text-align:center;}}
        h1 .hl{{color:#00ffff;}}
        .sub{{text-align:center;font-size:8px;font-family:'Orbitron',monospace;color:#88ddff;letter-spacing:3px;margin-bottom:16px;}}
        .form-group{{margin-bottom:12px;}}
        label{{display:block;font-size:8px;font-family:'Orbitron',monospace;color:#88ddff;letter-spacing:2px;margin-bottom:3px;}}
        input,select{{width:100%;padding:8px 12px;background:rgba(0,0,0,0.2);border:1px solid rgba(0,255,255,0.05);border-radius:8px;color:#fff;font-size:13px;outline:none;font-family:'Inter',sans-serif;margin-top:2px;}}
        input:focus,select:focus{{border-color:rgba(0,255,255,0.15);}}
        select option{{background:#0a0a1a;color:#fff;}}
        .btn{{width:100%;padding:10px;background:rgba(0,255,255,0.05);border:1px solid rgba(0,255,255,0.05);border-radius:8px;color:#88ddff;font-family:'Orbitron',monospace;font-size:10px;letter-spacing:2px;cursor:pointer;transition:all 0.3s ease;margin-top:4px;}}
        .btn:hover{{border-color:rgba(0,255,255,0.2);color:#00ffff;}}
        .back{{display:block;text-align:center;font-size:8px;font-family:'Orbitron',monospace;color:#88ddff;text-decoration:none;margin-top:10px;letter-spacing:2px;transition:all 0.3s ease;}}
        .back:hover{{color:#00ffff;}}
    </style>
    </head>
    <body>
    <div class="box">
        <h1><span class="hl">edit</span> user</h1>
        <div class="sub">premium · {username}</div>
        <form method="POST">
            <div class="form-group">
                <label><i class="fas fa-key"></i> new password (optional)</label>
                <input type="password" name="password" placeholder="leave blank to keep">
            </div>
            <div class="form-group">
                <label><i class="fas fa-user-tag"></i> role</label>
                <select name="role">
                    <option value="user" {"selected" if users[username].get("role")=="user" else ""}>user</option>
                    <option value="admin" {"selected" if users[username].get("role")=="admin" else ""}>admin</option>
                </select>
            </div>
            <button type="submit" class="btn"><i class="fas fa-save"></i> update</button>
        </form>
        <a href="{url_for('admin_dashboard')}" class="back"><i class="fas fa-arrow-left"></i> back</a>
    </div>
    </body>
    </html>
    '''

@app.route('/admin/toggle/<username>')
def admin_toggle_user(username):
    if not session.get("admin_auth"):
        return redirect(url_for('admin_login'))

    if username == "sakil2026":
        flash("cannot toggle default admin!", "error")
        return redirect(url_for('admin_dashboard'))

    users = get_users()
    if username not in users:
        flash("user not found!", "error")
        return redirect(url_for('admin_dashboard'))

    users[username]["active"] = not users[username].get("active", True)
    if save_users(users):
        status = "enabled" if users[username]["active"] else "disabled"
        flash(f"user {status}!", "success")
    else:
        flash("error toggling!", "error")

    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete/<username>')
def admin_delete_user(username):
    if not session.get("admin_auth"):
        return redirect(url_for('admin_login'))

    if username == "sakil2026":
        flash("cannot delete default admin!", "error")
        return redirect(url_for('admin_dashboard'))

    users = get_users()
    if username not in users:
        flash("user not found!", "error")
        return redirect(url_for('admin_dashboard'))

    del users[username]
    if save_users(users):
        flash(f"user '{username}' deleted!", "success")
    else:
        flash("error deleting!", "error")

    return redirect(url_for('admin_dashboard'))

@app.route('/admin/logout')
def admin_logout():
    session.pop("admin_auth", None)
    return redirect(url_for('admin_login'))

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

# ============================================
# MAIN
# ============================================

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    print("="*60)
    print("⚡ SAKIL BHAI - USER PANEL v8.0")
    print("🔥 CYBERPUNK EDITION · PREMIUM SYSTEM")
    print("📍 PERFECT LOCATION TRACKING - RED BORDER")
    print("="*60)
    print(f"✅ User Panel:  http://0.0.0.0:{port}")
    print(f"✅ Login:       http://0.0.0.0:{port}/login")
    print(f"✅ Admin:       http://0.0.0.0:{port}/admin")
    print("="*60)
    print("🔑 Default: sakil2026 / sakil2026")
    print("📁 Firebase: sakil-paid-hack-sell-1342007")
    print("="*60)

    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
