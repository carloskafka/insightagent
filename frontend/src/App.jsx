
import React, { useState, useRef, useEffect } from 'react';

export default function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [token, setToken] = useState(localStorage.getItem('token') || '');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoggedIn, setIsLoggedIn] = useState(!!token);
  const [conversations, setConversations] = useState([]);
  const [currentConversationId, setCurrentConversationId] = useState(null);
  
  const messagesEndRef = useRef(null);
  const wsRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (token && isLoggedIn) {
      fetchConversations();
      connectWebSocket();
    }
  }, [token, isLoggedIn]);

  const fetchConversations = async () => {
    try {
      const response = await fetch('http://localhost:8000/conversations', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setConversations(data);
      }
    } catch (error) {
      console.error('Error fetching conversations:', error);
    }
  };

  const connectWebSocket = () => {
    wsRef.current = new WebSocket('ws://localhost:8000/ws');
    
    wsRef.current.onopen = () => {
      console.log('WebSocket connected');
    };
    
    wsRef.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setMessages(prev => [...prev, { role: 'assistant', content: data.response }]);
      setIsLoading(false);
    };
    
    wsRef.current.onclose = () => {
      console.log('WebSocket disconnected');
    };
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const formData = new URLSearchParams();
      formData.append('username', email);
      formData.append('password', password);
      
      const response = await fetch('http://localhost:8000/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: formData
      });
      
      if (response.ok) {
        const data = await response.json();
        setToken(data.access_token);
        localStorage.setItem('token', data.access_token);
        setIsLoggedIn(true);
      } else {
        alert('Login failed');
      }
    } catch (error) {
      console.error('Login error:', error);
      alert('Login failed');
    }
  };

  const handleSignup = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch('http://localhost:8000/signup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });
      
      if (response.ok) {
        alert('Signup successful! Please login.');
      } else {
        const data = await response.json();
        alert(data.detail || 'Signup failed');
      }
    } catch (error) {
      console.error('Signup error:', error);
      alert('Signup failed');
    }
  };

  const handleLogout = () => {
    setToken('');
    localStorage.removeItem('token');
    setIsLoggedIn(false);
    setMessages([]);
    setConversations([]);
    if (wsRef.current) {
      wsRef.current.close();
    }
  };

  const sendMessage = async () => {
    if (!input.trim() || !token) return;
    
    const userMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);
    
    try {
      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          message: input,
          conversation_id: currentConversationId
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        setMessages(prev => [...prev, { role: 'assistant', content: data.response }]);
        setCurrentConversationId(data.conversation_id);
        fetchConversations();
      }
    } catch (error) {
      console.error('Send message error:', error);
      setMessages(prev => [...prev, { role: 'assistant', content: 'Error: Could not get response' }]);
    }
    
    setIsLoading(false);
  };

  const sendViaWebSocket = () => {
    if (!input.trim() || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
    
    const userMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);
    
    wsRef.current.send(JSON.stringify({ message: input }));
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file || !token) return;
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      const response = await fetch('http://localhost:8000/upload', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
      });
      
      if (response.ok) {
        alert('File uploaded successfully!');
      } else {
        alert('Upload failed');
      }
    } catch (error) {
      console.error('Upload error:', error);
      alert('Upload failed');
    }
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);
      audioChunksRef.current = [];
      
      mediaRecorderRef.current.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data);
      };
      
      mediaRecorderRef.current.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        await sendAudio(audioBlob);
      };
      
      mediaRecorderRef.current.start();
      setIsRecording(true);
    } catch (error) {
      console.error('Error starting recording:', error);
      alert('Could not access microphone');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const sendAudio = async (audioBlob) => {
    if (!token) return;
    
    const formData = new FormData();
    formData.append('audio', audioBlob, 'recording.webm');
    
    try {
      const response = await fetch('http://localhost:8000/voice', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
      });
      
      if (response.ok) {
        const data = await response.json();
        setMessages(prev => [
          ...prev,
          { role: 'user', content: data.text },
          { role: 'assistant', content: data.response }
        ]);
      }
    } catch (error) {
      console.error('Voice error:', error);
    }
  };

  const handleTextToSpeech = async (text) => {
    try {
      const response = await fetch(`http://localhost:8000/tts?text=${encodeURIComponent(text)}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const blob = await response.blob();
        const audioUrl = URL.createObjectURL(blob);
        const audio = new Audio(audioUrl);
        audio.play();
      }
    } catch (error) {
      console.error('TTS error:', error);
    }
  };

  const selectConversation = (convId) => {
    setCurrentConversationId(convId);
    // Load conversation messages (implement as needed)
  };

  if (!isLoggedIn) {
    return (
      <div style={styles.container}>
        <h1 style={styles.title}>Chatbot Login</h1>
        <form onSubmit={handleLogin} style={styles.form}>
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            style={styles.input}
            required
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            style={styles.input}
            required
          />
          <button type="submit" style={styles.button}>Login</button>
          <button type="button" onClick={handleSignup} style={styles.secondaryButton}>Sign Up</button>
        </form>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      <header style={styles.header}>
        <h1 style={styles.title}>Chatbot</h1>
        <button onClick={handleLogout} style={styles.logoutButton}>Logout</button>
      </header>
      
      <div style={styles.main}>
        {conversations.length > 0 && (
          <aside style={styles.sidebar}>
            <h3>Conversations</h3>
            {conversations.map(conv => (
              <div
                key={conv.id}
                onClick={() => selectConversation(conv.id)}
                style={{
                  ...styles.conversationItem,
                  backgroundColor: conv.id === currentConversationId ? '#e0e0e0' : 'transparent'
                }}
              >
                {conv.title}
              </div>
            ))}
          </aside>
        )}
        
        <div style={styles.chatContainer}>
          <div style={styles.messagesContainer}>
            {messages.map((msg, index) => (
              <div
                key={index}
                style={{
                  ...styles.message,
                  alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
                  backgroundColor: msg.role === 'user' ? '#007bff' : '#f0f0f0',
                  color: msg.role === 'user' ? 'white' : 'black'
                }}
              >
                {msg.content}
                {msg.role === 'assistant' && (
                  <button
                    onClick={() => handleTextToSpeech(msg.content)}
                    style={styles.ttsButton}
                  >
                    🔊
                  </button>
                )}
              </div>
            ))}
            {isLoading && <div style={styles.loading}>Thinking...</div>}
            <div ref={messagesEndRef} />
          </div>
          
          <div style={styles.inputContainer}>
            <input
              type="file"
              id="file-upload"
              onChange={handleFileUpload}
              style={{ display: 'none' }}
            />
            <label htmlFor="file-upload" style={styles.iconButton}>📎</label>
            
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
              placeholder="Type a message..."
              style={styles.textInput}
              disabled={isLoading}
            />
            
            <button
              onClick={sendMessage}
              disabled={isLoading || !input.trim()}
              style={styles.sendButton}
            >
              Send
            </button>
            
            <button
              onMouseDown={startRecording}
              onMouseUp={stopRecording}
              onTouchStart={startRecording}
              onTouchEnd={stopRecording}
              style={{
                ...styles.recordButton,
                backgroundColor: isRecording ? 'red' : '#ccc'
              }}
            >
              🎤
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

const styles = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    height: '100vh',
    fontFamily: 'Arial, sans-serif'
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '10px 20px',
    backgroundColor: '#333',
    color: 'white'
  },
  title: {
    margin: 0,
    fontSize: '24px'
  },
  form: {
    display: 'flex',
    flexDirection: 'column',
    maxWidth: '300px',
    margin: '50px auto',
    gap: '10px'
  },
  input: {
    padding: '10px',
    fontSize: '16px',
    border: '1px solid #ccc',
    borderRadius: '4px'
  },
  button: {
    padding: '10px 20px',
    backgroundColor: '#007bff',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '16px'
  },
  secondaryButton: {
    padding: '10px 20px',
    backgroundColor: '#6c757d',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '16px'
  },
  logoutButton: {
    padding: '8px 16px',
    backgroundColor: '#dc3545',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer'
  },
  main: {
    display: 'flex',
    flex: 1,
    overflow: 'hidden'
  },
  sidebar: {
    width: '250px',
    backgroundColor: '#f5f5f5',
    padding: '10px',
    borderRight: '1px solid #ddd',
    overflowY: 'auto'
  },
  conversationItem: {
    padding: '10px',
    cursor: 'pointer',
    borderRadius: '4px',
    marginBottom: '5px',
    whiteSpace: 'nowrap',
    overflow: 'hidden',
    textOverflow: 'ellipsis'
  },
  chatContainer: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column'
  },
  messagesContainer: {
    flex: 1,
    padding: '20px',
    overflowY: 'auto',
    display: 'flex',
    flexDirection: 'column',
    gap: '10px'
  },
  message: {
    maxWidth: '70%',
    padding: '10px 15px',
    borderRadius: '10px',
    wordWrap: 'break-word',
    display: 'flex',
    alignItems: 'center',
    gap: '8px'
  },
  ttsButton: {
    background: 'none',
    border: 'none',
    cursor: 'pointer',
    fontSize: '16px'
  },
  loading: {
    textAlign: 'center',
    color: '#666',
    fontStyle: 'italic'
  },
  inputContainer: {
    display: 'flex',
    padding: '10px 20px',
    borderTop: '1px solid #ddd',
    gap: '10px',
    alignItems: 'center'
  },
  textInput: {
    flex: 1,
    padding: '10px',
    fontSize: '16px',
    border: '1px solid #ccc',
    borderRadius: '4px'
  },
  sendButton: {
    padding: '10px 20px',
    backgroundColor: '#007bff',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer'
  },
  recordButton: {
    padding: '10px',
    border: 'none',
    borderRadius: '50%',
    cursor: 'pointer',
    fontSize: '20px',
    width: '44px',
    height: '44px'
  },
  iconButton: {
    cursor: 'pointer',
    fontSize: '20px',
    padding: '10px'
  }
};
