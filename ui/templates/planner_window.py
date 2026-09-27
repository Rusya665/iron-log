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

    <!-- Deload Modal Prompt -->
    <div id="modalDeloadPrompt" style="display:none; position:fixed; inset:0; background:rgba(0,0,0,0.78); backdrop-filter:blur(10px); z-index:9999; align-items:center; justify-content:center;">
        <div style="background:#131B2A; border:1px solid rgba(255,255,255,0.15); border-radius:12px; padding:22px 24px; width:360px; box-shadow:0 24px 60px rgba(0,0,0,0.9); display:flex; flex-direction:column; gap:14px;">
            <div style="font-family:'Outfit',sans-serif; font-size:16px; font-weight:800; color:#FFF; display:flex; align-items:center; gap:8px;">
                <span>🧪</span> Enter Deload Percentage
            </div>
            <div style="font-size:12px; color:var(--text-secondary); line-height:1.4;">
                Specify the reduction percentage (e.g. 20 for -20% / 80% weight). Mass will be scaled and rounded to 2.5 kg plates.
            </div>
            <div style="display:flex; align-items:center; gap:8px;">
                <input type="number" id="deloadPercentInput" class="plan-input" style="flex:1; font-size:15px; font-weight:700; text-align:center;" value="20" min="1" max="99" step="1" onkeydown="if(event.key==='Enter') confirmDeload()">
                <span style="font-size:15px; font-weight:700; color:#94A3B8;">%</span>
            </div>
            <div style="display:flex; gap:6px; font-size:11px; color:#64748B; flex-wrap:wrap;">
                <span>Quick presets:</span>
                <a href="javascript:void(0)" onclick="setDeloadVal(10)" style="color:#38BDF8; text-decoration:none;">-10%</a> · 
                <a href="javascript:void(0)" onclick="setDeloadVal(20)" style="color:#38BDF8; text-decoration:none;">-20% (80% load)</a> · 
                <a href="javascript:void(0)" onclick="setDeloadVal(25)" style="color:#38BDF8; text-decoration:none;">-25%</a> · 
                <a href="javascript:void(0)" onclick="setDeloadVal(30)" style="color:#38BDF8; text-decoration:none;">-30% (70% load)</a>
            </div>
            <div style="display:flex; gap:10px; margin-top:6px; justify-content:flex-end;">
                <button class="btn-sec" style="padding:7px 14px; font-size:12px;" onclick="closeDeloadModal()">Cancel</button>
                <button class="btn-primary2" style="padding:7px 16px; font-size:12px;" onclick="confirmDeload()">Apply</button>
            </div>
        </div>
    </div>

    <footer>
        <button class="btn-sec" onclick="window.close()">Cancel</button>
        <button class="btn-primary2" onclick="addPlanDay()">+ Add Day</button>
        <button class="btn-sec" onclick="applyDeload()">🧪 Deload Next Cycle...</button>
        <button class="btn-sec" onclick="restorePreDeload()">🔄 Restore Pre-Deload</button>
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
        function openDeloadModal() {
            const m = document.getElementById("modalDeloadPrompt");
            if (m) {
                m.style.display = "flex";
                const inp = document.getElementById("deloadPercentInput");
                if (inp) { inp.focus(); inp.select(); }
            } else {
                const val = prompt("Enter deload percentage (e.g. 20 for -20% / 80% weight):", "20");
                if (val !== null) applyDeloadPercentage(parseFloat(val));
            }
        }
        function closeDeloadModal() {
            const m = document.getElementById("modalDeloadPrompt");
            if (m) m.style.display = "none";
        }
        function setDeloadVal(v) {
            const inp = document.getElementById("deloadPercentInput");
            if (inp) inp.value = v;
        }
        function confirmDeload() {
            const inp = document.getElementById("deloadPercentInput");
            const val = inp ? parseFloat(inp.value) : 20;
            closeDeloadModal();
            applyDeloadPercentage(val);
        }
        function applyDeloadPercentage(percent) {
            if (isNaN(percent) || percent <= 0 || percent >= 100) {
                alert("Percentage must be between 1 and 99.");
                return;
            }
            const factor = 1.0 - (percent / 100.0);
            const tag = `${percent}% decreased deload`;
            currentPlan.forEach(d => {
                d.exercises.forEach(ex => {
                    const mParts = (ex.mass + "").split(",").map(p => {
                        const v = parseFloat(p.trim());
                        if (isNaN(v) || v <= 0) return p.trim();
                        // Scale and round to nearest 2.5 kg plates
                        let scaled = Math.round((v * factor) / 2.5) * 2.5;
                        if (scaled === 0 && v > 0) {
                            scaled = Math.round((v * factor) * 2) / 2;
                        }
                        return Math.round(scaled * 100) / 100;
                    });
                    ex.mass = mParts.join(", ");
                    let c = (ex.comment || "").trim();
                    c = c.replace(/\b\d+(\.\d+)?%\s*decreased\s*deload\b/gi, "")
                         .replace(/Deload\s*-\d+%/gi, "")
                         .replace(/·\s*·/g, "·")
                         .trim();
                    if (c.endsWith("·")) c = c.slice(0, -1).trim();
                    if (c.startsWith("·")) c = c.slice(1).trim();
                    ex.comment = c ? `${c} · ${tag}` : tag;
                });
            });
            renderCyclerDays();
        }
        function applyDeload() {
            openDeloadModal();
        }
        async function restorePreDeload() {
            if (!confirm("Restore plan from the last non-deload cycle (100% pre-deload weights)?")) return;
            const dayNums = currentPlan.map(d => parseInt(d.day_num));
            const res = await pywebview.api.restore_pre_deload(dayNums, 100.0);
            if (!res.success) {
                alert("Restore failed: " + res.error);
                return;
            }
            if (res.planned && res.planned.length === currentPlan.length) {
                res.planned.forEach((p, idx) => {
                    if (currentPlan[idx] && currentPlan[idx].date_str) {
                        p.date_str = currentPlan[idx].date_str;
                    }
                });
            }
            currentPlan = res.planned;
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
