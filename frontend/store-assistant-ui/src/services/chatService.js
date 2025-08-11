// src/services/chatService.js - SEPARATE FILE
import { chatAPI, detectLanguage } from '@/stores/api'

class ChatService {
  constructor() {
    this.sessionId = localStorage.getItem('sessionId') || null
  }

  async sendMessage(text, locale = null) {
    try {
      // Auto-detect language if not provided
      const detectedLanguage = locale || detectLanguage(text)
      
      console.log(`Sending message: "${text}" (${detectedLanguage})`)
      
      const response = await chatAPI.sendMessage(text, this.sessionId, detectedLanguage)
      
      // Update session ID
      if (response.session_id) {
        this.sessionId = response.session_id
        localStorage.setItem('sessionId', response.session_id)
      }
      
      return response
    } catch (error) {
      console.error('ChatService: Send message failed:', error)
      throw error
    }
  }

  async getSuggestions(language = 'en') {
    try {
      return await chatAPI.getSuggestions(language)
    } catch (error) {
      console.error('ChatService: Get suggestions failed:', error)
      return { suggestions: [] }
    }
  }

  async getHistory() {
    if (!this.sessionId) return { history: [] }
    
    try {
      return await chatAPI.getHistory(this.sessionId)
    } catch (error) {
      console.error('ChatService: Get history failed:', error)
      return { history: [] }
    }
  }

  clearSession() {
    this.sessionId = null
    localStorage.removeItem('sessionId')
  }

  getSessionId() {
    return this.sessionId
  }

  // Language detection utility
  detectLanguage(text) {
    return detectLanguage(text)
  }
}

// Export singleton instance as default
export default new ChatService()