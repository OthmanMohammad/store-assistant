// src/stores/api.js - FIXED VERSION
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

// Create axios instance
const apiClient = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json'
  },
  timeout: 30000 // 30 seconds timeout
})

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    // Add any auth headers here if needed
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`)
    return config
  },
  (error) => {
    console.error('API Request Error:', error)
    return Promise.reject(error)
  }
)

// Response interceptor
apiClient.interceptors.response.use(
  (response) => {
    console.log(`API Response: ${response.status} ${response.config.url}`)
    return response
  },
  (error) => {
    console.error('API Response Error:', error.response?.data || error.message)
    
    // Handle specific error cases
    if (error.response?.status === 404) {
      console.error('API endpoint not found')
    } else if (error.response?.status >= 500) {
      console.error('Server error occurred')
    } else if (error.code === 'ECONNABORTED') {
      console.error('Request timeout')
    }
    
    return Promise.reject(error)
  }
)

// Chat API functions
export const chatAPI = {
  // Send message to chat endpoint
  async sendMessage(text, sessionId = null, locale = null) {
    try {
      const payload = { text }
      if (sessionId) payload.session_id = sessionId
      if (locale) payload.locale = locale

      const response = await apiClient.post('/channels/webchat/message', payload)
      return response.data
    } catch (error) {
      throw new Error(`Failed to send message: ${error.message}`)
    }
  },

  // Get suggested questions
  async getSuggestions(language = 'en') {
    try {
      const response = await apiClient.get(`/channels/webchat/suggestions?language=${language}`)
      return response.data
    } catch (error) {
      console.error('Failed to get suggestions:', error)
      return { suggestions: [] }
    }
  },

  // Get conversation history
  async getHistory(sessionId) {
    try {
      const response = await apiClient.get(`/channels/webchat/history/${sessionId}`)
      return response.data
    } catch (error) {
      console.error('Failed to get history:', error)
      return { history: [] }
    }
  },

  // Test debug endpoint
  async debugMessage(text, locale = null) {
    try {
      const payload = { text }
      if (locale) payload.locale = locale

      const response = await apiClient.post('/channels/webchat/debug', payload)
      return response.data
    } catch (error) {
      throw new Error(`Debug request failed: ${error.message}`)
    }
  }
}

// Utility functions
export const detectLanguage = (text) => {
  if (!text.trim()) return 'en'
  
  // Count Arabic characters
  let arabicChars = 0
  let totalChars = 0
  
  for (let char of text) {
    if (/[\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF]/.test(char)) {
      arabicChars++
    }
    if (/[a-zA-Z\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF]/.test(char)) {
      totalChars++
    }
  }
  
  if (totalChars === 0) return 'en'
  
  const arabicRatio = arabicChars / totalChars
  return arabicRatio > 0.15 ? 'ar' : 'en'
}

// Health check function
export const healthCheck = async () => {
  try {
    const response = await apiClient.get('/health/readyz')
    return response.status === 200
  } catch (error) {
    console.error('Health check failed:', error)
    return false
  }
}

// ONLY ONE DEFAULT EXPORT - Export the axios instance
export default apiClient