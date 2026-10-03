import React, { createContext, useContext, useState, useEffect } from 'react';
import { api } from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(() => localStorage.getItem('access_token'));
  const [loading, setLoading] = useState(() => !!localStorage.getItem('access_token'));

  useEffect(() => {
    let isMounted = true;
    async function loadUser() {
      if (token) {
        try {
          const userData = await api.getMe();
          if (isMounted) setUser(userData);
        } catch (err) {
          console.warn('Session expired or invalid token:', err);
          if (isMounted) logout();
        }
      }
      if (isMounted) setLoading(false);
    }
    loadUser();
    return () => {
      isMounted = false;
    };
  }, [token]);

  const login = async (email, password) => {
    const res = await api.login(email, password);
    localStorage.setItem('access_token', res.access_token);
    setToken(res.access_token);
    setUser(res.user);
    setLoading(false);
    return res.user;
  };

  const signup = async (name, email, password) => {
    const res = await api.signup(name, email, password);
    localStorage.setItem('access_token', res.access_token);
    setToken(res.access_token);
    setUser(res.user);
    setLoading(false);
    return res.user;
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    setToken(null);
    setUser(null);
    setLoading(false);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!user,
        loading,
        login,
        signup,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
