// src/services/apiService.js
const API_BASE = 'http://localhost:8000'

class ApiService {
  async sendMessage(text, sessionId = null, locale = null) {
    try {
      const payload = { text }
      if (sessionId) payload.session_id = sessionId
      if (locale) payload.locale = locale

      console.log('Sending to backend:', payload)

      const response = await fetch(`${API_BASE}/channels/webchat/message`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload)
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      console.log('Backend response:', data)
      return data

    } catch (error) {
      console.error('API Error:', error)
      throw error
    }
  }

  async getSuggestions(language = 'en') {
    try {
      const response = await fetch(`${API_BASE}/channels/webchat/suggestions?language=${language}`)
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      return data
    } catch (error) {
      console.error('Suggestions API Error:', error)
      return { suggestions: [] }
    }
  }

  // Simple language detection
  detectLanguage(text) {
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
}

export default new ApiService()