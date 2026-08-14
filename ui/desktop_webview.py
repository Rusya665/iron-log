"""PyWebView (Microsoft Edge WebView2) Desktop GUI for Iron Log.

Ultra-modern, state-of-the-art dark glassmorphic interface:
- Modern Typography: Google Fonts 'Outfit' (headers & metrics) + 'Inter' (data & body)
- Glassmorphic Elevated Surfaces & Ambient Glow Accents
- Top Desktop Menu Bar (App, Settings, Profiles, 🧪 Experimental)
- Dedicated Standalone Dynamic Plan Cycler Window
- Real-time Strength Standards Hover Tooltip & Full 280+ Library Browser
- Profile Manager & Switcher Modals
- Bodymass Prefill & Fill-in Missing Masses Modals
- sessions.py Validator & Scraper Integration
- Multi-threaded Excel Generation
"""

import os
import sys

# Ensure project root is in sys.path when invoked directly
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import copy
import glob
import importlib
import json
import re
import subprocess
import tempfile
import threading
import webbrowser
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import webview

from core.models import Log
from core.plan_generator import (
    PlannedExercise,
    PlannedSession,
    build_planned_sessions,
    calculate_gym_stats,
    days_to_generate,
    detect_cycle,
    get_genuinely_new_exercises,
    write_planned_sessions,
)
from core.profile_manager import Profile, ProfileManager
from core.standards import EXERCISE_STANDARDS, get_tiered_standards
from core.updater import check_for_updates
from core.version import __version__
from core.xlsx_generator import TrainingLogProcessor

# ─────────────────────────────────────────────────────────────────────────────
# 1. MAIN APPLICATION HTML TEMPLATE
# ─────────────────────────────────────────────────────────────────────────────
HTML_TEMPLATE = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Iron Log</title>
    <!-- Google Fonts: Outfit (Metrics & Headers) + Inter (Interface & Data) + JetBrains Mono -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@500;600&family=Outfit:wght@500;600;700;800;900&display=swap" rel="stylesheet">
    
    <style>
        :root {{
            --bg-app: #0A0D14;
            --bg-sidebar: rgba(13, 17, 26, 0.95);
            --bg-card: rgba(18, 24, 38, 0.72);
            --bg-card-hover: rgba(24, 32, 50, 0.85);
            --bg-glass-modal: rgba(15, 20, 32, 0.92);
            --border-glass: rgba(255, 255, 255, 0.08);
            --border-glass-hover: rgba(99, 102, 241, 0.4);
            
            --text-primary: #FFFFFF;
            --text-secondary: #94A3B8;
            --text-muted: #64748B;
            
            --accent-blue-start: #2563EB;
            --accent-blue-end: #06B6D4;
            --accent-purple-start: #7C3AED;
            --accent-purple-end: #C026D3;
            --accent-emerald-start: #059669;
            --accent-emerald-end: #10B981;
            --accent-amber-start: #D97706;
            --accent-amber-end: #F59E0B;
            
            --radius-sm: 6px;
            --radius-md: 10px;
            --radius-lg: 14px;
            --radius-xl: 18px;
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            -webkit-font-smoothing: antialiased;
        }}

        body {{
            background-color: var(--bg-app);
            color: var(--text-primary);
            height: 100vh;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            user-select: none;
            background-image: 
                radial-gradient(circle at 15% 15%, rgba(37, 99, 235, 0.08) 0%, transparent 40%),
                radial-gradient(circle at 85% 85%, rgba(124, 58, 237, 0.08) 0%, transparent 40%);
        }}

        /* Modern Custom Scrollbar */
        ::-webkit-scrollbar {{ width: 7px; height: 7px; }}
        ::-webkit-scrollbar-track {{ background: transparent; }}
        ::-webkit-scrollbar-thumb {{ background: rgba(255, 255, 255, 0.14); border-radius: 4px; }}
        ::-webkit-scrollbar-thumb:hover {{ background: rgba(255, 255, 255, 0.28); }}

        /* ── 0. TOP DESKTOP MENU BAR ────────────────────────────────────── */
        .top-menubar {{
            height: 32px;
            background-color: rgba(10, 13, 20, 0.95);
            backdrop-filter: blur(12px);
            border-bottom: 1px solid var(--border-glass);
            display: flex;
            align-items: center;
            padding: 0 12px;
            font-size: 12px;
            color: var(--text-secondary);
            position: relative;
            z-index: 500;
            flex-shrink: 0;
        }}
        .brand-badge {{
            font-family: 'Outfit', sans-serif;
            font-weight: 800;
            font-size: 12px;
            letter-spacing: 1px;
            background: linear-gradient(135deg, #60A5FA, #A78BFA);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-right: 14px;
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        .menu-btn {{
            padding: 4px 10px;
            cursor: pointer;
            border-radius: var(--radius-sm);
            position: relative;
            transition: all 0.15s cubic-bezier(0.16, 1, 0.3, 1);
            font-weight: 500;
        }}
        .menu-btn:hover, .menu-btn.active {{
            background-color: rgba(255, 255, 255, 0.08);
            color: #FFFFFF;
        }}

        .menu-dropdown {{
            position: absolute;
            top: 30px;
            left: 0;
            background: rgba(18, 24, 38, 0.95);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: var(--radius-md);
            min-width: 230px;
            padding: 5px;
            box-shadow: 0 16px 36px rgba(0,0,0,0.65), 0 0 0 1px rgba(255,255,255,0.05);
            display: none;
            flex-direction: column;
            z-index: 1000;
            animation: menuFade 0.15s cubic-bezier(0.16, 1, 0.3, 1);
        }}
        @keyframes menuFade {{
            from {{ opacity: 0; transform: translateY(-4px) scale(0.98); }}
            to {{ opacity: 1; transform: translateY(0) scale(1); }}
        }}
        .menu-dropdown.show {{ display: flex; }}
        .menu-item {{
            padding: 7px 12px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            cursor: pointer;
            font-size: 12px;
            color: #E2E8F0;
            border-radius: var(--radius-sm);
            transition: all 0.12s ease;
        }}
        .menu-item:hover {{
            background: linear-gradient(90deg, rgba(59, 130, 246, 0.85), rgba(37, 99, 235, 0.85));
            color: #FFFFFF;
            transform: translateX(2px);
        }}
        .menu-sep {{ height: 1px; background: rgba(255, 255, 255, 0.07); margin: 4px 2px; }}

        /* ── APP BODY ────────────────────────────────────────────────────── */
        .app-body {{
            flex: 1;
            display: flex;
            height: calc(100vh - 32px);
            overflow: hidden;
        }}

        /* ── 1. LEFT SIDEBAR ─────────────────────────────────────────────── */
        aside {{
            width: 224px;
            background: var(--bg-sidebar);
            backdrop-filter: blur(16px);
            border-right: 1px solid var(--border-glass);
            padding: 20px 16px;
            display: flex;
            flex-direction: column;
            gap: 8px;
            flex-shrink: 0;
            box-shadow: 4px 0 24px rgba(0,0,0,0.25);
        }}
        
        .profile-card {{
            background: linear-gradient(135deg, rgba(30, 41, 59, 0.7), rgba(15, 23, 42, 0.8));
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: var(--radius-lg);
            padding: 12px 14px;
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 6px;
            cursor: pointer;
            transition: all 0.2s ease;
        }}
        .profile-card:hover {{
            border-color: rgba(99, 102, 241, 0.4);
            transform: translateY(-1px);
            box-shadow: 0 4px 14px rgba(0,0,0,0.3);
        }}
        .profile-avatar {{
            width: 36px;
            height: 36px;
            border-radius: 10px;
            background: linear-gradient(135deg, #3B82F6, #8B5CF6);
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: 'Outfit', sans-serif;
            font-weight: 800;
            font-size: 15px;
            color: #FFFFFF;
            box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3);
        }}
        .profile-info {{ display: flex; flex-direction: column; }}
        .prof-name {{ font-family: 'Outfit', sans-serif; font-size: 15px; font-weight: 700; color: #FFFFFF; letter-spacing: 0.2px; }}
        .prof-badge {{ font-size: 10px; color: #4ADE80; display: flex; align-items: center; gap: 4px; font-weight: 600; margin-top: 1px; }}
        .prof-dot {{ width: 6px; height: 6px; border-radius: 50%; background-color: #4ADE80; box-shadow: 0 0 6px #4ADE80; }}

        .divider {{ height: 1px; background: rgba(255, 255, 255, 0.06); margin: 6px 0; }}

        /* Primary Action Buttons */
        .btn-side-primary1 {{
            background: linear-gradient(135deg, var(--accent-blue-start), var(--accent-blue-end));
            color: #FFFFFF; font-size: 13px; font-weight: 700;
            border-radius: var(--radius-md); padding: 12px 14px; border: none; cursor: pointer; text-align: center;
            box-shadow: 0 4px 14px rgba(37, 99, 235, 0.35); transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
            display: flex; align-items: center; justify-content: center; gap: 8px;
        }}
        .btn-side-primary1:hover {{ filter: brightness(1.15); transform: translateY(-2px); box-shadow: 0 6px 20px rgba(37, 99, 235, 0.5); }}

        .btn-side-primary2 {{
            background: linear-gradient(135deg, var(--accent-purple-start), var(--accent-purple-end));
            color: #FFFFFF; font-size: 13px; font-weight: 700;
            border-radius: var(--radius-md); padding: 12px 14px; border: none; cursor: pointer; text-align: center;
            box-shadow: 0 4px 14px rgba(124, 58, 237, 0.35); transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
            display: flex; align-items: center; justify-content: center; gap: 8px;
        }}
        .btn-side-primary2:hover {{ filter: brightness(1.15); transform: translateY(-2px); box-shadow: 0 6px 20px rgba(124, 58, 237, 0.5); }}

        .btn-side-primary3 {{
            background: linear-gradient(135deg, var(--accent-emerald-start), var(--accent-emerald-end));
            color: #FFFFFF; font-size: 13px; font-weight: 700;
            border-radius: var(--radius-md); padding: 12px 14px; border: none; cursor: pointer; text-align: center;
            box-shadow: 0 4px 14px rgba(5, 150, 105, 0.35); transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
            display: flex; align-items: center; justify-content: center; gap: 8px;
        }}
        .btn-side-primary3:hover {{ filter: brightness(1.15); transform: translateY(-2px); box-shadow: 0 6px 20px rgba(5, 150, 105, 0.5); }}

        .btn-side-sec {{
            background: rgba(255, 255, 255, 0.04);
            color: var(--text-secondary);
            font-size: 12px; font-weight: 600;
            border-radius: var(--radius-md); padding: 9px 12px; border: 1px solid rgba(255, 255, 255, 0.04);
            cursor: pointer; text-align: left; transition: all 0.15s ease;
            display: flex; align-items: center; gap: 9px;
        }}
        .btn-side-sec:hover {{
            background: rgba(255, 255, 255, 0.08);
            color: #FFFFFF;
            border-color: rgba(255, 255, 255, 0.1);
            transform: translateX(2px);
        }}

        .side-status-box {{
            margin-top: auto;
            background: rgba(15, 23, 42, 0.6);
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: var(--radius-md);
            padding: 10px;
            display: flex;
            flex-direction: column;
            gap: 2px;
        }}
        .side-status {{ font-size: 11px; color: var(--text-secondary); display: flex; align-items: center; gap: 6px; font-weight: 500; }}
        .side-last-gen {{ font-size: 10px; color: var(--text-muted); font-family: 'JetBrains Mono', monospace; }}

        /* ── 2. MAIN DASHBOARD ───────────────────────────────────────────── */
        main {{
            flex: 1;
            padding: 22px 28px;
            display: flex;
            flex-direction: column;
            gap: 18px;
            overflow-y: auto;
            background-color: transparent;
        }}

        .main-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        .header-left {{ display: flex; flex-direction: column; gap: 2px; }}
        .main-title {{
            font-family: 'Outfit', sans-serif;
            font-size: 26px;
            font-weight: 800;
            color: #FFFFFF;
            letter-spacing: -0.5px;
        }}
        .main-sub {{ font-size: 12px; color: var(--text-muted); }}

        .btn-refresh {{
            background: rgba(255, 255, 255, 0.06);
            color: #FFFFFF;
            font-size: 12px; font-weight: 600;
            border-radius: var(--radius-md); padding: 8px 16px;
            border: 1px solid rgba(255, 255, 255, 0.1); cursor: pointer;
            transition: all 0.2s ease; display: flex; align-items: center; gap: 6px;
            backdrop-filter: blur(10px);
        }}
        .btn-refresh:hover {{
            background: rgba(255, 255, 255, 0.12);
            border-color: rgba(255, 255, 255, 0.2);
            transform: translateY(-1px);
        }}

        /* 3 Stats Metric Cards Row */
        .stats-row {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 14px;
        }}
        .stat-card {{
            background: var(--bg-card);
            backdrop-filter: blur(16px);
            border: 1px solid var(--border-glass);
            border-radius: var(--radius-lg);
            padding: 16px 18px;
            display: flex;
            flex-direction: column;
            gap: 4px;
            transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
            position: relative;
            overflow: hidden;
        }}
        .stat-card::before {{
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0; height: 2px;
            background: linear-gradient(90deg, transparent, rgba(99, 102, 241, 0.5), transparent);
            opacity: 0; transition: opacity 0.2s;
        }}
        .stat-card:hover {{
            background: var(--bg-card-hover);
            border-color: var(--border-glass-hover);
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(0,0,0,0.4);
        }}
        .stat-card:hover::before {{ opacity: 1; }}

        .stat-card.clickable {{ cursor: pointer; }}
        .stat-card.clickable:hover {{
            border-color: rgba(59, 130, 246, 0.5);
            box-shadow: 0 8px 24px rgba(37, 99, 235, 0.15);
        }}

        .stat-header {{ display: flex; align-items: center; justify-content: space-between; }}
        .stat-t {{
            font-size: 11px;
            font-weight: 700;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.8px;
        }}
        .stat-icon-badge {{
            width: 26px;
            height: 26px;
            border-radius: 6px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 13px;
        }}
        .stat-v {{
            font-family: 'Outfit', sans-serif;
            font-size: 28px;
            font-weight: 800;
            color: #FFFFFF;
            letter-spacing: -0.5px;
            margin: 2px 0;
        }}
        .stat-s {{ font-size: 11px; color: var(--text-secondary); }}

        /* Workout Cards Horizontal Row */
        .sessions-row {{
            display: flex;
            gap: 14px;
            overflow-x: auto;
            flex: 1;
            padding-bottom: 8px;
        }}
        .workout-card {{
            background: var(--bg-card);
            backdrop-filter: blur(16px);
            border: 1px solid var(--border-glass);
            border-radius: var(--radius-lg);
            min-width: 275px;
            flex: 1;
            padding: 16px;
            display: flex;
            flex-direction: column;
            gap: 8px;
            transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
        }}
        .workout-card:hover {{
            background: var(--bg-card-hover);
            border-color: rgba(255, 255, 255, 0.15);
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(0,0,0,0.4);
        }}
        .workout-card.pr-card {{
            background: linear-gradient(180deg, rgba(55, 35, 10, 0.75), rgba(28, 18, 5, 0.85));
            border-color: rgba(245, 158, 11, 0.4);
            box-shadow: 0 4px 20px rgba(245, 158, 11, 0.1);
        }}
        .workout-card.pr-card:hover {{
            border-color: rgba(245, 158, 11, 0.7);
            box-shadow: 0 8px 28px rgba(245, 158, 11, 0.2);
        }}

        .workout-card-hdr {{
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        .hdr-date {{ font-family: 'Outfit', sans-serif; font-size: 13px; font-weight: 700; color: #FFFFFF; }}
        .hdr-pill {{
            background: rgba(255, 255, 255, 0.08);
            border: 1px solid rgba(255, 255, 255, 0.1);
            color: #93C5FD;
            font-size: 10px; font-weight: 700;
            border-radius: 4px; padding: 2px 7px; text-transform: uppercase;
        }}
        .workout-card.pr-card .hdr-pill {{
            background: rgba(245, 158, 11, 0.2);
            border-color: rgba(245, 158, 11, 0.4);
            color: #FCD34D;
        }}

        .card-sep {{ height: 1px; background: rgba(255, 255, 255, 0.06); margin: 2px 0 4px 0; }}
        .workout-card.pr-card .card-sep {{ background: rgba(245, 158, 11, 0.2); }}

        .ex-list {{ display: flex; flex-direction: column; gap: 4px; }}
        .ex-item {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 12px;
            padding: 5px 8px;
            border-radius: var(--radius-sm);
            background: rgba(255, 255, 255, 0.02);
            transition: all 0.12s ease;
        }}
        .ex-item:hover {{
            background: rgba(255, 255, 255, 0.06);
        }}
        .ex-name {{
            color: #E2E8F0;
            font-weight: 600;
            cursor: pointer;
            transition: color 0.12s;
        }}
        .ex-name:hover {{ color: #60A5FA; }}
        .ex-meta {{
            color: var(--text-secondary);
            font-size: 11px;
            font-family: 'JetBrains Mono', monospace;
            font-weight: 500;
            background: rgba(0, 0, 0, 0.25);
            padding: 2px 6px;
            border-radius: 4px;
            border: 1px solid rgba(255, 255, 255, 0.04);
        }}

        /* ── 3. HOVER STANDARDS TOOLTIP ──────────────────────────────────── */
        #standardsTooltip {{
            position: fixed;
            background: rgba(18, 24, 38, 0.95);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.15);
            border-radius: var(--radius-md);
            padding: 12px 14px;
            box-shadow: 0 16px 36px rgba(0,0,0,0.85);
            z-index: 2000;
            display: none;
            pointer-events: none;
            max-width: 400px;
            animation: tipFade 0.15s cubic-bezier(0.16, 1, 0.3, 1);
        }}
        @keyframes tipFade {{
            from {{ opacity: 0; transform: scale(0.97); }}
            to {{ opacity: 1; transform: scale(1); }}
        }}
        #standardsTooltip table {{
            border-collapse: collapse;
            font-size: 10px;
            width: 100%;
        }}
        #standardsTooltip th {{
            background: rgba(255, 255, 255, 0.08);
            color: #FFFFFF;
            padding: 5px 7px;
            font-weight: 700;
            text-align: center;
        }}
        #standardsTooltip td {{
            padding: 4px 7px;
            text-align: center;
            color: #CBD5E1;
            border-bottom: 1px solid rgba(255, 255, 255, 0.04);
            font-family: 'JetBrains Mono', monospace;
        }}
        #standardsTooltip tr.user-mass-row {{
            background: rgba(37, 99, 235, 0.25);
            font-weight: 700;
        }}
        #standardsTooltip tr.user-mass-row td {{
            color: #93C5FD;
        }}
        #standardsTooltip .achieved {{
            color: #4ADE80 !important;
            font-weight: 800;
        }}

        /* ── 4. MODALS & DIALOGS ─────────────────────────────────────────── */
        .modal-overlay {{
            position: fixed; inset: 0; background: rgba(0, 0, 0, 0.78);
            backdrop-filter: blur(12px);
            display: none; align-items: center; justify-content: center; z-index: 1000;
            opacity: 0; transition: opacity 0.2s ease;
        }}
        .modal-overlay.active {{ display: flex; opacity: 1; }}
        .modal-window {{
            background: var(--bg-glass-modal);
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: var(--radius-xl);
            width: 900px; max-height: 88vh; display: flex; flex-direction: column; overflow: hidden;
            box-shadow: 0 24px 60px rgba(0,0,0,0.85);
            animation: modalPop 0.22s cubic-bezier(0.16, 1, 0.3, 1);
        }}
        @keyframes modalPop {{
            0% {{ transform: scale(0.96) translateY(10px); opacity: 0; }}
            100% {{ transform: scale(1) translateY(0); opacity: 1; }}
        }}

        .modal-hdr {{
            background: rgba(255, 255, 255, 0.03);
            padding: 18px 24px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.07);
        }}
        .modal-title {{ font-family: 'Outfit', sans-serif; font-size: 18px; font-weight: 800; color: #FFFFFF; }}
        .modal-sub {{ font-size: 12px; color: var(--text-secondary); margin-top: 3px; }}
        .modal-body {{
            flex: 1; overflow-y: auto; padding: 20px 24px;
            display: flex; flex-direction: column; gap: 14px;
        }}
        .modal-footer {{
            background: rgba(10, 14, 23, 0.75);
            padding: 14px 24px;
            border-top: 1px solid rgba(255, 255, 255, 0.06);
            display: flex; gap: 12px; align-items: center;
        }}

        .plan-input {{
            background: rgba(255, 255, 255, 0.05);
            color: #FFFFFF; border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: var(--radius-sm); padding: 8px 12px; font-size: 12px; font-weight: 500; outline: none;
            transition: all 0.15s ease;
        }}
        .plan-input:focus {{
            border-color: #3B82F6; background: rgba(255, 255, 255, 0.08);
            box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.25);
        }}

        /* Standards & Tables */
        table {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
        th {{
            color: var(--text-muted); font-weight: 700; text-transform: uppercase; font-size: 11px;
            letter-spacing: 0.5px; padding: 10px 8px; border-bottom: 1px solid rgba(255, 255, 255, 0.08);
            text-align: left;
        }}
        td {{ padding: 9px 8px; border-bottom: 1px solid rgba(255, 255, 255, 0.04); color: #CBD5E1; }}
        tr:hover {{ background: rgba(255, 255, 255, 0.03); }}
        
        .badge-slug {{ color: #38BDF8; font-family: 'JetBrains Mono', monospace; font-size: 11px; }}
        .btn-tool {{
            background: rgba(255, 255, 255, 0.06); color: #FFFFFF; border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 4px; padding: 4px 10px; font-size: 11px; font-weight: 600; cursor: pointer;
            transition: all 0.15s;
        }}
        .btn-tool:hover {{ background: #3B82F6; border-color: #3B82F6; }}
    </style>
</head>
<body onclick="closeAllMenus(event)">
    <!-- ── 0. TOP DESKTOP MENU BAR ─────────────────────────────────────── -->
    <nav class="top-menubar">
        <div class="brand-badge">⚡ IRON LOG</div>
        
        <div class="menu-btn" id="mBtnApp" onclick="toggleMenu('menuApp', event)">
            App
            <div class="menu-dropdown" id="menuApp">
                <div class="menu-item" onclick="openAboutModal()">ℹ️  About Iron Log</div>
                <div class="menu-item" onclick="triggerUpdateCheck()">🔄  Check for Updates</div>
                <div class="menu-sep"></div>
                <div class="menu-item" onclick="openProfileCreator()">👤  New Profile...</div>
                <div class="menu-item" onclick="openProfilePicker()">👥  Switch User...</div>
                <div class="menu-sep"></div>
                <div class="menu-item" onclick="pywebview.api.open_app_data_folder()">📂  Open App Data Folder</div>
                <div class="menu-sep"></div>
                <div class="menu-item" onclick="window.close()">❌  Exit</div>
            </div>
        </div>

        <div class="menu-btn" id="mBtnSettings" onclick="toggleMenu('menuSettings', event)">
            Settings
            <div class="menu-dropdown" id="menuSettings">
                <div class="menu-item" id="optAutoLogin" onclick="toggleSetting('auto_login')">Auto-Login: Enabled</div>
                <div class="menu-item" id="optAutoUpdate" onclick="toggleSetting('auto_update')">Auto-Update: Enabled</div>
                <div class="menu-sep"></div>
                <div class="menu-item" id="optShowPR" onclick="toggleSetting('show_pr')">Show PRs: ON</div>
                <div class="menu-item" id="optShowStandards" onclick="toggleSetting('show_standards')">Show Standards: ON</div>
                <div class="menu-item" id="optShowMilestones" onclick="toggleSetting('show_milestones')">Show Milestones: ON</div>
            </div>
        </div>

        <div class="menu-btn" id="mBtnProfiles" onclick="toggleMenu('menuProfiles', event)">
            Profiles
            <div class="menu-dropdown" id="menuProfiles">
                <!-- Dynamically injected -->
            </div>
        </div>

        <div class="menu-btn" id="mBtnExp" onclick="toggleMenu('menuExp', event)">
            🧪 Experimental
            <div class="menu-dropdown" id="menuExp">
                <div class="menu-item" onclick="runBodymassPrefill()">📅  Prefill Mass Dates</div>
                <div class="menu-item" onclick="openMissingMassesModal()">⚖️  Fill-in Missing Masses</div>
                <div class="menu-sep"></div>
                <div class="menu-item" onclick="runValidateSessions()">✅  Validate sessions.py</div>
            </div>
        </div>
    </nav>

    <!-- ── APP LAYOUT ──────────────────────────────────────────────────── -->
    <div class="app-body">
        <!-- ── 1. LEFT SIDEBAR ─────────────────────────────────────────── -->
        <aside>
            <!-- Athlete Profile Pill -->
            <div class="profile-card" onclick="openProfilePicker()" title="Click to manage or switch athlete profiles">
                <div class="profile-avatar" id="avatarLetter">R</div>
                <div class="profile-info">
                    <div class="prof-name" id="sidebarProfName">Rustem</div>
                    <div class="prof-badge"><span class="prof-dot"></span> Active Athlete</div>
                </div>
            </div>

            <!-- Primary Action Buttons -->
            <button class="btn-side-primary1" onclick="generateExcel()">
                <span>🚀</span> Generate Excel Log
            </button>
            <button class="btn-side-primary2" onclick="openPlanCycler()">
                <span>🗓️</span> Plan Next Cycle
            </button>
            <button class="btn-side-primary3" onclick="pywebview.api.open_latest_excel()">
                <span>📂</span> Open Latest Log
            </button>

            <div class="divider"></div>

            <!-- Secondary Action Buttons -->
            <button class="btn-side-sec" onclick="pywebview.api.edit_sessions()">
                <span>📝</span> Edit Sessions
            </button>
            <button class="btn-side-sec" onclick="pywebview.api.open_output()">
                <span>📊</span> Output Folder
            </button>
            <button class="btn-side-sec" onclick="openStandardsModal()">
                <span>📚</span> Exercise Library
            </button>
            <button class="btn-side-sec" onclick="runScraper()">
                <span>⚡</span> Run Scraper
            </button>

            <!-- Bottom Status Indicator -->
            <div class="side-status-box">
                <div class="side-status" id="sidebarStatus">● System Ready</div>
                <div class="side-last-gen" id="sidebarLastGen"></div>
            </div>
        </aside>

        <!-- ── 2. MAIN CONTENT AREA ────────────────────────────────────── -->
        <main>
            <div class="main-header">
                <div class="header-left">
                    <div class="main-title">Recent Sessions</div>
                    <div class="main-sub">Training progression overview & strength trajectory</div>
                </div>
                <button class="btn-refresh" onclick="loadDashboard()">
                    <span>↻</span> Refresh
                </button>
            </div>

            <!-- 3 Stats Metric Cards -->
            <div class="stats-row">
                <div class="stat-card">
                    <div class="stat-header">
                        <div class="stat-t">Gym Attendance</div>
                        <div class="stat-icon-badge" style="background: rgba(37, 99, 235, 0.2); color: #60A5FA;">🔥</div>
                    </div>
                    <div class="stat-v" id="c1Val">-- Days</div>
                    <div class="stat-s" id="c1Sub">-- this year · -- this month</div>
                </div>

                <div class="stat-card clickable" onclick="openSplitModal()" title="Click to view full training split routine & history">
                    <div class="stat-header">
                        <div class="stat-t">Current Split Duration</div>
                        <div class="stat-icon-badge" style="background: rgba(124, 58, 237, 0.2); color: #C084FC;">⚡</div>
                    </div>
                    <div class="stat-v" id="c2Val">-- Weeks</div>
                    <div class="stat-s" id="c2Sub">N-Day Split · started --</div>
                </div>

                <div class="stat-card">
                    <div class="stat-header">
                        <div class="stat-t">Last Workout</div>
                        <div class="stat-icon-badge" style="background: rgba(245, 158, 11, 0.2); color: #FBBF24;">🏆</div>
                    </div>
                    <div class="stat-v" id="c3Val">--</div>
                    <div class="stat-s" id="c3Sub">Day --</div>
                </div>
            </div>

            <!-- Recent Sessions Horizontal Cards -->
            <div class="sessions-row" id="sessionsGrid">
                <div style="color: var(--text-muted); font-size: 13px;">Loading workout sessions...</div>
            </div>
        </main>
    </div>

    <!-- ── 3. HOVER STANDARDS TOOLTIP ──────────────────────────────────── -->
    <div id="standardsTooltip"></div>

    <!-- ── 4. STRENGTH STANDARDS MODAL ─────────────────────────────────── -->
    <div id="modalStandards" class="modal-overlay">
        <div class="modal-window" style="width: 880px;">
            <div class="modal-hdr">
                <div class="modal-title">Strength Standards Library</div>
                <div class="modal-sub">Browse benchmark lift targets for all 280+ strength exercises</div>
                <div style="margin-top: 12px; display: flex; gap: 8px;">
                    <input type="text" id="stdSearchInput" class="plan-input" placeholder="🔍  Search exercises by name or slug in real-time..." style="flex: 1;" oninput="filterStandards(this.value)">
                </div>
            </div>
            <div class="modal-body" style="max-height: 65vh;">
                <table>
                    <thead>
                        <tr>
                            <th>Exercise Name</th><th>Slug</th><th>Beg</th><th>Nov</th><th>Int</th><th>Adv</th><th>Eli</th><th>Actions</th>
                        </tr>
                    </thead>
                    <tbody id="stdTbody"></tbody>
                </table>
            </div>
            <div class="modal-footer">
                <button class="btn-tool" style="padding: 8px 18px; margin-left: auto;" onclick="closeModal('modalStandards')">Close</button>
            </div>
        </div>
    </div>

    <!-- ── 5. SPLIT DETAILS MODAL ──────────────────────────────────────── -->
    <div id="modalSplit" class="modal-overlay">
        <div class="modal-window" style="width: 660px;">
            <div class="modal-hdr">
                <div class="modal-title">Current Split Details & History</div>
                <div class="modal-sub">Overview of your current split cycle breakdown</div>
            </div>
            <div class="modal-body">
                <div class="stat-card" style="background: rgba(30, 41, 59, 0.5);">
                    <div class="stat-t">Current Routine</div>
                    <div id="splitOverview" style="font-size: 13px; margin-top: 6px; line-height: 1.6;"></div>
                </div>
                <div style="font-weight: 700; font-size: 13px; margin-top: 6px; color: var(--text-secondary);">Split Session Logs:</div>
                <table>
                    <thead>
                        <tr><th>Date</th><th>Day</th><th>Exercises</th></tr>
                    </thead>
                    <tbody id="splitTbody"></tbody>
                </table>
            </div>
            <div class="modal-footer">
                <button class="btn-tool" style="padding: 8px 18px; margin-left: auto;" onclick="closeModal('modalSplit')">Close</button>
            </div>
        </div>
    </div>

    <!-- ── 6. ABOUT DIALOG MODAL ───────────────────────────────────────── -->
    <div id="modalAbout" class="modal-overlay">
        <div class="modal-window" style="width: 400px;">
            <div class="modal-hdr" style="text-align: center;">
                <div class="modal-title">Iron Log</div>
                <div class="modal-sub" id="aboutVerText">Version {__version__}</div>
            </div>
            <div class="modal-body" style="text-align: center; gap: 10px; padding: 24px 20px;">
                <div style="font-size: 14px; color: var(--text-secondary);">Designed & built by Rustem Nizamov</div>
                <div style="font-size: 12px; color: var(--text-muted);">High-Performance Local Strength & Progressive Overload Suite</div>
                <button class="btn-side-sec" style="margin: 14px auto 0 auto; justify-content: center; width: 190px;" onclick="pywebview.api.open_url('https://github.com/Rusya665/iron-log')">GitHub Repository ↗</button>
            </div>
            <div class="modal-footer">
                <button class="btn-tool" style="padding: 8px 18px; margin-left: auto;" onclick="closeModal('modalAbout')">Close</button>
            </div>
        </div>
    </div>

    <!-- ── 7. PROFILE PICKER MODAL ─────────────────────────────────────── -->
    <div id="modalProfilePicker" class="modal-overlay">
        <div class="modal-window" style="width: 540px;">
            <div class="modal-hdr">
                <div class="modal-title">Select Your Profile</div>
                <div class="modal-sub">Switch active athlete account</div>
            </div>
            <div class="modal-body">
                <div id="profilePickerList" style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px;"></div>
            </div>
            <div class="modal-footer">
                <button class="btn-side-primary2" style="padding: 8px 14px;" onclick="openProfileCreator()">+ New Profile</button>
                <button class="btn-tool" style="padding: 8px 18px; margin-left: auto;" onclick="closeModal('modalProfilePicker')">Close</button>
            </div>
        </div>
    </div>

    <!-- ── 8. PROFILE CREATOR / EDITOR MODAL ────────────────────────────── -->
    <div id="modalProfileCreator" class="modal-overlay">
        <div class="modal-window" style="width: 500px;">
            <div class="modal-hdr">
                <div class="modal-title" id="profModalTitle">Create Profile</div>
            </div>
            <div class="modal-body" style="gap: 12px;">
                <input type="hidden" id="profEditIndex" value="-1">
                <div>
                    <label style="font-size: 12px; color: var(--text-secondary); display: block; margin-bottom: 4px;">Name:</label>
                    <input type="text" id="profNameInput" class="plan-input" style="width: 100%;" placeholder="e.g. Rustem">
                </div>
                <div>
                    <label style="font-size: 12px; color: var(--text-secondary); display: block; margin-bottom: 4px;">Sex:</label>
                    <div style="display: flex; gap: 20px; font-size: 13px;">
                        <label style="display: flex; align-items: center; gap: 6px; cursor: pointer;">
                            <input type="radio" name="profSex" value="male" id="sexMale" checked> Male
                        </label>
                        <label style="display: flex; align-items: center; gap: 6px; cursor: pointer;">
                            <input type="radio" name="profSex" value="female" id="sexFemale"> Female
                        </label>
                    </div>
                </div>
                <div>
                    <label style="font-size: 12px; color: var(--text-secondary); display: block; margin-bottom: 4px;">Data Folder (sessions.py location):</label>
                    <div style="display: flex; gap: 8px;">
                        <input type="text" id="profDirInput" class="plan-input" style="flex: 1;" placeholder="C:/path/to/folder">
                        <button class="btn-tool" onclick="browseFolder()">Browse...</button>
                    </div>
                    <div style="font-size: 11px; color: var(--text-muted); margin-top: 4px;">Each user needs their own folder. Excel logs will be saved in a 'gym' subfolder.</div>
                </div>
            </div>
            <div class="modal-footer">
                <button class="btn-tool" style="padding: 8px 16px;" onclick="closeModal('modalProfileCreator')">Cancel</button>
                <button class="btn-side-primary3" style="padding: 8px 18px; margin-left: auto;" onclick="saveProfileForm()">Save Profile</button>
            </div>
        </div>
    </div>

    <!-- ── 9. FILL-IN MISSING MASSES MODAL ────────────────────────────── -->
    <div id="modalMissingMasses" class="modal-overlay">
        <div class="modal-window" style="width: 440px;">
            <div class="modal-hdr">
                <div class="modal-title">Fill-in Missing Masses</div>
                <div class="modal-sub">Enter body mass values for workout dates where mass is None.</div>
            </div>
            <div class="modal-body" id="missingMassesContainer" style="max-height: 50vh;"></div>
            <div class="modal-footer">
                <button class="btn-tool" style="padding: 8px 16px;" onclick="closeModal('modalMissingMasses')">Cancel</button>
                <button class="btn-side-primary3" style="padding: 8px 18px; margin-left: auto;" onclick="saveMissingMasses()">💾 Save Mass Values</button>
            </div>
        </div>
    </div>

    <script>
        let cachedStats = {{}};
        let activeMenu = null;

        function toggleMenu(menuId, e) {{
            if (e) e.stopPropagation();
            const el = document.getElementById(menuId);
            const isShow = el.classList.contains("show");
            closeAllMenus();
            if (!isShow) {{
                el.classList.add("show");
                activeMenu = menuId;
            }}
        }}

        function closeAllMenus() {{
            document.querySelectorAll(".menu-dropdown").forEach(d => d.classList.remove("show"));
            activeMenu = null;
        }}

        function closeModal(id) {{
            document.getElementById(id).classList.remove("active");
        }}

        function openModal(id) {{
            document.getElementById(id).classList.add("active");
        }}

        async function init() {{
            try {{
                await loadDashboard();
                await updateMenuState();
            }} catch (err) {{
                console.error("Init Error:", err);
                document.getElementById("sidebarStatus").innerText = "● Init Error: " + err;
            }}
        }}

        async function updateMenuState() {{
            if (!window.pywebview || !window.pywebview.api) return;
            const settings = await pywebview.api.get_settings();
            document.getElementById("optAutoLogin").innerText = "Auto-Login: " + (settings.auto_login ? "Enabled" : "Disabled");
            document.getElementById("optAutoUpdate").innerText = "Auto-Update: " + (settings.auto_update ? "Enabled" : "Disabled");
            document.getElementById("optShowPR").innerText = "Show PRs: " + (settings.show_pr ? "ON" : "OFF");
            document.getElementById("optShowStandards").innerText = "Show Standards: " + (settings.show_standards ? "ON" : "OFF");
            document.getElementById("optShowMilestones").innerText = "Show Milestones: " + (settings.show_milestones ? "ON" : "OFF");

            // Populate Profiles Menu
            const pData = await pywebview.api.get_profiles();
            const profMenu = document.getElementById("menuProfiles");
            profMenu.innerHTML = "";
            (pData.profiles || []).forEach((p, idx) => {{
                const isActive = idx === pData.active_index;
                const item = document.createElement("div");
                item.className = "menu-item";
                item.style.fontWeight = isActive ? "700" : "500";
                item.innerHTML = `<span>${{isActive ? '✓ ' : ''}}${{p.name}}</span><span style="font-size: 10px; color: var(--text-muted);">Select</span>`;
                item.onclick = async (e) => {{
                    e.stopPropagation();
                    closeAllMenus();
                    await pywebview.api.select_profile(idx);
                    await loadDashboard();
                    await updateMenuState();
                }};
                profMenu.appendChild(item);
            }});
            profMenu.innerHTML += '<div class="menu-sep"></div><div class="menu-item" onclick="openProfilePicker()">👥  Manage Profiles...</div>';
        }}

        async function toggleSetting(settingName) {{
            await pywebview.api.toggle_setting(settingName);
            await updateMenuState();
        }}

        async function loadDashboard() {{
            if (!window.pywebview || !window.pywebview.api) return;
            document.getElementById("sidebarStatus").innerText = "● Loading...";
            const data = await pywebview.api.get_active_data();
            if (!data.success) {{
                document.getElementById("sidebarStatus").innerText = "● " + data.error;
                return;
            }}
            document.getElementById("sidebarProfName").innerText = data.profile_name;
            document.getElementById("avatarLetter").innerText = (data.profile_name || "U").charAt(0).toUpperCase();
            const s = data.stats;
            cachedStats = s;

            // Stats Cards
            document.getElementById("c1Val").innerText = (s.total_days || 0) + " Days";
            document.getElementById("c1Sub").innerText = (s.this_year_days || 0) + " this year · " + (s.this_month_days || 0) + " this month";

            document.getElementById("c2Val").innerText = (s.current_split_weeks || 0).toFixed(1) + " Wks";
            document.getElementById("c2Sub").innerText = (s.cycle_length || "N/A") + "-Day Split · started " + (s.current_split_start || "N/A");

            document.getElementById("c3Val").innerText = s.latest_workout_date || "N/A";
            document.getElementById("c3Sub").innerText = "Day " + (s.latest_workout_day || "N/A") + " Completed";

            // Workout Cards
            const grid = document.getElementById("sessionsGrid");
            grid.innerHTML = "";
            (data.sessions || []).forEach(sess => {{
                const isPR = typeof sess.day === 'string' && sess.day.toUpperCase() === 'PR';
                const card = document.createElement("div");
                card.className = "workout-card" + (isPR ? " pr-card" : "");
                
                let exsHtml = "";
                sess.exercises.forEach(ex => {{
                    exsHtml += `
                        <div class="ex-item">
                            <span class="ex-name" onmouseenter="showTooltip(event, '${{ex.id}}', ${{sess.mass || 0}}, ${{ex.max_lift || 0}}, ${{isPR}})" onmouseleave="hideTooltip()">${{ex.name}}</span>
                            <span class="ex-meta">${{ex.summary}}</span>
                        </div>
                    `;
                }});
                
                const dayLabel = typeof sess.day === 'number' ? `Day ${{sess.day}}` : `${{sess.day}}`;
                card.innerHTML = `
                    <div class="workout-card-hdr">
                        <span class="hdr-date">📅  ${{sess.date}}</span>
                        <span class="hdr-pill">${{dayLabel}}</span>
                    </div>
                    <div class="card-sep"></div>
                    <div class="ex-list">${{exsHtml}}</div>
                `;
                grid.appendChild(card);
            }});

            document.getElementById("sidebarStatus").innerText = "● System Ready";
        }}

        /* ── Hover Standards Tooltip ──────────────────────────────────────── */
        let tooltipTimer = null;
        async function showTooltip(e, exId, userMass, userLift, isPR) {{
            clearTimeout(tooltipTimer);
            const x = e.clientX + 14;
            const y = e.clientY + 14;
            
            tooltipTimer = setTimeout(async () => {{
                const tableData = await pywebview.api.get_exercise_standards_table(exId);
                const tip = document.getElementById("standardsTooltip");
                
                if (!tableData || !tableData.standards || Object.keys(tableData.standards).length === 0) {{
                    tip.innerHTML = `<div style="font-size: 11px; color: var(--text-secondary);">Standards not available for ${{tableData.name || exId}}</div>`;
                }} else {{
                    let rowsHtml = "";
                    const targetBm = tableData.target_bm;
                    
                    for (const [bm, levels] of Object.entries(tableData.standards)) {{
                        const isUserBm = parseInt(bm) === targetBm;
                        let cells = `<td>${{bm}}kg</td>`;
                        for (const lvl of ["Beginner", "Novice", "Intermediate", "Advanced", "Elite"]) {{
                            const val = levels[lvl] || "-";
                            const achieved = isPR && typeof val === 'number' && userLift >= val;
                            cells += `<td class="${{achieved ? 'achieved' : ''}}">${{val}}</td>`;
                        }}
                        rowsHtml += `<tr class="${{isUserBm ? 'user-mass-row' : ''}}">${{cells}}</tr>`;
                    }}

                    tip.innerHTML = `
                        <div style="font-size: 12px; font-weight: 700; margin-bottom: 6px; color: #FFF; font-family: 'Outfit', sans-serif;">${{tableData.name}} Standards</div>
                        <table>
                            <thead><tr><th>Mass</th><th>Beg</th><th>Nov</th><th>Int</th><th>Adv</th><th>Eli</th></tr></thead>
                            <tbody>${{rowsHtml}}</tbody>
                        </table>
                    `;
                }}
                
                tip.style.left = Math.min(x, window.innerWidth - 410) + "px";
                tip.style.top = Math.min(y, window.innerHeight - 260) + "px";
                tip.style.display = "block";
            }}, 220);
        }}

        function hideTooltip() {{
            clearTimeout(tooltipTimer);
            document.getElementById("standardsTooltip").style.display = "none";
        }}

        /* ── Actions & Dialogs ────────────────────────────────────────────── */
        async function generateExcel() {{
            document.getElementById("sidebarStatus").innerText = "● Generating Log...";
            const res = await pywebview.api.generate_excel();
            if (res.success) {{
                document.getElementById("sidebarStatus").innerText = "✅ Generated Log";
                document.getElementById("sidebarLastGen").innerText = "Last gen: " + res.time;
            }} else {{
                document.getElementById("sidebarStatus").innerText = "❌ " + res.error;
                alert("Generation Error: " + res.error);
            }}
        }}

        async function openPlanCycler() {{
            document.getElementById("sidebarStatus").innerText = "● Opening Planner...";
            await pywebview.api.open_planner_window();
            document.getElementById("sidebarStatus").innerText = "● System Ready";
        }}

        async function runScraper() {{
            document.getElementById("sidebarStatus").innerText = "● Running scraper...";
            const res = await pywebview.api.run_scraper();
            if (res.success) {{
                document.getElementById("sidebarStatus").innerText = "● Scraper active";
            }} else {{
                document.getElementById("sidebarStatus").innerText = "● Scraper error: " + res.error;
            }}
        }}

        async function triggerUpdateCheck() {{
            document.getElementById("sidebarStatus").innerText = "● Checking updates...";
            const res = await pywebview.api.check_updates();
            if (res.has_update) {{
                if (confirm(`A new version (${{res.version}}) is available!\\nDo you want to open the download page?`)) {{
                    pywebview.api.open_url(res.url);
                }}
            }} else {{
                alert(`You are on the latest version (v${{res.current}}).`);
            }}
            document.getElementById("sidebarStatus").innerText = "● System Ready";
        }}

        async function runValidateSessions() {{
            document.getElementById("sidebarStatus").innerText = "● Validating...";
            const res = await pywebview.api.run_validate_sessions();
            if (res.success) {{
                let msg = "✅ " + res.message;
                if (res.none_mass_dates && res.none_mass_dates.length > 0) {{
                    msg += `\\n\\n⚠️ ${{res.none_mass_dates.length}} BODYMASS_LOG entries still have mass=None:\\n` + res.none_mass_dates.map(d => "  • " + d).join("\\n");
                    msg += "\\n\\nUse 🧪 Experimental → Fill-in Missing Masses to complete them.";
                }}
                alert(msg);
                document.getElementById("sidebarStatus").innerText = "✅ Validated";
            }} else {{
                alert("❌ " + res.error);
                document.getElementById("sidebarStatus").innerText = "❌ Validation failed";
            }}
        }}

        async function runBodymassPrefill() {{
            document.getElementById("sidebarStatus").innerText = "● Prefilling...";
            const res = await pywebview.api.run_bodymass_prefill();
            if (res.success) {{
                if (res.count === 0) {{
                    alert("All workout dates are already present in BODYMASS_LOG. Nothing to add.");
                }} else {{
                    alert(`✅ Added ${{res.count}} date(s) to BODYMASS_LOG with mass=None in sessions.py.`);
                }}
                document.getElementById("sidebarStatus").innerText = "● System Ready";
            }} else {{
                alert("Prefill Error: " + res.error);
            }}
        }}

        async function openMissingMassesModal() {{
            const res = await pywebview.api.get_missing_masses();
            if (!res.success) {{
                alert("Error: " + res.error);
                return;
            }}
            if (!res.entries || res.entries.length === 0) {{
                alert("All Done: No missing mass entries in BODYMASS_LOG! 🎉");
                return;
            }}
            const container = document.getElementById("missingMassesContainer");
            container.innerHTML = "";
            res.entries.forEach(d => {{
                const row = document.createElement("div");
                row.style.cssText = "display: flex; align-items: center; gap: 10px; margin-bottom: 8px;";
                row.innerHTML = `
                    <span style="font-size: 13px; width: 110px; font-family: 'JetBrains Mono', monospace;">${{d}}</span>
                    <input type="number" step="0.1" class="plan-input missing-mass-input" data-date="${{d}}" placeholder="e.g. 83.5" style="flex: 1;">
                    <span style="color: var(--text-secondary); font-size: 12px;">kg</span>
                `;
                container.appendChild(row);
            }});
            openModal("modalMissingMasses");
        }}

        async function saveMissingMasses() {{
            const inputs = document.querySelectorAll(".missing-mass-input");
            const updates = {{}};
            inputs.forEach(inp => {{
                const v = parseFloat(inp.value);
                if (!isNaN(v) && v > 0) {{
                    updates[inp.dataset.date] = v;
                }}
            }});
            if (Object.keys(updates).length === 0) {{
                alert("No mass values were entered.");
                return;
            }}
            const res = await pywebview.api.save_missing_masses(updates);
            if (res.success) {{
                alert(`✅ Updated ${{res.count}} mass value(s) in sessions.py.`);
                closeModal("modalMissingMasses");
                await loadDashboard();
            }} else {{
                alert("Error saving masses: " + res.error);
            }}
        }}

        function openAboutModal() {{
            openModal("modalAbout");
        }}

        /* ── Profile Modals ───────────────────────────────────────────────── */
        async function openProfilePicker() {{
            const data = await pywebview.api.get_profiles();
            const list = document.getElementById("profilePickerList");
            list.innerHTML = "";
            (data.profiles || []).forEach((p, idx) => {{
                const isAct = idx === data.active_index;
                const card = document.createElement("div");
                card.className = "stat-card clickable";
                card.style.borderColor = isAct ? "rgba(59, 130, 246, 0.6)" : "var(--border-glass)";
                card.innerHTML = `
                    <div style="font-family: 'Outfit', sans-serif; font-weight: 700; font-size: 16px; color: ${{isAct ? '#60A5FA' : '#FFF'}};">${{p.name}}</div>
                    <div style="font-size: 11px; color: var(--text-muted);">${{p.sessions_dir}}</div>
                    <div style="display: flex; gap: 6px; margin-top: 10px;">
                        <button class="btn-tool" onclick="selectProf(${{idx}})">Select</button>
                        <button class="btn-tool" onclick="editProf(${{idx}})">Edit</button>
                        <button class="btn-tool" style="color: #F87171;" onclick="deleteProf(${{idx}}, '${{p.name}}')">Delete</button>
                    </div>
                `;
                list.appendChild(card);
            }});
            openModal("modalProfilePicker");
        }}

        async function selectProf(idx) {{
            await pywebview.api.select_profile(idx);
            closeModal("modalProfilePicker");
            await loadDashboard();
            await updateMenuState();
        }}

        async function editProf(idx) {{
            const data = await pywebview.api.get_profiles();
            const p = data.profiles[idx];
            document.getElementById("profModalTitle").innerText = "Edit Profile";
            document.getElementById("profEditIndex").value = idx;
            document.getElementById("profNameInput").value = p.name;
            document.getElementById("profDirInput").value = p.sessions_dir;
            if (p.sex === "female") document.getElementById("sexFemale").checked = true;
            else document.getElementById("sexMale").checked = true;
            closeModal("modalProfilePicker");
            openModal("modalProfileCreator");
        }}

        async function deleteProf(idx, name) {{
            if (confirm(`Are you sure you want to delete profile '${{name}}'?`)) {{
                await pywebview.api.delete_profile(idx);
                await openProfilePicker();
                await updateMenuState();
            }}
        }}

        function openProfileCreator() {{
            document.getElementById("profModalTitle").innerText = "Create New Profile";
            document.getElementById("profEditIndex").value = -1;
            document.getElementById("profNameInput").value = "";
            document.getElementById("profDirInput").value = "";
            document.getElementById("sexMale").checked = true;
            openModal("modalProfileCreator");
        }}

        async function browseFolder() {{
            const path = await pywebview.api.browse_folder();
            if (path) {{
                document.getElementById("profDirInput").value = path;
            }}
        }}

        async function saveProfileForm() {{
            const idx = parseInt(document.getElementById("profEditIndex").value);
            const isEdit = idx >= 0;
            const pData = {{
                name: document.getElementById("profNameInput").value.trim(),
                sessions_dir: document.getElementById("profDirInput").value.trim(),
                sex: document.getElementById("sexFemale").checked ? "female" : "male"
            }};
            const res = await pywebview.api.save_profile(pData, isEdit, idx);
            if (res.success) {{
                closeModal("modalProfileCreator");
                await loadDashboard();
                await updateMenuState();
            }} else {{
                alert("Error: " + res.error);
            }}
        }}

        /* ── Standards & Split ───────────────────────────────────────────── */
        async function openStandardsModal() {{
            await filterStandards("");
            openModal("modalStandards");
        }}
        
        async function filterStandards(query) {{
            const list = await pywebview.api.search_standards(query);
            const tbody = document.getElementById("stdTbody");
            tbody.innerHTML = "";
            (list || []).forEach(item => {{
                const tr = document.createElement("tr");
                tr.innerHTML = `
                    <td style="font-weight: 600;">${{item.name}}</td>
                    <td><span class="badge-slug">${{item.slug}}</span></td>
                    <td>${{item.beg}}</td><td>${{item.nov}}</td><td>${{item.int}}</td><td>${{item.adv}}</td><td>${{item.eli}}</td>
                    <td style="display: flex; gap: 4px;">
                        <button class="btn-tool" onclick="pywebview.api.copy_clipboard('${{item.slug}}')">Copy</button>
                        <button class="btn-tool" onclick="pywebview.api.copy_clipboard('${{item.slug.replace(/-/g, '_')}} = \\'${{item.slug}}\\'')">Copy Py</button>
                        <button class="btn-tool" onclick="pywebview.api.open_url('https://strengthlevel.com/strength-standards/${{item.slug}}')">View ↗</button>
                    </td>
                `;
                tbody.appendChild(tr);
            }});
        }}

        function openSplitModal() {{
            const s = cachedStats;
            const daysEx = s.split_days_exercises || {{}};
            let routineHtml = "";
            for (const [dNum, exs] of Object.entries(daysEx)) {{
                routineHtml += `<div style="margin-bottom: 6px;"><strong style="color: #60A5FA;">Day ${{dNum}}:</strong> ${{exs.join(", ")}}</div>`;
            }}
            document.getElementById("splitOverview").innerHTML = routineHtml || "<div>Routine information loading...</div>";

            const tbody = document.getElementById("splitTbody");
            tbody.innerHTML = "";
            (s.split_sessions_details || []).forEach(sess => {{
                const tr = document.createElement("tr");
                tr.innerHTML = `
                    <td style="font-family: 'JetBrains Mono', monospace;">${{sess.date_str}}</td>
                    <td><span class="badge-slug">Day ${{sess.day}}</span></td>
                    <td>${{(sess.exercises || []).join(", ")}}</td>
                `;
                tbody.appendChild(tr);
            }});
            openModal("modalSplit");
        }}

        // Robust App Initializer
        function startApp() {{
            if (window.pywebview && window.pywebview.api) {{
                init();
            }} else {{
                window.addEventListener('pywebviewready', init);
                let attempts = 0;
                const timer = setInterval(() => {{
                    attempts++;
                    if (window.pywebview && window.pywebview.api) {{
                        clearInterval(timer);
                        init();
                    }} else if (attempts > 30) {{
                        clearInterval(timer);
                    }}
                }}, 100);
            }}
        }}

        if (document.readyState === 'loading') {{
            document.addEventListener('DOMContentLoaded', startApp);
        }} else {{
            startApp();
        }}
    </script>
</body>
</html>
"""


# ─────────────────────────────────────────────────────────────────────────────
# 2. STANDALONE PLANNER WINDOW HTML TEMPLATE
# ─────────────────────────────────────────────────────────────────────────────
PLANNER_HTML_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Iron Log - Plan Next Cycle</title>
    <!-- Google Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@500;600&family=Outfit:wght@500;600;700;800&display=swap" rel="stylesheet">

    <style>
        :root {
            --bg-app: #0A0D14;
            --bg-card: rgba(18, 24, 38, 0.75);
            --border-glass: rgba(255, 255, 255, 0.08);
            --text-primary: #FFFFFF;
            --text-secondary: #94A3B8;
            --text-muted: #64748B;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            -webkit-font-smoothing: antialiased;
        }

        body {
            background-color: var(--bg-app);
            color: var(--text-primary);
            height: 100vh;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            user-select: none;
            background-image: 
                radial-gradient(circle at 20% 15%, rgba(124, 58, 237, 0.08) 0%, transparent 40%),
                radial-gradient(circle at 80% 85%, rgba(37, 99, 235, 0.08) 0%, transparent 40%);
        }

        /* Custom Scrollbar */
        ::-webkit-scrollbar { width: 7px; height: 7px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.14); border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: rgba(255, 255, 255, 0.28); }

        header {
            background: rgba(15, 20, 32, 0.95);
            backdrop-filter: blur(16px);
            border-bottom: 1px solid var(--border-glass);
            padding: 16px 24px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .header-title {
            font-family: 'Outfit', sans-serif;
            font-size: 20px;
            font-weight: 800;
            color: #FFFFFF;
            letter-spacing: -0.3px;
        }
        .header-sub { font-size: 12px; color: var(--text-secondary); margin-top: 2px; }

        main {
            flex: 1;
            overflow-y: auto;
            padding: 20px 24px;
            display: flex;
            flex-direction: column;
            gap: 16px;
        }

        footer {
            background: rgba(10, 14, 23, 0.9);
            backdrop-filter: blur(16px);
            border-top: 1px solid var(--border-glass);
            padding: 14px 24px;
            display: flex;
            align-items: center;
            gap: 12px;
        }

        /* Cycler Day Box */
        .plan-day-card {
            background: var(--bg-card);
            backdrop-filter: blur(16px);
            border: 1px solid var(--border-glass);
            border-radius: 12px;
            padding: 16px;
            display: flex;
            flex-direction: column;
            gap: 12px;
            box-shadow: 0 8px 24px rgba(0,0,0,0.35);
        }
        .plan-day-hdr {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 8px;
            padding: 8px 14px;
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .day-pill {
            background: linear-gradient(135deg, #00897B, #004D40);
            color: white; font-family: 'Outfit', sans-serif; font-weight: 800; font-size: 12px;
            border-radius: 5px; padding: 4px 12px; letter-spacing: 0.5px;
            box-shadow: 0 2px 8px rgba(0, 137, 123, 0.3);
        }
        .date-label { font-size: 12px; font-weight: 600; color: var(--text-secondary); }

        .plan-input {
            background: rgba(255, 255, 255, 0.05);
            color: #FFFFFF; border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 6px; padding: 7px 10px; font-size: 12px; font-weight: 500; outline: none;
            transition: all 0.15s ease;
        }
        .plan-input:focus {
            border-color: #3B82F6; background: rgba(255, 255, 255, 0.08);
            box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.25);
        }
        .plan-input.center { text-align: center; }

        .plan-row-grid {
            display: grid;
            grid-template-columns: 55px 1fr 60px 105px 115px 1fr 140px;
            gap: 8px;
            align-items: center;
        }
        .plan-col-head {
            font-size: 11px; font-weight: 700; color: var(--text-muted); text-transform: uppercase;
            letter-spacing: 0.5px; padding: 0 4px;
        }
        .plan-item-row {
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid rgba(255, 255, 255, 0.04);
            border-radius: 6px; padding: 6px 8px; transition: all 0.15s;
        }
        .plan-item-row:hover {
            background: rgba(255, 255, 255, 0.05);
            border-color: rgba(255, 255, 255, 0.08);
        }

        .order-btn-group { display: flex; gap: 2px; }
        .btn-arrow {
            background: rgba(255, 255, 255, 0.05); color: #AAA; border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 4px; width: 24px; height: 26px; cursor: pointer; font-size: 10px;
            display: flex; align-items: center; justify-content: center; transition: all 0.15s;
        }
        .btn-arrow:hover { background: #3B82F6; color: #FFF; border-color: #3B82F6; }

        .btn-pill-inc {
            background: rgba(34, 197, 94, 0.15); color: #4ADE80; border: 1px solid rgba(34, 197, 94, 0.3);
            border-radius: 5px; padding: 4px 6px; font-size: 10px; font-weight: 700; cursor: pointer;
            transition: all 0.15s;
        }
        .btn-pill-inc:hover { background: #22C55E; color: #000; }
        
        .btn-pill-rep {
            background: rgba(192, 132, 252, 0.15); color: #C084FC; border: 1px solid rgba(192, 132, 252, 0.3);
            border-radius: 5px; padding: 4px 6px; font-size: 10px; font-weight: 700; cursor: pointer;
            transition: all 0.15s;
        }
        .btn-pill-rep:hover { background: #A855F7; color: #000; }

        .btn-trash {
            background: rgba(239, 68, 68, 0.15); color: #F87171; border: 1px solid rgba(239, 68, 68, 0.3);
            border-radius: 5px; width: 26px; height: 26px; cursor: pointer; font-size: 11px;
            display: flex; align-items: center; justify-content: center; transition: all 0.15s;
        }
        .btn-trash:hover { background: #EF4444; color: #FFF; }

        .btn-add-ex {
            background: linear-gradient(135deg, #0288D1, #01579B);
            color: white; font-weight: 700; font-size: 12px; border: none;
            border-radius: 6px; padding: 6px 14px; cursor: pointer; transition: all 0.15s;
        }
        .btn-add-ex:hover { filter: brightness(1.15); }

        .btn-del-day {
            background: rgba(220, 38, 38, 0.15); color: #FCA5A5; border: 1px solid rgba(220, 38, 38, 0.3);
            border-radius: 6px; padding: 5px 10px; font-size: 12px; cursor: pointer;
        }
        .btn-del-day:hover { background: #DC2626; color: #FFF; }

        .btn-save-plan {
            background: linear-gradient(135deg, #059669, #10B981);
            color: white; font-family: 'Outfit', sans-serif; font-weight: 800; font-size: 13px; border: none;
            border-radius: 8px; padding: 11px 24px; cursor: pointer; margin-left: auto;
            box-shadow: 0 4px 14px rgba(16, 185, 129, 0.35); transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
        }
        .btn-save-plan:hover { filter: brightness(1.15); transform: translateY(-1px); box-shadow: 0 6px 20px rgba(16, 185, 129, 0.5); }

        .btn-sec {
            background: rgba(255, 255, 255, 0.05); color: var(--text-secondary); font-size: 12px; font-weight: 700;
            border-radius: 8px; padding: 10px 18px; border: 1px solid rgba(255, 255, 255, 0.08); cursor: pointer;
            transition: all 0.15s;
        }
        .btn-sec:hover { background: rgba(255, 255, 255, 0.1); color: #FFF; }

        .btn-primary2 {
            background: linear-gradient(135deg, #7C3AED, #C026D3);
            color: #FFFFFF; font-size: 12px; font-weight: 700;
            border-radius: 8px; padding: 10px 18px; border: none; cursor: pointer;
            box-shadow: 0 4px 14px rgba(124, 58, 237, 0.3); transition: all 0.15s;
        }
        .btn-primary2:hover { filter: brightness(1.15); }
    </style>
</head>
<body>
    <header>
        <div>
            <div class="header-title" id="cyclerTitle">Plan Next Cycle</div>
            <div class="header-sub">Configure your training split. Type exercise variable name, sets, reps, mass, and notes.</div>
        </div>
    </header>

    <main id="cyclerDaysContainer"></main>

    <footer>
        <button class="btn-sec" onclick="window.close()">Cancel</button>
        <button class="btn-primary2" onclick="addPlanDay()">+ Add Day</button>
        <button class="btn-sec" onclick="applyDeload()">🧪 Deload Next Cycle (-10%)</button>
        <button class="btn-save-plan" onclick="saveCyclerPlan()">✅ Write to sessions.py</button>
    </footer>

    <script>
        let currentPlan = [];

        async function initPlanner() {
            const res = await pywebview.api.get_plan();
            if (!res.success) {
                alert(res.error);
                window.close();
                return;
            }
            currentPlan = res.planned;
            document.getElementById("cyclerTitle").innerText = "Plan Next Cycle (" + res.why + ")";
            renderCyclerDays();
        }

        function renderCyclerDays() {
            const container = document.getElementById("cyclerDaysContainer");
            container.innerHTML = "";

            currentPlan.forEach((d, dayIdx) => {
                const dayCard = document.createElement("div");
                dayCard.className = "plan-day-card";

                let rowsHtml = "";
                d.exercises.forEach((ex, exIdx) => {
                    rowsHtml += `
                        <div class="plan-row-grid plan-item-row">
                            <div class="order-btn-group">
                                <button class="btn-arrow" onclick="moveEx(${dayIdx}, ${exIdx}, -1)" ${exIdx===0?'disabled style="opacity:0.3;"':''}>▲</button>
                                <button class="btn-arrow" onclick="moveEx(${dayIdx}, ${exIdx}, 1)" ${exIdx===d.exercises.length-1?'disabled style="opacity:0.3;"':''}>▼</button>
                            </div>
                            <input type="text" class="plan-input" style="font-family: 'JetBrains Mono', monospace;" value="${ex.var_name}" oninput="updateEx(${dayIdx}, ${exIdx}, 'var_name', this.value)" placeholder="exercise_slug">
                            <input type="number" class="plan-input center" value="${ex.sets}" oninput="updateEx(${dayIdx}, ${exIdx}, 'sets', this.value)">
                            <input type="text" class="plan-input center" style="font-family: 'JetBrains Mono', monospace;" value="${ex.reps}" oninput="updateEx(${dayIdx}, ${exIdx}, 'reps', this.value)">
                            <input type="text" class="plan-input center" style="font-family: 'JetBrains Mono', monospace;" value="${ex.mass}" oninput="updateEx(${dayIdx}, ${exIdx}, 'mass', this.value)">
                            <input type="text" class="plan-input" value="${ex.comment || ''}" oninput="updateEx(${dayIdx}, ${exIdx}, 'comment', this.value)" placeholder="comment">
                            <div style="display: flex; gap: 4px; align-items: center;">
                                <button class="btn-pill-inc" onclick="incMass(${dayIdx}, ${exIdx})">+2.5kg</button>
                                <button class="btn-pill-rep" onclick="incReps(${dayIdx}, ${exIdx})">+2 Reps</button>
                                <button class="btn-trash" onclick="delEx(${dayIdx}, ${exIdx})">✕</button>
                            </div>
                        </div>
                    `;
                });

                dayCard.innerHTML = `
                    <div class="plan-day-hdr">
                        <span class="day-pill">Day ${d.day_num}</span>
                        <span class="date-label">Date:</span>
                        <input type="date" class="plan-input" value="${d.date_str}" onchange="updateDayDate(${dayIdx}, this.value)" style="width: 140px;">
                        <button class="btn-add-ex" style="margin-left: auto;" onclick="addEx(${dayIdx})">+ Add Exercise</button>
                        <button class="btn-del-day" onclick="delDay(${dayIdx})">🗑️ Delete Day</button>
                    </div>
                    <div class="plan-row-grid" style="padding: 0 8px;">
                        <div class="plan-col-head">Order</div>
                        <div class="plan-col-head">Exercise Slug</div>
                        <div class="plan-col-head" style="text-align: center;">Sets</div>
                        <div class="plan-col-head" style="text-align: center;">Reps</div>
                        <div class="plan-col-head" style="text-align: center;">Mass (kg)</div>
                        <div class="plan-col-head">Comment</div>
                        <div class="plan-col-head">Actions</div>
                    </div>
                    <div style="display: flex; flex-direction: column; gap: 4px;">${rowsHtml}</div>
                `;
                container.appendChild(dayCard);
            });
        }

        function updateEx(dIdx, eIdx, field, val) { currentPlan[dIdx].exercises[eIdx][field] = val; }
        function updateDayDate(dIdx, val) { currentPlan[dIdx].date_str = val; }
        function moveEx(dIdx, eIdx, dir) {
            const arr = currentPlan[dIdx].exercises;
            const target = eIdx + dir;
            if (target < 0 || target >= arr.length) return;
            const temp = arr[eIdx]; arr[eIdx] = arr[target]; arr[target] = temp;
            renderCyclerDays();
        }
        function incMass(dIdx, eIdx) {
            const ex = currentPlan[dIdx].exercises[eIdx];
            const mParts = (ex.mass + "").split(",").map(p => {
                const v = parseFloat(p.trim());
                return !isNaN(v) && v > 0 ? (Math.round((v + 2.5) * 100) / 100) : p.trim();
            });
            ex.mass = mParts.join(", ");

            // Automatically track increment in Comment field
            let c = (ex.comment || "").trim();
            const match = c.match(/\+([0-9.]+)\s*kg/i);
            if (match) {
                const currPlus = parseFloat(match[1]);
                const newPlus = Math.round((currPlus + 2.5) * 100) / 100;
                c = c.replace(/\+[0-9.]+\s*kg/i, `+${newPlus} kg`);
            } else {
                c = (c + " +2.5 kg").trim();
            }
            ex.comment = c;

            renderCyclerDays();
        }

        function incReps(dIdx, eIdx) {
            const ex = currentPlan[dIdx].exercises[eIdx];
            const rParts = (ex.reps + "").split(",").map(p => {
                const v = parseInt(p.trim());
                return !isNaN(v) ? (v + 2) : p.trim();
            });
            ex.reps = rParts.join(", ");

            // Automatically track rep increment in Comment field
            let c = (ex.comment || "").trim();
            const match = c.match(/\+([0-9]+)\s*reps/i);
            if (match) {
                const currPlus = parseInt(match[1]);
                const newPlus = currPlus + 2;
                c = c.replace(/\+[0-9]+\s*reps/i, `+${newPlus} reps`);
            } else {
                c = (c + " +2 reps").trim();
            }
            ex.comment = c;

            renderCyclerDays();
        }

        function delEx(dIdx, eIdx) { currentPlan[dIdx].exercises.splice(eIdx, 1); renderCyclerDays(); }
        function addEx(dIdx) {
            currentPlan[dIdx].exercises.push({ var_name: "squat", display_name: "Squat", sets: 3, reps: "6, 6, 6", mass: "80.0", comment: "" });
            renderCyclerDays();
        }
        function delDay(dIdx) {
            currentPlan.splice(dIdx, 1);
            currentPlan.forEach((d, i) => d.day_num = i + 1);
            renderCyclerDays();
        }
        function addPlanDay() {
            const nextDayNum = currentPlan.length + 1;
            const lastDate = currentPlan.length > 0 ? currentPlan[currentPlan.length - 1].date_str : new Date().toISOString().split('T')[0];
            const d = new Date(lastDate);
            d.setDate(d.getDate() + 2);
            currentPlan.push({
                day_num: nextDayNum,
                date_str: d.toISOString().split('T')[0],
                exercises: [{ var_name: "squat", display_name: "Squat", sets: 3, reps: "6, 6, 6", mass: "80.0", comment: "" }]
            });
            renderCyclerDays();
        }
        function applyDeload() {
            currentPlan.forEach(d => {
                d.exercises.forEach(ex => {
                    const mParts = (ex.mass + "").split(",").map(p => {
                        const v = parseFloat(p.trim());
                        return !isNaN(v) && v > 0 ? (Math.round((v * 0.9) * 2) / 2) : p.trim();
                    });
                    ex.mass = mParts.join(", ");
                    let c = (ex.comment || "").trim();
                    if (!c.includes("10% decreased deload") && !c.includes("Deload -10%")) {
                        c = (c ? c + " · " : "") + "10% decreased deload";
                    }
                    ex.comment = c;
                });
            });
            renderCyclerDays();
        }
        async function saveCyclerPlan() {
            const res = await pywebview.api.save_plan(currentPlan);
            if (res.success) {
                alert(`✅ Successfully created plan with ${currentPlan.length} days!`);
                window.close();
            } else {
                alert("Error writing plan: " + res.error);
            }
        }

        function startPlannerApp() {
            if (window.pywebview && window.pywebview.api) {
                initPlanner();
            } else {
                window.addEventListener('pywebviewready', initPlanner);
                let attempts = 0;
                const timer = setInterval(() => {
                    attempts++;
                    if (window.pywebview && window.pywebview.api) {
                        clearInterval(timer);
                        initPlanner();
                    } else if (attempts > 30) {
                        clearInterval(timer);
                    }
                }, 100);
            }
        }

        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', startPlannerApp);
        } else {
            startPlannerApp();
        }
    </script>
</body>
</html>
"""


_MAIN_WINDOW: Optional[webview.Window] = None
_PLANNER_WINDOW: Optional[webview.Window] = None


class WebViewBridgeApi:
    """Python backend bridge API matching 100% of CustomTkinter engine features."""

    def __init__(self):
        self.manager = ProfileManager()
        self.last_gen_time = ""

    def _load_sessions(self, p: Profile):
        sessions_file = getattr(p, "sessions_file", None) or os.path.join(p.sessions_dir, "sessions.py")
        if not os.path.exists(sessions_file):
            return None, sessions_file

        sessions_dir = os.path.dirname(sessions_file)
        if sessions_dir not in sys.path:
            sys.path.insert(0, sessions_dir)

        if "sessions" in sys.modules:
            sess = importlib.reload(sys.modules["sessions"])
        else:
            import sessions as sess
        return sess, sessions_file

    def open_planner_window(self):
        """Spawns the Dynamic Plan Cycler as a dedicated standalone window."""
        global _PLANNER_WINDOW
        if _PLANNER_WINDOW:
            try:
                _PLANNER_WINDOW.show()
                return {"success": True}
            except Exception:
                _PLANNER_WINDOW = None

        _PLANNER_WINDOW = webview.create_window(
            title="Iron Log - Plan Next Cycle",
            html=PLANNER_HTML_TEMPLATE,
            js_api=self,
            width=1100,
            height=750,
            min_size=(860, 560),
            background_color="#0A0D14",
        )
        return {"success": True}

    def get_settings(self) -> Dict[str, Any]:
        p = self.manager.get_active_profile()
        return {
            "auto_login": self.manager.remember_last_user,
            "auto_update": self.manager.auto_check_updates,
            "show_pr": getattr(p, "show_pr", True) if p else True,
            "show_standards": getattr(p, "show_standards", True) if p else True,
            "show_milestones": getattr(p, "show_milestones", True) if p else True,
        }

    def toggle_setting(self, setting_name: str) -> Dict[str, Any]:
        p = self.manager.get_active_profile()
        if setting_name == "auto_login":
            self.manager.remember_last_user = not self.manager.remember_last_user
        elif setting_name == "auto_update":
            self.manager.auto_check_updates = not self.manager.auto_check_updates
        elif p and hasattr(p, setting_name):
            setattr(p, setting_name, not getattr(p, setting_name))
        self.manager.save_profiles()
        return self.get_settings()

    def get_profiles(self) -> Dict[str, Any]:
        return {
            "active_index": self.manager.active_profile_index,
            "profiles": [p.to_dict() for p in self.manager.profiles],
        }

    def select_profile(self, index: int) -> Dict[str, Any]:
        self.manager.set_active(index)
        return {"success": True}

    def save_profile(self, profile_data: Dict[str, Any], is_edit: bool = False, index: int = 0) -> Dict[str, Any]:
        name = profile_data.get("name", "").strip()
        s_dir = profile_data.get("sessions_dir", "").strip()
        sex = profile_data.get("sex", "male")

        if not name:
            return {"success": False, "error": "Profile name cannot be empty."}
        if not s_dir:
            return {"success": False, "error": "Data folder path cannot be empty."}

        new_p = Profile(
            name=name,
            sessions_dir=s_dir,
            output_dir=os.path.join(s_dir, "gym"),
            sex=sex,
        )
        if is_edit:
            self.manager.update_profile(index, new_p)
        else:
            self.manager.add_profile(new_p)
            self.manager.set_active(len(self.manager.profiles) - 1)
        return {"success": True}

    def delete_profile(self, index: int) -> Dict[str, Any]:
        if 0 <= index < len(self.manager.profiles):
            self.manager.delete_profile(index)
            return {"success": True}
        return {"success": False, "error": "Invalid profile index"}

    def browse_folder(self) -> str:
        import tkinter as tk
        from tkinter import filedialog
        r = tk.Tk()
        r.withdraw()
        r.attributes("-topmost", True)
        path = filedialog.askdirectory(parent=r)
        r.destroy()
        return path or ""

    def check_updates(self) -> Dict[str, Any]:
        has_update, new_ver, dl_url = check_for_updates(__version__)
        return {"has_update": has_update, "version": new_ver, "url": dl_url, "current": __version__}

    def get_active_data(self) -> Dict[str, Any]:
        p = self.manager.get_active_profile()
        if not p:
            return {"success": False, "error": "No profile selected"}

        sess, file_path = self._load_sessions(p)
        if not sess:
            return {"success": False, "error": f"sessions.py not found at {file_path}"}

        user_data = getattr(sess, "USER_DATA", {})
        bm_log = getattr(sess, "BODYMASS_LOG", {})
        stats = calculate_gym_stats(user_data)

        date_pat = re.compile(r"^\d{4}-\d{2}-\d{2}$")
        sorted_dates = sorted([d for d in user_data.keys() if date_pat.match(d)], reverse=True)
        N, _ = detect_cycle(user_data)
        show_dates = sorted_dates[: N if N else 3]

        recent_sessions = []
        for d_str in reversed(show_dates):
            day_data = user_data[d_str]
            v = day_data.get("day")
            day_obj = v if isinstance(v, (int, str)) else None

            # Resolve mass for date
            mass = None
            if bm_log:
                for d in sorted(bm_log.keys()):
                    if d <= d_str:
                        bm_entry = bm_log[d]
                        mass = bm_entry if isinstance(bm_entry, (int, float)) else bm_entry.get("mass", 0)
                    else:
                        break

            exs = []
            for ex_id, log in day_data.items():
                if not isinstance(log, Log):
                    continue
                info = EXERCISE_STANDARDS.get(ex_id, {})
                display_name = info.get("name", ex_id)

                # Format reps
                n_sets = len(log.reps)
                if len(set(log.reps)) == 1:
                    reps_part = f"{n_sets} × {log.reps[0]}"
                else:
                    reps_part = "-".join(str(r) for r in log.reps)

                # Format mass
                max_lift = max(log.mass) if log.mass else 0
                if log.mass and max(log.mass) > 0:
                    if len(set(log.mass)) == 1:
                        mass_part = f" @ {log.mass[0]}kg"
                    else:
                        mass_part = f" @ {min(log.mass)}-{max(log.mass)}kg"
                else:
                    mass_part = " (BW)"
                    max_lift = mass if mass else 0

                summary = f"{reps_part}{mass_part}"
                exs.append({
                    "id": ex_id,
                    "name": display_name,
                    "summary": summary,
                    "max_lift": max_lift,
                })

            recent_sessions.append({
                "date": d_str,
                "day": day_obj,
                "mass": mass,
                "exercises": exs,
            })

        clean_stats = {
            "total_days": stats.get("total_days", 0),
            "this_year_days": stats.get("this_year_days", 0),
            "this_month_days": stats.get("this_month_days", 0),
            "latest_workout_date": stats.get("latest_workout_date", "N/A"),
            "latest_workout_day": stats.get("latest_workout_day", "N/A"),
            "current_split_weeks": stats.get("current_split_weeks", 0.0),
            "current_split_start": stats.get("current_split_start", "N/A"),
            "cycle_length": stats.get("cycle_length", "N/A"),
            "split_days_exercises": stats.get("split_days_exercises", {}),
            "split_sessions_details": [
                {"date_str": s.get("date_str", ""), "day": s.get("day", ""), "exercises": list(s.get("exercises", []))}
                for s in stats.get("split_sessions_details", [])
            ],
        }

        return {
            "success": True,
            "profile_name": p.name,
            "stats": clean_stats,
            "sessions": recent_sessions,
        }

    def get_exercise_standards_table(self, exercise_id: str) -> Dict[str, Any]:
        p = self.manager.get_active_profile()
        sex = getattr(p, "sex", "male") if p else "male"
        mass = getattr(p, "mass", 80.0) if p else 80.0
        standards = get_tiered_standards(exercise_id, sex, None)
        target_bm = int(mass / 5.0) * 5 if mass else 80
        name = EXERCISE_STANDARDS.get(exercise_id, {}).get("name", exercise_id)
        return {
            "exercise_id": exercise_id,
            "name": name,
            "target_bm": target_bm,
            "standards": standards or {},
        }

    def generate_excel(self) -> Dict[str, Any]:
        p = self.manager.get_active_profile()
        if not p:
            return {"success": False, "error": "No profile"}

        sess, _ = self._load_sessions(p)
        if not sess:
            return {"success": False, "error": "Could not load sessions.py"}

        try:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
            filename = os.path.join(p.output_dir, f"Training_Log_{timestamp}.xlsx")
            processor = TrainingLogProcessor(
                filename,
                sess.EXERCISE_REGISTRY,
                sess.USER_DATA,
                sess.BODYMASS_LOG,
                p.to_dict(),
            )
            processor.validate_data()
            processor.write_headers()
            processor.process_data(sess.USER_DATA)
            processor.write_calculations()
            processor.generate_charts()
            processor.write_definitions()
            processor.write_personal_records()
            processor.write_user_profile()
            processor.save()

            self.last_gen_time = datetime.now().strftime("%Y-%m-%d %H:%M")
            try:
                os.startfile(filename)
            except Exception:
                pass

            return {"success": True, "time": self.last_gen_time}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def run_scraper(self) -> Dict[str, Any]:
        script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts", "batch_scraper.py"))
        try:
            subprocess.Popen([sys.executable, script_path])
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def run_validate_sessions(self) -> Dict[str, Any]:
        p = self.manager.get_active_profile()
        if not p:
            return {"success": False, "error": "No active profile"}
        sess, _ = self._load_sessions(p)
        if not sess:
            return {"success": False, "error": "Could not load sessions.py"}

        dummy_path = os.path.join(tempfile.gettempdir(), "_ironlog_validate_dummy.xlsx")
        try:
            processor = TrainingLogProcessor(
                dummy_path,
                sess.EXERCISE_REGISTRY,
                sess.USER_DATA,
                sess.BODYMASS_LOG,
                p.to_dict(),
            )
            processor.validate_data()

            date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
            none_mass_dates = [
                d for d, v in getattr(sess, "BODYMASS_LOG", {}).items()
                if date_pattern.match(d) and isinstance(v, dict) and v.get("mass") is None
            ]

            try:
                processor.wb.close()
            except Exception:
                pass
            try:
                os.remove(dummy_path)
            except Exception:
                pass

            return {
                "success": True,
                "message": "sessions.py is valid! No data mismatches found.",
                "none_mass_dates": none_mass_dates,
            }
        except ValueError as ve:
            try:
                os.remove(dummy_path)
            except Exception:
                pass
            return {"success": False, "error": f"Validation Failed: {ve}"}
        except Exception as e:
            try:
                os.remove(dummy_path)
            except Exception:
                pass
            return {"success": False, "error": f"Unexpected error: {e}"}

    def run_bodymass_prefill(self) -> Dict[str, Any]:
        p = self.manager.get_active_profile()
        if not p:
            return {"success": False, "error": "No active profile"}
        sessions_file = getattr(p, "sessions_file", None) or os.path.join(p.sessions_dir, "sessions.py")
        if not os.path.exists(sessions_file):
            return {"success": False, "error": f"sessions.py not found at {sessions_file}"}

        sess, _ = self._load_sessions(p)
        if not sess:
            return {"success": False, "error": "Could not load sessions.py"}

        date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
        user_dates = {k for k in getattr(sess, "USER_DATA", {}).keys() if date_pattern.match(k)}
        existing_dates = set(getattr(sess, "BODYMASS_LOG", {}).keys())
        missing = sorted(user_dates - existing_dates)

        if not missing:
            return {"success": True, "count": 0, "message": "All workout dates are already present in BODYMASS_LOG."}

        with open(sessions_file, "r", encoding="utf-8") as f:
            lines = f.readlines()

        start_line = next((i for i, ln in enumerate(lines) if ln.startswith("BODYMASS_LOG = {")), -1)
        if start_line == -1:
            return {"success": False, "error": "Could not locate BODYMASS_LOG in sessions.py"}

        close_line = next((i for i in range(start_line + 1, len(lines)) if lines[i].rstrip("\r\n") == "}"), -1)
        if close_line == -1:
            return {"success": False, "error": "Could not find closing brace of BODYMASS_LOG"}

        insert_text = "".join(f'    "{d}": {{"mass": None}},\n' for d in missing)
        new_lines = lines[:close_line] + [insert_text] + lines[close_line:]

        with open(sessions_file, "w", encoding="utf-8") as f:
            f.writelines(new_lines)

        return {"success": True, "count": len(missing), "dates": missing}

    def get_missing_masses(self) -> Dict[str, Any]:
        p = self.manager.get_active_profile()
        if not p:
            return {"success": False, "error": "No active profile"}
        sess, _ = self._load_sessions(p)
        if not sess:
            return {"success": False, "error": "Could not load sessions.py"}

        date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
        none_entries = sorted([
            d for d, v in getattr(sess, "BODYMASS_LOG", {}).items()
            if date_pattern.match(d) and isinstance(v, dict) and v.get("mass") is None
        ])
        return {"success": True, "entries": none_entries}

    def save_missing_masses(self, updates: Dict[str, float]) -> Dict[str, Any]:
        p = self.manager.get_active_profile()
        if not p:
            return {"success": False, "error": "No active profile"}
        sessions_file = getattr(p, "sessions_file", None) or os.path.join(p.sessions_dir, "sessions.py")
        if not os.path.exists(sessions_file):
            return {"success": False, "error": "sessions.py not found"}

        with open(sessions_file, "r", encoding="utf-8") as f:
            source = f.read()

        count = 0
        for date_str, val in updates.items():
            old = f'"{date_str}": {{"mass": None}}'
            new = f'"{date_str}": {{"mass": {val}}}'
            if old in source:
                source = source.replace(old, new, 1)
                count += 1
            else:
                subbed, n = re.subn(
                    rf'("{re.escape(date_str)}")\s*:\s*\{{"mass"\s*:\s*None\}}',
                    rf'\1: {{"mass": {val}}}',
                    source,
                )
                if n > 0:
                    source = subbed
                    count += n

        with open(sessions_file, "w", encoding="utf-8") as f:
            f.write(source)

        return {"success": True, "count": count}

    def get_plan(self) -> Dict[str, Any]:
        p = self.manager.get_active_profile()
        if not p:
            return {"success": False, "error": "No profile"}

        sess, file_path = self._load_sessions(p)
        if not sess:
            return {"success": False, "error": "Could not load sessions.py"}

        user_data = getattr(sess, "USER_DATA", {})
        N, last_day_int = detect_cycle(user_data)
        if N is None:
            return {"success": False, "error": "Could not detect your split cycle yet."}

        day_nums = days_to_generate(N, last_day_int)
        if not day_nums:
            return {"success": False, "error": "All days in current cycle are already planned."}

        try:
            planned = build_planned_sessions(file_path, day_nums)
            why = f"Starting new cycle — all {N} days" if (last_day_int or 0) >= N else f"Completing cycle of {N}"
            serializable_plan = [
                {
                    "day_num": ps.day_number,
                    "date_str": ps.date_str,
                    "exercises": [
                        {
                            "var_name": ex.var_name,
                            "display_name": getattr(ex, "display_name", ex.var_name),
                            "sets": ex.sets,
                            "reps": ex.reps,
                            "mass": ex.mass,
                            "comment": ex.comment,
                        }
                        for ex in ps.exercises
                    ],
                }
                for ps in planned
            ]
            return {"success": True, "planned": serializable_plan, "why": why}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def save_plan(self, planned_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        p = self.manager.get_active_profile()
        if not p:
            return {"success": False, "error": "No profile"}

        sessions_file = getattr(p, "sessions_file", None) or os.path.join(p.sessions_dir, "sessions.py")
        try:
            planned_objs = []
            for d in planned_data:
                ex_objs = [
                    PlannedExercise(
                        var_name=e.get("var_name", "exercise"),
                        display_name=e.get("display_name", e.get("var_name", "exercise")),
                        sets=int(e.get("sets", 3)),
                        reps=str(e.get("reps", "5")),
                        mass=str(e.get("mass", "0")),
                        comment=str(e.get("comment", "")),
                    )
                    for e in d.get("exercises", [])
                ]
                planned_objs.append(
                    PlannedSession(day_number=int(d.get("day_num", 1)), date_str=d.get("date_str", ""), exercises=ex_objs)
                )

            write_planned_sessions(sessions_file, planned_objs)

            # Close standalone planner window if open
            global _PLANNER_WINDOW, _MAIN_WINDOW
            if _PLANNER_WINDOW:
                try:
                    _PLANNER_WINDOW.destroy()
                    _PLANNER_WINDOW = None
                except Exception:
                    pass

            # Trigger reload in main window
            if _MAIN_WINDOW:
                try:
                    _MAIN_WINDOW.evaluate_js("loadDashboard();")
                except Exception:
                    pass

            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def search_standards(self, query: str) -> List[Dict[str, Any]]:
        p = self.manager.get_active_profile()
        sex = getattr(p, "sex", "male") if p else "male"
        mass = getattr(p, "mass", 80.0) if p else 80.0

        q = (query or "").strip().lower()
        results = []
        target_bm = int(mass / 5.0) * 5

        for slug, info in EXERCISE_STANDARDS.items():
            name = info.get("name", slug)
            if q and (q not in name.lower() and q not in slug.lower()):
                continue

            standards = get_tiered_standards(slug, sex, mass)
            levels = standards.get(target_bm, {}) if standards else {}

            results.append({
                "slug": slug,
                "name": name,
                "beg": levels.get("Beginner", "-"),
                "nov": levels.get("Novice", "-"),
                "int": levels.get("Intermediate", "-"),
                "adv": levels.get("Advanced", "-"),
                "eli": levels.get("Elite", "-"),
            })
        return results

    def copy_clipboard(self, text: str):
        import tkinter as tk
        r = tk.Tk()
        r.withdraw()
        r.clipboard_clear()
        r.clipboard_append(text)
        r.update()
        r.destroy()

    def open_url(self, url: str):
        webbrowser.open(url)

    def open_latest_excel(self):
        p = self.manager.get_active_profile()
        if p and p.output_dir and os.path.exists(p.output_dir):
            files = sorted(glob.glob(os.path.join(p.output_dir, "Training_Log_*.xlsx")), reverse=True)
            if files:
                os.startfile(files[0])

    def edit_sessions(self):
        p = self.manager.get_active_profile()
        if p and p.sessions_dir:
            f = os.path.join(p.sessions_dir, "sessions.py")
            if os.path.exists(f):
                os.startfile(f)

    def open_output(self):
        p = self.manager.get_active_profile()
        if p and p.output_dir and os.path.exists(p.output_dir):
            os.startfile(p.output_dir)

    def open_app_data_folder(self):
        if getattr(sys, "frozen", False):
            path = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "IronLog")
        else:
            path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        os.makedirs(path, exist_ok=True)
        os.startfile(path)


def run_webview_app():
    global _MAIN_WINDOW
    api = WebViewBridgeApi()
    _MAIN_WINDOW = webview.create_window(
        title=f"Iron Log - Strength Tracker v{__version__} (PyWebView Edition)",
        html=HTML_TEMPLATE,
        js_api=api,
        width=1160,
        height=740,
        min_size=(960, 600),
        background_color="#0A0D14",
    )
    webview.start(debug=False)


if __name__ == "__main__":
    run_webview_app()
