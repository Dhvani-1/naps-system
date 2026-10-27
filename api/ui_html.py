"""HTML, CSS, and JavaScript generator for the client web portal UI."""

def get_client_ui_html() -> str:
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NAPS HR Apprentice Lifecycle & Email Scheduling Portal</title>
    <!-- Google Fonts: Inter -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-body: #F8FAFC;
            --bg-card: #FFFFFF;
            --bg-sidebar: #0F172A;
            --sidebar-hover: #1E293B;
            --sidebar-active: #2563EB;
            --text-main: #0F172A;
            --text-muted: #64748B;
            --text-sidebar: #94A3B8;
            --border-color: #E2E8F0;
            --primary: #1E40AF;
            --primary-hover: #1D4ED8;
            --success: #059669;
            --success-bg: #ECFDF5;
            --warning: #D97706;
            --warning-bg: #FFFBEB;
            --danger: #DC2626;
            --danger-bg: #FEF2F2;
            --simulation: #7C3AED;
            --simulation-bg: #F5F3FF;
            --radius-md: 8px;
            --radius-lg: 12px;
            --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
            --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.08), 0 2px 4px -2px rgba(0, 0, 0, 0.05);
            --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.05);
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }

        body {
            background-color: var(--bg-body);
            color: var(--text-main);
            min-height: 100vh;
            display: flex;
            overflow-x: hidden;
        }

        /* SIDEBAR STYLES */
        aside.sidebar {
            width: 280px;
            background-color: var(--bg-sidebar);
            color: #FFFFFF;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            position: fixed;
            left: 0;
            top: 0;
            bottom: 0;
            z-index: 100;
            padding: 24px 16px;
            box-shadow: 2px 0 10px rgba(0, 0, 0, 0.1);
        }

        .brand-logo {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 24px;
            padding: 0 8px;
        }

        .brand-icon {
            width: 38px;
            height: 38px;
            background: linear-gradient(135deg, #3B82F6, #1E40AF);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 800;
            font-size: 20px;
            color: #FFFFFF;
            box-shadow: 0 4px 8px rgba(37, 99, 235, 0.3);
        }

        .brand-text h2 {
            font-size: 16px;
            font-weight: 700;
            letter-spacing: -0.3px;
            color: #FFFFFF;
        }

        .brand-text span {
            font-size: 11px;
            font-weight: 500;
            color: #94A3B8;
            display: block;
        }

        .safety-badge {
            background: rgba(124, 58, 237, 0.15);
            border: 1px solid rgba(139, 92, 246, 0.4);
            border-radius: var(--radius-md);
            padding: 10px 12px;
            margin-bottom: 24px;
        }

        .safety-badge .badge-title {
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 12px;
            font-weight: 700;
            color: #C4B5FD;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .safety-badge p {
            font-size: 11px;
            color: #DDD6FE;
            margin-top: 4px;
            line-height: 1.4;
        }

        nav.nav-links {
            display: flex;
            flex-direction: column;
            gap: 6px;
            flex: 1;
        }

        .nav-item {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 10px 14px;
            border-radius: var(--radius-md);
            color: var(--text-sidebar);
            text-decoration: none;
            font-size: 13.5px;
            font-weight: 500;
            transition: all 0.2s ease;
            cursor: pointer;
        }

        .nav-item:hover {
            background-color: var(--sidebar-hover);
            color: #FFFFFF;
        }

        .nav-item.active {
            background-color: var(--sidebar-active);
            color: #FFFFFF;
            font-weight: 600;
            box-shadow: 0 4px 10px rgba(37, 99, 235, 0.35);
        }

        .nav-item svg {
            width: 18px;
            height: 18px;
            opacity: 0.85;
        }

        .sidebar-footer {
            padding-top: 16px;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
        }

        .user-chip {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 10px 12px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: var(--radius-md);
        }

        .user-info {
            display: flex;
            flex-direction: column;
        }

        .user-name {
            font-size: 12.5px;
            font-weight: 600;
            color: #FFFFFF;
        }

        .user-role {
            font-size: 11px;
            color: #94A3B8;
        }

        .btn-logout {
            background: transparent;
            border: none;
            color: #EF4444;
            cursor: pointer;
            padding: 6px;
            border-radius: 6px;
            transition: background 0.2s;
        }

        .btn-logout:hover {
            background: rgba(239, 68, 68, 0.15);
        }

        /* MAIN CONTENT AREA */
        main.main-content {
            margin-left: 280px;
            flex: 1;
            padding: 32px 40px;
            max-width: 1600px;
        }

        header.top-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 28px;
        }

        .page-title h1 {
            font-size: 24px;
            font-weight: 700;
            color: var(--text-main);
            letter-spacing: -0.5px;
        }

        .page-title p {
            font-size: 13px;
            color: var(--text-muted);
            margin-top: 2px;
        }

        .header-meta {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .chip-meta {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: #FFFFFF;
            border: 1px solid var(--border-color);
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 500;
            color: var(--text-muted);
            box-shadow: var(--shadow-sm);
        }

        .chip-meta.postgres {
            color: #0284C7;
            background: #F0F9FF;
            border-color: #BAE6FD;
        }

        /* CARDS & METRIC GRIDS */
        .grid-stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 16px;
            margin-bottom: 28px;
        }

        .card-stat {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-lg);
            padding: 20px 18px;
            box-shadow: var(--shadow-sm);
            transition: transform 0.2s, box-shadow 0.2s;
        }

        .card-stat:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-md);
        }

        .card-stat .stat-label {
            font-size: 12px;
            font-weight: 600;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .card-stat .stat-value {
            font-size: 28px;
            font-weight: 800;
            color: var(--text-main);
            margin-top: 8px;
            letter-spacing: -0.5px;
        }

        .card-stat.simulated .stat-value {
            color: var(--simulation);
        }

        .card-stat.active .stat-value {
            color: var(--success);
        }

        .card-stat.warning .stat-value {
            color: var(--warning);
        }

        .card-stat.danger .stat-value {
            color: var(--danger);
        }

        /* SECTION CARDS */
        .card-panel {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-lg);
            padding: 24px;
            box-shadow: var(--shadow-sm);
            margin-bottom: 28px;
        }

        .card-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 20px;
            padding-bottom: 14px;
            border-bottom: 1px solid var(--border-color);
        }

        .card-header h3 {
            font-size: 16px;
            font-weight: 700;
            color: var(--text-main);
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .card-header p {
            font-size: 12.5px;
            color: var(--text-muted);
            margin-top: 2px;
        }

        /* BUTTONS */
        .btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            padding: 8px 16px;
            font-size: 13.5px;
            font-weight: 600;
            border-radius: var(--radius-md);
            cursor: pointer;
            border: 1px solid transparent;
            transition: all 0.2s;
            text-decoration: none;
        }

        .btn-primary {
            background-color: var(--primary);
            color: #FFFFFF;
        }

        .btn-primary:hover {
            background-color: var(--primary-hover);
            box-shadow: 0 4px 10px rgba(30, 64, 175, 0.25);
        }

        .btn-secondary {
            background-color: #FFFFFF;
            border-color: var(--border-color);
            color: var(--text-main);
        }

        .btn-secondary:hover {
            background-color: #F8FAFC;
            border-color: #CBD5E1;
        }

        .btn-simulation {
            background-color: var(--simulation);
            color: #FFFFFF;
        }

        .btn-simulation:hover {
            background-color: #6D28D9;
            box-shadow: 0 4px 10px rgba(124, 58, 237, 0.3);
        }

        .btn-danger {
            background-color: var(--danger);
            color: #FFFFFF;
        }

        .btn-danger:hover {
            background-color: #B91C1C;
        }

        .btn-sm {
            padding: 5px 10px;
            font-size: 12px;
        }

        /* TABLES */
        .table-responsive {
            width: 100%;
            overflow-x: auto;
            border: 1px solid var(--border-color);
            border-radius: var(--radius-md);
        }

        table.data-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
            text-align: left;
            background: #FFFFFF;
        }

        table.data-table th {
            background-color: #F8FAFC;
            color: #475569;
            font-weight: 600;
            padding: 12px 14px;
            border-bottom: 1px solid var(--border-color);
            white-space: nowrap;
        }

        table.data-table td {
            padding: 12px 14px;
            border-bottom: 1px solid #F1F5F9;
            color: var(--text-main);
        }

        table.data-table tbody tr:hover {
            background-color: #F8FAFC;
        }

        /* BADGES */
        .badge {
            display: inline-flex;
            align-items: center;
            gap: 4px;
            padding: 3px 8px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 600;
            white-space: nowrap;
        }

        .badge-scheduled {
            background-color: #EFF6FF;
            color: #1D4ED8;
            border: 1px solid #BFDBFE;
        }

        .badge-simulated {
            background-color: var(--simulation-bg);
            color: var(--simulation);
            border: 1px solid #DDD6FE;
        }

        .badge-custom {
            background-color: #FFFBEB;
            color: #B45309;
            border: 1px solid #FDE68A;
        }

        .badge-optout {
            background-color: #F1F5F9;
            color: #64748B;
            border: 1px solid #E2E8F0;
        }

        .badge-cancelled {
            background-color: #FEF2F2;
            color: #B91C1C;
            border: 1px solid #FECACA;
        }

        .badge-active {
            background-color: var(--success-bg);
            color: var(--success);
            border: 1px solid #A7F3D0;
        }

        .badge-left {
            background-color: #FFF1F2;
            color: #E11D48;
            border: 1px solid #FECDD3;
        }

        /* VIEW TOGGLE BUTTONS */
        .view-toggle-group {
            display: inline-flex;
            background: #F1F5F9;
            padding: 3px;
            border-radius: var(--radius-md);
            gap: 2px;
            border: 1px solid var(--border-color);
        }

        .view-toggle-btn {
            border: none;
            background: transparent;
            padding: 6px 12px;
            font-size: 12px;
            font-weight: 600;
            color: var(--text-muted);
            border-radius: 6px;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            transition: all 0.2s ease;
        }

        .view-toggle-btn.active {
            background: #FFFFFF;
            color: var(--primary);
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }

        /* MILESTONE STEPPER PILLS */
        .milestone-stepper {
            display: inline-flex;
            align-items: center;
            gap: 3px;
            background: #F8FAFC;
            padding: 3px 5px;
            border-radius: 8px;
            border: 1px solid var(--border-color);
        }

        .stepper-node {
            display: inline-flex;
            align-items: center;
            gap: 3px;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 10.5px;
            font-weight: 600;
            cursor: pointer;
            text-decoration: none;
            transition: transform 0.15s;
        }

        .stepper-node:hover {
            transform: scale(1.05);
        }

        .stepper-node.stg-sent {
            background: var(--simulation-bg);
            color: var(--simulation);
            border: 1px solid #DDD6FE;
        }

        .stepper-node.stg-scheduled {
            background: #EFF6FF;
            color: #1D4ED8;
            border: 1px solid #BFDBFE;
        }

        .stepper-node.stg-custom {
            background: #FFFBEB;
            color: #B45309;
            border: 1px solid #FDE68A;
        }

        .stepper-node.stg-optout {
            background: #F1F5F9;
            color: #94A3B8;
            border: 1px solid #E2E8F0;
        }

        .stepper-node.stg-cancelled {
            background: #FEF2F2;
            color: #DC2626;
            border: 1px solid #FECACA;
        }

        /* DOSSIER MODAL STYLING */
        .dossier-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 12px;
            margin-bottom: 20px;
        }

        .dossier-card {
            background: #F8FAFC;
            border: 1px solid var(--border-color);
            border-radius: var(--radius-md);
            padding: 12px 14px;
        }

        .dossier-card .d-label {
            font-size: 11px;
            font-weight: 600;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 3px;
        }

        .dossier-card .d-val {
            font-size: 13.5px;
            font-weight: 600;
            color: var(--text-main);
            word-break: break-word;
        }

        /* FORM INPUTS */
        .form-group {
            margin-bottom: 16px;
        }

        .form-label {
            display: block;
            font-size: 12.5px;
            font-weight: 600;
            color: var(--text-main);
            margin-bottom: 6px;
        }

        .form-control {
            width: 100%;
            padding: 9px 12px;
            font-size: 13.5px;
            border: 1px solid var(--border-color);
            border-radius: var(--radius-md);
            background: #FFFFFF;
            color: var(--text-main);
            transition: border-color 0.2s;
        }

        .form-control:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(30, 64, 175, 0.1);
        }

        .form-row {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 16px;
        }

        /* MODALS */
        .modal-overlay {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(15, 23, 42, 0.6);
            backdrop-filter: blur(4px);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 1000;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.2s ease;
        }

        .modal-overlay.open {
            opacity: 1;
            pointer-events: auto;
        }

        .modal-card {
            background: #FFFFFF;
            border-radius: var(--radius-lg);
            width: 90%;
            max-width: 650px;
            max-height: 90vh;
            overflow-y: auto;
            box-shadow: var(--shadow-lg);
            padding: 28px;
            position: relative;
        }

        .modal-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 20px;
            padding-bottom: 12px;
            border-bottom: 1px solid var(--border-color);
        }

        .modal-header h3 {
            font-size: 18px;
            font-weight: 700;
        }

        .btn-close-modal {
            background: transparent;
            border: none;
            font-size: 20px;
            cursor: pointer;
            color: var(--text-muted);
        }

        /* LOGIN GATE */
        #loginGate {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 9999;
            padding: 20px;
        }

        .login-box {
            background: #FFFFFF;
            width: 100%;
            max-width: 440px;
            border-radius: var(--radius-lg);
            padding: 36px 32px;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.4);
        }

        .login-header {
            text-align: center;
            margin-bottom: 24px;
        }

        .login-header .logo-badge {
            width: 48px;
            height: 48px;
            background: linear-gradient(135deg, #2563EB, #1E40AF);
            color: #FFFFFF;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            font-weight: 800;
            margin: 0 auto 14px;
        }

        .login-header h2 {
            font-size: 20px;
            font-weight: 700;
            color: var(--text-main);
        }

        .login-header p {
            font-size: 13px;
            color: var(--text-muted);
            margin-top: 4px;
        }

        /* TOAST NOTIFICATIONS */
        .toast-container {
            position: fixed;
            bottom: 24px;
            right: 24px;
            z-index: 9999;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }

        .toast {
            background: #FFFFFF;
            border-left: 4px solid var(--primary);
            box-shadow: var(--shadow-lg);
            border-radius: 6px;
            padding: 12px 18px;
            font-size: 13px;
            color: var(--text-main);
            min-width: 300px;
            max-width: 450px;
            animation: slideIn 0.3s ease;
        }

        .toast.success { border-color: var(--success); }
        .toast.danger { border-color: var(--danger); }
        .toast.warning { border-color: var(--warning); }

        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }

        /* DROPZONE */
        .dropzone {
            border: 2px dashed #CBD5E1;
            border-radius: var(--radius-lg);
            padding: 36px 20px;
            text-align: center;
            background: #F8FAFC;
            cursor: pointer;
            transition: all 0.2s;
        }

        .dropzone:hover {
            border-color: var(--primary);
            background: #EFF6FF;
        }

        .dropzone svg {
            width: 44px;
            height: 44px;
            color: #94A3B8;
            margin-bottom: 12px;
        }

        /* VIEWS DISPLAY LOGIC */
        .app-view {
            display: none;
        }

        .app-view.active-view {
            display: block;
        }
    </style>
</head>
<body>

    <!-- ======================================================================= -->
    <!-- 1. LOGIN GATE MODAL                                                     -->
    <!-- ======================================================================= -->
    <div id="loginGate">
        <div class="login-box">
            <div class="login-header">
                <div class="logo-badge">N</div>
                <h2>Administrator Sign In</h2>
                <p>NAPS Apprentice Lifecycle & Email Scheduling Portal</p>
            </div>

            <div id="loginError" style="display:none; background:#FEE2E2; color:#991B1B; padding:10px 12px; border-radius:6px; font-size:12.5px; margin-bottom:16px;"></div>

            <form id="formLogin" onsubmit="handleLoginSubmit(event)">
                <div class="form-group">
                    <label class="form-label">Username or Admin Email</label>
                    <input type="text" id="loginUsername" class="form-control" placeholder="admin or admin@company.com" required autofocus>
                </div>
                <div class="form-group">
                    <label class="form-label">Password</label>
                    <input type="password" id="loginPassword" class="form-control" placeholder="••••••••••••" required>
                </div>
                <button type="submit" id="btnLoginSubmit" class="btn btn-primary" style="width: 100%; padding: 10px; margin-top: 8px;">
                    Sign In to Portal
                </button>
            </form>
            <div style="margin-top: 20px; text-align: center; font-size: 11.5px; color: #94A3B8;">
                Secured single-administrator session. System timezone: Asia/Kolkata.
            </div>
        </div>
    </div>

    <!-- ======================================================================= -->
    <!-- 2. APPLICATION SIDEBAR                                                  -->
    <!-- ======================================================================= -->
    <aside class="sidebar">
        <div class="brand-logo">
            <div class="brand-icon">N</div>
            <div class="brand-text">
                <h2>NAPS Portal</h2>
                <span>Apprentice Lifecycle & Emails</span>
            </div>
        </div>

        <div class="safety-badge">
            <div class="badge-title">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
                Simulation Mode
            </div>
            <p>Live SMTP is disabled for safety. All email dispatches are simulated and logged in the database.</p>
        </div>

        <nav class="nav-links">
            <a class="nav-item active" onclick="switchView('dashboard')">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="9"/><rect x="14" y="3" width="7" height="5"/><rect x="14" y="12" width="7" height="9"/><rect x="3" y="16" width="7" height="5"/></svg>
                Dashboard
            </a>
            <a class="nav-item" onclick="switchView('directory')">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
                Trainee Directory
            </a>
            <a class="nav-item" onclick="switchView('add-trainee')">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="16"/><line x1="8" y1="12" x2="16" y2="12"/></svg>
                Add New Trainee
            </a>
            <a class="nav-item" onclick="switchView('import')">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                Excel / CSV Import
            </a>
            <a class="nav-item" onclick="switchView('exceptions')">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
                Exceptions & Uncertain
            </a>
            <a class="nav-item" onclick="switchView('audit')">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
                Audit Trail
            </a>
            <a class="nav-item" onclick="switchView('settings')">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
                Settings & Safety
            </a>
        </nav>

        <div class="sidebar-footer">
            <div class="user-chip">
                <div class="user-info">
                    <span class="user-name" id="sidebarUsername">Administrator</span>
                    <span class="user-role">Single-User Access</span>
                </div>
                <button class="btn-logout" title="Sign Out" onclick="handleLogout()">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
                </button>
            </div>
        </div>
    </aside>

    <!-- ======================================================================= -->
    <!-- 3. MAIN APPLICATION CONTENT                                             -->
    <!-- ======================================================================= -->
    <main class="main-content">
        <!-- TOP HEADER -->
        <header class="top-header">
            <div class="page-title">
                <h1 id="viewHeaderTitle">Operational Dashboard</h1>
                <p id="viewHeaderSubtitle">Apprentice lifecycle health, milestone timelines, and simulation statistics.</p>
            </div>
            <div class="header-meta">
                <span class="chip-meta" id="chipDatabase">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg>
                    Database: Detecting...
                </span>
                <span class="chip-meta">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                    Asia/Kolkata (IST)
                </span>
            </div>
        </header>

        <!-- VIEW 1: DASHBOARD -->
        <div id="view-dashboard" class="app-view active-view">
            <!-- STATS ROW -->
            <div class="grid-stats">
                <div class="card-stat">
                    <div class="stat-label">Registered Trainees</div>
                    <div class="stat-value" id="statTotalTrainees">-</div>
                </div>
                <div class="card-stat active">
                    <div class="stat-label">Active In-Training</div>
                    <div class="stat-value" id="statActive">-</div>
                </div>
                <div class="card-stat">
                    <div class="stat-label">Completed / On-Roll</div>
                    <div class="stat-value" id="statCompleted">-</div>
                </div>
                <div class="card-stat warning">
                    <div class="stat-label">Early Exits (Left)</div>
                    <div class="stat-value" id="statLeft">-</div>
                </div>
                <div class="card-stat simulated">
                    <div class="stat-label">Simulated Emails Sent</div>
                    <div class="stat-value" id="statSent">-</div>
                </div>
                <div class="card-stat">
                    <div class="stat-label">Pending In Queue</div>
                    <div class="stat-value" id="statPending">-</div>
                </div>
                <div class="card-stat danger">
                    <div class="stat-label">Exceptions Requiring Action</div>
                    <div class="stat-value" id="statExceptions">-</div>
                </div>
            </div>

            <!-- EPHEMERAL SQLITE BANNER (Active only when on SQLite in Vercel/Cloud) -->
            <div id="bannerEphemeralDb" style="display:none; background:#FFFBEB; border:1px solid #FCD34D; border-radius:10px; padding:14px 18px; margin-bottom:20px; font-size:13px; color:#92400E; align-items:center; justify-content:space-between; gap:16px;">
                <div style="display:flex; align-items:flex-start; gap:10px;">
                    <span style="font-size:18px;">ℹ️</span>
                    <div>
                        <strong>Notice on Apprentice Persistence:</strong> The portal is currently running on temporary SQLite storage. On Vercel Serverless, temporary containers periodically reset when idle, which causes existing trainees to start as fresh.
                        <div style="margin-top:3px; color:#B45309; font-size:12px;">To retain trainees permanently across all browser reloads, configure a free cloud PostgreSQL connection string (from <strong>Neon.tech</strong> or <strong>Supabase</strong>) as <code>POSTGRES_URL</code> in your Vercel Environment Variables.</div>
                    </div>
                </div>
                <button type="button" class="btn btn-secondary btn-sm" onclick="switchView('settings')" style="white-space:nowrap; background:#fff;">Storage Guide</button>
            </div>

            <!-- DISPATCH WORKER TRIGGER PANEL -->
            <div class="card-panel">
                <div class="card-header">
                    <div>
                        <h3>
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
                            Execute Background Worker Dispatch Cycle (Simulation Mode)
                        </h3>
                        <p>Processes all milestone schedules whose scheduled_date &le; Target Evaluation Date. No real emails will be sent.</p>
                    </div>
                </div>
                <div style="display:flex; align-items:center; gap:16px;">
                    <div style="width: 240px;">
                        <label class="form-label">Target Evaluation Date</label>
                        <input type="date" id="workerTargetDate" class="form-control">
                    </div>
                    <div style="padding-top: 22px;">
                        <button class="btn btn-simulation" onclick="executeWorkerCycle()">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"/></svg>
                            Run Dispatch Cycle Now (Simulated)
                        </button>
                    </div>
                </div>
            </div>

            <!-- UPCOMING DISPATCH QUEUE -->
            <div class="card-panel">
                <div class="card-header">
                    <div>
                        <h3>
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>
                            Upcoming & Due Email Milestone Queue
                        </h3>
                        <p>Schedules eligible for processing by the background worker.</p>
                    </div>
                </div>
                <div class="table-responsive">
                    <table class="data-table" id="tableQueue">
                        <thead>
                            <tr>
                                <th>Queue ID</th>
                                <th>Trainee ID</th>
                                <th>Apprentice Name</th>
                                <th>Milestone Stage</th>
                                <th>Authoritative Scheduled Date</th>
                                <th>Dispatch Eligibility</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr><td colspan="7" style="text-align:center; padding:20px; color:#94A3B8;">Loading dispatch queue...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- VIEW 2: TRAINEE DIRECTORY -->
        <div id="view-directory" class="app-view">
            <div class="card-panel">
                <div style="display:flex; align-items:center; justify-content:space-between; gap:16px; margin-bottom:20px; flex-wrap:wrap;">
                    <div style="display:flex; align-items:center; gap:10px; flex:1; min-width:320px; flex-wrap:wrap;">
                        <input type="text" id="dirSearch" class="form-control" style="flex:1; min-width:220px;" placeholder="Search ID, Name, Department, Location, Manager, Email..." oninput="loadTrainees()">
                        <select id="dirStatusFilter" class="form-control" style="width:140px;" onchange="loadTrainees()">
                            <option value="All">All Statuses</option>
                            <option value="Active">Active</option>
                            <option value="Left">Left</option>
                            <option value="Completed">Completed</option>
                            <option value="On Roll">On Roll</option>
                        </select>
                        <div class="view-toggle-group">
                            <button type="button" class="view-toggle-btn active" id="btnToggleRoster" onclick="setDirectoryViewMode('roster')">
                                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></svg>
                                Roster View
                            </button>
                            <button type="button" class="view-toggle-btn" id="btnToggleMatrix" onclick="setDirectoryViewMode('matrix')">
                                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
                                Milestone Matrix
                            </button>
                        </div>
                    </div>
                    <div style="display:flex; align-items:center; gap:10px;">
                        <span id="dirCountBadge" style="font-size:12px; color:var(--text-muted); font-weight:600;">0 trainees</span>
                        <button class="btn btn-secondary btn-sm" onclick="exportData('csv')">Export CSV</button>
                        <button class="btn btn-secondary btn-sm" onclick="exportData('xlsx')">Export Excel (.xlsx)</button>
                    </div>
                </div>

                <div class="table-responsive">
                    <table class="data-table" id="tableTrainees">
                        <thead id="headTrainees"></thead>
                        <tbody>
                            <tr><td colspan="12" style="text-align:center; padding:20px;">Loading directory...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- VIEW 3: ADD NEW TRAINEE -->
        <div id="view-add-trainee" class="app-view">
            <div class="card-panel">
                <div class="card-header">
                    <div>
                        <h3>Register New Apprentice</h3>
                        <p>Automatically calculates 12-month Last Working Date (LWD) and derives all 6 milestone dates with weekend-to-Monday shifting.</p>
                    </div>
                </div>

                <form id="formAddTrainee" onsubmit="handleAddTraineeSubmit(event)">
                    <div class="form-row">
                        <div class="form-group">
                            <label class="form-label">Trainee ID *</label>
                            <input type="text" id="addId" class="form-control" placeholder="TR-1001" required>
                        </div>
                        <div class="form-group">
                            <label class="form-label">Full Name *</label>
                            <input type="text" id="addName" class="form-control" placeholder="Aarav Sharma" required>
                        </div>
                        <div class="form-group">
                            <label class="form-label">Trainee Email *</label>
                            <input type="email" id="addEmail" class="form-control" placeholder="trainee@company.com" required>
                        </div>
                    </div>

                    <div class="form-row">
                        <div class="form-group">
                            <label class="form-label">Date of Joining (DOJ) *</label>
                            <input type="date" id="addDoj" class="form-control" required onchange="calculateLiveMilestones()">
                        </div>
                        <div class="form-group">
                            <label class="form-label">Reporting Manager Name *</label>
                            <input type="text" id="addMgrName" class="form-control" placeholder="Vikram Malhotra" required>
                        </div>
                        <div class="form-group">
                            <label class="form-label">Manager Email *</label>
                            <input type="email" id="addMgrEmail" class="form-control" placeholder="manager@company.com" required>
                        </div>
                    </div>

                    <div class="form-row">
                        <div class="form-group">
                            <label class="form-label">Department *</label>
                            <input type="text" id="addDept" class="form-control" placeholder="Operations" required>
                        </div>
                        <div class="form-group">
                            <label class="form-label">Location / Facility *</label>
                            <input type="text" id="addLocation" class="form-control" placeholder="Mumbai" required>
                        </div>
                        <div class="form-group">
                            <label class="form-label">Calculated Last Working Date (Auto LWD = DOJ + 12m)</label>
                            <input type="text" id="addLwdPreview" class="form-control" readonly style="background:#F1F5F9; font-weight:600;">
                        </div>
                    </div>

                    <!-- MILESTONE PREVIEW TABLE -->
                    <div style="margin: 24px 0 16px;">
                        <h4 style="font-size:14px; font-weight:700; margin-bottom:8px;">Milestone Schedule Preferences & Custom Dates</h4>
                        <div class="table-responsive">
                            <table class="data-table">
                                <thead>
                                    <tr>
                                        <th>Milestone Stage</th>
                                        <th>Recipient</th>
                                        <th>Calculated Due Date</th>
                                        <th>Opt-Out Stage?</th>
                                        <th>Custom Override Date (Optional)</th>
                                    </tr>
                                </thead>
                                <tbody id="liveMilestoneRows">
                                    <tr><td colspan="5" style="text-align:center; padding:12px; color:#94A3B8;">Select Date of Joining above to calculate milestone schedules.</td></tr>
                                </tbody>
                            </table>
                        </div>
                    </div>

                    <div style="display:flex; justify-content:flex-end; gap:12px; margin-top:24px;">
                        <button type="submit" class="btn btn-primary">
                            Register Apprentice & Create Schedules
                        </button>
                    </div>
                </form>
            </div>
        </div>

        <!-- VIEW 4: EXCEL / CSV IMPORT -->
        <div id="view-import" class="app-view">
            <div class="card-panel">
                <div class="card-header">
                    <div>
                        <h3>Batch Excel / CSV Import Engine</h3>
                        <p>Idempotent batch upload with field-level error isolation, row removal from staging, and blank-cell preservation.</p>
                    </div>
                    <div style="display:flex; gap:10px;">
                        <button class="btn btn-secondary btn-sm" onclick="downloadTemplateFile('xlsx')">Download Excel Template (.xlsx)</button>
                        <button class="btn btn-secondary btn-sm" onclick="downloadTemplateFile('csv')">Download CSV Template (.csv)</button>
                    </div>
                </div>

                <!-- DRAG AND DROP ZONE -->
                <div class="dropzone" id="uploadDropzone" onclick="document.getElementById('importFileInput').click()">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
                    <h4 style="font-size:15px; font-weight:600; margin-bottom:4px;">Drag and drop Excel or CSV file here</h4>
                    <p style="font-size:12.5px; color:#94A3B8;">Supports .xlsx, .xls, and .csv files formatted with the 23 standard columns.</p>
                    <input type="file" id="importFileInput" style="display:none;" accept=".xlsx,.xls,.csv" onchange="handleFileSelected(event)">
                </div>

                <!-- STAGED ROWS CONTAINER -->
                <div id="stagedContainer" style="display:none; margin-top:28px;">
                    <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:14px; flex-wrap:wrap; gap:12px;">
                        <div>
                            <h4 style="font-size:15px; font-weight:700; color:var(--success); margin-bottom:2px;">
                                Staged Import Records (<span id="stagedCount">0</span> ready to commit)
                            </h4>
                            <p style="font-size:12px; color:var(--text-muted);">
                                Click <strong>✏️ Edit Dates</strong> to customize DOJ or milestone dates for any employee, or select checkboxes to save specific employees.
                            </p>
                        </div>
                        <div style="display:flex; gap:8px; align-items:center; flex-wrap:wrap;">
                            <button type="button" class="btn btn-danger btn-sm" onclick="deleteSelectedStagedRows()">🗑️ Remove Selected</button>
                            <button type="button" class="btn btn-primary btn-sm" id="btnCommitSelected" onclick="commitStagedRows(true)">
                                💾 Save Selected (<span id="selectedStagedBadge">0</span>)
                            </button>
                            <button type="button" class="btn btn-secondary btn-sm" id="btnCommitAll" onclick="commitStagedRows(false)">
                                💾 Save All (<span id="totalStagedBadge">0</span>)
                            </button>
                        </div>
                    </div>

                    <div class="table-responsive">
                        <table class="data-table" id="tableStaged">
                            <thead>
                                <tr>
                                    <th style="width:40px;"><input type="checkbox" id="checkAllStaged" onchange="toggleSelectAllStaged(this)"></th>
                                    <th>Trainee ID</th>
                                    <th>Name</th>
                                    <th>DOJ</th>
                                    <th>LWD</th>
                                    <th>Status</th>
                                    <th>Type</th>
                                    <th>Initial</th>
                                    <th>Q1</th>
                                    <th>Q2</th>
                                    <th>Q3</th>
                                    <th>Q4</th>
                                    <th>Exit</th>
                                    <th style="text-align:center;">Actions</th>
                                </tr>
                            </thead>
                            <tbody></tbody>
                        </table>
                    </div>

                    <!-- ERROR ROWS CONTAINER -->
                    <div id="importErrorsContainer" style="display:none; margin-top:28px;">
                        <h4 style="font-size:14px; font-weight:700; color:var(--danger); margin-bottom:8px;">
                            Rejected Rows (<span id="errorCount">0</span> rows with errors)
                        </h4>
                        <div class="table-responsive">
                            <table class="data-table" id="tableImportErrors">
                                <thead>
                                    <tr>
                                        <th>Row #</th>
                                        <th>Trainee ID</th>
                                        <th>Name</th>
                                        <th>Validation Errors</th>
                                    </tr>
                                </thead>
                                <tbody></tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- VIEW 5: EXCEPTIONS & UNCERTAIN -->
        <div id="view-exceptions" class="app-view">
            <div class="card-panel">
                <div class="card-header">
                    <div>
                        <h3>Delivery Exceptions & Uncertain Dispatches</h3>
                        <p>Inspect interrupted dispatches or delivery failures and administratively resolve them.</p>
                    </div>
                </div>

                <div class="table-responsive">
                    <table class="data-table" id="tableExceptions">
                        <thead>
                            <tr>
                                <th>Schedule ID</th>
                                <th>Trainee ID</th>
                                <th>Apprentice Name</th>
                                <th>Stage</th>
                                <th>Scheduled Date</th>
                                <th>Status</th>
                                <th>Attempts</th>
                                <th>Last Error Message</th>
                                <th>Action</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr><td colspan="9" style="text-align:center; padding:20px;">No exceptions requiring action.</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- VIEW 6: AUDIT TRAIL -->
        <div id="view-audit" class="app-view">
            <div class="card-panel">
                <div class="card-header">
                    <div>
                        <h3>Immutable System Audit Log</h3>
                        <p>Complete append-only audit trail of trainee creation, lifecycle changes, date overrides, and worker dispatches.</p>
                    </div>
                </div>
                <div class="table-responsive">
                    <table class="data-table" id="tableAudit">
                        <thead>
                            <tr>
                                <th>Log ID</th>
                                <th>Timestamp (IST)</th>
                                <th>Actor</th>
                                <th>Action</th>
                                <th>Entity</th>
                                <th>Entity ID</th>
                                <th>Reason / Justification</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr><td colspan="7" style="text-align:center; padding:20px;">Loading audit trail...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- VIEW 7: SETTINGS & DIAGNOSTICS -->
        <div id="view-settings" class="app-view">
            <div class="card-panel">
                <div class="card-header">
                    <div>
                        <h3>System Configuration & Platform Diagnostics</h3>
                        <p>Deployment specifications, active database connection, and simulation safeguards.</p>
                    </div>
                </div>

                <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(280px, 1fr)); gap:20px;">
                    <div style="background:#F8FAFC; padding:18px; border-radius:var(--radius-md); border:1px solid var(--border-color);">
                        <h4 style="font-size:13px; font-weight:700; color:#475569; margin-bottom:8px;">ACTIVE DELIVERY MODE</h4>
                        <span class="badge badge-simulated" style="font-size:13px; padding:6px 12px;">SIMULATION MODE (LOCKED)</span>
                        <p style="font-size:12px; color:#64748B; margin-top:8px;">All email schedules are processed safely without connecting to external SMTP servers.</p>
                    </div>

                    <div style="background:#F8FAFC; padding:18px; border-radius:var(--radius-md); border:1px solid var(--border-color);">
                        <h4 style="font-size:13px; font-weight:700; color:#475569; margin-bottom:8px;">DATABASE CONNECTION</h4>
                        <span class="badge badge-scheduled" id="settingsDbBadge" style="font-size:13px; padding:6px 12px;">Detecting...</span>
                        <p style="font-size:12px; color:#64748B; margin-top:8px;" id="settingsDbDesc">Persistent database configured for serverless production.</p>
                    </div>

                    <div style="background:#F8FAFC; padding:18px; border-radius:var(--radius-md); border:1px solid var(--border-color);">
                        <h4 style="font-size:13px; font-weight:700; color:#475569; margin-bottom:8px;">VERCEL CRON SCHEDULE</h4>
                        <span class="badge" style="background:#EFF6FF; color:#1D4ED8; font-size:13px; padding:6px 12px;">Daily at 09:00:00 AM IST</span>
                        <p style="font-size:12px; color:#64748B; margin-top:8px;">Configured in vercel.json triggering /api/cron/dispatch safely with CRON_SECRET.</p>
                    </div>
                </div>

                <div style="margin-top:28px; padding-top:20px; border-top:1px solid var(--border-color);">
                    <h4 style="font-size:14px; font-weight:700; color:var(--danger); margin-bottom:6px;">Prune Test & Unsent Trainee Data</h4>
                    <p style="font-size:12px; color:#64748B; margin-bottom:12px;">Safely deletes trainees without Sent email history. Any trainee with immutable Sent history is permanently preserved.</p>
                    <button class="btn btn-danger btn-sm" onclick="pruneTestData()">Prune Unsent Trainees</button>
                </div>
            </div>
        </div>
    </main>

    <!-- ======================================================================= -->
    <!-- 4. EDIT TRAINEE MODAL                                                   -->
    <!-- ======================================================================= -->
    <div id="modalEditTrainee" class="modal-overlay">
        <div class="modal-card">
            <div class="modal-header">
                <h3>Edit Apprentice & Milestone Preferences</h3>
                <button class="btn-close-modal" onclick="closeModal('modalEditTrainee')">&times;</button>
            </div>
            <form id="formEditTrainee" onsubmit="handleEditTraineeSubmit(event)">
                <input type="hidden" id="editTraineeId">
                <div class="form-row">
                    <div class="form-group">
                        <label class="form-label">Full Name</label>
                        <input type="text" id="editName" class="form-control" required>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Trainee Email</label>
                        <input type="email" id="editEmail" class="form-control" required>
                    </div>
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label class="form-label">Manager Name</label>
                        <input type="text" id="editMgrName" class="form-control" required>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Manager Email</label>
                        <input type="email" id="editMgrEmail" class="form-control" required>
                    </div>
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label class="form-label">Lifecycle Status</label>
                        <select id="editStatus" class="form-control" onchange="handleStatusChangeInModal(this.value)">
                            <option value="Active">Active</option>
                            <option value="Left">Left</option>
                            <option value="Completed">Completed</option>
                            <option value="On Roll">On Roll</option>
                        </select>
                    </div>
                    <div class="form-group" id="groupActualLwd" style="display:none;">
                        <label class="form-label" style="color:var(--danger);">Confirmed Actual Last Working Date (Required for 'Left') *</label>
                        <input type="date" id="editActualLwd" class="form-control">
                    </div>
                </div>

                <div style="margin:20px 0 12px;">
                    <h4 style="font-size:13.5px; font-weight:700;">Milestone Stages & Custom Scheduled Dates</h4>
                    <div class="table-responsive" style="margin-top:8px;">
                        <table class="data-table" id="tableModalSchedules">
                            <thead>
                                <tr>
                                    <th>Stage</th>
                                    <th>Status</th>
                                    <th>Scheduled Date (DD/MM/YYYY)</th>
                                    <th>Opt Out?</th>
                                </tr>
                            </thead>
                            <tbody></tbody>
                        </table>
                    </div>
                </div>

                <div style="display:flex; justify-content:space-between; align-items:center; margin-top:24px;">
                    <div style="display:flex; gap:8px;">
                        <button type="button" class="btn btn-secondary btn-sm" onclick="archiveCurrentTrainee()">Archive Trainee</button>
                        <button type="button" class="btn btn-danger btn-sm" onclick="deleteCurrentTrainee()">Delete</button>
                    </div>
                    <button type="submit" class="btn btn-primary">Save Changes</button>
                </div>
            </form>
        </div>
    </div>

    <!-- ======================================================================= -->
    <!-- 5. RESOLVE EXCEPTION MODAL                                              -->
    <!-- ======================================================================= -->
    <div id="modalResolveException" class="modal-overlay">
        <div class="modal-card" style="max-width:500px;">
            <div class="modal-header">
                <h3>Resolve Delivery Exception</h3>
                <button class="btn-close-modal" onclick="closeModal('modalResolveException')">&times;</button>
            </div>
            <form onsubmit="handleResolveExceptionSubmit(event)">
                <input type="hidden" id="resolveScheduleId">
                <div class="form-group">
                    <label class="form-label">Resolution Action</label>
                    <select id="resolveAction" class="form-control">
                        <option value="MARK_SENT">Mark as Sent (Confirm delivered via offline check)</option>
                        <option value="RETRY">Re-queue for Next Dispatch Run</option>
                    </select>
                </div>
                <div class="form-group">
                    <label class="form-label">Mandatory Administrative Justification *</label>
                    <textarea id="resolveReason" class="form-control" rows="3" placeholder="Provide audit explanation..." required></textarea>
                </div>
                <div style="display:flex; justify-content:flex-end; gap:10px; margin-top:16px;">
                    <button type="button" class="btn btn-secondary" onclick="closeModal('modalResolveException')">Cancel</button>
                    <button type="submit" class="btn btn-primary">Confirm Resolution</button>
                </div>
            </form>
        </div>
    </div>

    <!-- ======================================================================= -->
    <!-- 6. EDIT STAGED APPRENTICE & DATES MODAL                                 -->
    <!-- ======================================================================= -->
    <div id="modalEditStaged" class="modal-overlay">
        <div class="modal-card" style="max-width:720px;">
            <div class="modal-header">
                <div>
                    <h3 id="stagedModalTitle">Edit Staged Apprentice Dates</h3>
                    <p style="font-size:12px; color:var(--text-muted); margin-top:2px;">Adjust Date of Joining, Last Working Date, or individual stage dates before saving.</p>
                </div>
                <button class="btn-close-modal" onclick="closeModal('modalEditStaged')">&times;</button>
            </div>
            <form onsubmit="handleSaveStagedModal(event)">
                <div class="form-row" style="margin-bottom:14px;">
                    <div class="form-group">
                        <label class="form-label">Trainee ID</label>
                        <input type="text" id="stagedModalTraineeId" class="form-control" readonly style="background:#F1F5F9; font-weight:600;">
                    </div>
                    <div class="form-group">
                        <label class="form-label">Full Name</label>
                        <input type="text" id="stagedModalTraineeName" class="form-control" readonly style="background:#F1F5F9; font-weight:600;">
                    </div>
                </div>

                <div class="form-row" style="margin-bottom:8px;">
                    <div class="form-group">
                        <label class="form-label">Date of Joining (DOJ) *</label>
                        <input type="date" id="stagedModalDoj" class="form-control" required>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Last Working Date (LWD)</label>
                        <input type="date" id="stagedModalLwd" class="form-control">
                    </div>
                </div>

                <div style="display:flex; justify-content:flex-end; margin-bottom:14px;">
                    <button type="button" class="btn btn-secondary btn-sm" onclick="recalcStagedDatesFromDoj()">
                        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>
                        Recalculate All 6 Stages from DOJ
                    </button>
                </div>

                <div style="margin:16px 0 12px;">
                    <h4 style="font-size:13.5px; font-weight:700; margin-bottom:8px;">Milestone Stage Dates & Opt-Out Preferences</h4>
                    <div class="table-responsive">
                        <table class="data-table" id="tableStagedModalStages">
                            <thead>
                                <tr>
                                    <th>Stage</th>
                                    <th>Calculation Rule</th>
                                    <th>Scheduled Date</th>
                                    <th style="text-align:center;">Opt Out?</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td><strong>Initial Welcome</strong></td>
                                    <td>DOJ + 15 days (weekend to Mon)</td>
                                    <td><input type="date" class="form-control" id="staged_dt_initial"></td>
                                    <td style="text-align:center;"><input type="checkbox" id="staged_opt_initial"></td>
                                </tr>
                                <tr>
                                    <td><strong>Q1 Assessment</strong></td>
                                    <td>DOJ + 3 calendar months</td>
                                    <td><input type="date" class="form-control" id="staged_dt_q1"></td>
                                    <td style="text-align:center;"><input type="checkbox" id="staged_opt_q1"></td>
                                </tr>
                                <tr>
                                    <td><strong>Q2 Assessment</strong></td>
                                    <td>DOJ + 6 calendar months</td>
                                    <td><input type="date" class="form-control" id="staged_dt_q2"></td>
                                    <td style="text-align:center;"><input type="checkbox" id="staged_opt_q2"></td>
                                </tr>
                                <tr>
                                    <td><strong>Q3 Assessment</strong></td>
                                    <td>DOJ + 9 calendar months</td>
                                    <td><input type="date" class="form-control" id="staged_dt_q3"></td>
                                    <td style="text-align:center;"><input type="checkbox" id="staged_opt_q3"></td>
                                </tr>
                                <tr>
                                    <td><strong>Q4 Assessment</strong></td>
                                    <td>DOJ + 12 calendar months</td>
                                    <td><input type="date" class="form-control" id="staged_dt_q4"></td>
                                    <td style="text-align:center;"><input type="checkbox" id="staged_opt_q4"></td>
                                </tr>
                                <tr>
                                    <td><strong>Exit Feedback</strong></td>
                                    <td>LWD + 3 calendar months</td>
                                    <td><input type="date" class="form-control" id="staged_dt_exit"></td>
                                    <td style="text-align:center;"><input type="checkbox" id="staged_opt_exit"></td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>

                <div style="display:flex; justify-content:flex-end; gap:10px; margin-top:20px;">
                    <button type="button" class="btn btn-secondary" onclick="closeModal('modalEditStaged')">Cancel</button>
                    <button type="submit" class="btn btn-primary">Save Changes to Staging</button>
                </div>
            </form>
        </div>
    </div>

    <!-- ======================================================================= -->
    <!-- 7. VIEW TRAINEE DOSSIER MODAL                                           -->
    <!-- ======================================================================= -->
    <div id="modalViewTrainee" class="modal-overlay">
        <div class="modal-card" style="max-width:760px;">
            <div class="modal-header">
                <div>
                    <div style="display:flex; align-items:center; gap:8px;">
                        <h3 id="viewDossierName">Apprentice Profile</h3>
                        <span id="viewDossierStatusBadge" class="badge">Active</span>
                    </div>
                    <p style="font-size:12px; color:var(--text-muted); margin-top:2px;" id="viewDossierId">ID: -</p>
                </div>
                <button class="btn-close-modal" onclick="closeModal('modalViewTrainee')">&times;</button>
            </div>

            <!-- Profile Overview Cards -->
            <div class="dossier-grid">
                <div class="dossier-card">
                    <div class="d-label">Apprentice Email</div>
                    <div class="d-val" id="viewDossierEmail">-</div>
                </div>
                <div class="dossier-card">
                    <div class="d-label">Department</div>
                    <div class="d-val" id="viewDossierDept">-</div>
                </div>
                <div class="dossier-card">
                    <div class="d-label">Location / Hub</div>
                    <div class="d-val" id="viewDossierLocation">-</div>
                </div>
                <div class="dossier-card">
                    <div class="d-label">Reporting Manager</div>
                    <div class="d-val" id="viewDossierManager">-</div>
                </div>
                <div class="dossier-card">
                    <div class="d-label">Date of Joining (DOJ)</div>
                    <div class="d-val" id="viewDossierDoj">-</div>
                </div>
                <div class="dossier-card">
                    <div class="d-label">Last Working Date (LWD)</div>
                    <div class="d-val" id="viewDossierLwd">-</div>
                </div>
            </div>

            <div style="margin:20px 0 12px;">
                <h4 style="font-size:13.5px; font-weight:700; margin-bottom:8px;">Milestone Schedule Timelines</h4>
                <div class="table-responsive">
                    <table class="data-table" id="tableViewDossierStages">
                        <thead>
                            <tr>
                                <th>Stage</th>
                                <th>Recipient</th>
                                <th>Scheduled Date</th>
                                <th>Status</th>
                                <th>Type</th>
                                <th>Opt-Out</th>
                            </tr>
                        </thead>
                        <tbody></tbody>
                    </table>
                </div>
            </div>

            <div style="display:flex; justify-content:space-between; align-items:center; margin-top:20px;">
                <button type="button" class="btn btn-secondary" onclick="closeModal('modalViewTrainee')">Close</button>
                <button type="button" class="btn btn-primary" id="btnDossierEditAction" onclick="editFromDossier()">✏️ Edit Profile & Dates</button>
            </div>
        </div>
    </div>

    <!-- TOAST CONTAINER -->
    <div id="toastContainer" class="toast-container"></div>

    <!-- ======================================================================= -->
    <!-- 6. FRONTEND JAVASCRIPT APPLICATION CODE                                 -->
    <!-- ======================================================================= -->
    <script>
        // Global State
        let authToken = localStorage.getItem("naps_admin_token") || null;
        let currentUser = localStorage.getItem("naps_admin_user") || null;
        let stagedUploadRows = [];
        let currentEditingTrainee = null;
        let currentEditingStagedIndex = null;
        let currentDossierTraineeId = null;
        let directoryViewMode = "roster"; // "roster" or "matrix"
        let cachedTraineesList = [];

        // Utility Date & String Helpers
        function uiDateToIso(dStr) {
            if (!dStr) return "";
            dStr = String(dStr).trim();
            if (/^[0-9]{4}-[0-9]{2}-[0-9]{2}$/.test(dStr)) return dStr;
            const parts = dStr.split("/");
            if (parts.length === 3) {
                const day = parts[0].padStart(2, "0");
                const month = parts[1].padStart(2, "0");
                const year = parts[2];
                return `${year}-${month}-${day}`;
            }
            return "";
        }

        function isoDateToUi(isoStr) {
            if (!isoStr) return "";
            isoStr = String(isoStr).trim();
            if (/^[0-9]{2}[/][0-9]{2}[/][0-9]{4}$/.test(isoStr)) return isoStr;
            const parts = isoStr.split("-");
            if (parts.length === 3) {
                return `${parts[2].padStart(2, "0")}/${parts[1].padStart(2, "0")}/${parts[0]}`;
            }
            return isoStr;
        }

        function escapeHtml(str) {
            if (str === null || str === undefined) return "";
            return String(str)
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;")
                .replace(/"/g, "&quot;")
                .replace(/'/g, "&#039;");
        }

        // On Page Load
        document.addEventListener("DOMContentLoaded", () => {
            // Set default date for dispatch worker
            const today = new Date().toISOString().split("T")[0];
            const dateInput = document.getElementById("workerTargetDate");
            if (dateInput) dateInput.value = today;

            // Global backdrop click to dismiss modals without reloading
            document.addEventListener("click", (e) => {
                if (e.target && e.target.classList && e.target.classList.contains("modal-overlay")) {
                    e.target.classList.remove("open");
                }
            });

            // Escape key listener to dismiss any open modal
            document.addEventListener("keydown", (e) => {
                if (e.key === "Escape" || e.keyCode === 27) {
                    document.querySelectorAll(".modal-overlay.open").forEach(m => m.classList.remove("open"));
                }
            });

            if (authToken) {
                verifySessionAndBoot();
            } else {
                showLoginGate();
            }
        });

        // Toast Helper
        function showToast(message, type = "info") {
            const container = document.getElementById("toastContainer");
            const toast = document.createElement("div");
            toast.className = `toast ${type}`;
            toast.innerText = message;
            container.appendChild(toast);
            setTimeout(() => {
                toast.style.opacity = "0";
                setTimeout(() => toast.remove(), 300);
            }, 4000);
        }

        // Authenticated Fetch Helper
        async function apiFetch(url, options = {}) {
            options.headers = options.headers || {};
            if (authToken) {
                options.headers["Authorization"] = `Bearer ${authToken}`;
            }
            const res = await fetch(url, options);
            if (res.status === 401) {
                authToken = null;
                localStorage.removeItem("naps_admin_token");
                showLoginGate();
                throw new Error("Session expired. Please sign in again.");
            }
            return res;
        }

        // Session Verification
        async function verifySessionAndBoot() {
            try {
                const res = await apiFetch("/api/auth/me");
                if (res.ok) {
                    const data = await res.json();
                    currentUser = data.username;
                    document.getElementById("sidebarUsername").innerText = currentUser;
                    document.getElementById("loginGate").style.display = "none";
                    updateDbChip(data.database_engine);
                    loadDashboardStats();
                    loadQueue();
                } else {
                    showLoginGate();
                }
            } catch (err) {
                showLoginGate();
            }
        }

        function showLoginGate() {
            document.getElementById("loginGate").style.display = "flex";
        }

        function updateDbChip(engine) {
            const chip = document.getElementById("chipDatabase");
            const settingsBadge = document.getElementById("settingsDbBadge");
            const settingsDesc = document.getElementById("settingsDbDesc");
            const banner = document.getElementById("bannerEphemeralDb");
            if (engine === "postgres") {
                chip.innerHTML = `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg> Database: PostgreSQL (Persistent)`;
                chip.className = "chip-meta postgres";
                if (settingsBadge) {
                    settingsBadge.innerText = "PostgreSQL (Cloud Persistent)";
                    settingsBadge.className = "badge badge-scheduled";
                    settingsDesc.innerText = "Connected to persistent cloud PostgreSQL (Neon / Supabase / Vercel Postgres). Data persists across all deployments.";
                }
                if (banner) banner.style.display = "none";
            } else {
                chip.innerHTML = `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg> Database: SQLite (Temporary / Local)`;
                chip.className = "chip-meta";
                if (settingsBadge) {
                    settingsBadge.innerText = "SQLite (Local / Ephemeral)";
                    settingsBadge.className = "badge badge-optout";
                    settingsDesc.innerText = "Operating on local SQLite. On Vercel Serverless containers, local /tmp data resets between idle instances. Add POSTGRES_URL to your Vercel Environment Variables to retain trainees permanently.";
                }
                if (banner) banner.style.display = "flex";
            }
        }

        // Login Submit
        async function handleLoginSubmit(e) {
            e.preventDefault();
            const btn = document.getElementById("btnLoginSubmit");
            const errBox = document.getElementById("loginError");
            errBox.style.display = "none";
            btn.disabled = true;
            btn.innerText = "Signing in...";

            const username = document.getElementById("loginUsername").value.trim();
            const password = document.getElementById("loginPassword").value.trim();

            try {
                const res = await fetch("/api/auth/login", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ username, password })
                });
                const data = await res.json();
                if (res.ok) {
                    authToken = data.token;
                    currentUser = data.username;
                    localStorage.setItem("naps_admin_token", authToken);
                    localStorage.setItem("naps_admin_user", currentUser);
                    document.getElementById("sidebarUsername").innerText = currentUser;
                    document.getElementById("loginGate").style.display = "none";
                    updateDbChip(data.database_engine);
                    loadDashboardStats();
                    loadQueue();
                    showToast("Administrator signed in successfully.", "success");
                } else {
                    errBox.innerText = data.detail || "Invalid login credentials.";
                    errBox.style.display = "block";
                }
            } catch (err) {
                errBox.innerText = "Connection error. Please try again.";
                errBox.style.display = "block";
            } finally {
                btn.disabled = false;
                btn.innerText = "Sign In to Portal";
            }
        }

        // Logout
        async function handleLogout() {
            if (confirm("Sign out of the administrator portal?")) {
                try {
                    await apiFetch("/api/auth/logout", { method: "POST" });
                } catch (e) {}
                authToken = null;
                localStorage.removeItem("naps_admin_token");
                localStorage.removeItem("naps_admin_user");
                location.reload();
            }
        }

        // Navigation Switching
        function switchView(viewName) {
            document.querySelectorAll(".nav-item").forEach(item => item.classList.remove("active"));
            document.querySelectorAll(".app-view").forEach(v => v.classList.remove("active-view"));

            const targetView = document.getElementById(`view-${viewName}`);
            if (targetView) targetView.classList.add("active-view");

            const titles = {
                "dashboard": ["Operational Dashboard", "Apprentice lifecycle health, milestone timelines, and simulation statistics."],
                "directory": ["Trainee Directory", "Master apprentice roster with synchronized milestone timelines and profile manager."],
                "add-trainee": ["Register Apprentice", "Add a new apprentice with automatic LWD and independent milestone calculation."],
                "import": ["Batch Import Engine", "Upload Excel or CSV rosters with staging review and validation breakdown."],
                "exceptions": ["Delivery Exceptions", "Review interrupted dispatches and administratively resolve uncertain records."],
                "audit": ["System Audit Trail", "Immutable record of apprentice operations, state changes, and worker executions."],
                "settings": ["Settings & Safety Diagnostics", "Deployment parameters, database connections, and simulation locks."]
            };

            if (titles[viewName]) {
                document.getElementById("viewHeaderTitle").innerText = titles[viewName][0];
                document.getElementById("viewHeaderSubtitle").innerText = titles[viewName][1];
            }

            // Find matching nav item
            const navItems = document.querySelectorAll(".nav-item");
            navItems.forEach(n => {
                if (n.getAttribute("onclick") && n.getAttribute("onclick").includes(viewName)) {
                    n.classList.add("active");
                }
            });

            // Trigger data loader for view
            if (viewName === "dashboard") { loadDashboardStats(); loadQueue(); }
            else if (viewName === "directory") { loadTrainees(); }
            else if (viewName === "exceptions") { loadExceptions(); }
            else if (viewName === "audit") { loadAuditLogs(); }
        }

        // DASHBOARD LOADER
        async function loadDashboardStats() {
            try {
                const res = await apiFetch("/api/dashboard/stats");
                if (!res.ok) {
                    let errMsg = `Server returned status ${res.status}`;
                    try { const errObj = await res.json(); if (errObj.detail) errMsg = errObj.detail; } catch (_) {}
                    console.warn("Dashboard stats notice:", errMsg);
                    return;
                }
                const data = await res.json();
                if (data.total_trainees !== undefined) document.getElementById("statTotalTrainees").innerText = data.total_trainees;
                if (data.active_count !== undefined) document.getElementById("statActive").innerText = data.active_count;
                if (data.completed_count !== undefined && data.on_roll_count !== undefined) {
                    document.getElementById("statCompleted").innerText = (data.completed_count + data.on_roll_count);
                }
                if (data.left_count !== undefined) document.getElementById("statLeft").innerText = data.left_count;
                if (data.simulated_sent_count !== undefined) document.getElementById("statSent").innerText = data.simulated_sent_count;
                if (data.pending_queue_count !== undefined) document.getElementById("statPending").innerText = data.pending_queue_count;
                if (data.exceptions_count !== undefined) document.getElementById("statExceptions").innerText = data.exceptions_count;
            } catch (e) {
                console.error("Dashboard stats error:", e);
            }
        }

        async function loadQueue() {
            try {
                const res = await apiFetch("/api/dashboard/queue");
                if (!res.ok) {
                    let errMsg = `Server returned status ${res.status}`;
                    try { const errObj = await res.json(); if (errObj.detail) errMsg = errObj.detail; } catch (_) {}
                    console.warn("Queue load notice:", errMsg);
                    return;
                }
                const data = await res.json();
                const tbody = document.querySelector("#tableQueue tbody");
                tbody.innerHTML = "";

                if (!data.queue || data.queue.length === 0) {
                    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding:20px; color:#94A3B8;">No pending milestone emails due in queue.</td></tr>`;
                    return;
                }

                data.queue.forEach(item => {
                    const row = document.createElement("tr");
                    const badgeClass = item.due_status === "Due Today" ? "badge-custom" : (item.due_status === "Overdue" ? "badge-cancelled" : "badge-scheduled");
                    row.innerHTML = `
                        <td>#${item.queue_id}</td>
                        <td><strong>${item.trainee_id}</strong></td>
                        <td>${item.trainee_name}</td>
                        <td>${formatStageLabel(item.stage)}</td>
                        <td>${item.scheduled_date}</td>
                        <td><span class="badge ${badgeClass}">${item.due_status}</span></td>
                        <td><span class="badge badge-scheduled">${item.status}</span></td>
                    `;
                    tbody.appendChild(row);
                });
            } catch (e) {
                console.error("Queue load error:", e);
            }
        }

        function formatStageLabel(stg) {
            const key = String(stg || "").toLowerCase();
            const map = {
                "initial": "Initial Welcome (DOJ+15d)",
                "q1": "Quarterly Assessment 1 (DOJ+3m)",
                "q2": "Quarterly Assessment 2 (DOJ+6m)",
                "q3": "Quarterly Assessment 3 (DOJ+9m)",
                "q4": "Quarterly Assessment 4 (DOJ+12m)",
                "exit": "Exit Feedback (LWD+3m)"
            };
            return map[key] || stg;
        }

        // TRIGGER WORKER CYCLE
        async function executeWorkerCycle() {
            const dateVal = document.getElementById("workerTargetDate").value;
            if (!confirm(`Run background worker dispatch cycle for date: ${dateVal} in SIMULATION mode?`)) return;

            try {
                showToast("Executing dispatch worker cycle...", "info");
                const res = await apiFetch("/api/worker/run", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ target_date: dateVal })
                });
                const data = await res.json();
                if (res.ok) {
                    const s = data.summary;
                    showToast(`Simulation complete: ${s.sent} simulated, ${s.due} due, ${s.failed} failed.`, "success");
                    loadDashboardStats();
                    loadQueue();
                } else {
                    showToast(data.detail || "Worker run failed", "danger");
                }
            } catch (err) {
                showToast("Worker execution failed: " + err.message, "danger");
            }
        }

        // TRAINEE DIRECTORY LOADER & VIEW MODES
        function setDirectoryViewMode(mode) {
            directoryViewMode = mode;
            const btnRoster = document.getElementById("btnToggleRoster");
            const btnMatrix = document.getElementById("btnToggleMatrix");
            if (btnRoster && btnMatrix) {
                if (mode === "roster") {
                    btnRoster.classList.add("active");
                    btnMatrix.classList.remove("active");
                } else {
                    btnRoster.classList.remove("active");
                    btnMatrix.classList.add("active");
                }
            }
            renderTraineeTable(cachedTraineesList);
        }

        async function loadTrainees() {
            const search = document.getElementById("dirSearch").value.trim();
            const status = document.getElementById("dirStatusFilter").value;
            const thead = document.getElementById("headTrainees");
            const tbody = document.querySelector("#tableTrainees tbody");
            const colSpan = directoryViewMode === "roster" ? 7 : 12;
            tbody.innerHTML = `<tr><td colspan="${colSpan}" style="text-align:center; padding:24px; color:#94A3B8;">Loading apprentice directory...</td></tr>`;

            try {
                const params = new URLSearchParams();
                if (search) params.append("search", search);
                if (status && status !== "All") params.append("status_filter", status);

                const res = await apiFetch(`/api/trainees?${params.toString()}`);
                const data = await res.json();
                cachedTraineesList = data.trainees || [];

                const countBadge = document.getElementById("dirCountBadge");
                if (countBadge) countBadge.innerText = `${cachedTraineesList.length} apprentice(s)`;

                renderTraineeTable(cachedTraineesList);
            } catch (err) {
                tbody.innerHTML = `<tr><td colspan="${colSpan}" style="text-align:center; padding:24px; color:var(--danger);">Failed to load trainees: ${err.message}</td></tr>`;
            }
        }

        function renderTraineeTable(trainees) {
            const thead = document.getElementById("headTrainees");
            const tbody = document.querySelector("#tableTrainees tbody");
            tbody.innerHTML = "";

            const colSpan = directoryViewMode === "roster" ? 7 : 12;
            if (!trainees || trainees.length === 0) {
                if (thead) thead.innerHTML = "";
                tbody.innerHTML = `<tr><td colspan="${colSpan}" style="text-align:center; padding:32px 20px; color:#94A3B8; font-size:13px;">No apprentices found matching search and filter criteria.</td></tr>`;
                return;
            }

            if (directoryViewMode === "roster") {
                // Roster View - Engineered for readability without overflow
                if (thead) {
                    thead.innerHTML = `
                        <tr>
                            <th>Apprentice</th>
                            <th>Department & Location</th>
                            <th>Reporting Manager</th>
                            <th style="text-align:center;">Status</th>
                            <th>Tenure</th>
                            <th>Milestone Progress Tracker</th>
                            <th style="text-align:center; width:130px;">Actions</th>
                        </tr>
                    `;
                }

                trainees.forEach(t => {
                    const row = document.createElement("tr");
                    const statusBadge = t.status === "Active" ? "badge-active" : (t.status === "Left" ? "badge-left" : "badge-scheduled");

                    function renderStepperNode(label, s) {
                        if (!s) return `<span class="stepper-node stg-optout" title="${label}: Not configured">${label}</span>`;
                        let cls = "stg-scheduled";
                        let tip = `${label} (${s.scheduled_date || '-'}) • Status: ${s.status || 'Scheduled'}`;
                        if (s.status === "Sent") {
                            cls = "stg-sent";
                            tip = `${label} (${s.scheduled_date}) • Sent [Simulated]`;
                        } else if (s.is_opted_out) {
                            cls = "stg-optout";
                            tip = `${label} (${s.scheduled_date}) • Opted Out`;
                        } else if (s.status === "Cancelled") {
                            cls = "stg-cancelled";
                            tip = `${label} (${s.scheduled_date}) • Cancelled`;
                        } else if (s.is_custom_date) {
                            cls = "stg-custom";
                            tip = `${label} (${s.scheduled_date}) • Custom Date`;
                        }
                        return `<span class="stepper-node ${cls}" title="${tip}">${label}</span>`;
                    }

                    const stg = t.stages || {};
                    const stepperHtml = `
                        <div class="milestone-stepper" title="Click 'View' for full date timeline">
                            ${renderStepperNode("Init", stg.initial || stg.INITIAL)}
                            <span style="color:#CBD5E1; font-size:10px;">›</span>
                            ${renderStepperNode("Q1", stg.q1 || stg.Q1)}
                            <span style="color:#CBD5E1; font-size:10px;">›</span>
                            ${renderStepperNode("Q2", stg.q2 || stg.Q2)}
                            <span style="color:#CBD5E1; font-size:10px;">›</span>
                            ${renderStepperNode("Q3", stg.q3 || stg.Q3)}
                            <span style="color:#CBD5E1; font-size:10px;">›</span>
                            ${renderStepperNode("Q4", stg.q4 || stg.Q4)}
                            <span style="color:#CBD5E1; font-size:10px;">›</span>
                            ${renderStepperNode("Exit", stg.exit || stg.EXIT)}
                        </div>
                    `;

                    row.innerHTML = `
                        <td>
                            <div style="font-weight:700; color:var(--primary); cursor:pointer;" data-id="${escapeHtml(t.trainee_id)}" onclick="openViewDossierModal(this.getAttribute('data-id'))" title="Click to view full dossier">
                                ${escapeHtml(t.trainee_name)}
                            </div>
                            <div style="font-size:11px; color:var(--text-muted); font-family:var(--font-mono); margin-top:1px;">
                                ${escapeHtml(t.trainee_id)}
                            </div>
                            <div style="font-size:11.5px; margin-top:2px;">
                                <a href="mailto:${escapeHtml(t.trainee_email)}" style="color:#64748B; text-decoration:none;" title="Send email">
                                    ✉️ ${escapeHtml(t.trainee_email)}
                                </a>
                            </div>
                        </td>
                        <td>
                            <div style="font-weight:600; color:var(--text-main); font-size:13px;">${escapeHtml(t.department || 'General')}</div>
                            <div style="font-size:11.5px; color:var(--text-muted); margin-top:2px;">📍 ${escapeHtml(t.location || 'Headquarters')}</div>
                        </td>
                        <td>
                            <div style="font-weight:600; color:var(--text-main); font-size:13px;">${escapeHtml(t.manager_name || 'N/A')}</div>
                            <div style="font-size:11.5px; margin-top:2px;">
                                ${t.manager_email ? `<a href="mailto:${escapeHtml(t.manager_email)}" style="color:#64748B; text-decoration:none;">✉️ ${escapeHtml(t.manager_email)}</a>` : '<span style="color:#94A3B8;">-</span>'}
                            </div>
                        </td>
                        <td style="text-align:center;">
                            <span class="badge ${statusBadge}">${t.status}</span>
                        </td>
                        <td>
                            <div style="font-size:11.5px; line-height:1.45;">
                                <div><span style="color:var(--text-muted); font-size:10.5px;">DOJ:</span> <strong>${t.date_of_joining || '-'}</strong></div>
                                <div><span style="color:var(--text-muted); font-size:10.5px;">LWD:</span> <span style="color:#64748B;">${t.last_working_date || '-'}</span></div>
                            </div>
                        </td>
                        <td>
                            ${stepperHtml}
                        </td>
                        <td style="text-align:center;">
                            <div style="display:inline-flex; gap:6px;">
                                <button type="button" class="btn btn-secondary btn-sm" data-id="${escapeHtml(t.trainee_id)}" onclick="openViewDossierModal(this.getAttribute('data-id'))" title="View Full Profile">👁️ View</button>
                                <button type="button" class="btn btn-secondary btn-sm" data-id="${escapeHtml(t.trainee_id)}" onclick="openEditTraineeModal(this.getAttribute('data-id'))" title="Edit Profile & Dates">✏️ Edit</button>
                            </div>
                        </td>
                    `;
                    tbody.appendChild(row);
                });
            } else {
                // Milestone Matrix View
                if (thead) {
                    thead.innerHTML = `
                        <tr>
                            <th>Trainee ID</th>
                            <th>Apprentice Name</th>
                            <th style="text-align:center;">Status</th>
                            <th>DOJ</th>
                            <th>LWD</th>
                            <th>Initial (15d)</th>
                            <th>Q1 (3m)</th>
                            <th>Q2 (6m)</th>
                            <th>Q3 (9m)</th>
                            <th>Q4 (12m)</th>
                            <th>Exit (3m)</th>
                            <th style="text-align:center; width:130px;">Actions</th>
                        </tr>
                    `;
                }

                trainees.forEach(t => {
                    const row = document.createElement("tr");

                    function renderStageBadge(stgKey) {
                        const stgObj = t.stages || {};
                        const s = stgObj[stgKey] || stgObj[stgKey.toUpperCase()];
                        if (!s) return "-";
                        if (s.status === "Sent") return `<span class="badge badge-simulated">${s.scheduled_date} [Simulated]</span>`;
                        if (s.is_opted_out) return `<span class="badge badge-optout">${s.scheduled_date} [Opted Out]</span>`;
                        if (s.status === "Cancelled") return `<span class="badge badge-cancelled">${s.scheduled_date} [Cancelled]</span>`;
                        if (s.is_custom_date) return `<span class="badge badge-custom">${s.scheduled_date} [Custom]</span>`;
                        return `<span class="badge badge-scheduled">${s.scheduled_date}</span>`;
                    }

                    const statusBadge = t.status === "Active" ? "badge-active" : (t.status === "Left" ? "badge-left" : "badge-scheduled");

                    row.innerHTML = `
                        <td><strong>${t.trainee_id}</strong></td>
                        <td>
                            <div style="font-weight:700; color:var(--primary); cursor:pointer;" data-id="${escapeHtml(t.trainee_id)}" onclick="openViewDossierModal(this.getAttribute('data-id'))">
                                ${escapeHtml(t.trainee_name)}
                            </div>
                            <div style="font-size:11px; color:var(--text-muted);">${escapeHtml(t.trainee_email)}</div>
                        </td>
                        <td style="text-align:center;"><span class="badge ${statusBadge}">${t.status}</span></td>
                        <td>${t.date_of_joining}</td>
                        <td>${t.last_working_date}</td>
                        <td>${renderStageBadge("initial")}</td>
                        <td>${renderStageBadge("q1")}</td>
                        <td>${renderStageBadge("q2")}</td>
                        <td>${renderStageBadge("q3")}</td>
                        <td>${renderStageBadge("q4")}</td>
                        <td>${renderStageBadge("exit")}</td>
                        <td style="text-align:center;">
                            <div style="display:inline-flex; gap:6px;">
                                <button type="button" class="btn btn-secondary btn-sm" data-id="${escapeHtml(t.trainee_id)}" onclick="openViewDossierModal(this.getAttribute('data-id'))" title="View Full Profile">👁️ View</button>
                                <button type="button" class="btn btn-secondary btn-sm" data-id="${escapeHtml(t.trainee_id)}" onclick="openEditTraineeModal(this.getAttribute('data-id'))" title="Edit Profile & Dates">✏️ Edit</button>
                            </div>
                        </td>
                    `;
                    tbody.appendChild(row);
                });
            }
        }

        // VIEW DOSSIER MODAL
        function openViewDossierModal(traineeId) {
            if (!traineeId) return;
            const t = (cachedTraineesList || []).find(x => String(x.trainee_id).trim() === String(traineeId).trim());
            if (!t) {
                openDossierFromApi(traineeId);
                return;
            }
            populateDossierModal(t);
        }

        async function openDossierFromApi(traineeId) {
            try {
                showToast("Loading apprentice profile...", "info");
                const res = await apiFetch(`/api/trainees/${encodeURIComponent(traineeId)}`);
                if (!res.ok) throw new Error("Apprentice record not found");
                const data = await res.json();
                const t = data.trainee;
                t.stages = {};
                (data.schedules || []).forEach(s => {
                    const k = (s.stage || "").toLowerCase();
                    t.stages[k] = s;
                    t.stages[s.stage] = s;
                });
                populateDossierModal(t);
            } catch (err) {
                showToast(err.message, "danger");
            }
        }

        function populateDossierModal(t) {
            currentDossierTraineeId = t.trainee_id;

            document.getElementById("viewDossierName").innerText = t.trainee_name || "Apprentice Profile";
            document.getElementById("viewDossierId").innerText = `ID: ${t.trainee_id}`;

            const badgeEl = document.getElementById("viewDossierStatusBadge");
            if (badgeEl) {
                badgeEl.innerText = t.status || "Active";
                badgeEl.className = "badge " + (t.status === "Active" ? "badge-active" : (t.status === "Left" ? "badge-left" : "badge-scheduled"));
            }

            document.getElementById("viewDossierEmail").innerHTML = `<a href="mailto:${escapeHtml(t.trainee_email)}">${escapeHtml(t.trainee_email)}</a>`;
            document.getElementById("viewDossierDept").innerText = t.department || "Unassigned";
            document.getElementById("viewDossierLocation").innerText = t.location || "Headquarters";

            const mgrHtml = t.manager_name ? `${escapeHtml(t.manager_name)} ${t.manager_email ? `<br><a href="mailto:${escapeHtml(t.manager_email)}" style="font-size:12px; color:var(--text-muted);">${escapeHtml(t.manager_email)}</a>` : ''}` : "-";
            document.getElementById("viewDossierManager").innerHTML = mgrHtml;

            document.getElementById("viewDossierDoj").innerText = t.date_of_joining || "-";
            document.getElementById("viewDossierLwd").innerText = `${t.last_working_date || '-'} (${t.lwd_mode || '12M Auto'})`;

            const tbody = document.querySelector("#tableViewDossierStages tbody");
            tbody.innerHTML = "";

            const stagesConfig = [
                { key: "initial", name: "Initial Welcome", recip: "Trainee" },
                { key: "q1", name: "Quarterly Assessment 1", recip: "Manager" },
                { key: "q2", name: "Quarterly Assessment 2", recip: "Manager" },
                { key: "q3", name: "Quarterly Assessment 3", recip: "Manager" },
                { key: "q4", name: "Quarterly Assessment 4", recip: "Manager" },
                { key: "exit", name: "Exit Feedback", recip: "Trainee" }
            ];

            stagesConfig.forEach(cfg => {
                const s = t.stages ? (t.stages[cfg.key] || t.stages[cfg.key.toUpperCase()]) : null;
                const tr = document.createElement("tr");
                if (s) {
                    let statusBadge = `<span class="badge badge-scheduled">${s.status}</span>`;
                    if (s.status === "Sent") statusBadge = `<span class="badge badge-simulated">Sent [Simulated]</span>`;
                    else if (s.status === "Cancelled") statusBadge = `<span class="badge badge-cancelled">Cancelled</span>`;

                    const typeBadge = s.is_custom_date ? `<span class="badge badge-custom">Custom</span>` : `<span class="badge" style="background:#F1F5F9; color:#475569;">Standard</span>`;
                    const optBadge = s.is_opted_out ? `<span class="badge badge-optout">Opted Out</span>` : `<span class="badge badge-active">Active</span>`;

                    tr.innerHTML = `
                        <td><strong>${cfg.name}</strong></td>
                        <td>${cfg.recip}</td>
                        <td><strong>${s.scheduled_date || s.scheduled_date_raw || '-'}</strong></td>
                        <td>${statusBadge}</td>
                        <td>${typeBadge}</td>
                        <td>${optBadge}</td>
                    `;
                } else {
                    tr.innerHTML = `
                        <td><strong>${cfg.name}</strong></td>
                        <td>${cfg.recip}</td>
                        <td>-</td>
                        <td>-</td>
                        <td>-</td>
                        <td>-</td>
                    `;
                }
                tbody.appendChild(tr);
            });

            document.getElementById("modalViewTrainee").classList.add("open");
        }

        function editFromDossier() {
            closeModal("modalViewTrainee");
            if (currentDossierTraineeId) {
                openEditTraineeModal(currentDossierTraineeId);
            }
        }

        // EDIT TRAINEE MODAL
        async function openEditTraineeModal(traineeId) {
            if (!traineeId) return;
            try {
                showToast("Loading apprentice details...", "info");
                const res = await apiFetch(`/api/trainees/${encodeURIComponent(traineeId)}`);
                if (!res.ok) {
                    const err = await res.json();
                    throw new Error(err.detail || "Apprentice not found");
                }
                const data = await res.json();
                currentEditingTrainee = data;

                const t = data.trainee;
                document.getElementById("editTraineeId").value = t.trainee_id;
                document.getElementById("editName").value = t.trainee_name;
                document.getElementById("editEmail").value = t.trainee_email;
                document.getElementById("editMgrName").value = t.manager_name;
                document.getElementById("editMgrEmail").value = t.manager_email;
                document.getElementById("editStatus").value = t.status;

                handleStatusChangeInModal(t.status);

                // Populate schedules table
                const sTable = document.querySelector("#tableModalSchedules tbody");
                sTable.innerHTML = "";
                data.schedules.forEach(s => {
                    const row = document.createElement("tr");
                    const isSent = s.status === "Sent";
                    const stageKey = (s.stage || "").toLowerCase();
                    row.innerHTML = `
                        <td><strong>${formatStageLabel(stageKey)}</strong></td>
                        <td><span class="badge ${s.status === 'Sent' ? 'badge-simulated' : (s.status === 'Cancelled' ? 'badge-cancelled' : 'badge-scheduled')}">${s.status}</span></td>
                        <td>
                            <input type="date" class="form-control" id="sched_date_${stageKey}" value="${s.scheduled_date_raw || uiDateToIso(s.scheduled_date) || ''}" ${isSent ? 'disabled' : ''}>
                        </td>
                        <td style="text-align:center;">
                            <input type="checkbox" id="sched_opt_${stageKey}" ${s.is_opted_out ? 'checked' : ''} ${isSent ? 'disabled' : ''}>
                        </td>
                    `;
                    sTable.appendChild(row);
                });

                document.getElementById("modalEditTrainee").classList.add("open");
            } catch (e) {
                showToast("Failed to load trainee details: " + e.message, "danger");
            }
        }

        function handleStatusChangeInModal(statusVal) {
            const grp = document.getElementById("groupActualLwd");
            const input = document.getElementById("editActualLwd");
            if (statusVal === "Left") {
                grp.style.display = "block";
                input.required = true;
            } else {
                grp.style.display = "none";
                input.required = false;
            }
        }

        async function handleEditTraineeSubmit(e) {
            e.preventDefault();
            const tid = document.getElementById("editTraineeId").value;
            const name = document.getElementById("editName").value.trim();
            const email = document.getElementById("editEmail").value.trim();
            const mgrName = document.getElementById("editMgrName").value.trim();
            const mgrEmail = document.getElementById("editMgrEmail").value.trim();
            const status = document.getElementById("editStatus").value;
            const actualLwd = document.getElementById("editActualLwd").value;

            try {
                showToast("Saving apprentice changes...", "info");
                // 1. Update basic info and status
                const updatePayload = {
                    trainee_name: name,
                    trainee_email: email,
                    manager_name: mgrName,
                    manager_email: mgrEmail,
                    status: status,
                };
                if (status === "Left" && actualLwd) {
                    updatePayload.confirmed_actual_lwd = actualLwd;
                }

                const res = await apiFetch(`/api/trainees/${encodeURIComponent(tid)}`, {
                    method: "PUT",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(updatePayload)
                });
                if (!res.ok) {
                    const err = await res.json();
                    throw new Error(err.detail || "Update failed");
                }

                // 2. Update schedules
                const schedPayload = { stages: {} };
                const stages = ["initial", "q1", "q2", "q3", "q4", "exit"];
                stages.forEach(stg => {
                    const dateEl = document.getElementById(`sched_date_${stg}`) || document.getElementById(`sched_date_${stg.toUpperCase()}`);
                    const optEl = document.getElementById(`sched_opt_${stg}`) || document.getElementById(`sched_opt_${stg.toUpperCase()}`);
                    if (dateEl && optEl && !dateEl.disabled) {
                        schedPayload.stages[stg] = {
                            scheduled_date: dateEl.value,
                            opt_out: optEl.checked
                        };
                    }
                });

                const sRes = await apiFetch(`/api/trainees/${encodeURIComponent(tid)}/schedules`, {
                    method: "PUT",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(schedPayload)
                });
                if (!sRes.ok) {
                    const sErr = await sRes.json();
                    throw new Error(sErr.detail || "Failed to update milestone schedules");
                }

                closeModal("modalEditTrainee");
                showToast(`Apprentice '${tid}' updated successfully!`, "success");
                loadTrainees();
                loadDashboardStats();
            } catch (err) {
                showToast("Update error: " + err.message, "danger");
            }
        }

        async function archiveCurrentTrainee() {
            const tid = document.getElementById("editTraineeId").value;
            if (confirm(`Archive trainee '${tid}'? (All Sent history and schedules will be preserved in archived state).`)) {
                try {
                    await apiFetch(`/api/trainees/${tid}/archive`, { method: "POST" });
                    closeModal("modalEditTrainee");
                    showToast(`Trainee '${tid}' archived.`, "success");
                    loadTrainees();
                    loadDashboardStats();
                } catch (e) {
                    showToast("Archive error: " + e.message, "danger");
                }
            }
        }

        async function deleteCurrentTrainee() {
            const tid = document.getElementById("editTraineeId").value;
            if (confirm(`Permanently delete trainee '${tid}'? This is only allowed if NO emails have been sent.`)) {
                try {
                    const res = await apiFetch(`/api/trainees/${tid}`, { method: "DELETE" });
                    if (!res.ok) {
                        const err = await res.json();
                        throw new Error(err.detail);
                    }
                    closeModal("modalEditTrainee");
                    showToast(`Trainee '${tid}' deleted.`, "success");
                    loadTrainees();
                    loadDashboardStats();
                } catch (e) {
                    showToast(e.message, "danger");
                }
            }
        }

        function closeModal(modalId) {
            const el = document.getElementById(modalId);
            if (el) el.classList.remove("open");
        }

        // ADD NEW TRAINEE FORM & LIVE CALCULATOR
        function calculateLiveMilestones() {
            const dojVal = document.getElementById("addDoj").value;
            if (!dojVal) return;

            const doj = new Date(dojVal + "T00:00:00");
            if (isNaN(doj)) return;

            // Auto LWD: +12 calendar months
            const lwd = new Date(doj);
            lwd.setFullYear(lwd.getFullYear() + 1);

            document.getElementById("addLwdPreview").value = formatDateUIStr(lwd);

            // Calculate Stages:
            // Initial: DOJ + 15 calendar days
            const initDate = new Date(doj);
            initDate.setDate(initDate.getDate() + 15);

            // Q1: DOJ + 3m
            const q1Date = addMonthsClamped(doj, 3);
            // Q2: DOJ + 6m
            const q2Date = addMonthsClamped(doj, 6);
            // Q3: DOJ + 9m
            const q3Date = addMonthsClamped(doj, 9);
            // Q4: DOJ + 12m
            const q4Date = addMonthsClamped(doj, 12);
            // Exit: LWD + 3m
            const exitDate = addMonthsClamped(lwd, 3);

            const stagesConfig = [
                { key: "initial", name: "Initial Welcome (DOJ+15d)", recip: "Trainee", date: adjustWeekend(initDate) },
                { key: "q1", name: "Quarterly Assessment 1 (DOJ+3m)", recip: "Manager", date: adjustWeekend(q1Date) },
                { key: "q2", name: "Quarterly Assessment 2 (DOJ+6m)", recip: "Manager", date: adjustWeekend(q2Date) },
                { key: "q3", name: "Quarterly Assessment 3 (DOJ+9m)", recip: "Manager", date: adjustWeekend(q3Date) },
                { key: "q4", name: "Quarterly Assessment 4 (DOJ+12m)", recip: "Manager", date: adjustWeekend(q4Date) },
                { key: "exit", name: "Exit Feedback (LWD+3m)", recip: "Trainee", date: adjustWeekend(exitDate) }
            ];

            const tbody = document.getElementById("liveMilestoneRows");
            tbody.innerHTML = "";

            stagesConfig.forEach(cfg => {
                const row = document.createElement("tr");
                row.innerHTML = `
                    <td><strong>${cfg.name}</strong></td>
                    <td>${cfg.recip}</td>
                    <td><span class="badge badge-scheduled">${formatDateUIStr(cfg.date)}</span></td>
                    <td style="text-align:center;">
                        <input type="checkbox" id="add_opt_${cfg.key}">
                    </td>
                    <td>
                        <input type="date" class="form-control" id="add_custom_${cfg.key}" value="${cfg.date.toISOString().split('T')[0]}">
                    </td>
                `;
                tbody.appendChild(row);
            });
        }

        function addMonthsClamped(baseDate, months) {
            const d = new Date(baseDate);
            const expectedMonth = (d.getMonth() + months) % 12;
            d.setMonth(d.getMonth() + months);
            // Clamp if day overflowed
            if (d.getMonth() !== expectedMonth) {
                d.setDate(0);
            }
            return d;
        }

        function adjustWeekend(d) {
            const day = d.getDay();
            const res = new Date(d);
            if (day === 6) res.setDate(res.getDate() + 2); // Sat -> Mon
            if (day === 0) res.setDate(res.getDate() + 1); // Sun -> Mon
            return res;
        }

        function formatDateUIStr(d) {
            const day = String(d.getDate()).padStart(2, "0");
            const mon = String(d.getMonth() + 1).padStart(2, "0");
            return `${day}/${mon}/${d.getFullYear()}`;
        }

        async function handleAddTraineeSubmit(e) {
            e.preventDefault();
            const id = document.getElementById("addId").value.trim();
            const name = document.getElementById("addName").value.trim();
            const email = document.getElementById("addEmail").value.trim();
            const doj = document.getElementById("addDoj").value;
            const mgrName = document.getElementById("addMgrName").value.trim();
            const mgrEmail = document.getElementById("addMgrEmail").value.trim();
            const dept = document.getElementById("addDept").value.trim();
            const loc = document.getElementById("addLocation").value.trim();

            const stagePrefs = {};
            ["initial", "q1", "q2", "q3", "q4", "exit"].forEach(stg => {
                const optEl = document.getElementById(`add_opt_${stg}`);
                const dateEl = document.getElementById(`add_custom_${stg}`);
                if (optEl && dateEl) {
                    stagePrefs[stg] = {
                        opt_out: optEl.checked,
                        custom_date: dateEl.value || null
                    };
                }
            });

            try {
                const res = await apiFetch("/api/trainees", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        trainee_id: id,
                        trainee_name: name,
                        trainee_email: email,
                        date_of_joining: doj,
                        manager_name: mgrName,
                        manager_email: mgrEmail,
                        department: dept,
                        location: loc,
                        stage_preferences: stagePrefs
                    })
                });

                if (!res.ok) {
                    const err = await res.json();
                    throw new Error(err.detail);
                }

                showToast(`Apprentice '${id}' registered with 6 milestone schedules.`, "success");
                document.getElementById("formAddTrainee").reset();
                document.getElementById("addLwdPreview").value = "";
                document.getElementById("liveMilestoneRows").innerHTML = `<tr><td colspan="5" style="text-align:center; padding:12px; color:#94A3B8;">Select Date of Joining above to calculate milestone schedules.</td></tr>`;
                switchView("directory");
                loadDashboardStats();
            } catch (err) {
                showToast("Registration error: " + err.message, "danger");
            }
        }

        // BATCH IMPORT HANDLERS
        function downloadTemplateFile(fmt) {
            window.location.href = `/api/templates/download?format=${fmt}`;
        }

        async function handleFileSelected(e) {
            const file = e.target.files[0];
            if (!file) return;

            const formData = new FormData();
            formData.append("file", file);

            try {
                showToast("Parsing and validating import file...", "info");
                const res = await apiFetch("/api/import/preview", {
                    method: "POST",
                    body: formData
                });
                
                let data;
                try {
                    data = await res.json();
                } catch (parseErr) {
                    throw new Error(`Server returned HTTP ${res.status}: ${res.statusText || 'Upload processing error'}`);
                }

                if (!res.ok) {
                    throw new Error(data && data.detail ? data.detail : `Upload failed with status ${res.status}`);
                }

                stagedUploadRows = data.staged_rows || [];

                renderStagedRows(stagedUploadRows);
                renderErrorRows(data.error_rows || []);
                document.getElementById("stagedContainer").style.display = "block";
                showToast(`Staged ${data.valid_count || 0} valid row(s). Found ${data.error_count || 0} error(s).`, "success");
            } catch (err) {
                showToast("Import error: " + err.message, "danger");
                console.error("Import file error:", err);
            } finally {
                e.target.value = "";
            }
        }

        function renderStagedRows(rows) {
            const stagedCountEl = document.getElementById("stagedCount");
            const totalBadgeEl = document.getElementById("totalStagedBadge");
            if (stagedCountEl) stagedCountEl.innerText = rows.length;
            if (totalBadgeEl) totalBadgeEl.innerText = rows.length;

            const tbody = document.querySelector("#tableStaged tbody");
            tbody.innerHTML = "";

            if (rows.length === 0) {
                tbody.innerHTML = `<tr><td colspan="14" style="text-align:center; padding:24px; color:#94A3B8;">No staged rows remain.</td></tr>`;
                updateStagedSelectionCount();
                return;
            }

            rows.forEach((r, idx) => {
                const tr = document.createElement("tr");
                const formatStagedCell = (stg) => {
                    if (!stg) return "-";
                    const isOpt = Boolean(stg.opt_out !== undefined ? stg.opt_out : stg.opted_out);
                    const d = stg.date || "-";
                    if (isOpt) {
                        return `<span style="text-decoration:line-through; color:var(--text-muted);">${escapeHtml(d)}</span> <span class="badge badge-optout" style="font-size:10px; margin-left:4px;">Opt-out</span>`;
                    }
                    return escapeHtml(d);
                };
                const sInit = formatStagedCell(r.stages ? (r.stages.initial || r.stages.INITIAL) : null);
                const sQ1 = formatStagedCell(r.stages ? (r.stages.q1 || r.stages.Q1) : null);
                const sQ2 = formatStagedCell(r.stages ? (r.stages.q2 || r.stages.Q2) : null);
                const sQ3 = formatStagedCell(r.stages ? (r.stages.q3 || r.stages.Q3) : null);
                const sQ4 = formatStagedCell(r.stages ? (r.stages.q4 || r.stages.Q4) : null);
                const sExit = formatStagedCell(r.stages ? (r.stages.exit || r.stages.EXIT) : null);

                tr.innerHTML = `
                    <td><input type="checkbox" class="staged-row-check" data-id="${r.trainee_id}" onchange="updateStagedSelectionCount()"></td>
                    <td><strong>${escapeHtml(r.trainee_id)}</strong></td>
                    <td>${escapeHtml(r.trainee_name)}</td>
                    <td><strong>${r.date_of_joining || '-'}</strong></td>
                    <td>${r.last_working_date || '-'}</td>
                    <td><span class="badge badge-scheduled">${r.status || 'Active'}</span></td>
                    <td>${r.is_existing ? '<span class="badge badge-custom">Update</span>' : '<span class="badge badge-active">New</span>'}</td>
                    <td>${sInit}</td>
                    <td>${sQ1}</td>
                    <td>${sQ2}</td>
                    <td>${sQ3}</td>
                    <td>${sQ4}</td>
                    <td>${sExit}</td>
                    <td style="text-align:center;">
                        <button type="button" class="btn btn-secondary btn-sm" onclick="openEditStagedModal(${idx})" title="Edit DOJ, LWD or Milestone dates for this employee">
                            ✏️ Edit Dates
                        </button>
                    </td>
                `;
                tbody.appendChild(tr);
            });

            updateStagedSelectionCount();
        }

        function updateStagedSelectionCount() {
            const checked = document.querySelectorAll(".staged-row-check:checked");
            const count = checked.length;
            const badge = document.getElementById("selectedStagedBadge");
            if (badge) badge.innerText = count;

            const btnCommitSel = document.getElementById("btnCommitSelected");
            if (btnCommitSel) {
                if (count > 0) {
                    btnCommitSel.removeAttribute("disabled");
                    btnCommitSel.style.opacity = "1";
                } else {
                    btnCommitSel.setAttribute("disabled", "true");
                    btnCommitSel.style.opacity = "0.6";
                }
            }

            const checkAll = document.getElementById("checkAllStaged");
            const allChecks = document.querySelectorAll(".staged-row-check");
            if (checkAll && allChecks.length > 0) {
                checkAll.checked = (checked.length === allChecks.length);
                checkAll.indeterminate = (checked.length > 0 && checked.length < allChecks.length);
            }
        }

        function openEditStagedModal(idx) {
            currentEditingStagedIndex = idx;
            const r = stagedUploadRows[idx];
            if (!r) return;

            document.getElementById("stagedModalTraineeId").value = r.trainee_id || "";
            document.getElementById("stagedModalTraineeName").value = r.trainee_name || "";
            document.getElementById("stagedModalDoj").value = uiDateToIso(r.date_of_joining);
            document.getElementById("stagedModalLwd").value = uiDateToIso(r.last_working_date);

            const stages = ["initial", "q1", "q2", "q3", "q4", "exit"];
            stages.forEach(stg => {
                const sInfo = (r.stages && (r.stages[stg] || r.stages[stg.toUpperCase()])) ? (r.stages[stg] || r.stages[stg.toUpperCase()]) : {};
                const dtEl = document.getElementById(`staged_dt_${stg}`);
                const optEl = document.getElementById(`staged_opt_${stg}`);
                if (dtEl) dtEl.value = uiDateToIso(sInfo.date || "");
                if (optEl) optEl.checked = Boolean(sInfo.opt_out !== undefined ? sInfo.opt_out : sInfo.opted_out);
            });

            document.getElementById("modalEditStaged").classList.add("open");
        }

        function recalcStagedDatesFromDoj() {
            const dojVal = document.getElementById("stagedModalDoj").value;
            if (!dojVal) {
                showToast("Please specify a Date of Joining (DOJ) first.", "warning");
                return;
            }

            const doj = new Date(dojVal + "T00:00:00");
            if (isNaN(doj)) {
                showToast("Invalid Date of Joining.", "warning");
                return;
            }

            // Auto LWD: +12 calendar months
            const lwd = new Date(doj);
            lwd.setFullYear(lwd.getFullYear() + 1);
            document.getElementById("stagedModalLwd").value = lwd.toISOString().split("T")[0];

            // Initial: DOJ + 15 days
            const initDate = new Date(doj);
            initDate.setDate(initDate.getDate() + 15);
            const q1Date = addMonthsClamped(doj, 3);
            const q2Date = addMonthsClamped(doj, 6);
            const q3Date = addMonthsClamped(doj, 9);
            const q4Date = addMonthsClamped(doj, 12);
            const exitDate = addMonthsClamped(lwd, 3);

            document.getElementById("staged_dt_initial").value = adjustWeekend(initDate).toISOString().split("T")[0];
            document.getElementById("staged_dt_q1").value = adjustWeekend(q1Date).toISOString().split("T")[0];
            document.getElementById("staged_dt_q2").value = adjustWeekend(q2Date).toISOString().split("T")[0];
            document.getElementById("staged_dt_q3").value = adjustWeekend(q3Date).toISOString().split("T")[0];
            document.getElementById("staged_dt_q4").value = adjustWeekend(q4Date).toISOString().split("T")[0];
            document.getElementById("staged_dt_exit").value = adjustWeekend(exitDate).toISOString().split("T")[0];

            showToast("Recalculated all 6 stages from DOJ with weekend-to-Monday shift.", "info");
        }

        function handleSaveStagedModal(e) {
            e.preventDefault();
            if (currentEditingStagedIndex === null || !stagedUploadRows[currentEditingStagedIndex]) return;

            const r = stagedUploadRows[currentEditingStagedIndex];
            const dojIso = document.getElementById("stagedModalDoj").value;
            const lwdIso = document.getElementById("stagedModalLwd").value;

            if (!dojIso) {
                showToast("Date of Joining is required.", "warning");
                return;
            }

            r.date_of_joining = isoDateToUi(dojIso);
            r.last_working_date = isoDateToUi(lwdIso);

            if (!r.stages) r.stages = {};
            const stages = ["initial", "q1", "q2", "q3", "q4", "exit"];
            stages.forEach(stg => {
                const dtVal = document.getElementById(`staged_dt_${stg}`).value;
                const optVal = document.getElementById(`staged_opt_${stg}`).checked;
                r.stages[stg] = {
                    date: isoDateToUi(dtVal),
                    opt_out: optVal,
                    opted_out: optVal
                };
            });

            closeModal("modalEditStaged");
            renderStagedRows(stagedUploadRows);
            showToast(`Updated dates and preferences for apprentice '${r.trainee_id}' in staging table.`, "success");
        }

        function renderErrorRows(errors) {
            const container = document.getElementById("importErrorsContainer");
            const tbody = document.querySelector("#tableImportErrors tbody");
            tbody.innerHTML = "";

            if (!errors || errors.length === 0) {
                container.style.display = "none";
                return;
            }

            container.style.display = "block";
            document.getElementById("errorCount").innerText = errors.length;

            errors.forEach(err => {
                const tr = document.createElement("tr");
                const errList = err.errors.map(e => `<strong>${e.field || 'General'}:</strong> ${e.reason || e}`).join("<br>");
                tr.innerHTML = `
                    <td>Row ${err.row_number}</td>
                    <td><strong>${escapeHtml(err.trainee_id)}</strong></td>
                    <td>${escapeHtml(err.trainee_name)}</td>
                    <td style="color:var(--danger);">${errList}</td>
                `;
                tbody.appendChild(tr);
            });
        }

        function toggleSelectAllStaged(masterCheckbox) {
            document.querySelectorAll(".staged-row-check").forEach(cb => cb.checked = masterCheckbox.checked);
            updateStagedSelectionCount();
        }

        function deleteSelectedStagedRows() {
            const checked = Array.from(document.querySelectorAll(".staged-row-check:checked")).map(cb => cb.getAttribute("data-id"));
            if (checked.length === 0) {
                showToast("Select at least one staged row to remove.", "warning");
                return;
            }
            if (!confirm(`Remove ${checked.length} selected row(s) from staged import?`)) return;
            stagedUploadRows = stagedUploadRows.filter(r => !checked.includes(r.trainee_id));
            renderStagedRows(stagedUploadRows);
            if (stagedUploadRows.length === 0) {
                document.getElementById("stagedContainer").style.display = "none";
            }
            showToast(`Removed ${checked.length} row(s) from staged import.`, "info");
        }

        async function commitStagedRows(selectedOnly = false) {
            if (stagedUploadRows.length === 0) {
                showToast("No staged records available to commit.", "warning");
                return;
            }

            let rowsToCommit = [];
            let traineeIds = [];

            if (selectedOnly) {
                const checkedBoxes = Array.from(document.querySelectorAll(".staged-row-check:checked"));
                traineeIds = checkedBoxes.map(cb => cb.getAttribute("data-id"));
                if (traineeIds.length === 0) {
                    showToast("Please select at least one employee checkbox to save.", "warning");
                    return;
                }
                rowsToCommit = stagedUploadRows.filter(r => traineeIds.includes(r.trainee_id));
                if (!confirm(`Save ${rowsToCommit.length} selected employee(s) to persistent database?`)) return;
            } else {
                rowsToCommit = stagedUploadRows;
                traineeIds = stagedUploadRows.map(r => r.trainee_id);
                if (!confirm(`Save all ${rowsToCommit.length} employee(s) in staging to persistent database?`)) return;
            }

            try {
                showToast(`Committing ${rowsToCommit.length} apprentice record(s)...`, "info");
                const res = await apiFetch("/api/import/commit", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        trainee_ids_to_commit: traineeIds,
                        staged_rows: rowsToCommit
                    })
                });

                const data = await res.json();
                if (!res.ok) throw new Error(data.detail || "Commit failed");

                showToast(data.message || `Saved ${rowsToCommit.length} employee(s) successfully!`, "success");

                // Remove committed rows from staged rows
                stagedUploadRows = stagedUploadRows.filter(r => !traineeIds.includes(r.trainee_id));

                if (stagedUploadRows.length > 0) {
                    renderStagedRows(stagedUploadRows);
                    showToast(`${stagedUploadRows.length} remaining apprentice(s) left in staging.`, "info");
                } else {
                    document.getElementById("stagedContainer").style.display = "none";
                    switchView("directory");
                }
                loadDashboardStats();
            } catch (err) {
                showToast("Commit error: " + err.message, "danger");
            }
        }

        // EXPORT DATA
        function exportData(fmt) {
            window.location.href = `/api/export/directory?format=${fmt}`;
        }

        // EXCEPTIONS LOADER
        async function loadExceptions() {
            const tbody = document.querySelector("#tableExceptions tbody");
            tbody.innerHTML = `<tr><td colspan="9" style="text-align:center; padding:20px; color:#94A3B8;">Loading exceptions...</td></tr>`;

            try {
                const res = await apiFetch("/api/exceptions");
                const data = await res.json();
                tbody.innerHTML = "";

                if (!data.exceptions || data.exceptions.length === 0) {
                    tbody.innerHTML = `<tr><td colspan="9" style="text-align:center; padding:20px; color:var(--success);">No delivery exceptions or uncertain dispatches in database.</td></tr>`;
                    return;
                }

                data.exceptions.forEach(ex => {
                    const tr = document.createElement("tr");
                    tr.innerHTML = `
                        <td>#${ex.id}</td>
                        <td><strong>${ex.trainee_id}</strong></td>
                        <td>${ex.trainee_name}</td>
                        <td>${formatStageLabel(ex.stage)}</td>
                        <td>${ex.scheduled_date}</td>
                        <td><span class="badge badge-cancelled">${ex.status}</span></td>
                        <td>${ex.attempt_count}</td>
                        <td style="color:var(--danger); font-size:12px;">${ex.last_error || 'Timeout during transmission'}</td>
                        <td>
                            <button class="btn btn-primary btn-sm" onclick="openResolveModal(${ex.id})">Resolve</button>
                        </td>
                    `;
                    tbody.appendChild(tr);
                });
            } catch (e) {
                tbody.innerHTML = `<tr><td colspan="9" style="text-align:center; padding:20px; color:var(--danger);">Failed to load exceptions: ${e.message}</td></tr>`;
            }
        }

        function openResolveModal(scheduleId) {
            document.getElementById("resolveScheduleId").value = scheduleId;
            document.getElementById("resolveReason").value = "";
            document.getElementById("modalResolveException").classList.add("open");
        }

        async function handleResolveExceptionSubmit(e) {
            e.preventDefault();
            const sid = document.getElementById("resolveScheduleId").value;
            const act = document.getElementById("resolveAction").value;
            const rsn = document.getElementById("resolveReason").value.trim();

            try {
                const res = await apiFetch("/api/exceptions/resolve", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        schedule_id: parseInt(sid),
                        action: act,
                        reason: rsn
                    })
                });

                if (!res.ok) {
                    const err = await res.json();
                    throw new Error(err.detail);
                }

                closeModal("modalResolveException");
                showToast(`Schedule #${sid} resolved as ${act}.`, "success");
                loadExceptions();
                loadDashboardStats();
            } catch (err) {
                showToast("Resolution error: " + err.message, "danger");
            }
        }

        // AUDIT TRAIL LOADER
        async function loadAuditLogs() {
            const tbody = document.querySelector("#tableAudit tbody");
            tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding:20px; color:#94A3B8;">Loading audit trail...</td></tr>`;

            try {
                const res = await apiFetch("/api/audit-logs");
                const data = await res.json();
                tbody.innerHTML = "";

                if (!data.logs || data.logs.length === 0) {
                    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding:20px; color:#94A3B8;">No audit logs recorded yet.</td></tr>`;
                    return;
                }

                data.logs.forEach(l => {
                    const tr = document.createElement("tr");
                    tr.innerHTML = `
                        <td>#${l.id}</td>
                        <td>${l.timestamp}</td>
                        <td><strong>${l.actor}</strong></td>
                        <td><span class="badge badge-scheduled">${l.action}</span></td>
                        <td>${l.entity_type}</td>
                        <td>${l.entity_id}</td>
                        <td style="font-size:12px; color:#475569;">${l.reason || '-'}</td>
                    `;
                    tbody.appendChild(tr);
                });
            } catch (e) {
                tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding:20px; color:var(--danger);">Failed to load audit logs: ${e.message}</td></tr>`;
            }
        }

        // PRUNE TEST DATA
        async function pruneTestData() {
            if (!confirm("Are you sure you want to prune all unsent trainees? Trainees with Sent email history will be preserved.")) return;

            try {
                const res = await apiFetch("/api/database/prune", { method: "POST" });
                const data = await res.json();
                showToast(data.message, "success");
                loadDashboardStats();
            } catch (e) {
                showToast("Pruning failed: " + e.message, "danger");
            }
        }
    </script>
</body>
</html>
"""
