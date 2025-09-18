// StillMe Desktop - Professional Chat Interface
import React, { useState, useEffect, useRef } from 'react';
import './App.css';

interface Message {
  id: string;
  message: string;
  timestamp: string;
  from: string;
  type: 'sent' | 'received' | 'system';
}

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [messageText, setMessageText] = useState('');
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected'>('connecting');
  const [wsStatus, setWsStatus] = useState('Connecting...');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);

  // Auto scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // WebSocket connection
  useEffect(() => {
    const connectWebSocket = () => {
      try {
        const ws = new WebSocket('ws://localhost:8000/ws/desktop-client');
        wsRef.current = ws;

        ws.onopen = () => {
          console.log('✅ Desktop WebSocket connected');
          setConnectionStatus('connected');
          setWsStatus('Connected to Gateway');
          
          // Add system message
          const systemMessage: Message = {
            id: Date.now().toString(),
            message: 'Connected to StillMe Gateway successfully!',
            timestamp: new Date().toISOString(),
            from: 'system',
            type: 'system'
          };
          setMessages(prev => [...prev, systemMessage]);
        };

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            console.log('📨 Received message:', data);
            
            if (data.type === 'message') {
              const newMessage: Message = {
                id: Date.now().toString() + Math.random(),
                message: data.data.message,
                timestamp: data.timestamp || new Date().toISOString(),
                from: data.from || 'mobile-client',
                type: 'received'
              };
              setMessages(prev => [...prev, newMessage]);
            }
          } catch (error) {
            console.error('❌ Error parsing message:', error);
          }
        };

        ws.onclose = () => {
          console.log('❌ Desktop WebSocket disconnected');
          setConnectionStatus('disconnected');
          setWsStatus('Disconnected from Gateway');
          
          // Add system message
          const systemMessage: Message = {
            id: Date.now().toString(),
            message: 'Disconnected from Gateway. Attempting to reconnect...',
            timestamp: new Date().toISOString(),
            from: 'system',
            type: 'system'
          };
          setMessages(prev => [...prev, systemMessage]);
          
          // Reconnect after 3 seconds
          setTimeout(connectWebSocket, 3000);
        };

        ws.onerror = (error) => {
          console.error('❌ WebSocket error:', error);
          setConnectionStatus('disconnected');
          setWsStatus('Connection Error');
        };

      } catch (error) {
        console.error('❌ Failed to connect WebSocket:', error);
        setConnectionStatus('disconnected');
        setWsStatus('Connection Failed');
      }
    };

    connectWebSocket();

    // Cleanup
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  // HTTP Polling fallback
  useEffect(() => {
    const pollForMessages = async () => {
      try {
        const response = await fetch('http://localhost:8000/messages/desktop-client');
        if (response.ok) {
          const data = await response.json();
          if (data.messages && data.messages.length > 0) {
            data.messages.forEach((msg: any) => {
              const newMessage: Message = {
                id: Date.now().toString() + Math.random(),
                message: msg.message,
                timestamp: msg.timestamp,
                from: msg.from,
                type: 'received'
              };
              setMessages(prev => [...prev, newMessage]);
            });
          }
        }
      } catch (error) {
        console.error('❌ Polling error:', error);
      }
    };

    const interval = setInterval(pollForMessages, 3000);
    return () => clearInterval(interval);
  }, [connectionStatus]);

  const sendMessage = async () => {
    if (!messageText.trim()) return;

    const newMessage: Message = {
      id: Date.now().toString(),
      message: messageText,
      timestamp: new Date().toISOString(),
      from: 'desktop-client',
      type: 'sent'
    };

    setMessages(prev => [...prev, newMessage]);
    setMessageText('');

    try {
    // Send to StillMe AI via HTTP POST
    const response = await fetch('http://localhost:8000/send-message', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        target: 'stillme-ai',
        from: 'desktop-client',
        message: messageText,
        timestamp: new Date().toISOString()
      })
    });

      if (response.ok) {
        console.log('✅ Message sent successfully');
      } else {
        console.error('❌ Failed to send message');
      }
    } catch (error) {
      console.error('❌ Error sending message:', error);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="app">
      {/* Header */}
      <div className="header">
        <div className="header-content">
          <div className="logo">
            <div className="logo-shield">
              <span className="logo-s">S</span>
            </div>
            <div className="logo-text">
              <h1>StillMe AI</h1>
              <p>Desktop Chat</p>
            </div>
          </div>
          <div className="status">
            <div className={`status-indicator ${connectionStatus}`}></div>
            <span className="status-text">{wsStatus}</span>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="messages-container">
        {messages.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">💬</div>
            <h3>Welcome to StillMe AI Chat</h3>
            <p>Start a conversation with your mobile device!</p>
          </div>
        ) : (
          messages.map((msg) => (
            <div key={msg.id} className={`message ${msg.type}`}>
              <div className="message-content">
                <div className="message-text">{msg.message}</div>
                <div className="message-time">
                  {new Date(msg.timestamp).toLocaleTimeString()}
                </div>
              </div>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="input-container">
        <div className="input-wrapper">
          <textarea
            value={messageText}
            onChange={(e) => setMessageText(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your message here..."
            className="message-input"
            rows={1}
          />
          <button
            onClick={sendMessage}
            disabled={!messageText.trim()}
            className="send-button"
          >
            ➤
          </button>
        </div>
      </div>
    </div>
  );
}

export default App;

