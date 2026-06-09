<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { getLanguages, translateText, type Language, type Translation } from '@/api'

// 父组件通过 v-model 绑定这个事件
// 翻译成功后通知父组件刷新历史
const emit = defineEmits<{
  (e: 'translated', record: Translation): void
}>()

// 表单状态
const form = reactive({
  source_text: '',
  source_lang: 'en',
  target_lang: 'zh-CN',
})

// 加载状态
const languages = ref<Language[]>([])
const loading = ref(false)
const result = ref<Translation | null>(null)
const errorMsg = ref('')

// 页面加载时拉取语言列表
onMounted(async () => {
  try {
    const res = await getLanguages()
    languages.value = res.languages
  } catch (err) {
    errorMsg.value = '加载语言列表失败'
    console.error(err)
  }
})

async function handleSubmit() {
  if (!form.source_text.trim()) {
    errorMsg.value = '请输入要翻译的文本'
    return
  }
  errorMsg.value = ''
  loading.value = true
  result.value = null
  try {
    const record = await translateText({
      source_text: form.source_text,
      source_lang: form.source_lang,
      target_lang: form.target_lang,
    })
    result.value = record
    emit('translated', record) // 通知父组件
  } catch (err: any) {
    errorMsg.value = err?.response?.data?.detail || err?.message || '翻译失败'
    console.error(err)
  } finally {
    loading.value = false
  }
}

function swapLanguages() {
  const tmp = form.source_lang
  form.source_lang = form.target_lang
  form.target_lang = tmp
}
</script>

<template>
  <section class="translate-form card">
    <h2><span class="icon">🌐</span>翻译</h2>

    <form @submit.prevent="handleSubmit">
      <div class="row">
        <label class="field">
          <span>源语言</span>
          <select v-model="form.source_lang" :disabled="loading">
            <option v-for="l in languages" :key="l.code" :value="l.code">
              {{ l.name }}
            </option>
          </select>
        </label>

        <button
          type="button"
          class="swap-btn"
          :disabled="loading"
          @click="swapLanguages"
          title="交换源/目标语言"
        >
          ⇄
        </button>

        <label class="field">
          <span>目标语言</span>
          <select v-model="form.target_lang" :disabled="loading">
            <option v-for="l in languages" :key="l.code" :value="l.code">
              {{ l.name }}
            </option>
          </select>
        </label>
      </div>

      <label class="field">
        <span>原文</span>
        <textarea
          v-model="form.source_text"
          :disabled="loading"
          rows="5"
          placeholder="请输入要翻译的文本..."
        ></textarea>
      </label>

      <button
        type="submit"
        class="primary"
        :disabled="loading || !form.source_text.trim()"
      >
        <span v-if="loading" class="spinner"></span>
        <span v-else>翻译</span>
      </button>

      <p v-if="errorMsg" class="error">⚠️ {{ errorMsg }}</p>
    </form>

    <transition name="fade-slide">
      <div
        v-if="result"
        class="result"
        :class="{ failed: result.status === 'failed' }"
      >
        <h3>
          <span class="result-icon">{{ result.status === 'failed' ? '❌' : '✨' }}</span>
          {{ result.status === 'failed' ? '翻译失败' : '译文' }}
        </h3>
        <p
          v-if="result.status === 'failed'"
          class="translated-text failed-text"
        >
          本次翻译未成功，请稍后重试。记录已保存到历史。
        </p>
        <p v-else class="translated-text">{{ result.translated_text }}</p>
        <small class="meta">
          <span>模型：{{ result.model_used || '未知' }}</span>
          <span class="dot">·</span>
          <span>创建时间：{{ new Date(result.created_at).toLocaleString() }}</span>
        </small>
      </div>
    </transition>
  </section>
</template>

<style scoped>
.card {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: var(--shadow);
  transition: box-shadow 0.2s;
}

.card:hover {
  box-shadow: var(--shadow-md);
}

.translate-form h2 {
  margin-top: 0;
  margin-bottom: 20px;
  font-size: 18px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.icon {
  font-size: 20px;
}

.row {
  display: flex;
  gap: 8px;
  align-items: flex-end;
  margin-bottom: 12px;
}

.field {
  display: flex;
  flex-direction: column;
  flex: 1;
  gap: 6px;
  margin-bottom: 12px;
}

.field span {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-muted);
}

select,
textarea {
  font-size: 14px;
  padding: 10px 12px;
  border: 1px solid var(--border);
  border-radius: 8px;
  font-family: inherit;
  background: #fff;
  transition: border-color 0.15s, box-shadow 0.15s;
  resize: vertical;
}

select:focus,
textarea:focus {
  outline: none;
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
}

textarea {
  min-height: 100px;
}

.swap-btn {
  background: var(--primary-light);
  color: var(--primary);
  border: 1px solid #c7d2fe;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  cursor: pointer;
  font-size: 18px;
  margin-bottom: 12px;
  flex-shrink: 0;
  transition: all 0.15s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.swap-btn:hover:not(:disabled) {
  background: var(--primary);
  color: #fff;
  transform: rotate(180deg);
}

.swap-btn:disabled {
  cursor: not-allowed;
  opacity: 0.4;
}

button.primary {
  background: var(--primary);
  color: #fff;
  border: none;
  border-radius: 8px;
  padding: 12px 28px;
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
  min-width: 100px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

button.primary:hover:not(:disabled) {
  background: var(--primary-hover);
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
}

button.primary:active:not(:disabled) {
  transform: translateY(0);
}

button.primary:disabled {
  background: #9ca3af;
  cursor: not-allowed;
}

.spinner {
  display: inline-block;
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.error {
  color: var(--danger);
  font-size: 13px;
  margin: 8px 0 0;
  padding: 8px 12px;
  background: var(--danger-light);
  border-radius: 6px;
}

.result {
  margin-top: 20px;
  padding: 18px;
  background: var(--success-light);
  border-left: 3px solid var(--success);
  border-radius: 8px;
}

.result.failed {
  background: var(--danger-light);
  border-left-color: var(--danger);
}

.result h3 {
  margin: 0 0 10px;
  font-size: 14px;
  color: var(--success);
  display: flex;
  align-items: center;
  gap: 6px;
}

.result.failed h3 {
  color: var(--danger);
}

.result-icon {
  font-size: 16px;
}

.translated-text {
  font-size: 16px;
  line-height: 1.7;
  margin: 0 0 10px;
  white-space: pre-wrap;
  color: var(--text);
}

.failed-text {
  color: var(--text-muted);
  font-style: italic;
}

.meta {
  color: var(--text-subtle);
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.dot {
  color: var(--text-subtle);
}

/* 过渡动画 */
.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.3s ease;
}

.fade-slide-enter-from {
  opacity: 0;
  transform: translateY(-8px);
}

.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
</style>
