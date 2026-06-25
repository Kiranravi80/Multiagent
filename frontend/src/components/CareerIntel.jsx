import React, { useState, useEffect } from 'react';
import { UploadCloud, CheckCircle, ExternalLink, Briefcase, FileText, Check } from 'lucide-react';

export default function CareerIntel({ 
  token,
  apiPrefix
}) {
  const [profile, setProfile] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [applications, setApplications] = useState([]);
  const [uploadStatus, setUploadStatus] = useState(null);
  const [loading, setLoading] = useState(false);

  const fetchCareerData = async () => {
    try {
      const headers = { 'Authorization': `Bearer ${token}` };
      
      // Fetch Profile
      const profRes = await fetch(`${apiPrefix}/profile/me`, { headers });
      if (profRes.ok) {
        const profData = await profRes.json();
        setProfile(profData);
      }

      // Fetch Jobs
      const jobsRes = await fetch(`${apiPrefix}/jobs`, { headers });
      if (jobsRes.ok) {
        const jobsData = await jobsRes.json();
        setJobs(jobsData.jobs || []);
      }

      // Fetch Applications
      const appsRes = await fetch(`${apiPrefix}/applications`, { headers });
      if (appsRes.ok) {
        const appsData = await appsRes.json();
        setApplications(appsData.applications || []);
      }
    } catch (err) {
      console.error("Failed to fetch career intelligence data", err);
    }
  };

  useEffect(() => {
    fetchCareerData();
  }, []);

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    setLoading(true);
    setUploadStatus("Uploading resume...");

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch(`${apiPrefix}/resume/upload`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
      });

      if (response.ok) {
        setUploadStatus("Upload complete! Parsing resume...");
        // Auto parse resume
        const parseResponse = await fetch(`${apiPrefix}/resume/parse`, {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (parseResponse.ok) {
          setUploadStatus("Resume parsed successfully!");
          fetchCareerData();
        } else {
          setUploadStatus("Resume uploaded, but auto-parsing failed.");
        }
      } else {
        setUploadStatus("Upload failed. Verify size limit.");
      }
    } catch (err) {
      console.error(err);
      setUploadStatus("Connection failed during upload.");
    } finally {
      setLoading(false);
    }
  };

  const handleApproveApp = async (appId) => {
    try {
      const response = await fetch(`${apiPrefix}/applications/${appId}/approve`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        fetchCareerData();
      }
    } catch (err) {
      console.error("Failed to approve application", err);
    }
  };

  return (
    <div>
      <div className="section-header">
        <h1 className="section-title">Career Intelligence</h1>
      </div>

      <div className="dashboard-grid dashboard-grid-2col">
        {/* Left Side: Resume & Jobs */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          {/* Resume Card */}
          <div className="card">
            <div className="card-header-bar">
              <div className="card-title-text">
                <FileText size={20} className="text-primary" />
                <span>Resume Management</span>
              </div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {profile ? (
                <div style={{ background: 'rgba(255,255,255,0.02)', padding: '1rem', borderRadius: '8px', border: '1px solid var(--border-glass)' }}>
                  <div style={{ fontWeight: 700, color: 'white', marginBottom: '0.25rem' }}>{profile.full_name || 'Resume Profile'}</div>
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Email: {profile.email}</div>
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Skills: {profile.skills?.join(', ') || 'None parsed yet'}</div>
                </div>
              ) : (
                <div style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>No resume uploaded or parsed. Upload your PDF resume below.</div>
              )}

              <label 
                className="btn btn-outline" 
                style={{ 
                  border: '1px dashed var(--border-glass)', 
                  padding: '2rem', 
                  borderRadius: '12px',
                  display: 'flex', 
                  flexDirection: 'column', 
                  gap: '0.5rem',
                  alignItems: 'center',
                  cursor: 'pointer'
                }}
              >
                <UploadCloud size={32} className="text-primary" />
                <span>Choose PDF Resume File</span>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Max size 10MB</span>
                <input type="file" accept=".pdf" style={{ display: 'none' }} onChange={handleFileUpload} disabled={loading} />
              </label>

              {uploadStatus && (
                <div style={{ 
                  fontSize: '0.85rem', 
                  color: uploadStatus.includes('success') || uploadStatus.includes('complete') ? '#10b981' : '#f59e0b',
                  background: 'rgba(255, 255, 255, 0.01)',
                  padding: '0.5rem 0.75rem',
                  borderRadius: '6px',
                  border: '1px solid var(--border-glass)',
                  textAlign: 'center'
                }}>
                  {uploadStatus}
                </div>
              )}
            </div>
          </div>

          {/* Matched Jobs Card */}
          <div className="card">
            <div className="card-header-bar">
              <div className="card-title-text">
                <Briefcase size={20} className="text-secondary" />
                <span>Scraped & Matched Jobs</span>
              </div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', maxHeight: '400px', overflowY: 'auto' }}>
              {jobs.length === 0 ? (
                <div style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '2rem' }}>No job listings found in database.</div>
              ) : (
                jobs.map((job) => (
                  <div key={job.id} style={{ background: 'rgba(255,255,255,0.015)', padding: '1rem', borderRadius: '8px', border: '1px solid var(--border-glass)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <div style={{ fontWeight: 700, color: 'white' }}>{job.title}</div>
                      <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>{job.company} — {job.location}</div>
                      <div style={{ fontSize: '0.75rem', color: '#818cf8', marginTop: '0.25rem' }}>Source: {job.source} | Match Score: {job.match_score || 'Pending'}</div>
                    </div>
                    {job.url && (
                      <a href={job.url} target="_blank" rel="noreferrer" className="btn btn-outline btn-sm">
                        <ExternalLink size={12} />
                      </a>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Right Side: Active Applications */}
        <div className="card">
          <div className="card-header-bar">
            <div className="card-title-text">
              <CheckCircle size={20} className="text-success" />
              <span>Job Applications Pipeline</span>
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', maxHeight: '720px', overflowY: 'auto' }}>
            {applications.length === 0 ? (
              <div style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '4rem' }}>No applications active in the automated pipeline.</div>
            ) : (
              applications.map((app) => (
                <div key={app.id} style={{ 
                  background: 'rgba(255,255,255,0.02)', 
                  padding: '1.25rem', 
                  borderRadius: '12px', 
                  border: '1px solid var(--border-glass)',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.75rem'
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div>
                      <div style={{ fontWeight: 800, color: 'white', fontSize: '1rem' }}>{app.job_title || 'Unknown Role'}</div>
                      <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', fontWeight: 500 }}>{app.company || 'Unknown Company'}</div>
                    </div>
                    <span className={`badge badge-${app.status === 'applied' ? 'success' : app.status === 'pending_approval' ? 'warning' : 'idle'}`}>
                      {app.status}
                    </span>
                  </div>

                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', background: 'rgba(0,0,0,0.2)', padding: '0.5rem', borderRadius: '6px' }}>
                    {app.timeline && app.timeline[app.timeline.length - 1]?.notes || 'No activity log.'}
                  </div>

                  {app.status === 'pending_approval' && (
                    <button 
                      className="btn btn-primary btn-sm" 
                      onClick={() => handleApproveApp(app.id)}
                      style={{ alignSelf: 'flex-start' }}
                    >
                      <Check size={12} />
                      <span>Approve & Auto-Apply</span>
                    </button>
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
