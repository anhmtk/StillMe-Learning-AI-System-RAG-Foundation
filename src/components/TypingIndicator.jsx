import React from 'react'
import { motion } from 'framer-motion'
import { Bot } from 'lucide-react'

const TypingIndicator = ({ isDark }) => {
  return (
    <div className="flex items-end space-x-2 mr-auto">
      {/* AI Avatar */}
      <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
        isDark ? 'bg-gray-700 text-gray-200' : 'bg-gray-200 text-gray-700'
      }`}>
        <Bot className="w-4 h-4" />
      </div>

      {/* Typing Bubble */}
      <div className={`px-4 py-3 rounded-2xl rounded-bl-md shadow-sm ${
        isDark
          ? 'bg-gray-800 border border-gray-700'
          : 'bg-white border border-gray-200'
      }`}>
        <div className="flex items-center space-x-1">
          <span className={`text-xs ${
            isDark ? 'text-gray-400' : 'text-gray-500'
          }`}>
            StillMe đang trả lời
          </span>
          <div className="flex space-x-1 ml-2">
            {[0, 1, 2].map((index) => (
              <motion.div
                key={index}
                className={`w-1.5 h-1.5 rounded-full ${
                  isDark ? 'bg-gray-400' : 'bg-gray-500'
                }`}
                animate={{
                  scale: [1, 1.2, 1],
                  opacity: [0.5, 1, 0.5],
                }}
                transition={{
                  duration: 1.5,
                  repeat: Infinity,
                  delay: index * 0.2,
                }}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

export default TypingIndicator
