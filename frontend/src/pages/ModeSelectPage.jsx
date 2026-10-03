import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Target, Layers, ArrowRight, FileText, Code2, Headphones, Sparkles } from 'lucide-react';

export default function ModeSelectPage() {
  const navigate = useNavigate();

  return (
    <div className="app-container" style={{ padding: '3rem 1.5rem', maxWidth: '1100px' }}>
      <div style={{ textAlign: 'center', marginBottom: '3.5rem' }}>
        <div className="badge badge-indigo" style={{ marginBottom: '1rem', padding: '0.4rem 0.9rem' }}>
          <Sparkles size={14} /> Select Your Preparation Track
        </div>
        <h1 style={{ fontSize: '2.5rem', marginBottom: '1rem' }}>
          Choose Your Interview Mode
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '1.05rem', maxWidth: '650px', margin: '0 auto' }}>
          Experience conversational AI mock interviews that adapt difficulty turn-by-turn with spoken evaluation and live coding switch.
        </p>
      </div>

      <div className="grid-2" style={{ gap: '2rem' }}>
        {/* Mode A Card */}
        <div className="glass-panel" style={{
          padding: '2.5rem',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          position: 'relative',
          overflow: 'hidden',
          border: '1px solid rgba(99, 102, 241, 0.25)',
        }}>
          <div style={{
            position: 'absolute',
            top: 0,
            right: 0,
            width: '120px',
            height: '120px',
            background: 'radial-gradient(circle, rgba(99, 102, 241, 0.15) 0%, transparent 70%)',
          }} />

          <div>
            <div style={{
              width: '52px',
              height: '52px',
              borderRadius: '12px',
              background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.2), rgba(139, 92, 246, 0.2))',
              border: '1px solid rgba(99, 102, 241, 0.4)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: '1.5rem',
              color: 'var(--accent-primary)',
            }}>
              <Target size={28} />
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
              <span className="badge badge-indigo">Mode A</span>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Gap-Targeted Spoken Interview</span>
            </div>

            <h2 style={{ fontSize: '1.6rem', marginBottom: '1rem' }}>
              Targeted Role Mock (JD + Resume)
            </h2>

            <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem', lineHeight: '1.6', marginBottom: '1.5rem' }}>
              Upload your resume and paste a target job description. The AI computes vector embeddings to discover exact skill gaps and tailors the live spoken interview to drill those precise areas.
            </p>

            <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '0.6rem', marginBottom: '2rem' }}>
              <li style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-primary)', fontSize: '0.9rem' }}>
                <FileText size={16} color="var(--accent-primary)" /> Automatic Resume & JD Vector Gap Analysis
              </li>
              <li style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-primary)', fontSize: '0.9rem' }}>
                <Headphones size={16} color="var(--accent-cyan)" /> Spoken Question Delivery & Live Transcription
              </li>
              <li style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-primary)', fontSize: '0.9rem' }}>
                <Code2 size={16} color="var(--accent-emerald)" /> Dynamic Code Editor popup for DSA/OOPs gaps
              </li>
            </ul>
          </div>

          <button
            onClick={() => navigate('/setup/mode-a')}
            className="btn btn-primary"
            style={{ width: '100%', padding: '0.9rem' }}
          >
            Launch Mode A Setup <ArrowRight size={18} />
          </button>
        </div>

        {/* Mode B Card */}
        <div className="glass-panel" style={{
          padding: '2.5rem',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          position: 'relative',
          overflow: 'hidden',
          border: '1px solid rgba(6, 182, 212, 0.25)',
        }}>
          <div style={{
            position: 'absolute',
            top: 0,
            right: 0,
            width: '120px',
            height: '120px',
            background: 'radial-gradient(circle, rgba(6, 182, 212, 0.15) 0%, transparent 70%)',
          }} />

          <div>
            <div style={{
              width: '52px',
              height: '52px',
              borderRadius: '12px',
              background: 'linear-gradient(135deg, rgba(6, 182, 212, 0.2), rgba(16, 185, 129, 0.2))',
              border: '1px solid rgba(6, 182, 212, 0.4)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: '1.5rem',
              color: 'var(--accent-cyan)',
            }}>
              <Layers size={28} />
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
              <span className="badge badge-cyan">Mode B</span>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Multi-Subject Adaptive Exam</span>
            </div>

            <h2 style={{ fontSize: '1.6rem', marginBottom: '1rem' }}>
              Subject Mastery Mode
            </h2>

            <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem', lineHeight: '1.6', marginBottom: '1.5rem' }}>
              Select one or more core Computer Science subjects (DSA, OS, DBMS, Networks, OOPs, HR, Aptitude). Practice turn-by-turn difficulty scaling (Level 1–5) powered by Blended RAG.
            </p>

            <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '0.6rem', marginBottom: '2rem' }}>
              <li style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-primary)', fontSize: '0.9rem' }}>
                <Layers size={16} color="var(--accent-cyan)" /> 7 Core Subjects: DSA, OS, DBMS, Networks, OOPs, HR, Aptitude
              </li>
              <li style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-primary)', fontSize: '0.9rem' }}>
                <Sparkles size={16} color="var(--accent-amber)" /> Blended Sourcing: Your PDFs + Question Bank + LLM
              </li>
              <li style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-primary)', fontSize: '0.9rem' }}>
                <Code2 size={16} color="var(--accent-emerald)" /> Monaco Editor with multi-language & pseudocode toggles
              </li>
            </ul>
          </div>

          <button
            onClick={() => navigate('/setup/mode-b')}
            className="btn btn-secondary"
            style={{ width: '100%', padding: '0.9rem', borderColor: 'rgba(6, 182, 212, 0.4)' }}
          >
            Launch Subject Mode Setup <ArrowRight size={18} />
          </button>
        </div>
      </div>
    </div>
  );
}
