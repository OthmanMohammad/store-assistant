<!-- src/components/Chat/SuggestionPanel.vue -->
<template>
  <div class="suggestions-panel">
    <h4 class="suggestions-title">
      💡 {{ title }}
    </h4>
    
    <div class="suggestion-buttons">
      <button
        v-for="(suggestion, index) in suggestions"
        :key="index"
        @click="$emit('suggestion-click', suggestion)"
        class="suggestion-btn"
        :dir="language === 'ar' ? 'rtl' : 'ltr'"
      >
        {{ suggestion }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  suggestions: {
    type: Array,
    default: () => []
  },
  language: {
    type: String,
    default: 'en'
  }
})

defineEmits(['suggestion-click'])

const title = computed(() => {
  return props.language === 'ar' 
    ? 'أسئلة مقترحة:' 
    : 'Suggested Questions:'
})
</script>