import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';
import { Mic, LogOut, User as UserIcon, Sparkles, LayoutDashboard } from 'lucide-react';

export default function Navbar() {
  const { user, isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();
  const [health, setHealth] = useState(null);

  useEffect(() => {
    api.checkHealth()
      .then(setHealth)
      .catch(() => setHealth({ status: 'offline' }));
  }, []);

  const handleLogout = () => {
    logout();
    navigate('/auth');
  };

  return (
    <header style={{
      borderBottom: '1px solid var(--border-subtle)',
      background: 'rgba(7, 11, 18, 0.85)',
      backdropFilter: 'blur(12px)',
      position: 'sticky',
      top: 0,
      zIndex: 50,
    }}>
      <div className="app-container" style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        paddingTop: '1rem',
        paddingBottom: '1rem',
      }}>
        {/* Brand */}
        <Link to="/" style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.75rem',
          textDecoration: 'none',
        }}>
          <div style={{
            width: '38px',
            height: '38px',
            borderRadius: '10px',
            background: 'linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 0 15px rgba(99, 102, 241, 0.4)',
          }}>
            <Mic size={20} color="#FFFFFF" />
          </div>
          <div>
            <span style={{
              fontFamily: 'var(--font-heading)',
              fontWeight: 800,
              fontSize: '1.2rem',
              color: '#FFFFFF',
              letterSpacing: '-0.02em',
            }}>
              Adapt<span style={{ color: 'var(--accent-primary)' }}>IQ</span>
            </span>
            <span className="badge badge-indigo" style={{ marginLeft: '0.5rem', fontSize: '0.65rem' }}>
              v2.0
            </span>
          </div>
        </Link>

        {/* Backend health status badge */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            padding: '0.35rem 0.75rem',
            borderRadius: '20px',
            background: 'rgba(18, 26, 43, 0.6)',
            border: '1px solid var(--border-subtle)',
            fontSize: '0.8rem',
            color: 'var(--text-secondary)',
          }}>
            <span style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              backgroundColor: health?.status === 'healthy' ? 'var(--accent-emerald)' : 'var(--accent-rose)',
              boxShadow: health?.status === 'healthy' ? '0 0 8px var(--accent-emerald)' : 'none',
              display: 'inline-block',
            }} />
            <span>
              {health?.status === 'healthy' ? `${health.database?.type || 'Online'}` : 'Backend Connecting...'}
            </span>
          </div>

          {/* User profile / Auth buttons */}
          {isAuthenticated ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <Link to="/" className="btn btn-secondary" style={{ padding: '0.5rem 0.9rem', fontSize: '0.85rem' }}>
                <LayoutDashboard size={15} /> Dashboard
              </Link>
              <Link to="/mode-select" className="btn btn-primary" style={{ padding: '0.5rem 1rem', fontSize: '0.85rem' }}>
                <Sparkles size={15} /> Start Interview
              </Link>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-primary)', fontSize: '0.9rem' }}>
                <UserIcon size={16} color="var(--accent-cyan)" />
                <span>{user?.name}</span>
              </div>
              <button onClick={handleLogout} className="btn btn-secondary" style={{ padding: '0.5rem 0.85rem', fontSize: '0.85rem' }}>
                <LogOut size={15} /> Logout
              </button>
            </div>
          ) : (
            <div style={{ display: 'flex', gap: '0.75rem' }}>
              <Link to="/auth" className="btn btn-primary" style={{ padding: '0.5rem 1.25rem', fontSize: '0.9rem' }}>
                Sign In / Sign Up
              </Link>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
