import React, { useState, useEffect } from 'react';
import { Mail, Calendar, Send, Clock, User, Check } from 'lucide-react';

export default function Communication({ 
  token,
  apiPrefix
}) {
  const [emails, setEmails] = useState([]);
  const [events, setEvents] = useState([]);

  const fetchCommData = async () => {
    try {
      const headers = { 'Authorization': `Bearer ${token}` };
      
      // Fetch Emails
      const mailRes = await fetch(`${apiPrefix}/communication/emails`, { headers });
      if (mailRes.ok) {
        const mailData = await mailRes.json();
        setEmails(mailData.emails || []);
      }

      // Fetch Calendar Events
      const calRes = await fetch(`${apiPrefix}/communication/calendar`, { headers });
      if (calRes.ok) {
        const calData = await calRes.json();
        setEvents(calData.events || []);
      }
    } catch (err) {
      console.error("Failed to load communication details", err);
    }
  };

  useEffect(() => {
    fetchCommData();
  }, []);

  const handleSendEmail = async (emailId) => {
    try {
      const response = await fetch(`${apiPrefix}/communication/emails/${emailId}/send`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        fetchCommData();
      }
    } catch (err) {
      console.error("Failed to send email draft", err);
    }
  };

  return (
    <div>
      <div className="section-header">
        <h1 className="section-title">Communication & Scheduling</h1>
      </div>

      <div className="dashboard-grid dashboard-grid-2col">
        {/* Left Side: Inbox Outbox queues */}
        <div className="card">
          <div className="card-header-bar">
            <div className="card-title-text">
              <Mail size={20} className="text-primary" />
              <span>Recruiter Correspondence Queue</span>
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem', maxHeight: '720px', overflowY: 'auto' }}>
            {emails.length === 0 ? (
              <div style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '4rem' }}>No communications registered in database.</div>
            ) : (
              emails.map((mail) => (
                <div key={mail.id} style={{ 
                  background: 'rgba(255,255,255,0.015)', 
                  padding: '1.25rem', 
                  borderRadius: '12px', 
                  border: '1px solid var(--border-glass)',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.75rem'
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <User size={14} className="text-primary" />
                      <span style={{ fontWeight: 700, color: 'white' }}>To: {mail.to_email}</span>
                    </div>
                    <span className={`badge badge-${mail.status === 'sent' ? 'success' : 'warning'}`}>
                      {mail.status}
                    </span>
                  </div>

                  <div style={{ fontWeight: 600, color: 'white', fontSize: '0.9rem' }}>Subject: {mail.subject}</div>
                  
                  <div style={{ 
                    fontSize: '0.85rem', 
                    color: 'white', 
                    background: 'rgba(0,0,0,0.15)', 
                    padding: '0.75rem', 
                    borderRadius: '6px', 
                    whiteSpace: 'pre-wrap', 
                    lineHeight: 1.4 
                  }}>
                    {mail.body}
                  </div>

                  {(mail.status === 'draft' || mail.status === 'pending_approval') && (
                    <button 
                      className="btn btn-primary btn-sm" 
                      onClick={() => handleSendEmail(mail.id)}
                      style={{ alignSelf: 'flex-start' }}
                    >
                      <Send size={12} />
                      <span>Approve & Send Email</span>
                    </button>
                  )}
                </div>
              ))
            )}
          </div>
        </div>

        {/* Right Side: Calendar events & Holdings */}
        <div className="card">
          <div className="card-header-bar">
            <div className="card-title-text">
              <Calendar size={20} className="text-secondary" />
              <span>Calendar holds & Interview Slots</span>
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', maxHeight: '720px', overflowY: 'auto' }}>
            {events.length === 0 ? (
              <div style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '4rem' }}>No calendar holding events.</div>
            ) : (
              events.map((ev) => (
                <div key={ev.id} style={{ 
                  background: 'rgba(255,255,255,0.02)', 
                  padding: '1rem', 
                  borderRadius: '8px', 
                  border: '1px solid var(--border-glass)',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.5rem'
                }}>
                  <div style={{ fontWeight: 800, color: 'white' }}>{ev.title}</div>
                  {ev.description && <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{ev.description}</p>}
                  
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.75rem', color: '#818cf8', marginTop: '0.25rem' }}>
                    <Clock size={12} />
                    <span>
                      {new Date(ev.start_time).toLocaleString()} — {new Date(ev.end_time).toLocaleString()}
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
