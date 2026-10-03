import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';
import {
  Sparkles,
  Target,
  Layers,
  ArrowUpRight,
  CheckCircle2,
  TrendingUp,
  Award,
  AlertTriangle,
  BookOpen,
  Calendar,
  Clock,
  ArrowRight,
  BarChart2,
  Compass,
  Zap,
} from 'lucide-react';

export default function DashboardPage() {
  const { user } = useAuth();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    async function loadDashboard() {
      const token = localStorage.getItem('access_token');
      if (!token) {
        setLoading(false);
        return;
      }
      setLoading(true);
      setError('');
      try {
        const res = await api.getDashboard();
        setData(res);
      } catch (err) {
        console.error('Failed to load dashboard:', err);
        if (!err.message?.includes('401') && !err.message?.includes('Unauthorized')) {
          setError('Could not load analytics data. Please make sure the backend is active.');
        }
      } finally {
        setLoading(false);
      }
    }

    loadDashboard();
  }, [user]);


  const summary = data?.summary || {
    total_interviews: 0,
    completed_interviews: 0,
    total_questions_answered: 0,
    average_score: 7.2,
    tier_badge: 'Developing Competence',
    tracked_weak_topics: 0,
  };

  const progression = data?.score_progression || [];
  const radar = data?.rubric_radar || {
    technical_accuracy: 7.5,
    clarity: 8.0,
    completeness: 7.0,
    depth: 6.8,
  };
  const subjects = data?.subject_mastery || [];
  const heatmap = data?.weak_topic_heatmap || [];
  const sessions = data?.recent_sessions || [];

  return (
    <div className="app-container" style={{ padding: '2.5rem 1.5rem', minHeight: 'calc(100vh - 80px)' }}>
      {/* Hero Welcome Banner */}
      <div
        className="glass-panel"
        style={{
          padding: '2.5rem',
          marginBottom: '2rem',
          background: 'linear-gradient(135deg, rgba(18, 26, 43, 0.9) 0%, rgba(30, 41, 59, 0.7) 100%)',
          border: '1px solid rgba(99, 102, 241, 0.25)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '1.5rem',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.75rem' }}>
            <span className="badge badge-indigo">
              <Sparkles size={12} /> AdaptIQ Coach
            </span>
            <span className="badge badge-emerald">
              <Award size={12} /> {summary.tier_badge}
            </span>
          </div>
          <h1 style={{ fontSize: '2.2rem', marginBottom: '0.4rem', fontWeight: 700 }}>
            Welcome back, {user ? user.name : 'Candidate'}
          </h1>
          <p style={{ color: 'var(--text-secondary)', maxWidth: '650px', lineHeight: '1.5', fontSize: '0.95rem' }}>
            Track your mock interview progress, examine topic mastery heatmaps, and target foundational algorithmic weak points with adaptive difficulty scaling.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
          <Link to="/mode-select" className="btn btn-primary" style={{ padding: '0.85rem 1.75rem', fontSize: '0.95rem' }}>
            Start Mock Interview <ArrowUpRight size={18} />
          </Link>
        </div>
      </div>

      {error && (
        <div
          style={{
            padding: '1rem',
            background: 'rgba(239, 68, 68, 0.15)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            borderRadius: '10px',
            color: '#FCA5A5',
            marginBottom: '2rem',
          }}
        >
          {error}
        </div>
      )}

      {/* Guest Welcome Card if Not Signed In */}
      {!user && !localStorage.getItem('access_token') && (
        <div
          className="glass-panel"
          style={{
            padding: '1.25rem 1.75rem',
            marginBottom: '2rem',
            background: 'rgba(99, 102, 241, 0.08)',
            border: '1px solid rgba(99, 102, 241, 0.3)',
            borderRadius: '12px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: '1rem',
          }}
        >
          <div>
            <h4 style={{ fontSize: '1.05rem', fontWeight: 600, color: 'var(--accent-primary)', marginBottom: '0.25rem' }}>
              Sign in to save and track your interview progress
            </h4>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
              Create a free account or log in to track your personalized weak-topic heatmap, score growth trendlines, and session reports.
            </p>
          </div>
          <Link to="/auth" className="btn btn-primary" style={{ padding: '0.6rem 1.4rem', fontSize: '0.85rem' }}>
            Sign In / Sign Up &rarr;
          </Link>
        </div>
      )}


      {/* Top 4 Summary Cards */}
      <div className="grid-4" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))', gap: '1.25rem', marginBottom: '2rem' }}>
        <div className="glass-card" style={{ padding: '1.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
            <span style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>Interviews Taken</span>
            <div style={{ padding: '0.45rem', borderRadius: '8px', background: 'rgba(99, 102, 241, 0.15)', color: 'var(--accent-primary)' }}>
              <Layers size={18} />
            </div>
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 700, marginBottom: '0.2rem' }}>
            {summary.total_interviews}
          </div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            {summary.completed_interviews} fully completed sessions
          </div>
        </div>

        <div className="glass-card" style={{ padding: '1.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
            <span style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>Average Rubric Score</span>
            <div style={{ padding: '0.45rem', borderRadius: '8px', background: 'rgba(16, 185, 129, 0.15)', color: 'var(--accent-emerald)' }}>
              <TrendingUp size={18} />
            </div>
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 700, marginBottom: '0.2rem', color: 'var(--accent-emerald)' }}>
            {summary.average_score} <span style={{ fontSize: '1rem', color: 'var(--text-muted)' }}>/ 10</span>
          </div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            Turn-by-turn evaluator average
          </div>
        </div>

        <div className="glass-card" style={{ padding: '1.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
            <span style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>Questions Evaluated</span>
            <div style={{ padding: '0.45rem', borderRadius: '8px', background: 'rgba(6, 182, 212, 0.15)', color: 'var(--accent-cyan)' }}>
              <CheckCircle2 size={18} />
            </div>
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 700, marginBottom: '0.2rem' }}>
            {summary.total_questions_answered}
          </div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            Spoken & code answers analyzed
          </div>
        </div>

        <div className="glass-card" style={{ padding: '1.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
            <span style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>Identified Weak Areas</span>
            <div style={{ padding: '0.45rem', borderRadius: '8px', background: 'rgba(245, 158, 11, 0.15)', color: 'var(--accent-amber)' }}>
              <Target size={18} />
            </div>
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 700, marginBottom: '0.2rem', color: 'var(--accent-amber)' }}>
            {summary.tracked_weak_topics}
          </div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            Active targeted topics
          </div>
        </div>
      </div>

      {/* Analytics Charts Grid: Progression Trajectory & Rubric Radar */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(420px, 1fr))', gap: '1.5rem', marginBottom: '2rem' }}>
        {/* Score Progression Trajectory */}
        <div className="glass-panel" style={{ padding: '1.75rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
            <div>
              <h3 style={{ fontSize: '1.15rem', fontWeight: 600 }}>Performance Trajectory</h3>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>Session-over-session score trend</p>
            </div>
            <span className="badge badge-indigo">Growth Metric</span>
          </div>

          {progression.length > 0 ? (
            <div style={{ width: '100%', height: '220px', position: 'relative' }}>
              {/* SVG Area Chart */}
              <svg width="100%" height="100%" viewBox="0 0 460 200" preserveAspectRatio="none">
                <defs>
                  <linearGradient id="scoreGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#6366F1" stopOpacity="0.45" />
                    <stop offset="100%" stopColor="#6366F1" stopOpacity="0.0" />
                  </linearGradient>
                </defs>

                {/* Grid guidelines */}
                {[40, 80, 120, 160].map((y) => (
                  <line key={y} x1="30" y1={y} x2="440" y2={y} stroke="rgba(255,255,255,0.06)" strokeDasharray="3 3" />
                ))}

                {/* Build coordinates */}
                {(() => {
                  const points = progression.slice(-8).map((p, idx, arr) => {
                    const x = 40 + (idx / Math.max(1, arr.length - 1)) * 380;
                    const y = 170 - (p.score / 10) * 130;
                    return { x, y, score: p.score, date: p.date };
                  });

                  const lineD = points.reduce((acc, pt, i) => `${acc} ${i === 0 ? 'M' : 'L'} ${pt.x} ${pt.y}`, '');
                  const areaD = `${lineD} L ${points[points.length - 1]?.x || 420} 180 L 40 180 Z`;

                  return (
                    <>
                      <path d={areaD} fill="url(#scoreGrad)" />
                      <path d={lineD} fill="none" stroke="#6366F1" strokeWidth="3" strokeLinecap="round" />
                      {points.map((pt, i) => (
                        <g key={i}>
                          <circle cx={pt.x} cy={pt.y} r="5" fill="#06B6D4" stroke="#0D1322" strokeWidth="2" />
                          <text x={pt.x} y={pt.y - 10} fill="#E2E8F0" fontSize="10" textAnchor="middle">
                            {pt.score}
                          </text>
                        </g>
                      ))}
                    </>
                  );
                })()}
              </svg>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.5rem', padding: '0 1rem' }}>
                <span>Earlier Sessions</span>
                <span>Latest Session</span>
              </div>
            </div>
          ) : (
            <div style={{ height: '200px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>
              Complete mock interviews to view your trajectory trendline.
            </div>
          )}
        </div>

        {/* 4-Rubric Radar & Balance Card */}
        <div className="glass-panel" style={{ padding: '1.75rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
            <div>
              <h3 style={{ fontSize: '1.15rem', fontWeight: 600 }}>Rubric Balance Assessment</h3>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>Evaluation breakdown across 4 key criteria</p>
            </div>
            <span className="badge badge-cyan">Fine-Tuned Evaluator</span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '1rem', marginTop: '0.5rem' }}>
            <div style={{ background: 'rgba(255,255,255,0.03)', padding: '1rem', borderRadius: '10px', border: '1px solid var(--border-subtle)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: '0.4rem' }}>
                <span style={{ color: 'var(--text-secondary)' }}>Technical Accuracy</span>
                <strong style={{ color: '#06B6D4' }}>{radar.technical_accuracy}/10</strong>
              </div>
              <div style={{ width: '100%', height: '6px', background: 'rgba(255,255,255,0.08)', borderRadius: '3px', overflow: 'hidden' }}>
                <div style={{ width: `${(radar.technical_accuracy / 10) * 100}%`, height: '100%', background: 'linear-gradient(90deg, #06B6D4, #3B82F6)' }} />
              </div>
            </div>

            <div style={{ background: 'rgba(255,255,255,0.03)', padding: '1rem', borderRadius: '10px', border: '1px solid var(--border-subtle)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: '0.4rem' }}>
                <span style={{ color: 'var(--text-secondary)' }}>Clarity & Articulation</span>
                <strong style={{ color: '#10B981' }}>{radar.clarity}/10</strong>
              </div>
              <div style={{ width: '100%', height: '6px', background: 'rgba(255,255,255,0.08)', borderRadius: '3px', overflow: 'hidden' }}>
                <div style={{ width: `${(radar.clarity / 10) * 100}%`, height: '100%', background: 'linear-gradient(90deg, #10B981, #059669)' }} />
              </div>
            </div>

            <div style={{ background: 'rgba(255,255,255,0.03)', padding: '1rem', borderRadius: '10px', border: '1px solid var(--border-subtle)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: '0.4rem' }}>
                <span style={{ color: 'var(--text-secondary)' }}>Completeness</span>
                <strong style={{ color: '#8B5CF6' }}>{radar.completeness}/10</strong>
              </div>
              <div style={{ width: '100%', height: '6px', background: 'rgba(255,255,255,0.08)', borderRadius: '3px', overflow: 'hidden' }}>
                <div style={{ width: `${(radar.completeness / 10) * 100}%`, height: '100%', background: 'linear-gradient(90deg, #8B5CF6, #6366F1)' }} />
              </div>
            </div>

            <div style={{ background: 'rgba(255,255,255,0.03)', padding: '1rem', borderRadius: '10px', border: '1px solid var(--border-subtle)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: '0.4rem' }}>
                <span style={{ color: 'var(--text-secondary)' }}>Depth & Complexity</span>
                <strong style={{ color: '#F59E0B' }}>{radar.depth}/10</strong>
              </div>
              <div style={{ width: '100%', height: '6px', background: 'rgba(255,255,255,0.08)', borderRadius: '3px', overflow: 'hidden' }}>
                <div style={{ width: `${(radar.depth / 10) * 100}%`, height: '100%', background: 'linear-gradient(90deg, #F59E0B, #D97706)' }} />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Subject Mastery Progress Grid (7 Core CS Subjects) */}
      <div className="glass-panel" style={{ padding: '1.75rem', marginBottom: '2rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem', flexWrap: 'wrap', gap: '0.5rem' }}>
          <div>
            <h3 style={{ fontSize: '1.25rem', fontWeight: 600 }}>Core Computer Science Subjects Mastery</h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>Performance across the 7 foundational curriculum trees</p>
          </div>
          <Link to="/mode-select" className="btn btn-secondary" style={{ fontSize: '0.8rem', padding: '0.4rem 0.8rem' }}>
            Practice Subjects &rarr;
          </Link>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem' }}>
          {subjects.map((sub) => (
            <div
              key={sub.subject_id}
              style={{
                background: 'rgba(255, 255, 255, 0.02)',
                border: '1px solid var(--border-subtle)',
                borderRadius: '10px',
                padding: '1.2rem',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.6rem' }}>
                <h4 style={{ fontSize: '0.95rem', fontWeight: 600 }}>{sub.name}</h4>
                <span className="badge badge-indigo" style={{ fontSize: '0.75rem' }}>
                  {sub.mastery_pct}% Mastery
                </span>
              </div>

              <div style={{ width: '100%', height: '6px', background: 'rgba(255,255,255,0.06)', borderRadius: '3px', overflow: 'hidden', marginBottom: '0.6rem' }}>
                <div
                  style={{
                    width: `${sub.mastery_pct}%`,
                    height: '100%',
                    background:
                      sub.mastery_pct >= 70
                        ? 'linear-gradient(90deg, #10B981, #059669)'
                        : sub.mastery_pct >= 40
                        ? 'linear-gradient(90deg, #3B82F6, #06B6D4)'
                        : 'linear-gradient(90deg, #F59E0B, #EF4444)',
                  }}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                <span>{sub.questions_answered} questions attempted</span>
                <span>{sub.total_topics} topics in curriculum</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Weak-Topic Heatmap (Adaptive Learning Loop) */}
      <div className="glass-panel" style={{ padding: '1.75rem', marginBottom: '2rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem', flexWrap: 'wrap', gap: '0.5rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
              <h3 style={{ fontSize: '1.25rem', fontWeight: 600 }}>Targeted Weak-Topic Heatmap</h3>
              <span className="badge badge-amber" style={{ fontSize: '0.75rem' }}>Dynamic Profiling</span>
              <span className="badge badge-indigo" style={{ fontSize: '0.75rem' }}>Top 12 Priority Targets</span>
            </div>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
              Top priority topics flagged during interviews for reinforcement. The adaptive agent routes questions here when difficulty decreases.
            </p>
          </div>
        </div>

        {heatmap.length > 0 ? (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '1rem' }}>
            {heatmap.map((item) => {
              const isHighWeakness = item.weakness_level >= 3.5;
              const isMediumWeakness = item.weakness_level > 2.0 && item.weakness_level < 3.5;
              return (
                <div
                  key={item.topic_id}
                  style={{
                    background: isHighWeakness
                      ? 'rgba(239, 68, 68, 0.08)'
                      : isMediumWeakness
                      ? 'rgba(245, 158, 11, 0.08)'
                      : 'rgba(16, 185, 129, 0.08)',
                    border: `1px solid ${
                      isHighWeakness
                        ? 'rgba(239, 68, 68, 0.3)'
                        : isMediumWeakness
                        ? 'rgba(245, 158, 11, 0.3)'
                        : 'rgba(16, 185, 129, 0.3)'
                    }`,
                    borderRadius: '10px',
                    padding: '1.25rem',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                    <span
                      style={{
                        fontSize: '0.75rem',
                        fontWeight: 700,
                        textTransform: 'uppercase',
                        color: isHighWeakness ? '#EF4444' : isMediumWeakness ? '#F59E0B' : '#10B981',
                      }}
                    >
                      {item.status}
                    </span>
                    <span className="badge badge-indigo" style={{ fontSize: '0.7rem' }}>
                      Severity: {item.weakness_level}/5.0
                    </span>
                  </div>

                  <h4 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '0.35rem' }}>{item.name}</h4>
                  <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.75rem' }}>
                    Missed or low-scoring attempts: {item.failure_count}
                  </p>

                  <Link
                    to="/mode-select"
                    className="btn btn-secondary"
                    style={{ fontSize: '0.75rem', padding: '0.35rem 0.75rem', width: '100%', textAlign: 'center', display: 'block' }}
                  >
                    Drill This Topic &rarr;
                  </Link>
                </div>
              );
            })}
          </div>
        ) : (
          <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
            No weak topics recorded yet! Take a mock interview to generate personalized reinforcement targets.
          </div>
        )}
      </div>

      {/* Recent Sessions Table */}
      <div className="glass-panel" style={{ padding: '1.75rem' }}>
        <h3 style={{ fontSize: '1.25rem', fontWeight: 600, marginBottom: '1rem' }}>Past Interview Sessions</h3>
        {sessions.length > 0 ? (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.9rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-subtle)', color: 'var(--text-muted)' }}>
                  <th style={{ padding: '0.75rem' }}>Date</th>
                  <th style={{ padding: '0.75rem' }}>Mode</th>
                  <th style={{ padding: '0.75rem' }}>Turns Completed</th>
                  <th style={{ padding: '0.75rem' }}>Score</th>
                  <th style={{ padding: '0.75rem' }}>Status</th>
                  <th style={{ padding: '0.75rem', textAlign: 'right' }}>Report</th>
                </tr>
              </thead>
              <tbody>
                {sessions.map((s) => (
                  <tr key={s.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                    <td style={{ padding: '0.75rem' }}>{s.created_at}</td>
                    <td style={{ padding: '0.75rem' }}>
                      <span className={s.mode === 'RESUME_JD' ? 'badge badge-indigo' : 'badge badge-cyan'}>
                        {s.mode === 'RESUME_JD' ? 'Resume + JD Gap' : 'CS Subjects'}
                      </span>
                    </td>
                    <td style={{ padding: '0.75rem' }}>
                      {s.turns_taken} of {s.max_turns}
                    </td>
                    <td style={{ padding: '0.75rem' }}>
                      {s.overall_score !== null ? (
                        <span style={{ fontWeight: 700, color: s.overall_score >= 7.0 ? 'var(--accent-emerald)' : '#F59E0B' }}>
                          {s.overall_score} / 10.0
                        </span>
                      ) : (
                        <span style={{ color: 'var(--text-muted)' }}>In Progress</span>
                      )}
                    </td>
                    <td style={{ padding: '0.75rem' }}>
                      <span className={s.status === 'completed' ? 'badge badge-emerald' : 'badge badge-amber'}>
                        {s.status}
                      </span>
                    </td>
                    <td style={{ padding: '0.75rem', textAlign: 'right' }}>
                      <Link to={`/report/${s.id}`} className="btn btn-secondary" style={{ fontSize: '0.75rem', padding: '0.35rem 0.75rem' }}>
                        View Report &rarr;
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
            No past sessions recorded yet. Start your first mock interview above!
          </div>
        )}
      </div>
    </div>
  );
}
