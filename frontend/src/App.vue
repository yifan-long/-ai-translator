<script setup lang="ts">
import { ref } from 'vue'
import TranslateForm from '@/components/TranslateForm.vue'
import HistoryList from '@/components/HistoryList.vue'

// 翻译完成后让 historyKey +1，触发 HistoryList 重新拉取
const historyKey = ref(0)

function onTranslated() {
  historyKey.value += 1
}
</script>

<template>
  <header class="app-header">
    <h1>AI 在线翻译</h1>
    <p class="subtitle">基于 LangChain + DeepSeek 驱动 · 支持多语种互译</p>
  </header>
  <main>
    <TranslateForm @translated="onTranslated" />
    <HistoryList :refresh-key="historyKey" />
  </main>
  <footer class="app-footer">
    <small>Powered by FastAPI · Vue 3 · LangChain</small>
  </footer>
</template>

<style scoped>
.app-header {
  text-align: center;
  margin-bottom: 32px;
}

.app-header h1 {
  margin-bottom: 8px;
}

.subtitle {
  margin: 0;
  color: var(--text-muted);
  font-size: 14px;
}

.app-footer {
  text-align: center;
  margin-top: 40px;
  color: var(--text-subtle);
}
</style>
