<template>
  <div id="app">
    <RouterView />
    
    <!-- Global Loading Overlay -->
    <div v-if="isGlobalLoading" class="global-loading">
      <div class="loading-content">
        <div class="loading-spinner"></div>
        <span>Loading...</span>
      </div>
    </div>

    <!-- Global Error Toast -->
    <div v-if="globalError" class="global-error">
      <div class="error-content">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/>
          <line x1="15" y1="9" x2="9" y2="15"/>
          <line x1="9" y1="9" x2="15" y2="15"/>
        </svg>
        <span>{{ globalError }}</span>
        <button @click="clearGlobalError" class="error-close">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"/>
            <line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { RouterView } from 'vue-router'

// Global state
const isGlobalLoading = ref(false)
const globalError = ref(null)

// Methods
const clearGlobalError = () => {
  globalError.value = null
}

// Global error handler
const handleGlobalError = (error) => {
  console.error('Global error:', error)
  globalError.value = 'An unexpected error occurred. Please refresh the page.'
}

// Setup global error handling
onMounted(() => {
  window.addEventListener('unhandledrejection', (event) => {
    handleGlobalError(event.reason)
  })
  
  window.addEventListener('error', (event) => {
    handleGlobalError(event.error)
  })
})
</script>

<style>
/* Global Loading Overlay */
.global-loading {
  position: fixed;
  inset: 0;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.loading-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  padding: 32px;
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #f0f0f0;
  border-top: 3px solid #10a37f;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.loading-content span {
  color: #6b6b6b;
  font-size: 14px;
  font-weight: 500;
}

/* Global Error Toast */
.global-error {
  position: fixed;
  bottom: 24px;
  right: 24px;
  z-index: 9998;
  max-width: 400px;
}

.error-content {
  background: #fee;
  border: 1px solid #fcc;
  border-radius: 12px;
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  color: #c00;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
  animation: slideInRight 0.3s ease-out;
}

@keyframes slideInRight {
  from {
    opacity: 0;
    transform: translateX(100%);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.error-content span {
  flex: 1;
  font-size: 14px;
  line-height: 1.4;
}

.error-close {
  background: none;
  border: none;
  cursor: pointer;
  color: #c00;
  padding: 4px;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.error-close:hover {
  background: rgba(204, 0, 0, 0.1);
}

/* Responsive */
@media (max-width: 640px) {
  .global-error {
    bottom: 16px;
    right: 16px;
    left: 16px;
    max-width: none;
  }
  
  .loading-content {
    margin: 16px;
  }
}
</style>