"""PyWebView (Microsoft Edge WebView2) Desktop GUI for Iron Log.

Ultra-sleek, modern dark-themed interface with glassmorphic modals,
custom scrollbars, interactive workout cycler, and instant search.
"""

import copy
import glob
import importlib
import json
import os
import re
import sys
import threading
import webbrowser
from datetime import datetime, timedelta
from typing import Any, Dict, List

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
from core.version import __version__
from core.xlsx_generator import TrainingLogProcessor

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Iron Log</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: "Roboto", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
        body { background-color: #121212; color: #FFFFFF; height: 100vh; display: flex; overflow: hidden; user-select: none; }
        
        /* Custom Modern Scrollbars */
        ::-webkit-scrollbar { width: 8px; height: 8px; }
        ::-webkit-scrollbar-track { background: #121212; }
        ::-webkit-scrollbar-thumb { background: #2E2E2E; border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: #444444; }

        /* Left Sidebar (210px, #161616) */
        aside {
            width: 210px;
            background-color: #161616;
            border-right: 1px solid #222222;
            padding: 20px 16px;
            display: flex;
            flex-direction: column;
            gap: 6px;
            flex-shrink: 0;
        }
        .prof-name { font-size: 17px; font-weight: bold; color: #FFFFFF; }
        .prof-sub { font-size: 11px; color: #555555; margin-bottom: 4px; }
        .divider { height: 1px; background-color: #2E2E2E; margin: 8px 0; }
        
        /* Sidebar Action Buttons */
        .btn-side-primary1 {
            background: linear-gradient(135deg, #1565C0, #1976D2);
            color: #FFFFFF; font-size: 13px; font-weight: bold;
            border-radius: 8px; padding: 11px 12px; border: none; cursor: pointer; text-align: center;
            box-shadow: 0 2px 6px rgba(21, 101, 192, 0.3); transition: all 0.15s ease;
        }
        .btn-side-primary1:hover { filter: brightness(1.15); transform: translateY(-1px); }

        .btn-side-primary2 {
            background: linear-gradient(135deg, #6A1B9A, #7B1FA2);
            color: #FFFFFF; font-size: 13px; font-weight: bold;
            border-radius: 8px; padding: 11px 12px; border: none; cursor: pointer; text-align: center;
            box-shadow: 0 2px 6px rgba(106, 27, 154, 0.3); transition: all 0.15s ease;
        }
        .btn-side-primary2:hover { filter: brightness(1.15); transform: translateY(-1px); }

        .btn-side-primary3 {
            background: linear-gradient(135deg, #1B5E20, #2E7D32);
            color: #FFFFFF; font-size: 13px; font-weight: bold;
            border-radius: 8px; padding: 11px 12px; border: none; cursor: pointer; text-align: center;
            box-shadow: 0 2px 6px rgba(27, 94, 32, 0.3); transition: all 0.15s ease;
        }
        .btn-side-primary3:hover { filter: brightness(1.15); transform: translateY(-1px); }

        .btn-side-sec {
            background-color: #252525; color: #BBBBBB; font-size: 12px; font-weight: 500;
            border-radius: 7px; padding: 9px 12px; border: 1px solid transparent; cursor: pointer; text-align: left;
            transition: all 0.15s ease; display: flex; align-items: center; gap: 8px;
        }
        .btn-side-sec:hover { background-color: #333333; color: #FFFFFF; border-color: #444; }
        
        .side-status { margin-top: auto; font-size: 11px; color: #555555; }
        .side-last-gen { font-size: 10px; color: #444444; margin-top: 2px; }

        /* Main Content Area */
        main {
            flex: 1;
            padding: 18px 22px;
            display: flex;
            flex-direction: column;
            gap: 16px;
            overflow-y: auto;
            background-color: #121212;
        }
        
        .main-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .main-title { font-size: 22px; font-weight: 800; color: #FFFFFF; letter-spacing: 0.3px; }
        .btn-refresh {
            background-color: #252525; color: #FFFFFF; font-size: 12px; font-weight: bold;
            border-radius: 6px; padding: 7px 16px; border: 1px solid #333; cursor: pointer;
            transition: all 0.15s;
        }
        .btn-refresh:hover { background-color: #333333; border-color: #555; }

        /* Stats Cards Row */
        .stats-row {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 12px;
        }
        .stat-card {
            background-color: #1C1C1E;
            border: 1px solid #2E2E2E;
            border-radius: 10px;
            padding: 14px 16px;
            display: flex;
            flex-direction: column;
            gap: 2px;
            transition: all 0.15s ease;
        }
        .stat-card.clickable { cursor: pointer; }
        .stat-card.clickable:hover { background-color: #242428; border-color: #3B82F6; transform: translateY(-1px); }
        .stat-t { font-size: 10px; font-weight: 800; color: #777777; text-transform: uppercase; letter-spacing: 0.5px; }
        .stat-v { font-size: 24px; font-weight: 800; color: #FFFFFF; margin: 2px 0; }
        .stat-s { font-size: 11px; color: #555555; }

        /* Workout Cards Grid */
        .sessions-row {
            display: flex;
            gap: 12px;
            overflow-x: auto;
            flex: 1;
            padding-bottom: 6px;
        }
        .workout-card {
            background-color: #1C1C1E;
            border: 1px solid #2E2E2E;
            border-radius: 10px;
            min-width: 260px;
            flex: 1;
            padding: 14px;
            display: flex;
            flex-direction: column;
            gap: 6px;
        }
        .workout-card.pr-card {
            background-color: #2A1A00;
            border-color: #5A3000;
        }
        .workout-card-hdr { font-size: 13px; font-weight: bold; color: #FFFFFF; }
        .workout-card.pr-card .workout-card-hdr { color: #B45309; }
        .card-sep { height: 1px; background-color: #2E2E2E; margin: 4px 0 6px 0; }
        .workout-card.pr-card .card-sep { background-color: #5A3000; }
        
        .ex-item { display: flex; justify-content: space-between; font-size: 12px; padding: 3px 0; }
        .ex-name { color: #DDDDDD; font-weight: 500; }
        .ex-meta { color: #888888; font-size: 11px; }

        /* Modal Windows */
        .modal-overlay {
            position: fixed; inset: 0; background: rgba(0, 0, 0, 0.75);
            backdrop-filter: blur(8px);
            display: none; align-items: center; justify-content: center; z-index: 1000;
            opacity: 0; transition: opacity 0.2s ease;
        }
        .modal-overlay.active { display: flex; opacity: 1; }
        .modal-window {
            background-color: #161618; border: 1px solid #2E2E32; border-radius: 12px;
            width: 1020px; max-height: 88vh; display: flex; flex-direction: column; overflow: hidden;
            box-shadow: 0 16px 40px rgba(0,0,0,0.85);
            animation: modalPop 0.2s cubic-bezier(0.16, 1, 0.3, 1);
        }
        @keyframes modalPop {
            0% { transform: scale(0.96) translateY(8px); opacity: 0; }
            100% { transform: scale(1) translateY(0); opacity: 1; }
        }

        .modal-hdr { background: #1E1E22; padding: 14px 20px; border-bottom: 1px solid #2A2A2E; }
        .modal-title { font-size: 16px; font-weight: 800; color: #FFFFFF; }
        .modal-sub { font-size: 12px; color: #888888; margin-top: 2px; }
        .modal-body { flex: 1; overflow-y: auto; padding: 16px 20px; display: flex; flex-direction: column; gap: 14px; }
        .modal-footer {
            background: #141416; padding: 12px 20px; border-top: 1px solid #222226;
            display: flex; gap: 12px; align-items: center;
        }

        /* ── Modern Cycler Day Box ───────────────────────────────────────── */
        .plan-day-card {
            background-color: #1A1A1E; border: 1px solid #2A2A30; border-radius: 10px;
            padding: 12px 14px; display: flex; flex-direction: column; gap: 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        }
        .plan-day-hdr {
            background-color: #222228; border-radius: 8px; padding: 8px 12px;
            display: flex; align-items: center; gap: 12px;
        }
        .day-pill {
            background: linear-gradient(135deg, #00695C, #00897B);
            color: white; font-weight: 800; font-size: 12px;
            border-radius: 5px; padding: 5px 12px; letter-spacing: 0.5px;
        }
        .date-label { font-size: 12px; font-weight: 600; color: #888888; }
        
        .plan-input {
            background-color: #222226; color: #FFFFFF; border: 1px solid #33333A;
            border-radius: 6px; padding: 6px 10px; font-size: 12px; font-weight: 500; outline: none;
            transition: all 0.15s;
        }
        .plan-input:focus { border-color: #3B82F6; background-color: #26262C; box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2); }
        .plan-input.center { text-align: center; }

        /* Grid layout for Plan Row Headers and Rows */
        .plan-row-grid {
            display: grid;
            grid-template-columns: 55px 1fr 60px 100px 110px 1fr 105px;
            gap: 8px;
            align-items: center;
        }
        .plan-col-head {
            font-size: 11px; font-weight: 700; color: #666666; text-transform: uppercase;
            letter-spacing: 0.5px; padding: 0 4px;
        }
        .plan-item-row {
            background-color: #16161A; border: 1px solid #24242A; border-radius: 6px;
            padding: 6px 8px; transition: background 0.15s;
        }
        .plan-item-row:hover { background-color: #1C1C22; border-color: #2E2E36; }

        /* Control Buttons */
        .order-btn-group { display: flex; gap: 2px; }
        .btn-arrow {
            background: #25252A; color: #AAA; border: 1px solid #33333C;
            border-radius: 4px; width: 24px; height: 26px; cursor: pointer; font-size: 10px;
            display: flex; align-items: center; justify-content: center; transition: all 0.15s;
        }
        .btn-arrow:hover { background: #3B82F6; color: #FFF; border-color: #3B82F6; }

        .btn-pill-inc {
            background: #1C2E24; color: #4ADE80; border: 1px solid #234E36;
            border-radius: 5px; padding: 4px 8px; font-size: 11px; font-weight: 700; cursor: pointer;
            transition: all 0.15s;
        }
        .btn-pill-inc:hover { background: #22C55E; color: #000; }

        .btn-trash {
            background: #331A1A; color: #F87171; border: 1px solid #552222;
            border-radius: 5px; width: 28px; height: 28px; cursor: pointer; font-size: 12px;
            display: flex; align-items: center; justify-content: center; transition: all 0.15s;
        }
        .btn-trash:hover { background: #EF4444; color: #FFF; }

        .btn-add-ex {
            background: linear-gradient(135deg, #0277BD, #0288D1);
            color: white; font-weight: 700; font-size: 12px; border: none;
            border-radius: 6px; padding: 6px 14px; cursor: pointer; transition: all 0.15s;
        }
        .btn-add-ex:hover { filter: brightness(1.15); }

        .btn-del-day {
            background: #3B1C1C; color: #FCA5A5; border: 1px solid #662222;
            border-radius: 6px; padding: 5px 10px; font-size: 12px; cursor: pointer;
        }
        .btn-del-day:hover { background: #DC2626; color: #FFF; }

        .btn-save-plan {
            background: linear-gradient(135deg, #1B5E20, #2E7D32);
            color: white; font-weight: 800; font-size: 13px; border: none;
            border-radius: 7px; padding: 10px 24px; cursor: pointer; margin-left: auto;
            box-shadow: 0 2px 8px rgba(27, 94, 32, 0.4); transition: all 0.15s;
        }
        .btn-save-plan:hover { filter: brightness(1.15); transform: translateY(-1px); }

        /* Tables for Standards & Split */
        table { width: 100%; border-collapse: collapse; font-size: 12px; }
        th { color: #777777; font-weight: bold; text-align: left; padding: 8px; border-bottom: 1px solid #2A2A2E; }
        td { padding: 8px; border-bottom: 1px solid #1E1E22; }
        tr:hover { background-color: #1A1A20; }
        
        .badge-slug { color: #38BDF8; font-family: monospace; font-size: 12px; }
        .btn-tool {
            background: #25252A; color: white; border: 1px solid #33333C;
            border-radius: 4px; padding: 4px 10px; font-size: 11px; font-weight: 600; cursor: pointer;
        }
        .btn-tool:hover { background: #3B82F6; border-color: #3B82F6; }
    </style>
</head>
<body>
    <!-- ── 1. LEFT SIDEBAR ─────────────────────────────────────────────── -->
    <aside>
        <div class="prof-name" id="sidebarProfName">Default User</div>
        <div class="prof-sub">Iron Log (PyWebView Edition)</div>
        <div class="divider"></div>

        <!-- Primary Action Buttons -->
        <button class="btn-side-primary1" onclick="generateExcel()">🚀 Generate Excel Log</button>
        <button class="btn-side-primary2" onclick="openPlanCycler()">🗓️ Plan Next Cycle</button>
        <button class="btn-side-primary3" onclick="pywebview.api.open_latest_excel()">📂 Open Latest Log</button>

        <div class="divider"></div>

        <!-- Secondary Action Buttons -->
        <button class="btn-side-sec" onclick="pywebview.api.edit_sessions()">📝  Edit Sessions</button>
        <button class="btn-side-sec" onclick="pywebview.api.open_output()">📊  Output Folder</button>
        <button class="btn-side-sec" onclick="openStandardsModal()">📚  Exercise Library</button>
        <button class="btn-side-sec" onclick="openSplitModal()">🔄  Split Details</button>

        <div class="side-status" id="sidebarStatus">Ready</div>
        <div class="side-last-gen" id="sidebarLastGen"></div>
    </aside>

    <!-- ── 2. MAIN CONTENT AREA ────────────────────────────────────────── -->
    <main>
        <div class="main-header">
            <div class="main-title">Recent Sessions</div>
            <button class="btn-refresh" onclick="loadDashboard()">↻  Refresh</button>
        </div>

        <!-- 3 Stats Metric Cards -->
        <div class="stats-row">
            <div class="stat-card">
                <div class="stat-t">GYM ATTENDANCE</div>
                <div class="stat-v" id="c1Val">-- Days</div>
                <div class="stat-s" id="c1Sub">-- this year · -- this month</div>
            </div>
            <div class="stat-card clickable" onclick="openSplitModal()">
                <div class="stat-t">CURRENT SPLIT DURATION</div>
                <div class="stat-v" id="c2Val">-- Weeks</div>
                <div class="stat-s" id="c2Sub">N-Day Split · started --</div>
            </div>
            <div class="stat-card">
                <div class="stat-t">LAST WORKOUT</div>
                <div class="stat-v" id="c3Val">--</div>
                <div class="stat-s" id="c3Sub">Day --</div>
            </div>
        </div>

        <!-- Recent Sessions Horizontal Cards -->
        <div class="sessions-row" id="sessionsGrid">
            <div style="color: #777777;">Loading workout sessions...</div>
        </div>
    </main>

    <!-- ── 3. DYNAMIC PLAN CYCLER MODAL ────────────────────────────────── -->
    <div id="modalCycler" class="modal-overlay">
        <div class="modal-window">
            <div class="modal-hdr">
                <div class="modal-title" id="cyclerTitle">Plan Next Cycle</div>
                <div class="modal-sub">Define your training split. Type exercise variable name, sets, reps, mass, and notes.</div>
            </div>
            <div class="modal-body" id="cyclerDaysContainer"></div>
            <div class="modal-footer">
                <button class="btn-side-sec" style="padding: 8px 16px; font-weight: bold;" onclick="closeModal('modalCycler')">Cancel</button>
                <button class="btn-side-primary2" style="padding: 8px 16px;" onclick="addPlanDay()">+ Add Day</button>
                <button class="btn-side-sec" style="padding: 8px 14px;" onclick="applyDeload()">🧪 Deload Next Cycle (-10%)</button>
                <button class="btn-save-plan" onclick="saveCyclerPlan()">✅ Write to sessions.py</button>
            </div>
        </div>
    </div>

    <!-- ── 4. STRENGTH STANDARDS MODAL ─────────────────────────────────── -->
    <div id="modalStandards" class="modal-overlay">
        <div class="modal-window" style="width: 860px;">
            <div class="modal-hdr">
                <div class="modal-title">Strength Standards Library</div>
                <div style="margin-top: 10px; display: flex; gap: 8px;">
                    <input type="text" id="stdSearchInput" class="plan-input" placeholder="Filter exercises by name or slug..." style="flex: 1;" oninput="filterStandards(this.value)">
                </div>
            </div>
            <div class="modal-body">
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
                <button class="btn-side-sec" style="padding: 8px 18px; margin-left: auto;" onclick="closeModal('modalStandards')">Close</button>
            </div>
        </div>
    </div>

    <!-- ── 5. SPLIT DETAILS MODAL ──────────────────────────────────────── -->
    <div id="modalSplit" class="modal-overlay">
        <div class="modal-window" style="width: 620px;">
            <div class="modal-hdr">
                <div class="modal-title">Current Split Details & History</div>
            </div>
            <div class="modal-body">
                <div class="stat-card">
                    <div class="stat-t">CURRENT SPLIT ROUTINE</div>
                    <div id="splitOverview" style="font-size: 13px; margin-top: 4px; line-height: 1.6;"></div>
                </div>
                <div style="font-weight: bold; font-size: 13px; margin-top: 6px; color: #AAA;">Recent Split Sessions History:</div>
                <table>
                    <thead>
                        <tr><th>Date</th><th>Day</th><th>Exercises Count</th></tr>
                    </thead>
                    <tbody id="splitTbody"></tbody>
                </table>
            </div>
            <div class="modal-footer">
                <button class="btn-side-sec" style="padding: 8px 18px; margin-left: auto;" onclick="closeModal('modalSplit')">Close</button>
            </div>
        </div>
    </div>

    <script>
        let currentPlan = [];
        let cachedStats = {};

        function closeModal(id) {
            document.getElementById(id).classList.remove("active");
        }

        async function init() {
            await loadDashboard();
        }

        async function loadDashboard() {
            document.getElementById("sidebarStatus").innerText = "Loading...";
            const data = await pywebview.api.get_active_data();
            if (!data.success) {
                document.getElementById("sidebarStatus").innerText = data.error;
                return;
            }
            document.getElementById("sidebarProfName").innerText = data.profile_name;
            const s = data.stats;
            cachedStats = s;

            // Stats Cards
            document.getElementById("c1Val").innerText = (s.total_days || 0) + " Days";
            document.getElementById("c1Sub").innerText = (s.this_year_days || 0) + " this year · " + (s.this_month_days || 0) + " this month";

            document.getElementById("c2Val").innerText = (s.current_split_weeks || 0).toFixed(1) + " Weeks";
            document.getElementById("c2Sub").innerText = (s.cycle_length || "N/A") + "-Day Split · started " + (s.current_split_start || "N/A");

            document.getElementById("c3Val").innerText = s.latest_workout_date || "N/A";
            document.getElementById("c3Sub").innerText = "Day " + (s.latest_workout_day || "N/A");

            // Workout Cards
            const grid = document.getElementById("sessionsGrid");
            grid.innerHTML = "";
            (data.sessions || []).forEach(sess => {
                const isPR = typeof sess.day === 'string' && sess.day.toUpperCase() === 'PR';
                const card = document.createElement("div");
                card.className = "workout-card" + (isPR ? " pr-card" : "");
                
                let exsHtml = "";
                sess.exercises.forEach(ex => {
                    exsHtml += `
                        <div class="ex-item">
                            <span class="ex-name">${ex.name}</span>
                            <span class="ex-meta">${ex.reps} @ ${ex.mass}</span>
                        </div>
                    `;
                });
                
                const hdrStr = typeof sess.day === 'number' ? `📅  ${sess.date}  ·  Day ${sess.day}` : `📅  ${sess.date}  ·  ${sess.day}`;
                card.innerHTML = `
                    <div class="workout-card-hdr">${hdrStr}</div>
                    <div class="card-sep"></div>
                    <div style="display: flex; flex-direction: column; gap: 3px;">${exsHtml}</div>
                `;
                grid.appendChild(card);
            });

            document.getElementById("sidebarStatus").innerText = "Ready (" + data.profile_name + ")";
        }

        async function generateExcel() {
            document.getElementById("sidebarStatus").innerText = "Generating Excel Log...";
            const res = await pywebview.api.generate_excel();
            if (res.success) {
                document.getElementById("sidebarStatus").innerText = "✅ Created Excel log!";
                document.getElementById("sidebarLastGen").innerText = "Last gen: " + res.time;
            } else {
                alert("Excel Generation Error:\\n" + res.error);
                document.getElementById("sidebarStatus").innerText = "Error";
            }
        }

        async function openPlanCycler() {
            const res = await pywebview.api.get_plan();
            if (!res.success) {
                alert(res.error);
                return;
            }
            currentPlan = res.planned;
            document.getElementById("cyclerTitle").innerText = "Plan Next Cycle (" + res.why + ")";
            renderCycler();
            document.getElementById("modalCycler").classList.add("active");
        }

        function renderCycler() {
            const c = document.getElementById("cyclerDaysContainer");
            c.innerHTML = "";
            currentPlan.forEach((day, dIdx) => {
                const card = document.createElement("div");
                card.className = "plan-day-card";
                
                let rowsHtml = "";
                day.exercises.forEach((ex, eIdx) => {
                    rowsHtml += `
                        <div class="plan-item-row plan-row-grid">
                            <div class="order-btn-group">
                                <button class="btn-arrow" onclick="moveEx(${dIdx}, ${eIdx}, -1)">▲</button>
                                <button class="btn-arrow" onclick="moveEx(${dIdx}, ${eIdx}, 1)">▼</button>
                            </div>
                            <div>
                                <input type="text" class="plan-input" value="${ex.var_name}" onchange="currentPlan[${dIdx}].exercises[${eIdx}].var_name = this.value" placeholder="exercise_slug" style="width: 100%;">
                            </div>
                            <div>
                                <input type="text" class="plan-input center" value="${ex.sets}" onchange="currentPlan[${dIdx}].exercises[${eIdx}].sets = this.value" style="width: 100%;">
                            </div>
                            <div>
                                <input type="text" class="plan-input center" value="${ex.reps}" onchange="currentPlan[${dIdx}].exercises[${eIdx}].reps = this.value" placeholder="e.g. 6,6,6" style="width: 100%;">
                            </div>
                            <div>
                                <input type="text" class="plan-input center" value="${ex.mass}" onchange="currentPlan[${dIdx}].exercises[${eIdx}].mass = this.value" placeholder="kg" style="width: 100%;">
                            </div>
                            <div>
                                <input type="text" class="plan-input" value="${ex.comment || ''}" onchange="currentPlan[${dIdx}].exercises[${eIdx}].comment = this.value" placeholder="Comment / notes" style="width: 100%;">
                            </div>
                            <div style="display: flex; gap: 4px; align-items: center;">
                                <button class="btn-pill-inc" onclick="addMass(${dIdx}, ${eIdx}, 2.5)">+2.5</button>
                                <button class="btn-trash" onclick="removeEx(${dIdx}, ${eIdx})">✕</button>
                            </div>
                        </div>
                    `;
                });

                card.innerHTML = `
                    <div class="plan-day-hdr">
                        <div class="day-pill">Day ${day.day_num}</div>
                        <span class="date-label">Date:</span>
                        <input type="text" class="plan-input" value="${day.date_str}" onchange="currentPlan[${dIdx}].date_str = this.value" placeholder="YYYY-MM-DD" style="width: 120px;">
                        <button class="btn-add-ex" style="margin-left: auto;" onclick="addEx(${dIdx})">+ Add Exercise</button>
                        <button class="btn-del-day" onclick="removeDay(${dIdx})">🗑️ Delete Day</button>
                    </div>

                    <div class="plan-row-grid" style="padding: 0 8px;">
                        <div class="plan-col-head">Order</div>
                        <div class="plan-col-head">Exercise Name / Slug</div>
                        <div class="plan-col-head" style="text-align: center;">Sets</div>
                        <div class="plan-col-head" style="text-align: center;">Reps</div>
                        <div class="plan-col-head" style="text-align: center;">Mass (kg)</div>
                        <div class="plan-col-head">Comment</div>
                        <div class="plan-col-head">Actions</div>
                    </div>

                    <div style="display: flex; flex-direction: column; gap: 6px;">
                        ${rowsHtml}
                    </div>
                `;
                c.appendChild(card);
            });
        }

        function moveEx(d, e, dir) {
            const arr = currentPlan[d].exercises;
            const target = e + dir;
            if (target >= 0 && target < arr.length) {
                const tmp = arr[e];
                arr[e] = arr[target];
                arr[target] = tmp;
                renderCycler();
            }
        }

        function addEx(d) {
            currentPlan[d].exercises.push({ var_name: "exercise", sets: 3, reps: "5", mass: "0", comment: "" });
            renderCycler();
        }

        function removeEx(d, e) {
            currentPlan[d].exercises.splice(e, 1);
            renderCycler();
        }

        function addDay() {
            currentPlan.push({ day_num: currentPlan.length + 1, date_str: "", exercises: [] });
            renderCycler();
        }

        function removeDay(d) {
            currentPlan.splice(d, 1);
            currentPlan.forEach((x, i) => x.day_num = i + 1);
            renderCycler();
        }

        function addMass(d, e, delta) {
            const m = parseFloat(currentPlan[d].exercises[e].mass) || 0;
            currentPlan[d].exercises[e].mass = (m + delta).toString();
            renderCycler();
        }

        function applyDeload() {
            currentPlan.forEach(d => {
                d.exercises.forEach(e => {
                    const m = parseFloat(e.mass);
                    if (!isNaN(m)) {
                        e.mass = (Math.round(m * 0.9 * 2) / 2).toString();
                        e.comment = "Deload -10%";
                    }
                });
            });
            renderCycler();
        }

        async function saveCyclerPlan() {
            const res = await pywebview.api.save_plan(currentPlan);
            if (res.success) {
                closeModal('modalCycler');
                await loadDashboard();
            } else {
                alert("Error saving plan: " + res.error);
            }
        }

        async function openStandardsModal() {
            await filterStandards("");
            document.getElementById("modalStandards").classList.add("active");
        }

        async function filterStandards(q) {
            const list = await pywebview.api.search_standards(q);
            const tbody = document.getElementById("stdTbody");
            tbody.innerHTML = "";
            list.forEach(row => {
                const tr = document.createElement("tr");
                const py = `${row.slug.replace(/-/g, '_')} = "${row.slug}"`;
                tr.innerHTML = `
                    <td style="font-weight: 600;">${row.name}</td>
                    <td><span class="badge-slug">${row.slug}</span></td>
                    <td style="text-align: center;">${row.beg}</td>
                    <td style="text-align: center;">${row.nov}</td>
                    <td style="text-align: center;">${row.int}</td>
                    <td style="text-align: center;">${row.adv}</td>
                    <td style="text-align: center;">${row.eli}</td>
                    <td style="display: flex; gap: 4px;">
                        <button class="btn-tool" onclick="pywebview.api.copy_clipboard('${row.slug}')">Copy</button>
                        <button class="btn-tool" style="background: #1B5E20; border-color: #2E7D32;" onclick="pywebview.api.copy_clipboard('${py}')">Copy Py</button>
                        <button class="btn-tool" style="background: #1565C0; border-color: #1976D2;" onclick="pywebview.api.open_url('https://strengthlevel.com/strength-standards/${row.slug}')">View</button>
                    </td>
                `;
                tbody.appendChild(tr);
            });
        }

        function openSplitModal() {
            const s = cachedStats;
            document.getElementById("splitOverview").innerHTML = `
                • Active Split Duration: <b>${(s.current_split_weeks || 0).toFixed(1)} Weeks</b> (Started ${s.current_split_start || "N/A"})<br>
                • Detected Cycle Length: <b>${s.cycle_length || "N/A"} Days</b><br>
                • Total Recorded Sessions: <b>${s.total_days || 0}</b>
            `;
            const tb = document.getElementById("splitTbody");
            tb.innerHTML = "";
            (s.split_sessions_details || []).slice().reverse().forEach(row => {
                const tr = document.createElement("tr");
                tr.innerHTML = `<td>${row.date_str}</td><td>Day ${row.day}</td><td>${row.exercises ? row.exercises.length : 0}</td>`;
                tb.appendChild(tr);
            });
            document.getElementById("modalSplit").classList.add("active");
        }

        window.addEventListener('pywebviewready', init);
    </script>
</body>
</html>
"""


class WebViewBridgeApi:
    """Python backend bridge API matching the CustomTkinter engine features."""

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

    def get_active_data(self) -> Dict[str, Any]:
        p = self.manager.get_active_profile()
        if not p:
            return {"success": False, "error": "No profile selected"}

        sess, file_path = self._load_sessions(p)
        if not sess:
            return {"success": False, "error": f"sessions.py not found at {file_path}"}

        user_data = getattr(sess, "USER_DATA", {})
        stats = calculate_gym_stats(user_data)

        date_pat = re.compile(r"^\d{4}-\d{2}-\d{2}$")
        sorted_dates = sorted([d for d in user_data.keys() if date_pat.match(d)], reverse=True)
        N, _ = detect_cycle(user_data)
        show_dates = sorted_dates[: N if N else 3]

        recent_sessions = []
        for d_str in reversed(show_dates):
            day_data = user_data[d_str]
            exs = []
            for ex_id, log in day_data.items():
                if not isinstance(log, Log):
                    continue
                info = EXERCISE_STANDARDS.get(ex_id, {})
                reps_str = "-".join(str(r) for r in log.reps) if len(set(log.reps)) > 1 else f"{len(log.reps)} × {log.reps[0]}"
                mass_str = f"{log.mass[0]}kg" if log.mass and max(log.mass) > 0 else "BW"
                exs.append({
                    "name": info.get("name", ex_id),
                    "reps": reps_str,
                    "mass": mass_str,
                })
            recent_sessions.append({
                "date": d_str,
                "day": day_data.get("day", "?"),
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

            # Novel exercise confirmation
            new_exs = get_genuinely_new_exercises(sessions_file, planned_objs)
            write_planned_sessions(sessions_file, planned_objs)
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


def run_webview_app():
    api = WebViewBridgeApi()
    window = webview.create_window(
        title=f"Iron Log {__version__} (PyWebView Edition)",
        html=HTML_TEMPLATE,
        js_api=api,
        width=1100,
        height=720,
        min_size=(960, 580),
        background_color="#121212",
    )
    webview.start(debug=False)


if __name__ == "__main__":
    run_webview_app()
