<template>
  <div class="home-view">
    <!-- Header -->
    <div class="chat-header">
      <h1>🏪 Store Assistant</h1>
      <p>AI-powered customer service • Ask anything about our store!</p>
      <div class="language-indicator">{{ currentLanguage.toUpperCase() }}</div>
    </div>

    <!-- Chat Container -->
    <div class="chat-container">
      <!-- Messages Area -->
      <div class="messages-area" ref="messagesContainer">
        <div v-for="message in messages" :key="message.id" class="message" :class="message.role">
          <div class="bubble" :class="`${message.role}-bubble`">
            {{ message.text }}
            
            <!-- Bot message metadata -->
            <div v-if="message.role === 'assistant' && !message.isWelcome" class="message-meta">
              <div class="meta-row">
                <span v-if="message.confidence !== undefined" class="confidence" :class="getConfidenceClass(message.confidence)">
                  Confidence: {{ Math.round(message.confidence * 100) }}%
                </span>
                <span v-if="message.sources && message.sources.length > 0" class="sources">
                  Sources: {{ message.sources.slice(0, 2).join(', ') }}
                </span>
              </div>
              <div class="timestamp">
                {{ formatTime(message.timestamp) }}
              </div>
            </div>
          </div>
        </div>
        
        <!-- Typing indicator -->
        <div v-if="isTyping" class="message assistant">
          <div class="bubble assistant-bubble typing">
            <span class="typing-text">Thinking...</span>
          </div>
        </div>

        <!-- Error message -->
        <div v-if="error" class="error-message">
          {{ error }}
          <button @click="clearError">✕</button>
        </div>
      </div>

      <!-- Suggestions (show only when no messages) -->
      <div v-if="suggestions.length > 0 && messages.length <= 1" class="suggestions-panel">
        <h4>💡 Suggested Questions:</h4>
        <div class="suggestion-buttons">
          <button 
            v-for="suggestion in suggestions" 
            :key="suggestion"
            @click="sendMessage(suggestion)"
            class="suggestion-btn"
          >
            {{ suggestion }}
          </button>
        </div>
      </div>

      <!-- Input Area -->
      <div class="input-area">
        <div class="input-row">
          <input 
            v-model="inputText"
            @keypress.enter="sendMessage()"
            :placeholder="currentLanguage === 'ar' ? 'اكتب سؤالك هنا...' : 'Type your question...'"
            :disabled="isLoading"
            :dir="currentLanguage === 'ar' ? 'rtl' : 'ltr'"
            class="text-input"
          />
          <button 
            @click="sendMessage()" 
            :disabled="!canSend"
            class="send-btn"
            :class="{ 'enabled': canSend, 'disabled': !canSend }"
          >
            {{ isLoading ? 'Sending...' : (currentLanguage === 'ar' ? 'إرسال' : 'Send') }}
          </button>
        </div>
        
        <!-- Language detection hint -->
        <div v-if="detectedLanguage && detectedLanguage !== currentLanguage" class="language-hint">
          🌍 Detected {{ detectedLanguage === 'ar' ? 'Arabic' : 'English' }} - 
          <button @click="currentLanguage = detectedLanguage" class="lang-switch-btn">
            Switch to {{ detectedLanguage === 'ar' ? 'Arabic' : 'English' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Debug info -->
    <div class="debug-info">
      Session: {{ sessionId || 'New' }} | Language: {{ currentLanguage }} | Backend: {{ backendStatus }}
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted } from 'vue'
import apiService from '@/services/apiService'

// State
const inputText = ref('')
const isLoading = ref(false)
const isTyping = ref(false)
const error = ref(null)
const sessionId = ref(localStorage.getItem('sessionId') || null)
const currentLanguage = ref('en')
const detectedLanguage = ref(null)
const suggestions = ref([])
const backendStatus = ref('Unknown')

const messages = ref([
  {
    id: 'welcome',
    role: 'assistant',
    text: 'Hello! أهلاً وسهلاً! How can I help you today? كيف يمكنني مساعدتك؟',
    timestamp: new Date(),
    isWelcome: true
  }
])

const messagesContainer = ref(null)

// Computed
const canSend = computed(() => {
  return inputText.value.trim().length > 0 && !isLoading.value
})

// Methods
const sendMessage = async (messageText = null) => {
  const text = messageText || inputText.value.trim()
  if (!text || isLoading.value) return

  // Detect language
  const detected = apiService.detectLanguage(text)
  detectedLanguage.value = detected
  if (!messageText) currentLanguage.value = detected

  const userMessage = {
    id: Date.now(),
    role: 'user',
    text: text,
    timestamp: new Date(),
    language: detected
  }

  // Add user message
  messages.value.push(userMessage)
  
  // Clear input if not from suggestion
  if (!messageText) {
    inputText.value = ''
    detectedLanguage.value = null
  }
  
  // Show loading/typing
  isLoading.value = true
  isTyping.value = true
  error.value = null
  
  await scrollToBottom()

  try {
    // Call real API
    const response = await apiService.sendMessage(text, sessionId.value, detected)
    
    // Update session ID
    if (response.session_id) {
      sessionId.value = response.session_id
      localStorage.setItem('sessionId', response.session_id)
    }

    // Update language if detected by backend
    if (response.language) {
      currentLanguage.value = response.language
    }
    
    // Add bot response
    const botMessage = {
      id: Date.now() + 1,
      role: 'assistant',
      text: response.text || 'Sorry, I couldn\'t understand that.',
      timestamp: new Date(),
      language: response.language || detected,
      confidence: response.confidence || 0,
      sources: response.sources || []
    }
    
    messages.value.push(botMessage)

    // Update suggestions if provided
    if (response.suggested_questions && response.suggested_questions.length > 0) {
      suggestions.value = response.suggested_questions
    }
    
    backendStatus.value = 'Connected ✅'     
    
  } catch (err) {
    console.error('Send message error:', err)
    error.value = 'Failed to connect to backend. Make sure FastAPI is running on port 8000.'
    backendStatus.value = 'Error ❌'
    
    // Add error message
    const errorMessage = {
      id: Date.now() + 1,
      role: 'assistant',
      text: 'Sorry, I\'m having technical difficulties. Please make sure the backend server is running.',
      timestamp: new Date(),
      isError: true
    }
    
    messages.value.push(errorMessage)
  } finally {
    isLoading.value = false
    isTyping.value = false
    await scrollToBottom()
  }
}

const loadSuggestions = async () => {
  try {
    const response = await apiService.getSuggestions(currentLanguage.value)
    suggestions.value = response.suggestions || []
  } catch (err) {
    console.error('Load suggestions error:', err)
  }
}

const clearError = () => {
  error.value = null
}

const scrollToBottom = async () => {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

const formatTime = (timestamp) => {
  return timestamp.toLocaleTimeString('en-US', { 
    hour: '2-digit', 
    minute: '2-digit' 
  })
}

const getConfidenceClass = (confidence) => {
  if (confidence > 0.7) return 'high'
  if (confidence > 0.4) return 'medium'
  return 'low'
}

// Auto-detect language as user types
const handleInput = () => {
  if (inputText.value.length > 2) {
    detectedLanguage.value = apiService.detectLanguage(inputText.value)
  } else {
    detectedLanguage.value = null
  }
}

// Initialize
onMounted(async () => {
  await loadSuggestions()
  
  // Test backend connection
  try {
    await fetch('http://localhost:8000/health/readyz')
    backendStatus.value = 'Connected ✅'
  } catch (err) {
    backendStatus.value = 'Disconnected ❌'
    error.value = 'Backend not accessible. Make sure FastAPI is running on port 8000.'
  }
})
</script>

<style scoped>
/* Previous styles plus new ones */
.home-view {
  max-width: 800px;
  margin: 20px auto;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
  overflow: hidden;
}

.chat-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 20px;
  text-align: center;
  position: relative;
}

.language-indicator {
  position: absolute;
  top: 20px;
  right: 20px;
  background: rgba(255,255,255,0.2);
  padding: 4px 8px;
  border-radius: 10px;
  font-size: 12px;
}

.chat-header h1 {
  margin: 0 0 5px 0;
  font-size: 24px;
}

.chat-header p {
  margin: 0;
  opacity: 0.9;
  font-size: 14px;
}

.chat-container {
  display: flex;
  flex-direction: column;
  height: 500px;
}

.messages-area {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background: #fafafa;
}

.message {
  margin-bottom: 15px;
  display: flex;
}

.message.user {
  justify-content: flex-end;
}

.message.assistant {
  justify-content: flex-start;
}

.bubble {
  max-width: 70%;
  padding: 12px 16px;
  border-radius: 18px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  word-wrap: break-word;
}

.user-bubble {
  background: #667eea;
  color: white;
  margin-left: 50px;
}

.assistant-bubble {
  background: white;
  border: 1px solid #e0e0e0;
  margin-right: 50px;
  color: #374151;
}

.assistant-bubble.typing {
  opacity: 0.7;
}

.message-meta {
  font-size: 11px;
  color: #666;
  margin-top: 8px;
}

.meta-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 3px;
}

.confidence.high { color: #10b981; }
.confidence.medium { color: #f59e0b; }
.confidence.low { color: #ef4444; }

.sources {
  font-size: 10px;
  color: #888;
}

.timestamp {
  font-size: 10px;
  color: #9ca3af;
}

.typing-text {
  font-style: italic;
  opacity: 0.7;
}

.error-message {
  text-align: center;
  color: #dc2626;
  background: #fef2f2;
  padding: 12px;
  border-radius: 8px;
  margin: 16px;
  border: 1px solid #fecaca;
  position: relative;
}

.error-message button {
  position: absolute;
  top: 8px;
  right: 8px;
  background: none;
  border: none;
  color: #dc2626;
  cursor: pointer;
  font-weight: bold;
}

.suggestions-panel {
  padding: 15px 20px;
  background: #f8faff;
  border-top: 1px solid #e5e7eb;
}

.suggestions-panel h4 {
  margin: 0 0 10px 0;
  font-size: 14px;
  color: #374151;
}

.suggestion-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.suggestion-btn {
  padding: 6px 12px;
  background: white;
  border: 1px solid #d1d5db;
  border-radius: 15px;
  cursor: pointer;
  font-size: 12px;
  color: #374151;
  transition: all 0.2s;
}

.suggestion-btn:hover {
  background: #3b82f6;
  color: white;
  border-color: #3b82f6;
}

.input-area {
  padding: 20px;
  background: white;
  border-top: 1px solid #e5e7eb;
}

.input-row {
  display: flex;
  gap: 10px;
  align-items: center;
}

.text-input {
  flex: 1;
  padding: 12px;
  border: 1px solid #d1d5db;
  border-radius: 25px;
  outline: none;
  font-size: 14px;
}

.text-input:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.text-input:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.send-btn {
  padding: 12px 24px;
  border: none;
  border-radius: 25px;
  cursor: pointer;
  font-weight: 500;
  font-size: 14px;
  transition: all 0.2s;
}

.send-btn.enabled {
  background: #3b82f6;
  color: white;
}

.send-btn.enabled:hover {
  background: #2563eb;
}

.send-btn.disabled {
  background: #d1d5db;
  color: #9ca3af;
  cursor: not-allowed;
}

.language-hint {
  margin-top: 8px;
  font-size: 12px;
  color: #6b7280;
}

.lang-switch-btn {
  color: #3b82f6;
  background: none;
  border: none;
  cursor: pointer;
  text-decoration: underline;
}

.debug-info {
  padding: 8px 16px;
  background: #f9fafb;
  border-top: 1px solid #e5e7eb;
  font-size: 11px;
  color: #6b7280;
  text-align: center;
}
</style>