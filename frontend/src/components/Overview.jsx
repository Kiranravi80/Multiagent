import React, { useState } from 'react';
import { Cpu, Database, Activity, Play, CheckCircle, AlertTriangle, Terminal } from 'lucide-react';

export default function Overview({ 
  metrics, 
  agentsData, 
  eventLogs, 
  onTriggerAgent, 
  triggeringAgents 
}) {
  const getStatusBadgeClass = (status) => {
    switch (status) {
      case 'running': return 'badge badge-running';
      case 'error': return 'badge badge-error';
      case 'paused': return 'badge badge-warning';
      default: return 'badge badge-idle';
    }
  };

  return (
    <div>
      <div className="section-header">
        <h1 className="section-title">PAIOS Control Center</h1>
        <span className="badge badge-running">System Live</span>
      </div>

      {/* Top Resource Stats */}
      <div className="stats-container">
        <div className="stat-card">
          <div className="stat-title">CPU Load</div>
          <div className="stat-num">{metrics?.resources?.cpu_percent?.toFixed(1) || '0.0'}%</div>
          <div className="stat-desc">Host utilization rate</div>
        </div>

        <div className="stat-card">
          <div className="stat-title">Memory Allocation</div>
          <div className="stat-num">{metrics?.resources?.memory_percent?.toFixed(1) || '0.0'}%</div>
          <div className="stat-desc">System memory usage</div>
        </div>

        <div className="stat-card success">
          <div className="stat-title">MongoDB Database</div>
          <div className="stat-num">{metrics?.database?.collections?.jobs || '0'}</div>
          <div className="stat-desc">{metrics?.database?.latency_ms ? `Connected (${metrics.database.latency_ms}ms)` : 'Disconnected'}</div>
        </div>

        <div className="stat-card purple">
          <div className="stat-title">Active Consumers</div>
          <div className="stat-num">{metrics?.websockets?.active_connections || '1'}</div>
          <div className="stat-desc">WebSocket listener streams</div>
        </div>
      </div>

      {/* Main Grid */}
      <div className="dashboard-grid dashboard-grid-2col">
        {/* Left Side: Agents List */}
        <div className="card">
          <div className="card-header-bar">
            <div className="card-title-text">
              <Cpu size={20} className="text-primary" />
              <span>AI Service Agents</span>
            </div>
            <span style={{ fontSize: '0.8rem', color: '#9f9fad' }}>
              {agentsData?.agents_healthy || 0} / {agentsData?.agents_total || 0} Healthy
            </span>
          </div>

          <div className="agents-panel-grid">
            {agentsData?.agents && Object.entries(agentsData.agents).map(([name, state]) => (
              <div className="agent-status-card" key={name}>
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                    <span style={{ fontWeight: 700, color: 'white' }}>{name}</span>
                    <span className={getStatusBadgeClass(state.status)}>{state.status}</span>
                  </div>

                  <div className="agent-card-info-row">
                    <span>Uptime</span>
                    <span style={{ color: 'white', fontWeight: 600 }}>{Math.round(state.uptime_seconds / 60)}m</span>
                  </div>
                  <div className="agent-card-info-row">
                    <span>Avg Time</span>
                    <span style={{ color: 'white', fontWeight: 600 }}>{state.last_execution ? '1.2s' : '0.0s'}</span>
                  </div>
                  <div className="agent-card-info-row">
                    <span>Errors</span>
                    <span style={{ color: state.error_count > 0 ? '#ef4444' : '#10b981', fontWeight: 600 }}>
                      {state.error_count}
                    </span>
                  </div>

                  {state.message && state.message !== 'OK' && (
                    <div style={{
                      fontSize: '0.72rem',
                      color: '#ef4444',
                      background: 'rgba(239, 68, 68, 0.05)',
                      padding: '0.4rem',
                      borderRadius: '4px',
                      border: '1px solid rgba(239, 68, 68, 0.1)',
                      marginTop: '0.5rem',
                      wordBreak: 'break-all'
                    }}>
                      {state.message}
                    </div>
                  )}
                </div>

                <div style={{ marginTop: '1.25rem', paddingTop: '0.75rem', borderTop: '1px solid rgba(255,255,255,0.04)' }}>
                  <button 
                    className="btn btn-primary btn-sm" 
                    style={{ width: '100%' }}
                    onClick={() => onTriggerAgent(name)}
                    disabled={triggeringAgents[name]}
                  >
                    <Play size={12} />
                    <span>{triggeringAgents[name] ? 'Triggering...' : 'Execute'}</span>
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right Side: Live Logs */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column' }}>
          <div className="card-header-bar">
            <div className="card-title-text">
              <Activity size={20} className="text-secondary" />
              <span>Live Message Stream</span>
            </div>
          </div>

          <div className="event-log-container">
            {eventLogs.length === 0 ? (
              <div style={{ 
                color: '#9f9fad', 
                textAlign: 'center', 
                padding: '4rem 1rem',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: '0.75rem'
              }}>
                <Terminal size={32} style={{ opacity: 0.4 }} />
                <span>Waiting for events... Trigger an agent to start the stream.</span>
              </div>
            ) : (
              eventLogs.map((evt, idx) => {
                const timestamp = new Date(evt.timestamp).toLocaleTimeString();
                const correlationId = evt.correlation_id ? evt.correlation_id.substring(0, 8) : 'N/A';
                return (
                  <div className="event-card-item" key={idx}>
                    <div className="event-meta">
                      <span>[{timestamp}] <strong style={{ color: '#fff' }}>{evt.source_agent || 'system'}</strong></span>
                      <span>CorrID: {correlationId}</span>
                    </div>
                    <div>
                      <span className="badge badge-idle" style={{ color: '#818cf8', borderColor: 'rgba(99, 102, 241, 0.2)' }}>
                        {evt.event_type}
                      </span>
                    </div>
                    <pre className="event-payload-box">
                      {JSON.stringify(evt.payload, null, 2)}
                    </pre>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
