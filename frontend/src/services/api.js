const BACKEND_URL = import.meta.env.VITE_API_URL || '';
const API_BASE = `${BACKEND_URL}/api/v1`;

async function request(endpoint, options = {}) {
  const token = localStorage.getItem('access_token');
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
    ...options.headers,
  };

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Network request failed' }));
    throw new Error(errorData.detail || `Request failed with status ${response.status}`);
  }

  return response.json();
}

export const api = {
  // System
  checkHealth: async () => {
    const res = await fetch(`${BACKEND_URL}/health`);
    return res.json();
  },

  // Auth
  signup: (name, email, password) =>
    request('/auth/signup', {
      method: 'POST',
      body: JSON.stringify({ name, email, password }),
    }),

  login: (email, password) =>
    request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),

  getMe: () => request('/auth/me'),

  // Subjects & Topics
  getSubjects: () => request('/subjects'),
  getSubjectTopics: (subjectId) => request(`/subjects/${subjectId}/topics`),

  // Resume & JD
  uploadResume: async (formData) => {
    const token = localStorage.getItem('access_token');
    const response = await fetch(`${API_BASE}/resume/upload`, {
      method: 'POST',
      headers: {
        ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
      },
      body: formData,
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({ detail: 'Upload failed' }));
      throw new Error(err.detail || 'Resume upload failed');
    }
    return response.json();
  },

  submitJD: (raw_text) =>
    request('/jd/submit', {
      method: 'POST',
      body: JSON.stringify({ raw_text }),
    }),

  uploadJD: async (formData) => {
    const token = localStorage.getItem('access_token');
    const response = await fetch(`${API_BASE}/jd/upload`, {
      method: 'POST',
      headers: {
        ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
      },
      body: formData,
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({ detail: 'Upload failed' }));
      throw new Error(err.detail || 'Job description upload failed');
    }
    return response.json();
  },

  runGapAnalysis: (resume_id, jd_id) =>
    request('/jd/gap-analysis', {
      method: 'POST',
      body: JSON.stringify({ resume_id, jd_id }),
    }),

  // Interview Sessions
  startSession: (data) =>
    request('/session/start', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  submitAnswer: (sessionId, data) =>
    request(`/session/${sessionId}/answer`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  getSessionState: (sessionId) =>
    request(`/session/${sessionId}/state`),

  getCurrentQuestion: (sessionId) =>
    request(`/session/${sessionId}/current-question`),

  getSessionReport: (sessionId) =>
    request(`/session/${sessionId}/report`),

  runCode: (codeContent, codeLanguage = 'python', stdinInput = '', answerMode = 'full_code', questionText = '', topicName = '') =>
    request('/session/run-code', {
      method: 'POST',
      body: JSON.stringify({
        code_content: codeContent,
        code_language: codeLanguage,
        stdin_input: stdinInput,
        answer_mode: answerMode,
        question_text: questionText,
        topic_name: topicName,
      }),
    }),


  // Voice Layer
  transcribeAudio: async (audioBlob, promptContext = '') => {
    const token = localStorage.getItem('access_token');
    const formData = new FormData();
    formData.append('audio_file', audioBlob, 'candidate_response.webm');
    if (promptContext) {
      formData.append('prompt_context', promptContext);
    }

    const response = await fetch(`${API_BASE}/voice/transcribe`, {
      method: 'POST',
      headers: {
        ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
      },
      body: formData,
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({ detail: 'Voice transcription failed' }));
      throw new Error(err.detail || 'Voice transcription failed');
    }

    return response.json();
  },

  // Analytics & Candidate Dashboard
  getDashboard: () => request('/analytics/dashboard'),

  getSessions: () => request('/analytics/sessions'),

  exportSessionReport: async (sessionId) => {
    const token = localStorage.getItem('access_token');
    const response = await fetch(`${API_BASE}/analytics/session/${sessionId}/export`, {
      headers: {
        ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
      },
    });
    if (!response.ok) {
      throw new Error('Failed to export session report');
    }
    return response.text();
  },
};


