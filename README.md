# AI 在线翻译

> 一个能跑能用的全栈翻译小项目。后端 FastAPI + LangChain + DeepSeek，前端 Vue 3。

不是 demo，不是教程代码——是**能 clone 下来 5 分钟跑起来**的完整 Web 应用。

<br>

## 它长这样

```
┌──────────────────────────────────────────────┐
│              AI 在线翻译                      │
│   基于 LangChain + DeepSeek · 多语种互译      │
├──────────────────────────────────────────────┤
│  🌐 翻译                                     │
│                                              │
│  源语言 [English ▼]  ⇄  目标语言 [中文 ▼]    │
│                                              │
│  ┌────────────────────────────────────┐      │
│  │ Hello, how are you today?         │      │
│  │                                    │      │
│  └────────────────────────────────────┘      │
│                  [    翻 译    ]              │
│                                              │
│  ✨ 译文                                     │
│  ┌────────────────────────────────────┐      │
│  │ 你好,今天怎么样?                    │      │
│  │                                    │      │
│  └────────────────────────────────────┘      │
│  模型: deepseek-chat · 2026-06-09 18:30      │
├──────────────────────────────────────────────┤
│  📚 历史记录  (共 12 条)              ↻ 刷新 │
│                                              │
│  [en]  Hello, how are you today?             │
│  [zh]  你好，今天怎么样？            [删除]  │
│  🕐 2026-06-09 18:30 · deepseek-chat         │
│                                              │
│  [en]  Good morning                          │
│  [zh]  早上好                        [删除]  │
│  🕐 2026-06-09 17:45 · deepseek-chat         │
└──────────────────────────────────────────────┘
```

<br>

## 5 分钟跑起来

### 1. 拿代码

```bash
git clone https://github.com/yifan-long/-ai-translator.git
cd -ai-translator
```

### 2. 跑后端

需要 Python 3.11+ 和 [uv](https://docs.astral.sh/uv/)（一个比 pip 快 10 倍的包管理器）。

```bash
cd backend
uv sync                                          # 装依赖
cp .env.example .env                             # 复制配置模板
```

打开 `.env`，填一行：

```env
OPENAI_API_KEY=你的_deepseek_key
```

key 在 [platform.deepseek.com](https://platform.deepseek.com/) 注册就有，**新用户有免费额度**。

```bash
uv run alembic upgrade head                      # 建数据库
uv run uvicorn app.main:app --reload             # 启动
```

后端跑在 `http://127.0.0.1:8000`，API 文档在 `http://127.0.0.1:8000/docs`（自动生成的，能直接调）。

### 3. 跑前端

另开一个终端：

```bash
cd frontend
npm install
npm run dev
```

浏览器打开 `http://localhost:5173`，开始翻译。

<br>

## 它有啥功能

| 功能 | 干啥 |
|------|------|
| 多语种翻译 | 中 / 英 / 日 / 法 / 韩 / 德 / 俄 / 西，8 种语言互译 |
| 历史记录 | 自动保存，可分页查看、删除 |
| 失败降级 | API 挂了不崩，会把"翻译失败"标出来 |
| 结构化输出 | AI 吐的不是乱码，是带分类的结果 |
| 自动迁移 | 数据库表结构变更可追溯、可回滚 |
| 环境变量 | API key 走 `.env`，不在代码里裸奔 |

<br>

## 技术栈

后端：
- **FastAPI** —— 写接口快，自动出 Swagger
- **SQLModel** —— 把 SQLAlchemy 和 Pydantic 揉一起了
- **Alembic** —— 数据库迁移工具（再也不用删库重建）
- **LangChain + LCEL** —— `prompt | llm | parser` 链式调用
- **DeepSeek** —— 便宜好用的中文大模型

前端：
- **Vue 3 + Composition API** —— `<script setup>` 写起来很爽
- **Vite** —— 前端构建工具，冷启动 < 1s
- **TypeScript** —— 类型安全，少写 bug
- **Axios** —— HTTP 客户端

工程化：
- **pydantic-settings** —— 启动时校验必填配置，少一种"线上 500"
- **uv** —— Rust 写的 Python 包管理器

<br>

## 项目结构

```
translate/
├── backend/                  # FastAPI 后端
│   ├── app/
│   │   ├── api/             # 路由
│   │   │   └── routes/      # translate / history / languages
│   │   ├── core/            # 配置、数据库连接
│   │   ├── models/          # SQLModel 数据模型
│   │   └── services/        # 业务逻辑
│   │       ├── translator.py   # LangChain 翻译
│   │       └── history.py      # 历史 CRUD
│   ├── alembic/             # 数据库迁移
│   └── .env.example
├── frontend/                 # Vue 3 前端
│   └── src/
│       ├── api/             # Axios 封装 + TS 类型
│       └── components/      # TranslateForm / HistoryList
└── md/                       # 学习笔记
    ├── Plan.md
    ├── Phase1-8 文档
    └── Alembic迁移指南.md
```

<br>

## API 列表

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/v1/translate` | 翻译，返回完整记录 |
| `GET`  | `/api/v1/history` | 历史列表（支持分页） |
| `GET`  | `/api/v1/history/{id}` | 查单条 |
| `PUT`  | `/api/v1/history/{id}` | 更新 |
| `DELETE` | `/api/v1/history/{id}` | 删除 |
| `GET`  | `/api/v1/languages` | 支持的语言列表 |

<br>

## 一些实现细节

### 依赖注入（写得优雅）

```python
# 一行搞定 session 注入
SessionDep = Annotated[AsyncSession, Depends(get_async_session)]

@router.post("/translate")
async def translate(payload: TranslateRequest, session: SessionDep):
    ...
```

### LCEL 链式调用（大模型调用就这么简单）

```python
chain = prompt | model | StrOutputParser()
result = await chain.ainvoke({"source_text": "...", "source_lang": "en", "target_lang": "zh-CN"})
```

### 错误降级（不把错误暴露给用户）

```python
try:
    text = await translator.translate_text(...)
    status = "success"
except Exception:
    text = None
    status = "failed"   # 记录失败，但流程不崩
```

### 配置 fail-fast（少一种"线上 500"）

```python
class Settings(BaseSettings):
    OPENAI_API_KEY: str = Field(...)   # 三个点是"必填"
    model_config = {"env_file": ".env"}
```

启动时如果 `.env` 缺 key，**直接报错退出**，而不是跑到一半挂。

<br>

## 我踩过的坑

- **SQLite 加 NOT NULL 字段** → 分两步走：先可空带默认值，再 alter 改非空。详见 [Alembic 迁移指南](md/Alembic迁移指南.md)
- **`Annotated[int, Query(1, ge=1)]` 报错** → 默认值要写在 `=` 后面，不能塞 `Query()` 里
- **`Field()` 不会强制必填** → 必填得用 `Field(...)`（三个点）
- **`.env` 必须加 `.gitignore`** → 不然 API key 上 GitHub 就泄露了

<br>

## 给想 fork 的人

如果你想基于这个项目改：

1. **换模型**：改 `backend/.env` 里的 `OPENAI_API_BASE` 和 `OPENAI_API_VERSION`
2. **加字段**：改 `backend/app/models/translation.py` → 跑 `alembic revision --autogenerate -m "..."` → `alembic upgrade head`
3. **加路由**：在 `backend/app/api/routes/` 下加文件 → 在 `app/main.py` 注册
4. **改 UI**：所有组件在 `frontend/src/components/`，CSS 变量在 `frontend/src/style.css`

<br>

## License

MIT —— 随便用，标个来源就行。

<br>

---

如果这个项目对你有帮助，欢迎 **⭐ Star** —— 这是对我最大的鼓励。

有问题或建议提 [Issue](https://github.com/yifan-long/-ai-translator/issues)，看到就回。
