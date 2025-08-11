<!-- src/components/Chat/MessageBubble.vue -->
<template>
  <div class="message" :class="messageClasses" :dir="isRtl ? 'rtl' : 'ltr'">
    <div class="bubble" :class="bubbleClasses">
      <!-- Message Text -->
      <div class="message-text" v-html="formattedText" />
      
      <!-- Bot Message Metadata -->
      <div v-if="message.role === 'assistant' && !message.isWelcome" class="bot-info">
        <div class="meta-row">
          <!-- Confidence Score -->
          <span v-if="message.confidence !== undefined" class="confidence" :class="confidenceClass">
            Confidence: {{ Math.round(message.confidence * 100) }}%
          </span>
          
          <!-- Sources -->
          <span v-if="message.sources && message.sources.length > 0" class="sources">
            Sources: {{ message.sources.slice(0, 2).join(', ') }}
          </span>
        </div>
        
        <!-- Timestamp -->
        <div class="timestamp">
          {{ formatTime(message.timestamp) }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  message: {
    type: Object,
    required: true
  },
  isRtl: {
    type: Boolean,
    default: false
  }
})

// Message positioning classes
const messageClasses = computed(() => ({
  'user': props.message.role === 'user',
  'bot': props.message.role === 'assistant'
}))

// Bubble styling classes
const bubbleClasses = computed(() => {
  if (props.message.role === 'user') {
    return 'user-bubble'
  } else {
    return props.message.isError ? 'bot-bubble error' : 'bot-bubble'
  }
})

// Confidence score styling
const confidenceClass = computed(() => {
  const confidence = props.message.confidence || 0
  if (confidence > 0.7) return 'high'
  if (confidence > 0.4) return 'medium'
  return 'low'
})

// Format message text with basic formatting
const formattedText = computed(() => {
  if (!props.message.text) return ''
  
  let text = props.message.text
  
  // Convert line breaks to <br>
  text = text.replace(/\n/g, '<br>')
  
  // Bold text **text**
  text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
  
  // Preserve phone numbers and prices
  text = text.replace(/(\+?\d{1,4}[-.\s]?\(?\d{1,3}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9})/g, '<strong>$1</strong>')
  text = text.replace(/(\d+\.?\d*\s?(JOD|دينار|ديناراً))/gi, '<strong style="color: #4CAF50;">$1</strong>')
  
  return text
})

// Format timestamp
const formatTime = (timestamp) => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
}
</script>