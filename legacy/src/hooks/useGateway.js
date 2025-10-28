import { useState, useCallback } from 'react'

export const useGateway = (gatewayUrl) => {
  const [isConnected, setIsConnected] = useState(false)
  const [isChecking, setIsChecking] = useState(false)

  const checkConnection = useCallback(async () => {
    setIsChecking(true)
    try {
      const response = await fetch(`${gatewayUrl}/health`, {
        method: 'GET',
        mode: 'cors',
        headers: {
          'Content-Type': 'application/json',
        }
      })
      
      if (response.ok) {
        const data = await response.json()
        setIsConnected(data.status === 'healthy')
      } else {
        setIsConnected(false)
      }
    } catch (error) {
      console.error('Gateway connection check failed:', error)
      setIsConnected(false)
    } finally {
      setIsChecking(false)
    }
  }, [gatewayUrl])

  return { isConnected, isChecking, checkConnection }
}
