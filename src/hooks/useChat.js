import { useState, useCallback } from 'react'

export const useChat = (gatewayUrl) => {
  const [messages, setMessages] = useState([])
  const [isLoading, setIsLoading] = useState(false)

  const sendMessage = useCallback(async (message) => {
    setIsLoading(true)
    
    try {
      const response = await fetch(`${gatewayUrl}/send-message`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message,
          language: 'vi'
        }),
      })

      if (response.ok) {
        const data = await response.json()
        return data.response
      } else {
        throw new Error('Failed to send message')
      }
    } catch (error) {
      console.error('Error sending message:', error)
      throw error
    } finally {
      setIsLoading(false)
    }
  }, [gatewayUrl])

  const addMessage = useCallback((message) => {
    setMessages(prev => [...prev, message])
  }, [])

  const clearMessages = useCallback(() => {
    setMessages([])
  }, [])

  return {
    messages,
    isLoading,
    sendMessage,
    addMessage,
    clearMessages
  }
}
