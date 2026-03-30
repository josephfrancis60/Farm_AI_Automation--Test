import React, { useState, useEffect, useRef } from 'react';
import { Mic, Send, AlertTriangle, Info, CheckCircle, XCircle, Bell, Clock } from 'lucide-react';
import VoiceVisualizer from './VoiceVisualizer';

const API_BASE = '/api';

function App() {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [alerts, setAlerts] = useState([]);
  const [reminders, setReminders] = useState([]);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const activeReminderIdRef = useRef(null);
  const [activeReminderId, setActiveReminderId] = useState(null);

  const [isBackendOnline, setIsBackendOnline] = useState(true);
  const prevOnlineRef = useRef(true);

  const chatEndRef = useRef(null);
  const recognitionRef = useRef(null);
  const isSpokenRef = useRef(false); // To prevent multiple initial speaks
  const announcedReminders = useRef(new Set());

  const checkBackendStatus = async () => {
    try {
      const res = await fetch(`${API_BASE}/health`);
      if (res.ok) {
        if (!prevOnlineRef.current) {
          // System came back online
          speak("Sir, connectivity has been restored. My processing cores are now online.");
          setMessages(prev => [...prev, {
            id: Date.now(),
            role: 'echo',
            content: "Connectivity restored. Systems operational.",
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false })
          }]);
        }
        setIsBackendOnline(true);
        prevOnlineRef.current = true;
      } else {
        throw new Error('Offline');
      }
    } catch (err) {
      if (prevOnlineRef.current) {
        // System just went offline
        setIsBackendOnline(false);
        prevOnlineRef.current = false;
        speak("Servers are down. Please restore connectivity to my main processing cores.");
      }
    }
  };

  // Initialize Speech Recognition
  useEffect(() => {
    if (SpeechRecognition) {
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = true;
      recognitionRef.current.interimResults = true;
      recognitionRef.current.lang = 'en-US';

      recognitionRef.current.onresult = (event) => {
        const transcript = Array.from(event.results)
          .map(result => result[0].transcript)
          .join('');
        setInputValue(transcript);
        // Do not auto-send here. User must press Send or Enter to finish.
      };

      recognitionRef.current.onend = () => {
        setIsListening(false);
      };

      recognitionRef.current.onerror = (event) => {
        console.error('Speech recognition error', event.error);
        setIsListening(false);
      };
    }

    // Initial welcome speech (only if online)
    const initialGreeting = "Welcome back sir. How may I assist you.";

    // Initial check
    checkBackendStatus().then(() => {
      const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false });

      // If still offline after first check
      if (!prevOnlineRef.current) {
        const offMsg = "Servers are down....";
        speak(offMsg);
        setMessages([{
          id: Date.now(),
          role: 'error',
          content: offMsg,
          timestamp: now
        }]);
        isSpokenRef.current = true;
      } else if (!isSpokenRef.current) {
        speak(initialGreeting);
        setMessages([{
          id: Date.now(),
          role: 'echo',
          content: initialGreeting,
          timestamp: now
        }]);
        isSpokenRef.current = true;
      }
    });

    // Polling for backend status, alerts, and reminders
    const interval = setInterval(() => {
      checkBackendStatus();
      if (prevOnlineRef.current) {
        fetchAlerts();
        fetchReminders();
      }
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
        toggleMic();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isListening]);

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

      // Auto-speak reminders when due
      const now = new Date();
      data.forEach(rem => {
        const dueTime = new Date(rem.due_time);
        if (now >= dueTime && !announcedReminders.current.has(rem.id) && !activeReminderIdRef.current) {
          // Trigger natural announcement via hidden chat message
          announcedReminders.current.add(rem.id);
          activeReminderIdRef.current = rem.id;
          setActiveReminderId(rem.id);
          handleTrigger(`[SYSTEM TRIGGER: REMINDER DUE] Title: ${rem.title}, Message: ${rem.message}. Please announce this naturally.`);
        }
      });

      setReminders(data);
    } catch (err) {
      console.error('Failed to fetch reminders', err);
    }
  };

  const clearReminder = async (id, isSilent = false) => {
    try {
      await fetch(`${API_BASE}/reminders/${id}`, { method: 'DELETE' });
      if (!isSilent) {
        handleTrigger(`[SYSTEM TRIGGER: REMINDER CANCELED] The user manually canceled a reminder. Acknowledge this naturally.`);
      }
      fetchReminders();
    } catch (err) {
      console.error('Failed to clear reminder', err);
    }
  };

  const handleTrigger = async (text) => {
    if (isProcessing) return;
    setIsProcessing(true);
    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text })
      });
      const data = await res.json();

      const echoMsg = {
        id: Date.now() + 1,
        role: 'echo',
        content: data.reply,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false })
      };
      setMessages(prev => [...prev, echoMsg]);
      speak(data.reply);
    } catch (err) {
      console.error("System trigger failed", err);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleSend = async (text) => {
    const messageText = text || inputValue;
    if (!messageText.trim() || isProcessing) return;

    const userMsg = {
      id: Date.now(),
      role: 'user',
      content: messageText,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false })
    };

    setMessages(prev => [...prev, userMsg]);
    setInputValue('');
    setIsProcessing(true);

    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: messageText })
      });
      const data = await res.json();

      const echoMsg = {
        id: Date.now() + 1,
        role: 'echo',
        content: data.reply,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false })
      };

      setMessages(prev => [...prev, echoMsg]);
      speak(data.reply);
    } catch (err) {
      const offlineMsg = "Servers are down....";
      speak(offlineMsg);
      const errMsg = {
        id: Date.now() + 1,
        role: 'error',
        content: offlineMsg,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false })
      };
      setMessages(prev => [...prev, errMsg]);
    } finally {
      setIsProcessing(false);
    }
  };

  const speak = (text) => {
    if (!window.speechSynthesis) return;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);

    utterance.onstart = () => setIsSpeaking(true);
    utterance.onend = () => {
      setIsSpeaking(false);
      // Auto-clear active reminder after speaking finishes
      if (activeReminderIdRef.current) {
        clearReminder(activeReminderIdRef.current, true); // true = silent
        activeReminderIdRef.current = null;
        setActiveReminderId(null);
      }
    };
    utterance.onerror = () => {
      setIsSpeaking(false);
      activeReminderIdRef.current = null;
      setActiveReminderId(null);
    };

    // Find a good male voice if possible
    const voices = window.speechSynthesis.getVoices();
    const preferred = voices.find(v => v.name.includes('David') || v.name.includes('Microsoft David') || v.name.includes('Daniel'));
    if (preferred) utterance.voice = preferred;

    utterance.rate = 1.0;
    utterance.pitch = 0.9;
    window.speechSynthesis.speak(utterance);
  };

  const toggleMic = () => {
    if (isListening) {
      recognitionRef.current?.stop();
    } else {
      setIsListening(true);
      recognitionRef.current?.start();
    }
  };

  const clearAlert = async (id) => {
    try {
      await fetch(`${API_BASE}/alerts/${id}`, { method: 'DELETE' });
      fetchAlerts();
    } catch (err) {
      console.error('Failed to clear alert', err);
    }
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
        <div className="logo">ECHO</div>
        <div className="status-indicator">
          <div className={`status-dot ${!isBackendOnline ? 'offline' : ''}`}></div>
          <span className={isBackendOnline ? 'text-online' : 'text-offline'}>
            {isBackendOnline ? 'SYSTEM ONLINE' : 'SYSTEM OFFLINE'}
          </span>
          <span style={{ color: 'var(--text-dim)', margin: '0 4px' }}>·</span>
          <span style={{ color: 'var(--cyan)' }}>Banglore</span>
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
              <div className="message-content">{msg.content}</div>
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
              reminders.map(rem => {
                const hitTime = new Date(rem.due_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false });
                return (
                  <div key={rem.id} className={`alert-card WARNING ${rem.id === activeReminderId ? 'highlight-reminder' : ''}`}>
                    <button className="alert-clear" onClick={() => clearReminder(rem.id)}>CNCL</button>
                    <div className="alert-title" style={{ color: 'var(--amber)' }}>{rem.title}</div>
                    <div className="alert-msg" style={{ fontSize: '0.75rem', opacity: 0.8 }}>{rem.message}</div>
                    <div className="reminder-hit-time">
                      <Clock size={10} style={{ verticalAlign: 'middle', marginRight: '4px' }} />
                      HIT: {hitTime}
                    </div>
                  </div>
                );
              })
            )}
          </div>

          <div className="monitor-section">
            <h3><Bell size={14} style={{ verticalAlign: 'middle', marginRight: '8px' }} /> Alerts</h3>
            {alerts.length === 0 ? (
              <div style={{ color: 'var(--text-dim)', fontSize: '0.8rem', padding: '10px' }}>ALERTS CLEARED</div>
            ) : (
              alerts.map(alert => (
                <div key={alert.id} className={`alert-card ${alert.category}`}>
                  <button className="alert-clear" onClick={() => clearAlert(alert.id)}>CLR</button>
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
          onClick={toggleMic}
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
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            disabled={isProcessing}
          />
        </div>
        <button className="send-btn" onClick={() => handleSend()}>
          <Send size={20} />
        </button>
      </footer>
    </div>
  );
}

export default App;
