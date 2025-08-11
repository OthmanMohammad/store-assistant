<template>
  <div class="chat-view">
    <ChatContainer />
  </div>
</template>

<script setup>
import ChatContainer from '@/components/Chat/ChatContainer.vue'
</script>

<style scoped>
.chat-view {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}
</style>