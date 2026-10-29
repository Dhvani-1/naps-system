"""NAPS Enterprise HR Frontend - Vercel Serverless UI Generator.

Generates the exact Streamlit-identical Enterprise HR web interface:
- High-contrast Enterprise styling (Inter typography, clean white layout)
- Streamlit-identical white sidebar with 6 navigation views:
  1. Dashboard
  2. Trainee Directory
  3. Add Trainee
  4. Worker & Dispatch
  5. Excel / CSV Import
  6. Audit & Exceptions
- Preserves all business logic, live date calculations, weekend shifts,
  opt-out preferences, and strict simulation delivery safeguards.
"""

def get_client_ui_html() -> str:
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NAPS Apprenticeship Management System</title>
    <!-- Google Fonts: Inter -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        /* High-contrast Enterprise Base Typography matching app.py */
        *, *::before, *::after {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        html, body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background-color: #FFFFFF;
            color: #0F172A;
            line-height: 1.5;
            -webkit-font-smoothing: antialiased;
        }

        /* App Layout Container */
        .app-layout {
            display: flex;
            min-height: 100vh;
        }

        /* Streamlit-Identical White Sidebar */
        aside.st-sidebar {
            width: 310px;
            min-width: 310px;
            background-color: #FFFFFF;
            border-right: 1px solid #E2E8F0;
            padding: 1.5rem 1.25rem;
            display: flex;
            flex-direction: column;
            position: sticky;
            top: 0;
            height: 100vh;
            overflow-y: auto;
            z-index: 50;
        }

        .sidebar-brand-title {
            font-size: 1.15rem;
            font-weight: 700;
            color: #0F172A;
            letter-spacing: -0.02em;
        }

        .sidebar-brand-sub {
            font-size: 0.775rem;
            color: #64748B;
            margin-bottom: 1.25rem;
        }

        .sidebar-section-label {
            font-size: 0.75rem;
            font-weight: 700;
            color: #64748B;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 0.5rem;
        }

        .st-divider {
            border: 0;
            border-top: 1px solid #E2E8F0;
            margin: 1.1rem 0;
        }

        /* Streamlit-Style Radio Navigation */
        .nav-radio-group {
            display: flex;
            flex-direction: column;
            gap: 2px;
            margin-bottom: 0.5rem;
        }

        .nav-radio-item {
            display: flex;
            align-items: center;
            padding: 0.55rem 0.75rem;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.875rem;
            font-weight: 500;
            color: #334155;
            transition: background 0.15s ease, color 0.15s ease;
            user-select: none;
        }

        .nav-radio-item:hover {
            background-color: #F8FAFC;
            color: #0F172A;
        }

        .nav-radio-item.active {
            background-color: #F1F5F9;
            color: #0F172A;
            font-weight: 600;
        }

        .nav-radio-bullet {
            width: 14px;
            height: 14px;
            border-radius: 50%;
            border: 2px solid #94A3B8;
            margin-right: 10px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
        }

        .nav-radio-item.active .nav-radio-bullet {
            border-color: #0F172A;
        }

        .nav-radio-item.active .nav-radio-bullet::after {
            content: '';
            width: 6px;
            height: 6px;
            background-color: #0F172A;
            border-radius: 50%;
        }

        /* Main Content Container */
        main.st-main {
            flex: 1;
            padding: 2rem 3rem 4rem 3rem;
            max-width: 1400px;
            background-color: #FFFFFF;
            overflow-y: auto;
        }

        /* Enterprise Headers */
        .app-title {
            font-size: 1.75rem;
            font-weight: 700;
            color: #0F172A;
            letter-spacing: -0.025em;
            margin-bottom: 0.2rem;
        }

        .app-subtitle {
            font-size: 0.95rem;
            color: #475569;
            margin-bottom: 1.25rem;
            line-height: 1.5;
        }

        .section-title {
            font-size: 1.25rem;
            font-weight: 700;
            color: #0F172A;
            letter-spacing: -0.015em;
            margin-top: 1rem;
            margin-bottom: 0.25rem;
        }

        .section-caption {
            font-size: 0.875rem;
            color: #64748B;
            margin-bottom: 1rem;
        }

        /* Card Panels (KPI Cards) */
        .metric-panel {
            background-color: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 8px;
            padding: 1.15rem 1.25rem;
            box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
            margin-bottom: 1rem;
        }

        .metric-panel-label {
            font-size: 0.75rem;
            font-weight: 600;
            color: #64748B;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 0.35rem;
        }

        .metric-panel-value {
            font-size: 1.75rem;
            font-weight: 700;
            color: #0F172A;
            letter-spacing: -0.02em;
        }

        .metric-panel-detail {
            font-size: 0.8rem;
            color: #475569;
            margin-top: 0.35rem;
        }

        /* Grid Layouts */
        .grid-4 {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 1rem;
            margin-bottom: 1rem;
        }

        .grid-3 {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 1rem;
            margin-bottom: 1rem;
        }

        .grid-2 {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1.25rem;
            margin-bottom: 1rem;
        }

        .grid-5-4 {
            display: grid;
            grid-template-columns: 5fr 4fr;
            gap: 1.5rem;
            margin-bottom: 1rem;
        }

        /* Status Badges */
        .badge {
            display: inline-block;
            padding: 0.25rem 0.6rem;
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            border: 1px solid transparent;
            line-height: 1.2;
        }

        .badge-active { background-color: #ECFDF5; color: #065F46; border-color: #A7F3D0; }
        .badge-left { background-color: #FFF1F2; color: #9F1239; border-color: #FECDD3; }
        .badge-completed { background-color: #EFF6FF; color: #1E40AF; border-color: #BFDBFE; }
        .badge-onroll, .badge-on_roll { background-color: #F5F3FF; color: #5B21B6; border-color: #DDD6FE; }

        .badge-sent { background-color: #ECFDF5; color: #065F46; border-color: #A7F3D0; }
        .badge-scheduled { background-color: #F1F5F9; color: #334155; border-color: #CBD5E1; }
        .badge-processing { background-color: #FEF3C7; color: #92400E; border-color: #FDE68A; }
        .badge-cancelled { background-color: #F8FAFC; color: #64748B; border-color: #E2E8F0; }
        .badge-failed { background-color: #FFF1F2; color: #9F1239; border-color: #FECDD3; }
        .badge-retrying { background-color: #FFF7ED; color: #C2410C; border-color: #FFEDD5; }
        .badge-uncertain { background-color: #FEF3C7; color: #B45309; border-color: #FDE68A; }
        .badge-admin { background-color: #0F172A; color: #FFFFFF; border-color: #0F172A; font-weight: 700; letter-spacing: 0.06em; }

        /* Clean Enterprise Buttons */
        .st-btn-primary {
            background-color: #0F172A !important;
            color: #FFFFFF !important;
            border: 1px solid #0F172A !important;
            border-radius: 6px !important;
            font-weight: 600 !important;
            font-size: 0.875rem !important;
            padding: 0.5rem 1.25rem !important;
            cursor: pointer;
            transition: background-color 0.15s ease-in-out;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
        }

        .st-btn-primary:hover {
            background-color: #1E293B !important;
            border-color: #1E293B !important;
        }

        .st-btn-secondary {
            background-color: #FFFFFF !important;
            color: #1E293B !important;
            border: 1px solid #CBD5E1 !important;
            border-radius: 6px !important;
            font-weight: 500 !important;
            font-size: 0.875rem !important;
            padding: 0.5rem 1.25rem !important;
            cursor: pointer;
            transition: background-color 0.15s ease-in-out;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
        }

        .st-btn-secondary:hover {
            background-color: #F8FAFC !important;
            border-color: #94A3B8 !important;
        }

        .st-btn-danger {
            background-color: #FFFFFF !important;
            color: #9F1239 !important;
            border: 1px solid #FECDD3 !important;
            border-radius: 6px !important;
            font-weight: 500 !important;
            font-size: 0.875rem !important;
            padding: 0.5rem 1.25rem !important;
            cursor: pointer;
        }

        .st-btn-danger:hover {
            background-color: #FFF1F2 !important;
        }

        .w-full {
            width: 100%;
        }

        /* Streamlit-Style Inputs, Selects, Checkboxes */
        .form-group {
            margin-bottom: 0.95rem;
        }

        .form-label {
            display: block;
            font-size: 0.875rem;
            font-weight: 500;
            color: #0F172A;
            margin-bottom: 0.35rem;
        }

        .form-caption {
            font-size: 0.775rem;
            color: #64748B;
            margin-top: 0.25rem;
        }

        .st-input, .st-select, .st-textarea {
            width: 100%;
            padding: 0.55rem 0.85rem;
            border: 1px solid #CBD5E1;
            border-radius: 6px;
            font-size: 0.875rem;
            font-family: inherit;
            color: #0F172A;
            background-color: #FFFFFF;
            outline: none;
            transition: border-color 0.15s ease;
        }

        .st-input:focus, .st-select:focus, .st-textarea:focus {
            border-color: #0F172A;
        }

        .st-checkbox-label {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 0.875rem;
            color: #0F172A;
            cursor: pointer;
            margin-bottom: 0.4rem;
        }

        .st-checkbox {
            width: 16px;
            height: 16px;
            accent-color: #0F172A;
            cursor: pointer;
        }

        /* Streamlit-Style Alert Boxes */
        .st-alert {
            padding: 0.85rem 1rem;
            border-radius: 6px;
            font-size: 0.85rem;
            margin-bottom: 1rem;
            border: 1px solid transparent;
        }

        .st-alert-info { background-color: #EFF6FF; color: #1E40AF; border-color: #BFDBFE; }
        .st-alert-success { background-color: #ECFDF5; color: #065F46; border-color: #A7F3D0; }
        .st-alert-warning { background-color: #FFFBEB; color: #92400E; border-color: #FDE68A; }
        .st-alert-error { background-color: #FFF1F2; color: #9F1239; border-color: #FECDD3; }

        /* Streamlit-Style Expanders */
        .st-expander {
            border: 1px solid #E2E8F0;
            border-radius: 8px;
            margin-bottom: 1rem;
            background-color: #FFFFFF;
            overflow: hidden;
        }

        .st-expander-header {
            padding: 0.75rem 1rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            cursor: pointer;
            user-select: none;
            background-color: #FFFFFF;
            font-weight: 500;
            font-size: 0.875rem;
            color: #0F172A;
        }

        .st-expander-header:hover {
            background-color: #F8FAFC;
        }

        .st-expander-chevron {
            font-size: 0.75rem;
            color: #64748B;
            transition: transform 0.2s ease;
        }

        .st-expander.open .st-expander-chevron {
            transform: rotate(90deg);
        }

        .st-expander-content {
            padding: 1rem;
            border-top: 1px solid #E2E8F0;
            display: none;
        }

        .st-expander.open .st-expander-content {
            display: block;
        }

        /* Streamlit-Style Tabs */
        .st-tab-bar {
            display: flex;
            border-bottom: 1px solid #E2E8F0;
            margin-bottom: 1.25rem;
            gap: 1rem;
        }

        .st-tab-btn {
            background: none;
            border: none;
            border-bottom: 2px solid transparent;
            padding: 0.5rem 0.25rem;
            font-size: 0.875rem;
            font-weight: 500;
            color: #475569;
            cursor: pointer;
            transition: color 0.15s ease, border-color 0.15s ease;
        }

        .st-tab-btn:hover {
            color: #0F172A;
        }

        .st-tab-btn.active {
            color: #0F172A;
            font-weight: 600;
            border-bottom-color: #0F172A;
        }

        .st-tab-pane {
            display: none;
        }

        .st-tab-pane.active {
            display: block;
        }

        /* Streamlit-Style DataFrames */
        .st-table-container {
            border: 1px solid #E2E8F0;
            border-radius: 8px;
            overflow-x: auto;
            background-color: #FFFFFF;
            margin-bottom: 0.75rem;
        }

        .st-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.825rem;
            text-align: left;
            white-space: nowrap;
        }

        .st-table th {
            background-color: #F8FAFC;
            color: #475569;
            font-weight: 600;
            padding: 0.55rem 0.85rem;
            border-bottom: 1px solid #E2E8F0;
        }

        .st-table td {
            padding: 0.55rem 0.85rem;
            border-bottom: 1px solid #F1F5F9;
            color: #0F172A;
        }

        .st-table tr:hover td {
            background-color: #F8FAFC;
        }

        /* Login Page Specific Styling */
        .login-container-box {
            margin-top: 2rem;
            margin-bottom: 2rem;
        }

        .login-brand-header {
            text-align: center;
            margin-bottom: 2rem;
        }

        .login-brand-title {
            font-size: 2rem;
            font-weight: 800;
            color: #0F172A;
            letter-spacing: -0.03em;
            margin-bottom: 0.25rem;
        }

        .login-brand-sub {
            font-size: 0.95rem;
            color: #64748B;
            line-height: 1.5;
        }

        .login-card {
            background-color: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 12px;
            padding: 2.25rem 2.25rem 1.5rem 2.25rem;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05), 0 8px 10px -6px rgba(0, 0, 0, 0.03);
            margin-bottom: 1.25rem;
        }

        .login-card-title {
            font-size: 1.35rem;
            font-weight: 700;
            color: #0F172A;
            letter-spacing: -0.02em;
            margin-bottom: 0.35rem;
        }

        .login-card-desc {
            font-size: 0.875rem;
            color: #64748B;
            margin-bottom: 1.5rem;
            line-height: 1.45;
        }

        .login-security-notice {
            background-color: #F8FAFC;
            border: 1px solid #E2E8F0;
            border-radius: 8px;
            padding: 0.9rem 1.1rem;
            margin-top: 1.5rem;
            font-size: 0.825rem;
            color: #475569;
            line-height: 1.5;
        }

        /* Drag-and-drop Upload Zone */
        .upload-zone {
            border: 2px dashed #CBD5E1;
            border-radius: 8px;
            padding: 2rem;
            text-align: center;
            background-color: #F8FAFC;
            cursor: pointer;
            transition: border-color 0.15s ease;
            margin-bottom: 1rem;
        }

        .upload-zone:hover {
            border-color: #0F172A;
        }

        /* Toast Notifications */
        #toast-container {
            position: fixed;
            bottom: 24px;
            right: 24px;
            z-index: 9999;
            display: flex;
            flex-direction: column;
            gap: 8px;
        }

        .toast {
            padding: 0.75rem 1.25rem;
            border-radius: 6px;
            font-size: 0.875rem;
            font-weight: 500;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.06);
            color: #FFFFFF;
            animation: slideIn 0.2s ease-out;
        }

        .toast-success { background-color: #059669; }
        .toast-error { background-color: #DC2626; }
        .toast-info { background-color: #0F172A; }

        @keyframes slideIn {
            from { transform: translateY(10px); opacity: 0; }
            to { transform: translateY(0); opacity: 1; }
        }

        /* Responsive tweaks */
        @media (max-width: 1024px) {
            .grid-4 { grid-template-columns: repeat(2, 1fr); }
            .grid-5-4 { grid-template-columns: 1fr; }
            main.st-main { padding: 1.5rem; }
        }
    </style>
</head>
<body>

<div id="toast-container"></div>

<!-- ============================================================== -->
<!-- 1. LOGIN GATE VIEW (UNAUTHENTICATED)                           -->
<!-- ============================================================== -->
<div id="view-login" class="app-layout" style="display: none;">
    <aside class="st-sidebar">
        <div class="sidebar-brand-title">NAPS Enterprise</div>
        <div class="sidebar-brand-sub">Apprenticeship Lifecycle & Scheduling</div>
        <hr class="st-divider">
        <div class="sidebar-section-label">Access Control</div>
        <div class="st-alert st-alert-info" style="margin-bottom: 0;">
            System access restricted to authorized administrators. Please sign in to proceed.
        </div>
        <hr class="st-divider">
        <div style="font-size: 0.85rem; color: #334155; line-height: 1.8;">
            <div><b>System Timezone:</b> <code>Asia/Kolkata</code></div>
            <div><b>System Date (IST):</b> <span id="login-sidebar-date">-</span></div>
        </div>
    </aside>

    <main class="st-main" style="display: flex; justify-content: center; align-items: flex-start;">
        <div style="width: 100%; max-width: 580px;">
            <div class="login-container-box">
                <div class="login-brand-header">
                    <div class="login-brand-title">NAPS Enterprise Portal</div>
                    <div class="login-brand-sub">Apprenticeship Email Scheduling, Date Calculation & Lifecycle Engine</div>
                </div>

                <div class="login-card">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem;">
                        <span class="badge badge-admin">ADMINISTRATOR ONLY</span>
                        <span style="font-size: 0.775rem; color: #64748B; font-weight: 500;">Protected Access</span>
                    </div>
                    <div class="login-card-title">Administrator Sign In</div>
                    <div class="login-card-desc">Enter your administrator credentials to access trainee management, milestone timelines, and email dispatch queues.</div>

                    <form id="login-form" onsubmit="handleLoginSubmit(event)">
                        <div class="form-group">
                            <label class="form-label" for="login-username">Administrator Username or Email</label>
                            <input class="st-input" id="login-username" type="text" placeholder="e.g. admin or admin@company.com" required>
                        </div>
                        <div class="form-group">
                            <label class="form-label" for="login-password">Administrator Password</label>
                            <input class="st-input" id="login-password" type="password" placeholder="Enter administrator password" required>
                        </div>
                        <div style="margin-top: 1.25rem;">
                            <button type="submit" class="st-btn-primary w-full" id="btn-login-submit">
                                Sign In as Administrator
                            </button>
                        </div>
                    </form>
                </div>

                <div class="login-security-notice">
                    <div style="font-weight: 600; color: #0F172A; margin-bottom: 0.25rem;">Administrator Credentials:</div>
                    <div>Username: <code>admin</code> (or <code>admin@company.com</code>) &bull; Password: <code>Admin@123</code></div>
                    <div style="font-size: 0.75rem; color: #64748B; margin-top: 0.35rem;">
                        Configurable via <code>NAPS_ADMIN_USERNAME</code> and <code>NAPS_ADMIN_PASSWORD</code> environment variables.
                    </div>
                </div>
            </div>
        </div>
    </main>
</div>

<!-- ============================================================== -->
<!-- 2. AUTHENTICATED PORTAL                                        -->
<!-- ============================================================== -->
<div id="view-authenticated" class="app-layout" style="display: none;">
    <!-- Streamlit Sidebar -->
    <aside class="st-sidebar">
        <div class="sidebar-brand-title">NAPS Enterprise</div>
        <div class="sidebar-brand-sub">Apprenticeship Lifecycle & Scheduling</div>

        <div class="sidebar-section-label">Navigation</div>
        <div class="nav-radio-group">
            <div class="nav-radio-item active" onclick="switchNav('dashboard')">
                <span class="nav-radio-bullet"></span> Dashboard
            </div>
            <div class="nav-radio-item" onclick="switchNav('directory')">
                <span class="nav-radio-bullet"></span> Trainee Directory
            </div>
            <div class="nav-radio-item" onclick="switchNav('add-trainee')">
                <span class="nav-radio-bullet"></span> Add Trainee
            </div>
            <div class="nav-radio-item" onclick="switchNav('worker-dispatch')">
                <span class="nav-radio-bullet"></span> Worker & Dispatch
            </div>
            <div class="nav-radio-item" onclick="switchNav('import-export')">
                <span class="nav-radio-bullet"></span> Excel / CSV Import
            </div>
            <div class="nav-radio-item" onclick="switchNav('audit-exceptions')">
                <span class="nav-radio-bullet"></span> Audit & Exceptions
            </div>
        </div>

        <hr class="st-divider">

        <div class="sidebar-section-label">Authenticated Session</div>
        <div><span class="badge badge-admin">ADMINISTRATOR</span></div>
        <div style="font-size: 0.85rem; color: #0F172A; font-weight: 600; margin-top: 0.4rem; margin-bottom: 0.2rem;" id="session-user-email">
            admin@company.com
        </div>
        <div style="font-size: 0.75rem; color: #64748B; margin-bottom: 0.75rem;">Full Administrative Authorization</div>
        <button type="button" class="st-btn-secondary w-full" onclick="handleLogout()">Log Out</button>

        <hr class="st-divider">

        <div class="sidebar-section-label">System Environment</div>
        <div style="font-size: 0.825rem; color: #334155; line-height: 1.8;">
            <div><b>Delivery Mode:</b> <span id="env-delivery-mode">Simulation (Dry-Run)</span></div>
            <div><b>Timezone:</b> <code>Asia/Kolkata</code></div>
            <div><b>System Date (IST):</b> <span id="env-system-date">-</span></div>
            <div><b>Database Engine:</b> <span id="env-database-engine">Loading...</span></div>
        </div>
    </aside>

    <!-- Main Content Area -->
    <main class="st-main">
        <!-- Persistent Application Header -->
        <div class="app-title">NAPS Trainee Email & Lifecycle Engine</div>
        <div class="app-subtitle">
            Automated milestone calculation, weekend adjustment, opt-out enforcement, and immutable delivery safeguards.
        </div>

        <!-- ------------------------------------------------------ -->
        <!-- VIEW 1: DASHBOARD                                      -->
        <!-- ------------------------------------------------------ -->
        <section id="page-dashboard" class="page-view">
            <!-- 4 Top KPI Metric Cards -->
            <div class="grid-4">
                <div class="metric-panel">
                    <div class="metric-panel-label">Total Trainees</div>
                    <div class="metric-panel-value" id="kpi-total-trainees">0</div>
                    <div class="metric-panel-detail" id="kpi-trainees-sub">0 Active &bull; 0 Left &bull; 0 Completed</div>
                </div>
                <div class="metric-panel">
                    <div class="metric-panel-label">Pending Schedules</div>
                    <div class="metric-panel-value" id="kpi-pending-schedules">0</div>
                    <div class="metric-panel-detail" id="kpi-pending-sub">All queues on schedule</div>
                </div>
                <div class="metric-panel">
                    <div class="metric-panel-label">Delivered Milestones</div>
                    <div class="metric-panel-value" id="kpi-delivered-milestones">0</div>
                    <div class="metric-panel-detail">Immutable audit-recorded deliveries</div>
                </div>
                <div class="metric-panel">
                    <div class="metric-panel-label">Delivery Exceptions</div>
                    <div class="metric-panel-value" id="kpi-delivery-exceptions">0</div>
                    <div class="metric-panel-detail" id="kpi-exceptions-sub">All channels healthy</div>
                </div>
            </div>

            <div class="section-title">Queue Operations & Dispatch Overview</div>
            <div class="section-caption">Monitor upcoming milestones, execute dispatch batches, and review exceptions.</div>

            <div class="grid-5-4">
                <!-- Left: Upcoming & Due Email Schedules -->
                <div>
                    <div style="font-weight: 600; font-size: 0.95rem; margin-bottom: 0.5rem;">Upcoming & Due Email Schedules</div>
                    <div class="st-table-container">
                        <table class="st-table">
                            <thead>
                                <tr>
                                    <th>Queue ID</th>
                                    <th>Trainee ID</th>
                                    <th>Employee Name</th>
                                    <th>Stage</th>
                                    <th>Scheduled Date</th>
                                    <th>Dispatch Eligibility</th>
                                    <th>Status</th>
                                </tr>
                            </thead>
                            <tbody id="dash-queue-tbody">
                                <tr><td colspan="7" style="text-align: center; color: #64748B;">Loading pending queue...</td></tr>
                            </tbody>
                        </table>
                    </div>

                    <!-- Quick Dispatch Action Expander -->
                    <div class="st-expander open" id="dash-worker-expander">
                        <div class="st-expander-header" onclick="toggleExpander('dash-worker-expander')">
                            <span>Execute Background Worker Dispatch Cycle</span>
                            <span class="st-expander-chevron">&#9654;</span>
                        </div>
                        <div class="st-expander-content">
                            <div class="section-caption">Processes all schedules whose scheduled_date &le; Target Evaluation Date.</div>
                            <div class="grid-2" style="align-items: flex-end;">
                                <div class="form-group" style="margin-bottom: 0;">
                                    <label class="form-label" for="dash-target-date">Target Evaluation Date</label>
                                    <input type="date" class="st-input" id="dash-target-date">
                                </div>
                                <div>
                                    <button type="button" class="st-btn-primary w-full" onclick="triggerWorkerDispatch('dash-target-date', 'dash-worker-result')">
                                        Run Dispatch Now
                                    </button>
                                </div>
                            </div>
                            <div id="dash-worker-result" style="margin-top: 0.75rem;"></div>
                        </div>
                    </div>
                </div>

                <!-- Right: Exceptions & Recent System Activity Feed -->
                <div>
                    <div style="font-weight: 600; font-size: 0.95rem; margin-bottom: 0.5rem;">Exceptions Requiring Attention</div>
                    <div id="dash-exceptions-list" style="margin-bottom: 1rem;">
                        <div class="st-alert st-alert-success" style="margin-bottom: 0;">No delivery exceptions currently requiring attention.</div>
                    </div>

                    <hr class="st-divider">

                    <div style="font-weight: 600; font-size: 0.95rem; margin-bottom: 0.5rem;">Recent System Activity Feed</div>
                    <div id="dash-recent-activity">
                        <div style="color: #64748B; font-size: 0.85rem;">Loading audit feed...</div>
                    </div>
                </div>
            </div>
        </section>

        <!-- ------------------------------------------------------ -->
        <!-- VIEW 2: TRAINEE DIRECTORY                              -->
        <!-- ------------------------------------------------------ -->
        <section id="page-directory" class="page-view" style="display: none;">
            <!-- Filter Bar -->
            <div class="grid-3" style="grid-template-columns: 3fr 1fr 1fr; margin-bottom: 0.5rem;">
                <div class="form-group">
                    <label class="form-label" for="dir-search-input">Search Trainees</label>
                    <input type="text" class="st-input" id="dir-search-input" placeholder="Filter by Trainee ID, Name, Department, or Email..." oninput="filterDirectoryTable()">
                </div>
                <div class="form-group">
                    <label class="form-label" for="dir-status-filter">Status Filter</label>
                    <select class="st-select" id="dir-status-filter" onchange="filterDirectoryTable()">
                        <option value="All">All</option>
                        <option value="Active">Active</option>
                        <option value="Left">Left</option>
                        <option value="Completed">Completed</option>
                        <option value="On Roll">On Roll</option>
                    </select>
                </div>
                <div class="form-group">
                    <label class="form-label" for="dir-dept-filter">Department Filter</label>
                    <select class="st-select" id="dir-dept-filter" onchange="filterDirectoryTable()">
                        <option value="All">All</option>
                    </select>
                </div>
            </div>

            <div class="section-caption" id="dir-count-caption">Showing 0 of 0 registered apprentices.</div>

            <!-- Master Timeline Table -->
            <div class="section-title">Master Trainee Directory & Milestone Schedule Timeline</div>
            <div class="section-caption">
                Authoritative scheduled milestone dispatch dates and statuses for all trainees across all 6 stages. Synchronized with database and worker.
            </div>

            <div class="st-table-container">
                <table class="st-table" id="master-directory-table">
                    <thead>
                        <tr>
                            <th>Trainee ID</th>
                            <th>Name</th>
                            <th>Status</th>
                            <th>DOJ</th>
                            <th>LWD</th>
                            <th>Initial Email (DOJ+15d)</th>
                            <th>Q1 Milestone (DOJ+3m)</th>
                            <th>Q2 Milestone (DOJ+6m)</th>
                            <th>Q3 Milestone (DOJ+9m)</th>
                            <th>Q4 Milestone (DOJ+12m)</th>
                            <th>Exit Feedback (LWD+3m)</th>
                            <th>Department</th>
                            <th>Manager</th>
                        </tr>
                    </thead>
                    <tbody id="master-directory-tbody">
                        <tr><td colspan="13" style="text-align: center; color: #64748B;">Loading directory roster...</td></tr>
                    </tbody>
                </table>
            </div>
            <div class="form-caption" style="margin-bottom: 1.5rem;">
                Status Indicators: [Scheduled] Normal Automated Date &bull; [Custom Override] Manual Date &bull; [Opted Out] Stage Inactive &bull; [Sent] Delivered &bull; [Cancelled] Lifecycle Inactive &bull; [Uncertain] Exception
            </div>

            <hr class="st-divider">

            <!-- Trainee Details & Configuration Selector -->
            <div class="section-title">Trainee Details & Configuration</div>
            <div class="section-caption">
                Select an apprentice to inspect full profile details, update lifecycle status, or customize specific milestone schedules.
            </div>

            <div class="form-group" style="max-width: 600px; margin-bottom: 1.25rem;">
                <label class="form-label" for="dir-select-trainee">Select Trainee for Profile & Schedules</label>
                <select class="st-select" id="dir-select-trainee" onchange="loadSelectedTraineeDetails()">
                    <option value="">-- Choose Trainee --</option>
                </select>
            </div>

            <!-- 3 Tabs Container -->
            <div id="dir-details-container" style="display: none;">
                <div class="st-tab-bar">
                    <button type="button" class="st-tab-btn active" onclick="switchDirectoryTab('tab-schedules')">Milestone Schedules & Opt-Outs</button>
                    <button type="button" class="st-tab-btn" onclick="switchDirectoryTab('tab-profile')">Profile Information</button>
                    <button type="button" class="st-tab-btn" onclick="switchDirectoryTab('tab-edit')">Edit Trainee & Lifecycle</button>
                </div>

                <!-- TAB 1: MILESTONE SCHEDULES & OPT-OUTS -->
                <div id="tab-schedules" class="st-tab-pane active">
                    <div style="font-weight: 600; font-size: 1.05rem; margin-bottom: 0.25rem;">Email Stage Schedule Dates & Opt-Out Preferences</div>
                    <div class="section-caption">
                        Authoritative email stages and dispatch dates. Synchronized in real time across the database, worker, and import engine. Sent stages are strictly immutable.
                    </div>

                    <div class="st-table-container">
                        <table class="st-table">
                            <thead>
                                <tr>
                                    <th>Stage</th>
                                    <th>Recipient</th>
                                    <th>Math Due Date</th>
                                    <th>Effective Scheduled Date</th>
                                    <th>Date Mode</th>
                                    <th>Opt-out Preference</th>
                                    <th>Status</th>
                                    <th>Attempts</th>
                                    <th>Details</th>
                                </tr>
                            </thead>
                            <tbody id="trainee-schedules-summary-tbody"></tbody>
                        </table>
                    </div>

                    <hr class="st-divider">

                    <div style="font-weight: 600; font-size: 0.95rem; margin-bottom: 0.25rem;">Update Email Stage Schedule Dates & Opt-Outs</div>
                    <div class="section-caption">Modifications are validated, audited, and synchronized across all views immediately.</div>

                    <form id="form-sync-stages" onsubmit="handleSaveStagePreferences(event)">
                        <div class="grid-2" id="sync-stages-inputs-grid"></div>
                        <div style="margin-top: 1rem;">
                            <button type="submit" class="st-btn-primary">Save & Synchronize Email Stages</button>
                        </div>
                    </form>
                </div>

                <!-- TAB 2: PROFILE INFORMATION -->
                <div id="tab-profile" class="st-tab-pane">
                    <div class="grid-3" id="profile-info-grid" style="font-size: 0.875rem; line-height: 2;"></div>
                </div>

                <!-- TAB 3: EDIT TRAINEE & LIFECYCLE -->
                <div id="tab-edit" class="st-tab-pane">
                    <div style="font-weight: 600; font-size: 1.05rem; margin-bottom: 0.25rem;">Edit Trainee Details & Lifecycle Status</div>
                    <form id="form-edit-trainee" onsubmit="handleEditTraineeSubmit(event)">
                        <div class="grid-2">
                            <!-- Col 1 -->
                            <div>
                                <div class="form-group">
                                    <label class="form-label" for="edit-name">Trainee Name</label>
                                    <input type="text" class="st-input" id="edit-name" required>
                                </div>
                                <div class="form-group">
                                    <label class="form-label" for="edit-email">Trainee Email</label>
                                    <input type="email" class="st-input" id="edit-email" required>
                                </div>
                                <div class="form-group">
                                    <label class="form-label" for="edit-mgr-name">Manager Name</label>
                                    <input type="text" class="st-input" id="edit-mgr-name" required>
                                </div>
                                <div class="form-group">
                                    <label class="form-label" for="edit-mgr-email">Manager Email</label>
                                    <input type="email" class="st-input" id="edit-mgr-email" required>
                                </div>
                                <div class="form-group">
                                    <label class="form-label" for="edit-dept">Department</label>
                                    <input type="text" class="st-input" id="edit-dept" required>
                                </div>
                                <div class="form-group">
                                    <label class="form-label" for="edit-loc">Location</label>
                                    <input type="text" class="st-input" id="edit-loc" required>
                                </div>
                            </div>

                            <!-- Col 2 -->
                            <div>
                                <div class="form-group">
                                    <label class="form-label" for="edit-doj">Date of Joining (DOJ)</label>
                                    <input type="date" class="st-input" id="edit-doj" onchange="recalculateEditLwdPreview()" required>
                                </div>
                                <div class="form-group">
                                    <label class="form-label" for="edit-status">Lifecycle Status</label>
                                    <select class="st-select" id="edit-status" onchange="toggleEditStatusConfirmation()">
                                        <option value="Active">Active</option>
                                        <option value="Left">Left</option>
                                        <option value="Completed">Completed</option>
                                        <option value="On Roll">On Roll</option>
                                    </select>
                                </div>

                                <div style="font-weight: 600; font-size: 0.85rem; margin-top: 0.5rem; margin-bottom: 0.35rem;">
                                    Last Working Date (LWD) Management:
                                </div>
                                <div style="display: flex; gap: 1rem; margin-bottom: 0.5rem;">
                                    <label class="st-checkbox-label">
                                        <input type="radio" name="edit-lwd-mode" id="edit-lwd-mode-auto" value="auto" checked onchange="toggleEditLwdMode()">
                                        Automatic (DOJ + 12 calendar months)
                                    </label>
                                    <label class="st-checkbox-label">
                                        <input type="radio" name="edit-lwd-mode" id="edit-lwd-mode-manual" value="manual" onchange="toggleEditLwdMode()">
                                        Manual Override Date
                                    </label>
                                </div>

                                <div class="form-group">
                                    <label class="form-label" for="edit-lwd">Last Working Date (LWD)</label>
                                    <input type="date" class="st-input" id="edit-lwd" required>
                                    <div class="form-caption">Must be on or after Date of Joining.</div>
                                </div>

                                <!-- Left Confirmation Alert -->
                                <div id="edit-left-confirm-box" style="display: none;" class="st-alert st-alert-warning">
                                    <div style="font-weight: 600; margin-bottom: 0.35rem;">Confirmation Required: Status is 'Left'.</div>
                                    <div>You must explicitly confirm the actual Last Working Date. Default DOJ + 12 months cannot be silently assumed.</div>
                                    <label class="st-checkbox-label" style="margin-top: 0.5rem;">
                                        <input type="checkbox" class="st-checkbox" id="edit-chk-confirm-lwd">
                                        I confirm that the above Last Working Date is the trainee's actual departure date.
                                    </label>
                                </div>

                                <!-- DOJ change review checkbox -->
                                <div id="edit-doj-change-box" style="display: none;" class="st-alert st-alert-info">
                                    <div>Notice: DOJ was modified. Please confirm you have reviewed the manual LWD.</div>
                                    <label class="st-checkbox-label" style="margin-top: 0.5rem;">
                                        <input type="checkbox" class="st-checkbox" id="edit-chk-reviewed-doj">
                                        I have reviewed and confirmed the manual LWD.
                                    </label>
                                </div>
                            </div>
                        </div>

                        <div style="margin-top: 1rem;">
                            <button type="submit" class="st-btn-primary">Save Trainee & Reconcile Schedules</button>
                        </div>
                    </form>

                    <hr class="st-divider">

                    <div class="st-expander" id="archive-expander">
                        <div class="st-expander-header" onclick="toggleExpander('archive-expander')">
                            <span>Archive Trainee Record</span>
                            <span class="st-expander-chevron">&#9654;</span>
                        </div>
                        <div class="st-expander-content">
                            <div class="section-caption">
                                Archiving deactivates the trainee record while strictly preserving all email schedules and Sent delivery history.
                            </div>
                            <button type="button" class="st-btn-secondary" onclick="handleArchiveCurrentTrainee()">Archive Trainee Record</button>
                        </div>
                    </div>
                </div>
            </div>
        </section>

        <!-- ------------------------------------------------------ -->
        <!-- VIEW 3: ADD TRAINEE                                    -->
        <!-- ------------------------------------------------------ -->
        <section id="page-add-trainee" class="page-view" style="display: none;">
            <div class="section-title">Enroll New NAPS Apprentice</div>
            <div class="section-caption">
                All milestone dates are deterministically computed with calendar month clamping and automatic weekend adjustments.
            </div>

            <form id="form-create-trainee" onsubmit="handleCreateTraineeSubmit(event)">
                <div class="grid-2">
                    <!-- Left Col -->
                    <div>
                        <div class="form-group">
                            <label class="form-label" for="add-id">Trainee ID (Mandatory, Unique)*</label>
                            <input type="text" class="st-input" id="add-id" placeholder="e.g. TR-5001" required>
                        </div>
                        <div class="form-group">
                            <label class="form-label" for="add-name">Trainee Full Name*</label>
                            <input type="text" class="st-input" id="add-name" placeholder="e.g. Priyanshu Roy" required>
                        </div>
                        <div class="form-group">
                            <label class="form-label" for="add-email">Trainee Email Address*</label>
                            <input type="email" class="st-input" id="add-email" placeholder="e.g. trainee@example.com" required>
                        </div>
                        <div class="form-group">
                            <label class="form-label" for="add-doj">Date of Joining (DOJ)*</label>
                            <input type="date" class="st-input" id="add-doj" onchange="calculateAddTraineeMilestones()" required>
                        </div>
                        <div class="form-group">
                            <label class="form-label" for="add-dept">Department*</label>
                            <input type="text" class="st-input" id="add-dept" value="Engineering" required>
                        </div>
                        <div class="form-group">
                            <label class="form-label" for="add-loc">Location*</label>
                            <input type="text" class="st-input" id="add-loc" value="Bangalore" required>
                        </div>
                    </div>

                    <!-- Right Col -->
                    <div>
                        <div class="form-group">
                            <label class="form-label" for="add-mgr-name">Manager Name*</label>
                            <input type="text" class="st-input" id="add-mgr-name" value="Project Manager" required>
                        </div>
                        <div class="form-group">
                            <label class="form-label" for="add-mgr-email">Manager Email Address*</label>
                            <input type="email" class="st-input" id="add-mgr-email" value="manager@example.com" required>
                        </div>
                        <div class="form-group">
                            <label class="form-label" for="add-status">Status</label>
                            <select class="st-select" id="add-status" onchange="toggleAddStatusConfirmation()">
                                <option value="Active">Active</option>
                                <option value="Left">Left</option>
                                <option value="Completed">Completed</option>
                                <option value="On Roll">On Roll</option>
                            </select>
                        </div>

                        <div style="font-size: 0.85rem; margin-bottom: 0.5rem;">
                            <b>Default LWD (DOJ + 12m):</b> <code id="add-auto-lwd-display">-</code>
                        </div>

                        <label class="st-checkbox-label">
                            <input type="checkbox" class="st-checkbox" id="add-chk-custom-lwd" onchange="toggleAddCustomLwdInput()">
                            Provide Manual Last Working Date Override
                        </label>

                        <div class="form-group" id="add-custom-lwd-box" style="display: none;">
                            <label class="form-label" for="add-custom-lwd">Manual Last Working Date</label>
                            <input type="date" class="st-input" id="add-custom-lwd" onchange="calculateAddTraineeMilestones()">
                        </div>

                        <div id="add-left-confirm-box" style="display: none;" class="st-alert st-alert-warning">
                            <div style="font-weight: 600; margin-bottom: 0.35rem;">Confirmation Required: Status is 'Left'.</div>
                            <div>You must explicitly confirm the actual Last Working Date.</div>
                            <label class="st-checkbox-label" style="margin-top: 0.5rem;">
                                <input type="checkbox" class="st-checkbox" id="add-chk-confirm-lwd">
                                Confirm actual LWD for status Left*
                            </label>
                        </div>
                    </div>
                </div>

                <hr class="st-divider">

                <div style="font-weight: 600; font-size: 0.95rem; margin-bottom: 0.25rem;">Initial Email Stage Schedule Dates & Opt-Outs</div>
                <div class="section-caption">All 6 stages are enabled by default for new apprentices. You may customize dates or opt out.</div>

                <div class="grid-3" id="add-stages-preview-grid"></div>

                <div style="margin-top: 1.25rem;">
                    <button type="submit" class="st-btn-primary">Register Trainee & Generate Schedules</button>
                </div>
            </form>
        </section>

        <!-- ------------------------------------------------------ -->
        <!-- VIEW 4: WORKER & DISPATCH                              -->
        <!-- ------------------------------------------------------ -->
        <section id="page-worker-dispatch" class="page-view" style="display: none;">
            <div class="section-title">Automated Dispatch Worker & Engine Controls</div>
            <div class="section-caption">
                The background worker processes eligible schedules whose scheduled_date &le; Target Evaluation Date in Asia/Kolkata.
            </div>

            <!-- SMTP & Dispatch Configuration Overview -->
            <div class="st-expander open" id="smtp-config-expander">
                <div class="st-expander-header" onclick="toggleExpander('smtp-config-expander')">
                    <span>SMTP & Dispatch Configuration</span>
                    <span class="st-expander-chevron">&#9654;</span>
                </div>
                <div class="st-expander-content">
                    <div style="background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 1rem 1.25rem;">
                        <div style="font-weight: 700; color: #0F172A; margin-bottom: 0.5rem; font-size: 0.95rem;">
                            Active Dispatch Settings:
                        </div>
                        <div style="font-size: 0.85rem; color: #334155; line-height: 1.8;">
                            &bull; <b>Sender Email:</b> <code id="worker-sender-email">admin@company.com</code><br/>
                            &bull; <b>SMTP Server:</b> <code id="worker-smtp-server">smtp.gmail.com:587 (STARTTLS)</code><br/>
                            &bull; <b>SMTP Authentication:</b> <span id="worker-smtp-auth" style="color: #065F46; font-weight: 600;">Configured</span><br/>
                            &bull; <b>Delivery Mode:</b> <span id="worker-delivery-mode-html" style="color: #B45309; font-weight: 600;">Simulation (Dry-Run Enabled)</span>
                        </div>
                    </div>
                </div>
            </div>

            <hr class="st-divider">

            <div class="grid-3">
                <div class="metric-panel">
                    <div class="metric-panel-label">Delivery Mode</div>
                    <div class="metric-panel-value" style="font-size: 1.25rem;" id="worker-card-mode">Simulation (Dry-Run)</div>
                </div>
                <div class="metric-panel">
                    <div class="metric-panel-label">Target Dispatch Hour</div>
                    <div class="metric-panel-value" style="font-size: 1.25rem;">09:00:00 Asia/Kolkata</div>
                </div>
                <div class="metric-panel">
                    <div class="metric-panel-label">Automatic Retries</div>
                    <div class="metric-panel-value" style="font-size: 1.25rem;">1 Transient Retry Allowed</div>
                </div>
            </div>

            <hr class="st-divider">

            <div class="grid-2" style="max-width: 650px; align-items: flex-end; margin-bottom: 1.25rem;">
                <div class="form-group" style="margin-bottom: 0;">
                    <label class="form-label" for="worker-target-date">Target Evaluation Date (Asia/Kolkata)</label>
                    <input type="date" class="st-input" id="worker-target-date">
                </div>
                <div>
                    <button type="button" class="st-btn-primary w-full" onclick="triggerWorkerDispatch('worker-target-date', 'worker-run-result')">
                        Run Dispatch Worker Cycle
                    </button>
                </div>
            </div>

            <div id="worker-run-result" style="margin-bottom: 1.5rem;"></div>

            <hr class="st-divider">

            <div class="section-title">Queue Status: Pending & In-Flight Schedules</div>
            <div class="st-table-container">
                <table class="st-table">
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Trainee ID</th>
                            <th>Name</th>
                            <th>Stage</th>
                            <th>Scheduled Date</th>
                            <th>Status</th>
                            <th>Attempts</th>
                        </tr>
                    </thead>
                    <tbody id="worker-queue-tbody">
                        <tr><td colspan="7" style="text-align: center; color: #64748B;">Loading queued schedules...</td></tr>
                    </tbody>
                </table>
            </div>
        </section>

        <!-- ------------------------------------------------------ -->
        <!-- VIEW 5: EXCEL / CSV IMPORT                             -->
        <!-- ------------------------------------------------------ -->
        <section id="page-import-export" class="page-view" style="display: none;">
            <div class="section-title">Idempotent Trainee & Email Stage Import / Export</div>
            <div class="section-caption">
                Upload .xlsx or .csv files with trainee fields and stage preferences. Re-importing unchanged data preserves custom dates, opt-outs, and Sent history.
            </div>

            <div class="grid-2">
                <!-- Col 1: Download Templates -->
                <div>
                    <div style="font-weight: 600; font-size: 0.95rem; margin-bottom: 0.5rem;">Download Import Template:</div>
                    <div style="display: flex; gap: 0.75rem;">
                        <button type="button" class="st-btn-secondary" onclick="downloadTemplate('xlsx')">Download Excel Template (.xlsx)</button>
                        <button type="button" class="st-btn-secondary" onclick="downloadTemplate('csv')">Download CSV Template (.csv)</button>
                    </div>
                </div>

                <!-- Col 2: Export Current DB -->
                <div>
                    <div style="font-weight: 600; font-size: 0.95rem; margin-bottom: 0.5rem;">Export Current Database:</div>
                    <div style="display: flex; gap: 0.75rem;">
                        <button type="button" class="st-btn-secondary" onclick="exportDatabase('xlsx')">Export Trainees & Schedules (.xlsx)</button>
                        <button type="button" class="st-btn-secondary" onclick="exportDatabase('csv')">Export Trainees & Schedules (.csv)</button>
                    </div>
                </div>
            </div>

            <hr class="st-divider">

            <!-- Column Specifications Expander -->
            <div class="st-expander" id="specs-expander">
                <div class="st-expander-header" onclick="toggleExpander('specs-expander')">
                    <span>Documented Column Specifications & Validation Rules</span>
                    <span class="st-expander-chevron">&#9654;</span>
                </div>
                <div class="st-expander-content" style="font-size: 0.85rem; color: #334155; line-height: 1.7;">
                    <div><b>Trainee Core Fields:</b> <code>trainee_id</code>, <code>trainee_name</code>, <code>trainee_email</code>, <code>date_of_joining</code> (DD/MM/YYYY), <code>manager_name</code>, <code>manager_email</code>, <code>department</code>, <code>location</code>, <code>status</code>, <code>last_working_date</code>, <code>confirmed_actual_lwd</code></div>
                    <div style="margin-top: 0.4rem;"><b>Stage Opt-Out Columns (True/False):</b> <code>initial_email_opt_out</code>, <code>q1_opt_out</code>, <code>q2_opt_out</code>, <code>q3_opt_out</code>, <code>q4_opt_out</code>, <code>exit_feedback_opt_out</code></div>
                    <div style="margin-top: 0.4rem;"><b>Stage Scheduled Date Columns (DD/MM/YYYY):</b> <code>initial_email_scheduled_date</code>, <code>q1_scheduled_date</code>, <code>q2_scheduled_date</code>, <code>q3_scheduled_date</code>, <code>q4_scheduled_date</code>, <code>exit_feedback_scheduled_date</code></div>
                    <div style="margin-top: 0.5rem; font-style: italic; color: #64748B;">
                        *Rules: For new trainees, omitted stage dates are automatically calculated and weekend-adjusted. For updates, blank cells preserve existing values. Sent history is strictly immutable.
                    </div>
                </div>
            </div>

            <!-- Upload File Box -->
            <div class="upload-zone" onclick="document.getElementById('file-upload-input').click()">
                <div style="font-weight: 600; font-size: 1rem; color: #0F172A; margin-bottom: 0.25rem;">Select Trainee Excel or CSV File</div>
                <div style="font-size: 0.85rem; color: #64748B;">Drag and drop or click to browse (.xlsx, .xls, .csv)</div>
                <input type="file" id="file-upload-input" accept=".xlsx, .xls, .csv" style="display: none;" onchange="handleFileUpload(event)">
            </div>

            <!-- Staging Container (Visible after upload) -->
            <div id="staging-container" style="display: none;">
                <!-- 4 Staging Metrics -->
                <div class="grid-4">
                    <div class="metric-panel">
                        <div class="metric-panel-label">Total Records in File</div>
                        <div class="metric-panel-value" id="staging-kpi-total">0</div>
                    </div>
                    <div class="metric-panel">
                        <div class="metric-panel-label">New Registrations</div>
                        <div class="metric-panel-value" id="staging-kpi-new">0</div>
                    </div>
                    <div class="metric-panel">
                        <div class="metric-panel-label">Existing Trainee Updates</div>
                        <div class="metric-panel-value" id="staging-kpi-upd">0</div>
                    </div>
                    <div class="metric-panel">
                        <div class="metric-panel-label">Configured Schedule Overrides</div>
                        <div class="metric-panel-value" id="staging-kpi-overrides">0</div>
                    </div>
                </div>

                <hr class="st-divider">

                <div class="section-title">Milestone Schedule Calculations for Uploaded Records</div>
                <div class="section-caption">
                    Authoritative email milestone schedule dates calculated deterministically from Date of Joining (DOJ) and Last Working Date (LWD). Dates falling on Saturdays or Sundays are automatically shifted to Monday. Custom dates and opt-outs specified in the spreadsheet or configured below are highlighted.
                </div>

                <div class="st-table-container">
                    <table class="st-table">
                        <thead>
                            <tr>
                                <th>Row #</th>
                                <th>Trainee ID</th>
                                <th>Employee Name</th>
                                <th>Type</th>
                                <th>DOJ</th>
                                <th>LWD</th>
                                <th>Status</th>
                                <th>Initial Email (DOJ+15d)</th>
                                <th>Q1 Milestone (DOJ+3m)</th>
                                <th>Q2 Milestone (DOJ+6m)</th>
                                <th>Q3 Milestone (DOJ+9m)</th>
                                <th>Q4 Milestone (DOJ+12m)</th>
                                <th>Exit Feedback (LWD+3m)</th>
                            </tr>
                        </thead>
                        <tbody id="staging-preview-tbody"></tbody>
                    </table>
                </div>
                <div class="form-caption" style="margin-bottom: 1.25rem;">
                    Status Indicators: [Scheduled] Normal (Weekend Adjusted) &bull; [Custom Override] Manual Date &bull; [Opted Out] Inactive
                </div>

                <!-- Expander: Delete / Remove Rows from Staging Table -->
                <div class="st-expander" id="staging-del-expander">
                    <div class="st-expander-header" onclick="toggleExpander('staging-del-expander')">
                        <span>Delete / Remove Rows from Staging Table</span>
                        <span class="st-expander-chevron">&#9654;</span>
                    </div>
                    <div class="st-expander-content">
                        <div class="section-caption">Remove specific rows from this upload preview so they will not be imported into the database.</div>
                        <div class="grid-2" style="grid-template-columns: 3fr 1fr; align-items: flex-end;">
                            <div class="form-group" style="margin-bottom: 0;">
                                <label class="form-label" for="staging-del-select">Select Rows to Remove from Staging</label>
                                <select class="st-select" id="staging-del-select" multiple size="4"></select>
                            </div>
                            <div style="display: flex; flex-direction: column; gap: 0.5rem;">
                                <button type="button" class="st-btn-secondary" onclick="deleteSelectedStagedRows()">Delete Selected Rows</button>
                                <button type="button" class="st-btn-secondary" onclick="clearEntireStagedUpload()">Clear / Discard Entire Upload</button>
                            </div>
                        </div>
                    </div>
                </div>

                <hr class="st-divider">

                <!-- Employee Milestone Schedule Configuration & Overrides -->
                <div class="section-title">Employee Milestone Schedule Configuration & Overrides</div>
                <div class="section-caption">
                    Review or customize specific email milestone schedule dates and opt-out preferences for any employee before saving to database.
                </div>

                <div class="form-group" style="max-width: 600px; margin-bottom: 1.25rem;">
                    <label class="form-label" for="staging-emp-select">Select Employee to View / Adjust Schedule Dates</label>
                    <select class="st-select" id="staging-emp-select" onchange="loadStagedEmployeeScheduleConfig()">
                        <option value="">-- Choose Employee --</option>
                    </select>
                </div>

                <div id="staging-emp-config-box" style="display: none; background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; padding: 1.25rem; margin-bottom: 1.5rem;">
                    <div id="staging-emp-config-title" style="font-weight: 600; font-size: 0.95rem; margin-bottom: 0.5rem;"></div>
                    <div id="staging-emp-existing-notice" class="st-alert st-alert-info" style="display: none;">
                        Notice: Existing trainee in database. Any milestone emails already sent in history are strictly immutable.
                    </div>
                    <div class="grid-2" id="staging-emp-stages-grid"></div>
                    <div style="display: flex; gap: 0.75rem; margin-top: 1rem;">
                        <button type="button" class="st-btn-primary" onclick="saveStagedEmployeeConfig()">Save Schedule Configuration</button>
                        <button type="button" class="st-btn-secondary" onclick="deleteCurrentStagedEmployee()">Delete Row</button>
                        <button type="button" class="st-btn-secondary" onclick="resetStagedEmployeeOverrides()">Reset to Original</button>
                    </div>
                </div>

                <hr class="st-divider">

                <!-- Database Commit Section -->
                <div class="section-title">Database Synchronization & Persistence</div>
                <div class="section-caption">Commit all rows and synchronized schedule dates directly into the database.</div>

                <div style="max-width: 400px; margin-bottom: 1rem;">
                    <button type="button" class="st-btn-primary w-full" id="btn-commit-staging" onclick="commitStagedRows()">
                        Commit Valid Records & Synchronize Schedules
                    </button>
                </div>
                <div id="commit-result-box"></div>
            </div>

            <hr class="st-divider">

            <!-- Database Clean Up Utility Expander -->
            <div class="st-expander" id="db-clean-up-expander">
                <div class="st-expander-header" onclick="toggleExpander('db-clean-up-expander')">
                    <span>Delete / Clean Up Trainees from Database</span>
                    <span class="st-expander-chevron">&#9654;</span>
                </div>
                <div class="st-expander-content">
                    <div class="section-title" style="margin-top: 0;">Database Clean Up Utility</div>
                    <div class="section-caption">
                        Delete registered trainees and their unsent schedules directly from the database. Note: Trainees with already 'Sent' milestone emails are protected and cannot be hard deleted to preserve audit logs.
                    </div>

                    <div class="form-group">
                        <label class="form-label" for="db-cleanup-select">Select Trainees to Delete from Database</label>
                        <select class="st-select" id="db-cleanup-select" multiple size="5"></select>
                    </div>

                    <div class="grid-2" style="grid-template-columns: 3fr 1fr; align-items: center;">
                        <label class="st-checkbox-label" style="margin-bottom: 0;">
                            <input type="checkbox" class="st-checkbox" id="chk-confirm-db-delete">
                            I confirm that I want to permanently delete the selected trainee(s) and their unsent schedules
                        </label>
                        <button type="button" class="st-btn-danger w-full" onclick="executeDatabaseDeleteTrainees()">
                            Delete from Database
                        </button>
                    </div>
                    <div id="db-delete-result" style="margin-top: 0.75rem;"></div>
                </div>
            </div>
        </section>

        <!-- ------------------------------------------------------ -->
        <!-- VIEW 6: AUDIT & EXCEPTIONS                             -->
        <!-- ------------------------------------------------------ -->
        <section id="page-audit-exceptions" class="page-view" style="display: none;">
            <div class="st-tab-bar">
                <button type="button" class="st-tab-btn active" onclick="switchAuditTab('tab-audit-trail')">Activity Audit Trail</button>
                <button type="button" class="st-tab-btn" onclick="switchAuditTab('tab-delivery-exceptions')">Delivery Exceptions & Uncertain Deliveries</button>
            </div>

            <!-- TAB 1: AUDIT TRAIL -->
            <div id="tab-audit-trail" class="st-tab-pane active">
                <div style="font-weight: 600; font-size: 1.05rem; margin-bottom: 0.25rem;">Append-Only System Audit Trail</div>
                <div class="section-caption">
                    Comprehensive log of entity changes, status updates, overrides, worker actions, and exception resolutions.
                </div>

                <div class="form-group" style="max-width: 300px; margin-bottom: 1rem;">
                    <label class="form-label" for="audit-filter-entity">Filter Entity Type</label>
                    <select class="st-select" id="audit-filter-entity" onchange="loadAuditLogs()">
                        <option value="All">All</option>
                        <option value="trainee">trainee</option>
                        <option value="schedule">schedule</option>
                        <option value="import">import</option>
                        <option value="worker">worker</option>
                    </select>
                </div>

                <div class="st-table-container">
                    <table class="st-table">
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Timestamp (IST)</th>
                                <th>Actor</th>
                                <th>Entity</th>
                                <th>Action</th>
                                <th>Reason</th>
                                <th>Old Values</th>
                                <th>New Values</th>
                            </tr>
                        </thead>
                        <tbody id="audit-logs-tbody">
                            <tr><td colspan="8" style="text-align: center; color: #64748B;">Loading audit log entries...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- TAB 2: EXCEPTIONS & UNCERTAIN DELIVERIES -->
            <div id="tab-delivery-exceptions" class="st-tab-pane">
                <div style="font-weight: 600; font-size: 1.05rem; margin-bottom: 0.25rem;">Exception Management & Uncertain Delivery Resolution</div>
                <div class="section-caption">
                    When SMTP timeouts or ambiguities occur during transmission, schedules are placed into Uncertain status. Admin authorization is required.
                </div>

                <div id="exceptions-cards-container">
                    <div style="color: #64748B; font-size: 0.85rem;">Loading exceptions list...</div>
                </div>
            </div>
        </section>
    </main>
</div>

<!-- ============================================================== -->
<!-- JAVASCRIPT: CLIENT ENGINE & REST BACKEND INTEGRATION           -->
<!-- ============================================================== -->
<script>
    // System Constants & Stage Names matching models.py
    const STAGE_LABELS = {
        "initial": "Initial Welcome Email",
        "q1": "Quarterly Assessment 1",
        "q2": "Quarterly Assessment 2",
        "q3": "Quarterly Assessment 3",
        "q4": "Quarterly Assessment 4",
        "exit": "Exit Feedback"
    };

    const STAGE_ROLES = {
        "initial": "Trainee",
        "q1": "Manager",
        "q2": "Manager",
        "q3": "Manager",
        "q4": "Manager",
        "exit": "Trainee"
    };

    const STAGES_ORDER = ["initial", "q1", "q2", "q3", "q4", "exit"];

    // Session State
    let currentUser = null;
    let allTraineesCache = [];
    let currentSelectedTrainee = null;
    let stagedRowsCache = [];
    let stagedOverrides = {}; // trainee_id -> { stage -> { scheduled_date, opt_out } }

    // -------------------------------------------------------------
    // UTILITY HELPERS
    // -------------------------------------------------------------
    function showToast(message, type = "info") {
        const c = document.getElementById("toast-container");
        const t = document.createElement("div");
        t.className = `toast toast-${type}`;
        t.textContent = message;
        c.appendChild(t);
        setTimeout(() => { t.remove(); }, 4000);
    }

    function toggleExpander(id) {
        const el = document.getElementById(id);
        if (el) el.classList.toggle("open");
    }

    function escapeHtml(str) {
        if (!str) return "";
        return String(str)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    // Date calculations in JS identical to date_engine.py
    function addCalendarMonths(d, months) {
        const year = d.getFullYear();
        const month = d.getMonth();
        const day = d.getDate();

        const targetMonthIndex = month + months;
        const targetYear = year + Math.floor(targetMonthIndex / 12);
        const targetMonth = ((targetMonthIndex % 12) + 12) % 12;

        const lastDayOfTargetMonth = new Date(targetYear, targetMonth + 1, 0).getDate();
        const clampedDay = Math.min(day, lastDayOfTargetMonth);

        return new Date(targetYear, targetMonth, clampedDay);
    }

    function adjustForWeekend(d) {
        const dayOfWeek = d.getDay(); // 0 is Sunday, 6 is Saturday
        const res = new Date(d.getTime());
        if (dayOfWeek === 6) { // Saturday -> +2 days to Monday
            res.setDate(res.getDate() + 2);
        } else if (dayOfWeek === 0) { // Sunday -> +1 day to Monday
            res.setDate(res.getDate() + 1);
        }
        return res;
    }

    function formatDateIso(d) {
        const y = d.getFullYear();
        const m = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');
        return `${y}-${m}-${day}`;
    }

    function formatDateUi(d) {
        if (!d) return "-";
        const day = String(d.getDate()).padStart(2, '0');
        const m = String(d.getMonth() + 1).padStart(2, '0');
        const y = d.getFullYear();
        return `${day}/${m}/${y}`;
    }

    function parseIsoDate(isoStr) {
        if (!isoStr) return null;
        const parts = isoStr.split("-");
        if (parts.length !== 3) return null;
        return new Date(parseInt(parts[0], 10), parseInt(parts[1], 10) - 1, parseInt(parts[2], 10));
    }

    function parseUiDate(uiStr) {
        if (!uiStr) return null;
        const parts = uiStr.split("/");
        if (parts.length !== 3) return null;
        return new Date(parseInt(parts[2], 10), parseInt(parts[1], 10) - 1, parseInt(parts[0], 10));
    }

    // -------------------------------------------------------------
    // API CLIENT
    // -------------------------------------------------------------
    async function apiFetch(endpoint, options = {}) {
        const token = localStorage.getItem("naps_admin_token");
        const headers = options.headers || {};
        if (token) {
            headers["Authorization"] = `Bearer ${token}`;
        }
        if (!(options.body instanceof FormData) && !headers["Content-Type"]) {
            headers["Content-Type"] = "application/json";
        }
        options.headers = headers;

        const res = await fetch(endpoint, options);
        if (res.status === 401) {
            localStorage.removeItem("naps_admin_token");
            currentUser = null;
            showLoginGate();
            throw new Error("Session expired. Please sign in as administrator.");
        }
        return res;
    }

    // -------------------------------------------------------------
    // AUTHENTICATION
    // -------------------------------------------------------------
    async function checkAuthSession() {
        const token = localStorage.getItem("naps_admin_token");
        if (!token) {
            showLoginGate();
            return;
        }
        try {
            const res = await apiFetch("/api/auth/me");
            if (res.ok) {
                const data = await res.json();
                currentUser = data.username || "admin@company.com";
                showAuthenticatedPortal();
            } else {
                showLoginGate();
            }
        } catch (e) {
            showLoginGate();
        }
    }

    function showLoginGate() {
        document.getElementById("view-authenticated").style.display = "none";
        document.getElementById("view-login").style.display = "flex";
        const today = new Date();
        document.getElementById("login-sidebar-date").textContent = formatDateUi(today);
    }

    function showAuthenticatedPortal() {
        document.getElementById("view-login").style.display = "none";
        document.getElementById("view-authenticated").style.display = "flex";
        document.getElementById("session-user-email").textContent = currentUser || "admin@company.com";

        // Load initial dashboard
        loadDashboardData();
        loadWorkerConfig();
    }

    async function handleLoginSubmit(e) {
        e.preventDefault();
        const u = document.getElementById("login-username").value.trim();
        const p = document.getElementById("login-password").value;
        const btn = document.getElementById("btn-login-submit");
        btn.disabled = true;
        btn.textContent = "Signing in...";

        try {
            const res = await fetch("/api/auth/login", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ username: u, password: p })
            });
            const data = await res.json();
            if (res.ok && data.token) {
                localStorage.setItem("naps_admin_token", data.token);
                currentUser = data.user || u;
                showToast("Authentication successful! Loading system...", "success");
                showAuthenticatedPortal();
            } else {
                showToast(data.detail || "Access denied: Invalid administrator username or password.", "error");
            }
        } catch (err) {
            showToast("Network error signing in.", "error");
        } finally {
            btn.disabled = false;
            btn.textContent = "Sign In as Administrator";
        }
    }

    async function handleLogout() {
        try {
            await apiFetch("/api/auth/logout", { method: "POST" });
        } catch (e) {}
        localStorage.removeItem("naps_admin_token");
        currentUser = null;
        showLoginGate();
    }

    // -------------------------------------------------------------
    // NAVIGATION
    // -------------------------------------------------------------
    function switchNav(navKey) {
        document.querySelectorAll(".nav-radio-item").forEach(item => item.classList.remove("active"));
        document.querySelectorAll(".page-view").forEach(p => p.style.display = "none");

        const items = document.querySelectorAll(".nav-radio-item");
        const map = {
            "dashboard": { idx: 0, id: "page-dashboard" },
            "directory": { idx: 1, id: "page-directory" },
            "add-trainee": { idx: 2, id: "page-add-trainee" },
            "worker-dispatch": { idx: 3, id: "page-worker-dispatch" },
            "import-export": { idx: 4, id: "page-import-export" },
            "audit-exceptions": { idx: 5, id: "page-audit-exceptions" },
        };

        const target = map[navKey];
        if (target) {
            items[target.idx].classList.add("active");
            document.getElementById(target.id).style.display = "block";

            // Trigger data refresh on tab switch
            if (navKey === "dashboard") loadDashboardData();
            if (navKey === "directory") loadDirectoryData();
            if (navKey === "add-trainee") initAddTraineeForm();
            if (navKey === "worker-dispatch") loadWorkerDispatchData();
            if (navKey === "import-export") loadImportExportData();
            if (navKey === "audit-exceptions") loadAuditExceptionsData();
        }
    }

    // -------------------------------------------------------------
    // VIEW 1: DASHBOARD LOGIC
    // -------------------------------------------------------------
    async function loadDashboardData() {
        try {
            const statsRes = await apiFetch("/api/dashboard/stats");
            if (statsRes.ok) {
                const s = await statsRes.json();
                document.getElementById("kpi-total-trainees").textContent = s.total_trainees;
                document.getElementById("kpi-trainees-sub").textContent = `${s.active_count} Active • ${s.left_count} Left • ${s.completed_count} Completed`;

                document.getElementById("kpi-pending-schedules").textContent = s.pending_queue_count;
                if (s.overdue_count > 0) {
                    document.getElementById("kpi-pending-sub").innerHTML = `<span style="color: #B91C1C; font-weight: 600;">${s.overdue_count} Due/Overdue</span>`;
                } else {
                    document.getElementById("kpi-pending-sub").textContent = "All queues on schedule";
                }

                document.getElementById("kpi-delivered-milestones").textContent = s.simulated_sent_count;

                document.getElementById("kpi-delivery-exceptions").textContent = s.exceptions_count;
                if (s.exceptions_count > 0) {
                    document.getElementById("kpi-delivery-exceptions").style.color = "#991B1B";
                    document.getElementById("kpi-exceptions-sub").textContent = "Attention required";
                } else {
                    document.getElementById("kpi-delivery-exceptions").style.color = "#065F46";
                    document.getElementById("kpi-exceptions-sub").textContent = "All channels healthy";
                }

                document.getElementById("env-delivery-mode").textContent = s.delivery_mode;
                document.getElementById("env-system-date").textContent = s.today_ist || "-";
                document.getElementById("env-database-engine").textContent = s.database_engine || "PostgreSQL";

                // Target evaluation date default
                const today = new Date();
                document.getElementById("dash-target-date").value = formatDateIso(today);

                // Render recent activity feed
                const actList = s.recent_activity || [];
                const actDiv = document.getElementById("dash-recent-activity");
                if (actList.length === 0) {
                    actDiv.innerHTML = '<div style="color: #64748B; font-size: 0.85rem;">No audit activity logged yet.</div>';
                } else {
                    actDiv.innerHTML = actList.map(l => `
                        <div style="font-size: 0.825rem; margin-bottom: 0.5rem; line-height: 1.4;">
                            <div style="color: #475569;">
                                <b>${escapeHtml(l.timestamp)}</b> &bull; <code>${escapeHtml(l.action)}</code> on ${escapeHtml(l.entity_type)} (${escapeHtml(l.entity_id)}) by ${escapeHtml(l.actor)}
                            </div>
                            ${l.reason ? `<div style="color: #64748B; font-style: italic; margin-left: 8px;">Reason: ${escapeHtml(l.reason)}</div>` : ''}
                        </div>
                    `).join("");
                }

                // Render exceptions alert
                const excList = s.exceptions || [];
                const excDiv = document.getElementById("dash-exceptions-list");
                if (excList.length === 0) {
                    excDiv.innerHTML = '<div class="st-alert st-alert-success" style="margin-bottom: 0;">No delivery exceptions currently requiring attention.</div>';
                } else {
                    excDiv.innerHTML = excList.map(e => `
                        <div class="st-alert st-alert-error" style="margin-bottom: 0.5rem;">
                            <div style="font-weight: 600;">Schedule #${e.id} &bull; Trainee ${escapeHtml(e.trainee_id)} (${escapeHtml(e.trainee_name)}) &bull; ${STAGE_LABELS[e.stage] || e.stage}: ${e.status}</div>
                            <div style="font-size: 0.775rem; margin-top: 0.2rem;">Error Details: ${escapeHtml(e.last_error || "Unknown error")}</div>
                        </div>
                    `).join("");
                }
            }

            // Load upcoming queue
            const qRes = await apiFetch("/api/dashboard/queue");
            if (qRes.ok) {
                const qData = await qRes.json();
                const tbody = document.getElementById("dash-queue-tbody");
                const rows = qData.queue || [];
                if (rows.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; color: #64748B;">No pending schedules currently in queue.</td></tr>';
                } else {
                    tbody.innerHTML = rows.slice(0, 15).map(r => `
                        <tr>
                            <td><b>${r.queue_id}</b></td>
                            <td><code>${escapeHtml(r.trainee_id)}</code></td>
                            <td>${escapeHtml(r.trainee_name)}</td>
                            <td>${STAGE_LABELS[r.stage] || r.stage}</td>
                            <td>${r.scheduled_date}</td>
                            <td><span style="${r.due_status === 'Overdue' || r.due_status === 'Due Today' ? 'color: #B91C1C; font-weight: 600;' : 'color: #475569;'}">${r.due_status}</span></td>
                            <td><span class="badge badge-${r.status.toLowerCase()}">${r.status}</span></td>
                        </tr>
                    `).join("");
                }
            }
        } catch (err) {
            console.error("Dashboard load error", err);
        }
    }

    async function triggerWorkerDispatch(dateInputId, resultContainerId) {
        const dVal = document.getElementById(dateInputId).value;
        const resDiv = document.getElementById(resultContainerId);
        resDiv.innerHTML = '<div class="st-alert st-alert-info">Dispatching eligible schedules...</div>';

        try {
            const res = await apiFetch("/api/worker/run", {
                method: "POST",
                body: JSON.stringify({ target_date: dVal || null })
            });
            const data = await res.json();
            if (res.ok) {
                const sum = data.summary || {};
                const sent = sum.sent || 0;
                const claimed = sum.due || sum.claimed || 0;
                const failed = sum.failed || 0;
                resDiv.innerHTML = `
                    <div class="st-alert st-alert-success">
                        <b>Cycle completed successfully:</b> ${sent} sent, ${claimed} processed, ${failed} failed.
                    </div>
                `;
                // Refresh stats
                loadDashboardData();
            } else {
                resDiv.innerHTML = `<div class="st-alert st-alert-error">${data.detail || "Dispatch failed."}</div>`;
            }
        } catch (e) {
            resDiv.innerHTML = `<div class="st-alert st-alert-error">${e.message}</div>`;
        }
    }

    // -------------------------------------------------------------
    // VIEW 2: TRAINEE DIRECTORY LOGIC
    // -------------------------------------------------------------
    async function loadDirectoryData() {
        try {
            const res = await apiFetch("/api/trainees");
            if (res.ok) {
                const data = await res.json();
                allTraineesCache = data.trainees || [];

                // Populate Department dropdown
                const depts = Array.from(new Set(allTraineesCache.map(t => t.department).filter(Boolean))).sort();
                const deptSelect = document.getElementById("dir-dept-filter");
                const currentDept = deptSelect.value;
                deptSelect.innerHTML = '<option value="All">All</option>' + depts.map(d => `<option value="${escapeHtml(d)}">${escapeHtml(d)}</option>`).join("");
                if (depts.includes(currentDept)) deptSelect.value = currentDept;

                filterDirectoryTable();
                populateTraineeSelect();
            }
        } catch (err) {
            console.error("Directory load error", err);
        }
    }

    function parseDateUniversal(str) {
        if (!str || str === "-" || str === "Missing") return null;
        if (str.includes("-")) {
            const parts = str.split("-");
            if (parts.length === 3) {
                return new Date(parseInt(parts[0], 10), parseInt(parts[1], 10) - 1, parseInt(parts[2], 10));
            }
        } else if (str.includes("/")) {
            const parts = str.split("/");
            if (parts.length === 3) {
                return new Date(parseInt(parts[2], 10), parseInt(parts[1], 10) - 1, parseInt(parts[0], 10));
            }
        }
        return null;
    }

    function addMonthsClamped(d, n) {
        const targetYear = d.getFullYear() + Math.floor((d.getMonth() + n) / 12);
        const targetMonth = ((d.getMonth() + n) % 12 + 12) % 12;
        const lastDayOfTargetMonth = new Date(targetYear, targetMonth + 1, 0).getDate();
        const targetDay = Math.min(d.getDate(), lastDayOfTargetMonth);
        return new Date(targetYear, targetMonth, targetDay);
    }

    function adjustWeekendJS(d) {
        const day = d.getDay(); // 0 is Sunday, 6 is Saturday
        const res = new Date(d);
        if (day === 6) { // Saturday -> Monday (+2 days)
            res.setDate(res.getDate() + 2);
        } else if (day === 0) { // Sunday -> Monday (+1 day)
            res.setDate(res.getDate() + 1);
        }
        return res;
    }

    function formatUIDateJS(d) {
        const dd = String(d.getDate()).padStart(2, "0");
        const mm = String(d.getMonth() + 1).padStart(2, "0");
        const yyyy = d.getFullYear();
        return `${dd}/${mm}/${yyyy}`;
    }

    function computeAutoScheduledDateUI(dojStr, lwdStr, stageKey) {
        const doj = parseDateUniversal(dojStr);
        if (!doj) return "-";
        let lwd = parseDateUniversal(lwdStr);
        if (!lwd) {
            lwd = addMonthsClamped(doj, 12);
        }
        const stg = (stageKey || "").toUpperCase();
        let targetDate = null;
        if (stg === "INITIAL") {
            targetDate = new Date(doj);
            targetDate.setDate(targetDate.getDate() + 15);
        } else if (stg === "Q1") {
            targetDate = addMonthsClamped(doj, 3);
        } else if (stg === "Q2") {
            targetDate = addMonthsClamped(doj, 6);
        } else if (stg === "Q3") {
            targetDate = addMonthsClamped(doj, 9);
        } else if (stg === "Q4") {
            targetDate = addMonthsClamped(doj, 12);
        } else if (stg === "EXIT") {
            targetDate = addMonthsClamped(lwd, 3);
        }
        if (!targetDate) return "-";
        const shifted = adjustWeekendJS(targetDate);
        return formatUIDateJS(shifted);
    }

    function formatStageCellBadge(s, t, stageKey) {
        let dt = s && s.scheduled_date ? s.scheduled_date : "";
        if (!dt || dt === "-") {
            if (t && (t.date_of_joining_raw || t.date_of_joining)) {
                dt = computeAutoScheduledDateUI(t.date_of_joining_raw || t.date_of_joining, t.last_working_date_raw || t.last_working_date, stageKey);
            }
        }
        if (!dt) dt = "-";
        if (s && s.status === "Sent") return `${dt} <span class="badge badge-sent">[Sent]</span>`;
        if (s && s.is_opted_out) return `${dt} <span class="badge badge-cancelled">[Opted Out]</span>`;
        if (s && s.status === "Cancelled") return `${dt} <span class="badge badge-cancelled">[Cancelled]</span>`;
        if (s && s.status === "Uncertain") return `${dt} <span class="badge badge-uncertain">[Uncertain]</span>`;
        if (s && s.status === "Processing") return `${dt} <span class="badge badge-processing">[Processing]</span>`;
        if (s && s.is_custom_date) return `${dt} <span class="badge badge-scheduled">[Custom Override]</span>`;
        return `${dt} <span class="badge badge-scheduled">[Scheduled]</span>`;
    }

    function filterDirectoryTable() {
        const query = (document.getElementById("dir-search-input").value || "").toLowerCase().trim();
        const statusFilter = document.getElementById("dir-status-filter").value;
        const deptFilter = document.getElementById("dir-dept-filter").value;

        const filtered = allTraineesCache.filter(t => {
            if (statusFilter !== "All" && t.status !== statusFilter) return false;
            if (deptFilter !== "All" && t.department !== deptFilter) return false;
            if (query) {
                const fields = [t.trainee_id, t.trainee_name, t.trainee_email, t.department, t.location, t.manager_name, t.manager_email];
                if (!fields.some(f => (f || "").toLowerCase().includes(query))) return false;
            }
            return true;
        });

        document.getElementById("dir-count-caption").textContent = `Showing ${filtered.length} of ${allTraineesCache.length} registered apprentices.`;

        const tbody = document.getElementById("master-directory-tbody");
        if (filtered.length === 0) {
            tbody.innerHTML = '<tr><td colspan="13" style="text-align: center; color: #64748B;">No trainees found matching current criteria.</td></tr>';
            return;
        }

        tbody.innerHTML = filtered.map(t => {
            const stg = t.stages || {};
            const getStageObj = (key) => stg[key] || stg[key.toUpperCase()] || stg[key.toLowerCase()];
            return `
                <tr>
                    <td><b>${escapeHtml(t.trainee_id)}</b></td>
                    <td>${escapeHtml(t.trainee_name)}</td>
                    <td><span class="badge badge-${t.status.toLowerCase().replace(' ', '_')}">${t.status}</span></td>
                    <td>${t.date_of_joining}</td>
                    <td>${t.last_working_date}</td>
                    <td>${formatStageCellBadge(getStageObj("INITIAL"), t, "INITIAL")}</td>
                    <td>${formatStageCellBadge(getStageObj("Q1"), t, "Q1")}</td>
                    <td>${formatStageCellBadge(getStageObj("Q2"), t, "Q2")}</td>
                    <td>${formatStageCellBadge(getStageObj("Q3"), t, "Q3")}</td>
                    <td>${formatStageCellBadge(getStageObj("Q4"), t, "Q4")}</td>
                    <td>${formatStageCellBadge(getStageObj("EXIT"), t, "EXIT")}</td>
                    <td>${escapeHtml(t.department || "-")}</td>
                    <td>${escapeHtml(t.manager_name || "-")}</td>
                </tr>
            `;
        }).join("");
    }

    function populateTraineeSelect() {
        const sel = document.getElementById("dir-select-trainee");
        const prevVal = sel.value;
        sel.innerHTML = '<option value="">-- Choose Trainee --</option>' + allTraineesCache.map(t => `
            <option value="${escapeHtml(t.trainee_id)}">${escapeHtml(t.trainee_id)} - ${escapeHtml(t.trainee_name)} (${t.status})</option>
        `).join("");

        if (prevVal && allTraineesCache.some(t => t.trainee_id === prevVal)) {
            sel.value = prevVal;
            loadSelectedTraineeDetails();
        }
    }

    async function loadSelectedTraineeDetails() {
        const traineeId = document.getElementById("dir-select-trainee").value;
        const container = document.getElementById("dir-details-container");
        if (!traineeId) {
            container.style.display = "none";
            currentSelectedTrainee = null;
            return;
        }

        try {
            const res = await apiFetch(`/api/trainees/${traineeId}`);
            if (res.ok) {
                const data = await res.json();
                currentSelectedTrainee = data;
                container.style.display = "block";
                renderTraineeTabs(data);
            }
        } catch (e) {
            showToast("Failed to load trainee details.", "error");
        }
    }

    function switchDirectoryTab(tabId) {
        document.querySelectorAll("#dir-details-container .st-tab-btn").forEach(btn => btn.classList.remove("active"));
        document.querySelectorAll("#dir-details-container .st-tab-pane").forEach(pane => pane.classList.remove("active"));

        event.target.classList.add("active");
        document.getElementById(tabId).classList.add("active");
    }

    function renderTraineeTabs(data) {
        const t = data.trainee;
        const scheds = data.schedules || [];

        // Tab 1: Summary Table
        const sumTbody = document.getElementById("trainee-schedules-summary-tbody");
        sumTbody.innerHTML = scheds.map(s => {
            const details = s.last_error || s.cancellation_reason || (s.sent_at ? `Sent to ${s.recipient_email_used || '-'}` : '-');
            return `
                <tr>
                    <td><b>${STAGE_LABELS[s.stage] || s.stage}</b> (<code>${s.stage}</code>)</td>
                    <td>${s.recipient_role || STAGE_ROLES[s.stage] || 'Trainee'}</td>
                    <td>${s.original_due_date || '-'}</td>
                    <td>${s.scheduled_date}</td>
                    <td>${s.is_custom_date ? 'Custom Override' : 'Automatic (Weekend Adjusted)'}</td>
                    <td>${s.is_opted_out ? 'Opted Out' : 'Active (Enabled)'}</td>
                    <td><span class="badge badge-${s.status.toLowerCase()}">${s.status}</span></td>
                    <td>${s.attempt_count}</td>
                    <td>${escapeHtml(details)}</td>
                </tr>
            `;
        }).join("");

        // Tab 1: 2-Column form to adjust stages
        const grid = document.getElementById("sync-stages-inputs-grid");
        grid.innerHTML = scheds.map(s => {
            const isSent = s.status === "Sent";
            return `
                <div style="background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; padding: 1rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.35rem;">
                        <span style="font-weight: 700; color: #0F172A;">${STAGE_LABELS[s.stage] || s.stage} (<code>${s.stage}</code>)</span>
                        <span class="badge badge-${s.status.toLowerCase()}">${s.status}</span>
                    </div>
                    <div style="font-size: 0.775rem; color: #64748B; margin-bottom: 0.75rem;">
                        Recipient: ${s.recipient_role || STAGE_ROLES[s.stage]} &bull; Math Due: ${s.original_due_date || '-'}
                    </div>

                    ${isSent ? `
                        <div class="st-alert st-alert-info" style="margin-bottom: 0;">
                            Delivered on ${s.scheduled_date} to ${escapeHtml(s.recipient_email_used || '-')}. Record is immutable.
                        </div>
                    ` : `
                        <label class="st-checkbox-label">
                            <input type="checkbox" class="st-checkbox" id="sync-opt-${s.stage}" ${s.is_opted_out ? 'checked' : ''}>
                            Opt Out (Disable stage)
                        </label>
                        <div class="form-group" style="margin-top: 0.5rem; margin-bottom: 0.25rem;">
                            <label class="form-label" for="sync-dt-${s.stage}">Scheduled Date</label>
                            <input type="date" class="st-input" id="sync-dt-${s.stage}" value="${s.scheduled_date_raw || ''}">
                        </div>
                        ${s.is_custom_date ? `
                            <label class="st-checkbox-label" style="margin-top: 0.4rem;">
                                <input type="checkbox" class="st-checkbox" id="sync-clear-${s.stage}">
                                Reset to automatic calculated date
                            </label>
                        ` : ''}
                    `}
                </div>
            `;
        }).join("");

        // Tab 2: Profile Info
        const profGrid = document.getElementById("profile-info-grid");
        profGrid.innerHTML = `
            <div>
                <div><b>Trainee ID:</b> <code>${escapeHtml(t.trainee_id)}</code></div>
                <div><b>Full Name:</b> ${escapeHtml(t.trainee_name)}</div>
                <div><b>Email Address:</b> <code>${escapeHtml(t.trainee_email)}</code></div>
                <div><b>Status:</b> <code>${escapeHtml(t.status)}</code></div>
            </div>
            <div>
                <div><b>Date of Joining (DOJ):</b> ${t.date_of_joining}</div>
                <div><b>Last Working Date (LWD):</b> ${t.last_working_date} <i>(${t.lwd_mode === 'auto' ? 'Auto (DOJ + 12m)' : 'Manual Override'})</i></div>
                <div><b>Department:</b> ${escapeHtml(t.department || "-")}</div>
                <div><b>Location:</b> ${escapeHtml(t.location || "-")}</div>
            </div>
            <div>
                <div><b>Reporting Manager:</b> ${escapeHtml(t.manager_name || "-")}</div>
                <div><b>Manager Email:</b> <code>${escapeHtml(t.manager_email || "-")}</code></div>
                <div><b>Registration Date:</b> ${t.created_at || "-"}</div>
                <div><b>Last Updated:</b> ${t.updated_at || "-"}</div>
            </div>
        `;

        // Tab 3: Edit Trainee Form
        document.getElementById("edit-name").value = t.trainee_name || "";
        document.getElementById("edit-email").value = t.trainee_email || "";
        document.getElementById("edit-mgr-name").value = t.manager_name || "";
        document.getElementById("edit-mgr-email").value = t.manager_email || "";
        document.getElementById("edit-dept").value = t.department || "";
        document.getElementById("edit-loc").value = t.location || "";
        document.getElementById("edit-doj").value = t.date_of_joining_raw || "";
        document.getElementById("edit-status").value = t.status || "Active";
        document.getElementById("edit-lwd").value = t.last_working_date_raw || "";

        if (t.lwd_mode === "auto") {
            document.getElementById("edit-lwd-mode-auto").checked = true;
        } else {
            document.getElementById("edit-lwd-mode-manual").checked = true;
        }

        toggleEditStatusConfirmation();
    }

    function toggleEditLwdMode() {
        const isAuto = document.getElementById("edit-lwd-mode-auto").checked;
        if (isAuto) {
            recalculateEditLwdPreview();
        }
    }

    function recalculateEditLwdPreview() {
        const dojVal = document.getElementById("edit-doj").value;
        if (!dojVal) return;
        const doj = parseIsoDate(dojVal);
        if (!doj) return;

        const isAuto = document.getElementById("edit-lwd-mode-auto").checked;
        if (isAuto) {
            const autoLwd = addCalendarMonths(doj, 12);
            document.getElementById("edit-lwd").value = formatDateIso(autoLwd);
        }
    }

    function toggleEditStatusConfirmation() {
        const st = document.getElementById("edit-status").value;
        const box = document.getElementById("edit-left-confirm-box");
        box.style.display = st === "Left" ? "block" : "none";
    }

    async function handleSaveStagePreferences(e) {
        e.preventDefault();
        if (!currentSelectedTrainee) return;
        const traineeId = currentSelectedTrainee.trainee.trainee_id;
        const scheds = currentSelectedTrainee.schedules || [];

        const payloadStages = {};
        for (const s of scheds) {
            if (s.status === "Sent") continue;
            const optEl = document.getElementById(`sync-opt-${s.stage}`);
            const dtEl = document.getElementById(`sync-dt-${s.stage}`);
            const clearEl = document.getElementById(`sync-clear-${s.stage}`);

            payloadStages[s.stage] = {
                opt_out: optEl ? optEl.checked : s.is_opted_out,
                scheduled_date: dtEl && dtEl.value ? formatDateUi(parseIsoDate(dtEl.value)) : null,
                clear_custom_date: clearEl ? clearEl.checked : false
            };
        }

        try {
            const res = await apiFetch(`/api/trainees/${traineeId}/schedules`, {
                method: "PUT",
                body: JSON.stringify({ stages: payloadStages })
            });
            if (res.ok) {
                showToast(`Email stages for trainee ${traineeId} synchronized and saved to database!`, "success");
                loadSelectedTraineeDetails();
                loadDirectoryData();
            } else {
                const err = await res.json();
                showToast(err.detail || "Error saving stage preferences.", "error");
            }
        } catch (e) {
            showToast("Network error saving stage preferences.", "error");
        }
    }

    async function handleEditTraineeSubmit(e) {
        e.preventDefault();
        if (!currentSelectedTrainee) return;
        const traineeId = currentSelectedTrainee.trainee.trainee_id;

        const statusVal = document.getElementById("edit-status").value;
        const confirmChk = document.getElementById("edit-chk-confirm-lwd");
        if (statusVal === "Left" && (!confirmChk || !confirmChk.checked)) {
            showToast("Confirmation Required: Status is 'Left'. You must confirm the actual Last Working Date.", "error");
            return;
        }

        const isAuto = document.getElementById("edit-lwd-mode-auto").checked;

        const payload = {
            trainee_name: document.getElementById("edit-name").value.trim(),
            trainee_email: document.getElementById("edit-email").value.trim(),
            manager_name: document.getElementById("edit-mgr-name").value.trim(),
            manager_email: document.getElementById("edit-mgr-email").value.trim(),
            department: document.getElementById("edit-dept").value.trim(),
            location: document.getElementById("edit-loc").value.trim(),
            date_of_joining: formatDateUi(parseIsoDate(document.getElementById("edit-doj").value)),
            last_working_date: formatDateUi(parseIsoDate(document.getElementById("edit-lwd").value)),
            status: statusVal,
            lwd_mode: isAuto ? "auto" : "manual",
            confirmed_actual_lwd: confirmChk ? confirmChk.checked : false,
            manual_lwd_reviewed: true
        };

        try {
            const res = await apiFetch(`/api/trainees/${traineeId}`, {
                method: "PUT",
                body: JSON.stringify(payload)
            });
            if (res.ok) {
                showToast(`Trainee ${traineeId} updated and schedules reconciled successfully!`, "success");
                loadSelectedTraineeDetails();
                loadDirectoryData();
            } else {
                const err = await res.json();
                showToast(err.detail || "Error updating trainee.", "error");
            }
        } catch (e) {
            showToast("Network error updating trainee.", "error");
        }
    }

    async function handleArchiveCurrentTrainee() {
        if (!currentSelectedTrainee) return;
        const tid = currentSelectedTrainee.trainee.trainee_id;
        if (!confirm(`Are you sure you want to archive trainee ${tid}?`)) return;

        try {
            const res = await apiFetch(`/api/trainees/${tid}/archive`, { method: "POST" });
            if (res.ok) {
                showToast(`Trainee ${tid} archived successfully.`, "success");
                document.getElementById("dir-details-container").style.display = "none";
                loadDirectoryData();
            } else {
                const err = await res.json();
                showToast(err.detail || "Failed to archive.", "error");
            }
        } catch (e) {
            showToast("Error archiving trainee.", "error");
        }
    }

    // -------------------------------------------------------------
    // VIEW 3: ADD TRAINEE LOGIC
    // -------------------------------------------------------------
    function initAddTraineeForm() {
        const today = new Date();
        document.getElementById("add-doj").value = formatDateIso(today);
        document.getElementById("add-chk-custom-lwd").checked = false;
        document.getElementById("add-custom-lwd-box").style.display = "none";
        document.getElementById("add-left-confirm-box").style.display = "none";
        calculateAddTraineeMilestones();
    }

    function toggleAddCustomLwdInput() {
        const chk = document.getElementById("add-chk-custom-lwd").checked;
        document.getElementById("add-custom-lwd-box").style.display = chk ? "block" : "none";
        calculateAddTraineeMilestones();
    }

    function toggleAddStatusConfirmation() {
        const st = document.getElementById("add-status").value;
        document.getElementById("add-left-confirm-box").style.display = st === "Left" ? "block" : "none";
    }

    function calculateAddTraineeMilestones() {
        const dojStr = document.getElementById("add-doj").value;
        if (!dojStr) return;
        const doj = parseIsoDate(dojStr);
        if (!doj) return;

        // Auto LWD: DOJ + 12 calendar months
        const autoLwd = addCalendarMonths(doj, 12);
        document.getElementById("add-auto-lwd-display").textContent = formatDateUi(autoLwd);

        // Effective LWD
        const useCustom = document.getElementById("add-chk-custom-lwd").checked;
        const customLwdVal = document.getElementById("add-custom-lwd").value;
        const customLwd = useCustom && customLwdVal ? parseIsoDate(customLwdVal) : null;
        const effectiveLwd = customLwd || autoLwd;

        // Calculate 6 stages identically to date_engine.py
        const mathDates = {
            "initial": new Date(doj.getTime() + 15 * 86400000),
            "q1": addCalendarMonths(doj, 3),
            "q2": addCalendarMonths(doj, 6),
            "q3": addCalendarMonths(doj, 9),
            "q4": addCalendarMonths(doj, 12),
            "exit": addCalendarMonths(effectiveLwd, 3),
        };

        const schedDates = {
            "initial": adjustForWeekend(mathDates.initial),
            "q1": adjustForWeekend(mathDates.q1),
            "q2": adjustForWeekend(mathDates.q2),
            "q3": adjustForWeekend(mathDates.q3),
            "q4": adjustForWeekend(mathDates.q4),
            "exit": adjustForWeekend(mathDates.exit),
        };

        const grid = document.getElementById("add-stages-preview-grid");
        grid.innerHTML = STAGES_ORDER.map(stg => `
            <div style="background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 6px; padding: 0.85rem;">
                <label class="st-checkbox-label" style="font-weight: 600;">
                    <input type="checkbox" class="st-checkbox" id="add-opt-${stg}" checked>
                    Enable ${STAGE_LABELS[stg]}
                </label>
                <div class="form-group" style="margin-top: 0.5rem; margin-bottom: 0;">
                    <label class="form-label" for="add-dt-${stg}" style="font-size: 0.775rem;">Scheduled Date (${stg})</label>
                    <input type="date" class="st-input" id="add-dt-${stg}" value="${formatDateIso(schedDates[stg])}">
                    <div class="form-caption">Math Due: ${formatDateUi(mathDates[stg])}</div>
                </div>
            </div>
        `).join("");
    }

    async function handleCreateTraineeSubmit(e) {
        e.preventDefault();

        const stVal = document.getElementById("add-status").value;
        const confirmChk = document.getElementById("add-chk-confirm-lwd");
        if (stVal === "Left" && (!confirmChk || !confirmChk.checked)) {
            showToast("Confirmation Required: Status is 'Left'. Please confirm actual LWD.", "error");
            return;
        }

        const dojVal = document.getElementById("add-doj").value;
        const useCustom = document.getElementById("add-chk-custom-lwd").checked;
        const customLwdVal = document.getElementById("add-custom-lwd").value;

        const stagePrefs = {};
        for (const stg of STAGES_ORDER) {
            const enabled = document.getElementById(`add-opt-${stg}`).checked;
            const chosenDateStr = document.getElementById(`add-dt-${stg}`).value;
            stagePrefs[stg] = {
                opt_out: !enabled,
                custom_date: chosenDateStr ? formatDateUi(parseIsoDate(chosenDateStr)) : null
            };
        }

        const payload = {
            trainee_id: document.getElementById("add-id").value.trim(),
            trainee_name: document.getElementById("add-name").value.trim(),
            trainee_email: document.getElementById("add-email").value.trim(),
            date_of_joining: formatDateUi(parseIsoDate(dojVal)),
            manager_name: document.getElementById("add-mgr-name").value.trim(),
            manager_email: document.getElementById("add-mgr-email").value.trim(),
            department: document.getElementById("add-dept").value.trim(),
            location: document.getElementById("add-loc").value.trim(),
            status: stVal,
            last_working_date: useCustom && customLwdVal ? formatDateUi(parseIsoDate(customLwdVal)) : null,
            confirmed_actual_lwd: confirmChk ? confirmChk.checked : false,
            stage_preferences: stagePrefs
        };

        try {
            const res = await apiFetch("/api/trainees", {
                method: "POST",
                body: JSON.stringify(payload)
            });
            const data = await res.json();
            if (res.ok) {
                showToast(`Trainee ${payload.trainee_id} and 6 schedules created successfully!`, "success");
                document.getElementById("form-create-trainee").reset();
                initAddTraineeForm();
                switchNav("directory");
            } else {
                showToast(data.detail || "Validation error creating trainee.", "error");
            }
        } catch (e) {
            showToast("Network error creating trainee.", "error");
        }
    }

    // -------------------------------------------------------------
    // VIEW 4: WORKER & DISPATCH LOGIC
    // -------------------------------------------------------------
    async function loadWorkerConfig() {
        try {
            const res = await apiFetch("/api/worker/config");
            if (res.ok) {
                const c = await res.json();
                document.getElementById("worker-sender-email").textContent = c.sender_email;
                document.getElementById("worker-smtp-server").textContent = `${c.smtp_host}:${c.smtp_port} (${c.smtp_use_tls ? 'STARTTLS' : 'PLAIN'})`;
                document.getElementById("worker-smtp-auth").innerHTML = c.has_password
                    ? '<span style="color: #065F46; font-weight: 600;">Configured</span>'
                    : '<span style="color: #B91C1C; font-weight: 600;">Not Set &bull; Configure in .env</span>';
                document.getElementById("worker-delivery-mode-html").innerHTML = c.is_dry_run
                    ? '<span style="color: #B45309; font-weight: 600;">Simulation (Dry-Run Enabled)</span>'
                    : '<span style="color: #065F46; font-weight: 600;">Live SMTP Transmission</span>';

                document.getElementById("worker-card-mode").textContent = c.delivery_mode;
            }
        } catch (e) {}
    }

    async function loadWorkerDispatchData() {
        loadWorkerConfig();
        const today = new Date();
        document.getElementById("worker-target-date").value = formatDateIso(today);

        // Load queued schedules
        try {
            const res = await apiFetch("/api/dashboard/queue");
            if (res.ok) {
                const q = await res.json();
                const tbody = document.getElementById("worker-queue-tbody");
                const rows = q.queue || [];
                if (rows.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; color: #64748B;">No pending schedules currently queued.</td></tr>';
                } else {
                    tbody.innerHTML = rows.map(r => `
                        <tr>
                            <td><b>${r.queue_id}</b></td>
                            <td><code>${escapeHtml(r.trainee_id)}</code></td>
                            <td>${escapeHtml(r.trainee_name)}</td>
                            <td>${STAGE_LABELS[r.stage] || r.stage}</td>
                            <td>${r.scheduled_date}</td>
                            <td><span class="badge badge-${r.status.toLowerCase()}">${r.status}</span></td>
                            <td>${r.attempt_count}</td>
                        </tr>
                    `).join("");
                }
            }
        } catch (e) {}
    }

    // -------------------------------------------------------------
    // VIEW 5: EXCEL / CSV IMPORT & EXPORT LOGIC
    // -------------------------------------------------------------
    async function loadImportExportData() {
        // Populate Database Cleanup multiselect
        try {
            const res = await apiFetch("/api/trainees");
            if (res.ok) {
                const data = await res.json();
                const list = data.trainees || [];
                const sel = document.getElementById("db-cleanup-select");
                if (list.length === 0) {
                    sel.innerHTML = '<option disabled>No active trainees currently exist in database</option>';
                } else {
                    sel.innerHTML = list.map(t => `
                        <option value="${escapeHtml(t.trainee_id)}">${escapeHtml(t.trainee_id)} - ${escapeHtml(t.trainee_name)} (${escapeHtml(t.department || 'N/A')}, ${t.status})</option>
                    `).join("");
                }
            }
        } catch (e) {}
    }

    function downloadTemplate(fmt) {
        window.location.href = `/api/templates/download?format=${fmt}`;
    }

    function exportDatabase(fmt) {
        window.location.href = `/api/export/directory?format=${fmt}`;
    }

    async function handleFileUpload(e) {
        const file = e.target.files[0];
        if (!file) return;

        const formData = new FormData();
        formData.append("file", file);

        showToast("Uploading and validating file...", "info");

        try {
            const res = await apiFetch("/api/import/preview", {
                method: "POST",
                body: formData
            });
            const data = await res.json();
            if (res.ok) {
                stagedRowsCache = data.staged_rows || [];
                stagedOverrides = {};

                renderStagingPreview(data);
                showToast(`Validated ${stagedRowsCache.length} records.`, "success");
            } else {
                showToast(data.detail || "Error parsing file.", "error");
            }
        } catch (err) {
            showToast("Network error uploading file.", "error");
        }
    }

    function renderStagingPreview(data) {
        document.getElementById("staging-container").style.display = "block";

        const newCount = stagedRowsCache.filter(r => !r.is_existing).length;
        const updCount = stagedRowsCache.filter(r => r.is_existing).length;

        document.getElementById("staging-kpi-total").textContent = stagedRowsCache.length;
        document.getElementById("staging-kpi-new").textContent = newCount;
        document.getElementById("staging-kpi-upd").textContent = updCount;
        document.getElementById("staging-kpi-overrides").textContent = Object.keys(stagedOverrides).length;

        // Render preview table
        const tbody = document.getElementById("staging-preview-tbody");
        tbody.innerHTML = stagedRowsCache.map((item, idx) => {
            const stgMap = item.stages || {};
            function fmtCol(code) {
                const s = stgMap[code] || stgMap[code.toUpperCase()] || stgMap[code.toLowerCase()];
                let d = s ? (s.date || s.scheduled_date || "") : "";
                if (!d || d === "-") {
                    d = computeAutoScheduledDateUI(item.date_of_joining, item.last_working_date, code);
                }
                if (!d) d = "-";
                if (s && (s.opt_out || s.is_opted_out)) return `${d} <span class="badge badge-cancelled">[Opted Out]</span>`;
                if (s && (s.is_custom || s.is_custom_date)) return `${d} <span class="badge badge-scheduled">[Custom Override]</span>`;
                return `${d} <span class="badge badge-scheduled">[Scheduled]</span>`;
            }

            return `
                <tr>
                    <td>${idx + 2}</td>
                    <td><b>${escapeHtml(item.trainee_id)}</b></td>
                    <td>${escapeHtml(item.trainee_name)}</td>
                    <td><span class="badge ${item.is_existing ? 'badge-processing' : 'badge-completed'}">${item.is_existing ? 'Update (Existing)' : 'New Registration'}</span></td>
                    <td>${item.date_of_joining || '-'}</td>
                    <td>${item.last_working_date || '-'}</td>
                    <td><span class="badge badge-${(item.status || 'Active').toLowerCase()}">${item.status || 'Active'}</span></td>
                    <td>${fmtCol("initial")}</td>
                    <td>${fmtCol("q1")}</td>
                    <td>${fmtCol("q2")}</td>
                    <td>${fmtCol("q3")}</td>
                    <td>${fmtCol("q4")}</td>
                    <td>${fmtCol("exit")}</td>
                </tr>
            `;
        }).join("");

        // Populate Delete Staging rows select
        const delSelect = document.getElementById("staging-del-select");
        delSelect.innerHTML = stagedRowsCache.map((item, idx) => `
            <option value="${idx}">Row ${idx + 2}: ${escapeHtml(item.trainee_id)} - ${escapeHtml(item.trainee_name)} (${escapeHtml(item.status || 'Active')})</option>
        `).join("");

        // Populate Employee Configurator select
        const empSelect = document.getElementById("staging-emp-select");
        empSelect.innerHTML = '<option value="">-- Choose Employee --</option>' + stagedRowsCache.map((item, idx) => `
            <option value="${idx}">Row ${idx + 2}: ${escapeHtml(item.trainee_id)} - ${escapeHtml(item.trainee_name)} (${item.is_existing ? 'Update' : 'New'})</option>
        `).join("");
    }

    function deleteSelectedStagedRows() {
        const sel = document.getElementById("staging-del-select");
        const indices = Array.from(sel.selectedOptions).map(o => parseInt(o.value, 10)).sort((a, b) => b - a);
        if (indices.length === 0) {
            showToast("Please select at least one row to remove.", "warning");
            return;
        }

        for (const idx of indices) {
            const tid = stagedRowsCache[idx].trainee_id;
            delete stagedOverrides[tid];
            stagedRowsCache.splice(idx, 1);
        }

        showToast(`Removed ${indices.length} row(s) from staged import.`, "success");
        renderStagingPreview({ staged_rows: stagedRowsCache });
    }

    function clearEntireStagedUpload() {
        stagedRowsCache = [];
        stagedOverrides = {};
        document.getElementById("file-upload-input").value = "";
        document.getElementById("staging-container").style.display = "none";
        showToast("Staged upload discarded.", "info");
    }

    function loadStagedEmployeeScheduleConfig() {
        const selVal = document.getElementById("staging-emp-select").value;
        const box = document.getElementById("staging-emp-config-box");
        if (selVal === "") {
            box.style.display = "none";
            return;
        }

        const idx = parseInt(selVal, 10);
        const emp = stagedRowsCache[idx];
        if (!emp) return;

        box.style.display = "block";
        document.getElementById("staging-emp-config-title").innerHTML = `
            Configuring Email Stage Schedules for: <code>${escapeHtml(emp.trainee_id)}</code> &mdash; <b>${escapeHtml(emp.trainee_name)}</b>
        `;
        document.getElementById("staging-emp-existing-notice").style.display = emp.is_existing ? "block" : "none";

        const grid = document.getElementById("staging-emp-stages-grid");
        const stgMap = emp.stages || {};
        grid.innerHTML = STAGES_ORDER.map(stg => {
            const sInfo = stgMap[stg] || {};
            const curDate = sInfo.date || "-";
            const curOpt = sInfo.opt_out || false;
            let isoDate = "";
            if (curDate && curDate !== "-") {
                const parsed = parseUiDate(curDate);
                if (parsed) isoDate = formatDateIso(parsed);
            }

            return `
                <div style="background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 6px; padding: 0.85rem;">
                    <div style="font-weight: 600; color: #0F172A; margin-bottom: 0.25rem;">
                        ${STAGE_LABELS[stg]} (<code>${stg}</code>)
                    </div>
                    <div style="font-size: 0.775rem; color: #64748B; margin-bottom: 0.5rem;">
                        Role: ${STAGE_ROLES[stg]}
                    </div>
                    <label class="st-checkbox-label">
                        <input type="checkbox" class="st-checkbox" id="cfg-opt-${stg}" ${curOpt ? 'checked' : ''}>
                        Opt Out (Disable stage)
                    </label>
                    <div class="form-group" style="margin-top: 0.4rem; margin-bottom: 0;">
                        <label class="form-label" for="cfg-dt-${stg}" style="font-size: 0.775rem;">Scheduled Date</label>
                        <input type="date" class="st-input" id="cfg-dt-${stg}" value="${isoDate}">
                    </div>
                </div>
            `;
        }).join("");
    }

    function saveStagedEmployeeConfig() {
        const selVal = document.getElementById("staging-emp-select").value;
        if (selVal === "") return;
        const idx = parseInt(selVal, 10);
        const emp = stagedRowsCache[idx];
        if (!emp) return;

        const tid = emp.trainee_id;
        if (!stagedOverrides[tid]) stagedOverrides[tid] = {};
        if (!emp.stages) emp.stages = {};

        for (const stg of STAGES_ORDER) {
            const optVal = document.getElementById(`cfg-opt-${stg}`).checked;
            const dtVal = document.getElementById(`cfg-dt-${stg}`).value;
            const uiDate = dtVal ? formatDateUi(parseIsoDate(dtVal)) : "-";

            emp.stages[stg] = {
                date: uiDate,
                opt_out: optVal,
                is_custom: true
            };

            stagedOverrides[tid][stg] = {
                scheduled_date: uiDate,
                opt_out: optVal
            };
        }

        showToast(`Schedule preferences and dates updated for ${tid}. Reflected in preview table.`, "success");
        renderStagingPreview({ staged_rows: stagedRowsCache });
    }

    function deleteCurrentStagedEmployee() {
        const selVal = document.getElementById("staging-emp-select").value;
        if (selVal === "") return;
        const idx = parseInt(selVal, 10);
        const tid = stagedRowsCache[idx].trainee_id;
        delete stagedOverrides[tid];
        stagedRowsCache.splice(idx, 1);
        document.getElementById("staging-emp-config-box").style.display = "none";
        showToast(`Removed row for ${tid} from staged import.`, "success");
        renderStagingPreview({ staged_rows: stagedRowsCache });
    }

    function resetStagedEmployeeOverrides() {
        const selVal = document.getElementById("staging-emp-select").value;
        if (selVal === "") return;
        const idx = parseInt(selVal, 10);
        const emp = stagedRowsCache[idx];
        delete stagedOverrides[emp.trainee_id];
        showToast("Reverted overrides for this employee.", "info");
        loadStagedEmployeeScheduleConfig();
    }

    async function commitStagedRows() {
        if (stagedRowsCache.length === 0) {
            showToast("No staged rows to commit.", "warning");
            return;
        }

        const btn = document.getElementById("btn-commit-staging");
        btn.disabled = true;
        btn.textContent = "Committing Records...";
        const resDiv = document.getElementById("commit-result-box");
        resDiv.innerHTML = '<div class="st-alert st-alert-info">Persisting and synchronizing schedules...</div>';

        const tids = stagedRowsCache.map(r => r.trainee_id);

        try {
            const res = await apiFetch("/api/import/commit", {
                method: "POST",
                body: JSON.stringify({
                    trainee_ids_to_commit: tids,
                    staged_rows: stagedRowsCache
                })
            });
            const data = await res.json();
            if (res.ok) {
                resDiv.innerHTML = `
                    <div class="st-alert st-alert-success">
                        <b>Import Completed:</b> ${data.message}
                    </div>
                `;
                showToast("Records committed successfully!", "success");
                loadDirectoryData();
            } else {
                resDiv.innerHTML = `<div class="st-alert st-alert-error">${data.detail || "Import failed."}</div>`;
            }
        } catch (e) {
            resDiv.innerHTML = `<div class="st-alert st-alert-error">${e.message}</div>`;
        } finally {
            btn.disabled = false;
            btn.textContent = "Commit Valid Records & Synchronize Schedules";
        }
    }

    async function executeDatabaseDeleteTrainees() {
        const sel = document.getElementById("db-cleanup-select");
        const selectedIds = Array.from(sel.selectedOptions).map(o => o.value);
        if (selectedIds.length === 0) {
            showToast("Please select at least one trainee to delete.", "warning");
            return;
        }

        const chk = document.getElementById("chk-confirm-db-delete");
        if (!chk || !chk.checked) {
            showToast("Please confirm the deletion by checking the box.", "error");
            return;
        }

        const resDiv = document.getElementById("db-delete-result");
        resDiv.innerHTML = '<div class="st-alert st-alert-info">Deleting selected trainees...</div>';

        try {
            const res = await apiFetch("/api/database/delete-trainees", {
                method: "POST",
                body: JSON.stringify({ trainee_ids: selectedIds })
            });
            const data = await res.json();
            if (res.ok) {
                resDiv.innerHTML = `<div class="st-alert st-alert-success">${data.message}</div>`;
                showToast("Deletion complete.", "success");
                loadDirectoryData();
                loadImportExportData();
            } else {
                resDiv.innerHTML = `<div class="st-alert st-alert-error">${data.detail || "Deletion failed."}</div>`;
            }
        } catch (e) {
            resDiv.innerHTML = `<div class="st-alert st-alert-error">${e.message}</div>`;
        }
    }

    // -------------------------------------------------------------
    // VIEW 6: AUDIT & EXCEPTIONS LOGIC
    // -------------------------------------------------------------
    function switchAuditTab(tabId) {
        document.querySelectorAll("#page-audit-exceptions .st-tab-btn").forEach(btn => btn.classList.remove("active"));
        document.querySelectorAll("#page-audit-exceptions .st-tab-pane").forEach(pane => pane.classList.remove("active"));

        event.target.classList.add("active");
        document.getElementById(tabId).classList.add("active");
    }

    async function loadAuditExceptionsData() {
        loadAuditLogs();
        loadExceptionsList();
    }

    async function loadAuditLogs() {
        const entity = document.getElementById("audit-filter-entity").value;
        const endpoint = entity === "All" ? "/api/audit-logs" : `/api/audit-logs?entity_type=${entity}`;

        try {
            const res = await apiFetch(endpoint);
            if (res.ok) {
                const data = await res.json();
                const tbody = document.getElementById("audit-logs-tbody");
                const logs = data.logs || [];
                if (logs.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; color: #64748B;">No audit records found.</td></tr>';
                } else {
                    tbody.innerHTML = logs.map(l => `
                        <tr>
                            <td>${l.id}</td>
                            <td>${l.timestamp}</td>
                            <td>${escapeHtml(l.actor)}</td>
                            <td><b>${escapeHtml(l.entity_type)}</b> (<code>${escapeHtml(l.entity_id)}</code>)</td>
                            <td><code>${escapeHtml(l.action)}</code></td>
                            <td>${escapeHtml(l.reason || "-")}</td>
                            <td style="max-width: 200px; overflow: hidden; text-overflow: ellipsis;">${escapeHtml(l.old_values || "-")}</td>
                            <td style="max-width: 200px; overflow: hidden; text-overflow: ellipsis;">${escapeHtml(l.new_values || "-")}</td>
                        </tr>
                    `).join("");
                }
            }
        } catch (e) {}
    }

    async function loadExceptionsList() {
        try {
            const res = await apiFetch("/api/exceptions");
            if (res.ok) {
                const data = await res.json();
                const container = document.getElementById("exceptions-cards-container");
                const excList = data.exceptions || [];

                if (excList.length === 0) {
                    container.innerHTML = '<div class="st-alert st-alert-success">No uncertain or failed schedules currently requiring attention.</div>';
                } else {
                    container.innerHTML = excList.map(r => `
                        <div style="background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; padding: 1.15rem; margin-bottom: 1rem;">
                            <div style="font-weight: 600; font-size: 0.95rem; margin-bottom: 0.35rem;">
                                Schedule #${r.id} &bull; Trainee <code>${escapeHtml(r.trainee_id)}</code> (${escapeHtml(r.trainee_name)}) &bull; Stage: ${STAGE_LABELS[r.stage] || r.stage}
                            </div>
                            <div style="font-size: 0.8rem; color: #475569; margin-bottom: 0.5rem;">
                                Status: <span class="badge badge-${r.status.toLowerCase()}">${r.status}</span> &bull; Scheduled Date: ${r.scheduled_date} &bull; Attempts: ${r.attempt_count}
                            </div>
                            <div class="form-caption" style="margin-bottom: 0.75rem;">
                                Error / Details: <b>${escapeHtml(r.last_error || "Unknown exception")}</b>
                            </div>

                            ${r.status === "Uncertain" ? `
                                <div style="background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 6px; padding: 0.85rem; margin-top: 0.5rem;">
                                    <div class="grid-3" style="grid-template-columns: 2fr 1fr 1fr; align-items: flex-end;">
                                        <div class="form-group" style="margin-bottom: 0;">
                                            <label class="form-label" for="res-txt-${r.id}" style="font-size: 0.775rem;">Resolution Justification*</label>
                                            <input type="text" class="st-input" id="res-txt-${r.id}" placeholder="Enter mandatory justification reason">
                                        </div>
                                        <div>
                                            <button type="button" class="st-btn-primary w-full" onclick="executeResolveException(${r.id}, 'confirm_sent')">
                                                Mark as Confirmed Sent
                                            </button>
                                        </div>
                                        <div>
                                            <button type="button" class="st-btn-secondary w-full" onclick="executeResolveException(${r.id}, 'authorize_retry')">
                                                Authorize Retry
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            ` : ''}
                        </div>
                    `).join("");
                }
            }
        } catch (e) {}
    }

    async function executeResolveException(schedId, action) {
        const input = document.getElementById(`res-txt-${schedId}`);
        const reason = input ? input.value.trim() : "";
        if (!reason) {
            showToast("Justification is mandatory.", "error");
            return;
        }

        try {
            const res = await apiFetch("/api/exceptions/resolve", {
                method: "POST",
                body: JSON.stringify({
                    schedule_id: schedId,
                    action: action,
                    reason: reason
                })
            });
            if (res.ok) {
                showToast(`Schedule #${schedId} resolved successfully.`, "success");
                loadExceptionsList();
                loadAuditLogs();
            } else {
                const err = await res.json();
                showToast(err.detail || "Failed to resolve exception.", "error");
            }
        } catch (e) {
            showToast("Error resolving exception.", "error");
        }
    }

    // -------------------------------------------------------------
    // SYSTEM BOOT
    // -------------------------------------------------------------
    window.addEventListener("DOMContentLoaded", () => {
        checkAuthSession();
    });
</script>
</body>
</html>
"""
