<!-- src/components/UI/LanguageIndicator.vue -->
<template>
  <div class="language-indicator" :title="title">
    {{ displayText }}
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  language: {
    type: String,
    default: 'en'
  }
})

const displayText = computed(() => {
  return props.language.toUpperCase()
})

const title = computed(() => {
  return props.language === 'ar' 
    ? 'Current language: Arabic' 
    : 'Current language: English'
})
</script>