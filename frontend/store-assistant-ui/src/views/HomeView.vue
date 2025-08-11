<template>
  <div class="chat-app">
    <!-- Header -->
    <header class="chat-header">
      <div class="header-content">
        <div class="logo-section">
          <div class="logo">🏪</div>
          <h1>TechMart Assistant</h1>
        </div>
        <div class="header-actions">
          <div class="language-badge" :class="currentLanguage">
            {{ currentLanguage.toUpperCase() }}
          </div>
          <button @click="clearChat" class="clear-btn" title="New Chat">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M3 6h18M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/>
            </svg>
          </button>
        </div>
      </div>
    </header>

    <!-- Main Chat Area -->
    <main class="chat-main">
      <div class="chat-container" ref="chatContainer">
        <!-- Welcome Message for New Chats -->
        <div v-if="messages.length <= 1" class="welcome-screen">
          <div class="welcome-content">
            <h2>How can I help you today?</h2>
            <p>Ask me anything about TechMart Palestine - products, services, store hours, and more!</p>
            
            <!-- Quick Actions -->
            <div class="quick-actions" v-if="suggestions.length > 0">
              <h3>Try asking about:</h3>
              <div class="action-grid">
                <button 
                  v-for="suggestion in suggestions.slice(0, 4)" 
                  :key="suggestion"
                  @click="sendMessage(suggestion)"
                  class="action-card"
                >
                  <span>{{ suggestion }}</span>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="9,18 15,12 9,6"/>
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Messages -->
        <div v-if="messages.length > 1" class="messages-container">
          <div 
            v-for="message in displayMessages" 
            :key="message.id" 
            class="message-wrapper"
            :class="message.role"
          >
            <div class="message-content">
              <!-- Avatar -->
              <div class="avatar" :class="message.role">
                <div v-if="message.role === 'user'" class="user-avatar">
                  {{ currentLanguage === 'ar' ? 'ع' : 'U' }}
                </div>
                <div v-else class="assistant-avatar">
                  🏪
                </div>
              </div>

              <!-- Message Bubble -->
              <div class="message-bubble">
                <div class="message-text" v-html="formatMessage(message.text)"></div>
                
                <!-- 🔥 NEW: Streaming cursor -->
                <span v-if="message.isStreaming" class="streaming-cursor">|</span>
                
                <!-- 🔥 MODIFIED: Assistant Message Metadata -->
                <div v-if="message.role === 'assistant' && !message.isWelcome" class="message-meta">
                  <div class="meta-items">
                    <!-- 🔥 NEW: Show streaming status -->
                    <span v-if="message.isStreaming" class="streaming-status">
                      <div class="typing-dots">
                        <span></span>
                        <span></span>
                        <span></span>
                      </div>
                      Writing... ({{ message.tokenCount || 0 }} tokens)
                    </span>
                    
                    <!-- Regular metadata (shown when not streaming) -->
                    <template v-else>
                      <span v-if="message.confidence" class="confidence" :class="getConfidenceClass(message.confidence)">
                        {{ Math.round(message.confidence * 100) }}% confidence
                      </span>
                      <span v-if="message.sources && message.sources.length" class="sources">
                        {{ message.sources.length }} source{{ message.sources.length > 1 ? 's' : '' }}
                      </span>
                      <span class="timestamp">{{ formatTime(message.timestamp) }}</span>
                    </template>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 🔥 REMOVED: Old typing indicator (replaced by streaming) -->
        </div>

        <!-- Error Message -->
        <div v-if="error" class="error-banner">
          <div class="error-content">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <line x1="15" y1="9" x2="9" y2="15"/>
              <line x1="9" y1="9" x2="15" y2="15"/>
            </svg>
            <span>{{ error }}</span>
            <button @click="clearError" class="error-close">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="18" y1="6" x2="6" y2="18"/>
                <line x1="6" y1="6" x2="18" y2="18"/>
              </svg>
            </button>
          </div>
        </div>
      </div>
    </main>

    <!-- Input Area -->
    <footer class="chat-footer">
      <div class="input-container">
        <div class="input-wrapper">
          <textarea
            ref="messageInput"
            v-model="inputText"
            @keydown="handleKeyDown"
            @input="handleInput"
            :placeholder="getPlaceholder()"
            :dir="currentLanguage === 'ar' ? 'rtl' : 'ltr'"
            :disabled="isLoading || isStreaming"
            class="message-input"
            rows="1"
          ></textarea>
          
          <!-- 🔥 MODIFIED: Send button with streaming state -->
          <button 
            @click="sendMessage()"
            :disabled="!canSend"
            class="send-button"
            :class="{ 'can-send': canSend, 'streaming': isStreaming }"
          >
            <!-- 🔥 NEW: Different icons for different states -->
            <svg v-if="!isLoading && !isStreaming" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="22" y1="2" x2="11" y2="13"/>
              <polygon points="22,2 15,22 11,13 2,9 22,2"/>
            </svg>
            
            <!-- Show pause icon while streaming -->
            <svg v-else-if="isStreaming" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="6" y="4" width="4" height="16"/>
              <rect x="14" y="4" width="4" height="16"/>
            </svg>
            
            <!-- Loading spinner for other loading states -->
            <div v-else class="loading-spinner"></div>
          </button>
        </div>
        
        <!-- Language Detection Hint -->
        <div v-if="detectedLanguage && detectedLanguage !== currentLanguage" class="language-hint">
          <span>{{ detectedLanguage === 'ar' ? 'العربية' : 'English' }} detected</span>
          <button @click="currentLanguage = detectedLanguage" class="switch-language">
            Switch to {{ detectedLanguage === 'ar' ? 'Arabic' : 'English' }}
          </button>
        </div>
        
        <!-- Footer Info -->
        <div class="footer-info">
          <span>TechMart Assistant can make mistakes. Check important info.</span>
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted } from 'vue'
import apiService from '@/services/apiService'

// EXISTING STATE
const inputText = ref('')
const isLoading = ref(false)
const error = ref(null)
const sessionId = ref(localStorage.getItem('sessionId') || null)
const currentLanguage = ref('en')
const detectedLanguage = ref(null)
const suggestions = ref([])
const chatContainer = ref(null)
const messageInput = ref(null)

// 🔥 NEW: Streaming state
const isStreaming = ref(false)
const streamingMessageId = ref(null)

const messages = ref([
  {
    id: 'welcome',
    role: 'assistant',
    text: 'Hello! I\'m your TechMart Palestine assistant. How can I help you today?',
    timestamp: new Date(),
    isWelcome: true
  }
])

// 🔥 MODIFIED: canSend computed to prevent sending while streaming
const canSend = computed(() => {
  return inputText.value.trim().length > 0 && !isLoading.value && !isStreaming.value
})

const displayMessages = computed(() => {
  return messages.value.filter(msg => !msg.isWelcome)
})

// 🔥 MODIFIED: sendMessage function with streaming
const sendMessage = async (messageText = null) => {
  const text = messageText || inputText.value.trim()
  if (!text || isLoading.value || isStreaming.value) return

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

  messages.value.push(userMessage)
  
  if (!messageText) {
    inputText.value = ''
    detectedLanguage.value = null
    resizeTextarea()
  }
  
  // 🔥 NEW: Create streaming assistant message
  const assistantMessage = {
    id: Date.now() + 1,
    role: 'assistant',
    text: '',
    timestamp: new Date(),
    language: detected,
    confidence: 0,
    sources: [],
    isStreaming: true,
    tokenCount: 0
  }
  
  messages.value.push(assistantMessage)
  streamingMessageId.value = assistantMessage.id
  
  isLoading.value = true
  isStreaming.value = true
  error.value = null
  
  await scrollToBottom()

  try {
    // 🔥 NEW: Use streaming API
    await apiService.sendStreamingMessage(
      text, 
      sessionId.value, 
      detected,
      // onToken callback - called for each token
      (tokenData) => {
        // Find the streaming message and update it
        const msgIndex = messages.value.findIndex(m => m.id === streamingMessageId.value)
        if (msgIndex !== -1) {
          messages.value[msgIndex].text = tokenData.fullText
          messages.value[msgIndex].tokenCount = tokenData.tokenCount
          messages.value[msgIndex].language = tokenData.language
          
          // Auto-scroll as text appears
          nextTick(() => scrollToBottom())
        }
      },
      // onComplete callback - called when response is done
      (completeData) => {
        // Update final message data
        const msgIndex = messages.value.findIndex(m => m.id === streamingMessageId.value)
        if (msgIndex !== -1) {
          messages.value[msgIndex].isStreaming = false
          messages.value[msgIndex].confidence = completeData.confidence || 0
          messages.value[msgIndex].sources = completeData.sources || []
          messages.value[msgIndex].metadata = completeData.metadata
        }
        
        // Update session and language
        if (completeData.sessionId) {
          sessionId.value = completeData.sessionId
          localStorage.setItem('sessionId', completeData.sessionId)
        }
        
        if (completeData.language) {
          currentLanguage.value = completeData.language
        }
        
        // Clean up streaming state
        isLoading.value = false
        isStreaming.value = false
        streamingMessageId.value = null
        
        scrollToBottom()
      },
      // onError callback
      (err) => {
        console.error('Streaming error:', err)
        
        // Update message with error
        const msgIndex = messages.value.findIndex(m => m.id === streamingMessageId.value)
        if (msgIndex !== -1) {
          messages.value[msgIndex].isStreaming = false
          messages.value[msgIndex].text = messages.value[msgIndex].text || 
            'Sorry, I\'m experiencing technical difficulties. Please try again.'
          messages.value[msgIndex].isError = true
        }
        
        error.value = 'Failed to send message. Please try again.'
        
        // Clean up
        isLoading.value = false
        isStreaming.value = false
        streamingMessageId.value = null
      }
    )
    
  } catch (err) {
    console.error('Send message error:', err)
    error.value = 'Failed to send message. Please try again.'
    
    // Remove the failed streaming message
    const msgIndex = messages.value.findIndex(m => m.id === streamingMessageId.value)
    if (msgIndex !== -1) {
      messages.value.splice(msgIndex, 1)
    }
    
    isLoading.value = false
    isStreaming.value = false
    streamingMessageId.value = null
  }
}

// EXISTING METHODS (unchanged)
const clearChat = () => {
  messages.value = [messages.value[0]] // Keep welcome message
  sessionId.value = null
  localStorage.removeItem('sessionId')
  error.value = null
}

const clearError = () => {
  error.value = null
}

const handleKeyDown = (event) => {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    sendMessage()
  }
}

const handleInput = () => {
  resizeTextarea()
  
  if (inputText.value.length > 2) {
    detectedLanguage.value = apiService.detectLanguage(inputText.value)
  } else {
    detectedLanguage.value = null
  }
}

const resizeTextarea = () => {
  const textarea = messageInput.value
  if (textarea) {
    textarea.style.height = 'auto'
    textarea.style.height = Math.min(textarea.scrollHeight, 200) + 'px'
  }
}

const scrollToBottom = async () => {
  await nextTick()
  if (chatContainer.value) {
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight
  }
}

const formatMessage = (text) => {
  if (!text) return ''
  
  let formatted = text
  formatted = formatted.replace(/\n/g, '<br>')
  formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
  formatted = formatted.replace(/(\d+\.?\d*\s?(JOD|دينار))/gi, '<span class="price">$1</span>')
  formatted = formatted.replace(/(\+?\d{1,4}[-.\s]?\(?\d{1,3}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9})/g, '<span class="phone">$1</span>')
  
  return formatted
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

const getPlaceholder = () => {
  return currentLanguage.value === 'ar' 
    ? 'اكتب رسالتك هنا...' 
    : 'Message TechMart Assistant...'
}

const loadSuggestions = async () => {
  try {
    const response = await apiService.getSuggestions(currentLanguage.value)
    suggestions.value = response.suggestions || []
  } catch (err) {
    console.error('Load suggestions error:', err)
  }
}

// Initialize
onMounted(async () => {
  await loadSuggestions()
})
</script>

<style scoped>
/* ChatGPT-Style Professional UI + STREAMING STYLES */
.chat-app {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #ffffff;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
}

/* Header */
.chat-header {
  background: #ffffff;
  border-bottom: 1px solid #e5e5e5;
  padding: 12px 0;
  flex-shrink: 0;
}

.header-content {
  max-width: 768px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 16px;
}

.logo-section {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo {
  font-size: 24px;
}

.logo-section h1 {
  font-size: 18px;
  font-weight: 600;
  color: #2d2d2d;
  margin: 0;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.language-badge {
  background: #f7f7f8;
  color: #6b6b6b;
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
}

.language-badge.ar {
  background: #e3f2fd;
  color: #1976d2;
}

.clear-btn {
  background: none;
  border: none;
  padding: 8px;
  border-radius: 6px;
  cursor: pointer;
  color: #6b6b6b;
  transition: all 0.2s;
}

.clear-btn:hover {
  background: #f7f7f8;
  color: #2d2d2d;
}

/* Main Chat Area */
.chat-main {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.chat-container {
  flex: 1;
  overflow-y: auto;
  padding: 24px 0;
}

/* Welcome Screen */
.welcome-screen {
  max-width: 768px;
  margin: 0 auto;
  padding: 48px 16px;
  text-align: center;
}

.welcome-content h2 {
  font-size: 32px;
  font-weight: 600;
  color: #2d2d2d;
  margin: 0 0 12px 0;
}

.welcome-content p {
  font-size: 16px;
  color: #6b6b6b;
  margin: 0 0 32px 0;
  line-height: 1.5;
}

.quick-actions h3 {
  font-size: 16px;
  font-weight: 500;
  color: #2d2d2d;
  margin: 0 0 16px 0;
}

.action-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 12px;
  max-width: 600px;
  margin: 0 auto;
}

.action-card {
  background: #ffffff;
  border: 1px solid #e5e5e5;
  border-radius: 12px;
  padding: 16px;
  text-align: left;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.action-card:hover {
  background: #f7f7f8;
  border-color: #d0d0d0;
}

.action-card span {
  color: #2d2d2d;
  font-size: 14px;
}

.action-card svg {
  color: #6b6b6b;
  opacity: 0.5;
}

/* Messages */
.messages-container {
  max-width: 768px;
  margin: 0 auto;
  padding: 0 16px;
}

.message-wrapper {
  margin-bottom: 24px;
}

.message-wrapper.user .message-content {
  margin-left: 48px;
}

.message-wrapper.assistant .message-content {
  margin-right: 48px;
}

.message-content {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 14px;
  font-weight: 600;
}

.avatar.user .user-avatar {
  background: #19c37d;
  color: white;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
}

.avatar.assistant .assistant-avatar {
  background: #10a37f;
  color: white;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  font-size: 16px;
}

.message-bubble {
  flex: 1;
  line-height: 1.6;
}

.message-text {
  color: #2d2d2d;
  font-size: 16px;
  word-wrap: break-word;
  transition: all 0.1s ease-out;
  animation: fadeInText 0.2s ease-out;
}

@keyframes fadeInText {
  from { opacity: 0.7; }
  to { opacity: 1; }
}

.message-text .price {
  color: #10a37f;
  font-weight: 600;
}

.message-text .phone {
  color: #1976d2;
  font-weight: 500;
}

/* 🔥 NEW: Streaming cursor animation */
.streaming-cursor {
  display: inline-block;
  color: #10a37f;
  font-weight: bold;
  font-size: 16px;
  margin-left: 2px;
  animation: blink 1s infinite;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

/* 🔥 NEW: Streaming message bubble effect */
.message-bubble:has(.streaming-cursor) {
  border-left: 3px solid #10a37f;
  background: linear-gradient(90deg, rgba(16, 163, 127, 0.02), transparent);
  transition: all 0.3s ease;
}

.message-meta {
  margin-top: 8px;
}

.meta-items {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: #8e8e8e;
  transition: all 0.3s ease;
}

/* 🔥 NEW: Streaming status indicator */
.streaming-status {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #10a37f;
  font-size: 12px;
  font-style: italic;
  background: rgba(16, 163, 127, 0.1);
  padding: 4px 8px;
  border-radius: 12px;
  border: 1px solid rgba(16, 163, 127, 0.2);
  font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Roboto Mono', monospace;
  font-weight: 500;
}

/* 🔥 NEW: Mini typing dots for streaming status */
.streaming-status .typing-dots {
  display: flex;
  gap: 2px;
}

.streaming-status .typing-dots span {
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: #10a37f;
  animation: typing-mini 1.4s ease-in-out infinite;
}

.streaming-status .typing-dots span:nth-child(1) { animation-delay: -0.32s; }
.streaming-status .typing-dots span:nth-child(2) { animation-delay: -0.16s; }

@keyframes typing-mini {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.5; }
  40% { transform: scale(1); opacity: 1; }
}

.confidence.high { color: #10a37f; }
.confidence.medium { color: #ff8c00; }
.confidence.low { color: #ef4444; }

/* 🔥 NEW: Enhanced message highlighting during streaming */
.message-wrapper.assistant:has(.streaming-cursor) .avatar.assistant .assistant-avatar {
  animation: glow 2s ease-in-out infinite;
}

@keyframes glow {
  0%, 100% { box-shadow: 0 0 5px rgba(16, 163, 127, 0.3); }
  50% { box-shadow: 0 0 15px rgba(16, 163, 127, 0.6), 0 0 25px rgba(16, 163, 127, 0.3); }
}

/* Error Banner */
.error-banner {
  max-width: 768px;
  margin: 0 auto 16px auto;
  padding: 0 16px;
}

.error-content {
  background: #fee;
  border: 1px solid #fcc;
  border-radius: 8px;
  padding: 12px 16px;
  display: flex;
  align-items: center;
  gap: 8px;
  color: #c00;
}

.error-close {
  background: none;
  border: none;
  cursor: pointer;
  color: #c00;
  margin-left: auto;
}

/* Footer Input */
.chat-footer {
  background: #ffffff;
  border-top: 1px solid #e5e5e5;
  padding: 16px 0 24px 0;
  flex-shrink: 0;
}

.input-container {
  max-width: 768px;
  margin: 0 auto;
  padding: 0 16px;
}

.input-wrapper {
  background: #ffffff;
  border: 1px solid #d0d0d0;
  border-radius: 24px;
  padding: 12px 16px;
  display: flex;
  align-items: flex-end;
  gap: 8px;
  transition: border-color 0.2s;
}

.input-wrapper:focus-within {
  border-color: #10a37f;
  box-shadow: 0 0 0 3px rgba(16, 163, 127, 0.1);
}

.message-input {
  flex: 1;
  border: none;
  outline: none;
  resize: none;
  font-size: 16px;
  line-height: 1.5;
  color: #2d2d2d;
  background: transparent;
  font-family: inherit;
  max-height: 200px;
}

.message-input::placeholder {
  color: #8e8e8e;
}

.message-input:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.send-button {
  background: #f7f7f8;
  border: none;
  border-radius: 50%;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
  color: #8e8e8e;
  flex-shrink: 0;
}

.send-button.can-send {
  background: #10a37f;
  color: white;
}

.send-button.can-send:hover {
  background: #0e9168;
}

/* 🔥 NEW: Streaming send button states */
.send-button.streaming {
  background: #ff6b6b;
  color: white;
  animation: pulse-red 2s ease-in-out infinite;
}

.send-button.streaming:hover {
  background: #ff5252;
}

.send-button.streaming:disabled {
  opacity: 1;
  cursor: pointer;
  transform: scale(1);
}

@keyframes pulse-red {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.8; }
}

.send-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: scale(0.95);
}

.loading-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid #ffffff;
  border-top: 2px solid transparent;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* Language Hint */
.language-hint {
  margin-top: 8px;
  font-size: 12px;
  color: #8e8e8e;
  display: flex;
  align-items: center;
  gap: 8px;
}

.switch-language {
  background: none;
  border: none;
  color: #10a37f;
  cursor: pointer;
  text-decoration: underline;
  font-size: 12px;
}

/* Footer Info */
.footer-info {
  margin-top: 8px;
  text-align: center;
  font-size: 12px;
  color: #8e8e8e;
}

/* Responsive */
@media (max-width: 768px) {
  .welcome-content h2 {
    font-size: 24px;
  }
  
  .action-grid {
    grid-template-columns: 1fr;
  }
  
  .message-wrapper.user .message-content {
    margin-left: 0;
  }
  
  .message-wrapper.assistant .message-content {
    margin-right: 0;
  }
  
  .meta-items {
    flex-direction: column;
    gap: 4px;
  }

  /* 🔥 NEW: Mobile responsiveness for streaming */
  .streaming-cursor {
    font-size: 14px;
  }
  
  .streaming-status {
    font-size: 11px;
    padding: 3px 6px;
  }
  
  .streaming-status .typing-dots span {
    width: 3px;
    height: 3px;
  }
}

/* RTL Support */
[dir="rtl"] .message-content {
  flex-direction: row-reverse;
}

[dir="rtl"] .input-wrapper {
  flex-direction: row-reverse;
}

/* 🔥 NEW: Dark mode support for streaming (if you add dark mode later) */
@media (prefers-color-scheme: dark) {
  .streaming-cursor {
    color: #19c37d;
  }
  
  .streaming-status {
    color: #19c37d;
    background: rgba(25, 195, 125, 0.1);
    border-color: rgba(25, 195, 125, 0.2);
  }
  
  .streaming-status .typing-dots span {
    background: #19c37d;
  }
}

/* 🔥 NEW: Reduced motion support */
@media (prefers-reduced-motion: reduce) {
  .streaming-cursor,
  .typing-dots span,
  .send-button.streaming {
    animation: none;
  }
  
  .streaming-cursor {
    opacity: 1;
  }
}
</style>