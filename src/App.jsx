import React, { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Send, 
  Moon, 
  Sun, 
  Bot, 
  User, 
  Loader2,
  Wifi,
  WifiOff,
  Settings,
  Trash2,
  Server,
  Home
} from 'lucide-react'
import { useChat } from './hooks/useChat'
import { useTheme } from './hooks/useTheme'
import { useGateway } from './hooks/useGateway'
import MessageBubble from './components/MessageBubble'
import TypingIndicator from './components/TypingIndicator'
import Header from './components/Header'
import InputArea from './components/InputArea'

// Toggle between VPS and Local Gateway
const VPS_GATEWAY_URL = "http://160.191.89.99:21568"
const LOCAL_GATEWAY_URL = "http://localhost:21568"

function App() {
  const [messages, setMessages] = useState([])
  const [inputValue, setInputValue] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const [useVPS, setUseVPS] = useState(true) // Toggle VPS/Local
  const { isDark, toggleTheme } = useTheme()
  
  // Dynamic gateway URL based on toggle
  const currentGatewayUrl = useVPS ? VPS_GATEWAY_URL : LOCAL_GATEWAY_URL
  const { isConnected, checkConnection } = useGateway(currentGatewayUrl)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  useEffect(() => {
    // Add welcome message
    setMessages([
      {
        id: 1,
        type: 'ai',
        content: 'Xin chào! Tôi là StillMe AI. Hãy gửi tin nhắn để bắt đầu trò chuyện! 😊',
        timestamp: new Date(),
        avatar: '🤖'
      }
    ])
    
    // Check connection on mount
    checkConnection()
  }, [currentGatewayUrl]) // Re-check when gateway URL changes

  const sendMessage = async () => {
    if (!inputValue.trim() || isTyping) return

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: inputValue.trim(),
      timestamp: new Date(),
      avatar: '👤'
    }

    setMessages(prev => [...prev, userMessage])
    setInputValue('')
    setIsTyping(true)

    try {
      const response = await fetch(`${currentGatewayUrl}/send-message`, {
        method: 'POST',
        mode: 'cors',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: inputValue.trim(),
          language: 'vi'
        }),
      })

      if (response.ok) {
        const data = await response.json()
        const aiMessage = {
          id: Date.now() + 1,
          type: 'ai',
          content: data.response || 'Xin lỗi, tôi không thể trả lời lúc này.',
          timestamp: new Date(),
          avatar: '🤖'
        }
        
        setTimeout(() => {
          setMessages(prev => [...prev, aiMessage])
          setIsTyping(false)
        }, 1000) // Simulate typing delay
      } else {
        throw new Error('Failed to send message')
      }
    } catch (error) {
      console.error('Error sending message:', error)
      const errorMessage = {
        id: Date.now() + 1,
        type: 'ai',
        content: 'Xin lỗi, có lỗi xảy ra khi kết nối đến server. Vui lòng thử lại sau.',
        timestamp: new Date(),
        avatar: '🤖'
      }
      
      setTimeout(() => {
        setMessages(prev => [...prev, errorMessage])
        setIsTyping(false)
      }, 1000)
    }
  }

  const clearChat = () => {
    setMessages([
      {
        id: 1,
        type: 'ai',
        content: 'Chat đã được xóa. Hãy gửi tin nhắn để bắt đầu trò chuyện! 😊',
        timestamp: new Date(),
        avatar: '🤖'
      }
    ])
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const toggleGateway = () => {
    setUseVPS(!useVPS)
    // Clear chat when switching gateway
    clearChat()
  }

  return (
    <div className={`min-h-screen transition-colors duration-300 ${
      isDark ? 'bg-gray-900' : 'bg-gray-50'
    }`}>
      {/* Header */}
      <Header 
        isDark={isDark}
        toggleTheme={toggleTheme}
        isConnected={isConnected}
        onCheckConnection={checkConnection}
        onClearChat={clearChat}
        useVPS={useVPS}
        onToggleGateway={toggleGateway}
        currentGatewayUrl={currentGatewayUrl}
      />

      {/* Main Chat Area */}
      <div className="flex flex-col h-[calc(100vh-80px)] max-w-4xl mx-auto">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          <AnimatePresence>
            {messages.map((message) => (
              <motion.div
                key={message.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.3 }}
                className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <MessageBubble message={message} isDark={isDark} />
              </motion.div>
            ))}
          </AnimatePresence>
          
          {/* Typing Indicator */}
          {isTyping && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex justify-start"
            >
              <TypingIndicator isDark={isDark} />
            </motion.div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <InputArea
          inputValue={inputValue}
          setInputValue={setInputValue}
          onSendMessage={sendMessage}
          onKeyPress={handleKeyPress}
          isTyping={isTyping}
          isDark={isDark}
        />
      </div>
    </div>
  )
}

export default App