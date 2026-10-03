import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Layers, ArrowRight, CheckCircle2, Code2, Server, Database, Network, Box, Users, Brain } from 'lucide-react';
import { api } from '../services/api';

const SUBJECT_ICONS = {
  dsa: Code2,
  os: Server,
  dbms: Database,
  computer_networks: Network,
  oops: Box,
  hr_behavioral: Users,
  aptitude: Brain,
};

export default function SetupModeBPage() {
  const [subjects, setSubjects] = useState([]);
  const [selectedSubjects, setSelectedSubjects] = useState(['dsa', 'os']);
  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(true);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    api.getSubjects()
      .then((data) => {
        if (data && data.length > 0) {
          setSubjects(data);
        }
      })
      .catch(() => {})
      .finally(() => setFetching(false));
  }, []);

  const toggleSubject = (id) => {
    if (selectedSubjects.includes(id)) {
      if (selectedSubjects.length === 1) {
        setError('Please keep at least one subject selected.');
        return;
      }
      setSelectedSubjects(selectedSubjects.filter((s) => s !== id));
      setError('');
    } else {
      setSelectedSubjects([...selectedSubjects, id]);
      setError('');
    }
  };

  const handleStart = async () => {
    setLoading(true);
    setError('');
    try {
      const session = await api.startSession({
        mode: 'SUBJECT',
        subject_ids: selectedSubjects,
      });
      navigate(`/interview/${session.id}`);
    } catch (err) {
      setError(err.message || 'Failed to start subject interview session. Please sign in or try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container" style={{ maxWidth: '950px', padding: '3rem 1.5rem' }}>
      <div style={{ marginBottom: '2.5rem' }}>
        <div className="badge badge-cyan" style={{ marginBottom: '0.75rem' }}>
          <Layers size={14} /> Mode B: Subject Mastery Track
        </div>
        <h1 style={{ fontSize: '2.2rem', marginBottom: '0.5rem' }}>Core CS Subject Exam Drill</h1>
        <p style={{ color: 'var(--text-secondary)' }}>
          Select target core Computer Science subjects. Questions are dynamically generated using our blended knowledge pipeline and turn-by-turn difficulty scaling.
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
        }}>
          {error}
        </div>
      )}

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
        gap: '1.25rem',
        marginBottom: '2.5rem',
      }}>
        {subjects.map((sub) => {
          const isSelected = selectedSubjects.includes(sub.id);
          const Icon = SUBJECT_ICONS[sub.id] || Layers;
          const hasCoding = sub.id === 'dsa' || sub.id === 'oops';

          return (
            <div
              key={sub.id}
              onClick={() => toggleSubject(sub.id)}
              className="glass-card"
              style={{
                cursor: 'pointer',
                borderColor: isSelected ? 'var(--accent-cyan)' : 'var(--border-subtle)',
                background: isSelected ? 'rgba(6, 182, 212, 0.08)' : 'rgba(18, 26, 43, 0.5)',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
              }}
            >
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                  <div style={{
                    width: '42px',
                    height: '42px',
                    borderRadius: '10px',
                    background: isSelected ? 'rgba(6, 182, 212, 0.2)' : 'rgba(255, 255, 255, 0.05)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: isSelected ? 'var(--accent-cyan)' : 'var(--text-secondary)',
                  }}>
                    <Icon size={22} />
                  </div>
                  {isSelected && (
                    <div style={{ color: 'var(--accent-cyan)' }}>
                      <CheckCircle2 size={20} />
                    </div>
                  )}
                </div>

                <h3 style={{ fontSize: '1.15rem', marginBottom: '0.4rem', color: isSelected ? '#FFFFFF' : 'var(--text-primary)' }}>
                  {sub.name}
                </h3>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: '1.4' }}>
                  {sub.description}
                </p>
              </div>

              <div style={{ marginTop: '1.25rem', display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                <span className="badge badge-indigo" style={{ fontSize: '0.65rem' }}>
                  {sub.topics ? `${sub.topics.length} Topics` : 'Knowledge Grounded'}
                </span>
                {hasCoding && (
                  <span className="badge badge-emerald" style={{ fontSize: '0.65rem' }}>
                    <Code2 size={12} /> Spoken & Monaco
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
          Selected Track: <strong style={{ color: '#FFFFFF' }}>{selectedSubjects.length} subjects active</strong>
        </div>
        <button
          onClick={handleStart}
          disabled={loading || selectedSubjects.length === 0}
          className="btn btn-primary"
          style={{ padding: '0.9rem 2.25rem', background: 'linear-gradient(135deg, var(--accent-cyan) 0%, var(--accent-primary) 100%)' }}
        >
          {loading ? 'Launching Session...' : <>Start Adaptive Spoken Interview <ArrowRight size={18} /></>}
        </button>
      </div>
    </div>
  );
}
