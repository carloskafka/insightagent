import React, { useState, useRef, useEffect } from 'react'
import {
  Send, Mic, MicOff, Paperclip, Volume2, LogOut, Plus,
  MessageSquare, Trash2, Menu, Bot, User, Loader2
} from 'lucide-react'
import './App.css'

const API = 'http://localhost:8000'

const WELCOME_MESSAGE = {
  role: 'assistant',
  isWelcome: true,
  time: new Date(),
  content: `Hi! I'm InsightAgent, your AI assistant powered by GPT-o3 120B.

Here's what I can do for you:

💬  Answer any question — general knowledge, explanations, analysis
🔍  Web search — try "search for the latest AI news"
🧮  Math & calculations — try "calculate 15% of 2500"
📄  Document analysis — upload a file and ask questions about it
🎤  Voice input — click the mic button and speak

How can I help you today?`
}

const SUGGESTIONS = [
  'What are your main capabilities?',
  'Search for the latest AI news',
  'Explain quantum computing simply',
  'Calculate 15% of 2500',
]

function formatTime(date) {
  return new Date(date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

export default function App() {
  const [authTab, setAuthTab] = useState('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [authMsg, setAuthMsg] = useState({ type: '', text: '' })
  const [authLoading, setAuthLoading] = useState(false)

  const [token] = useState(() => localStorage.getItem('token') || '')
  const [userEmail, setUserEmail] = useState(() => localStorage.getItem('userEmail') || '')
  const [isLoggedIn, setIsLoggedIn] = useState(() => !!localStorage.getItem('token'))

  const [messages, setMessages] = useState([WELCOME_MESSAGE])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [conversations, setConversations] = useState([])
  const [currentConversationId, setCurrentConversationId] = useState(null)
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [isRecording, setIsRecording] = useState(false)

  const tokenRef = useRef(token)
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)
  const wsRef = useRef(null)
  const mediaRecorderRef = useRef(null)
  const audioChunksRef = useRef([])
  const fileInputRef = useRef(null)
  const isRecordingRef = useRef(false)
  const audioCtxRef = useRef(null)
  const animFrameRef = useRef(null)

  useEffect(() => {
    if (isLoggedIn) {
      fetchConversations()
      connectWebSocket()
    }
    return () => wsRef.current?.close()
  }, [isLoggedIn])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  const authHeader = () => ({ Authorization: `Bearer ${tokenRef.current}` })

  const fetchConversations = async () => {
    try {
      const res = await fetch(`${API}/conversations`, { headers: authHeader() })
      if (res.ok) setConversations(await res.json())
    } catch (e) { console.error(e) }
  }

  const connectWebSocket = () => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return
    wsRef.current = new WebSocket('ws://localhost:8000/ws')
    wsRef.current.onclose = () => console.log('WS closed')
  }

  const handleLogin = async (e) => {
    e.preventDefault()
    setAuthLoading(true)
    setAuthMsg({ type: '', text: '' })
    try {
      const res = await fetch(`${API}/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      })
      if (res.ok) {
        const data = await res.json()
        localStorage.setItem('token', data.access_token)
        localStorage.setItem('userEmail', email)
        tokenRef.current = data.access_token
        setUserEmail(email)
        setIsLoggedIn(true)
      } else {
        const err = await res.json()
        setAuthMsg({ type: 'error', text: err.detail || 'Invalid credentials' })
      }
    } catch {
      setAuthMsg({ type: 'error', text: 'Connection error. Is the server running?' })
    } finally {
      setAuthLoading(false)
    }
  }

  const handleSignup = async (e) => {
    e.preventDefault()
    setAuthLoading(true)
    setAuthMsg({ type: '', text: '' })
    try {
      const res = await fetch(`${API}/signup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      })
      if (res.ok) {
        setAuthMsg({ type: 'success', text: 'Account created! You can now sign in.' })
        setAuthTab('login')
        setPassword('')
      } else {
        const err = await res.json()
        setAuthMsg({ type: 'error', text: err.detail || 'Signup failed' })
      }
    } catch {
      setAuthMsg({ type: 'error', text: 'Connection error. Is the server running?' })
    } finally {
      setAuthLoading(false)
    }
  }

  const handleLogout = () => {
    wsRef.current?.close()
    localStorage.removeItem('token')
    localStorage.removeItem('userEmail')
    tokenRef.current = ''
    setIsLoggedIn(false)
    setMessages([])
    setConversations([])
    setCurrentConversationId(null)
    setSidebarOpen(false)
  }

  const newChat = () => {
    setCurrentConversationId(null)
    setMessages([WELCOME_MESSAGE])
    setSidebarOpen(false)
    setTimeout(() => inputRef.current?.focus(), 0)
  }

  const selectConversation = async (conv) => {
    setCurrentConversationId(conv.id)
    setSidebarOpen(false)
    try {
      const res = await fetch(`${API}/conversations/${conv.id}`, { headers: authHeader() })
      if (res.ok) {
        const data = await res.json()
        setMessages((data.messages || []).map(m => ({ ...m, time: new Date(m.created_at) })))
      }
    } catch (e) { console.error(e) }
  }

  const deleteConversation = async (e, convId) => {
    e.stopPropagation()
    try {
      const res = await fetch(`${API}/conversations/${convId}`, {
        method: 'DELETE',
        headers: authHeader()
      })
      if (res.ok) {
        setConversations(prev => prev.filter(c => c.id !== convId))
        if (currentConversationId === convId) { setCurrentConversationId(null); setMessages([]) }
      }
    } catch (e) { console.error(e) }
  }

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return
    const text = input.trim()
    setInput('')
    if (inputRef.current) inputRef.current.style.height = 'auto'
    setMessages(prev => [...prev, { role: 'user', content: text, time: new Date() }])
    setIsLoading(true)

    try {
      const res = await fetch(`${API}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...authHeader() },
        body: JSON.stringify({ message: text, conversation_id: currentConversationId })
      })
      if (res.ok) {
        const data = await res.json()
        setMessages(prev => [...prev, { role: 'assistant', content: data.response, time: new Date() }])
        setCurrentConversationId(data.conversation_id)
        fetchConversations()
      } else {
        throw new Error('API error')
      }
    } catch {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Something went wrong. Please try again.',
        time: new Date()
      }])
    } finally {
      setIsLoading(false)
      setTimeout(() => inputRef.current?.focus(), 0)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage() }
  }

  const handleInputChange = (e) => {
    setInput(e.target.value)
    e.target.style.height = 'auto'
    e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px'
  }

  const handleTextToSpeech = async (text) => {
    try {
      const res = await fetch(`${API}/tts?text=${encodeURIComponent(text)}&lang=en`, {
        method: 'POST',
        headers: authHeader()
      })
      if (res.ok) {
        const blob = await res.blob()
        new Audio(URL.createObjectURL(blob)).play()
      }
    } catch (e) { console.error(e) }
  }

  const handleFileUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    const formData = new FormData()
    formData.append('file', file)
    try {
      const res = await fetch(`${API}/upload`, {
        method: 'POST',
        headers: authHeader(),
        body: formData
      })
      if (res.ok) {
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: `File "${file.name}" uploaded and added to context.`,
          time: new Date()
        }])
      }
    } catch (e) { console.error(e) }
    e.target.value = ''
  }

  const stopRecording = () => {
    if (!isRecordingRef.current) return
    isRecordingRef.current = false
    cancelAnimationFrame(animFrameRef.current)
    audioCtxRef.current?.close().catch(() => {})
    audioCtxRef.current = null
    mediaRecorderRef.current?.stop()
    setIsRecording(false)
  }

  const startRecording = async () => {
    if (isRecordingRef.current) { stopRecording(); return }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })

      // Silence detection via AudioContext
      const audioCtx = new AudioContext()
      audioCtxRef.current = audioCtx
      const analyser = audioCtx.createAnalyser()
      analyser.fftSize = 512
      audioCtx.createMediaStreamSource(stream).connect(analyser)
      const buf = new Uint8Array(analyser.frequencyBinCount)

      let silenceMs = 0
      let hadSpeech = false
      let lastTick = Date.now()

      const detect = () => {
        if (!isRecordingRef.current) return
        analyser.getByteTimeDomainData(buf)
        const rms = Math.sqrt(buf.reduce((s, v) => s + (v - 128) ** 2, 0) / buf.length)
        const dt = Date.now() - lastTick
        lastTick = Date.now()

        if (rms > 8) {
          hadSpeech = true
          silenceMs = 0
        } else if (hadSpeech) {
          silenceMs += dt
          if (silenceMs >= 1800) { stopRecording(); return }
        }
        animFrameRef.current = requestAnimationFrame(detect)
      }

      // MediaRecorder setup
      mediaRecorderRef.current = new MediaRecorder(stream)
      audioChunksRef.current = []
      mediaRecorderRef.current.ondataavailable = (e) => audioChunksRef.current.push(e.data)
      mediaRecorderRef.current.onstop = async () => {
        const blob = new Blob(audioChunksRef.current, { type: 'audio/webm' })
        const formData = new FormData()
        formData.append('audio', blob, 'recording.webm')
        try {
          const res = await fetch(`${API}/voice`, {
            method: 'POST',
            headers: authHeader(),
            body: formData
          })
          if (res.ok) {
            const data = await res.json()
            setMessages(prev => [
              ...prev,
              { role: 'user', content: data.text, time: new Date() },
              { role: 'assistant', content: data.response, time: new Date() }
            ])
            fetchConversations()
          } else {
            setMessages(prev => [...prev, {
              role: 'assistant',
              content: 'Could not understand the audio. Please try again.',
              time: new Date()
            }])
          }
        } catch (e) { console.error(e) }
      }

      mediaRecorderRef.current.start()
      isRecordingRef.current = true
      setIsRecording(true)
      animFrameRef.current = requestAnimationFrame(detect)
    } catch {
      alert('Microphone access denied')
    }
  }

  const handleSuggestion = (text) => {
    setInput(text)
    setTimeout(() => inputRef.current?.focus(), 0)
  }

  const showSuggestions = messages.length === 1 && messages[0].isWelcome

  // ── AUTH ────────────────────────────────────────────────
  if (!isLoggedIn) {
    const isLoginTab = authTab === 'login'
    return (
      <div className="auth-page">
        <div className="auth-card">
          <div className="auth-logo">
            <div className="auth-logo-icon"><Bot size={22} /></div>
            <span className="auth-logo-text">InsightAgent</span>
          </div>

          <div className="auth-tabs">
            <button
              className={`auth-tab ${authTab === 'login' ? 'active' : ''}`}
              onClick={() => { setAuthTab('login'); setAuthMsg({ type: '', text: '' }) }}
            >Login</button>
            <button
              className={`auth-tab ${authTab === 'signup' ? 'active' : ''}`}
              onClick={() => { setAuthTab('signup'); setAuthMsg({ type: '', text: '' }) }}
            >Sign Up</button>
          </div>

          {authMsg.text && (
            <div className={`auth-message ${authMsg.type}`}>{authMsg.text}</div>
          )}

          <form onSubmit={isLoginTab ? handleLogin : handleSignup}>
            <div className="auth-field">
              <label className="auth-label">Email</label>
              <input
                type="email"
                className="auth-input"
                placeholder="you@example.com"
                value={email}
                onChange={e => setEmail(e.target.value)}
                required
                autoFocus
              />
            </div>
            <div className="auth-field">
              <label className="auth-label">Password</label>
              <input
                type="password"
                className="auth-input"
                placeholder="••••••••"
                value={password}
                onChange={e => setPassword(e.target.value)}
                required
              />
            </div>
            <button type="submit" className="auth-btn" disabled={authLoading}>
              {authLoading && <Loader2 size={17} className="spin" />}
              {isLoginTab ? 'Sign In' : 'Create Account'}
            </button>
          </form>
        </div>
      </div>
    )
  }

  // ── CHAT ────────────────────────────────────────────────
  const initials = userEmail ? userEmail[0].toUpperCase() : '?'
  const activeConv = conversations.find(c => c.id === currentConversationId)

  return (
    <div className="app">
      <div
        className={`sidebar-overlay ${sidebarOpen ? 'visible' : ''}`}
        onClick={() => setSidebarOpen(false)}
      />

      <aside className={`sidebar ${sidebarOpen ? 'open' : ''}`}>
        <div className="sidebar-header">
          <div className="sidebar-logo">
            <div className="sidebar-logo-icon"><Bot size={18} /></div>
            <span className="sidebar-logo-text">InsightAgent</span>
          </div>
          <button className="new-chat-btn" onClick={newChat}>
            <Plus size={15} /> New Conversation
          </button>
        </div>

        <div className="sidebar-conversations">
          {conversations.length > 0 && (
            <>
              <div className="conv-section-label">Recent</div>
              {conversations.map(conv => (
                <div
                  key={conv.id}
                  className={`conv-item ${conv.id === currentConversationId ? 'active' : ''}`}
                  onClick={() => selectConversation(conv)}
                >
                  <MessageSquare size={13} style={{ flexShrink: 0 }} />
                  <span className="conv-item-title">{conv.title || 'Untitled'}</span>
                  <button
                    className="conv-delete-btn"
                    onClick={(e) => deleteConversation(e, conv.id)}
                    title="Delete"
                  >
                    <Trash2 size={13} />
                  </button>
                </div>
              ))}
            </>
          )}
        </div>

        <div className="sidebar-footer">
          <div className="sidebar-user">
            <div className="sidebar-user-avatar">{initials}</div>
            <span className="sidebar-user-email">{userEmail}</span>
            <button className="logout-btn" onClick={handleLogout} title="Logout">
              <LogOut size={16} />
            </button>
          </div>
        </div>
      </aside>

      <main className="main">
        <header className="chat-header">
          <button className="menu-btn" onClick={() => setSidebarOpen(true)}>
            <Menu size={20} />
          </button>
          <div>
            <div className="chat-header-title">
              {activeConv?.title || (currentConversationId ? 'Conversation' : 'New Conversation')}
            </div>
            <div className="chat-header-subtitle">Powered by GPT-o3 120B</div>
          </div>
        </header>

        <div className="messages-area">
          {messages.length === 0 && (
            <div className="empty-state">
              <div className="empty-state-icon"><Bot size={28} /></div>
              <h3>How can I help you?</h3>
              <p>Start a conversation or select one from the sidebar.</p>
            </div>
          )}

          {showSuggestions && (
            <div className="suggestion-chips">
              {SUGGESTIONS.map((s, i) => (
                <button key={i} className="chip" onClick={() => handleSuggestion(s)}>
                  {s}
                </button>
              ))}
            </div>
          )}

          {messages.map((msg, i) => (
            <div key={i} className={`message-row ${msg.role}`}>
              <div className={`avatar ${msg.role === 'assistant' ? 'bot' : 'user'}`}>
                {msg.role === 'assistant' ? <Bot size={16} /> : <User size={15} />}
              </div>
              <div className="message-content">
                <div className={`bubble ${msg.role === 'user' ? 'user' : 'assistant'}`}>
                  {msg.content}
                </div>
                <div className="message-meta">
                  {msg.time && <span className="message-time">{formatTime(msg.time)}</span>}
                  {msg.role === 'assistant' && (
                    <button
                      className="tts-btn"
                      onClick={() => handleTextToSpeech(msg.content)}
                      title="Read aloud"
                    >
                      <Volume2 size={13} />
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="typing-indicator">
              <div className="avatar bot"><Bot size={16} /></div>
              <div className="typing-dots">
                <div className="typing-dot" />
                <div className="typing-dot" />
                <div className="typing-dot" />
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        <div className="input-bar">
          <input type="file" ref={fileInputRef} onChange={handleFileUpload} style={{ display: 'none' }} />
          <div className="input-wrapper">
            <button className="icon-btn" onClick={() => fileInputRef.current?.click()} title="Attach file">
              <Paperclip size={18} />
            </button>

            <textarea
              ref={inputRef}
              className="text-input"
              placeholder="Message InsightAgent…"
              value={input}
              onChange={handleInputChange}
              onKeyDown={handleKeyDown}
              disabled={isLoading}
              rows={1}
            />

            <button
              className={`icon-btn ${isRecording ? 'recording' : ''}`}
              onClick={startRecording}
              title={isRecording ? 'Stop recording' : 'Start recording'}
            >
              {isRecording ? <MicOff size={18} /> : <Mic size={18} />}
            </button>

            <button
              className="send-btn"
              onClick={sendMessage}
              disabled={!input.trim() || isLoading}
              title="Send"
            >
              {isLoading
                ? <Loader2 size={18} className="spin" />
                : <Send size={18} />}
            </button>
          </div>
          <p className="input-hint">Enter to send · Shift+Enter for new line</p>
        </div>
      </main>
    </div>
  )
}
