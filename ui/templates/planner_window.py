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
            color-scheme: dark;
            accent-color: #3B82F6;

            --bg-app: #0A0D14;
            --bg-card: rgba(18, 24, 38, 0.75);
            --bg-glass-modal: rgba(15, 20, 32, 0.96);
            --border-glass: rgba(255, 255, 255, 0.08);
            --text-primary: #FFFFFF;
            --text-secondary: #94A3B8;
            --text-muted: #64748B;
            --scrollbar-thumb: rgba(148, 163, 184, 0.36);
            --scrollbar-track: transparent;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            -webkit-font-smoothing: antialiased;
        }

        :focus-visible {
            outline: 2px solid #60A5FA;
            outline-offset: 2px;
        }

        .sr-only {
            position: absolute;
            width: 1px;
            height: 1px;
            padding: 0;
            margin: -1px;
            overflow: hidden;
            clip: rect(0, 0, 0, 0);
            white-space: nowrap;
            border: 0;
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

        /* Standard Custom Scrollbar with Legacy WebKit Fallback */
        main {
            scrollbar-color: var(--scrollbar-thumb) var(--scrollbar-track);
            scrollbar-width: thin;
        }

        @supports not (scrollbar-color: auto) {
            main {
                scrollbar-width: auto;
            }
            ::-webkit-scrollbar { width: 7px; height: 7px; }
            ::-webkit-scrollbar-track { background: var(--scrollbar-track); }
            ::-webkit-scrollbar-thumb { background: var(--scrollbar-thumb); border-radius: 4px; }
            ::-webkit-scrollbar-thumb:hover { background: rgba(148, 163, 184, 0.55); }
        }

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
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35);
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
            color: white;
            font-family: 'Outfit', sans-serif;
            font-weight: 800;
            font-size: 12px;
            border-radius: 5px;
            padding: 4px 12px;
            letter-spacing: 0.5px;
            box-shadow: 0 2px 8px rgba(0, 137, 123, 0.3);
        }
        .date-label { font-size: 12px; font-weight: 600; color: var(--text-secondary); }

        .plan-input {
            background: rgba(255, 255, 255, 0.05);
            color: #FFFFFF;
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 6px;
            padding: 7px 10px;
            font-size: 12px;
            font-weight: 500;
            transition: border-color 0.15s ease, background 0.15s ease, box-shadow 0.15s ease;
        }
        .plan-input:focus {
            border-color: #3B82F6;
            background: rgba(255, 255, 255, 0.08);
            box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.25);
            outline: none;
        }
        .plan-input:user-invalid {
            border-color: #EF4444;
            box-shadow: 0 0 0 2px rgba(239, 68, 68, 0.25);
        }
        .plan-input.center { text-align: center; }

        /* Branded Customizable Native <select> (progressive enhancement) */
        .brand-select,
        .brand-select::picker(select) {
            appearance: base-select;
        }
        .brand-select {
            background: rgba(255, 255, 255, 0.06);
            color: #FFFFFF;
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 6px;
            padding: 7px 10px;
            font-size: 12px;
            font-weight: 700;
            cursor: pointer;
            align-items: center;
        }
        .brand-select::picker(select) {
            background: #131B2A;
            color: #F8FAFC;
            border: 1px solid rgba(255, 255, 255, 0.16);
            border-radius: 8px;
            padding: 4px;
            box-shadow: 0 16px 36px rgba(0, 0, 0, 0.75);
        }
        .brand-select::picker-icon {
            color: #94A3B8;
        }
        .brand-select option {
            padding: 6px 10px;
            border-radius: 5px;
            color: #E2E8F0;
            cursor: pointer;
        }
        .brand-select option:hover,
        .brand-select option:checked {
            background: rgba(59, 130, 246, 0.28);
            color: #FFFFFF;
        }
        .brand-select option::checkmark {
            color: #60A5FA;
        }

        .plan-row-grid {
            display: grid;
            grid-template-columns: 55px 1fr 60px 105px 115px 1fr 190px;
            gap: 8px;
            align-items: center;
        }
        .plan-col-head {
            font-size: 11px;
            font-weight: 700;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            padding: 0 4px;
        }
        .plan-item-row {
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid rgba(255, 255, 255, 0.04);
            border-radius: 6px;
            padding: 6px 8px;
            transition: background 0.15s ease, border-color 0.15s ease;
        }
        .plan-item-row:hover {
            background: rgba(255, 255, 255, 0.05);
            border-color: rgba(255, 255, 255, 0.08);
        }

        .order-btn-group { display: flex; gap: 2px; }
        .btn-arrow {
            background: rgba(255, 255, 255, 0.05);
            color: #AAA;
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 4px;
            width: 24px;
            height: 26px;
            cursor: pointer;
            font-size: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: background 0.15s ease, color 0.15s ease, border-color 0.15s ease;
        }
        .btn-arrow:hover:not(:disabled) { background: #3B82F6; color: #FFF; border-color: #3B82F6; }
        .btn-arrow:disabled { opacity: 0.3; cursor: default; }

        .btn-pill-inc {
            background: rgba(34, 197, 94, 0.15);
            color: #4ADE80;
            border: 1px solid rgba(34, 197, 94, 0.3);
            border-radius: 5px;
            padding: 4px 6px;
            font-size: 10px;
            font-weight: 700;
            cursor: pointer;
            transition: background 0.15s ease, color 0.15s ease;
        }
        .btn-pill-inc:hover { background: #22C55E; color: #000; }

        .btn-pill-rep {
            background: rgba(192, 132, 252, 0.15);
            color: #C084FC;
            border: 1px solid rgba(192, 132, 252, 0.3);
            border-radius: 5px;
            padding: 4px 6px;
            font-size: 10px;
            font-weight: 700;
            cursor: pointer;
            transition: background 0.15s ease, color 0.15s ease;
        }
        .btn-pill-rep:hover { background: #A855F7; color: #000; }

        .btn-trash {
            background: rgba(239, 68, 68, 0.15);
            color: #F87171;
            border: 1px solid rgba(239, 68, 68, 0.3);
            border-radius: 5px;
            width: 26px;
            height: 26px;
            cursor: pointer;
            font-size: 11px;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: background 0.15s ease, color 0.15s ease;
        }
        .btn-trash:hover { background: #EF4444; color: #FFF; }

        .btn-add-ex {
            background: linear-gradient(135deg, #0288D1, #01579B);
            color: white;
            font-weight: 700;
            font-size: 12px;
            border: none;
            border-radius: 6px;
            padding: 6px 14px;
            cursor: pointer;
            transition: filter 0.15s ease;
        }
        .btn-add-ex:hover { filter: brightness(1.15); }

        .btn-del-day {
            background: rgba(220, 38, 38, 0.15);
            color: #FCA5A5;
            border: 1px solid rgba(220, 38, 38, 0.3);
            border-radius: 6px;
            padding: 5px 10px;
            font-size: 12px;
            cursor: pointer;
            transition: background 0.15s ease, color 0.15s ease;
        }
        .btn-del-day:hover { background: #DC2626; color: #FFF; }

        .btn-save-plan {
            background: linear-gradient(135deg, #059669, #10B981);
            color: white;
            font-family: 'Outfit', sans-serif;
            font-weight: 800;
            font-size: 13px;
            border: none;
            border-radius: 8px;
            padding: 11px 24px;
            cursor: pointer;
            margin-left: auto;
            box-shadow: 0 4px 14px rgba(16, 185, 129, 0.35);
            transition: filter 0.2s ease, transform 0.2s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.2s ease;
        }
        .btn-save-plan:hover { filter: brightness(1.15); box-shadow: 0 6px 20px rgba(16, 185, 129, 0.5); }
        @media (prefers-reduced-motion: no-preference) {
            .btn-save-plan:hover { transform: translateY(-1px); }
        }

        .btn-sec {
            background: rgba(255, 255, 255, 0.05);
            color: var(--text-secondary);
            font-size: 12px;
            font-weight: 700;
            border-radius: 8px;
            padding: 10px 18px;
            border: 1px solid rgba(255, 255, 255, 0.08);
            cursor: pointer;
            transition: background 0.15s ease, color 0.15s ease;
        }
        .btn-sec:hover { background: rgba(255, 255, 255, 0.1); color: #FFF; }

        .btn-primary2 {
            background: linear-gradient(135deg, #7C3AED, #C026D3);
            color: #FFFFFF;
            font-size: 12px;
            font-weight: 700;
            border-radius: 8px;
            padding: 10px 18px;
            border: none;
            cursor: pointer;
            box-shadow: 0 4px 14px rgba(124, 58, 237, 0.3);
            transition: filter 0.15s ease;
        }
        .btn-primary2:hover { filter: brightness(1.15); }

        .preset-row {
            display: flex;
            gap: 6px;
            font-size: 11px;
            color: #64748B;
            flex-wrap: wrap;
            align-items: center;
        }
        .preset-chip {
            appearance: none;
            background: rgba(56, 189, 248, 0.1);
            border: 1px solid rgba(56, 189, 248, 0.25);
            color: #38BDF8;
            border-radius: 4px;
            padding: 2px 7px;
            font-size: 11px;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.15s ease, color 0.15s ease;
        }
        .preset-chip:hover {
            background: rgba(56, 189, 248, 0.25);
            color: #FFFFFF;
        }

        /* ── NATIVE MODAL DIALOGS ────────────────────────────────────────── */
        dialog.app-dialog {
            background: #131B2A;
            color: var(--text-primary);
            border: 1px solid rgba(255, 255, 255, 0.15);
            border-radius: 12px;
            padding: 22px 24px;
            width: 390px;
            max-width: calc(100vw - 32px);
            margin: auto;
            box-shadow: 0 24px 60px rgba(0, 0, 0, 0.9);
            opacity: 0;
            transition-property: opacity, transform, display, overlay;
            transition-duration: 0.2s;
            transition-timing-function: cubic-bezier(0.16, 1, 0.3, 1);
            transition-behavior: allow-discrete;
        }

        @media (prefers-reduced-motion: no-preference) {
            dialog.app-dialog {
                transform: scale(0.96) translateY(8px);
            }
        }

        dialog.app-dialog[open] {
            display: flex;
            flex-direction: column;
            gap: 14px;
            opacity: 1;

            @starting-style {
                opacity: 0;
            }

            @media (prefers-reduced-motion: no-preference) {
                transform: scale(1) translateY(0);

                @starting-style {
                    transform: scale(0.96) translateY(8px);
                }
            }
        }

        dialog.app-dialog:modal {
            overscroll-behavior: contain;
        }

        dialog.app-dialog::backdrop {
            background: rgba(0, 0, 0, 0);
            backdrop-filter: blur(0px);
            overflow: hidden;
            overscroll-behavior: contain;
            transition-property: background-color, backdrop-filter, display, overlay;
            transition-duration: 0.2s;
            transition-timing-function: ease-out;
            transition-behavior: allow-discrete;
        }

        dialog.app-dialog[open]::backdrop {
            background: rgba(0, 0, 0, 0.78);
            backdrop-filter: blur(10px);

            @starting-style {
                background: rgba(0, 0, 0, 0);
                backdrop-filter: blur(0px);
            }
        }

        .dlg-title {
            font-family: 'Outfit', sans-serif;
            font-size: 16px;
            font-weight: 800;
            color: #FFF;
            display: flex;
            align-items: center;
            gap: 8px;
            margin: 0;
        }

        /* ── TOP-LAYER TOAST NOTIFICATIONS (popover="manual") ────────────── */
        .toast-region {
            position: fixed;
            inset-block-end: 18px;
            inset-inline-end: 18px;
            pointer-events: none;
            z-index: 50;
        }
        .toast-item[popover] {
            position: fixed;
            inset: auto;
            inset-inline-end: 18px;
            inset-block-end: var(--toast-offset, 18px);
            margin: 0;
            max-width: min(400px, calc(100vw - 36px));
            min-width: 240px;
            background: rgba(18, 24, 38, 0.96);
            backdrop-filter: blur(18px);
            border: 1px solid rgba(255, 255, 255, 0.14);
            border-inline-start: 3px solid #3B82F6;
            border-radius: 10px;
            padding: 12px 14px;
            color: #F8FAFC;
            font-size: 12px;
            line-height: 1.45;
            box-shadow: 0 14px 36px rgba(0, 0, 0, 0.7);
            display: flex;
            align-items: flex-start;
            gap: 10px;
            pointer-events: auto;
            opacity: 0;
            transition-property: opacity, transform, inset-block-end, display, overlay;
            transition-duration: 0.2s;
            transition-timing-function: cubic-bezier(0.16, 1, 0.3, 1);
            transition-behavior: allow-discrete;
        }
        @media (prefers-reduced-motion: no-preference) {
            .toast-item[popover] {
                transform: translateY(10px);
            }
        }
        .toast-item[popover]:popover-open {
            opacity: 1;

            @starting-style {
                opacity: 0;
            }

            @media (prefers-reduced-motion: no-preference) {
                transform: translateY(0);

                @starting-style {
                    transform: translateY(10px);
                }
            }
        }
        .toast-item[data-variant="success"] { border-inline-start-color: #10B981; }
        .toast-item[data-variant="warning"] { border-inline-start-color: #F59E0B; }
        .toast-item[data-variant="error"] { border-inline-start-color: #EF4444; }
        .toast-msg { flex: 1; white-space: pre-wrap; word-break: break-word; user-select: text; }
        .toast-close {
            appearance: none;
            background: transparent;
            border: 1px solid transparent;
            color: var(--text-secondary);
            border-radius: 4px;
            min-inline-size: 24px;
            min-block-size: 24px;
            cursor: pointer;
            font-size: 12px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
        }
        .toast-close:hover { background: rgba(255, 255, 255, 0.1); color: #FFFFFF; }

        @media (prefers-reduced-motion: reduce) {
            dialog.app-dialog,
            dialog.app-dialog::backdrop,
            .toast-item[popover] {
                transition-duration: 0.08s;
            }
        }
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

    <!-- Toast Region & Screen Reader Announcer -->
    <div id="toastRegion" class="toast-region" role="region" aria-label="Notifications"></div>
    <p class="sr-only">Screen reader notifications</p>
    <div id="srAnnouncer" class="sr-only" aria-live="polite" aria-atomic="true"></div>

    <!-- Deload Dialog -->
    <dialog id="modalDeloadPrompt" class="app-dialog" closedby="any" aria-labelledby="deloadTitle">
        <h1 class="dlg-title" id="deloadTitle">
            <span aria-hidden="true">🧪</span> Enter Deload Percentage
        </h1>
        <div style="font-size:12px; color:var(--text-secondary); line-height:1.4;">
            Specify the reduction percentage (e.g. 20 for -20% / 80% weight). Mass will be scaled and rounded to the selected plate step.
        </div>
        <div style="display:flex; align-items:center; gap:8px;">
            <input type="number" id="deloadPercentInput" class="plan-input" aria-label="Deload reduction percentage" style="flex:1; font-size:15px; font-weight:700; text-align:center;" value="20" min="1" max="99" step="1" autofocus onkeydown="if(event.key==='Enter') confirmDeload()">
            <span style="font-size:15px; font-weight:700; color:#94A3B8;">%</span>
            <select id="deloadStepInput" name="deloadStep" class="brand-select" aria-label="Plate rounding increment" style="width:135px;" title="Plate rounding increment">
                <option value="2.5">2.5 kg plates</option>
                <option value="1">1.0 kg micro</option>
            </select>
        </div>
        <div class="preset-row">
            <span>Quick presets:</span>
            <button type="button" class="preset-chip" onclick="setDeloadVal(10)">-10%</button>
            <button type="button" class="preset-chip" onclick="setDeloadVal(20)">-20% (80%)</button>
            <button type="button" class="preset-chip" onclick="setDeloadVal(25)">-25%</button>
            <button type="button" class="preset-chip" onclick="setDeloadVal(30)">-30% (70%)</button>
        </div>
        <div style="display:flex; gap:10px; margin-top:6px; justify-content:flex-end;">
            <button type="button" class="btn-sec" style="padding:7px 14px; font-size:12px;" onclick="closeDeloadModal()">Cancel</button>
            <button type="button" class="btn-primary2" style="padding:7px 16px; font-size:12px;" onclick="confirmDeload()">Apply</button>
        </div>
    </dialog>

    <!-- Restore / Reload Pre-Deload Dialog -->
    <dialog id="modalRestorePrompt" class="app-dialog" closedby="any" aria-labelledby="restoreTitle">
        <h1 class="dlg-title" id="restoreTitle">
            <span aria-hidden="true">🔄</span> Restore / Reload Pre-Deload
        </h1>
        <div style="font-size:12px; color:var(--text-secondary); line-height:1.4;">
            Scale your last clean non-deload cycle (e.g. 85-90% for a Week 1 Reload after deload, or 100% for full baseline).
        </div>
        <div style="display:flex; align-items:center; gap:8px;">
            <input type="number" id="restorePercentInput" class="plan-input" aria-label="Restore scale percentage" style="flex:1; font-size:15px; font-weight:700; text-align:center;" value="100" min="10" max="120" step="1" autofocus onkeydown="if(event.key==='Enter') confirmRestore()">
            <span style="font-size:15px; font-weight:700; color:#94A3B8;">%</span>
            <select id="restoreStepInput" name="restoreStep" class="brand-select" aria-label="Plate rounding increment" style="width:135px;" title="Plate rounding increment">
                <option value="2.5">2.5 kg plates</option>
                <option value="1">1.0 kg micro</option>
            </select>
        </div>
        <div class="preset-row">
            <span>Quick presets:</span>
            <button type="button" class="preset-chip" onclick="setRestoreVal(85)">85% (Reload)</button>
            <button type="button" class="preset-chip" onclick="setRestoreVal(90)">90% (Reload)</button>
            <button type="button" class="preset-chip" onclick="setRestoreVal(100)">100% (Full)</button>
        </div>
        <div style="display:flex; gap:10px; margin-top:6px; justify-content:flex-end;">
            <button type="button" class="btn-sec" style="padding:7px 14px; font-size:12px;" onclick="closeRestoreModal()">Cancel</button>
            <button type="button" class="btn-primary2" style="padding:7px 16px; font-size:12px;" onclick="confirmRestore()">Restore</button>
        </div>
    </dialog>

    <footer>
        <button type="button" class="btn-sec" onclick="window.close()">Cancel</button>
        <button type="button" class="btn-primary2" onclick="addPlanDay()">+ Add Day</button>
        <button type="button" class="btn-sec" onclick="applyDeload()">🧪 Deload Next Cycle...</button>
        <button type="button" class="btn-sec" onclick="restorePreDeload()">🔄 Restore Pre-Deload</button>
        <button type="button" class="btn-save-plan" onclick="saveCyclerPlan()">✅ Write to sessions.py</button>
    </footer>

    <script>
        let currentPlan = [];
        const activeToasts = [];

        function escapeAttr(str) {
            if (str === null || str === undefined) return "";
            return String(str)
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;")
                .replace(/"/g, "&quot;")
                .replace(/'/g, "&#039;");
        }

        function announceSR(text) {
            if (!text) return;
            if (typeof document.ariaNotify === "function") {
                try {
                    document.ariaNotify(text);
                    return;
                } catch (_e) {}
            }
            const el = document.getElementById("srAnnouncer");
            if (el) {
                el.textContent = "";
                requestAnimationFrame(() => { el.textContent = text; });
            }
        }

        function reflowToasts() {
            let offset = 18;
            for (let i = activeToasts.length - 1; i >= 0; i--) {
                const item = activeToasts[i];
                item.el.style.setProperty("--toast-offset", offset + "px");
                offset += (item.el.offsetHeight || 52) + 10;
            }
        }

        function dismissToast(entry) {
            const idx = activeToasts.indexOf(entry);
            if (idx === -1) return;
            clearTimeout(entry.timer);
            activeToasts.splice(idx, 1);
            try {
                if (entry.el.matches(":popover-open")) entry.el.hidePopover();
            } catch (_e) {}
            setTimeout(() => entry.el.remove(), 220);
            reflowToasts();
        }

        function showToast(message, variant = "info", durationMs = 4500) {
            const region = document.getElementById("toastRegion");
            if (!region) return;
            const toast = document.createElement("div");
            toast.className = "toast-item";
            toast.setAttribute("popover", "manual");
            toast.dataset.variant = variant;

            const msgEl = document.createElement("div");
            msgEl.className = "toast-msg";
            msgEl.textContent = message;

            const closeBtn = document.createElement("button");
            closeBtn.type = "button";
            closeBtn.className = "toast-close";
            closeBtn.setAttribute("aria-label", "Dismiss notification");
            closeBtn.textContent = "✕";

            toast.appendChild(msgEl);
            toast.appendChild(closeBtn);
            region.appendChild(toast);

            const entry = { el: toast, timer: null, paused: false };
            activeToasts.push(entry);

            const startTimer = () => {
                if (durationMs <= 0 || entry.paused) return;
                clearTimeout(entry.timer);
                entry.timer = setTimeout(() => dismissToast(entry), durationMs);
            };

            closeBtn.addEventListener("click", () => dismissToast(entry));
            toast.addEventListener("pointerenter", () => { entry.paused = true; clearTimeout(entry.timer); });
            toast.addEventListener("pointerleave", () => { entry.paused = false; startTimer(); });
            toast.addEventListener("focusin", () => { entry.paused = true; clearTimeout(entry.timer); });
            toast.addEventListener("focusout", () => { entry.paused = false; startTimer(); });

            try {
                toast.showPopover();
            } catch (_e) {
                toast.style.display = "flex";
            }
            reflowToasts();
            announceSR(message);
            startTimer();
        }

        function setupDialogLightDismissFallback() {
            if ("closedBy" in HTMLDialogElement.prototype) return;
            const outside = (e, dialog) => {
                const r = dialog.getBoundingClientRect();
                return e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom;
            };
            for (const dialog of document.querySelectorAll('dialog[closedby="any"]')) {
                let pressedOutside = false;
                dialog.addEventListener("pointerdown", (e) => { pressedOutside = outside(e, dialog); });
                dialog.addEventListener("pointerup", (e) => {
                    if (pressedOutside && outside(e, dialog)) dialog.close();
                });
            }
        }

        async function initPlanner() {
            setupDialogLightDismissFallback();
            const res = await pywebview.api.get_plan();
            if (!res.success) {
                showToast(res.error || "Failed to load plan.", "error", 6000);
                setTimeout(() => window.close(), 1800);
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
                                <button type="button" class="btn-arrow" aria-label="Move exercise up" onclick="moveEx(${dayIdx}, ${exIdx}, -1)" ${exIdx===0?'disabled':''}>▲</button>
                                <button type="button" class="btn-arrow" aria-label="Move exercise down" onclick="moveEx(${dayIdx}, ${exIdx}, 1)" ${exIdx===d.exercises.length-1?'disabled':''}>▼</button>
                            </div>
                            <input type="text" class="plan-input" aria-label="Exercise slug" style="font-family: 'JetBrains Mono', monospace;" value="${escapeAttr(ex.var_name)}" oninput="updateEx(${dayIdx}, ${exIdx}, 'var_name', this.value)" placeholder="exercise_slug">
                            <input type="number" class="plan-input center" aria-label="Sets" value="${escapeAttr(ex.sets)}" oninput="updateEx(${dayIdx}, ${exIdx}, 'sets', this.value)">
                            <input type="text" class="plan-input center" aria-label="Reps" style="font-family: 'JetBrains Mono', monospace;" value="${escapeAttr(ex.reps)}" oninput="updateEx(${dayIdx}, ${exIdx}, 'reps', this.value)">
                            <input type="text" class="plan-input center" aria-label="Mass in kg" style="font-family: 'JetBrains Mono', monospace;" value="${escapeAttr(ex.mass)}" oninput="updateEx(${dayIdx}, ${exIdx}, 'mass', this.value)">
                            <input type="text" class="plan-input" aria-label="Comment" value="${escapeAttr(ex.comment || '')}" oninput="updateEx(${dayIdx}, ${exIdx}, 'comment', this.value)" placeholder="comment">
                            <div style="display: flex; gap: 4px; align-items: center;">
                                <button type="button" class="btn-pill-inc" onclick="incMass(${dayIdx}, ${exIdx}, 1)" title="Micro-load +1 kg (2 x 0.5 kg fractional plates)">+1kg</button>
                                <button type="button" class="btn-pill-inc" onclick="incMass(${dayIdx}, ${exIdx}, 2.5)">+2.5kg</button>
                                <button type="button" class="btn-pill-rep" onclick="incReps(${dayIdx}, ${exIdx})">+2 Reps</button>
                                <button type="button" class="btn-trash" aria-label="Delete exercise" onclick="delEx(${dayIdx}, ${exIdx})">✕</button>
                            </div>
                        </div>
                    `;
                });

                dayCard.innerHTML = `
                    <div class="plan-day-hdr">
                        <span class="day-pill">Day ${d.day_num}</span>
                        <label class="date-label" for="dayDate_${dayIdx}">Date:</label>
                        <input type="date" id="dayDate_${dayIdx}" class="plan-input" value="${escapeAttr(d.date_str)}" onchange="updateDayDate(${dayIdx}, this.value)" style="width: 140px;">
                        <button type="button" class="btn-add-ex" style="margin-left: auto;" onclick="addEx(${dayIdx})">+ Add Exercise</button>
                        <button type="button" class="btn-del-day" onclick="delDay(${dayIdx})">🗑️ Delete Day</button>
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
        function incMass(dIdx, eIdx, step = 2.5) {
            const ex = currentPlan[dIdx].exercises[eIdx];
            const mParts = (ex.mass + "").split(",").map(p => {
                const v = parseFloat(p.trim());
                return !isNaN(v) && v > 0 ? (Math.round((v + step) * 100) / 100) : p.trim();
            });
            ex.mass = mParts.join(", ");

            // Automatically track increment in Comment field
            let c = (ex.comment || "").trim();
            const match = c.match(/\+([0-9.]+)\s*kg/i);
            if (match) {
                const currPlus = parseFloat(match[1]);
                const newPlus = Math.round((currPlus + step) * 100) / 100;
                c = c.replace(/\+[0-9.]+\s*kg/i, `+${newPlus} kg`);
            } else {
                c = (c + ` +${step} kg`).trim();
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
            if (m && typeof m.showModal === "function") {
                if (!m.open) m.showModal();
                const inp = document.getElementById("deloadPercentInput");
                if (inp) { inp.focus(); inp.select(); }
            }
        }
        function closeDeloadModal() {
            const m = document.getElementById("modalDeloadPrompt");
            if (m && m.open) m.close();
        }
        function setDeloadVal(v) {
            const inp = document.getElementById("deloadPercentInput");
            if (inp) inp.value = v;
        }
        function confirmDeload() {
            const inp = document.getElementById("deloadPercentInput");
            const stepInp = document.getElementById("deloadStepInput");
            const val = inp ? parseFloat(inp.value) : 20;
            const stepKg = stepInp ? parseFloat(stepInp.value) : 2.5;
            closeDeloadModal();
            applyDeloadPercentage(val, stepKg);
        }
        function applyDeloadPercentage(percent, stepKg = 2.5) {
            if (isNaN(percent) || percent <= 0 || percent >= 100) {
                showToast("Percentage must be between 1 and 99.", "warning");
                return;
            }
            const step = (!isNaN(stepKg) && stepKg > 0) ? stepKg : 2.5;
            const factor = 1.0 - (percent / 100.0);
            const tag = `${percent}% decreased deload`;
            currentPlan.forEach(d => {
                d.exercises.forEach(ex => {
                    const mParts = (ex.mass + "").split(",").map(p => {
                        const v = parseFloat(p.trim());
                        if (isNaN(v) || v <= 0) return p.trim();
                        // Scale and round to nearest selected plate increment
                        let scaled = Math.round((v * factor) / step) * step;
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
            showToast(`Applied -${percent}% deload (${step} kg rounding).`, "success", 3200);
        }
        function applyDeload() {
            openDeloadModal();
        }
        function openRestoreModal() {
            const m = document.getElementById("modalRestorePrompt");
            if (m && typeof m.showModal === "function") {
                if (!m.open) m.showModal();
                const inp = document.getElementById("restorePercentInput");
                if (inp) { inp.focus(); inp.select(); }
            }
        }
        function closeRestoreModal() {
            const m = document.getElementById("modalRestorePrompt");
            if (m && m.open) m.close();
        }
        function setRestoreVal(v) {
            const inp = document.getElementById("restorePercentInput");
            if (inp) inp.value = v;
        }
        function confirmRestore() {
            const inp = document.getElementById("restorePercentInput");
            const stepInp = document.getElementById("restoreStepInput");
            const scalePct = inp ? parseFloat(inp.value) : 100.0;
            const stepKg = stepInp ? parseFloat(stepInp.value) : 2.5;
            if (isNaN(scalePct) || scalePct < 10 || scalePct > 120) {
                showToast("Percentage must be between 10 and 120.", "warning");
                return;
            }
            closeRestoreModal();
            executeRestorePreDeload(scalePct, stepKg);
        }
        async function executeRestorePreDeload(scalePct, stepKg = 2.5) {
            const dayNums = currentPlan.map(d => parseInt(d.day_num));
            const res = await pywebview.api.restore_pre_deload(dayNums, scalePct, stepKg);
            if (!res.success) {
                showToast("Restore failed: " + res.error, "error", 6000);
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
            showToast(`Restored pre-deload baseline at ${scalePct}%.`, "success", 3200);
        }
        function restorePreDeload() {
            openRestoreModal();
        }
        async function saveCyclerPlan() {
            const res = await pywebview.api.save_plan(currentPlan);
            if (res.success) {
                showToast(`✅ Created plan with ${currentPlan.length} day(s)! Closing...`, "success", 2000);
                setTimeout(() => window.close(), 900);
            } else {
                showToast("Error writing plan: " + res.error, "error", 6500);
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
