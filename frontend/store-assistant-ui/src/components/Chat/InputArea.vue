<!-- src/components/Chat/InputArea.vue -->
<template>
  <div class="input-area">
    <div class="input-row">
      <!-- Text Input -->
      <div class="input-container">
        <textarea
          ref="textInput"
          v-model="inputText"
          :placeholder="placeholder"
          :dir="currentLanguage === 'ar' ? 'rtl' : 'ltr'"
          class="text-input"
          :class="textareaClasses"
          rows="1"
          @keydown="handleKeydown"
          @input="handleInput"
          :disabled="isLoading"
        />
        
        <!-- Character count -->
        <div v-if="inputText.length > 0" class="char-count">
          {{ inputText.length }}
        </div>
      </div>
      
      <!-- Send Button -->
      <button
        @click="sendMessage"
        :disabled="!canSend"
        class="send-btn"
        :class="sendButtonClasses"
      >
        <span v-if="!isLoading">{{ sendButtonText }}</span>
        <div v-else class="loading-spinner"></div>
      </button>
    </div>
    
    <!-- Language detection indicator -->
    <div v-if="detectedLanguage && detectedLanguage !== currentLanguage" class="language-hint">
      🌍 Detected {{ detectedLanguage === 'ar' ? 'Arabic' : 'English' }} - 
      <button @click="$emit('language-change', detectedLanguage)" class="lang-switch-btn">
        Switch to {{ detectedLanguage === 'ar' ? 'Arabic' : 'English' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, watch } from 'vue'
import { detectLanguage } from '@/stores/api'

const props = defineProps({
  isLoading: {
    type: Boolean,
    default: false
  },
  currentLanguage: {
    type: String,
    default: 'en'
  }
})

const emit = defineEmits(['send-message', 'language-change'])

const inputText = ref('')
const textInput = ref(null)
const detectedLanguage = ref(null)

// Computed properties
const placeholder = computed(() => {
  return props.currentLanguage === 'ar' 
    ? 'اكتب سؤالك هنا...' 
    : 'Type your question...'
})

const sendButtonText = computed(() => {
  return props.currentLanguage === 'ar' ? 'إرسال' : 'Send'
})

const canSend = computed(() => {
  return inputText.value.trim().length > 0 && !props.isLoading
})

const textareaClasses = computed(() => ({
  'disabled': props.isLoading,
  'rtl': props.currentLanguage === 'ar'
}))

const sendButtonClasses = computed(() => ({
  'enabled': canSend.value,
  'disabled': !canSend.value
}))

// Methods
const sendMessage = () => {
  if (!canSend.value) return
  
  const text = inputText.value.trim()
  emit('send-message', text)
  inputText.value = ''
  detectedLanguage.value = null
  
  // Reset textarea height
  if (textInput.value) {
    textInput.value.style.height = 'auto'
  }
}

const handleKeydown = (event) => {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    sendMessage()
  }
}

const handleInput = () => {
  // Auto-resize textarea
  autoResize()
  
  // Detect language
  if (inputText.value.length > 2) {
    detectedLanguage.value = detectLanguage(inputText.value)
  } else {
    detectedLanguage.value = null
  }
}

const autoResize = () => {
  if (textInput.value) {
    textInput.value.style.height = 'auto'
    textInput.value.style.height = Math.min(textInput.value.scrollHeight, 120) + 'px'
  }
}
</script>
