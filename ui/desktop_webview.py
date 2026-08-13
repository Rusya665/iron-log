"""PyWebView (Microsoft Edge WebView2) Desktop GUI for Iron Log.

Provides modern web styling (Tailwind CSS, Glassmorphism, smooth animations)
with zero Electron overhead by utilizing the OS native Edge WebView2 runtime.
"""

import json
import os
import re
import sys
import threading
import webbrowser
from datetime import datetime
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
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        body { background-color: #121214; color: #F4F4F5; height: 100vh; display: flex; flex-direction: column; overflow: hidden; }
        
        /* Header */
        header { background-color: #18181B; border-bottom: 1px solid #27272A; padding: 10px 18px; display: flex; align-items: center; justify-content: space-between; }
        .brand { font-size: 16px; font-weight: 800; color: #38BDF8; letter-spacing: 1px; display: flex; align-items: center; gap: 8px; }
        .version { font-size: 12px; color: #71717A; font-weight: normal; }
        .engine-badge { background: #064E3B; border: 1px solid #15803D; color: #4ADE80; font-size: 11px; font-weight: 600; padding: 3px 8px; border-radius: 4px; }
        
        .profile-bar { display: flex; align-items: center; gap: 8px; font-size: 13px; }
        select, input { background: #27272A; border: 1px solid #3F3F46; color: #F4F4F5; padding: 5px 10px; border-radius: 6px; font-size: 13px; outline: none; }
        select:focus, input:focus { border-color: #3B82F6; }
        
        /* Tabs */
        .tabs { display: flex; gap: 4px; padding: 10px 18px 0 18px; background: #121214; border-bottom: 1px solid #27272A; }
        .tab-btn { background: transparent; border: none; color: #A1A1AA; padding: 8px 16px; font-weight: 600; font-size: 13px; cursor: pointer; border-bottom: 2px solid transparent; }
        .tab-btn:hover { color: #FFFFFF; }
        .tab-btn.active { color: #38BDF8; border-bottom-color: #38BDF8; }
        
        /* Main Views */
        main { flex: 1; padding: 16px 18px; overflow-y: auto; display: flex; flex-direction: column; gap: 14px; }
        .view-tab { display: none; flex-direction: column; gap: 14px; flex: 1; }
        .view-tab.active { display: flex; }
        
        /* Cards */
        .stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
        .stat-card { background: #18181B; border: 1px solid #27272A; border-radius: 8px; padding: 12px 14px; display: flex; flex-direction: column; gap: 4px; }
        .stat-title { font-size: 11px; font-weight: 600; color: #A1A1AA; text-transform: uppercase; }
        .stat-val { font-size: 20px; font-weight: bold; color: #38BDF8; }
        .stat-sub { font-size: 11px; color: #71717A; }
        
        /* Action Buttons */
        .actions-bar { display: flex; gap: 8px; align-items: center; }
        .btn { background: #27272A; border: 1px solid #3F3F46; color: #F4F4F5; padding: 7px 14px; border-radius: 6px; font-weight: 600; font-size: 12px; cursor: pointer; display: inline-flex; align-items: center; gap: 6px; transition: all 0.15s; }
        .btn:hover { background: #3F3F46; border-color: #52525B; }
        .btn-primary { background: #2563EB; border-color: #3B82F6; color: #FFFFFF; }
        .btn-primary:hover { background: #1D4ED8; }
        .btn-success { background: #15803D; border-color: #22C55E; color: #FFFFFF; }
        .btn-success:hover { background: #166534; }
        .btn-danger { background: #991B1B; border-color: #EF4444; color: #FFFFFF; }
        .btn-sm { padding: 3px 8px; font-size: 11px; }
        
        /* Sessions Container */
        .sessions-row { display: flex; gap: 12px; overflow-x: auto; padding-bottom: 8px; }
        .session-card { background: #18181B; border: 1px solid #27272A; border-radius: 8px; min-width: 250px; flex: 1; padding: 12px; display: flex; flex-direction: column; gap: 8px; }
        .session-hdr { font-size: 13px; font-weight: bold; color: #38BDF8; border-bottom: 1px solid #27272A; padding-bottom: 6px; }
        .session-ex { display: flex; flex-direction: column; font-size: 12px; gap: 2px; }
        .session-ex-name { font-weight: 600; color: #E4E4E7; }
        .session-ex-meta { color: #A1A1AA; font-size: 11px; }
        
        /* Tables */
        table { width: 100%; border-collapse: collapse; background: #18181B; border-radius: 8px; overflow: hidden; border: 1px solid #27272A; font-size: 12px; }
        th, td { padding: 8px 10px; text-align: left; border-bottom: 1px solid #27272A; }
        th { background: #27272A; color: #E4E4E7; font-weight: 600; }
        tr:hover { background: #202024; }
        
        /* Toast Notification */
        #toast { position: fixed; bottom: 35px; right: 20px; background: #10B981; color: white; padding: 8px 16px; border-radius: 6px; font-weight: 600; font-size: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.5); opacity: 0; transition: opacity 0.3s; pointer-events: none; z-index: 100; }
        
        /* Footer */
        footer { background: #18181B; border-top: 1px solid #27272A; padding: 6px 18px; font-size: 11px; color: #A1A1AA; display: flex; justify-content: space-between; }
    </style>
</head>
<body>
    <header>
        <div class="brand">
            <span>⚡ IRON LOG</span>
            <span class="version" id="appVersion">v1.3.1</span>
        </div>
        <div class="profile-bar">
            <span>Profile:</span>
            <select id="profileSelect" onchange="onProfileChange(this.value)"></select>
            <button class="btn btn-sm" onclick="promptNewProfile()">+ New</button>
        </div>
        <div class="engine-badge">Engine: PyWebView (Edge WebView2)</div>
    </header>

    <div class="tabs">
        <button class="tab-btn active" onclick="switchTab('dashboard', this)">Dashboard</button>
        <button class="tab-btn" onclick="switchTab('planner', this)">Cycle Planner</button>
        <button class="tab-btn" onclick="switchTab('standards', this)">Strength Standards</button>
        <button class="tab-btn" onclick="switchTab('split', this)">Split Details</button>
    </div>

    <main>
        <!-- Tab 1: Dashboard -->
        <div id="tab-dashboard" class="view-tab active">
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-title">Total Sessions</div>
                    <div class="stat-val" id="statTotal">--</div>
                    <div class="stat-sub" id="statTotalSub">-- this year</div>
                </div>
                <div class="stat-card">
                    <div class="stat-title">Last Workout</div>
                    <div class="stat-val" id="statLast">--</div>
                    <div class="stat-sub" id="statLastSub">Latest date</div>
                </div>
                <div class="stat-card" style="cursor: pointer;" onclick="switchTab('split', document.querySelectorAll('.tab-btn')[3])">
                    <div class="stat-title">Active Split</div>
                    <div class="stat-val" id="statSplit">--</div>
                    <div class="stat-sub">Click for details</div>
                </div>
                <div class="stat-card">
                    <div class="stat-title">Body Mass</div>
                    <div class="stat-val" id="statMass">-- kg</div>
                    <div class="stat-sub">From log</div>
                </div>
            </div>

            <div class="actions-bar">
                <button class="btn btn-primary" onclick="generateExcel()">📊 Generate Excel Log</button>
                <button class="btn" onclick="switchTab('planner', document.querySelectorAll('.tab-btn')[1])">📅 Cycle Planner</button>
                <button class="btn" onclick="switchTab('standards', document.querySelectorAll('.tab-btn')[2])">🏋️ Standards Browser</button>
                <button class="btn" onclick="pywebview.api.edit_sessions()">Edit sessions.py</button>
                <button class="btn" onclick="pywebview.api.open_output()">Output Folder</button>
            </div>

            <div style="font-size: 13px; font-weight: bold; color: #A1A1AA;">Recent Workout Sessions (Active Cycle)</div>
            <div class="sessions-row" id="sessionsContainer">
                <div style="color: #71717A;">Loading workout sessions...</div>
            </div>
        </div>

        <!-- Tab 2: Cycle Planner -->
        <div id="tab-planner" class="view-tab">
            <div class="actions-bar">
                <button class="btn" onclick="applyDeload()">Deload (-10%)</button>
                <button class="btn" onclick="addPlanDay()">+ Add Day</button>
                <button class="btn btn-success" style="margin-left: auto;" onclick="savePlan()">💾 Save Plan to sessions.py</button>
            </div>
            <div id="plannerDays" style="display: flex; flex-direction: column; gap: 12px; overflow-y: auto;">
                <div>Loading planner...</div>
            </div>
        </div>

        <!-- Tab 3: Strength Standards -->
        <div id="tab-standards" class="view-tab">
            <div style="display: flex; gap: 10px; align-items: center;">
                <span style="font-weight: 600; font-size: 13px;">Search:</span>
                <input type="text" id="stdSearch" placeholder="Type exercise name or slug (e.g. bench press)..." style="flex: 1;" oninput="onStandardsSearch(this.value)">
            </div>
            <div style="overflow-y: auto; flex: 1;">
                <table>
                    <thead>
                        <tr>
                            <th>Exercise Name</th>
                            <th>Slug</th>
                            <th>Beg</th>
                            <th>Nov</th>
                            <th>Int</th>
                            <th>Adv</th>
                            <th>Eli</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody id="standardsTbody"></tbody>
                </table>
            </div>
        </div>

        <!-- Tab 4: Split Details -->
        <div id="tab-split" class="view-tab">
            <div class="stat-card" style="margin-bottom: 10px;">
                <div class="stat-title" style="color: #38BDF8; font-size: 13px;">Routine Overview</div>
                <div id="splitOverviewText" style="font-size: 13px; margin-top: 6px; line-height: 1.6;"></div>
            </div>
            <div style="font-weight: bold; font-size: 13px; margin-bottom: 6px;">Split Sessions History</div>
            <div style="overflow-y: auto; flex: 1;">
                <table>
                    <thead>
                        <tr>
                            <th>Date</th>
                            <th>Day</th>
                            <th>Exercises Count</th>
                        </tr>
                    </thead>
                    <tbody id="splitHistoryTbody"></tbody>
                </table>
            </div>
        </div>
    </main>

    <div id="toast">Copied to clipboard!</div>

    <footer>
        <span id="statusTxt">Ready</span>
        <span>HTML5 + CSS + Edge WebView2 Engine</span>
    </footer>

    <script>
        let currentPlan = [];
        let allStandards = [];

        function showToast(msg) {
            const t = document.getElementById("toast");
            t.innerText = msg;
            t.style.opacity = "1";
            setTimeout(() => { t.style.opacity = "0"; }, 2500);
        }

        function setStatus(msg) {
            document.getElementById("statusTxt").innerText = msg;
        }

        function switchTab(tabId, btn) {
            document.querySelectorAll(".view-tab").forEach(el => el.classList.remove("active"));
            document.querySelectorAll(".tab-btn").forEach(el => el.classList.remove("active"));
            document.getElementById("tab-" + tabId).classList.add("active");
            if (btn) btn.classList.add("active");
            if (tabId === "planner") loadPlanner();
            if (tabId === "standards" && allStandards.length === 0) onStandardsSearch("");
        }

        async function initApp() {
            try {
                const profilesData = await pywebview.api.get_profiles();
                const sel = document.getElementById("profileSelect");
                sel.innerHTML = "";
                profilesData.profiles.forEach((p, idx) => {
                    const opt = document.createElement("option");
                    opt.value = idx;
                    opt.text = p.name;
                    if (idx === profilesData.active_index) opt.selected = true;
                    sel.appendChild(opt);
                });
                await loadDashboardData();
            } catch(e) {
                setStatus("Init error: " + e);
            }
        }

        async function onProfileChange(idx) {
            await pywebview.api.select_profile(parseInt(idx));
            await loadDashboardData();
        }

        async function promptNewProfile() {
            const name = prompt("Enter new profile name:");
            if (name && name.trim()) {
                await pywebview.api.create_profile(name.trim());
                await initApp();
            }
        }

        async function loadDashboardData() {
            setStatus("Loading data...");
            const data = await pywebview.api.get_active_data();
            if (!data.success) {
                setStatus(data.error);
                return;
            }
            const s = data.stats;
            document.getElementById("statTotal").innerText = s.total_days || "--";
            document.getElementById("statTotalSub").innerText = (s.this_year_days || 0) + " this year";
            document.getElementById("statLast").innerText = s.latest_workout_date || "--";
            document.getElementById("statLastSub").innerText = "Day " + (s.latest_workout_day || "");
            document.getElementById("statSplit").innerText = (s.current_split_weeks || 0).toFixed(1) + " Wks";
            document.getElementById("statMass").innerText = (data.current_mass || "--") + " kg";

            // Render Recent Sessions
            const sc = document.getElementById("sessionsContainer");
            sc.innerHTML = "";
            if (!data.sessions || data.sessions.length === 0) {
                sc.innerHTML = "<div style='color: #71717A;'>No sessions found.</div>";
            } else {
                data.sessions.forEach(sess => {
                    const card = document.createElement("div");
                    card.className = "session-card";
                    let exHtml = "";
                    sess.exercises.forEach(ex => {
                        exHtml += `
                            <div class="session-ex">
                                <span class="session-ex-name">• ${ex.name}</span>
                                <span class="session-ex-meta">[${ex.reps}] @ ${ex.mass}</span>
                            </div>
                        `;
                    });
                    card.innerHTML = `
                        <div class="session-hdr">📅 ${sess.date} (Day ${sess.day})</div>
                        <div style="display: flex; flex-direction: column; gap: 8px;">${exHtml}</div>
                    `;
                    sc.appendChild(card);
                });
            }

            // Split Overview Tab
            document.getElementById("splitOverviewText").innerHTML = `
                • Active Split Duration: <b>${(s.current_split_weeks || 0).toFixed(1)} Weeks</b> (Started ${s.current_split_start || "N/A"})<br>
                • Detected Cycle Length: <b>${s.cycle_length || "N/A"} Days</b><br>
                • Total Recorded Sessions: <b>${s.total_days || 0}</b>
            `;
            const splitTbody = document.getElementById("splitHistoryTbody");
            splitTbody.innerHTML = "";
            (s.split_sessions_details || []).slice().reverse().forEach(row => {
                const tr = document.createElement("tr");
                tr.innerHTML = `<td>${row.date_str}</td><td>Day ${row.day}</td><td>${row.exercises ? row.exercises.length : 0}</td>`;
                splitTbody.appendChild(tr);
            });

            setStatus("Ready — Profile: " + data.profile_name);
        }

        async function generateExcel() {
            setStatus("Generating Excel report in background...");
            showToast("Generating Excel file...");
            const res = await pywebview.api.generate_excel();
            if (res.success) {
                setStatus("✅ Created Excel log: " + res.filename);
                showToast("Excel Log generated successfully!");
            } else {
                setStatus("Error: " + res.error);
                alert("Excel Generation Error:\\n" + res.error);
            }
        }

        async function loadPlanner() {
            const res = await pywebview.api.get_plan();
            if (!res.success) {
                document.getElementById("plannerDays").innerHTML = `<div style="color: #EF4444;">${res.error}</div>`;
                return;
            }
            currentPlan = res.planned;
            renderPlanner();
        }

        function renderPlanner() {
            const container = document.getElementById("plannerDays");
            container.innerHTML = "";
            currentPlan.forEach((day, dIdx) => {
                const dayBox = document.createElement("div");
                dayBox.className = "stat-card";
                let rowsHtml = "";
                day.exercises.forEach((ex, eIdx) => {
                    rowsHtml += `
                        <tr style="border-bottom: 1px solid #27272A;">
                            <td>
                                <button class="btn btn-sm" onclick="movePlanEx(${dIdx}, ${eIdx}, -1)">▲</button>
                                <button class="btn btn-sm" onclick="movePlanEx(${dIdx}, ${eIdx}, 1)">▼</button>
                            </td>
                            <td><input type="text" value="${ex.var_name}" onchange="currentPlan[${dIdx}].exercises[${eIdx}].var_name = this.value" style="width: 100%;"></td>
                            <td><input type="text" value="${ex.sets}" onchange="currentPlan[${dIdx}].exercises[${eIdx}].sets = this.value" style="width: 50px;"></td>
                            <td><input type="text" value="${ex.reps}" onchange="currentPlan[${dIdx}].exercises[${eIdx}].reps = this.value" style="width: 80px;"></td>
                            <td><input type="text" value="${ex.mass}" onchange="currentPlan[${dIdx}].exercises[${eIdx}].mass = this.value" style="width: 80px;"></td>
                            <td><input type="text" value="${ex.comment || ''}" onchange="currentPlan[${dIdx}].exercises[${eIdx}].comment = this.value" style="width: 120px;"></td>
                            <td><button class="btn btn-sm btn-danger" onclick="removePlanEx(${dIdx}, ${eIdx})">✕</button></td>
                        </tr>
                    `;
                });

                dayBox.innerHTML = `
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <span style="font-weight: bold; color: #38BDF8;">Day ${day.day_num}</span>
                        <input type="text" value="${day.date_str}" onchange="currentPlan[${dIdx}].date_str = this.value" placeholder="YYYY-MM-DD" style="width: 120px;">
                        <button class="btn btn-sm" onclick="addPlanEx(${dIdx})">+ Add Exercise</button>
                        <button class="btn btn-sm btn-danger" onclick="removePlanDay(${dIdx})">Delete Day</button>
                    </div>
                    <table>
                        <thead>
                            <tr>
                                <th style="width: 60px;">Order</th>
                                <th>Exercise Variable</th>
                                <th style="width: 60px;">Sets</th>
                                <th style="width: 90px;">Reps</th>
                                <th style="width: 90px;">Mass</th>
                                <th>Comment</th>
                                <th style="width: 40px;">Del</th>
                            </tr>
                        </thead>
                        <tbody>${rowsHtml}</tbody>
                    </table>
                `;
                container.appendChild(dayBox);
            });
        }

        function movePlanEx(dIdx, eIdx, dir) {
            const arr = currentPlan[dIdx].exercises;
            const target = eIdx + dir;
            if (target >= 0 && target < arr.length) {
                const temp = arr[eIdx];
                arr[eIdx] = arr[target];
                arr[target] = temp;
                renderPlanner();
            }
        }

        function addPlanEx(dIdx) {
            currentPlan[dIdx].exercises.push({ var_name: "exercise", sets: 3, reps: "5", mass: "0", comment: "" });
            renderPlanner();
        }

        function removePlanEx(dIdx, eIdx) {
            currentPlan[dIdx].exercises.splice(eIdx, 1);
            renderPlanner();
        }

        function addPlanDay() {
            currentPlan.push({ day_num: currentPlan.length + 1, date_str: "", exercises: [] });
            renderPlanner();
        }

        function removePlanDay(dIdx) {
            currentPlan.splice(dIdx, 1);
            currentPlan.forEach((d, i) => d.day_num = i + 1);
            renderPlanner();
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
            renderPlanner();
            showToast("Applied 10% deload to planned exercises!");
        }

        async function savePlan() {
            const res = await pywebview.api.save_plan(currentPlan);
            if (res.success) {
                showToast("Plan successfully saved to sessions.py!");
                setStatus("✅ Plan saved!");
                switchTab('dashboard', document.querySelectorAll('.tab-btn')[0]);
                await loadDashboardData();
            } else {
                alert("Error saving plan: " + res.error);
            }
        }

        async function onStandardsSearch(q) {
            const data = await pywebview.api.search_standards(q);
            const tbody = document.getElementById("standardsTbody");
            tbody.innerHTML = "";
            data.forEach(row => {
                const tr = document.createElement("tr");
                const pyCode = `${row.slug.replace(/-/g, '_')} = "${row.slug}"`;
                tr.innerHTML = `
                    <td>${row.name}</td>
                    <td style="color: #38BDF8;">${row.slug}</td>
                    <td>${row.beg}</td>
                    <td>${row.nov}</td>
                    <td>${row.int}</td>
                    <td>${row.adv}</td>
                    <td>${row.eli}</td>
                    <td>
                        <button class="btn btn-sm" onclick="copySlug('${row.slug}')">Copy</button>
                        <button class="btn btn-sm btn-success" onclick="copyPy('${pyCode}')">Copy Py</button>
                        <button class="btn btn-sm" onclick="pywebview.api.open_url('https://strengthlevel.com/strength-standards/${row.slug}')">View</button>
                    </td>
                `;
                tbody.appendChild(tr);
            });
        }

        function copySlug(s) {
            pywebview.api.copy_to_clipboard(s);
            showToast(`Copied '${s}' to clipboard!`);
        }

        function copyPy(c) {
            pywebview.api.copy_to_clipboard(c);
            showToast(`Copied '${c}' to clipboard!`);
        }

        window.addEventListener('pywebviewready', initApp);
    </script>
</body>
</html>
"""


class WebViewBridgeApi:
    """Python backend methods exposed directly to JavaScript in the PyWebView window."""

    def __init__(self):
        self.manager = ProfileManager()

    def get_profiles(self) -> Dict[str, Any]:
        return {
            "profiles": [p.to_dict() for p in self.manager.profiles],
            "active_index": self.manager.active_profile_index,
        }

    def select_profile(self, index: int) -> Dict[str, Any]:
        self.manager.set_active(index)
        return {"success": True}

    def create_profile(self, name: str) -> Dict[str, Any]:
        self.manager.add_profile(Profile(name=name, sessions_dir="", output_dir="", sex="male"))
        return {"success": True}

    def _load_sessions(self, profile: Profile):
        sessions_file = getattr(profile, "sessions_file", None) or os.path.join(profile.sessions_dir, "sessions.py")
        if not os.path.exists(sessions_file):
            return None, sessions_file

        sessions_dir = os.path.dirname(sessions_file)
        if sessions_dir not in sys.path:
            sys.path.insert(0, sessions_dir)

        import importlib
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

        # Prepare serializable sessions list
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
                reps_str = ",".join(str(r) for r in log.reps)
                mass_str = f"{log.mass[0]}kg" if log.mass and max(log.mass) > 0 else "BW"
                exs.append({
                    "id": ex_id,
                    "name": info.get("name", ex_id),
                    "reps": reps_str,
                    "mass": mass_str,
                })
            recent_sessions.append({
                "date": d_str,
                "day": day_data.get("day", "?"),
                "exercises": exs,
            })

        # Body mass
        bm_log = getattr(sess, "BODYMASS_LOG", {})
        current_mass = p.mass
        if bm_log:
            sorted_bm = sorted(bm_log.items(), key=lambda x: str(x[0]), reverse=True)
            current_mass = sorted_bm[0][1]

        # Make stats JSON serializable
        clean_stats = {
            "total_days": stats.get("total_days", 0),
            "this_year_days": stats.get("this_year_days", 0),
            "latest_workout_date": stats.get("latest_workout_date", "--"),
            "latest_workout_day": stats.get("latest_workout_day", ""),
            "current_split_weeks": stats.get("current_split_weeks", 0.0),
            "current_split_start": stats.get("current_split_start", "N/A"),
            "cycle_length": stats.get("cycle_length", "N/A"),
            "split_sessions_details": [
                {
                    "date_str": s.get("date_str", ""),
                    "day": s.get("day", ""),
                    "exercises": list(s.get("exercises", [])),
                }
                for s in stats.get("split_sessions_details", [])
            ],
        }

        return {
            "success": True,
            "profile_name": p.name,
            "stats": clean_stats,
            "sessions": recent_sessions,
            "current_mass": current_mass,
        }

    def generate_excel(self) -> Dict[str, Any]:
        p = self.manager.get_active_profile()
        if not p:
            return {"success": False, "error": "No profile selected"}

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

            try:
                os.startfile(filename)
            except Exception:
                pass

            return {"success": True, "filename": filename}
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

    def get_plan(self) -> Dict[str, Any]:
        p = self.manager.get_active_profile()
        if not p:
            return {"success": False, "error": "No profile selected"}

        sess, file_path = self._load_sessions(p)
        if not sess:
            return {"success": False, "error": "Could not load sessions.py"}

        user_data = getattr(sess, "USER_DATA", {})
        N, last_day = detect_cycle(user_data)
        if N is None:
            return {"success": False, "error": "Cycle length unknown — complete at least 1 cycle"}

        day_nums = days_to_generate(N, last_day)
        if not day_nums:
            return {"success": False, "error": "All days in current cycle are already planned"}

        try:
            planned = build_planned_sessions(file_path, day_nums)
            serializable_plan = [
                {
                    "day_num": ps.day_num,
                    "date_str": ps.date_str,
                    "exercises": [
                        {
                            "var_name": ex.var_name,
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
            return {"success": True, "planned": serializable_plan}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def save_plan(self, planned_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        p = self.manager.get_active_profile()
        if not p:
            return {"success": False, "error": "No profile selected"}

        sessions_file = getattr(p, "sessions_file", None) or os.path.join(p.sessions_dir, "sessions.py")
        try:
            planned_objs = []
            for d in planned_data:
                ex_objs = [
                    PlannedExercise(
                        var_name=e.get("var_name", "exercise"),
                        sets=int(e.get("sets", 3)),
                        reps=str(e.get("reps", "5")),
                        mass=str(e.get("mass", "0")),
                        comment=str(e.get("comment", "")),
                    )
                    for e in d.get("exercises", [])
                ]
                planned_objs.append(
                    PlannedSession(day_num=int(d.get("day_num", 1)), date_str=d.get("date_str", ""), exercises=ex_objs)
                )

            write_planned_sessions(sessions_file, planned_objs)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def copy_to_clipboard(self, text: str):
        import tkinter as tk
        r = tk.Tk()
        r.withdraw()
        r.clipboard_clear()
        r.clipboard_append(text)
        r.update()
        r.destroy()

    def open_url(self, url: str):
        webbrowser.open(url)

    def edit_sessions(self):
        p = self.manager.get_active_profile()
        if p and p.sessions_dir:
            file_path = os.path.join(p.sessions_dir, "sessions.py")
            if os.path.exists(file_path):
                os.startfile(file_path)

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
        background_color="#121214",
    )
    webview.start(debug=False)


if __name__ == "__main__":
    run_webview_app()
