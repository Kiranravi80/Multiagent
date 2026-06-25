import React, { useState } from 'react';
import { Award, CheckCircle, Send, Play, Terminal, HelpCircle } from 'lucide-react';

export default function InterviewPrep({ 
  token,
  apiPrefix
}) {
  const [role, setRole] = useState('Senior Software Engineer');
  const [company, setCompany] = useState('Google');
  const [session, setSession] = useState(null);
  const [activeQuestionIdx, setActiveQuestionIdx] = useState(0);
  const [userAnswer, setUserAnswer] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [initializing, setInitializing] = useState(false);
  const [feedback, setFeedback] = useState(null);

  const startNewSession = async (e) => {
    e.preventDefault();
    setInitializing(true);
    setFeedback(null);
    setSession(null);
    try {
      const response = await fetch(`${apiPrefix}/interview/sessions?role=${encodeURIComponent(role)}&company=${encodeURIComponent(company)}`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        if (data.interview_id) {
          // Fetch the full session immediately
          const sessResponse = await fetch(`${apiPrefix}/interview/sessions/${data.interview_id}`, {
            headers: { 'Authorization': `Bearer ${token}` }
          });
          if (sessResponse.ok) {
            const sessData = await sessResponse.json();
            setSession(sessData);
            setActiveQuestionIdx(0);
          }
        }
      }
    } catch (err) {
      console.error(err);
    } finally {
      setInitializing(false);
    }
  };

  const submitAnswer = async (e) => {
    e.preventDefault();
    if (!userAnswer.trim()) return;

    setSubmitting(true);
    setFeedback(null);

    try {
      const response = await fetch(`${apiPrefix}/interview/sessions/${session.id}/answer?question_index=${activeQuestionIdx}`, {
        method: 'POST',
        headers: { 
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(userAnswer)
      });

      if (response.ok) {
        const data = await response.json();
        setFeedback(data);
        setUserAnswer('');
        
        // Refresh session state to update scores and progress
        const sessResponse = await fetch(`${apiPrefix}/interview/sessions/${session.id}`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (sessResponse.ok) {
          const sessData = await sessResponse.json();
          setSession(sessData);
        }
      }
    } catch (err) {
      console.error(err);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div>
      <div className="section-header">
        <h1 className="section-title">Interview Simulator</h1>
      </div>

      <div className="dashboard-grid dashboard-grid-2col">
        {/* Left Side: Active Q&A Interface */}
        <div className="card">
          <div className="card-header-bar">
            <div className="card-title-text">
              <HelpCircle size={20} className="text-primary" />
              <span>Interactive Mock Interview</span>
            </div>
          </div>

          {!session ? (
            <form onSubmit={startNewSession} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem', padding: '2rem 1rem' }}>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', lineHeight: 1.5 }}>
                Configure target parameters below to generate a tailored interview simulation customized to your resume and the role requirements.
              </p>

              <div className="form-group">
                <label>Target Role / Title</label>
                <input 
                  type="text" 
                  className="input-control" 
                  value={role}
                  onChange={(e) => setRole(e.target.value)}
                  placeholder="e.g. Senior Software Engineer"
                  required
                />
              </div>

              <div className="form-group">
                <label>Target Company</label>
                <input 
                  type="text" 
                  className="input-control" 
                  value={company}
                  onChange={(e) => setCompany(e.target.value)}
                  placeholder="e.g. Google"
                  required
                />
              </div>

              <button type="submit" className="btn btn-primary" style={{ alignSelf: 'flex-start' }} disabled={initializing}>
                <Play size={14} />
                <span>{initializing ? 'Generating Simulator...' : 'Start Session'}</span>
              </button>
            </form>
          ) : (
            <div className="interview-container">
              {/* Question Navigation */}
              <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap', borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '0.75rem' }}>
                {session.questions && session.questions.map((q, idx) => (
                  <button 
                    key={idx}
                    className={`btn btn-sm ${idx === activeQuestionIdx ? 'btn-primary' : 'btn-outline'}`}
                    onClick={() => {
                      setActiveQuestionIdx(idx);
                      setFeedback(null);
                    }}
                    style={{ minWidth: '40px' }}
                  >
                    Q{idx + 1} {q.user_answer ? '✓' : ''}
                  </button>
                ))}
              </div>

              {/* Active Question Display */}
              <div className="chat-history">
                <div className="chat-bubble ai">
                  <div style={{ fontWeight: 800, color: 'white', marginBottom: '0.5rem' }}>Question {activeQuestionIdx + 1}:</div>
                  <div>{session.questions?.[activeQuestionIdx]?.question}</div>
                </div>

                {session.questions?.[activeQuestionIdx]?.user_answer && (
                  <div className="chat-bubble user">
                    <div style={{ fontWeight: 800, color: 'white', marginBottom: '0.5rem' }}>Your Answer:</div>
                    <div>{session.questions[activeQuestionIdx].user_answer}</div>
                  </div>
                )}
              </div>

              {/* Answer submission form */}
              {!session.questions?.[activeQuestionIdx]?.user_answer ? (
                <form onSubmit={submitAnswer} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                  <div className="form-group">
                    <label>Provide your verbal / written response:</label>
                    <textarea 
                      className="input-control" 
                      rows={5}
                      value={userAnswer}
                      onChange={(e) => setUserAnswer(e.target.value)}
                      placeholder="Type your response here..."
                      style={{ resize: 'vertical' }}
                      required
                      disabled={submitting}
                    />
                  </div>
                  <button type="submit" className="btn btn-primary" style={{ alignSelf: 'flex-start' }} disabled={submitting}>
                    <Send size={14} />
                    <span>{submitting ? 'Evaluating response...' : 'Submit Answer'}</span>
                  </button>
                </form>
              ) : (
                <div style={{ 
                  background: 'rgba(16, 185, 129, 0.05)', 
                  border: '1px solid rgba(16, 185, 129, 0.15)', 
                  padding: '1rem', 
                  borderRadius: '8px',
                  color: 'white',
                  fontSize: '0.85rem'
                }}>
                  <CheckCircle size={16} style={{ color: '#10b981', display: 'inline', marginRight: '0.5rem', verticalAlign: 'middle' }} />
                  <span>Question answered. Review performance score on the right.</span>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Right Side: Score Summary & Question Feedback */}
        <div className="card">
          <div className="card-header-bar">
            <div className="card-title-text">
              <Award size={20} className="text-secondary" />
              <span>AI Evaluation Report</span>
            </div>
          </div>

          {!session ? (
            <div style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '6rem 2rem' }}>
              No active simulation metrics. Start an interview session on the left to see grading feedback.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
              {/* Overall Session Stats */}
              <div style={{ background: 'rgba(255,255,255,0.015)', padding: '1.25rem', borderRadius: '12px', border: '1px solid var(--border-glass)' }}>
                <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Average Overall Score</div>
                <div style={{ fontSize: '2.5rem', fontWeight: 800, color: 'white', margin: '0.25rem 0' }}>
                  {session.score !== null ? `${session.score}%` : 'N/A'}
                </div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                  Status: <span style={{ color: session.status === 'completed' ? '#10b981' : '#f59e0b', fontWeight: 700, textTransform: 'capitalize' }}>{session.status}</span>
                </div>
                {session.overall_feedback && (
                  <p style={{ fontSize: '0.82rem', marginTop: '0.75rem', borderTop: '1px solid rgba(255,255,255,0.04)', paddingTop: '0.5rem', lineHeight: 1.4 }}>
                    {session.overall_feedback}
                  </p>
                )}
              </div>

              {/* Selected Question Detailed Feedback */}
              {session.questions?.[activeQuestionIdx]?.user_answer ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontWeight: 800, color: 'white' }}>Question {activeQuestionIdx + 1} Score:</span>
                    <span className="badge badge-success" style={{ fontSize: '1rem', padding: '0.3rem 0.75rem' }}>
                      {session.questions[activeQuestionIdx].score}%
                    </span>
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                    {session.questions[activeQuestionIdx].feedback && (
                      <div style={{ background: 'rgba(255,255,255,0.02)', padding: '1rem', borderRadius: '8px', border: '1px solid var(--border-glass)' }}>
                        <div style={{ fontWeight: 700, color: 'white', fontSize: '0.85rem', marginBottom: '0.4rem' }}>AI Feedback:</div>
                        <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', lineHeight: 1.4 }}>
                          {session.questions[activeQuestionIdx].feedback}
                        </p>
                      </div>
                    )}

                    {session.questions[activeQuestionIdx].strengths && session.questions[activeQuestionIdx].strengths.length > 0 && (
                      <div style={{ background: 'rgba(16, 185, 129, 0.02)', padding: '1rem', borderRadius: '8px', border: '1px solid rgba(16, 185, 129, 0.1)' }}>
                        <div style={{ fontWeight: 700, color: '#10b981', fontSize: '0.85rem', marginBottom: '0.4rem' }}>Strengths:</div>
                        <ul style={{ paddingLeft: '1.25rem', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                          {session.questions[activeQuestionIdx].strengths.map((str, i) => (
                            <li key={i} style={{ marginBottom: '0.2rem' }}>{str}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {session.questions[activeQuestionIdx].improvements && session.questions[activeQuestionIdx].improvements.length > 0 && (
                      <div style={{ background: 'rgba(245, 158, 11, 0.02)', padding: '1rem', borderRadius: '8px', border: '1px solid rgba(245, 158, 11, 0.1)' }}>
                        <div style={{ fontWeight: 700, color: '#f59e0b', fontSize: '0.85rem', marginBottom: '0.4rem' }}>Suggested Improvements:</div>
                        <ul style={{ paddingLeft: '1.25rem', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                          {session.questions[activeQuestionIdx].improvements.map((imp, i) => (
                            <li key={i} style={{ marginBottom: '0.2rem' }}>{imp}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              ) : (
                <div style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '4rem 1rem', background: 'rgba(0,0,0,0.1)', borderRadius: '8px' }}>
                  Submit an answer to Question {activeQuestionIdx + 1} to load detailed grading feedback.
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
