import React from 'react'
import { motion } from 'framer-motion'
import { 
  Bot, 
  Moon, 
  Sun, 
  Wifi, 
  WifiOff, 
  RefreshCw,
  Trash2,
  Settings,
  Server,
  Home
} from 'lucide-react'

const Header = ({ isDark, toggleTheme, isConnected, onCheckConnection, onClearChat, useVPS, onToggleGateway, currentGatewayUrl }) => {
  return (
    <motion.header 
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      className="gradient-header shadow-lg"
    >
      <div className="max-w-4xl mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          {/* Logo and Title */}
          <div className="flex items-center space-x-3">
            <motion.div
              whileHover={{ rotate: 360 }}
              transition={{ duration: 0.5 }}
              className="p-2 bg-white/20 rounded-full"
            >
              <Bot className="w-8 h-8 text-white" />
            </motion.div>
            <div>
              <h1 className="text-2xl font-bold text-white">StillMe AI</h1>
              <p className="text-white/80 text-sm">Trợ lý AI thông minh</p>
            </div>
          </div>

          {/* Status and Controls */}
          <div className="flex items-center space-x-4">
            {/* Gateway Toggle */}
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={onToggleGateway}
              className={`flex items-center space-x-2 px-3 py-1 rounded-full transition-colors ${
                useVPS 
                  ? 'bg-orange-500/20 text-orange-200 border border-orange-400/30' 
                  : 'bg-green-500/20 text-green-200 border border-green-400/30'
              }`}
              title={useVPS ? "Đang dùng VPS - Click để chuyển Local" : "Đang dùng Local - Click để chuyển VPS"}
            >
              {useVPS ? (
                <>
                  <Server className="w-4 h-4" />
                  <span className="text-sm">VPS</span>
                </>
              ) : (
                <>
                  <Home className="w-4 h-4" />
                  <span className="text-sm">Local</span>
                </>
              )}
            </motion.button>

            {/* Connection Status */}
            <div className="flex items-center space-x-2">
              {isConnected ? (
                <div className="flex items-center space-x-1 text-green-200">
                  <Wifi className="w-4 h-4" />
                  <span className="text-sm">Đã kết nối</span>
                </div>
              ) : (
                <div className="flex items-center space-x-1 text-red-200">
                  <WifiOff className="w-4 h-4" />
                  <span className="text-sm">Mất kết nối</span>
                </div>
              )}
            </div>

            {/* Control Buttons */}
            <div className="flex items-center space-x-2">
              {/* Refresh Connection */}
              <motion.button
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.9 }}
                onClick={onCheckConnection}
                className="p-2 bg-white/20 hover:bg-white/30 rounded-full transition-colors"
                title="Kiểm tra kết nối"
              >
                <RefreshCw className="w-4 h-4 text-white" />
              </motion.button>

              {/* Clear Chat */}
              <motion.button
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.9 }}
                onClick={onClearChat}
                className="p-2 bg-white/20 hover:bg-white/30 rounded-full transition-colors"
                title="Xóa chat"
              >
                <Trash2 className="w-4 h-4 text-white" />
              </motion.button>

              {/* Theme Toggle */}
              <motion.button
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.9 }}
                onClick={toggleTheme}
                className="p-2 bg-white/20 hover:bg-white/30 rounded-full transition-colors"
                title={isDark ? "Chế độ sáng" : "Chế độ tối"}
              >
                {isDark ? (
                  <Sun className="w-4 h-4 text-white" />
                ) : (
                  <Moon className="w-4 h-4 text-white" />
                )}
              </motion.button>
            </div>
          </div>
        </div>
      </div>
    </motion.header>
  )
}

export default Header
