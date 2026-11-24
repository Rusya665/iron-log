from core.version import __version__


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
        @property --fade-start {{
            syntax: "<length>";
            inherits: false;
            initial-value: 0px;
        }}
        @property --fade-end {{
            syntax: "<length>";
            inherits: false;
            initial-value: 0px;
        }}

        :root {{
            color-scheme: dark;
            accent-color: #3B82F6;

            --bg-app: #0A0D14;
            --bg-sidebar: rgba(13, 17, 26, 0.95);
            --bg-card: rgba(18, 24, 38, 0.72);
            --bg-card-hover: rgba(24, 32, 50, 0.85);
            --bg-glass-modal: rgba(15, 20, 32, 0.96);
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

            --scrollbar-thumb: rgba(148, 163, 184, 0.36);
            --scrollbar-track: transparent;

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

        :focus-visible {{
            outline: 2px solid #60A5FA;
            outline-offset: 2px;
        }}

        .sr-only {{
            position: absolute;
            width: 1px;
            height: 1px;
            padding: 0;
            margin: -1px;
            overflow: hidden;
            clip: rect(0, 0, 0, 0);
            white-space: nowrap;
            border: 0;
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

        /* Standard Custom Scrollbar with Legacy WebKit Fallback */
        main,
        .sessions-row,
        .modal-body,
        #updateReleaseNotes {{
            scrollbar-color: var(--scrollbar-thumb) var(--scrollbar-track);
            scrollbar-width: thin;
        }}

        @supports not (scrollbar-color: auto) {{
            main,
            .sessions-row,
            .modal-body,
            #updateReleaseNotes {{
                scrollbar-width: auto;
            }}
            ::-webkit-scrollbar {{ width: 7px; height: 7px; }}
            ::-webkit-scrollbar-track {{ background: var(--scrollbar-track); }}
            ::-webkit-scrollbar-thumb {{ background: var(--scrollbar-thumb); border-radius: 4px; }}
            ::-webkit-scrollbar-thumb:hover {{ background: rgba(148, 163, 184, 0.55); }}
        }}

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
            z-index: 10;
            flex-shrink: 0;
        }}
        .brand-badge {{
            font-family: 'Outfit', sans-serif;
            font-weight: 800;
            font-size: 12px;
            letter-spacing: 1px;
            background: linear-gradient(135deg, #60A5FA, #A78BFA);
            -webkit-background-clip: text;
            background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-right: 14px;
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        .menubar-strip {{
            display: flex;
            align-items: center;
        }}
        .menu-btn {{
            appearance: none;
            background: transparent;
            border: none;
            color: var(--text-secondary);
            padding: 4px 10px;
            cursor: pointer;
            border-radius: var(--radius-sm);
            font-size: 12px;
            font-weight: 500;
            transition: background-color 0.15s cubic-bezier(0.16, 1, 0.3, 1), color 0.15s ease;
        }}
        .menu-btn:hover,
        .menu-btn[aria-expanded="true"] {{
            background-color: rgba(255, 255, 255, 0.08);
            color: #FFFFFF;
        }}

        #mBtnApp {{ anchor-name: --menu-app-anchor; }}
        #mBtnSettings {{ anchor-name: --menu-settings-anchor; }}
        #mBtnProfiles {{ anchor-name: --menu-profiles-anchor; }}
        #mBtnExp {{ anchor-name: --menu-exp-anchor; }}

        #menuApp {{ position-anchor: --menu-app-anchor; }}
        #menuSettings {{ position-anchor: --menu-settings-anchor; }}
        #menuProfiles {{ position-anchor: --menu-profiles-anchor; }}
        #menuExp {{ position-anchor: --menu-exp-anchor; }}

        .menu-dropdown[popover] {{
            background: rgba(18, 24, 38, 0.96);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: var(--radius-md);
            min-width: 230px;
            padding: 5px;
            box-shadow: 0 16px 36px rgba(0, 0, 0, 0.65), 0 0 0 1px rgba(255, 255, 255, 0.05);
            color: #E2E8F0;
            opacity: 0;
            transition-property: opacity, transform, display, overlay;
            transition-duration: 0.15s;
            transition-timing-function: cubic-bezier(0.16, 1, 0.3, 1);
            transition-behavior: allow-discrete;
        }}

        @media (prefers-reduced-motion: no-preference) {{
            .menu-dropdown[popover] {{
                transform: translateY(-4px) scale(0.98);
            }}
            /* Switching between open menubar menus is instant, as in native menubars */
            [role="menubar"]:has(> [popover]:popover-open) > [popover] {{
                transition: none;
            }}
        }}

        .menu-dropdown[popover]:popover-open {{
            display: flex;
            flex-direction: column;
            opacity: 1;

            @starting-style {{
                opacity: 0;
            }}

            @media (prefers-reduced-motion: no-preference) {{
                transform: translateY(0) scale(1);

                @starting-style {{
                    transform: translateY(-4px) scale(0.98);
                }}
            }}
        }}

        @supports (position-area: block-end) {{
            .menu-dropdown[popover] {{
                position: fixed;
                inset: auto;
                margin: 4px 0 0 0;
                position-area: block-end span-inline-end;
                position-try-fallbacks: flip-inline, flip-block;
            }}
        }}

        @supports not (position-area: block-end) {{
            .menu-dropdown[popover] {{
                position: fixed;
                inset: auto;
                margin: 0;
            }}
        }}

        .menu-item {{
            appearance: none;
            background: transparent;
            border: none;
            width: 100%;
            text-align: left;
            padding: 7px 12px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            cursor: pointer;
            font-size: 12px;
            color: #E2E8F0;
            border-radius: var(--radius-sm);
            transition: background 0.12s ease, color 0.12s ease, transform 0.12s ease;
        }}
        .menu-item:hover,
        .menu-item:focus-visible {{
            background: linear-gradient(90deg, rgba(59, 130, 246, 0.85), rgba(37, 99, 235, 0.85));
            color: #FFFFFF;
            outline: none;
        }}
        @media (prefers-reduced-motion: no-preference) {{
            .menu-item:hover {{
                transform: translateX(2px);
            }}
        }}
        .menu-sep {{
            border: 0;
            height: 1px;
            background: rgba(255, 255, 255, 0.07);
            margin: 4px 2px;
        }}

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
            box-shadow: 4px 0 24px rgba(0, 0, 0, 0.25);
        }}

        .profile-card {{
            appearance: none;
            width: 100%;
            text-align: left;
            background: linear-gradient(135deg, rgba(30, 41, 59, 0.7), rgba(15, 23, 42, 0.8));
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: var(--radius-lg);
            padding: 12px 14px;
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 6px;
            cursor: pointer;
            transition: border-color 0.2s ease, transform 0.2s ease, box-shadow 0.2s ease;
        }}
        .profile-card:hover {{
            border-color: rgba(99, 102, 241, 0.4);
            box-shadow: 0 4px 14px rgba(0, 0, 0, 0.3);
        }}
        @media (prefers-reduced-motion: no-preference) {{
            .profile-card:hover {{ transform: translateY(-1px); }}
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
            flex-shrink: 0;
        }}
        .profile-info {{ display: flex; flex-direction: column; min-width: 0; }}
        .prof-name {{
            font-family: 'Outfit', sans-serif;
            font-size: 15px;
            font-weight: 700;
            color: #FFFFFF;
            letter-spacing: 0.2px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}
        .prof-badge {{ font-size: 10px; color: #4ADE80; display: flex; align-items: center; gap: 4px; font-weight: 600; margin-top: 1px; }}
        .prof-dot {{ width: 6px; height: 6px; border-radius: 50%; background-color: #4ADE80; box-shadow: 0 0 6px #4ADE80; }}

        .divider {{ height: 1px; background: rgba(255, 255, 255, 0.06); margin: 6px 0; }}

        /* Primary Action Buttons */
        .btn-side-primary1,
        .btn-side-primary2,
        .btn-side-primary3 {{
            color: #FFFFFF;
            font-size: 13px;
            font-weight: 700;
            border-radius: var(--radius-md);
            padding: 12px 14px;
            border: none;
            cursor: pointer;
            text-align: center;
            transition: filter 0.2s ease, transform 0.2s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.2s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        }}
        .btn-side-primary1 {{
            background: linear-gradient(135deg, var(--accent-blue-start), var(--accent-blue-end));
            box-shadow: 0 4px 14px rgba(37, 99, 235, 0.35);
        }}
        .btn-side-primary1:hover {{ filter: brightness(1.15); box-shadow: 0 6px 20px rgba(37, 99, 235, 0.5); }}

        .btn-side-primary2 {{
            background: linear-gradient(135deg, var(--accent-purple-start), var(--accent-purple-end));
            box-shadow: 0 4px 14px rgba(124, 58, 237, 0.35);
        }}
        .btn-side-primary2:hover {{ filter: brightness(1.15); box-shadow: 0 6px 20px rgba(124, 58, 237, 0.5); }}

        .btn-side-primary3 {{
            background: linear-gradient(135deg, var(--accent-emerald-start), var(--accent-emerald-end));
            box-shadow: 0 4px 14px rgba(5, 150, 105, 0.35);
        }}
        .btn-side-primary3:hover {{ filter: brightness(1.15); box-shadow: 0 6px 20px rgba(5, 150, 105, 0.5); }}

        @media (prefers-reduced-motion: no-preference) {{
            .btn-side-primary1:hover,
            .btn-side-primary2:hover,
            .btn-side-primary3:hover {{ transform: translateY(-2px); }}
        }}

        .btn-side-sec {{
            background: rgba(255, 255, 255, 0.04);
            color: var(--text-secondary);
            font-size: 12px;
            font-weight: 600;
            border-radius: var(--radius-md);
            padding: 9px 12px;
            border: 1px solid rgba(255, 255, 255, 0.04);
            cursor: pointer;
            text-align: left;
            transition: background 0.15s ease, color 0.15s ease, border-color 0.15s ease, transform 0.15s ease;
            display: flex;
            align-items: center;
            gap: 9px;
        }}
        .btn-side-sec:hover {{
            background: rgba(255, 255, 255, 0.08);
            color: #FFFFFF;
            border-color: rgba(255, 255, 255, 0.1);
        }}
        @media (prefers-reduced-motion: no-preference) {{
            .btn-side-sec:hover {{ transform: translateX(2px); }}
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
            font-size: 12px;
            font-weight: 600;
            border-radius: var(--radius-md);
            padding: 8px 16px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            cursor: pointer;
            transition: background 0.2s ease, border-color 0.2s ease, transform 0.2s ease;
            display: flex;
            align-items: center;
            gap: 6px;
            backdrop-filter: blur(10px);
        }}
        .btn-refresh:hover {{
            background: rgba(255, 255, 255, 0.12);
            border-color: rgba(255, 255, 255, 0.2);
        }}
        @media (prefers-reduced-motion: no-preference) {{
            .btn-refresh:hover {{ transform: translateY(-1px); }}
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
            transition: background 0.25s ease, border-color 0.25s ease, transform 0.25s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.25s ease;
            position: relative;
            overflow: hidden;
            text-align: left;
            color: inherit;
        }}
        .stat-card::before {{
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0; height: 2px;
            background: linear-gradient(90deg, transparent, rgba(99, 102, 241, 0.5), transparent);
            opacity: 0;
            transition: opacity 0.2s;
        }}
        .stat-card:hover {{
            background: var(--bg-card-hover);
            border-color: var(--border-glass-hover);
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
        }}
        @media (prefers-reduced-motion: no-preference) {{
            .stat-card:hover {{ transform: translateY(-2px); }}
        }}
        .stat-card:hover::before {{ opacity: 1; }}

        .stat-card.clickable {{ cursor: pointer; }}
        .stat-card.clickable:hover {{
            border-color: rgba(59, 130, 246, 0.5);
            box-shadow: 0 8px 24px rgba(37, 99, 235, 0.15);
        }}

        .stat-header {{ display: flex; align-items: center; justify-content: space-between; width: 100%; }}
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

        /* Workout Cards Horizontal Row with Scroll-Driven Affordance Fades */
        .sessions-row {{
            display: flex;
            gap: 14px;
            overflow-x: auto;
            flex: 1;
            padding-bottom: 8px;
            scroll-padding-inline: 2.5rem;
        }}

        @supports (animation-timeline: scroll(self inline)) {{
            .sessions-row {{
                --fade-size: 2.5rem;
                --fade-dir: right;
                --fade-start-pos: 0;
                --fade-end-pos: 100%;
                mask:
                    linear-gradient(black, black) no-clip subtract,
                    linear-gradient(to var(--fade-dir), black, transparent) var(--fade-start-pos) 0 / var(--fade-start) 100% no-repeat no-clip,
                    linear-gradient(to var(--fade-dir), transparent, black) var(--fade-end-pos) 0 / var(--fade-end) 100% no-repeat no-clip;
                animation: reveal-fade-start linear both, hide-fade-end linear both;
                animation-timeline: scroll(self inline);
                animation-range: 0 var(--fade-size), calc(100% - var(--fade-size)) 100%;
            }}
        }}

        @keyframes reveal-fade-start {{
            to {{ --fade-start: var(--fade-size); }}
        }}
        @keyframes hide-fade-end {{
            from {{ --fade-end: var(--fade-size); }}
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
            transition: background 0.25s ease, border-color 0.25s ease, transform 0.25s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.25s ease;
        }}
        .workout-card:hover {{
            background: var(--bg-card-hover);
            border-color: rgba(255, 255, 255, 0.15);
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
        }}
        @media (prefers-reduced-motion: no-preference) {{
            .workout-card:hover {{ transform: translateY(-2px); }}
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
            font-size: 10px;
            font-weight: 700;
            border-radius: 4px;
            padding: 2px 7px;
            text-transform: uppercase;
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
            gap: 8px;
            font-size: 12px;
            padding: 5px 8px;
            border-radius: var(--radius-sm);
            background: rgba(255, 255, 255, 0.02);
            transition: background 0.12s ease;
        }}
        .ex-item:hover {{
            background: rgba(255, 255, 255, 0.06);
        }}
        .ex-name {{
            appearance: none;
            background: transparent;
            border: none;
            padding: 0;
            text-align: left;
            color: #E2E8F0;
            font-size: 12px;
            font-weight: 600;
            cursor: pointer;
            transition: color 0.12s;
        }}
        .ex-name:hover,
        .ex-name:focus-visible {{ color: #60A5FA; }}
        .ex-name[data-active-anchor] {{
            anchor-name: --active-ex-anchor;
        }}
        .ex-meta {{
            color: var(--text-secondary);
            font-size: 11px;
            font-family: 'JetBrains Mono', monospace;
            font-weight: 500;
            background: rgba(0, 0, 0, 0.25);
            padding: 2px 6px;
            border-radius: 4px;
            border: 1px solid rgba(255, 255, 255, 0.04);
            flex-shrink: 0;
        }}

        /* ── 3. HOVER STANDARDS TOOLTIP (Popover + Anchor Positioning) ───── */
        #standardsTooltip[popover] {{
            background: rgba(18, 24, 38, 0.96);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.15);
            border-radius: var(--radius-md);
            padding: 12px 14px;
            box-shadow: 0 16px 36px rgba(0, 0, 0, 0.85);
            color: var(--text-primary);
            pointer-events: none;
            max-width: 400px;
            opacity: 0;
            transition-property: opacity, transform, display, overlay;
            transition-duration: 0.15s;
            transition-timing-function: cubic-bezier(0.16, 1, 0.3, 1);
            transition-behavior: allow-discrete;
        }}

        @media (prefers-reduced-motion: no-preference) {{
            #standardsTooltip[popover] {{
                transform: scale(0.97);
            }}
        }}

        #standardsTooltip[popover]:popover-open {{
            opacity: 1;

            @starting-style {{
                opacity: 0;
            }}

            @media (prefers-reduced-motion: no-preference) {{
                transform: scale(1);

                @starting-style {{
                    transform: scale(0.97);
                }}
            }}
        }}

        @supports (position-area: block-end) {{
            #standardsTooltip[popover] {{
                position: fixed;
                inset: auto;
                margin: 8px 0 0 0;
                position-anchor: --active-ex-anchor;
                position-area: block-end span-inline-end;
                position-try-fallbacks: flip-block, flip-inline, flip-block flip-inline;
            }}
        }}

        @supports not (position-area: block-end) {{
            #standardsTooltip[popover] {{
                position: fixed;
                inset: auto;
                margin: 0;
            }}
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
            position: static;
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

        /* ── 4. NATIVE MODAL DIALOGS ─────────────────────────────────────── */
        dialog.app-dialog {{
            background: var(--bg-glass-modal);
            color: var(--text-primary);
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: var(--radius-xl);
            padding: 0;
            margin: auto;
            max-width: calc(100vw - 32px);
            max-height: 88vh;
            overflow: hidden;
            box-shadow: 0 24px 60px rgba(0, 0, 0, 0.85);
            opacity: 0;
            transition-property: opacity, transform, display, overlay;
            transition-duration: 0.22s;
            transition-timing-function: cubic-bezier(0.16, 1, 0.3, 1);
            transition-behavior: allow-discrete;
        }}

        @media (prefers-reduced-motion: no-preference) {{
            dialog.app-dialog {{
                transform: scale(0.96) translateY(10px);
            }}
        }}

        dialog.app-dialog[open] {{
            display: flex;
            flex-direction: column;
            opacity: 1;

            @starting-style {{
                opacity: 0;
            }}

            @media (prefers-reduced-motion: no-preference) {{
                transform: scale(1) translateY(0);

                @starting-style {{
                    transform: scale(0.96) translateY(10px);
                }}
            }}
        }}

        dialog.app-dialog:modal {{
            overscroll-behavior: contain;
        }}

        dialog.app-dialog::backdrop {{
            background: rgba(0, 0, 0, 0);
            backdrop-filter: blur(0px);
            overflow: hidden;
            overscroll-behavior: contain;
            transition-property: background-color, backdrop-filter, display, overlay;
            transition-duration: 0.22s;
            transition-timing-function: ease-out;
            transition-behavior: allow-discrete;
        }}

        dialog.app-dialog[open]::backdrop {{
            background: rgba(0, 0, 0, 0.76);
            backdrop-filter: blur(12px);

            @starting-style {{
                background: rgba(0, 0, 0, 0);
                backdrop-filter: blur(0px);
            }}
        }}

        @media (prefers-reduced-motion: reduce) {{
            dialog.app-dialog,
            dialog.app-dialog::backdrop,
            .menu-dropdown[popover],
            #standardsTooltip[popover],
            .toast-item[popover] {{
                transition-duration: 0.08s;
            }}
        }}

        .modal-hdr {{
            background: rgba(255, 255, 255, 0.03);
            padding: 18px 24px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.07);
            flex-shrink: 0;
        }}
        .modal-title {{
            font-family: 'Outfit', sans-serif;
            font-size: 18px;
            font-weight: 800;
            color: #FFFFFF;
            margin: 0;
        }}
        .modal-sub {{ font-size: 12px; color: var(--text-secondary); margin-top: 3px; }}
        .modal-body {{
            flex: 1;
            overflow-y: auto;
            padding: 20px 24px;
            display: flex;
            flex-direction: column;
            gap: 14px;
        }}
        .modal-footer {{
            background: rgba(10, 14, 23, 0.75);
            padding: 14px 24px;
            border-top: 1px solid rgba(255, 255, 255, 0.06);
            display: flex;
            gap: 12px;
            align-items: center;
            flex-shrink: 0;
        }}

        .plan-input {{
            background: rgba(255, 255, 255, 0.05);
            color: #FFFFFF;
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: var(--radius-sm);
            padding: 8px 12px;
            font-size: 12px;
            font-weight: 500;
            transition: border-color 0.15s ease, background 0.15s ease, box-shadow 0.15s ease;
        }}
        .plan-input:focus {{
            border-color: #3B82F6;
            background: rgba(255, 255, 255, 0.08);
            box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.25);
            outline: none;
        }}
        .plan-input:user-invalid {{
            border-color: #EF4444;
            box-shadow: 0 0 0 2px rgba(239, 68, 68, 0.25);
        }}

        /* Standards & Tables */
        table {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
        thead th {{
            position: sticky;
            top: 0;
            z-index: 2;
            background: rgba(15, 20, 32, 0.98);
            color: var(--text-muted);
            font-weight: 700;
            text-transform: uppercase;
            font-size: 11px;
            letter-spacing: 0.5px;
            padding: 10px 8px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            text-align: left;
        }}
        td {{ padding: 9px 8px; border-bottom: 1px solid rgba(255, 255, 255, 0.04); color: #CBD5E1; }}
        tr:hover {{ background: rgba(255, 255, 255, 0.03); }}

        #stdTbody tr {{
            content-visibility: auto;
            contain-intrinsic-size: auto none auto 38px;
        }}

        .badge-slug {{ color: #38BDF8; font-family: 'JetBrains Mono', monospace; font-size: 11px; }}
        .btn-tool {{
            background: rgba(255, 255, 255, 0.06);
            color: #FFFFFF;
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 4px;
            padding: 4px 10px;
            min-block-size: 26px;
            font-size: 11px;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.15s ease, border-color 0.15s ease, color 0.15s ease;
        }}
        .btn-tool:hover {{ background: #3B82F6; border-color: #3B82F6; }}
        .btn-tool[data-copied] {{
            background: rgba(16, 185, 129, 0.22);
            border-color: rgba(16, 185, 129, 0.55);
            color: #6EE7B7;
        }}
        .btn-tool[data-failed] {{
            background: rgba(239, 68, 68, 0.22);
            border-color: rgba(239, 68, 68, 0.55);
            color: #FCA5A5;
        }}
        .btn-danger {{
            background: rgba(239, 68, 68, 0.18);
            color: #FCA5A5;
            border: 1px solid rgba(239, 68, 68, 0.35);
            border-radius: var(--radius-sm);
            padding: 8px 18px;
            font-size: 12px;
            font-weight: 700;
            cursor: pointer;
            transition: background 0.15s ease, color 0.15s ease;
        }}
        .btn-danger:hover {{
            background: #EF4444;
            color: #FFFFFF;
        }}

        /* ── 5. SEMANTIC UPDATE PROGRESS BAR ────────────────────────────── */
        progress.update-progress {{
            appearance: none;
            border: 0 solid;
            width: 100%;
            height: 8px;
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.08);
            overflow: clip;
            container-type: inline-size;
            --progress-bar-indeterminate-size: 32%;
            --progress-bar-indeterminate-duration: 1.4s;
        }}
        @media (prefers-reduced-motion: reduce) {{
            progress.update-progress {{
                --progress-bar-indeterminate-duration: 8s;
            }}
        }}
        progress.update-progress::-webkit-progress-bar {{
            background: transparent;
        }}
        progress.update-progress::-webkit-progress-value {{
            background: linear-gradient(90deg, #3B82F6, #10B981);
            border-radius: 999px;
            transition: inline-size 0.2s ease;
            animation: var(--progress-bar-animation, none);
        }}
        progress.update-progress::-moz-progress-bar {{
            background: linear-gradient(90deg, #3B82F6, #10B981);
            border-radius: 999px;
            transition: inline-size 0.2s ease;
            animation: var(--progress-bar-animation, none);
        }}
        progress.update-progress:indeterminate {{
            --progress-bar-animation: progress-indeterminate var(--progress-bar-indeterminate-duration) infinite linear;
        }}
        @keyframes progress-indeterminate {{
            from, to {{
                inline-size: var(--progress-bar-indeterminate-size);
                margin-right: auto;
            }}
            from {{ translate: -100%; }}
            to {{ translate: 100cqi; }}
        }}

        /* ── 6. TOP-LAYER TOAST NOTIFICATIONS (popover="manual") ────────── */
        .toast-region {{
            position: fixed;
            inset-block-end: 18px;
            inset-inline-end: 18px;
            display: flex;
            flex-direction: column;
            gap: 10px;
            max-width: min(420px, calc(100vw - 36px));
            pointer-events: none;
            z-index: 50;
        }}
        .toast-item[popover] {{
            position: fixed;
            inset: auto;
            inset-inline-end: 18px;
            inset-block-end: var(--toast-offset, 18px);
            margin: 0;
            max-width: min(420px, calc(100vw - 36px));
            min-width: 260px;
            background: rgba(18, 24, 38, 0.96);
            backdrop-filter: blur(18px);
            border: 1px solid rgba(255, 255, 255, 0.14);
            border-inline-start: 3px solid #3B82F6;
            border-radius: var(--radius-md);
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
        }}
        @media (prefers-reduced-motion: no-preference) {{
            .toast-item[popover] {{
                transform: translateY(10px);
            }}
        }}
        .toast-item[popover]:popover-open {{
            opacity: 1;

            @starting-style {{
                opacity: 0;
            }}

            @media (prefers-reduced-motion: no-preference) {{
                transform: translateY(0);

                @starting-style {{
                    transform: translateY(10px);
                }}
            }}
        }}
        .toast-item[data-variant="success"] {{ border-inline-start-color: #10B981; }}
        .toast-item[data-variant="warning"] {{ border-inline-start-color: #F59E0B; }}
        .toast-item[data-variant="error"] {{ border-inline-start-color: #EF4444; }}
        .toast-msg {{
            flex: 1;
            white-space: pre-wrap;
            word-break: break-word;
            user-select: text;
        }}
        .toast-close {{
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
            transition: background 0.12s ease, color 0.12s ease;
        }}
        .toast-close:hover {{
            background: rgba(255, 255, 255, 0.1);
            color: #FFFFFF;
        }}
    </style>
</head>
<body>
    <!-- ── 0. TOP DESKTOP MENU BAR ─────────────────────────────────────── -->
    <nav class="top-menubar" aria-label="Application">
        <div class="brand-badge">⚡ IRON LOG</div>

        <div class="menubar-strip" role="menubar" aria-label="Application commands">
            <button type="button" class="menu-btn" id="mBtnApp" role="menuitem" aria-haspopup="menu" aria-expanded="false" popovertarget="menuApp" tabindex="0">App</button>
            <div class="menu-dropdown" id="menuApp" popover="auto" role="menu" aria-labelledby="mBtnApp">
                <button type="button" class="menu-item" role="menuitem" onclick="closeAllMenus(); openAboutModal()">ℹ️  About Iron Log</button>
                <button type="button" class="menu-item" role="menuitem" onclick="closeAllMenus(); triggerUpdateCheck()">🔄  Check for Updates</button>
                <hr class="menu-sep">
                <button type="button" class="menu-item" role="menuitem" onclick="closeAllMenus(); openProfileCreator()">👤  New Profile...</button>
                <button type="button" class="menu-item" role="menuitem" onclick="closeAllMenus(); openProfilePicker()">👥  Switch User...</button>
                <hr class="menu-sep">
                <button type="button" class="menu-item" role="menuitem" onclick="closeAllMenus(); pywebview.api.open_app_data_folder()">📂  Open App Data Folder</button>
                <hr class="menu-sep">
                <button type="button" class="menu-item" role="menuitem" onclick="closeAllMenus(); window.close()">❌  Exit</button>
            </div>

            <button type="button" class="menu-btn" id="mBtnSettings" role="menuitem" aria-haspopup="menu" aria-expanded="false" popovertarget="menuSettings" tabindex="-1">Settings</button>
            <div class="menu-dropdown" id="menuSettings" popover="auto" role="menu" aria-labelledby="mBtnSettings">
                <button type="button" class="menu-item" role="menuitem" id="optAutoLogin" onclick="toggleSetting('auto_login')">Auto-Login: Enabled</button>
                <button type="button" class="menu-item" role="menuitem" id="optAutoUpdate" onclick="toggleSetting('auto_update')">Auto-Update: Enabled</button>
                <hr class="menu-sep">
                <button type="button" class="menu-item" role="menuitem" id="optShowPR" onclick="toggleSetting('show_pr')">Show PRs: ON</button>
                <button type="button" class="menu-item" role="menuitem" id="optShowStandards" onclick="toggleSetting('show_standards')">Show Standards: ON</button>
                <button type="button" class="menu-item" role="menuitem" id="optShowMilestones" onclick="toggleSetting('show_milestones')">Show Milestones: ON</button>
            </div>

            <button type="button" class="menu-btn" id="mBtnProfiles" role="menuitem" aria-haspopup="menu" aria-expanded="false" popovertarget="menuProfiles" tabindex="-1">Profiles</button>
            <div class="menu-dropdown" id="menuProfiles" popover="auto" role="menu" aria-labelledby="mBtnProfiles">
                <!-- Dynamically injected -->
            </div>

            <button type="button" class="menu-btn" id="mBtnExp" role="menuitem" aria-haspopup="menu" aria-expanded="false" popovertarget="menuExp" tabindex="-1">🧪 Experimental</button>
            <div class="menu-dropdown" id="menuExp" popover="auto" role="menu" aria-labelledby="mBtnExp">
                <button type="button" class="menu-item" role="menuitem" onclick="closeAllMenus(); runBodymassPrefill()">📅  Prefill Mass Dates</button>
                <button type="button" class="menu-item" role="menuitem" onclick="closeAllMenus(); openMissingMassesModal()">⚖️  Fill-in Missing Masses</button>
                <hr class="menu-sep">
                <button type="button" class="menu-item" role="menuitem" onclick="closeAllMenus(); runValidateSessions()">✅  Validate sessions.py</button>
            </div>
        </div>
    </nav>

    <!-- ── APP LAYOUT ──────────────────────────────────────────────────── -->
    <div class="app-body">
        <!-- ── 1. LEFT SIDEBAR ─────────────────────────────────────────── -->
        <aside>
            <!-- Athlete Profile Pill -->
            <button type="button" class="profile-card" onclick="openProfilePicker()" title="Click to manage or switch athlete profiles">
                <div class="profile-avatar" id="avatarLetter" aria-hidden="true">R</div>
                <div class="profile-info">
                    <div class="prof-name" id="sidebarProfName">Rustem</div>
                    <div class="prof-badge"><span class="prof-dot" aria-hidden="true"></span> Active Athlete</div>
                </div>
            </button>

            <!-- Primary Action Buttons -->
            <button type="button" class="btn-side-primary1" onclick="generateExcel()">
                <span aria-hidden="true">🚀</span> Generate Excel Log
            </button>
            <button type="button" class="btn-side-primary2" onclick="openPlanCycler()">
                <span aria-hidden="true">🗓️</span> Plan Next Cycle
            </button>
            <button type="button" class="btn-side-primary3" onclick="pywebview.api.open_latest_excel()">
                <span aria-hidden="true">📂</span> Open Latest Log
            </button>

            <div class="divider"></div>

            <!-- Secondary Action Buttons -->
            <button type="button" class="btn-side-sec" onclick="pywebview.api.edit_sessions()">
                <span aria-hidden="true">📝</span> Edit Sessions
            </button>
            <button type="button" class="btn-side-sec" onclick="pywebview.api.open_output()">
                <span aria-hidden="true">📊</span> Output Folder
            </button>
            <button type="button" class="btn-side-sec" onclick="openStandardsModal()">
                <span aria-hidden="true">📚</span> Exercise Library
            </button>
            <button type="button" class="btn-side-sec" onclick="runScraper()">
                <span aria-hidden="true">⚡</span> Run Scraper
            </button>

            <!-- Bottom Status Indicator -->
            <div class="side-status-box">
                <div class="side-status" id="sidebarStatus" role="status" aria-live="polite">● System Ready</div>
                <div class="side-last-gen" id="sidebarLastGen"></div>
            </div>
        </aside>

        <!-- ── 2. MAIN CONTENT AREA ────────────────────────────────────── -->
        <main>
            <div class="main-header">
                <div class="header-left">
                    <div class="main-title">Recent Sessions</div>
                    <div class="main-sub">Training progression overview &amp; strength trajectory</div>
                </div>
                <button type="button" class="btn-refresh" onclick="loadDashboard()">
                    <span aria-hidden="true">↻</span> Refresh
                </button>
            </div>

            <!-- 3 Stats Metric Cards -->
            <div class="stats-row">
                <div class="stat-card">
                    <div class="stat-header">
                        <div class="stat-t">Gym Attendance</div>
                        <div class="stat-icon-badge" style="background: rgba(37, 99, 235, 0.2); color: #60A5FA;" aria-hidden="true">🔥</div>
                    </div>
                    <div class="stat-v" id="c1Val">-- Days</div>
                    <div class="stat-s" id="c1Sub">-- this year · -- this month</div>
                </div>

                <button type="button" class="stat-card clickable" onclick="openSplitModal()" title="Click to view full training split routine &amp; history">
                    <div class="stat-header">
                        <div class="stat-t">Current Split Duration</div>
                        <div class="stat-icon-badge" style="background: rgba(124, 58, 237, 0.2); color: #C084FC;" aria-hidden="true">⚡</div>
                    </div>
                    <div class="stat-v" id="c2Val">-- Weeks</div>
                    <div class="stat-s" id="c2Sub">N-Day Split · started --</div>
                </button>

                <div class="stat-card">
                    <div class="stat-header">
                        <div class="stat-t">Last Workout</div>
                        <div class="stat-icon-badge" style="background: rgba(245, 158, 11, 0.2); color: #FBBF24;" aria-hidden="true">🏆</div>
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

    <!-- ── 3. HOVER STANDARDS TOOLTIP (Top-Layer Popover) ──────────────── -->
    <div id="standardsTooltip" popover="manual" role="tooltip"></div>

    <!-- ── 3b. TOAST NOTIFICATIONS REGION & LIVE ANNOUNCER ─────────────── -->
    <div id="toastRegion" class="toast-region" role="region" aria-label="Notifications"></div>
    <p class="sr-only">Screen reader notifications</p>
    <div id="srAnnouncer" class="sr-only" aria-live="polite" aria-atomic="true"></div>

    <!-- ── 4. STRENGTH STANDARDS DIALOG ────────────────────────────────── -->
    <dialog id="modalStandards" class="app-dialog" closedby="any" aria-labelledby="standardsTitle" style="width: 880px;">
        <div class="modal-hdr">
            <h1 class="modal-title" id="standardsTitle">Strength Standards Library</h1>
            <div class="modal-sub">Browse benchmark lift targets for all 280+ strength exercises</div>
            <div style="margin-top: 12px; display: flex; gap: 8px;">
                <input type="search" id="stdSearchInput" class="plan-input" placeholder="🔍  Search exercises by name or slug in real-time..." aria-label="Search exercises" style="flex: 1;" oninput="filterStandards(this.value)" autofocus>
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
        <form method="dialog" class="modal-footer">
            <button type="submit" class="btn-tool" style="padding: 8px 18px; margin-left: auto;">Close</button>
        </form>
    </dialog>

    <!-- ── 5. SPLIT DETAILS DIALOG ─────────────────────────────────────── -->
    <dialog id="modalSplit" class="app-dialog" closedby="any" aria-labelledby="splitTitle" style="width: 660px;">
        <div class="modal-hdr">
            <h1 class="modal-title" id="splitTitle">Current Split Details &amp; History</h1>
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
        <form method="dialog" class="modal-footer">
            <button type="submit" class="btn-tool" style="padding: 8px 18px; margin-left: auto;" autofocus>Close</button>
        </form>
    </dialog>

    <!-- ── 6. ABOUT DIALOG ─────────────────────────────────────────────── -->
    <dialog id="modalAbout" class="app-dialog" closedby="any" aria-labelledby="aboutTitle" style="width: 400px;">
        <div class="modal-hdr" style="text-align: center;">
            <h1 class="modal-title" id="aboutTitle">Iron Log</h1>
            <div class="modal-sub" id="aboutVerText">Version {__version__}</div>
        </div>
        <div class="modal-body" style="text-align: center; gap: 10px; padding: 24px 20px;">
            <div style="font-size: 14px; color: var(--text-secondary);">Designed &amp; built by Rustem Nizamov</div>
            <div style="font-size: 12px; color: var(--text-muted);">High-Performance Local Strength &amp; Progressive Overload Suite</div>
            <button type="button" class="btn-side-sec" style="margin: 14px auto 0 auto; justify-content: center; width: 190px;" onclick="pywebview.api.open_url('https://github.com/Rusya665/iron-log')">GitHub Repository ↗</button>
        </div>
        <form method="dialog" class="modal-footer">
            <button type="submit" class="btn-tool" style="padding: 8px 18px; margin-left: auto;" autofocus>Close</button>
        </form>
    </dialog>

    <!-- ── 7. PROFILE PICKER DIALOG ────────────────────────────────────── -->
    <dialog id="modalProfilePicker" class="app-dialog" closedby="any" aria-labelledby="pickerTitle" style="width: 540px;">
        <div class="modal-hdr">
            <h1 class="modal-title" id="pickerTitle">Select Your Profile</h1>
            <div class="modal-sub">Switch active athlete account</div>
        </div>
        <div class="modal-body">
            <div id="profilePickerList" style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px;"></div>
        </div>
        <div class="modal-footer">
            <button type="button" class="btn-side-primary2" style="padding: 8px 14px;" onclick="openProfileCreator()">+ New Profile</button>
            <button type="button" class="btn-tool" style="padding: 8px 18px; margin-left: auto;" onclick="closeModal('modalProfilePicker')">Close</button>
        </div>
    </dialog>

    <!-- ── 8. PROFILE CREATOR / EDITOR DIALOG ──────────────────────────── -->
    <dialog id="modalProfileCreator" class="app-dialog" aria-labelledby="profModalTitle" style="width: 500px;">
        <div class="modal-hdr">
            <h1 class="modal-title" id="profModalTitle">Create Profile</h1>
        </div>
        <div class="modal-body" style="gap: 12px;">
            <input type="hidden" id="profEditIndex" value="-1">
            <div>
                <label for="profNameInput" style="font-size: 12px; color: var(--text-secondary); display: block; margin-bottom: 4px;">Name:</label>
                <input type="text" id="profNameInput" class="plan-input" style="width: 100%;" placeholder="e.g. Rustem" required autofocus>
            </div>
            <fieldset style="border: none; padding: 0;">
                <legend style="font-size: 12px; color: var(--text-secondary); margin-bottom: 4px;">Sex:</legend>
                <div style="display: flex; gap: 20px; font-size: 13px;">
                    <label style="display: flex; align-items: center; gap: 6px; cursor: pointer;">
                        <input type="radio" name="profSex" value="male" id="sexMale" checked> Male
                    </label>
                    <label style="display: flex; align-items: center; gap: 6px; cursor: pointer;">
                        <input type="radio" name="profSex" value="female" id="sexFemale"> Female
                    </label>
                </div>
            </fieldset>
            <div>
                <label for="profDirInput" style="font-size: 12px; color: var(--text-secondary); display: block; margin-bottom: 4px;">Data Folder (sessions.py location):</label>
                <div style="display: flex; gap: 8px;">
                    <input type="text" id="profDirInput" class="plan-input" style="flex: 1;" placeholder="C:/path/to/folder" required>
                    <button type="button" class="btn-tool" onclick="browseFolder()">Browse...</button>
                </div>
                <div style="font-size: 11px; color: var(--text-muted); margin-top: 4px;">Each user needs their own folder. Excel logs will be saved in a 'gym' subfolder.</div>
            </div>
        </div>
        <div class="modal-footer">
            <button type="button" class="btn-tool" style="padding: 8px 16px;" onclick="closeModal('modalProfileCreator')">Cancel</button>
            <button type="button" class="btn-side-primary3" style="padding: 8px 18px; margin-left: auto;" onclick="saveProfileForm()">Save Profile</button>
        </div>
    </dialog>

    <!-- ── 9. FILL-IN MISSING MASSES DIALOG ────────────────────────────── -->
    <dialog id="modalMissingMasses" class="app-dialog" aria-labelledby="missingMassesTitle" style="width: 440px;">
        <div class="modal-hdr">
            <h1 class="modal-title" id="missingMassesTitle">Fill-in Missing Masses</h1>
            <div class="modal-sub">Enter body mass values for workout dates where mass is None.</div>
        </div>
        <div class="modal-body" id="missingMassesContainer" style="max-height: 50vh;"></div>
        <div class="modal-footer">
            <button type="button" class="btn-tool" style="padding: 8px 16px;" onclick="closeModal('modalMissingMasses')">Cancel</button>
            <button type="button" class="btn-side-primary3" style="padding: 8px 18px; margin-left: auto;" onclick="saveMissingMasses()">💾 Save Mass Values</button>
        </div>
    </dialog>

    <!-- ── 10. SOFTWARE UPDATE DIALOG ──────────────────────────────────── -->
    <dialog id="modalUpdate" class="app-dialog" aria-labelledby="updateModalTitle" style="width: 520px;">
        <div class="modal-hdr">
            <h1 class="modal-title" id="updateModalTitle">🚀 Software Update Available</h1>
            <div class="modal-sub" id="updateModalSub">A new version of Iron Log is ready to install</div>
        </div>
        <div class="modal-body" style="gap: 14px; padding: 20px 24px;">
            <div style="display: flex; align-items: center; justify-content: space-between; background: rgba(255, 255, 255, 0.04); padding: 12px 18px; border-radius: var(--radius-md); border: 1px solid rgba(255, 255, 255, 0.08);">
                <div>
                    <div style="font-size: 11px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px;">Current Version</div>
                    <div style="font-size: 15px; font-weight: 700; color: var(--text-secondary); font-family: 'JetBrains Mono', monospace;" id="updateCurrentVer">v{__version__}</div>
                </div>
                <div style="font-size: 18px; color: #60A5FA;" aria-hidden="true">➔</div>
                <div>
                    <div style="font-size: 11px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px;">New Version</div>
                    <div style="font-size: 16px; font-weight: 800; color: #4ADE80; font-family: 'JetBrains Mono', monospace;" id="updateNewVer">v-.-.-</div>
                </div>
            </div>

            <div id="updateNotesSection" style="display: flex; flex-direction: column; gap: 6px;">
                <div style="font-size: 12px; font-weight: 700; color: var(--text-secondary);">Release Notes:</div>
                <div id="updateReleaseNotes" style="font-size: 12px; color: #CBD5E1; background: rgba(0, 0, 0, 0.3); border: 1px solid rgba(255, 255, 255, 0.06); border-radius: var(--radius-sm); padding: 10px 12px; max-height: 120px; overflow-y: auto; font-family: 'JetBrains Mono', monospace; white-space: pre-wrap; line-height: 1.5;"></div>
            </div>

            <!-- Progress Section (shown during download) -->
            <div id="updateProgressSection" style="display: none; flex-direction: column; gap: 8px;">
                <div style="display: flex; justify-content: space-between; font-size: 12px;">
                    <span id="updateProgressStatus" role="status" aria-live="polite" style="color: #60A5FA; font-weight: 600;">Downloading update...</span>
                    <span id="updateProgressPercent" style="color: #FFFFFF; font-family: 'JetBrains Mono', monospace; font-weight: 700;">0%</span>
                </div>
                <progress id="updateProgressBar" class="update-progress" max="100" value="0" aria-labelledby="updateProgressStatus"></progress>
                <div id="updateProgressDetails" style="font-size: 11px; color: var(--text-muted); font-family: 'JetBrains Mono', monospace; text-align: right;">0.0 MB / 0.0 MB</div>
            </div>

            <div id="updateErrorBox" role="alert" style="display: none; background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.3); color: #FCA5A5; padding: 10px 14px; border-radius: var(--radius-sm); font-size: 12px; line-height: 1.4;"></div>

            <div id="updateInfoMessage" style="font-size: 11px; color: var(--text-muted); line-height: 1.5;">
                Iron Log will download the setup file in the background, close automatically, silently install the new version, and restart itself. All your logs, profiles, and data will be safely preserved.
            </div>
        </div>
        <div class="modal-footer" id="updateModalFooter">
            <button type="button" class="btn-tool" style="padding: 8px 18px;" id="btnUpdateLater" onclick="dismissUpdateModal()">Remind Me Later</button>
            <button type="button" class="btn-side-primary1" style="padding: 8px 22px; margin-left: auto; width: auto;" id="btnUpdateNow" onclick="startUpdateInstall()">
                ⚡ Update &amp; Restart
            </button>
        </div>
    </dialog>

    <!-- ── 11. DESTRUCTIVE CONFIRMATION DIALOG ─────────────────────────── -->
    <dialog id="modalConfirm" class="app-dialog" closedby="any" aria-labelledby="confirmTitle" style="width: 400px;">
        <div class="modal-hdr">
            <h1 class="modal-title" id="confirmTitle">Confirm Action</h1>
        </div>
        <div class="modal-body">
            <p id="confirmMessage" style="font-size: 13px; color: var(--text-secondary); line-height: 1.5;"></p>
        </div>
        <form method="dialog" class="modal-footer">
            <button type="submit" value="cancel" class="btn-tool" style="padding: 8px 16px;" autofocus>Cancel</button>
            <button type="submit" value="confirm" id="confirmActionBtn" class="btn-danger" style="margin-left: auto;">Delete</button>
        </form>
    </dialog>

    <script>
        let cachedStats = {{}};
        let windowBlurred = false;
        const activeToasts = [];
        const copyTimers = new WeakMap();

        function escapeHtml(str) {{
            if (str === null || str === undefined) return "";
            return String(str)
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;")
                .replace(/"/g, "&quot;")
                .replace(/'/g, "&#039;");
        }}

        function announceSR(text) {{
            if (!text) return;
            if (typeof document.ariaNotify === "function") {{
                try {{
                    document.ariaNotify(text);
                    return;
                }} catch (_e) {{}}
            }}
            const el = document.getElementById("srAnnouncer");
            if (el) {{
                el.textContent = "";
                requestAnimationFrame(() => {{ el.textContent = text; }});
            }}
        }}

        /* ── Top-Layer Toast Notifications (popover="manual") ────────────── */
        function reflowToasts() {{
            let offset = 18;
            for (let i = activeToasts.length - 1; i >= 0; i--) {{
                const item = activeToasts[i];
                item.el.style.setProperty("--toast-offset", offset + "px");
                offset += (item.el.offsetHeight || 56) + 10;
            }}
        }}

        function dismissToast(entry) {{
            const idx = activeToasts.indexOf(entry);
            if (idx === -1) return;
            clearTimeout(entry.timer);
            activeToasts.splice(idx, 1);
            try {{
                if (entry.el.matches(":popover-open")) entry.el.hidePopover();
            }} catch (_e) {{}}
            setTimeout(() => entry.el.remove(), 240);
            reflowToasts();
        }}

        function showToast(message, variant = "info", durationMs = 5200) {{
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

            const entry = {{ el: toast, timer: null, paused: false }};
            activeToasts.push(entry);

            const startTimer = () => {{
                if (durationMs <= 0 || entry.paused) return;
                clearTimeout(entry.timer);
                entry.timer = setTimeout(() => dismissToast(entry), durationMs);
            }};

            closeBtn.addEventListener("click", () => dismissToast(entry));
            toast.addEventListener("pointerenter", () => {{ entry.paused = true; clearTimeout(entry.timer); }});
            toast.addEventListener("pointerleave", () => {{ entry.paused = false; startTimer(); }});
            toast.addEventListener("focusin", () => {{ entry.paused = true; clearTimeout(entry.timer); }});
            toast.addEventListener("focusout", () => {{ entry.paused = false; startTimer(); }});

            try {{
                toast.showPopover();
            }} catch (_e) {{
                toast.style.display = "flex";
            }}
            reflowToasts();
            announceSR(message);
            startTimer();
        }}

        /* ── Native Dialog Helpers ───────────────────────────────────────── */
        function openModal(id) {{
            const dlg = document.getElementById(id);
            if (!dlg) return;
            if (typeof dlg.showModal === "function") {{
                if (!dlg.open) dlg.showModal();
            }} else {{
                dlg.setAttribute("open", "");
            }}
        }}

        function closeModal(id) {{
            const dlg = document.getElementById(id);
            if (!dlg) return;
            if (typeof dlg.close === "function" && dlg.open) {{
                dlg.close();
            }} else {{
                dlg.removeAttribute("open");
            }}
        }}

        function confirmDialog(title, message, confirmLabel = "Confirm") {{
            return new Promise((resolve) => {{
                const dlg = document.getElementById("modalConfirm");
                document.getElementById("confirmTitle").textContent = title;
                document.getElementById("confirmMessage").textContent = message;
                document.getElementById("confirmActionBtn").textContent = confirmLabel;
                dlg.returnValue = "";
                const onClose = () => {{
                    const accepted = dlg.returnValue === "confirm";
                    dlg.returnValue = "";
                    resolve(accepted);
                }};
                dlg.addEventListener("close", onClose, {{ once: true }});
                openModal("modalConfirm");
            }});
        }}

        /* ── Menubar Keyboard & Popover Coordination ─────────────────────── */
        function closeAllMenus() {{
            document.querySelectorAll(".menu-dropdown[popover]").forEach((m) => {{
                try {{
                    if (m.matches(":popover-open")) m.hidePopover();
                }} catch (_e) {{}}
            }});
        }}

        function setupMenubar() {{
            const bar = document.querySelector('[role="menubar"]');
            if (!bar) return;
            const triggers = [...bar.querySelectorAll(':scope > button[popovertarget]')];
            const supportsAnchor = CSS.supports("position-area", "block-end");

            window.addEventListener("blur", () => {{ windowBlurred = true; }});
            window.addEventListener("focus", () => {{ setTimeout(() => {{ windowBlurred = false; }}, 0); }});

            const getMenu = (btn) => document.getElementById(btn.getAttribute("popovertarget"));
            const isMenuOpen = (menu) => menu && menu.matches(":popover-open");
            const positionFallback = (btn, menu) => {{
                if (supportsAnchor) return;
                const r = btn.getBoundingClientRect();
                menu.style.left = Math.min(r.left, Math.max(8, window.innerWidth - menu.offsetWidth - 8)) + "px";
                menu.style.top = (r.bottom + 4) + "px";
            }};

            const moveRoot = (fromBtn, dir) => {{
                const next = triggers[(triggers.indexOf(fromBtn) + dir + triggers.length) % triggers.length];
                triggers.forEach((t) => {{ t.tabIndex = t === next ? 0 : -1; }});
                closeAllMenus();
                next.focus({{ preventScroll: true }});
                const nextMenu = getMenu(next);
                if (nextMenu) {{
                    try {{ nextMenu.showPopover({{ source: next }}); }} catch (_e) {{ nextMenu.showPopover(); }}
                    positionFallback(next, nextMenu);
                }}
            }};

            triggers.forEach((btn) => {{
                const menu = getMenu(btn);
                if (!menu) return;

                menu.addEventListener("toggle", (e) => {{
                    const open = e.newState === "open";
                    btn.setAttribute("aria-expanded", String(open));
                    if (open) positionFallback(btn, menu);
                }});

                btn.addEventListener("pointerenter", () => {{
                    const anyOpen = triggers.some((t) => isMenuOpen(getMenu(t)));
                    if (anyOpen && !isMenuOpen(menu)) {{
                        closeAllMenus();
                        btn.focus({{ preventScroll: true, focusVisible: false }});
                        try {{ menu.showPopover({{ source: btn }}); }} catch (_e) {{ menu.showPopover(); }}
                        positionFallback(btn, menu);
                    }}
                }});

                btn.addEventListener("keydown", (e) => {{
                    if (e.key === "ArrowRight") {{
                        e.preventDefault();
                        moveRoot(btn, 1);
                    }} else if (e.key === "ArrowLeft") {{
                        e.preventDefault();
                        moveRoot(btn, -1);
                    }} else if (e.key === "ArrowDown" || e.key === "Home" || e.key === "End") {{
                        e.preventDefault();
                        if (!isMenuOpen(menu)) {{
                            try {{ menu.showPopover({{ source: btn }}); }} catch (_e) {{ menu.showPopover(); }}
                            positionFallback(btn, menu);
                        }}
                        const items = [...menu.querySelectorAll('button.menu-item:not(:disabled)')];
                        if (items.length) {{
                            (e.key === "End" ? items[items.length - 1] : items[0]).focus({{ preventScroll: true }});
                        }}
                    }}
                }});

                menu.addEventListener("keydown", (e) => {{
                    const items = [...menu.querySelectorAll('button.menu-item:not(:disabled)')];
                    const idx = items.indexOf(document.activeElement);
                    if (e.key === "ArrowDown") {{
                        e.preventDefault();
                        if (items.length) items[(idx + 1) % items.length].focus({{ preventScroll: true }});
                    }} else if (e.key === "ArrowUp") {{
                        e.preventDefault();
                        if (items.length) items[(idx - 1 + items.length) % items.length].focus({{ preventScroll: true }});
                    }} else if (e.key === "Home") {{
                        e.preventDefault();
                        if (items.length) items[0].focus({{ preventScroll: true }});
                    }} else if (e.key === "End") {{
                        e.preventDefault();
                        if (items.length) items[items.length - 1].focus({{ preventScroll: true }});
                    }} else if (e.key === "ArrowRight") {{
                        e.preventDefault();
                        moveRoot(btn, 1);
                    }} else if (e.key === "ArrowLeft") {{
                        e.preventDefault();
                        moveRoot(btn, -1);
                    }} else if (e.key === "Tab") {{
                        closeAllMenus();
                    }}
                }});
            }});
        }}

        function setupDialogLightDismissFallback() {{
            if ("closedBy" in HTMLDialogElement.prototype) return;
            const outside = (e, dialog) => {{
                const r = dialog.getBoundingClientRect();
                return e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom;
            }};
            for (const dialog of document.querySelectorAll('dialog[closedby="any"]')) {{
                let pressedOutside = false;
                dialog.addEventListener("pointerdown", (e) => {{ pressedOutside = outside(e, dialog); }});
                dialog.addEventListener("pointerup", (e) => {{
                    if (pressedOutside && outside(e, dialog)) dialog.close();
                }});
            }}
        }}

        async function init() {{
            try {{
                setupMenubar();
                setupDialogLightDismissFallback();
                await loadDashboard();
                await updateMenuState();

                // If no profiles exist, automatically open profile creation modal
                const pData = await pywebview.api.get_profiles();
                if (!pData.profiles || pData.profiles.length === 0) {{
                    openProfileCreator();
                }}

                // Automatically check for updates on startup (after 1.2s so dashboard loads first)
                setTimeout(() => {{
                    checkAutoUpdate();
                }}, 1200);

                // Periodic check every 30 minutes
                setInterval(() => {{
                    checkAutoUpdate();
                }}, 30 * 60 * 1000);
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
                const item = document.createElement("button");
                item.type = "button";
                item.className = "menu-item";
                item.setAttribute("role", "menuitem");
                item.style.fontWeight = isActive ? "700" : "500";
                item.innerHTML = `<span>${{isActive ? '✓ ' : ''}}${{escapeHtml(p.name)}}</span><span style="font-size: 10px; color: var(--text-muted);">Select</span>`;
                item.onclick = async () => {{
                    closeAllMenus();
                    await pywebview.api.select_profile(idx);
                    await loadDashboard();
                    await updateMenuState();
                }};
                profMenu.appendChild(item);
            }});
            const sep = document.createElement("hr");
            sep.className = "menu-sep";
            profMenu.appendChild(sep);

            const manageBtn = document.createElement("button");
            manageBtn.type = "button";
            manageBtn.className = "menu-item";
            manageBtn.setAttribute("role", "menuitem");
            manageBtn.textContent = "👥  Manage Profiles...";
            manageBtn.onclick = () => {{
                closeAllMenus();
                openProfilePicker();
            }};
            profMenu.appendChild(manageBtn);
        }}

        async function toggleSetting(settingName) {{
            await pywebview.api.toggle_setting(settingName);
            await updateMenuState();
            if (settingName === "auto_update") {{
                const settings = await pywebview.api.get_settings();
                if (settings.auto_update) {{
                    checkAutoUpdate();
                }}
            }}
        }}

        async function loadDashboard() {{
            if (!window.pywebview || !window.pywebview.api) return;
            document.getElementById("sidebarStatus").innerText = "● Loading...";
            const data = await pywebview.api.get_active_data();
            if (!data.success) {{
                document.getElementById("sidebarStatus").innerText = "● " + (data.error || "Error");
                document.getElementById("c1Val").innerText = "-- Days";
                document.getElementById("c1Sub").innerText = "-- this year · -- this month";
                document.getElementById("c2Val").innerText = "-- Wks";
                document.getElementById("c2Sub").innerText = "--";
                document.getElementById("c3Val").innerText = "--";
                document.getElementById("c3Sub").innerText = "--";
                const container = document.getElementById("sessionsGrid");
                if (container) {{
                    const isNoProf = (data.error === "No profile selected" || data.error === "No active profile");
                    const errTitle = isNoProf ? "No Profile Selected" : "Failed to Load sessions.py";
                    const editBtn = isNoProf ? "" : `
                        <button type="button" class="btn-side-sec" style="display: inline-flex; align-items: center; gap: 8px; padding: 10px 20px; font-weight: 600;" onclick="pywebview.api.edit_sessions()">
                            <span>✏️</span> Open in Editor
                        </button>
                    `;
                    container.innerHTML = `
                        <div style="width: 100%; background: rgba(239, 68, 68, 0.08); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: var(--radius-lg); padding: 32px; text-align: center; box-sizing: border-box;">
                            <div style="font-size: 36px; margin-bottom: 12px;">⚠️</div>
                            <div style="font-size: 16px; font-weight: 700; color: #f87171; margin-bottom: 8px;">${{errTitle}}</div>
                            <div style="font-size: 13px; color: #e2e8f0; font-family: 'JetBrains Mono', monospace; background: rgba(0,0,0,0.3); padding: 12px 16px; border-radius: 8px; margin: 12px auto 20px auto; max-width: 650px; text-align: left; word-break: break-all; white-space: pre-wrap;">${{escapeHtml(data.error)}}</div>
                            <div style="display: flex; gap: 12px; justify-content: center; flex-wrap: wrap;">
                                ${{editBtn}}
                                <button type="button" class="btn-side-primary2" style="display: inline-flex; align-items: center; gap: 8px; padding: 10px 20px; font-weight: 600;" onclick="openProfilePicker()">
                                    <span>📁</span> Manage Profile / Select Folder
                                </button>
                                <button type="button" class="btn-refresh" style="display: inline-flex; align-items: center; gap: 8px; padding: 10px 20px;" onclick="loadDashboard()">
                                    <span>🔄</span> Retry
                                </button>
                            </div>
                        </div>
                    `;
                }}
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
                    const safeExId = escapeHtml(ex.id).replace(/'/g, "&#39;");
                    exsHtml += `
                        <div class="ex-item">
                            <button type="button" class="ex-name" onmouseenter="showTooltip(event, '${{safeExId}}', ${{sess.mass || 0}}, ${{ex.max_lift || 0}}, ${{isPR}}, ${{Boolean(ex.is_weighted)}})" onmouseleave="hideTooltip()" onfocus="showTooltip(event, '${{safeExId}}', ${{sess.mass || 0}}, ${{ex.max_lift || 0}}, ${{isPR}}, ${{Boolean(ex.is_weighted)}})" onblur="hideTooltip()">${{escapeHtml(ex.name)}}</button>
                            <span class="ex-meta">${{escapeHtml(ex.summary)}}</span>
                        </div>
                    `;
                }});

                const dayLabel = typeof sess.day === 'number' ? `Day ${{sess.day}}` : `${{escapeHtml(sess.day)}}`;
                card.innerHTML = `
                    <div class="workout-card-hdr">
                        <span class="hdr-date">📅  ${{escapeHtml(sess.date)}}</span>
                        <span class="hdr-pill">${{dayLabel}}</span>
                    </div>
                    <div class="card-sep"></div>
                    <div class="ex-list">${{exsHtml}}</div>
                `;
                grid.appendChild(card);
            }});

            document.getElementById("sidebarStatus").innerText = "● System Ready";
        }}

        /* ── Hover Standards Tooltip (Anchor-Positioned Popover) ─────────── */
        let tooltipTimer = null;
        let activeAnchorEl = null;

        async function showTooltip(e, exId, userMass, userLift, isPR, isWeighted = false) {{
            clearTimeout(tooltipTimer);
            const triggerEl = e.currentTarget;
            const fallbackX = (e.clientX || (triggerEl.getBoundingClientRect().left + 12)) + 14;
            const fallbackY = (e.clientY || (triggerEl.getBoundingClientRect().bottom + 6)) + 14;

            tooltipTimer = setTimeout(async () => {{
                const tableData = await pywebview.api.get_exercise_standards_table(exId, userMass, isWeighted);
                const tip = document.getElementById("standardsTooltip");
                if (!tip) return;

                if (activeAnchorEl && activeAnchorEl !== triggerEl) {{
                    activeAnchorEl.removeAttribute("data-active-anchor");
                }}
                activeAnchorEl = triggerEl;
                activeAnchorEl.setAttribute("data-active-anchor", "");

                if (!tableData || !tableData.standards || Object.keys(tableData.standards).length === 0) {{
                    tip.innerHTML = `<div style="font-size: 11px; color: var(--text-secondary);">Standards not available for ${{escapeHtml(tableData?.name || exId)}}</div>`;
                }} else {{
                    let rowsHtml = "";
                    const targetBm = tableData.target_bm;
                    const unitSuffix = tableData.unit === "reps" ? " (Reps)" : " (kg)";

                    for (const [bm, levels] of Object.entries(tableData.standards)) {{
                        const isUserBm = Boolean(targetBm && parseInt(bm) === targetBm);
                        let cells = `<td>${{escapeHtml(bm)}}kg</td>`;
                        for (const lvl of ["Beginner", "Novice", "Intermediate", "Advanced", "Elite"]) {{
                            const val = levels[lvl] !== undefined ? levels[lvl] : "-";
                            const achieved = isPR && typeof val === 'number' && userLift >= val;
                            cells += `<td class="${{achieved ? 'achieved' : ''}}">${{escapeHtml(val)}}</td>`;
                        }}
                        rowsHtml += `<tr class="${{isUserBm ? 'user-mass-row' : ''}}">${{cells}}</tr>`;
                    }}

                    tip.innerHTML = `
                        <div style="font-size: 12px; font-weight: 700; margin-bottom: 6px; color: #FFF; font-family: 'Outfit', sans-serif;">${{escapeHtml(tableData.name)}} Standards${{unitSuffix}}</div>
                        <table>
                            <thead><tr><th>Mass</th><th>Beg</th><th>Nov</th><th>Int</th><th>Adv</th><th>Eli</th></tr></thead>
                            <tbody>${{rowsHtml}}</tbody>
                        </table>
                    `;
                }}

                if (!CSS.supports("position-area", "block-end")) {{
                    tip.style.left = Math.min(fallbackX, Math.max(8, window.innerWidth - 410)) + "px";
                    tip.style.top = Math.min(fallbackY, Math.max(8, window.innerHeight - 260)) + "px";
                }}

                try {{
                    if (!tip.matches(":popover-open")) tip.showPopover();
                }} catch (_err) {{
                    tip.style.display = "block";
                }}
            }}, 220);
        }}

        function hideTooltip() {{
            clearTimeout(tooltipTimer);
            const tip = document.getElementById("standardsTooltip");
            if (tip) {{
                try {{
                    if (tip.matches(":popover-open")) tip.hidePopover();
                }} catch (_err) {{
                    tip.style.display = "none";
                }}
            }}
            if (activeAnchorEl) {{
                activeAnchorEl.removeAttribute("data-active-anchor");
                activeAnchorEl = null;
            }}
        }}

        /* ── Actions & Dialogs ────────────────────────────────────────────── */
        async function generateExcel() {{
            document.getElementById("sidebarStatus").innerText = "● Generating Log...";
            const res = await pywebview.api.generate_excel();
            if (res.success) {{
                document.getElementById("sidebarStatus").innerText = "✅ Generated Log";
                document.getElementById("sidebarLastGen").innerText = "Last gen: " + res.time;
                showToast("Excel training log generated.", "success", 3800);
            }} else {{
                document.getElementById("sidebarStatus").innerText = "❌ " + res.error;
                showToast("Generation Error: " + res.error, "error", 7000);
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
                showToast("Strength standards scraper started.", "info", 3800);
            }} else {{
                document.getElementById("sidebarStatus").innerText = "● Scraper error: " + res.error;
                showToast("Scraper error: " + res.error, "error", 6500);
            }}
        }}

        let pendingUpdateUrl = null;
        let updateDismissed = false;
        let updatePollingTimer = null;

        function showUpdateModal(res) {{
            pendingUpdateUrl = res.url;
            document.getElementById("updateCurrentVer").innerText = "v" + (res.current || "{__version__}");
            document.getElementById("updateNewVer").innerText = "v" + (res.version || "New");
            document.getElementById("updateReleaseNotes").innerText = (res.notes || "").trim() || "Performance improvements, bug fixes, and feature updates.";

            const dlg = document.getElementById("modalUpdate");
            dlg.setAttribute("closedby", "closerequest");

            // Reset modal UI state
            document.getElementById("updateModalTitle").innerText = "🚀 Software Update Available";
            document.getElementById("updateModalSub").innerText = "A new version of Iron Log is ready to install";
            document.getElementById("updateNotesSection").style.display = "flex";
            document.getElementById("updateProgressSection").style.display = "none";
            const bar = document.getElementById("updateProgressBar");
            bar.value = 0;
            document.getElementById("updateProgressPercent").innerText = "0%";
            document.getElementById("updateProgressDetails").innerText = "";
            document.getElementById("updateErrorBox").style.display = "none";
            document.getElementById("updateErrorBox").innerText = "";
            document.getElementById("btnUpdateNow").disabled = false;
            document.getElementById("btnUpdateNow").innerText = "⚡ Update & Restart";
            document.getElementById("btnUpdateNow").style.display = "inline-flex";
            document.getElementById("btnUpdateLater").style.display = "inline-flex";

            openModal("modalUpdate");
        }}

        function dismissUpdateModal() {{
            updateDismissed = true;
            closeModal("modalUpdate");
        }}

        async function startUpdateInstall() {{
            if (!pendingUpdateUrl) {{
                showToast("Download URL not found.", "error");
                return;
            }}

            const dlg = document.getElementById("modalUpdate");
            dlg.setAttribute("closedby", "none");

            document.getElementById("btnUpdateNow").disabled = true;
            document.getElementById("btnUpdateLater").style.display = "none";
            document.getElementById("updateNotesSection").style.display = "none";
            document.getElementById("updateErrorBox").style.display = "none";
            document.getElementById("updateProgressSection").style.display = "flex";
            document.getElementById("updateModalTitle").innerText = "⚡ Updating Iron Log...";
            document.getElementById("updateModalSub").innerText = "Downloading installer...";
            document.getElementById("updateProgressStatus").innerText = "Starting download...";

            const bar = document.getElementById("updateProgressBar");
            bar.removeAttribute("value"); // Indeterminate state until first byte progress arrives

            const res = await pywebview.api.start_update(pendingUpdateUrl);
            if (!res.success) {{
                dlg.setAttribute("closedby", "closerequest");
                bar.value = 0;
                document.getElementById("updateErrorBox").style.display = "block";
                document.getElementById("updateErrorBox").innerText = "Failed to start update: " + (res.error || "Unknown error");
                document.getElementById("btnUpdateNow").disabled = false;
                document.getElementById("btnUpdateLater").style.display = "inline-flex";
                return;
            }}

            // Poll update progress every 200ms
            if (updatePollingTimer) clearInterval(updatePollingTimer);
            updatePollingTimer = setInterval(async () => {{
                try {{
                    const status = await pywebview.api.get_update_status();
                    if (status.state === "downloading") {{
                        const pct = status.percent || 0;
                        bar.value = pct;
                        document.getElementById("updateProgressPercent").innerText = pct + "%";
                        document.getElementById("updateProgressStatus").innerText = "Downloading update...";
                        const dlMB = ((status.downloaded || 0) / (1024 * 1024)).toFixed(1);
                        const totMB = ((status.total || 0) / (1024 * 1024)).toFixed(1);
                        document.getElementById("updateProgressDetails").innerText = dlMB + " MB / " + totMB + " MB";
                    }} else if (status.state === "installing") {{
                        clearInterval(updatePollingTimer);
                        bar.value = 100;
                        document.getElementById("updateProgressPercent").innerText = "100%";
                        document.getElementById("updateProgressStatus").innerText = "Download complete!";
                        document.getElementById("updateProgressDetails").innerText = "Opening Windows installer...";
                        document.getElementById("updateModalTitle").innerText = "✅ Ready to Install!";
                        document.getElementById("updateModalSub").innerText = "The setup window will now open to complete the installation.";
                    }} else if (status.state === "error") {{
                        clearInterval(updatePollingTimer);
                        dlg.setAttribute("closedby", "closerequest");
                        bar.value = 0;
                        document.getElementById("updateProgressSection").style.display = "none";
                        document.getElementById("updateErrorBox").style.display = "block";
                        document.getElementById("updateErrorBox").innerText = "Update Error: " + (status.error || "Failed to download update.");
                        document.getElementById("btnUpdateNow").disabled = false;
                        document.getElementById("btnUpdateNow").innerText = "Retry Update";
                        document.getElementById("btnUpdateLater").style.display = "inline-flex";
                    }}
                }} catch (e) {{
                    console.error("Update polling error:", e);
                }}
            }}, 200);
        }}

        async function checkAutoUpdate() {{
            if (updateDismissed) return;
            try {{
                if (!window.pywebview || !window.pywebview.api) return;
                const settings = await pywebview.api.get_settings();
                if (!settings.auto_update) return;

                const res = await pywebview.api.check_updates();
                if (res && res.has_update) {{
                    showUpdateModal(res);
                }}
            }} catch (err) {{
                console.warn("Auto update check failed:", err);
            }}
        }}

        async function triggerUpdateCheck() {{
            updateDismissed = false;
            document.getElementById("sidebarStatus").innerText = "● Checking updates...";
            try {{
                const res = await pywebview.api.check_updates();
                if (res && res.has_update) {{
                    showUpdateModal(res);
                }} else {{
                    showToast("You are on the latest version (v" + (res.current || "{__version__}") + ").", "success");
                }}
            }} catch (err) {{
                showToast("Failed to check for updates: " + err, "error", 6500);
            }}
            document.getElementById("sidebarStatus").innerText = "● System Ready";
        }}

        async function runValidateSessions() {{
            document.getElementById("sidebarStatus").innerText = "● Validating...";
            const res = await pywebview.api.run_validate_sessions();
            if (res.success) {{
                let msg = "✅ " + res.message;
                let variant = "success";
                if (res.none_mass_dates && res.none_mass_dates.length > 0) {{
                    variant = "warning";
                    msg += `\\n⚠️ ${{res.none_mass_dates.length}} BODYMASS_LOG entries have mass=None:\\n` + res.none_mass_dates.slice(0, 6).map(d => "  • " + d).join("\\n");
                    if (res.none_mass_dates.length > 6) msg += `\\n  • ...and ${{res.none_mass_dates.length - 6}} more`;
                    msg += "\\nUse Experimental > Fill-in Missing Masses to complete them.";
                }}
                showToast(msg, variant, variant === "warning" ? 9000 : 4500);
                document.getElementById("sidebarStatus").innerText = "✅ Validated";
            }} else {{
                showToast("❌ " + res.error, "error", 8000);
                document.getElementById("sidebarStatus").innerText = "❌ Validation failed";
            }}
        }}

        async function runBodymassPrefill() {{
            document.getElementById("sidebarStatus").innerText = "● Prefilling...";
            const res = await pywebview.api.run_bodymass_prefill();
            if (res.success) {{
                if (res.count === 0) {{
                    showToast("All workout dates are already present in BODYMASS_LOG. Nothing to add.", "info");
                }} else {{
                    showToast(`✅ Added ${{res.count}} date(s) to BODYMASS_LOG with mass=None in sessions.py.`, "success");
                }}
                document.getElementById("sidebarStatus").innerText = "● System Ready";
            }} else {{
                showToast("Prefill Error: " + res.error, "error", 6500);
            }}
        }}

        async function openMissingMassesModal() {{
            const res = await pywebview.api.get_missing_masses();
            if (!res.success) {{
                showToast("Error: " + res.error, "error");
                return;
            }}
            if (!res.entries || res.entries.length === 0) {{
                showToast("All Done: No missing mass entries in BODYMASS_LOG! 🎉", "success");
                return;
            }}
            const container = document.getElementById("missingMassesContainer");
            container.innerHTML = "";
            res.entries.forEach((d, idx) => {{
                const row = document.createElement("div");
                row.style.cssText = "display: flex; align-items: center; gap: 10px; margin-bottom: 8px;";
                row.innerHTML = `
                    <label for="missingMass_${{idx}}" style="font-size: 13px; width: 110px; font-family: 'JetBrains Mono', monospace;">${{escapeHtml(d)}}</label>
                    <input type="number" id="missingMass_${{idx}}" step="0.1" min="20" max="400" class="plan-input missing-mass-input" data-date="${{escapeHtml(d)}}" placeholder="e.g. 83.5" style="flex: 1;" ${{idx === 0 ? 'autofocus' : ''}}>
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
                showToast("No mass values were entered.", "warning");
                return;
            }}
            const res = await pywebview.api.save_missing_masses(updates);
            if (res.success) {{
                closeModal("modalMissingMasses");
                showToast(`✅ Updated ${{res.count}} mass value(s) in sessions.py.`, "success");
                await loadDashboard();
            }} else {{
                showToast("Error saving masses: " + res.error, "error");
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
                card.className = "stat-card";
                card.style.borderColor = isAct ? "rgba(59, 130, 246, 0.6)" : "var(--border-glass)";
                card.innerHTML = `
                    <div style="font-family: 'Outfit', sans-serif; font-weight: 700; font-size: 16px; color: ${{isAct ? '#60A5FA' : '#FFF'}};">${{escapeHtml(p.name)}}</div>
                    <div style="font-size: 11px; color: var(--text-muted); word-break: break-all;">${{escapeHtml(p.sessions_dir)}}</div>
                    <div style="display: flex; gap: 6px; margin-top: 10px;">
                        <button type="button" class="btn-tool" onclick="selectProf(${{idx}})">Select</button>
                        <button type="button" class="btn-tool" onclick="editProf(${{idx}})">Edit</button>
                        <button type="button" class="btn-tool" style="color: #F87171;" onclick="deleteProf(${{idx}})">Delete</button>
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

        async function deleteProf(idx) {{
            const data = await pywebview.api.get_profiles();
            const prof = (data.profiles || [])[idx];
            const name = prof ? prof.name : "profile";
            const ok = await confirmDialog("Delete Profile", `Are you sure you want to delete profile '${{name}}'?`, "Delete Profile");
            if (ok) {{
                await pywebview.api.delete_profile(idx);
                await openProfilePicker();
                await updateMenuState();
                showToast(`Deleted profile '${{name}}'.`, "info");
            }}
        }}

        function openProfileCreator() {{
            document.getElementById("profModalTitle").innerText = "Create New Profile";
            document.getElementById("profEditIndex").value = -1;
            document.getElementById("profNameInput").value = "";
            document.getElementById("profDirInput").value = "";
            document.getElementById("sexMale").checked = true;
            closeModal("modalProfilePicker");
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
                showToast(isEdit ? "Profile updated." : "Profile created.", "success");
            }} else {{
                showToast("Error: " + res.error, "error");
            }}
        }}

        async function copyText(txt, buttonEl = null) {{
            let ok = false;
            try {{
                if (navigator.clipboard && navigator.clipboard.writeText) {{
                    await navigator.clipboard.writeText(txt);
                    ok = true;
                }} else if (window.pywebview && window.pywebview.api) {{
                    await pywebview.api.copy_clipboard(txt);
                    ok = true;
                }}
            }} catch (_err) {{
                try {{
                    if (window.pywebview && window.pywebview.api) {{
                        await pywebview.api.copy_clipboard(txt);
                        ok = true;
                    }}
                }} catch (_e2) {{
                    ok = false;
                }}
            }}

            if (buttonEl) {{
                clearTimeout(copyTimers.get(buttonEl));
                if (!buttonEl.dataset.origLabel) {{
                    buttonEl.dataset.origLabel = buttonEl.textContent;
                }}
                buttonEl.removeAttribute("data-copied");
                buttonEl.removeAttribute("data-failed");
                void buttonEl.offsetWidth;
                buttonEl.setAttribute(ok ? "data-copied" : "data-failed", "");
                buttonEl.textContent = ok ? "✓ Copied" : "✕ Failed";
                announceSR(ok ? "Copied to clipboard" : "Copy failed");
                copyTimers.set(buttonEl, setTimeout(() => {{
                    buttonEl.removeAttribute("data-copied");
                    buttonEl.removeAttribute("data-failed");
                    buttonEl.textContent = buttonEl.dataset.origLabel;
                }}, 1800));
            }} else {{
                announceSR(ok ? "Copied to clipboard" : "Copy failed");
            }}
        }}

        /* ── Standards & Split ───────────────────────────────────────────── */
        async function openStandardsModal() {{
            await doFilterStandards("");
            openModal("modalStandards");
        }}

        let stdDebounceTimer = null;
        function filterStandards(query) {{
            clearTimeout(stdDebounceTimer);
            stdDebounceTimer = setTimeout(() => {{
                doFilterStandards(query);
            }}, 200);
        }}

        async function doFilterStandards(query) {{
            const list = await pywebview.api.search_standards(query);
            const tbody = document.getElementById("stdTbody");
            tbody.innerHTML = "";
            (list || []).forEach(item => {{
                const tr = document.createElement("tr");
                const safeName = escapeHtml(item.name);
                const safeSlug = escapeHtml(item.slug);
                const pyCode = safeSlug.replace(/-/g, '_') + ' = \\"' + safeSlug + '\\"';
                tr.innerHTML = `
                    <td style="font-weight: 600;">${{safeName}}</td>
                    <td><span class="badge-slug">${{safeSlug}}</span></td>
                    <td>${{escapeHtml(item.beg)}}</td><td>${{escapeHtml(item.nov)}}</td><td>${{escapeHtml(item.int)}}</td><td>${{escapeHtml(item.adv)}}</td><td>${{escapeHtml(item.eli)}}</td>
                    <td style="display: flex; gap: 4px;">
                        <button type="button" class="btn-tool" aria-label="Copy slug ${{safeSlug}}" onclick="copyText('${{safeSlug}}', this)">Copy</button>
                        <button type="button" class="btn-tool" aria-label="Copy Python variable for ${{safeSlug}}" onclick="copyText('${{pyCode}}', this)">Copy Py</button>
                        <button type="button" class="btn-tool" onclick="pywebview.api.open_url('https://strengthlevel.com/strength-standards/${{safeSlug}}')">View ↗</button>
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
                routineHtml += `<div style="margin-bottom: 6px;"><strong style="color: #60A5FA;">Day ${{escapeHtml(dNum)}}:</strong> ${{escapeHtml(exs.join(", "))}}</div>`;
            }}
            document.getElementById("splitOverview").innerHTML = routineHtml || "<div>Routine information loading...</div>";

            const tbody = document.getElementById("splitTbody");
            tbody.innerHTML = "";
            (s.split_sessions_details || []).forEach(sess => {{
                const tr = document.createElement("tr");
                tr.innerHTML = `
                    <td style="font-family: 'JetBrains Mono', monospace;">${{escapeHtml(sess.date_str)}}</td>
                    <td><span class="badge-slug">Day ${{escapeHtml(sess.day)}}</span></td>
                    <td>${{escapeHtml((sess.exercises || []).join(", "))}}</td>
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
