<!-- src/components/Chat/ChatContainer.vue -->
<template>
  <div class="chat-container">
    <!-- Header -->
    <div class="header">
      <h1>🏪 Store Assistant</h1>
      <p>AI-powered customer service • Ask anything about our store!</p>
      <LanguageIndicator :language="currentLanguage" />
    </div>

    <!-- Messages Area -->
    <div ref="messagesContainer" class="messages-area">
      <MessageBubble
        v-for="message in messages"
        :key="message.id"
        :message="message"
        :is-rtl="message.language === 'ar'"
      />
      
      <TypingIndicator v-if="isTyping" />
      
      <div v-if="error" class="error-message">
        {{ error }}
        <button @click="clearError">✕</button>
      </div>
    </div>

    <!-- Suggestions Panel -->
    <SuggestionPanel
      v-if="suggestions.length > 0 && !hasMessages"
      :suggestions="suggestions"
      :language="currentLanguage"
      @suggestion-click="handleSuggestionClick"
    />

    <!-- Input Area -->
    <InputArea
      :is-loading="isLoading"
      :current-language="currentLanguage"
      @send-message="handleSendMessage"
      @language-change="handleLanguageChange"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, computed, watch } from 'vue'
import { useChatStore } from '@/stores/chat'
import MessageBubble from './MessageBubble.vue'
import InputArea from './InputArea.vue'
import SuggestionPanel from './SuggestionPanel.vue'
import LanguageIndicator from '../UI/LanguageIndicator.vue'
import TypingIndicator from '../UI/TypingIndicator.vue'

const chatStore = useChatStore()
const messagesContainer = ref(null)

// Computed properties from store
const messages = computed(() => chatStore.messages)
const currentLanguage = computed(() => chatStore.currentLanguage)
const isTyping = computed(() => chatStore.isTyping)
const suggestions = computed(() => chatStore.suggestions)
const isLoading = computed(() => chatStore.isLoading)
const error = computed(() => chatStore.error)
const hasMessages = computed(() => chatStore.hasMessages)

// Methods
const handleSendMessage = async (text) => {
  await chatStore.sendMessage(text)
  await scrollToBottom()
}

const handleSuggestionClick = (suggestion) => {
  chatStore.useSuggestion(suggestion)
}

const handleLanguageChange = (language) => {
  chatStore.currentLanguage = language
  chatStore.loadSuggestions(language)
}

const clearError = () => {
  chatStore.error = null
}

const scrollToBottom = async () => {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

// Watch for new messages to auto-scroll
watch(messages, () => {
  scrollToBottom()
}, { deep: true })

// Initialize chat on mount
onMounted(async () => {
  await chatStore.initialize()
  await scrollToBottom()
})
</script>
