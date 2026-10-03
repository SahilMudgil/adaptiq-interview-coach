import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Target, UploadCloud, FileText, ArrowRight, CheckCircle2, AlertCircle, Sparkles, BarChart2 } from 'lucide-react';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';

export default function SetupModeAPage() {
  const { isAuthenticated } = useAuth();
  const [resumeFile, setResumeFile] = useState(null);
  const [resumeText, setResumeText] = useState('');
  const [useTextInput, setUseTextInput] = useState(false);
  const [jdFile, setJdFile] = useState(null);
  const [jdText, setJdText] = useState('');
  const [useJdTextInput, setUseJdTextInput] = useState(false);
  const [loading, setLoading] = useState(false);
  const [analyzingGaps, setAnalyzingGaps] = useState(false);
  const [gapResult, setGapResult] = useState(null);
  const [error, setError] = useState('');
  const [uploadedResumeId, setUploadedResumeId] = useState(null);
  const [submittedJdId, setSubmittedJdId] = useState(null);
  const navigate = useNavigate();

  const handleAnalyze = async (e) => {
    e.preventDefault();
    if (!isAuthenticated) {
      setError('Please sign in or use One-Click Demo Login to run gap analysis.');
      return;
    }
    if (!resumeFile && !resumeText.trim()) {
      setError('Please upload a resume PDF or paste resume text.');
      return;
    }
    if (!jdFile && !jdText.trim()) {
      setError('Please upload a JD PDF or paste job description text.');
      return;
    }

    setError('');
    setAnalyzingGaps(true);

    try {
      // 1. Upload/Submit Resume
      let rId = uploadedResumeId;
      if (!rId) {
        if (resumeFile) {
          const formData = new FormData();
          formData.append('file', resumeFile);
          const rRes = await api.uploadResume(formData);
          rId = rRes.id;
        } else {
          const formData = new FormData();
          formData.append('raw_text', resumeText);
          const rRes = await api.uploadResume(formData);
          rId = rRes.id;
        }
        setUploadedResumeId(rId);
      }

      // 2. Submit JD
      let jId = submittedJdId;
      if (!jId) {
        if (jdFile) {
          const formData = new FormData();
          formData.append('file', jdFile);
          const jRes = await api.uploadJD(formData);
          jId = jRes.id;
        } else {
          const jRes = await api.submitJD(jdText);
          jId = jRes.id;
        }
        setSubmittedJdId(jId);
      }

      // 3. Run Gap Analysis
      const analysis = await api.runGapAnalysis(rId, jId);
      setGapResult(analysis);
    } catch (err) {
      setError(err.message || 'Failed to analyze gap.');
    } finally {
      setAnalyzingGaps(false);
    }
  };

  const handleStartInterview = async () => {
    setLoading(true);
    setError('');
    try {
      const session = await api.startSession({
        mode: 'JD',
        resume_id: uploadedResumeId,
        jd_id: submittedJdId,
      });
      navigate(`/interview/${session.id}`);
    } catch (err) {
      setError(err.message || 'Failed to start session. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container" style={{ maxWidth: '900px', padding: '2.5rem 1.5rem' }}>
      <div style={{ marginBottom: '2rem' }}>
        <div className="badge badge-indigo" style={{ marginBottom: '0.75rem' }}>
          <Target size={14} /> Mode A: Targeted Role Track
        </div>
        <h1 style={{ fontSize: '2.2rem', marginBottom: '0.5rem' }}>Resume & JD Gap Matcher</h1>
        <p style={{ color: 'var(--text-secondary)' }}>
          Upload your resume and paste a target role. The AI evaluates technical overlap and targets your spoken interview specifically on missing competencies.
        </p>
      </div>

      {error && (
        <div style={{
          padding: '1rem',
          background: 'rgba(239, 68, 68, 0.15)',
          border: '1px solid rgba(239, 68, 68, 0.3)',
          borderRadius: '10px',
          color: '#FCA5A5',
          marginBottom: '1.5rem',
          fontSize: '0.9rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
        }}>
          <AlertCircle size={18} /> {error}
        </div>
      )}

      {/* Inputs Form */}
      <form onSubmit={handleAnalyze} style={{ display: 'flex', flexDirection: 'column', gap: '1.75rem' }}>
        {/* Step 1: Resume */}
        <div className="glass-panel" style={{ padding: '1.75rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
            <h3 style={{ fontSize: '1.15rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <UploadCloud size={20} color="var(--accent-primary)" /> 1. Candidate Resume
            </h3>
            <button
              type="button"
              onClick={() => setUseTextInput(!useTextInput)}
              style={{ background: 'transparent', border: 'none', color: 'var(--accent-primary)', cursor: 'pointer', fontSize: '0.8rem' }}
            >
              {useTextInput ? 'Switch to PDF file upload' : 'Paste resume text instead'}
            </button>
          </div>

          {useTextInput ? (
            <textarea
              className="textarea-field"
              rows={5}
              placeholder="Paste candidate resume text or CV summary here..."
              value={resumeText}
              onChange={(e) => {
                setResumeText(e.target.value);
                setUploadedResumeId(null);
              }}
            />
          ) : (
            <div>
              <input
                type="file"
                accept=".pdf,.txt"
                onChange={(e) => {
                  setResumeFile(e.target.files[0]);
                  setUploadedResumeId(null);
                }}
                style={{
                  display: 'block',
                  width: '100%',
                  padding: '1rem',
                  borderRadius: '10px',
                  border: '2px dashed var(--border-subtle)',
                  background: 'rgba(13, 19, 34, 0.6)',
                  color: 'var(--text-primary)',
                  cursor: 'pointer',
                }}
              />
              {resumeFile && (
                <div style={{ marginTop: '0.5rem', fontSize: '0.85rem', color: 'var(--accent-emerald)', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                  <CheckCircle2 size={16} /> Selected: {resumeFile.name}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Step 2: JD */}
        <div className="glass-panel" style={{ padding: '1.75rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
            <h3 style={{ fontSize: '1.15rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <FileText size={20} color="var(--accent-cyan)" /> 2. Target Job Description
            </h3>
            <button
              type="button"
              onClick={() => setUseJdTextInput(!useJdTextInput)}
              style={{ background: 'transparent', border: 'none', color: 'var(--accent-cyan)', cursor: 'pointer', fontSize: '0.8rem' }}
            >
              {useJdTextInput ? 'Switch to PDF file upload' : 'Paste JD text instead'}
            </button>
          </div>

          {useJdTextInput ? (
            <textarea
              className="textarea-field"
              rows={5}
              placeholder="Paste role requirements (e.g. Senior Software Engineer - Requirements: Proficient in C++, Multi-threading, OS internals, Distributed Systems, Algorithms)..."
              value={jdText}
              onChange={(e) => {
                setJdText(e.target.value);
                setSubmittedJdId(null);
              }}
            />
          ) : (
            <div>
              <input
                type="file"
                accept=".pdf,.txt"
                onChange={(e) => {
                  setJdFile(e.target.files[0]);
                  setSubmittedJdId(null);
                }}
                style={{
                  display: 'block',
                  width: '100%',
                  padding: '1rem',
                  borderRadius: '10px',
                  border: '2px dashed var(--border-subtle)',
                  background: 'rgba(13, 19, 34, 0.6)',
                  color: 'var(--text-primary)',
                  cursor: 'pointer',
                }}
              />
              {jdFile && (
                <div style={{ marginTop: '0.5rem', fontSize: '0.85rem', color: 'var(--accent-cyan)', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                  <CheckCircle2 size={16} /> Selected: {jdFile.name}
                </div>
              )}
            </div>
          )}
        </div>

        <button
          type="submit"
          disabled={analyzingGaps}
          className="btn btn-primary"
          style={{ padding: '0.95rem', fontSize: '1rem' }}
        >
          {analyzingGaps ? 'Running Semantic Vector & LLM Gap Analysis...' : <><Sparkles size={18} /> Compute Skill Gap Analysis</>}
        </button>
      </form>

      {/* Gap Analysis Live Result Display */}
      {gapResult && (
        <div className="glass-panel" style={{ marginTop: '2.5rem', padding: '2rem', border: '1px solid var(--accent-primary)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
            <div>
              <span className="badge badge-indigo">Analysis Complete</span>
              <h2 style={{ fontSize: '1.6rem', marginTop: '0.35rem' }}>Candidate Gap Breakdown</h2>
            </div>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--accent-cyan)' }}>
                {gapResult.overall_match_percentage}%
              </div>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Role Match Score</span>
            </div>
          </div>

          <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem', fontSize: '0.95rem', lineHeight: '1.5' }}>
            {gapResult.match_summary}
          </p>

          <div className="grid-2" style={{ gap: '1.25rem', marginBottom: '1.5rem' }}>
            <div style={{ background: 'rgba(16, 185, 129, 0.08)', padding: '1.25rem', borderRadius: '10px', border: '1px solid rgba(16, 185, 129, 0.2)' }}>
              <h4 style={{ color: 'var(--accent-emerald)', fontSize: '0.95rem', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                <CheckCircle2 size={16} /> Verified Candidate Strengths:
              </h4>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
                {(gapResult.matched_skills || []).map((s, idx) => (
                  <span key={idx} className="badge badge-emerald" style={{ fontSize: '0.75rem' }}>{s}</span>
                ))}
              </div>
            </div>

            <div style={{ background: 'rgba(239, 68, 68, 0.08)', padding: '1.25rem', borderRadius: '10px', border: '1px solid rgba(239, 68, 68, 0.2)' }}>
              <h4 style={{ color: '#FCA5A5', fontSize: '0.95rem', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                <AlertCircle size={16} /> Identified Capability Gaps:
              </h4>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
                {(gapResult.missing_critical_skills || []).map((s, idx) => (
                  <span key={idx} className="badge badge-amber" style={{ fontSize: '0.75rem' }}>{s}</span>
                ))}
              </div>
            </div>
          </div>

          {/* Recommended Spoken Focus */}
          <div style={{ marginBottom: '2rem' }}>
            <h4 style={{ fontSize: '1rem', marginBottom: '0.75rem' }}>Full-Loop Interview Agenda:</h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              <div style={{
                padding: '0.75rem 1rem',
                borderRadius: '8px',
                background: 'rgba(99, 102, 241, 0.1)',
                border: '1px solid rgba(99, 102, 241, 0.3)',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}>
                <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                  Turn 1: Self-Introduction & Resume Project Deep-Dive
                </span>
                <span className="badge badge-indigo" style={{ fontSize: '0.7rem' }}>
                  Opening Warmup & Architecture
                </span>
              </div>
              {(gapResult.recommended_interview_focus || []).map((f, idx) => (
                <div key={idx} style={{
                  padding: '0.75rem 1rem',
                  borderRadius: '8px',
                  background: 'rgba(255, 255, 255, 0.04)',
                  border: '1px solid var(--border-subtle)',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}>
                  <span style={{ fontWeight: 600 }}>Turn {idx + 2}: {typeof f === 'string' ? f : f.topic}</span>
                  <span className="badge badge-cyan" style={{ fontSize: '0.7rem' }}>
                    {typeof f === 'object' && f.reason ? f.reason : 'Technical Gap Drill'}
                  </span>
                </div>
              ))}
            </div>
          </div>

          <button
            onClick={handleStartInterview}
            disabled={loading}
            className="btn btn-primary"
            style={{ width: '100%', padding: '1rem', fontSize: '1.05rem' }}
          >
            {loading ? 'Starting Spoken Engine...' : <>Launch Spoken Mock Interview on These Gaps <ArrowRight size={18} /></>}
          </button>
        </div>
      )}
    </div>
  );
}
