const API_BASE = 'http://localhost:8000'

class ApiService {
  // EXISTING METHODS
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

  // 🔥 NEW: STREAMING METHODS
  /**
   * 🔥 NEW: Send streaming message using Server-Sent Events
   * @param {string} text - User message
   * @param {string|null} sessionId - Session ID
   * @param {string|null} locale - Language locale
   * @param {function} onToken - Callback for each token received
   * @param {function} onComplete - Callback when complete
   * @param {function} onError - Callback for errors
   */
  async sendStreamingMessage(text, sessionId = null, locale = null, onToken, onComplete, onError) {
    try {
      const payload = { text }
      if (sessionId) payload.session_id = sessionId
      if (locale) payload.locale = locale

      console.log('Starting streaming request:', payload)

      // Create fetch request for streaming
      const response = await fetch(`${API_BASE}/channels/webchat/message/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload)
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      // Read the stream
      const reader = response.body.getReader()
      const decoder = new TextDecoder()

      let buffer = ''
      let sessionIdFromStream = null

      while (true) {
        const { done, value } = await reader.read()
        
        if (done) break

        // Decode the chunk
        buffer += decoder.decode(value, { stream: true })
        
        // Process complete lines (SSE format: "data: {json}\n\n")
        const lines = buffer.split('\n\n')
        buffer = lines.pop() || '' // Keep incomplete line in buffer

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6)) // Remove "data: " prefix
              
              console.log('Received chunk:', data)

              // Handle different chunk types
              switch (data.type) {
                case 'session':
                  sessionIdFromStream = data.session_id
                  break
                  
                case 'token':
                  // Call token callback with the new token
                  if (onToken) {
                    onToken({
                      token: data.content,
                      fullText: data.full_text,
                      tokenCount: data.token_count,
                      language: data.language
                    })
                  }
                  break
                  
                case 'complete':
                  // Call completion callback with final data
                  if (onComplete) {
                    onComplete({
                      sessionId: sessionIdFromStream,
                      text: data.content,
                      language: data.language,
                      sources: data.sources,
                      confidence: data.confidence,
                      metadata: data.metadata
                    })
                  }
                  break
                  
                case 'error':
                  if (onError) {
                    onError(new Error(data.content || 'Streaming error occurred'))
                  }
                  break
                  
                case 'done':
                  console.log('Stream completed')
                  return // Exit the function
              }
            } catch (parseError) {
              console.error('Failed to parse SSE data:', parseError)
            }
          }
        }
      }

    } catch (error) {
      console.error('Streaming API Error:', error)
      if (onError) {
        onError(error)
      }
    }
  }

  // 🔥 NEW: Simplified streaming method for easy use
  async streamMessage(text, sessionId = null, locale = null) {
    return new Promise((resolve, reject) => {
      let currentMessage = {
        id: Date.now(),
        role: 'assistant',
        text: '',
        timestamp: new Date(),
        isStreaming: true,
        confidence: 0,
        sources: [],
        language: locale || 'en'
      }

      const tokens = []

      this.sendStreamingMessage(
        text,
        sessionId,
        locale,
        // onToken
        (tokenData) => {
          tokens.push(tokenData.token)
          currentMessage.text = tokenData.fullText
          currentMessage.language = tokenData.language
          currentMessage.tokenCount = tokenData.tokenCount
          
          // You can emit events here if using an event system
          // EventBus.emit('token-received', currentMessage)
        },
        // onComplete
        (completeData) => {
          currentMessage.isStreaming = false
          currentMessage.confidence = completeData.confidence
          currentMessage.sources = completeData.sources
          currentMessage.sessionId = completeData.sessionId
          currentMessage.metadata = completeData.metadata
          
          resolve(currentMessage)
        },
        // onError
        (error) => {
          currentMessage.isStreaming = false
          currentMessage.text = currentMessage.text || 'Sorry, I encountered an error.'
          currentMessage.error = error.message
          
          reject(error)
        }
      )
    })
  }

  // 🔥 NEW: Check if streaming is supported by browser
  isStreamingSupported() {
    return typeof window !== 'undefined' && 
           typeof ReadableStream !== 'undefined' && 
           typeof TextDecoder !== 'undefined'
  }

  // 🔥 NEW: Get streaming status
  getStreamingCapabilities() {
    return {
      supported: this.isStreamingSupported(),
      hasTextDecoder: typeof TextDecoder !== 'undefined',
      hasReadableStream: typeof ReadableStream !== 'undefined',
      hasFetch: typeof fetch !== 'undefined'
    }
  }
}

export default new ApiService()