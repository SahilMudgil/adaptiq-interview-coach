import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import Editor from '@monaco-editor/react';
import {
  Mic,
  MicOff,
  Code2,
  Headphones,
  Sparkles,
  Send,
  Volume2,
  VolumeX,
  Play,
  Square,
  RotateCcw,
  ArrowRight,
  CheckCircle2,
  AlertCircle,
  Clock,
  Database,
  Radio,
  Sliders,
} from 'lucide-react';
import { api } from '../services/api';
import QuestionPresentation from '../components/QuestionPresentation';

const LANGUAGE_STARTERS = {
  python: 'def solution():\n    # Write your solution here\n    print("Running Python solution...")\n\nsolution()\n',
  javascript: 'function solution() {\n    // Write your solution here\n    console.log("Running JavaScript solution...");\n}\n\nsolution();\n',
  cpp: '#include <iostream>\n#include <vector>\n#include <algorithm>\nusing namespace std;\n\nclass Solution {\npublic:\n    void solve() {\n        cout << "Running C++ solution..." << endl;\n    }\n};\n\nint main() {\n    Solution sol;\n    sol.solve();\n    return 0;\n}\n',
  java: 'public class Solution {\n    public static void solve() {\n        System.out.println("Running Java solution...");\n    }\n\n    public static void main(String[] args) {\n        solve();\n    }\n}\n',
  c: '#include <stdio.h>\n\nvoid solve() {\n    printf("Running C solution...\\n");\n}\n\nint main() {\n    solve();\n    return 0;\n}\n',
  sql: '-- Write your SQL query here\n',
  pseudocode: '// Write your algorithmic pseudocode here\n\n',
};

export const isSqlProblem = (q) => {
  if (!q) return false;
  const topic = (q.topic_id || '').toLowerCase();
  const text = (q.question_text || '').toLowerCase();
  if (topic === 'dbms_sql_queries' || topic.includes('sql')) return true;
  if (text.includes('write an sql query') || text.includes('write a query') || text.includes('sql query')) return true;
  return false;
};


export default function InterviewPage() {
  const { sessionId } = useParams();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [currentQuestion, setCurrentQuestion] = useState(null);
  const [questionType, setQuestionType] = useState('conceptual'); // 'conceptual' | 'coding'
  const [turnCount, setTurnCount] = useState(1);
  const [maxTurns, setMaxTurns] = useState(5);

  // Conceptual Answer State
  const [answerText, setAnswerText] = useState('');

  // Coding Answer State
  const [codeLanguage, setCodeLanguage] = useState('python');
  const [answerMode, setAnswerMode] = useState('full_code'); // 'full_code' | 'pseudocode'
  const [codeContent, setCodeContent] = useState(LANGUAGE_STARTERS.python);
  const [spokenNarration, setSpokenNarration] = useState('');
  const [isRunningCode, setIsRunningCode] = useState(false);
  const [executionResult, setExecutionResult] = useState(null);


  // Voice Recording & STT State
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTarget, setRecordingTarget] = useState('conceptual'); // 'conceptual' | 'coding'
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [whisperStats, setWhisperStats] = useState(null); // { latency_ms, duration_seconds }
  const [audioLevel, setAudioLevel] = useState(0);

  // Text-to-Speech (TTS) State
  const [isSpeakingQuestion, setIsSpeakingQuestion] = useState(false);
  const [autoSpeakQuestion, setAutoSpeakQuestion] = useState(true);
  const [ttsRate, setTtsRate] = useState(1.0);

  // Turn Feedback State
  const [lastEvaluation, setLastEvaluation] = useState(null);
  const [showFeedbackModal, setShowFeedbackModal] = useState(false);
  const [error, setError] = useState('');

  // Audio Refs
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const audioStreamRef = useRef(null);
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const animFrameRef = useRef(null);
  const canvasRef = useRef(null);

  // -------------------------------------------------------------
  // Text-To-Speech (AI Interviewer Voice)
  // -------------------------------------------------------------
  const speakText = (text) => {
    if (!('speechSynthesis' in window)) return;
    window.speechSynthesis.cancel();

    if (!text) return;

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = ttsRate;
    utterance.pitch = 1.0;

    // Pick natural English voice if available
    const voices = window.speechSynthesis.getVoices();
    const naturalVoice =
      voices.find((v) => v.name.includes('Natural') || v.name.includes('Google UK English Male') || v.name.includes('Samantha') || v.name.includes('Daniel')) ||
      voices.find((v) => v.lang.startsWith('en'));
    if (naturalVoice) {
      utterance.voice = naturalVoice;
    }

    utterance.onstart = () => setIsSpeakingQuestion(true);
    utterance.onend = () => setIsSpeakingQuestion(false);
    utterance.onerror = () => setIsSpeakingQuestion(false);

    window.speechSynthesis.speak(utterance);
  };

  const stopSpeaking = () => {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      setIsSpeakingQuestion(false);
    }
  };

  // -------------------------------------------------------------
  // Fetch initial session & current question
  // -------------------------------------------------------------
  useEffect(() => {
    async function initSession() {
      setLoading(true);
      setError('');
      try {
        const token = localStorage.getItem('access_token');
        const headers = { Authorization: `Bearer ${token}` };

        // 1. Load session state
        try {
          const s = await api.getSessionState(sessionId);
          const st = s?.state || {};
          setTurnCount((st.turns_taken || 0) + 1);
          setMaxTurns(st.max_turns || 5);
        } catch (stateErr) {
          console.warn('Could not load session state:', stateErr);
        }

        // 2. Load active question
        const qData = await api.getCurrentQuestion(sessionId);
        if (qData) {
          setCurrentQuestion(qData);

          // Determine question mode: safeguard against any questions with spoken conceptual intent
          let determinedType = qData.question_type || 'conceptual';
          const lowerQText = (qData.question_text || '').toLowerCase();
          if (
            lowerQText.startsWith('spoken conceptual question') ||
            lowerQText.startsWith('conceptual question') ||
            lowerQText.startsWith('spoken question') ||
            (!lowerQText.includes('problem statement') && (lowerQText.startsWith('explain ') || lowerQText.startsWith('describe ') || lowerQText.startsWith('what is ')))
          ) {
            determinedType = 'conceptual';
          }
          setQuestionType(determinedType);

          // Auto-detect SQL question only if question is coding mode
          if (determinedType === 'coding') {
            const isSql = isSqlProblem(qData);
            const targetLang = isSql ? 'sql' : 'python';
            setCodeLanguage(targetLang);
            setCodeContent(LANGUAGE_STARTERS[targetLang] || '');
          }

          if (autoSpeakQuestion && qData.question_text) {
            setTimeout(() => speakText(qData.question_text), 400);
          }
        }
      } catch (err) {
        console.warn('Could not load session data:', err);
      } finally {
        setLoading(false);
      }
    }

    initSession();

    return () => {
      stopSpeaking();
      cleanupAudioNodes();
    };
  }, [sessionId]);

  const cleanupAudioNodes = () => {
    if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    if (audioStreamRef.current) {
      audioStreamRef.current.getTracks().forEach((track) => track.stop());
      audioStreamRef.current = null;
    }
    if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
      audioContextRef.current.close().catch(() => {});
      audioContextRef.current = null;
    }
  };

  // -------------------------------------------------------------
  // Speech-To-Text (MediaRecorder + Web Audio API Analyser)
  // -------------------------------------------------------------
  const startRecording = async (target = 'conceptual') => {
    try {
      setError('');
      setRecordingTarget(target);
      audioChunksRef.current = [];

      // Stop interviewer speech when candidate begins talking
      stopSpeaking();

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioStreamRef.current = stream;

      // Realtime Audio Visualizer with Web Audio API
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      const audioCtx = new AudioCtx();
      audioContextRef.current = audioCtx;

      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 64;
      analyserRef.current = analyser;

      const source = audioCtx.createMediaStreamSource(stream);
      source.connect(analyser);

      // Draw real-time audio waveform / frequency bars
      const renderWaveform = () => {
        if (!analyserRef.current || !canvasRef.current) return;
        const canvas = canvasRef.current;
        const ctx = canvas.getContext('2d');
        const bufferLength = analyserRef.current.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);
        analyserRef.current.getByteFrequencyData(dataArray);

        // Average level
        const avg = dataArray.reduce((acc, v) => acc + v, 0) / bufferLength;
        setAudioLevel(Math.min(100, Math.round(avg * 1.5)));

        ctx.clearRect(0, 0, canvas.width, canvas.height);
        const barWidth = (canvas.width / bufferLength) * 2;
        let x = 0;

        for (let i = 0; i < bufferLength; i++) {
          const barHeight = (dataArray[i] / 255) * canvas.height;
          // Gradient bar
          const gradient = ctx.createLinearGradient(0, canvas.height, 0, 0);
          gradient.addColorStop(0, '#6366F1');
          gradient.addColorStop(1, '#06B6D4');
          ctx.fillStyle = gradient;
          ctx.fillRect(x, canvas.height - barHeight, barWidth - 2, barHeight);
          x += barWidth;
        }

        animFrameRef.current = requestAnimationFrame(renderWaveform);
      };
      renderWaveform();

      // MediaRecorder for Groq Whisper
      const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
        ? 'audio/webm;codecs=opus'
        : 'audio/webm';
      const recorder = new MediaRecorder(stream, { mimeType });
      mediaRecorderRef.current = recorder;

      recorder.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) {
          audioChunksRef.current.push(e.data);
        }
      };

      recorder.onstop = async () => {
        cleanupAudioNodes();
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        if (audioBlob.size > 500) {
          await transcribeRecordedAudio(audioBlob, target);
        }
      };

      recorder.start(250); // Slice chunks every 250ms
      setIsRecording(true);
    } catch (err) {
      console.error('Microphone error:', err);
      setError('Microphone access denied or audio device not found. You can still type your response.');
      setIsRecording(false);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    }
    setIsRecording(false);
    setAudioLevel(0);
  };

  const transcribeRecordedAudio = async (blob, target) => {
    setIsTranscribing(true);
    setError('');
    try {
      const promptContext = currentQuestion?.topic_id || 'Computer Science Technical Interview';
      const result = await api.transcribeAudio(blob, promptContext);

      if (result.success && result.transcript) {
        setWhisperStats({
          latency_ms: result.latency_ms,
          duration_seconds: result.duration_seconds || 0,
        });

        if (target === 'coding') {
          setSpokenNarration((prev) => (prev ? `${prev} ${result.transcript}` : result.transcript));
        } else {
          setAnswerText((prev) => (prev ? `${prev} ${result.transcript}` : result.transcript));
        }
      } else if (result.error) {
        setError(`Transcription note: ${result.error}`);
      }
    } catch (err) {
      console.error('Transcription failed:', err);
      setError('Audio transcription failed. Please check network connection or type manually.');
    } finally {
      setIsTranscribing(false);
    }
  };

  // -------------------------------------------------------------
  // Language & Mode Handlers
  // -------------------------------------------------------------
  const handleLanguageChange = (lang) => {
    setCodeLanguage(lang);
    setExecutionResult(null);
    if (!codeContent || Object.values(LANGUAGE_STARTERS).includes(codeContent)) {
      setCodeContent(LANGUAGE_STARTERS[lang] || '');
    }
  };

  const handleRunCode = async () => {
    if (!codeContent || !codeContent.trim()) return;
    setIsRunningCode(true);
    setExecutionResult(null);
    try {
      const res = await api.runCode(
        codeContent,
        codeLanguage,
        '',
        answerMode,
        currentQuestion?.question_text || '',
        currentQuestion?.topic_id || ''
      );
      setExecutionResult(res);
    } catch (err) {
      setExecutionResult({
        status: 'error',
        error: err.message || 'Execution failed',
        output: '',
        execution_time_ms: 0,
      });
    } finally {
      setIsRunningCode(false);
    }
  };


  const handleSubmitAnswer = async (e) => {
    if (e) e.preventDefault();
    if (isRecording) stopRecording();
    stopSpeaking();

    const isCoding = questionType === 'coding';
    const submissionBody = isCoding ? codeContent : answerText;

    if (!submissionBody || submissionBody.trim().length < 5) {
      setError(isCoding ? 'Please write code in the editor before submitting.' : 'Please provide an answer before submitting.');
      return;
    }

    setSubmitting(true);
    setError('');

    try {
      const payload = {
        transcript_text: isCoding ? spokenNarration : answerText,
        code_submission: isCoding ? codeContent : '',
        code_language: codeLanguage,
        answer_mode: isCoding ? answerMode : 'conceptual',
      };

      const res = await api.submitAnswer(sessionId, payload);
      setLastEvaluation(res.evaluation);
      setShowFeedbackModal(true);

      if (res.is_completed) {
        setTimeout(() => {
          navigate(`/report/${sessionId}`);
        }, 3500);
      } else if (res.next_question) {
        setCurrentQuestion(res.next_question);

        // Determine question mode: safeguard against questions with spoken conceptual intent
        let determinedType = res.next_question.question_type || 'conceptual';
        const lowerQText = (res.next_question.question_text || '').toLowerCase();
        if (
          lowerQText.startsWith('spoken conceptual question') ||
          lowerQText.startsWith('conceptual question') ||
          lowerQText.startsWith('spoken question') ||
          (!lowerQText.includes('problem statement') && (lowerQText.startsWith('explain ') || lowerQText.startsWith('describe ') || lowerQText.startsWith('what is ')))
        ) {
          determinedType = 'conceptual';
        }
        setQuestionType(determinedType);
        setTurnCount((prev) => prev + 1);
        setAnswerText('');
        setSpokenNarration('');
        setWhisperStats(null);
        setExecutionResult(null);

        // Configure code editor if next question is coding mode
        if (determinedType === 'coding') {
          const isSql = isSqlProblem(res.next_question);
          const targetLang = isSql ? 'sql' : (codeLanguage === 'sql' ? 'python' : codeLanguage);
          setCodeLanguage(targetLang);
          setCodeContent(LANGUAGE_STARTERS[targetLang] || '');
        }

        if (autoSpeakQuestion && res.next_question.question_text) {
          setTimeout(() => speakText(res.next_question.question_text), 800);
        }
      }
    } catch (err) {
      setError(err.message || 'Failed to submit answer.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="app-container" style={{ padding: '2rem 1.5rem', minHeight: 'calc(100vh - 80px)' }}>
      {/* Session Top Bar */}
      <div
        className="glass-panel"
        style={{
          padding: '1rem 1.5rem',
          marginBottom: '1.5rem',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '1rem',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
          <span className="badge badge-indigo">Turn {turnCount} of {maxTurns}</span>
          <span className="badge badge-amber">Difficulty Level {currentQuestion?.difficulty || 2}/5</span>
          <span className={questionType === 'coding' ? 'badge badge-emerald' : 'badge badge-cyan'}>
            {questionType === 'coding' ? 'Monaco Code Editor' : 'Voice-First Conceptual Call'}
          </span>
          <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
            Topic: {currentQuestion?.topic_id?.replace(/_/g, ' ') || 'Technical Interview'}
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          {/* Developer / Mode switcher */}
          <button
            onClick={() => {
              const newType = questionType === 'conceptual' ? 'coding' : 'conceptual';
              setQuestionType(newType);
              if (newType === 'coding') {
                const isSql = isSqlProblem(currentQuestion);
                const targetLang = isSql ? 'sql' : (codeLanguage === 'sql' ? 'python' : codeLanguage);
                setCodeLanguage(targetLang);
                setCodeContent(LANGUAGE_STARTERS[targetLang] || '');
              }
            }}
            className="btn btn-secondary"
            style={{ fontSize: '0.8rem', padding: '0.4rem 0.8rem' }}
          >
            Switch to {questionType === 'conceptual' ? 'Coding Mode' : 'Voice Mode'}
          </button>
          <Link to={`/report/${sessionId}`} className="btn btn-danger" style={{ fontSize: '0.8rem', padding: '0.4rem 0.8rem' }}>
            End Interview
          </Link>
        </div>
      </div>

      {error && (
        <div
          style={{
            padding: '0.85rem 1rem',
            background: 'rgba(239, 68, 68, 0.15)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            borderRadius: '10px',
            color: '#FCA5A5',
            marginBottom: '1.5rem',
            fontSize: '0.9rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
          }}
        >
          <AlertCircle size={18} /> {error}
        </div>
      )}

      {/* Main Question Display & AI Interviewer Voice Avatar */}
      <div
        className="glass-panel"
        style={{
          padding: '1.75rem',
          marginBottom: '1.5rem',
          borderLeft: '4px solid var(--accent-primary)',
          position: 'relative',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem', flexWrap: 'wrap', gap: '0.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <span
              style={{
                fontSize: '0.8rem',
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
                color: 'var(--accent-primary)',
                fontWeight: 700,
              }}
            >
              Interviewer (AI Voice Agent)
            </span>
            {isSpeakingQuestion && (
              <span className="badge badge-emerald" style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.7rem' }}>
                <Radio size={12} className="spin-slow" /> Speaking aloud...
              </span>
            )}
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            {/* TTS Audio Controls */}
            {isSpeakingQuestion ? (
              <button
                onClick={stopSpeaking}
                className="btn btn-secondary"
                style={{ padding: '0.3rem 0.6rem', fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.3rem' }}
                title="Mute Question"
              >
                <VolumeX size={14} color="#EF4444" /> Mute
              </button>
            ) : (
              <button
                onClick={() => speakText(currentQuestion?.question_text)}
                className="btn btn-secondary"
                style={{ padding: '0.3rem 0.6rem', fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.3rem' }}
                title="Read Question Aloud"
              >
                <Volume2 size={14} color="#06B6D4" /> Read Aloud
              </button>
            )}

            <label style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', fontSize: '0.75rem', color: 'var(--text-muted)', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={autoSpeakQuestion}
                onChange={(e) => setAutoSpeakQuestion(e.target.checked)}
                style={{ cursor: 'pointer' }}
              />
              Auto-read
            </label>

            <span className="badge badge-cyan" style={{ fontSize: '0.7rem' }}>
              Source: {currentQuestion?.source_mix || 'Blended RAG'}
            </span>
          </div>
        </div>

        <QuestionPresentation
          questionText={currentQuestion?.question_text}
          questionType={questionType}
          topicId={currentQuestion?.topic_id}
        />

        {/* Real-time speech speed tuner */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginTop: '0.75rem', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
          <span>Voice Speed:</span>
          {[0.9, 1.0, 1.15, 1.25].map((spd) => (
            <button
              key={spd}
              onClick={() => setTtsRate(spd)}
              style={{
                background: ttsRate === spd ? 'var(--accent-primary)' : 'rgba(255,255,255,0.06)',
                border: 'none',
                color: ttsRate === spd ? '#FFFFFF' : 'var(--text-secondary)',
                borderRadius: '4px',
                padding: '0.15rem 0.45rem',
                fontSize: '0.7rem',
                cursor: 'pointer',
              }}
            >
              {spd}x
            </button>
          ))}
        </div>
      </div>

      {/* Turn Evaluation Feedback Card */}
      {showFeedbackModal && lastEvaluation && (
        <div
          className="glass-panel"
          style={{
            padding: '1.5rem',
            marginBottom: '1.5rem',
            background: 'rgba(16, 185, 129, 0.08)',
            border: '1px solid rgba(16, 185, 129, 0.3)',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--accent-emerald)', fontWeight: 700 }}>
              <CheckCircle2 size={20} /> Turn Evaluation: {lastEvaluation.score} / 10.0
            </div>
            <button onClick={() => setShowFeedbackModal(false)} className="btn btn-primary" style={{ padding: '0.35rem 0.85rem', fontSize: '0.8rem' }}>
              Continue &rarr;
            </button>
          </div>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', lineHeight: '1.5', marginBottom: '0.75rem' }}>
            {lastEvaluation.feedback_text}
          </p>
          {lastEvaluation.sub_scores_json && (
            <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              {Object.entries(lastEvaluation.sub_scores_json).map(([k, v]) => (
                <span key={k}>
                  {k.replace('_', ' ')}: <strong style={{ color: 'var(--text-primary)' }}>{v}/10</strong>
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Dynamic Interaction Panel: Conceptual Voice UI vs Monaco Code Editor */}
      {questionType === 'conceptual' ? (
        /* Conceptual Spoken Call UI */
        <div
          className="glass-panel"
          style={{
            padding: '2.5rem 2rem',
            textAlign: 'center',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            minHeight: '380px',
            position: 'relative',
          }}
        >
          {/* Animated Glowing Voice Orb & Live Mic Visualizer */}
          <div style={{ position: 'relative', marginBottom: '1.5rem' }}>
            <div
              onClick={() => (isRecording ? stopRecording() : startRecording('conceptual'))}
              style={{
                width: '110px',
                height: '110px',
                borderRadius: '50%',
                background: isRecording
                  ? 'linear-gradient(135deg, #EF4444 0%, #DC2626 100%)'
                  : 'linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                cursor: 'pointer',
                boxShadow: isRecording
                  ? `0 0 ${25 + audioLevel}px rgba(239, 68, 68, 0.7)`
                  : '0 0 25px rgba(99, 102, 241, 0.5)',
                transition: 'all 0.15s ease',
                userSelect: 'none',
              }}
            >
              {isRecording ? <MicOff size={44} color="#FFFFFF" /> : <Mic size={44} color="#FFFFFF" />}
            </div>

            {/* Audio Waveform Canvas overlay while recording */}
            <canvas
              ref={canvasRef}
              width={160}
              height={36}
              style={{
                display: isRecording ? 'block' : 'none',
                position: 'absolute',
                bottom: '-28px',
                left: '50%',
                transform: 'translateX(-50%)',
                borderRadius: '6px',
                background: 'rgba(0,0,0,0.3)',
              }}
            />
          </div>

          <h3 style={{ fontSize: '1.3rem', marginBottom: '0.4rem', fontWeight: 600 }}>
            {isRecording
              ? 'Listening... Speak your answer aloud'
              : isTranscribing
              ? 'Transcribing speech with Groq Whisper...'
              : 'Click microphone to speak your answer'}
          </h3>

          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', maxWidth: '540px', marginBottom: '1.25rem' }}>
            {isRecording
              ? 'Your speech is being recorded with real-time waveform analysis. Click again when you are done speaking.'
              : 'Explain your reasoning naturally as if on a live voice call. Speech is automatically transcribed into high-fidelity technical text.'}
          </p>

          {/* Whisper transcription latency badge */}
          {whisperStats && (
            <div style={{ marginBottom: '1rem', display: 'flex', gap: '0.5rem', justifyContent: 'center' }}>
              <span className="badge badge-emerald" style={{ fontSize: '0.75rem' }}>
                Whisper Transcribed in {whisperStats.latency_ms}ms
              </span>
              {whisperStats.duration_seconds > 0 && (
                <span className="badge badge-indigo" style={{ fontSize: '0.75rem' }}>
                  Duration: {whisperStats.duration_seconds.toFixed(1)}s
                </span>
              )}
            </div>
          )}

          <div style={{ width: '100%', maxWidth: '680px', textAlign: 'left' }}>
            <textarea
              className="textarea-field"
              rows={4}
              placeholder="Your transcribed speech will appear here, or you can type directly..."
              value={answerText}
              onChange={(e) => setAnswerText(e.target.value)}
            />
          </div>

          <div style={{ display: 'flex', gap: '1rem', marginTop: '1.25rem', alignItems: 'center' }}>
            {isRecording ? (
              <button onClick={stopRecording} className="btn btn-danger" style={{ padding: '0.8rem 2rem' }}>
                <MicOff size={16} /> Stop Speaking & Transcribe
              </button>
            ) : (
              <button
                onClick={() => startRecording('conceptual')}
                disabled={isTranscribing}
                className="btn btn-secondary"
                style={{ padding: '0.8rem 1.8rem' }}
              >
                <Mic size={16} /> Start Speaking
              </button>
            )}

            <button
              onClick={handleSubmitAnswer}
              disabled={submitting || isRecording || isTranscribing}
              className="btn btn-primary"
              style={{ padding: '0.8rem 2.25rem' }}
            >
              {submitting ? 'Evaluator Scoring Answer...' : <>Submit Spoken Answer <Send size={16} /></>}
            </button>
          </div>
        </div>
      ) : (
        /* Monaco Code Editor UI */
        <div className="glass-panel" style={{ padding: '1.5rem' }}>
          {/* Editor Header Bar */}
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '1rem',
              flexWrap: 'wrap',
              gap: '1rem',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Language:</span>
                <select
                  className="select-field"
                  style={{ width: '150px', padding: '0.4rem 0.75rem', fontSize: '0.85rem' }}
                  value={codeLanguage}
                  onChange={(e) => handleLanguageChange(e.target.value)}
                >
                  <option value="python">Python</option>
                  <option value="javascript">JavaScript</option>
                  <option value="cpp">C++</option>
                  <option value="java">Java</option>
                  <option value="c">C</option>
                  <option value="sql">SQL (Database)</option>
                </select>
              </div>

              {/* Full code vs Pseudocode toggle */}
              <div
                style={{
                  display: 'flex',
                  background: 'rgba(13, 19, 34, 0.8)',
                  borderRadius: '8px',
                  padding: '3px',
                  border: '1px solid var(--border-subtle)',
                }}
              >
                <button
                  type="button"
                  onClick={() => {
                    setAnswerMode('full_code');
                    if (codeContent === LANGUAGE_STARTERS.pseudocode || codeContent.trim() === '// Write your algorithmic pseudocode here') {
                      setCodeContent(LANGUAGE_STARTERS[codeLanguage] || '');
                    }
                  }}
                  style={{
                    padding: '0.35rem 0.75rem',
                    borderRadius: '6px',
                    border: 'none',
                    background: answerMode === 'full_code' ? 'var(--accent-primary)' : 'transparent',
                    color: answerMode === 'full_code' ? '#FFFFFF' : 'var(--text-secondary)',
                    fontSize: '0.8rem',
                    fontWeight: 600,
                    cursor: 'pointer',
                  }}
                >
                  Full Code
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setAnswerMode('pseudocode');
                    if (Object.values(LANGUAGE_STARTERS).includes(codeContent)) {
                      setCodeContent(LANGUAGE_STARTERS.pseudocode);
                    }
                  }}
                  style={{
                    padding: '0.35rem 0.75rem',
                    borderRadius: '6px',
                    border: 'none',
                    background: answerMode === 'pseudocode' ? 'var(--accent-primary)' : 'transparent',
                    color: answerMode === 'pseudocode' ? '#FFFFFF' : 'var(--text-secondary)',
                    fontSize: '0.8rem',
                    fontWeight: 600,
                    cursor: 'pointer',
                  }}
                >
                  Pseudocode
                </button>
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <button
                type="button"
                onClick={handleRunCode}
                disabled={isRunningCode || !codeContent}
                className="btn btn-secondary"
                style={{
                  padding: '0.45rem 1rem',
                  fontSize: '0.85rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.4rem',
                  color: answerMode === 'pseudocode' ? '#A78BFA' : '#10B981',
                  borderColor: answerMode === 'pseudocode' ? 'rgba(167, 139, 250, 0.4)' : undefined,
                  background: answerMode === 'pseudocode' ? 'rgba(167, 139, 250, 0.08)' : undefined,
                }}
              >
                {answerMode === 'pseudocode' ? (
                  <>
                    <Sparkles size={14} color="#A78BFA" /> {isRunningCode ? 'Verifying Logic...' : 'Verify Pseudocode'}
                  </>
                ) : (
                  <>
                    <Play size={14} fill="#10B981" /> {isRunningCode ? 'Running Sandbox...' : 'Run Code'}
                  </>
                )}
              </button>

              {isRecording ? (
                <button
                  type="button"
                  onClick={stopRecording}
                  className="btn btn-danger"
                  style={{ padding: '0.45rem 0.9rem', fontSize: '0.85rem' }}
                >
                  <MicOff size={16} /> Stop Speaking ({audioLevel}%)
                </button>
              ) : (
                <button
                  type="button"
                  onClick={() => startRecording('coding')}
                  disabled={isTranscribing}
                  className="btn btn-secondary"
                  style={{ padding: '0.45rem 0.9rem', fontSize: '0.85rem' }}
                >
                  <Mic size={16} /> {isTranscribing ? 'Transcribing...' : 'Talk Through Approach'}
                </button>
              )}

              <button
                onClick={handleSubmitAnswer}
                disabled={submitting || isRecording}
                className="btn btn-primary"
                style={{ padding: '0.45rem 1.4rem', fontSize: '0.85rem' }}
              >
                {submitting ? 'Evaluating Code...' : <>Submit Solution <Send size={16} /></>}
              </button>
            </div>
          </div>

          {/* Monaco Editor Container */}
          <div style={{ borderRadius: '10px', overflow: 'hidden', border: '1px solid var(--border-subtle)', marginBottom: '1rem' }}>
            <Editor
              height="380px"
              language={codeLanguage}
              theme="vs-dark"
              value={codeContent}
              onChange={(val) => setCodeContent(val || '')}
              options={{
                minimap: { enabled: false },
                fontSize: 14,
                lineNumbers: 'on',
                scrollBeyondLastLine: false,
                automaticLayout: true,
              }}
            />
          </div>

          {/* Execution Terminal Output Panel */}
          {executionResult && (
            <div
              style={{
                background: '#090D16',
                border: '1px solid var(--border-subtle)',
                borderRadius: '8px',
                padding: '0.85rem 1.25rem',
                marginBottom: '1rem',
                fontFamily: 'monospace',
                fontSize: '0.85rem',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                  <span style={{ fontWeight: 600, color: 'var(--text-secondary)' }}>
                    {executionResult.is_pseudocode_analysis || answerMode === 'pseudocode' ? 'Pseudocode Logic Verifier' : 'Execution Terminal'}
                  </span>
                  <span
                    className={
                      executionResult.status === 'success'
                        ? 'badge badge-emerald'
                        : executionResult.status === 'logic_error'
                        ? 'badge badge-amber'
                        : executionResult.status === 'timeout'
                        ? 'badge badge-amber'
                        : 'badge badge-danger'
                    }
                    style={{ fontSize: '0.7rem' }}
                  >
                    {executionResult.status === 'success' && (executionResult.is_pseudocode_analysis || answerMode === 'pseudocode')
                      ? 'LOGIC VERIFIED'
                      : executionResult.status === 'logic_error'
                      ? 'LOGIC FLAW'
                      : executionResult.status.toUpperCase()}
                  </span>
                  {executionResult.execution_time_ms > 0 && (
                    <span className="badge badge-indigo" style={{ fontSize: '0.7rem' }}>
                      {executionResult.execution_time_ms}ms
                    </span>
                  )}
                </div>
                <button
                  type="button"
                  onClick={() => setExecutionResult(null)}
                  style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: '0.75rem' }}
                >
                  Clear Terminal
                </button>
              </div>

              {executionResult.output && (
                <pre style={{ margin: 0, color: '#A7F3D0', whiteSpace: 'pre-wrap', lineHeight: '1.4' }}>
                  {executionResult.output}
                </pre>
              )}
              {executionResult.error && (
                <pre
                  style={{
                    margin: 0,
                    color: executionResult.status === 'logic_error' ? '#FDE68A' : '#FCA5A5',
                    whiteSpace: 'pre-wrap',
                    lineHeight: '1.4',
                  }}
                >
                  {executionResult.error}
                </pre>
              )}
            </div>
          )}


          {/* Spoken Narration while Coding */}
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.35rem' }}>
              <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                Spoken Reasoning / Problem Approach:
              </label>
              {whisperStats && (
                <span className="badge badge-emerald" style={{ fontSize: '0.7rem' }}>
                  Whisper {whisperStats.latency_ms}ms
                </span>
              )}
            </div>
            <input
              type="text"
              className="input-field"
              placeholder="Click 'Talk Through Approach' or type your mental approach (e.g. 'I will use a two-pointer approach initialized at both ends...')"
              value={spokenNarration}
              onChange={(e) => setSpokenNarration(e.target.value)}
            />
          </div>
        </div>
      )}
    </div>
  );
}
