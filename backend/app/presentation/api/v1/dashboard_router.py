"""Dashboard Router.

Serves the visual administration panel and provides the aggregated metrics endpoint.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse

from app.application.dependencies.auth import get_current_user
from app.application.dependencies.container import get_container

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("", response_class=HTMLResponse)
async def get_dashboard() -> str:
    """Render and serve the premium PAIOS administration dashboard."""
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PAIOS Admin Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-dark: #09090b;
            --bg-card: rgba(20, 20, 25, 0.7);
            --bg-glass: rgba(255, 255, 255, 0.03);
            --border-glass: rgba(255, 255, 255, 0.06);
            --text-main: #f4f4f5;
            --text-muted: #a1a1aa;
            --primary: #6366f1;
            --primary-glow: rgba(99, 102, 241, 0.15);
            --success: #10b981;
            --success-glow: rgba(16, 185, 129, 0.15);
            --warning: #f59e0b;
            --warning-glow: rgba(245, 158, 11, 0.15);
            --danger: #ef4444;
            --danger-glow: rgba(239, 68, 68, 0.15);
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: 'Outfit', sans-serif;
            background-color: var(--bg-dark);
            color: var(--text-main);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            overflow-x: hidden;
        }

        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 1.5rem 2rem;
            border-bottom: 1px solid var(--border-glass);
            background: rgba(9, 9, 11, 0.8);
            backdrop-filter: blur(12px);
            position: sticky;
            top: 0;
            z-index: 10;
        }

        .logo-section {
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }

        .logo-icon {
            width: 2.2rem;
            height: 2.2rem;
            background: linear-gradient(135deg, var(--primary), #a855f7);
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 800;
            font-size: 1.2rem;
            box-shadow: 0 0 20px var(--primary-glow);
        }

        .logo-title {
            font-size: 1.4rem;
            font-weight: 800;
            letter-spacing: -0.5px;
            background: linear-gradient(to right, #ffffff, var(--text-muted));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .header-actions {
            display: flex;
            align-items: center;
            gap: 1rem;
        }

        .btn {
            padding: 0.6rem 1.2rem;
            border-radius: 6px;
            font-family: inherit;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
            border: 1px solid transparent;
            font-size: 0.9rem;
        }

        .btn-primary {
            background-color: var(--primary);
            color: white;
            box-shadow: 0 4px 12px var(--primary-glow);
        }

        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 16px rgba(99, 102, 241, 0.3);
        }

        .btn-outline {
            background-color: transparent;
            border-color: var(--border-glass);
            color: var(--text-main);
        }

        .btn-outline:hover {
            background-color: rgba(255, 255, 255, 0.05);
        }

        main {
            flex: 1;
            padding: 2rem;
            max-width: 1400px;
            margin: 0 auto;
            width: 100%;
            display: grid;
            grid-template-columns: 1fr;
            gap: 2rem;
        }

        @media (min-width: 1024px) {
            main {
                grid-template-columns: 3fr 1fr;
            }
        }

        .grid-stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
            grid-column: 1 / -1;
        }

        .card-stat {
            background: var(--bg-card);
            border: 1px solid var(--border-glass);
            border-radius: 12px;
            padding: 1.5rem;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            position: relative;
            overflow: hidden;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        }

        .card-stat::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 4px;
            height: 100%;
            background: var(--primary);
        }

        .card-stat.stat-success::before { background: var(--success); }
        .card-stat.stat-warning::before { background: var(--warning); }
        .card-stat.stat-danger::before { background: var(--danger); }

        .stat-label {
            color: var(--text-muted);
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 0.5rem;
        }

        .stat-value {
            font-size: 2rem;
            font-weight: 800;
        }

        .stat-meta {
            font-size: 0.75rem;
            color: var(--text-muted);
            margin-top: 0.5rem;
        }

        .card-main {
            background: var(--bg-card);
            border: 1px solid var(--border-glass);
            border-radius: 16px;
            padding: 1.75rem;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
            backdrop-filter: blur(12px);
        }

        .card-title {
            font-size: 1.25rem;
            font-weight: 700;
            margin-bottom: 1.5rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        /* Agent list grid */
        .agent-grid {
            display: grid;
            grid-template-columns: 1fr;
            gap: 1.5rem;
        }

        @media (min-width: 768px) {
            .agent-grid {
                grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
            }
        }

        .agent-card {
            background: var(--bg-glass);
            border: 1px solid var(--border-glass);
            border-radius: 12px;
            padding: 1.25rem;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            transition: all 0.3s ease;
        }

        .agent-card:hover {
            transform: translateY(-4px);
            border-color: rgba(255, 255, 255, 0.15);
        }

        .agent-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
        }

        .agent-name {
            font-weight: 700;
            font-size: 1.1rem;
            color: #ffffff;
        }

        .agent-status-badge {
            font-size: 0.75rem;
            font-weight: 800;
            padding: 0.25rem 0.6rem;
            border-radius: 20px;
            text-transform: uppercase;
            display: flex;
            align-items: center;
            gap: 0.3rem;
        }

        .status-idle { background: var(--primary-glow); color: #818cf8; }
        .status-running { background: var(--success-glow); color: var(--success); animation: pulse 1.5s infinite; }
        .status-error { background: var(--danger-glow); color: var(--danger); }
        .status-paused { background: var(--warning-glow); color: var(--warning); }

        .agent-metrics-row {
            display: flex;
            justify-content: space-between;
            font-size: 0.85rem;
            color: var(--text-muted);
            margin-bottom: 0.4rem;
        }

        .agent-metrics-value {
            font-weight: 600;
            color: var(--text-main);
        }

        .agent-footer {
            margin-top: 1.25rem;
            padding-top: 1rem;
            border-top: 1px solid rgba(255, 255, 255, 0.05);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        /* Event stream logs */
        .event-stream {
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
            max-height: 400px;
            overflow-y: auto;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.8rem;
            padding-right: 0.5rem;
        }

        .event-item {
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid var(--border-glass);
            padding: 0.75rem;
            border-radius: 8px;
            display: flex;
            flex-direction: column;
            gap: 0.3rem;
            animation: slideIn 0.3s ease;
        }

        .event-meta-line {
            display: flex;
            justify-content: space-between;
            color: var(--text-muted);
            font-size: 0.75rem;
        }

        .event-type-badge {
            color: var(--primary);
            font-weight: 700;
        }

        .event-payload {
            color: #d1d5db;
            white-space: pre-wrap;
            word-break: break-all;
            background: rgba(0, 0, 0, 0.2);
            padding: 0.4rem;
            border-radius: 4px;
            margin-top: 0.25rem;
            font-size: 0.75rem;
        }

        /* Login Modal Overlays */
        .modal-overlay {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(9, 9, 11, 0.85);
            backdrop-filter: blur(8px);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 100;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.3s ease;
        }

        .modal-overlay.active {
            opacity: 1;
            pointer-events: all;
        }

        .modal-card {
            background: #18181b;
            border: 1px solid var(--border-glass);
            border-radius: 16px;
            width: 90%;
            max-width: 400px;
            padding: 2.25rem;
            box-shadow: 0 24px 48px rgba(0,0,0,0.5);
            transform: scale(0.95);
            transition: transform 0.3s ease;
        }

        .modal-overlay.active .modal-card {
            transform: scale(1);
        }

        .modal-title {
            font-size: 1.5rem;
            font-weight: 800;
            margin-bottom: 1.5rem;
            text-align: center;
        }

        .input-group {
            margin-bottom: 1.25rem;
            display: flex;
            flex-direction: column;
            gap: 0.4rem;
        }

        .input-group label {
            font-size: 0.85rem;
            font-weight: 600;
            color: var(--text-muted);
        }

        .input-control {
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid var(--border-glass);
            border-radius: 6px;
            padding: 0.75rem;
            font-family: inherit;
            color: white;
            font-size: 0.95rem;
            transition: border 0.2s ease;
        }

        .input-control:focus {
            outline: none;
            border-color: var(--primary);
        }

        .error-banner {
            background: var(--danger-glow);
            color: var(--danger);
            border: 1px solid rgba(239, 68, 68, 0.2);
            padding: 0.75rem;
            border-radius: 6px;
            margin-bottom: 1.25rem;
            font-size: 0.85rem;
            display: none;
        }

        /* Animations */
        @keyframes pulse {
            0% { opacity: 0.6; box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.4); }
            70% { opacity: 1; box-shadow: 0 0 0 8px rgba(16, 185, 129, 0); }
            100% { opacity: 0.6; box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
        }

        @keyframes slideIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        /* Custom Scrollbar */
        ::-webkit-scrollbar {
            width: 6px;
        }
        ::-webkit-scrollbar-track {
            background: transparent;
        }
        ::-webkit-scrollbar-thumb {
            background: rgba(255,255,255,0.1);
            border-radius: 3px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: rgba(255,255,255,0.2);
        }
    </style>
</head>
<body>
    <header>
        <div class="logo-section">
            <div class="logo-icon">&alpha;</div>
            <div class="logo-title">PAIOS Control Center</div>
        </div>
        <div class="header-actions">
            <span id="ws-status-badge" class="agent-status-badge status-paused" style="margin-right: 1rem;">WS Offline</span>
            <button id="btn-logout" class="btn btn-outline" style="display: none;">Logout</button>
        </div>
    </header>

    <main>
        <!-- Top Stats Row -->
        <div class="grid-stats">
            <div class="card-stat" id="stat-card-cpu">
                <div class="stat-label">CPU LOAD</div>
                <div class="stat-value" id="metrics-cpu">0.0%</div>
                <div class="stat-meta">Host Processor utilization</div>
            </div>
            <div class="card-stat" id="stat-card-memory">
                <div class="stat-label">MEMORY LOAD</div>
                <div class="stat-value" id="metrics-memory">0.0%</div>
                <div class="stat-meta">Host RAM allocation</div>
            </div>
            <div class="card-stat stat-success" id="stat-card-db">
                <div class="stat-label">DATABASE</div>
                <div class="stat-value" id="metrics-db-jobs">0</div>
                <div class="stat-meta" id="metrics-db-status">MongoDB Connected (0ms)</div>
            </div>
            <div class="card-stat stat-success" id="stat-card-websockets">
                <div class="stat-label">ACTIVE CLIENTS</div>
                <div class="stat-value" id="metrics-ws-connections">0</div>
                <div class="stat-meta">WebSocket client streams</div>
            </div>
        </div>

        <!-- Left Column: Agent Grid -->
        <section class="card-main">
            <div class="card-title">
                <span>AI Service Agents</span>
                <span id="agents-summary" style="font-size: 0.85rem; font-weight: normal; color: var(--text-muted);">0 / 0 Healthy</span>
            </div>
            <div class="agent-grid" id="agent-grid-container">
                <!-- Agent cards dynamically injected here -->
            </div>
        </section>

        <!-- Right Column: Live Event Stream -->
        <section class="card-main" style="display: flex; flex-direction: column; justify-content: space-between;">
            <div>
                <div class="card-title">Live Message Stream</div>
                <div class="event-stream" id="event-stream-container">
                    <!-- Events dynamically injected here -->
                </div>
            </div>
        </section>
    </main>

    <!-- Glassmorphic Login Overlay -->
    <div class="modal-overlay" id="login-overlay">
        <div class="modal-card">
            <div class="modal-title">Authenticate PAIOS</div>
            <div class="error-banner" id="login-error-banner">Invalid credentials. Please try again.</div>
            <form id="login-form">
                <div class="input-group">
                    <label for="login-email">Email Address</label>
                    <input type="email" id="login-email" class="input-control" required placeholder="name@domain.com">
                </div>
                <div class="input-group" style="margin-bottom: 2rem;">
                    <label for="login-password">System Password</label>
                    <input type="password" id="login-password" class="input-control" required placeholder="••••••••">
                </div>
                <button type="submit" class="btn btn-primary" style="width: 100%; padding: 0.8rem;" id="btn-submit-login">Enter Dashboard</button>
            </form>
        </div>
    </div>

    <script>
        const API_PREFIX = '/api/v1';
        let ws = null;

        // Dom Elements
        const loginOverlay = document.getElementById('login-overlay');
        const loginForm = document.getElementById('login-form');
        const loginErrorBanner = document.getElementById('login-error-banner');
        const btnLogout = document.getElementById('btn-logout');
        const wsStatusBadge = document.getElementById('ws-status-badge');
        const agentGrid = document.getElementById('agent-grid-container');
        const eventStream = document.getElementById('event-stream-container');
        const agentsSummary = document.getElementById('agents-summary');

        // Check authentication
        function getToken() {
            return localStorage.getItem('paios_token');
        }

        function setToken(token) {
            localStorage.setItem('paios_token', token);
        }

        function clearToken() {
            localStorage.removeItem('paios_token');
        }

        // Show/Hide overlays
        function showLogin() {
            loginOverlay.classList.add('active');
            btnLogout.style.display = 'none';
        }

        function hideLogin() {
            loginOverlay.classList.remove('active');
            btnLogout.style.display = 'block';
        }

        // Handle Logout
        btnLogout.addEventListener('click', () => {
            clearToken();
            if (ws) ws.close();
            showLogin();
        });

        // Handle Login Submission
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const email = document.getElementById('login-email').value;
            const password = document.getElementById('login-password').value;
            loginErrorBanner.style.display = 'none';

            try {
                const response = await fetch(`${API_PREFIX}/auth/login`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, password })
                });

                if (response.ok) {
                    const data = await response.json();
                    setToken(data.access_token);
                    hideLogin();
                    initDashboard();
                } else {
                    loginErrorBanner.style.display = 'block';
                }
            } catch (err) {
                console.error("Login request failed", err);
                loginErrorBanner.innerText = "Connection failed. Is the server running?";
                loginErrorBanner.style.display = 'block';
            }
        });

        // Initialize dashboard operations
        async function initDashboard() {
            await fetchAgentStatus();
            await fetchSystemMetrics();
            connectWebSocket();
            // Start metrics polling interval
            setInterval(fetchSystemMetrics, 5000);
        }

        // Fetch Agent Grid
        async function fetchAgentStatus() {
            const token = getToken();
            if (!token) return showLogin();

            try {
                const response = await fetch(`${API_PREFIX}/agents/status`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });

                if (response.status === 401) {
                    clearToken();
                    return showLogin();
                }

                if (response.ok) {
                    const statusData = await response.json();
                    renderAgentGrid(statusData.agents);
                    updateAgentsSummary(statusData);
                }
            } catch (err) {
                console.error("Failed to load agent statuses", err);
            }
        }

        // Fetch Metrics Stats
        async function fetchSystemMetrics() {
            const token = getToken();
            if (!token) return;

            try {
                const response = await fetch(`${API_PREFIX}/dashboard/metrics`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });

                if (response.ok) {
                    const metrics = await response.json();
                    document.getElementById('metrics-cpu').innerText = `${metrics.resources.cpu_percent}%`;
                    document.getElementById('metrics-memory').innerText = `${metrics.resources.memory_percent}%`;
                    document.getElementById('metrics-db-jobs').innerText = metrics.database.collections.jobs;
                    document.getElementById('metrics-ws-connections').innerText = metrics.websockets.active_connections;
                    document.getElementById('metrics-db-status').innerText = `MongoDB Connected (${metrics.database.latency_ms}ms)`;
                }
            } catch (err) {
                console.error("Failed to fetch system metrics", err);
            }
        }

        // Execute Agent API
        async function triggerAgent(agentName) {
            const token = getToken();
            if (!token) return showLogin();

            // Find execute button and disable it
            const btn = document.getElementById(`btn-execute-${agentName}`);
            if (btn) {
                btn.disabled = true;
                btn.innerText = "Triggering...";
            }

            try {
                const response = await fetch(`${API_PREFIX}/agents/execute`, {
                    method: 'POST',
                    headers: { 
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    },
                    body: JSON.stringify({ agent_name: agentName, context: {} })
                });
                const res = await response.json();
                console.log(`Agent triggered result:`, res);
            } catch (err) {
                console.error(`Failed to trigger agent ${agentName}`, err);
            } finally {
                if (btn) {
                    btn.disabled = false;
                    btn.innerText = "Execute";
                }
                fetchAgentStatus();
            }
        }

        // Render Agent Cards
        function renderAgentGrid(agents) {
            agentGrid.innerHTML = '';
            for (const [name, state] of Object.entries(agents)) {
                const consecutiveErrors = state.error_count;
                const statusClass = `status-${state.status}`;
                const card = document.createElement('div');
                card.className = 'agent-card';
                card.innerHTML = `
                    <div>
                        <div class="agent-header">
                            <span class="agent-name">${name}</span>
                            <span class="agent-status-badge ${statusClass}" id="status-${name}">${state.status}</span>
                        </div>
                        <div class="agent-metrics-row">
                            <span>Uptime</span>
                            <span class="agent-metrics-value">${Math.round(state.uptime_seconds / 60)}m</span>
                        </div>
                        <div class="agent-metrics-row">
                            <span>Avg Duration</span>
                            <span class="agent-metrics-value">${state.last_execution ? 'Not set' : '0.0s'}</span>
                        </div>
                        <div class="agent-metrics-row">
                            <span>Success Count</span>
                            <span class="agent-metrics-value">${state.error_count === 0 && state.last_execution ? 1 : 0}</span>
                        </div>
                        <div class="agent-metrics-row">
                            <span>Failures</span>
                            <span class="agent-metrics-value">${state.error_count}</span>
                        </div>
                        ${state.message && state.message !== 'OK' ? `
                        <div style="font-size:0.75rem; color:var(--danger); margin-top:0.5rem; background:rgba(239, 68, 68, 0.05); padding:0.4rem; border-radius:4px; border:1px solid rgba(239, 68, 68, 0.1);">
                            ${state.message}
                        </div>
                        ` : ''}
                    </div>
                    <div class="agent-footer">
                        <button id="btn-execute-${name}" class="btn btn-primary" onclick="triggerAgent('${name}')" style="padding: 0.4rem 0.8rem; font-size: 0.8rem;">Execute</button>
                    </div>
                `;
                agentGrid.appendChild(card);
            }
        }

        function updateAgentsSummary(statusData) {
            agentsSummary.innerText = `${statusData.agents_healthy} / ${statusData.agents_total} Healthy`;
        }

        // Log events
        function addEventLog(event) {
            const item = document.createElement('div');
            item.className = 'event-item';
            
            const timestamp = new Date(event.timestamp).toLocaleTimeString();
            const source = event.source_agent || 'unknown';
            const type = event.event_type;
            const corrId = event.correlation_id ? event.correlation_id.substring(0, 8) : 'N/A';
            const payloadStr = JSON.stringify(event.payload, null, 2);

            item.innerHTML = `
                <div class="event-meta-line">
                    <span>[${timestamp}] <strong style="color:#ffffff;">${source}</strong></span>
                    <span>CorrID: ${corrId}</span>
                </div>
                <div><span class="event-type-badge">${type}</span></div>
                <pre class="event-payload">${payloadStr}</pre>
            `;

            eventStream.insertBefore(item, eventStream.firstChild);
            
            // Limit log entries to 50
            if (eventStream.children.length > 50) {
                eventStream.removeChild(eventStream.lastChild);
            }
        }

        // Websocket connection loop
        function connectWebSocket() {
            const loc = window.location;
            const wsProto = loc.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${wsProto}//${loc.host}/ws/agents`;
            
            ws = new WebSocket(wsUrl);

            ws.onopen = () => {
                wsStatusBadge.innerText = 'WS Connected';
                wsStatusBadge.className = 'agent-status-badge status-running';
            };

            ws.onmessage = (e) => {
                try {
                    const event = JSON.parse(e.data);
                    if (event.event_type === 'INITIAL_STATUS') {
                        renderAgentGrid(event.payload.agents);
                        updateAgentsSummary(event.payload);
                    } else {
                        addEventLog(event);
                        // Refresh grid on lifecycle updates
                        if (event.event_type.startsWith('AGENT_') || event.event_type.startsWith('SYSTEM_')) {
                            fetchAgentStatus();
                        }
                    }
                } catch (err) {
                    console.error("Failed to parse WebSocket message", err);
                }
            };

            ws.onclose = () => {
                wsStatusBadge.innerText = 'WS Offline';
                wsStatusBadge.className = 'agent-status-badge status-paused';
                // Attempt reconnect in 3s
                setTimeout(connectWebSocket, 3000);
            };

            ws.onerror = (err) => {
                console.error("WebSocket encountered error", err);
                ws.close();
            };
        }

        // Document Boot
        document.addEventListener('DOMContentLoaded', () => {
            const token = getToken();
            if (token) {
                hideLogin();
                initDashboard();
            } else {
                showLogin();
            }
        });
    </script>
</body>
</html>
"""


@router.get("/metrics")
async def get_metrics(
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict:
    """Fetch the real-time systems resource and storage utilization statistics."""
    container = get_container()
    return await container.metrics_service.get_system_metrics()
