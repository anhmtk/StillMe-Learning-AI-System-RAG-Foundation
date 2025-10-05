import React from 'react'
import { motion } from 'framer-motion'
import { Send, Loader2 } from 'lucide-react'

const InputArea = ({ 
  inputValue, 
  setInputValue, 
  onSendMessage, 
  onKeyPress, 
  isTyping, 
  isDark 
}) => {
  const handleSubmit = (e) => {
    e.preventDefault()
    if (!isTyping && inputValue.trim()) {
      onSendMessage()
    }
  }

  return (
    <motion.div
      initial={{ y: 100 }}
      animate={{ y: 0 }}
      className={`border-t ${
        isDark ? 'border-gray-700 bg-gray-900' : 'border-gray-200 bg-white'
      }`}
    >
      <div className="max-w-4xl mx-auto p-4">
        <form onSubmit={handleSubmit} className="flex items-end space-x-3">
          {/* Input Field */}
          <div className="flex-1 relative">
            <textarea
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={onKeyPress}
              placeholder="Nhập tin nhắn của bạn..."
              disabled={isTyping}
              className={`w-full px-4 py-3 pr-12 rounded-2xl border resize-none transition-colors ${
                isDark
                  ? 'bg-gray-800 border-gray-700 text-gray-100 placeholder-gray-400 focus:border-primary-500'
                  : 'bg-gray-50 border-gray-300 text-gray-900 placeholder-gray-500 focus:border-primary-500'
              } focus:outline-none focus:ring-2 focus:ring-primary-500/20`}
              rows={1}
              style={{
                minHeight: '48px',
                maxHeight: '120px',
              }}
              onInput={(e) => {
                e.target.style.height = 'auto'
                e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px'
              }}
            />
            
            {/* Character Count */}
            {inputValue.length > 0 && (
              <div className={`absolute bottom-1 right-12 text-xs ${
                isDark ? 'text-gray-400' : 'text-gray-500'
              }`}>
                {inputValue.length}/1000
              </div>
            )}
          </div>

          {/* Send Button */}
          <motion.button
            type="submit"
            disabled={!inputValue.trim() || isTyping}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className={`p-3 rounded-full transition-all duration-200 ${
              inputValue.trim() && !isTyping
                ? 'bg-primary-500 hover:bg-primary-600 text-white shadow-lg'
                : isDark
                  ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
                  : 'bg-gray-200 text-gray-400 cursor-not-allowed'
            }`}
          >
            {isTyping ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Send className="w-5 h-5" />
            )}
          </motion.button>
        </form>

        {/* Helper Text */}
        <div className={`text-xs mt-2 text-center ${
          isDark ? 'text-gray-400' : 'text-gray-500'
        }`}>
          Nhấn Enter để gửi, Shift + Enter để xuống dòng
        </div>
      </div>
    </motion.div>
  )
}

export default InputArea
