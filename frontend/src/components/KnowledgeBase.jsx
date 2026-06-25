import React, { useState, useEffect } from 'react';
import { BookOpen, Award, Compass, Star, Clock } from 'lucide-react';

export default function KnowledgeBase({ 
  token,
  apiPrefix
}) {
  const [digests, setDigests] = useState([]);
  const [learningPlans, setLearningPlans] = useState([]);
  const [knowledgeItems, setKnowledgeItems] = useState([]);

  useEffect(() => {
    const fetchKnowledgeData = async () => {
      try {
        const headers = { 'Authorization': `Bearer ${token}` };
        
        // Fetch digests
        const digRes = await fetch(`${apiPrefix}/knowledge/digests`, { headers });
        if (digRes.ok) {
          const digData = await digRes.json();
          setDigests(digData.digests || []);
        }

        // Fetch learning plans
        const lpRes = await fetch(`${apiPrefix}/knowledge/learning-plans`, { headers });
        if (lpRes.ok) {
          const lpData = await lpRes.json();
          setLearningPlans(lpData.learning_plans || []);
        }

        // Fetch knowledge items
        const itemsRes = await fetch(`${apiPrefix}/knowledge/items`, { headers });
        if (itemsRes.ok) {
          const itemsData = await itemsRes.json();
          setKnowledgeItems(itemsData.items || []);
        }
      } catch (err) {
        console.error("Failed to load knowledge metrics", err);
      }
    };

    fetchKnowledgeData();
  }, []);

  return (
    <div>
      <div className="section-header">
        <h1 className="section-title">Knowledge Intelligence</h1>
      </div>

      <div className="dashboard-grid dashboard-grid-2col">
        {/* Left Side: Digests & Trends */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          {/* Digests Card */}
          <div className="card">
            <div className="card-header-bar">
              <div className="card-title-text">
                <BookOpen size={20} className="text-primary" />
                <span>Technical Digests</span>
              </div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', maxHeight: '350px', overflowY: 'auto' }}>
              {digests.length === 0 ? (
                <div style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '2rem' }}>No technical digests compiled yet.</div>
              ) : (
                digests.map((dig) => (
                  <div key={dig.id} style={{ background: 'rgba(255,255,255,0.015)', padding: '1.25rem', borderRadius: '8px', border: '1px solid var(--border-glass)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                      <span style={{ fontWeight: 700, color: 'white', textTransform: 'capitalize' }}>{dig.type} Digest</span>
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                        <Clock size={12} /> {new Date(dig.created_at).toLocaleDateString()}
                      </span>
                    </div>
                    
                    {dig.summary && (
                      <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', lineHeight: 1.5, marginBottom: '0.75rem' }}>{dig.summary}</p>
                    )}

                    {dig.content && (
                      <div style={{ fontSize: '0.8rem', color: 'white', background: 'rgba(0,0,0,0.15)', padding: '0.75rem', borderRadius: '6px', whiteSpace: 'pre-wrap' }}>
                        {dig.content}
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Scraped Knowledge Items (Papers/GitHub) */}
          <div className="card">
            <div className="card-header-bar">
              <div className="card-title-text">
                <Compass size={20} className="text-secondary" />
                <span>Scraped Papers & Repositories</span>
              </div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', maxHeight: '420px', overflowY: 'auto' }}>
              {knowledgeItems.length === 0 ? (
                <div style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '2rem' }}>No scraped research items found.</div>
              ) : (
                knowledgeItems.map((item) => (
                  <div key={item.id} style={{ background: 'rgba(255,255,255,0.015)', padding: '1rem', borderRadius: '8px', border: '1px solid var(--border-glass)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
                      <div>
                        <span className="badge badge-idle" style={{ color: '#a855f7', borderColor: 'rgba(168, 85, 247, 0.2)', marginBottom: '0.25rem' }}>
                          {item.type}
                        </span>
                        <div style={{ fontWeight: 700, color: 'white' }}>{item.title}</div>
                      </div>
                      {item.url && (
                        <a href={item.url} target="_blank" rel="noreferrer" className="btn btn-outline btn-sm" style={{ padding: '0.25rem 0.5rem' }}>
                          View
                        </a>
                      )}
                    </div>
                    {item.summary && (
                      <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', lineHeight: 1.4 }}>{item.summary}</p>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Right Side: Learning Roadmaps */}
        <div className="card">
          <div className="card-header-bar">
            <div className="card-title-text">
              <Award size={20} className="text-success" />
              <span>Skills Acquisition Plans</span>
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem', maxHeight: '820px', overflowY: 'auto' }}>
            {learningPlans.length === 0 ? (
              <div style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '4rem' }}>No custom roadmaps compiled by AI agents yet.</div>
            ) : (
              learningPlans.map((plan) => (
                <div key={plan.id} style={{ background: 'rgba(255,255,255,0.02)', padding: '1.5rem', borderRadius: '12px', border: '1px solid var(--border-glass)', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                  <div>
                    <h3 style={{ fontWeight: 800, color: 'white', fontSize: '1.1rem', marginBottom: '0.25rem' }}>{plan.skill_name || 'Skill Plan'}</h3>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Target Role: {plan.target_role || 'General Growth'}</div>
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                    <div style={{ fontSize: '0.85rem', fontWeight: 600, color: '#a5b4fc' }}>Curated Milestones:</div>
                    {plan.modules && plan.modules.map((mod, index) => (
                      <div key={index} style={{ background: 'rgba(0,0,0,0.2)', padding: '0.75rem', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.03)' }}>
                        <div style={{ fontWeight: 700, color: 'white', fontSize: '0.85rem', marginBottom: '0.2rem' }}>
                          {index + 1}. {mod.title || 'Learning Module'}
                        </div>
                        <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', lineHeight: 1.4 }}>
                          {mod.description || 'Topic breakdown and practice projects.'}
                        </p>
                      </div>
                    ))}
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
