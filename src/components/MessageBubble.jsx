import React from 'react'
import { motion } from 'framer-motion'
import { Bot, User } from 'lucide-react'

const MessageBubble = ({ message, isDark }) => {
  const isUser = message.type === 'user'
  const isAI = message.type === 'ai'

  return (
    <motion.div
      initial={{ opacity: 0, y: 20, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ 
        duration: 0.3,
        ease: "easeOut"
      }}
      className={`flex items-end space-x-2 max-w-xs lg:max-w-md ${
        isUser ? 'flex-row-reverse space-x-reverse ml-auto' : 'mr-auto'
      }`}
    >
      {/* Avatar */}
      <motion.div
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={{ delay: 0.1, duration: 0.2 }}
        className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm ${
          isUser 
            ? 'bg-primary-500 text-white' 
            : isDark 
              ? 'bg-gray-700 text-gray-200' 
              : 'bg-gray-200 text-gray-700'
        }`}
      >
        {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
      </motion.div>

      {/* Message Content */}
      <motion.div
        initial={{ opacity: 0, x: isUser ? 20 : -20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ delay: 0.1, duration: 0.3 }}
        className={`relative px-4 py-3 rounded-2xl shadow-sm ${
          isUser
            ? 'bg-primary-500 text-white rounded-br-md'
            : isDark
              ? 'bg-gray-800 text-gray-100 rounded-bl-md border border-gray-700'
              : 'bg-white text-gray-900 rounded-bl-md border border-gray-200'
        }`}
      >
        {/* Message Text */}
        <p className="text-sm leading-relaxed whitespace-pre-wrap">
          {message.content}
        </p>

        {/* Timestamp */}
        <div className={`text-xs mt-1 ${
          isUser 
            ? 'text-primary-100' 
            : isDark 
              ? 'text-gray-400' 
              : 'text-gray-500'
        }`}>
          {message.timestamp.toLocaleTimeString('vi-VN', { 
            hour: '2-digit', 
            minute: '2-digit' 
          })}
        </div>

        {/* Message Tail */}
        <div
          className={`absolute bottom-0 w-3 h-3 transform rotate-45 ${
            isUser
              ? 'bg-primary-500 -right-1'
              : isDark
                ? 'bg-gray-800 border-r border-b border-gray-700 -left-1'
                : 'bg-white border-r border-b border-gray-200 -left-1'
          }`}
        />
      </motion.div>
    </motion.div>
  )
}

export default MessageBubble
