import React, { useState, useEffect, useRef } from 'react';
import { 
  Cpu, 
  Briefcase, 
  BookOpen, 
  Share2, 
  Mail, 
  HelpCircle, 
  LogOut, 
  Lock, 
  Terminal,
  Activity
} from 'lucide-react';

// Components
import Overview from './components/Overview';
import CareerIntel from './components/CareerIntel';
import KnowledgeBase from './components/KnowledgeBase';
import Presence from './components/Presence';
import Communication from './components/Communication';
import InterviewPrep from './components/InterviewPrep';

export default function App() {
  const [token, setToken] = useState(localStorage.getItem('paios_token') || '');
  const [activeTab, setActiveTab] = useState('overview');
  
  // Auth details
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loginError, setLoginError] = useState('');
  const [currentUser, setCurrentUser] = useState(null);

  // Live Metrics & WS state
  const [metrics, setMetrics] = useState(null);
  const [agentsData, setAgentsData] = useState(null);
  const [eventLogs, setEventLogs] = useState([]);
  const [wsStatus, setWsStatus] = useState('offline');
  const [triggeringAgents, setTriggeringAgents] = useState({});

  const wsRef = useRef(null);

  // Dynamically determine host endpoints
  const protocol = window.location.protocol;
  const hostname = window.location.hostname;
  const isDev = window.location.port !== '8000'; // If served by Vite dev server
  const apiHost = isDev ? `${hostname}:8000` : window.location.host;
  
  const apiPrefix = `${protocol}//${apiHost}/api/v1`;
  const wsPrefix = `${protocol === 'https:' ? 'wss:' : 'ws:'}//${apiHost}`;

  // Run initial loading and set intervals when authenticated
  useEffect(() => {
    if (!token) return;

    // Load initial user details
    fetchCurrentUser();

    // Fetch metrics and statuses immediately
    fetchSystemInfo();

    // Connect WebSocket
    connectWebSocket();

    // Set polling intervals
    const interval = setInterval(fetchSystemInfo, 5000);

    return () => {
      clearInterval(interval);
      if (wsRef.current) wsRef.current.close();
    };
  }, [token]);

  const fetchCurrentUser = async () => {
    try {
      const response = await fetch(`${apiPrefix}/profile/me`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.status === 401) {
        handleLogout();
        return;
      }
      if (response.ok) {
        const data = await response.json();
        setCurrentUser(data);
      }
    } catch (err) {
      console.error("Failed to load profile details", err);
    }
  };

  const fetchSystemInfo = async () => {
    try {
      const headers = { 'Authorization': `Bearer ${token}` };
      
      // Fetch system resources metrics
      const metricsRes = await fetch(`${apiPrefix}/dashboard/metrics`, { headers });
      if (metricsRes.ok) {
        const mData = await metricsRes.json();
        setMetrics(mData);
      }

      // Fetch AI agents active state statuses
      const agentsRes = await fetch(`${apiPrefix}/agents/status`, { headers });
      if (agentsRes.ok) {
        const aData = await agentsRes.json();
        setAgentsData(aData);
      }
    } catch (err) {
      console.error("Failed to sync system info", err);
    }
  };

  const connectWebSocket = () => {
    try {
      if (wsRef.current) wsRef.current.close();

      const socket = new WebSocket(`${wsPrefix}/ws/agents`);
      wsRef.current = socket;

      socket.onopen = () => {
        setWsStatus('online');
      };

      socket.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          // Add to log stream
          setEventLogs(prev => [message, ...prev].slice(0, 50));
          
          // Trigger a quick status update if agent state changed
          fetchSystemInfo();
        } catch (e) {
          console.error("Failed parsing event payload", e);
        }
      };

      socket.onclose = () => {
        setWsStatus('offline');
        // Reconnect after 3 seconds
        setTimeout(connectWebSocket, 3000);
      };
    } catch (err) {
      console.error("WS connection error", err);
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoginError('');

    try {
      const response = await fetch(`${apiPrefix}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });

      if (response.ok) {
        const data = await response.json();
        localStorage.setItem('paios_token', data.access_token);
        setToken(data.access_token);
      } else {
        setLoginError('Invalid username or system password.');
      }
    } catch (err) {
      setLoginError('Connection refused. Is the FastAPI service online?');
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('paios_token');
    setToken('');
    setCurrentUser(null);
    if (wsRef.current) wsRef.current.close();
  };

  const handleTriggerAgent = async (agentName) => {
    setTriggeringAgents(prev => ({ ...prev, [agentName]: true }));
    try {
      const response = await fetch(`${apiPrefix}/agents/execute`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ agent_name: agentName, context: {} })
      });
      const data = await response.json();
      console.log(`${agentName} execution trigger response:`, data);
    } catch (err) {
      console.error(err);
    } finally {
      setTriggeringAgents(prev => ({ ...prev, [agentName]: false }));
      fetchSystemInfo();
    }
  };

  // Render Login overlay if unauthenticated
  if (!token) {
    return (
      <div className="login-overlay">
        <div className="login-card">
          <div className="logo-section" style={{ justifyContent: 'center', marginBottom: '1.5rem' }}>
            <div className="logo-icon">&alpha;</div>
            <div className="logo-title" style={{ fontSize: '1.6rem' }}>PAIOS System</div>
          </div>
          
          <h2 style={{ fontSize: '1.15rem', color: 'white', marginBottom: '1.5rem', fontWeight: 600 }}>Authenticate Access Control</h2>
          
          {loginError && (
            <div style={{ 
              background: 'rgba(239,68,68,0.05)', 
              color: '#ef4444', 
              border: '1px solid rgba(239,68,68,0.15)', 
              padding: '0.75rem', 
              borderRadius: '8px', 
              fontSize: '0.85rem', 
              marginBottom: '1.25rem' 
            }}>
              {loginError}
            </div>
          )}

          <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem', textAlign: 'left' }}>
            <div className="form-group">
              <label>System Email Address</label>
              <input 
                type="email" 
                className="input-control" 
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="admin@paios.local"
                required
              />
            </div>
            
            <div className="form-group" style={{ marginBottom: '1.75rem' }}>
              <label>Security Keyphrase</label>
              <input 
                type="password" 
                className="input-control" 
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
              />
            </div>

            <button type="submit" className="btn btn-primary" style={{ width: '100%' }}>
              <Lock size={16} />
              <span>Unlock System Console</span>
            </button>
          </form>
        </div>
      </div>
    );
  }

  // Render Layout Frame
  return (
    <div className="app-container">
      {/* Side Navigation Panel */}
      <aside className="sidebar">
        <div className="logo-section">
          <div className="logo-icon">&alpha;</div>
          <div className="logo-title">PAIOS Control</div>
        </div>

        <nav className="nav-links">
          <button 
            className={`nav-item ${activeTab === 'overview' ? 'active' : ''}`}
            onClick={() => setActiveTab('overview')}
          >
            <Cpu size={18} />
            <span>Overview Dashboard</span>
          </button>

          <button 
            className={`nav-item ${activeTab === 'career' ? 'active' : ''}`}
            onClick={() => setActiveTab('career')}
          >
            <Briefcase size={18} />
            <span>Career Intelligence</span>
          </button>

          <button 
            className={`nav-item ${activeTab === 'knowledge' ? 'active' : ''}`}
            onClick={() => setActiveTab('knowledge')}
          >
            <BookOpen size={18} />
            <span>Knowledge Base</span>
          </button>

          <button 
            className={`nav-item ${activeTab === 'presence' ? 'active' : ''}`}
            onClick={() => setActiveTab('presence')}
          >
            <Share2 size={18} />
            <span>Presence Manager</span>
          </button>

          <button 
            className={`nav-item ${activeTab === 'communication' ? 'active' : ''}`}
            onClick={() => setActiveTab('communication')}
          >
            <Mail size={18} />
            <span>Inbox & Holds</span>
          </button>

          <button 
            className={`nav-item ${activeTab === 'interview' ? 'active' : ''}`}
            onClick={() => setActiveTab('interview')}
          >
            <HelpCircle size={18} />
            <span>Interview Simulator</span>
          </button>
        </nav>

        <div className="sidebar-footer">
          <div className="user-info-bar">
            <div className="user-details">
              <span className="user-name">{currentUser?.full_name || 'System Operator'}</span>
              <span className="user-role" style={{ color: wsStatus === 'online' ? '#10b981' : '#ef4444' }}>
                WS {wsStatus}
              </span>
            </div>
            <button className="btn btn-outline" style={{ padding: '0.4rem', borderRadius: '6px' }} onClick={handleLogout} title="Log Out">
              <LogOut size={16} />
            </button>
          </div>
        </div>
      </aside>

      {/* Main Panel Content Routing */}
      <main className="main-content">
        {activeTab === 'overview' && (
          <Overview 
            metrics={metrics} 
            agentsData={agentsData} 
            eventLogs={eventLogs} 
            onTriggerAgent={handleTriggerAgent}
            triggeringAgents={triggeringAgents}
          />
        )}
        
        {activeTab === 'career' && (
          <CareerIntel 
            token={token}
            apiPrefix={apiPrefix}
          />
        )}

        {activeTab === 'knowledge' && (
          <KnowledgeBase 
            token={token}
            apiPrefix={apiPrefix}
          />
        )}

        {activeTab === 'presence' && (
          <Presence 
            token={token}
            apiPrefix={apiPrefix}
          />
        )}

        {activeTab === 'communication' && (
          <Communication 
            token={token}
            apiPrefix={apiPrefix}
          />
        )}

        {activeTab === 'interview' && (
          <InterviewPrep 
            token={token}
            apiPrefix={apiPrefix}
          />
        )}
      </main>
    </div>
  );
}
