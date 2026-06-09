<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import {
  deleteTranslationById,
  getHistory,
  type Translation,
} from '@/api'

// 父组件可以通过修改 refreshKey 来触发刷新
const props = defineProps<{
  refreshKey: number
}>()

const items = ref<Translation[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const loading = ref(false)
const errorMsg = ref('')

async function fetchList() {
  loading.value = true
  errorMsg.value = ''
  try {
    const res = await getHistory(page.value, pageSize.value)
    items.value = res.items
    total.value = res.total
  } catch (err: any) {
    errorMsg.value = err?.response?.data?.detail || err?.message || '加载历史失败'
  } finally {
    loading.value = false
  }
}

async function handleDelete(id: string) {
  if (!confirm('确定删除这条翻译记录吗？')) return
  try {
    await deleteTranslationById(id)
    // 删完刷新（如果当前页删空了，自动往前翻一页）
    if (items.value.length === 1 && page.value > 1) {
      page.value -= 1
    }
    await fetchList()
  } catch (err: any) {
    errorMsg.value = err?.response?.data?.detail || err?.message || '删除失败'
  }
}

function goPage(p: number) {
  if (p < 1 || p > Math.max(1, Math.ceil(total.value / pageSize.value))) return
  page.value = p
  fetchList()
}

watch(
  () => props.refreshKey,
  () => fetchList(),
)

onMounted(fetchList)

const totalPages = () => Math.max(1, Math.ceil(total.value / pageSize.value))
</script>

<template>
  <section class="history-list card">
    <div class="header">
      <h2><span class="icon">📚</span>历史记录 <small>(共 {{ total }} 条)</small></h2>
      <button class="refresh" :disabled="loading" @click="fetchList">
        <span v-if="loading" class="spinner"></span>
        <span v-else>↻ 刷新</span>
      </button>
    </div>

    <p v-if="errorMsg" class="error">⚠️ {{ errorMsg }}</p>

    <div v-if="loading && items.length === 0" class="loading">
      <div class="big-spinner"></div>
      <p>加载中...</p>
    </div>

    <div v-else-if="items.length === 0" class="empty">
      <div class="empty-icon">📝</div>
      <p>暂无翻译记录</p>
      <small>翻译一些文本试试看吧</small>
    </div>

    <ul v-else class="list">
      <li v-for="item in items" :key="item.id" class="item">
        <div class="text-block">
          <div class="src">
            <span class="lang-tag">{{ item.source_lang }}</span>
            <span class="content">{{ item.source_text }}</span>
          </div>
          <div class="dst">
            <span class="lang-tag">{{ item.target_lang }}</span>
            <span
              v-if="item.status === 'failed'"
              class="content failed-text"
            >
              (翻译失败)
            </span>
            <span v-else class="content">{{ item.translated_text || '(无译文)' }}</span>
            <span v-if="item.status === 'failed'" class="failed-badge">失败</span>
          </div>
          <small class="time">
            <span class="time-icon">🕐</span>
            {{ new Date(item.created_at).toLocaleString() }}
            <span v-if="item.model_used" class="model"> · {{ item.model_used }}</span>
          </small>
        </div>
        <button
          class="delete"
          title="删除这条记录"
          @click="handleDelete(item.id)"
        >
          删除
        </button>
      </li>
    </ul>

    <div v-if="total > pageSize" class="pagination">
      <button :disabled="page <= 1" @click="goPage(page - 1)">
        ‹ 上一页
      </button>
      <span class="page-info">第 {{ page }} / {{ totalPages() }} 页</span>
      <button :disabled="page >= totalPages()" @click="goPage(page + 1)">
        下一页 ›
      </button>
    </div>
  </section>
</template>

<style scoped>
.card {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 24px;
  box-shadow: var(--shadow);
}

.history-list {
  margin-bottom: 24px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

h2 {
  margin: 0;
  font-size: 18px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.icon {
  font-size: 20px;
}

h2 small {
  color: var(--text-muted);
  font-weight: normal;
  font-size: 13px;
  margin-left: 4px;
}

.refresh {
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 6px 14px;
  cursor: pointer;
  font-size: 13px;
  color: var(--text-muted);
  transition: all 0.15s;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-width: 80px;
  justify-content: center;
}

.refresh:hover:not(:disabled) {
  background: var(--primary-light);
  color: var(--primary);
  border-color: #c7d2fe;
}

.refresh:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.empty,
.loading {
  text-align: center;
  color: var(--text-subtle);
  padding: 50px 20px;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 12px;
  opacity: 0.5;
}

.empty p {
  margin: 0 0 4px;
  font-size: 15px;
  color: var(--text-muted);
}

.empty small {
  font-size: 12px;
  color: var(--text-subtle);
}

.big-spinner {
  width: 36px;
  height: 36px;
  border: 3px solid var(--border);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto 12px;
}

.spinner {
  display: inline-block;
  width: 12px;
  height: 12px;
  border: 2px solid var(--border);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.list {
  list-style: none;
  margin: 0;
  padding: 0;
}

.item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 14px 0;
  border-bottom: 1px solid var(--border);
  transition: background 0.15s;
}

.item:hover {
  background: #fafbfc;
  margin: 0 -12px;
  padding: 14px 12px;
  border-radius: 6px;
}

.item:last-child {
  border-bottom: none;
}

.text-block {
  flex: 1;
  margin-right: 12px;
  min-width: 0;
}

.src,
.dst {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin-bottom: 6px;
}

.dst {
  margin-bottom: 4px;
}

.lang-tag {
  display: inline-block;
  background: var(--primary-light);
  color: var(--primary);
  font-size: 11px;
  font-weight: 500;
  padding: 2px 8px;
  border-radius: 4px;
  flex-shrink: 0;
  min-width: 44px;
  text-align: center;
  margin-top: 3px;
  letter-spacing: 0.3px;
}

.content {
  font-size: 14px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
  color: var(--text);
}

.failed-text {
  color: var(--text-subtle);
  font-style: italic;
}

.failed-badge {
  display: inline-block;
  background: var(--danger-light);
  color: var(--danger);
  font-size: 10px;
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 3px;
  margin-left: 6px;
  flex-shrink: 0;
  margin-top: 4px;
}

.time {
  color: var(--text-subtle);
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 6px;
}

.time-icon {
  opacity: 0.7;
}

.model {
  color: var(--text-muted);
}

.delete {
  background: #fff;
  color: var(--danger);
  border: 1px solid #fecaca;
  border-radius: 6px;
  padding: 5px 12px;
  font-size: 12px;
  cursor: pointer;
  flex-shrink: 0;
  transition: all 0.15s;
}

.delete:hover {
  background: var(--danger-light);
  border-color: var(--danger);
}

.error {
  color: var(--danger);
  font-size: 13px;
  margin: 0 0 12px;
  padding: 8px 12px;
  background: var(--danger-light);
  border-radius: 6px;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
  margin-top: 20px;
  font-size: 13px;
  color: var(--text-muted);
}

.pagination button {
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 6px 14px;
  cursor: pointer;
  font-size: 13px;
  color: var(--text);
  transition: all 0.15s;
}

.pagination button:hover:not(:disabled) {
  background: var(--primary-light);
  color: var(--primary);
  border-color: #c7d2fe;
}

.pagination button:disabled {
  cursor: not-allowed;
  opacity: 0.4;
}

.page-info {
  font-variant-numeric: tabular-nums;
}
</style>
