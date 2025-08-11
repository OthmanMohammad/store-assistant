import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { chatAPI, detectLanguage } from '@/stores/api'

export const useChatStore = defineStore('chat', () => {
  // State
  const messages = ref([])
  const sessionId = ref(localStorage.getItem('sessionId') || null)
  const currentLanguage = ref('en')
  const isTyping = ref(false)
  const suggestions = ref([])
  const isLoading = ref(false)
  const error = ref(null)

  // Computed
  const hasMessages = computed(() => messages.value.length > 0)

  // Actions
  async function sendMessage(text) {
    if (!text.trim() || isLoading.value) return

    const detectedLang = detectLanguage(text)
    currentLanguage.value = detectedLang

    // Add user message
    const userMessage = {
      id: Date.now(),
      role: 'user',
      text: text.trim(),
      timestamp: new Date(),
      language: detectedLang
    }
    messages.value.push(userMessage)

    isTyping.value = true
    isLoading.value = true
    error.value = null

    try {
      const response = await chatAPI.sendMessage(text, sessionId.value, detectedLang)
      
      if (response.session_id) {
        sessionId.value = response.session_id
        localStorage.setItem('sessionId', response.session_id)
      }

      if (response.language) {
        currentLanguage.value = response.language
      }

      const botMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        text: response.text || 'Sorry, I couldn\'t understand that.',
        timestamp: new Date(),
        language: response.language || detectedLang,
        confidence: response.confidence || 0,
        sources: response.sources || []
      }
      messages.value.push(botMessage)

      if (response.suggested_questions?.length > 0) {
        suggestions.value = response.suggested_questions
      }

    } catch (err) {
      error.value = 'Failed to send message. Please try again.'
      console.error('Send message error:', err)
    } finally {
      isTyping.value = false
      isLoading.value = false
    }
  }

  async function loadSuggestions(language = 'en') {
    try {
      const response = await chatAPI.getSuggestions(language)
      suggestions.value = response.suggestions || []
    } catch (err) {
      console.error('Load suggestions error:', err)
    }
  }

  function clearChat() {
    messages.value = []
    sessionId.value = null
    localStorage.removeItem('sessionId')
    suggestions.value = []
    error.value = null
  }

  function useSuggestion(suggestion) {
    sendMessage(suggestion)
  }

  async function initialize() {
    await loadSuggestions(currentLanguage.value)
    
    if (!sessionId.value) {
      messages.value.push({
        id: 'welcome',
        role: 'assistant',
        text: 'Hello! أهلاً وسهلاً! How can I help you today? كيف يمكنني مساعدتك؟',
        timestamp: new Date(),
        language: 'en',
        confidence: 1,
        sources: [],
        isWelcome: true
      })
    }
  }

  return {
    messages, sessionId, currentLanguage, isTyping, suggestions, isLoading, error,
    hasMessages, sendMessage, loadSuggestions, clearChat, useSuggestion, initialize
  }
})