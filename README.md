# AI 在线翻译 🌐

基于 **FastAPI + LangChain + Vue 3** 的 AI 在线翻译应用，使用 DeepSeek 大模型驱动，支持多语种互译、历史记录管理。

## ✨ 特性

- 🤖 基于 LangChain + DeepSeek 的高质量翻译
- 📚 翻译历史记录（分页、删除、失败状态展示）
- 🎨 响应式 UI，支持加载动画与失败状态
- 🔒 敏感配置走环境变量（fail-fast 校验）
- 📦 Alembic 数据库迁移，结构变更可追溯
- ⚡ LCEL 链式调用：`prompt | llm | StrOutputParser()`

## 🛠️ 技术栈

**后端**：FastAPI · SQLModel · SQLite · Alembic · LangChain · DeepSeek · Pydantic Settings
**前端**：Vue 3 · Vite · TypeScript · Axios

## 📂 项目结构

```
translate/
├── backend/                # FastAPI 后端
│   ├── app/
│   │   ├── api/            # 路由（translate / history / languages）
│   │   ├── core/           # 配置、数据库连接
│   │   ├── models/         # SQLModel 模型
│   │   └── services/       # 业务逻辑（translator / history）
│   ├── alembic/            # 数据库迁移
│   ├── .env.example        # 环境变量模板
│   └── pyproject.toml
├── frontend/               # Vue 3 前端
│   └── src/
│       ├── api/            # Axios 封装 + 类型
│       ├── components/     # TranslateForm / HistoryList
│       └── App.vue
└── md/                     # 8 个阶段的学习笔记
```

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/你的用户名/ai-translator.git
cd ai-translator
```

### 2. 启动后端

```bash
cd backend

# 安装依赖（需要先装 uv：https://docs.astral.sh/uv/）
uv sync

# 复制环境变量模板，填入你的 DeepSeek API Key
cp .env.example .env
# 编辑 .env，把 OPENAI_API_KEY 改成你的真实 key

# 应用数据库迁移
uv run alembic upgrade head

# 启动服务
uv run uvicorn app.main:app --reload
```

后端跑在 **http://127.0.0.1:8000**，Swagger 文档在 http://127.0.0.1:8000/docs

### 3. 启动前端

新开一个终端：

```bash
cd frontend
npm install
npm run dev
```

前端跑在 **http://localhost:5173**

## 🔑 获取 DeepSeek API Key

1. 访问 [https://platform.deepseek.com/](https://platform.deepseek.com/)
2. 注册并实名认证
3. 在「API Keys」页面创建一个 Key
4. 把 Key 填到 `backend/.env` 的 `OPENAI_API_KEY=` 后面

## 📡 API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/translate` | 翻译文本，返回完整记录（含 status） |
| GET  | `/api/v1/history` | 分页获取翻译历史（`?page=1&page_size=10`） |
| GET  | `/api/v1/history/{id}` | 获取单条记录 |
| PUT  | `/api/v1/history/{id}` | 更新记录 |
| DELETE | `/api/v1/history/{id}` | 删除记录 |
| GET  | `/api/v1/languages` | 获取支持的语言列表 |

## 📝 学习笔记

详细的项目搭建指南都在 [`md/`](./md) 目录下：

- [Alembic 迁移指南](./md/Alembic迁移指南.md) — 数据库迁移为什么这么重要
- Phase 1 ~ Phase 8 — 从零到完整项目的 8 个阶段

## 🧪 技术亮点

### 后端
- **APIRouter 模块化路由**：每个功能一个 router，主入口 `app.include_router` 聚合
- **`Annotated` 依赖注入**：`SessionDep = Annotated[AsyncSession, Depends(...)]` 类型安全
- **LCEL 链式调用**：`chain = prompt | llm | StrOutputParser()`，可组合、可测试
- **fail-fast 配置**：`OPENAI_API_KEY: str = Field(...)` 启动时无 key 直接报错
- **错误降级**：翻译失败时不抛 500，依然保存记录，`status="failed"` 标记

### 前端
- **Vite 代理**：`/api` 代理到后端，规避 CORS
- **TS 路径别名**：`@/components/...` 简洁引用
- **Vue 3 Composition API**：`<script setup>` + `defineEmits` / `defineProps`
- **状态管理零依赖**：用 `ref` + `emit` 父组件通信，告别 Vuex/Pinia 过度设计
- **CSS 变量**：统一的颜色 / 阴影 / 圆角，主题切换只需改 `:root`

## 📄 License

MIT
