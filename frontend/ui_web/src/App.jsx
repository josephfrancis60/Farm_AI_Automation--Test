import React, { useState, useEffect, useRef } from 'react';
import { Mic, Send, AlertTriangle, Info, CheckCircle, XCircle, Bell, Clock, Settings, X } from 'lucide-react';
import VoiceVisualizer from './VoiceVisualizer';

const API_BASE = '/api';
const WS_BASE = `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}/ws/live`;
const LIVE_CONTEXT_LIMIT = 131072;
const LIVE_TPM_LIMIT = 1000000;
const LANGUAGE_META = {
  English: { speechCode: 'en-US' },
  Tamil: { speechCode: 'ta-IN' },
  Malayalam: { speechCode: 'ml-IN' },
  Hindi: { speechCode: 'hi-IN' }
};

const toDisplayText = (value) => {
  if (value === null || value === undefined) return '';
  if (typeof value === 'string') return value;
  if (typeof value === 'number' || typeof value === 'boolean') return String(value);
  if (Array.isArray(value)) return value.map(toDisplayText).filter(Boolean).join(' ');
  if (typeof value === 'object') {
    if ('text' in value) return toDisplayText(value.text);
    if ('message' in value) return toDisplayText(value.message);
    return JSON.stringify(value);
  }
  return String(value);
};

function App() {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [alerts, setAlerts] = useState([]);
  const [reminders, setReminders] = useState([]);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isBackendOnline, setIsBackendOnline] = useState(true);
  const isBackendOnlineRef = useRef(true);
  const lastOfflineAnnouncementRef = useRef(0);
  const [modelName, setModelName] = useState('Gemini 2.5 Flash Native Audio');
  const [showSettings, setShowSettings] = useState(false);
  const [usage, setUsage] = useState({
    total: 0,
    prompt: 0,
    response: 0,
    thoughts: 0,
    promptDetails: {},
    responseDetails: {}
  });
  const [quotaStatus, setQuotaStatus] = useState('Waiting for Gemini usage metadata');

  // Settings state
  const [config, setConfig] = useState({
    model: 'gemini-2.5-flash-native-audio-preview-12-2025',
    voice: 'Kore',
    language: 'English',
    affective_dialog: true,
    proactive_audio: true
  });
  const [draftConfig, setDraftConfig] = useState(config);

  const activeReminderIdRef = useRef(null);
  const [activeReminderId, setActiveReminderId] = useState(null);
  const chatEndRef = useRef(null);
  const announcedReminders = useRef(new Set());
  const wsRef = useRef(null);
  const audioContextRef = useRef(null);
  const processorRef = useRef(null);
  const audioQueueRef = useRef([]);
  const isPlayingRef = useRef(false);
  const restartTimerRef = useRef(null);
  const recognitionRef = useRef(null);
  const voiceInputMessageIdRef = useRef(null);

  // Initialize
  useEffect(() => {
    checkBackendStatus();
    fetchAlerts();
    fetchReminders();

    // Show initial greeting text only — Gemini speaks when live session starts
    const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false });
    setMessages([{
      id: Date.now(),
      role: 'echo',
      content: 'Welcome back sir. Press Mic or M to start voice interaction.',
      timestamp: now
    }]);

    const interval = setInterval(() => {
      checkBackendStatus();
      fetchAlerts();
      fetchReminders();
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Global 'm' key listener
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key.toLowerCase() === 'm' && document.activeElement.tagName !== 'INPUT') {
        toggleLiveConnection();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isListening]);

  const openSettings = () => {
    setDraftConfig(config);
    setShowSettings(true);
  };

  const cancelSettings = () => {
    setDraftConfig(config);
    setShowSettings(false);
  };

  const applySettings = () => {
    const nextConfig = { ...draftConfig };
    setConfig(nextConfig);
    setShowSettings(false);
    if (isListening) {
      restartLiveConnection(nextConfig);
    }
  };

  const checkBackendStatus = async () => {
    try {
      const res = await fetch(`${API_BASE}/health`);
      if (res.ok) {
        if (!isBackendOnlineRef.current) {
          // System came back online — show text, Gemini will speak if session is active
          const onlineMsg = 'Sir, connectivity has been restored. My processing cores are now online.';
          setMessages(prev => [...prev, {
            id: Date.now(),
            role: 'echo',
            content: onlineMsg,
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false })
          }]);
          // If live session is open, send the message through it so Gemini speaks it
          if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({ type: 'text', text: onlineMsg }));
          }
        }
        setIsBackendOnline(true);
        isBackendOnlineRef.current = true;
      } else {
        throw new Error('Offline');
      }
    } catch (err) {
      const now = Date.now();
      const shouldAnnounce = isBackendOnlineRef.current || (now - lastOfflineAnnouncementRef.current > 180000); // 3 minutes

      if (shouldAnnounce) {
        setIsBackendOnline(false);
        isBackendOnlineRef.current = false;
        lastOfflineAnnouncementRef.current = now;
        
        const offlineMsg = 'Servers are down. Please restore connectivity to my main processing cores.';
        setMessages(prev => [...prev, {
          id: Date.now(),
          role: 'error',
          content: offlineMsg,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false })
        }]);
      }
    }
  };

  // Browser TTS is only used as a last resort when Gemini session is not active
  const speak = (text) => {
    if (!window.speechSynthesis) return;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.onstart = () => setIsSpeaking(true);
    utterance.onend = () => setIsSpeaking(false);
    const voices = window.speechSynthesis.getVoices();
    const preferred = voices.find(v => v.name.includes('David') || v.name.includes('Microsoft David'));
    if (preferred) utterance.voice = preferred;
    window.speechSynthesis.speak(utterance);
  };

  const fetchAlerts = async () => {
    try {
      const res = await fetch(`${API_BASE}/alerts`);
      const data = await res.json();
      setAlerts(data);
    } catch (err) {
      console.error('Failed to fetch alerts', err);
    }
  };

  const fetchReminders = async () => {
    try {
      const res = await fetch(`${API_BASE}/reminders`);
      const data = await res.json();
      setReminders(data);
    } catch (err) {
      console.error('Failed to fetch reminders', err);
    }
  };

  const clearReminder = async (id) => {
    try {
      await fetch(`${API_BASE}/reminders/${id}`, { method: 'DELETE' });
      fetchReminders();
    } catch (err) {
      console.error('Failed to clear reminder', err);
    }
  };

  const tokenWindowPercent = Math.min(100, (usage.total / LIVE_CONTEXT_LIMIT) * 100);
  const tpmPercent = Math.min(100, (usage.total / LIVE_TPM_LIMIT) * 100);

  const toggleLiveConnection = () => {
    if (isListening) {
      stopLiveConnection();
    } else {
      startLiveConnection();
    }
  };

  const startLiveConnection = async (sessionConfig = config) => {
    setIsListening(true);
    if (window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }
    await ensurePlaybackContext();
    
    // Connect to WebSocket
    const ws = new WebSocket(WS_BASE);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('WebSocket connected');
      setQuotaStatus(`Live session connected: ${sessionConfig.voice}`);
      ws.send(JSON.stringify({ type: 'config', ...sessionConfig }));
      startAudioCapture();
      startUiSpeechRecognition(sessionConfig.language);
      // Ask Gemini to greet — Gemini's voice will speak it
      setTimeout(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: 'text', text: 'Greet the user briefly and tell them you are ready to help.' }));
        }
      }, 800);
    };

    ws.onmessage = async (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === "audio") {
        const audioData = base64ToArrayBuffer(data.data);
        queueAudio(audioData);
      } else if (data.type === "transcript") {
        if (data.role === 'user' && recognitionRef.current) return;
        updateTranscript(data.role, data.text);
      } else if (data.type === "usage") {
        setUsage({
          total: data.total_tokens || 0,
          prompt: data.prompt_tokens || 0,
          response: data.response_tokens || 0,
          thoughts: data.thoughts_tokens || 0,
          promptDetails: data.prompt_tokens_details || {},
          responseDetails: data.response_tokens_details || {}
        });
        setQuotaStatus('Usage updated from Gemini Live');
      } else if (data.type === "error") {
        const message = data.message || 'Gemini Live session failed.';
        updateTranscript('error', message);
        setQuotaStatus(message);
      }
    };

    ws.onclose = () => {
      console.log("WebSocket closed");
      stopAudioCapture();
      stopUiSpeechRecognition();
      setIsListening(false);
    };

    ws.onerror = (err) => {
      console.error("WebSocket error", err);
      setQuotaStatus('WebSocket failed. Confirm the backend is running on port 8000.');
      stopUiSpeechRecognition();
      setIsListening(false);
    };
  };

  const stopLiveConnection = () => {
    if (restartTimerRef.current) {
      clearTimeout(restartTimerRef.current);
      restartTimerRef.current = null;
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    stopUiSpeechRecognition();
  };

  const restartLiveConnection = (nextConfig) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
    setQuotaStatus(`Restarting Live session for ${nextConfig.voice}`);
    audioQueueRef.current = [];
    isPlayingRef.current = false;
    stopAudioCapture();
    wsRef.current.close();
    wsRef.current = null;
    restartTimerRef.current = setTimeout(() => {
      startLiveConnection(nextConfig);
    }, 500);
  };

  const startAudioCapture = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 16000 });
      const source = audioContextRef.current.createMediaStreamSource(stream);
      
      // Use ScriptProcessor for simplicity (AudioWorklet is better but more complex for one file)
      const processor = audioContextRef.current.createScriptProcessor(4096, 1, 1);
      processorRef.current = processor;

      processor.onaudioprocess = (e) => {
        const inputData = e.inputBuffer.getChannelData(0);
        const pcmData = floatTo16BitPCM(inputData);
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
          wsRef.current.send(JSON.stringify({
            type: "audio",
            data: arrayBufferToBase64(pcmData)
          }));
        }
      };

      source.connect(processor);
      processor.connect(audioContextRef.current.destination);
    } catch (err) {
      console.error("Failed to capture audio", err);
    }
  };

  const stopAudioCapture = () => {
    if (processorRef.current) {
      processorRef.current.disconnect();
      processorRef.current = null;
    }
    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }
  };

  const queueAudio = (buffer) => {
    audioQueueRef.current.push(buffer);
    if (!isPlayingRef.current) {
      playNextInQueue();
    }
  };

  const updateVoiceInputTranscript = (text, isFinal) => {
    const displayText = toDisplayText(text).trim();
    if (!displayText) return;

    setMessages(prev => {
      const id = voiceInputMessageIdRef.current || Date.now();
      voiceInputMessageIdRef.current = isFinal ? null : id;
      const existingIndex = prev.findIndex(msg => msg.id === id);
      const nextMessage = {
        id,
        role: 'user',
        content: displayText,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false })
      };

      if (existingIndex >= 0) {
        return prev.map(msg => msg.id === id ? nextMessage : msg);
      }

      return [...prev, nextMessage];
    });
  };

  const startUiSpeechRecognition = (language) => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setQuotaStatus('Live session connected. Browser speech transcript is unavailable here.');
      return;
    }

    stopUiSpeechRecognition();

    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = LANGUAGE_META[language]?.speechCode || 'en-US';
    recognition.onresult = (event) => {
      let interim = '';
      let finalText = '';

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0]?.transcript || '';
        if (event.results[i].isFinal) {
          finalText += transcript;
        } else {
          interim += transcript;
        }
      }

      if (interim) updateVoiceInputTranscript(interim, false);
      if (finalText) updateVoiceInputTranscript(finalText, true);
    };
    recognition.onerror = () => {
      voiceInputMessageIdRef.current = null;
    };
    recognition.onend = () => {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        try {
          recognition.start();
        } catch (err) {
          // The browser can briefly reject immediate restarts.
        }
      }
    };

    recognitionRef.current = recognition;
    try {
      recognition.start();
    } catch (err) {
      recognitionRef.current = null;
    }
  };

  const stopUiSpeechRecognition = () => {
    const recognition = recognitionRef.current;
    recognitionRef.current = null;
    voiceInputMessageIdRef.current = null;
    if (recognition) {
      recognition.onend = null;
      recognition.onerror = null;
      recognition.onresult = null;
      try {
        recognition.stop();
      } catch (err) {
        // Already stopped.
      }
    }
  };

  const ensurePlaybackContext = async () => {
    if (!window.playAudioContext) {
      window.playAudioContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 24000 });
    }
    if (window.playAudioContext.state === 'suspended') {
      await window.playAudioContext.resume();
    }
    return window.playAudioContext;
  };

  const playNextInQueue = async () => {
    if (audioQueueRef.current.length === 0) {
      isPlayingRef.current = false;
      setIsSpeaking(false);
      return;
    }

    isPlayingRef.current = true;
    setIsSpeaking(true);
    const buffer = audioQueueRef.current.shift();
    
    // Play raw PCM 16-bit 24kHz from Gemini Live.
    await ensurePlaybackContext();
    
    const audioBuffer = window.playAudioContext.createBuffer(1, buffer.byteLength / 2, 24000);
    const nowBuffering = audioBuffer.getChannelData(0);
    const view = new Int16Array(buffer);
    for (let i = 0; i < view.length; i++) {
      nowBuffering[i] = view[i] / 32768.0;
    }

    const source = window.playAudioContext.createBufferSource();
    source.buffer = audioBuffer;
    source.connect(window.playAudioContext.destination);
    source.onended = playNextInQueue;
    source.start();
  };

  const updateTranscript = (role, text) => {
    const displayText = toDisplayText(text);
    if (!displayText) return;

    setMessages(prev => {
      // Find last message of same role to append if it's recent
      const last = prev[prev.length - 1];
      if (last && last.role === role && (Date.now() - last.id < 5000)) {
        return [...prev.slice(0, -1), { ...last, content: `${toDisplayText(last.content)} ${displayText}` }];
      }
      return [...prev, {
        id: Date.now(),
        role: role,
        content: displayText,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false })
      }];
    });
  };

  const handleSendText = async () => {
    if (!inputValue.trim()) return;
    const text = inputValue.trim();
    setInputValue('');
    updateTranscript('user', text);

    // If live WS is open, route through it
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'text', text }));
      return;
    }

    // Fallback: use regular REST API
    setIsProcessing(true);
    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text })
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Failed to reach server.');
      }
      updateTranscript('echo', data.reply);
      // Speak via browser TTS since Gemini live is not active
      speak(data.reply);
    } catch (err) {
      const message = err.message || 'Failed to reach server.';
      updateTranscript('error', message);
      setQuotaStatus(message);
    } finally {
      setIsProcessing(false);
    }
  };

  // Helpers
  const floatTo16BitPCM = (input) => {
    const buffer = new ArrayBuffer(input.length * 2);
    const view = new DataView(buffer);
    for (let i = 0; i < input.length; i++) {
      const s = Math.max(-1, Math.min(1, input[i]));
      view.setInt16(i * 2, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
    }
    return buffer;
  };

  const arrayBufferToBase64 = (buffer) => {
    let binary = '';
    const bytes = new Uint8Array(buffer);
    const len = bytes.byteLength;
    for (let i = 0; i < len; i++) {
      binary += String.fromCharCode(bytes[i]);
    }
    return window.btoa(binary);
  };

  const base64ToArrayBuffer = (base64) => {
    const binary_string = window.atob(base64);
    const len = binary_string.length;
    const bytes = new Uint8Array(len);
    for (let i = 0; i < len; i++) {
      bytes[i] = binary_string.charCodeAt(i);
    }
    return bytes.buffer;
  };

  const getAlertIcon = (category) => {
    switch (category) {
      case 'WARNING': return <AlertTriangle size={16} color="var(--amber)" />;
      case 'ERROR': return <XCircle size={16} color="var(--red)" />;
      case 'SUCCESS': return <CheckCircle size={16} color="var(--green)" />;
      default: return <Info size={16} color="var(--cyan)" />;
    }
  };

  return (
    <div className="hud-container">
      <header>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div className="logo">ECHO</div>
          <div 
            className="model-badge" 
            onClick={openSettings}
            title="Configure model settings"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              padding: '2px 10px',
              borderRadius: '12px',
              border: '1.5px solid var(--cyan)',
              backgroundColor: 'rgba(0, 255, 255, 0.08)',
              color: 'var(--cyan)',
              fontSize: '0.75rem',
              fontWeight: '500'
            }}
          >
            <button className="settings-icon-btn">
              <Settings size={12} />
            </button>
            {modelName}
          </div>
          <div className="usage-meter" title={quotaStatus}>
            <div className="usage-row">
              <span>Total {usage.total.toLocaleString()}</span>
              <span>In {usage.prompt.toLocaleString()}</span>
              <span>Out {usage.response.toLocaleString()}</span>
              <span>Think {usage.thoughts.toLocaleString()}</span>
            </div>
            <div className="usage-bar-label">
              <span>Context {tokenWindowPercent.toFixed(2)}%</span>
              <span>TPM {tpmPercent.toFixed(3)}%</span>
            </div>
            <div className="usage-bar">
              <div className="usage-bar-fill" style={{ width: `${tokenWindowPercent}%` }}></div>
            </div>
          </div>
        </div>
        <div className="status-indicator">
          <div className={`status-dot ${!isBackendOnline ? 'offline' : ''}`}></div>
          <span className={isBackendOnline ? 'text-online' : 'text-offline'}>
            {isBackendOnline ? 'SYSTEM ONLINE' : 'SYSTEM OFFLINE'}
          </span>
          <span style={{ color: 'var(--text-dim)', margin: '0 4px' }}>·</span>
          <span style={{ color: 'var(--cyan)' }}>BANGLORE</span>
        </div>
      </header>

      <main>
        <div className="chat-section">
          {messages.map(msg => (
            <div key={msg.id} className={`message ${msg.role}`}>
              <div className="message-meta">
                <span className="role-tag">
                  {msg.role === 'user' ? 'USER' :
                    msg.role === 'echo' ? 'ECHO · AGENT' :
                      'SYSTEM'}
                </span>
                <span> · {msg.timestamp}</span>
              </div>
              <div className="message-content">{toDisplayText(msg.content)}</div>
            </div>
          ))}
          <VoiceVisualizer isListening={isListening} isSpeaking={isSpeaking} />
          {isProcessing && (
            <div className="typing-indicator">● ● ● ECHO IS PROCESSING...</div>
          )}
          <div ref={chatEndRef} />
        </div>

        <aside className="monitor-panel">
          <div className="monitor-section">
            <h3><Clock size={14} style={{ verticalAlign: 'middle', marginRight: '8px' }} /> Reminders</h3>
            {reminders.length === 0 ? (
              <div style={{ color: 'var(--text-dim)', fontSize: '0.8rem', padding: '10px' }}>NO ACTIVE REMINDERS</div>
            ) : (
              reminders.map(rem => (
                <div key={rem.id} className={`alert-card WARNING`}>
                  <button className="alert-clear" onClick={() => clearReminder(rem.id)}>CNCL</button>
                  <div className="alert-title" style={{ color: 'var(--amber)' }}>{rem.title}</div>
                  <div className="alert-msg" style={{ fontSize: '0.75rem', opacity: 0.8 }}>{rem.message}</div>
                </div>
              ))
            )}
          </div>

          <div className="monitor-section">
            <h3><Bell size={14} style={{ verticalAlign: 'middle', marginRight: '8px' }} /> Alerts</h3>
            {alerts.length === 0 ? (
              <div style={{ color: 'var(--text-dim)', fontSize: '0.8rem', padding: '10px' }}>ALERTS CLEARED</div>
            ) : (
              alerts.map(alert => (
                <div key={alert.id} className={`alert-card ${alert.category}`}>
                  <div style={{ display: 'flex', gap: '8px', alignItems: 'center', marginBottom: '4px' }}>
                    {getAlertIcon(alert.category)}
                    <span className="alert-title">{alert.title}</span>
                  </div>
                  <div className="alert-msg">{alert.message}</div>
                </div>
              ))
            )}
          </div>
        </aside>
      </main>

      <footer>
        <button
          className={`mic-btn ${isListening ? 'listening' : ''}`}
          onClick={toggleLiveConnection}
          title="Press 'M' to toggle"
        >
          <Mic size={20} />
        </button>
        <div className="input-container">
          <input
            type="text"
            placeholder="HOW MAY I ASSIST YOU?"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSendText()}
            disabled={!isBackendOnline}
          />
        </div>
        <button className="send-btn" onClick={handleSendText} disabled={!isBackendOnline || !inputValue.trim()}>
          <Send size={20} />
        </button>
      </footer>

      {showSettings && (
        <div className="modal-overlay" onClick={cancelSettings}>
          <div className="liquid-glass-modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Model Configuration</h2>
              <button className="close-btn" onClick={cancelSettings}>
                <X size={20} />
              </button>
            </div>
            <div className="settings-grid">
              <div className="setting-item">
                <label>Voice</label>
                <select 
                  className="glass-select"
                  value={draftConfig.voice}
                  onChange={e => setDraftConfig({...draftConfig, voice: e.target.value})}
                >
                  <option value="Puck">Puck</option>
                  <option value="Charon">Charon</option>
                  <option value="Kore">Kore</option>
                  <option value="Fenrir">Fenrir</option>
                  <option value="Aoede">Aoede</option>
                </select>
              </div>
              <div className="setting-item">
                <label>Language</label>
                <select 
                  className="glass-select"
                  value={draftConfig.language}
                  onChange={e => setDraftConfig({...draftConfig, language: e.target.value})}
                >
                  <option value="English">English</option>
                  <option value="Tamil">Tamil</option>
                  <option value="Malayalam">Malayalam</option>
                  <option value="Hindi">Hindi</option>
                </select>
              </div>
              <div className="switch-group" title="Lets Gemini adapt tone and delivery based on the user's expression and mood.">
                <span>Affective Dialog</span>
                <label className="switch">
                  <input 
                    type="checkbox" 
                    checked={draftConfig.affective_dialog}
                    onChange={e => setDraftConfig({...draftConfig, affective_dialog: e.target.checked})}
                  />
                  <span className="slider"></span>
                </label>
              </div>
              <div className="switch-group" title="Lets Gemini decide when an audio response is useful, instead of replying to every sound.">
                <span>Proactive Audio</span>
                <label className="switch">
                  <input 
                    type="checkbox" 
                    checked={draftConfig.proactive_audio}
                    onChange={e => setDraftConfig({...draftConfig, proactive_audio: e.target.checked})}
                  />
                  <span className="slider"></span>
                </label>
              </div>
              <div className="modal-actions">
                <button className="secondary-action" onClick={cancelSettings}>Cancel</button>
                <button className="primary-action" onClick={applySettings}>Apply Changes</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
