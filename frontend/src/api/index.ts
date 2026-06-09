import axios from 'axios'

// ============ 类型定义 ============
// 跟后端 SQLModel 的 Translation 对齐
export interface Translation {
  id: string
  source_text: string
  source_lang: string
  target_lang: string
  translated_text: string | null
  model_used: string | null
  tokens_input: number | null
  tokens_output: number | null
  cost: number | null
  status: 'success' | 'failed'
  created_at: string
  updated_at: string
}

// 跟后端 GET /history 响应模型对齐
export interface HistoryListResponse {
  items: Translation[]
  total: number
}

// 跟后端 GET /languages 响应对齐
export interface Language {
  code: string
  name: string
}

export interface LanguagesResponse {
  languages: Language[]
}

// ============ Axios 实例 ============
const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000, // 翻译最长等 30 秒
})

// ============ 业务方法 ============

// POST /translate
export async function translateText(payload: {
  source_text: string
  source_lang: string
  target_lang: string
}): Promise<Translation> {
  const { data } = await api.post<Translation>('/translate', payload)
  return data
}

// GET /history
export async function getHistory(
  page = 1,
  pageSize = 10,
): Promise<HistoryListResponse> {
  const { data } = await api.get<HistoryListResponse>('/history', {
    params: { page, page_size: pageSize },
  })
  return data
}

// GET /history/{id}
export async function getTranslationById(id: string): Promise<Translation> {
  const { data } = await api.get<Translation>(`/history/${id}`)
  return data
}

// DELETE /history/{id}
export async function deleteTranslationById(id: string): Promise<void> {
  await api.delete(`/history/${id}`)
}

// GET /languages
export async function getLanguages(): Promise<LanguagesResponse> {
  const { data } = await api.get<LanguagesResponse>('/languages')
  return data
}

export default api
