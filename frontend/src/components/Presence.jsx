import React, { useState, useEffect } from 'react';
import { Share2, Globe, Users, Check, Save } from 'lucide-react';

export default function Presence({ 
  token,
  apiPrefix
}) {
  const [contents, setContents] = useState([]);
  const [portfolio, setPortfolio] = useState(null);
  const [contacts, setContacts] = useState([]);
  const [bio, setBio] = useState('');
  const [skills, setSkills] = useState('');
  const [portfolioStatus, setPortfolioStatus] = useState('');

  const fetchPresenceData = async () => {
    try {
      const headers = { 'Authorization': `Bearer ${token}` };
      
      // Fetch LinkedIn drafts
      const contentRes = await fetch(`${apiPrefix}/presence/content`, { headers });
      if (contentRes.ok) {
        const cData = await contentRes.json();
        setContents(cData.contents || []);
      }

      // Fetch Portfolio
      const portRes = await fetch(`${apiPrefix}/presence/portfolio`, { headers });
      if (portRes.ok) {
        const pData = await portRes.json();
        setPortfolio(pData);
        setBio(pData.bio || '');
        setSkills(pData.skills?.join(', ') || '');
      }

      // Fetch Networking Leads
      const netRes = await fetch(`${apiPrefix}/presence/networking`, { headers });
      if (netRes.ok) {
        const nData = await netRes.json();
        setContacts(nData.contacts || []);
      }
    } catch (err) {
      console.error("Failed to load presence details", err);
    }
  };

  useEffect(() => {
    fetchPresenceData();
  }, []);

  const handleApproveContent = async (contentId) => {
    try {
      const response = await fetch(`${apiPrefix}/presence/content/${contentId}/approve`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        fetchPresenceData();
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleUpdatePortfolio = async (e) => {
    e.preventDefault();
    setPortfolioStatus('Saving...');
    try {
      const skillList = skills.split(',').map(s => s.trim()).filter(Boolean);
      // Query parameters
      const url = new URL(`${apiPrefix}/presence/portfolio`);
      url.searchParams.append('bio', bio);
      skillList.forEach(s => url.searchParams.append('skills', s));

      const response = await fetch(url.toString(), {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        setPortfolioStatus('Portfolio configuration updated!');
        fetchPresenceData();
      } else {
        setPortfolioStatus('Failed to save portfolio.');
      }
    } catch (err) {
      console.error(err);
      setPortfolioStatus('Error during submission.');
    }
  };

  return (
    <div>
      <div className="section-header">
        <h1 className="section-title">Professional Presence</h1>
      </div>

      <div className="dashboard-grid dashboard-grid-2col">
        {/* Left Side: Content approval & Portfolio configuration */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          
          {/* LinkedIn / GitHub Content Approval */}
          <div className="card">
            <div className="card-header-bar">
              <div className="card-title-text">
                <Share2 size={20} className="text-primary" />
                <span>LinkedIn Draft Approval Panel</span>
              </div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem', maxHeight: '420px', overflowY: 'auto' }}>
              {contents.length === 0 ? (
                <div style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '2rem' }}>No pending social media drafts.</div>
              ) : (
                contents.map((c) => (
                  <div key={c.id} style={{ 
                    background: 'rgba(255,255,255,0.015)', 
                    padding: '1.25rem', 
                    borderRadius: '8px', 
                    border: '1px solid var(--border-glass)',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '0.75rem'
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontWeight: 700, color: 'white', textTransform: 'capitalize' }}>Platform: {c.platform || 'linkedin'}</span>
                      <span className={`badge badge-${c.status === 'approved' || c.status === 'published' ? 'success' : 'warning'}`}>
                        {c.status}
                      </span>
                    </div>

                    <div style={{ fontSize: '0.85rem', color: 'white', background: 'rgba(0,0,0,0.15)', padding: '0.75rem', borderRadius: '6px', whiteSpace: 'pre-wrap', lineHeight: 1.4 }}>
                      {c.text || c.content}
                    </div>

                    {c.status === 'draft' && (
                      <button 
                        className="btn btn-primary btn-sm" 
                        onClick={() => handleApproveContent(c.id)}
                        style={{ alignSelf: 'flex-start' }}
                      >
                        <Check size={12} />
                        <span>Approve & Publish</span>
                      </button>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Portfolio Layout Editor */}
          <div className="card">
            <div className="card-header-bar">
              <div className="card-title-text">
                <Globe size={20} className="text-secondary" />
                <span>Portfolio Website Configuration</span>
              </div>
            </div>

            <form onSubmit={handleUpdatePortfolio} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div className="form-group">
                <label>Biography Summary</label>
                <textarea 
                  className="input-control" 
                  rows={4} 
                  value={bio}
                  onChange={(e) => setBio(e.target.value)}
                  placeholder="Explain your technical background, career goals..."
                  style={{ resize: 'vertical' }}
                  required
                />
              </div>

              <div className="form-group">
                <label>Skills (Comma-separated)</label>
                <input 
                  type="text" 
                  className="input-control"
                  value={skills}
                  onChange={(e) => setSkills(e.target.value)}
                  placeholder="Python, React, MongoDB, FastAPI"
                  required
                />
              </div>

              <button type="submit" className="btn btn-primary" style={{ alignSelf: 'flex-start' }}>
                <Save size={16} />
                <span>Save Config</span>
              </button>

              {portfolioStatus && (
                <div style={{ 
                  fontSize: '0.85rem', 
                  color: portfolioStatus.includes('updated') ? '#10b981' : '#f59e0b',
                  background: 'rgba(255, 255, 255, 0.01)',
                  padding: '0.5rem',
                  borderRadius: '6px',
                  border: '1px solid var(--border-glass)',
                  textAlign: 'center'
                }}>
                  {portfolioStatus}
                </div>
              )}
            </form>
          </div>
        </div>

        {/* Right Side: Networking Leads */}
        <div className="card">
          <div className="card-header-bar">
            <div className="card-title-text">
              <Users size={20} className="text-success" />
              <span>Networking Leads & Outreach</span>
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem', maxHeight: '720px', overflowY: 'auto' }}>
            {contacts.length === 0 ? (
              <div style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '4rem' }}>No networking leads identified yet.</div>
            ) : (
              contacts.map((contact) => (
                <div key={contact.id} style={{ background: 'rgba(255,255,255,0.02)', padding: '1.25rem', borderRadius: '12px', border: '1px solid var(--border-glass)', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div>
                      <div style={{ fontWeight: 800, color: 'white', fontSize: '1rem' }}>{contact.name || 'Unknown Contact'}</div>
                      <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>{contact.role} @ {contact.company}</div>
                    </div>
                    <span className="badge badge-idle" style={{ color: '#818cf8', borderColor: 'rgba(99, 102, 241, 0.2)' }}>
                      {contact.status || 'discovered'}
                    </span>
                  </div>

                  {contact.outreach_notes && (
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', background: 'rgba(0,0,0,0.2)', padding: '0.5rem', borderRadius: '6px' }}>
                      <strong>Draft Note:</strong> {contact.outreach_notes}
                    </div>
                  )}

                  {contact.email && (
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                      Email: {contact.email}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
