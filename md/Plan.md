# AI 在线翻译项目 — 详细计划（v2）

## 一、协作原则（Code Along 模式）

> **本项目的核心学习方法：引导式编程 (Code Along)**
> 
> 无论哪个 AI 读取到这个项目，都必须遵守以下原则：
> 
> 1. **先出 Plan，再动手** — 每个 Phase 先给出完整的步骤文档，让学习者看清全局再开始
> 2. **引导代替给代码** — 说明"做什么"和"为什么"，引导学习者自己写代码，而不是直接贴完整代码
> 3. **解释每一行** — 每个文件的关键部分都要解释其作用和原理
> 4. **验证性学习** — 每完成一步都要求验证（启动、测试、查看结果），确保理解而不是复制粘贴
> 5. **谁做谁负责** — 明确标注每一步是"你"（学习者）还是"我"（AI）完成

---

## 二、项目概述

一个**AI 驱动的在线翻译平台**，用户输入文本，选择源语言和目标语言，调用 AI 模型进行翻译，并保存翻译历史记录。

### 核心功能
- 文本翻译（支持多语种）
- 翻译历史记录管理（CRUD）
- 基于 LangChain 对接 AI 模型（OpenAI / DeepSeek 等兼容接口）
- 前后端分离架构

### 技术栈

| 层级 | 技术 |
|------|------|
| **后端框架** | FastAPI |
| **ORM** | SQLModel (基于 SQLAlchemy 的 async 模式) |
| **数据库迁移** | Alembic |
| **AI 集成** | LangChain |
| **包管理** | uv（含虚拟环境管理） |
| **数据库** | SQLite（开发） |
| **前端** | Vue 3 + Vite + TypeScript |
| **API 风格** | RESTful |

---

## 三、目录结构

```
在线翻译项目/
├── backend/
│   ├── .venv/                       # uv 虚拟环境（自动创建，不手动操作）
│   ├── app/
│   │   ├── __init__.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── routes/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── translate.py     # 翻译接口
│   │   │   │   └── history.py       # 历史记录接口
│   │   │   └── deps.py              # 依赖注入（DB Session 等）
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py            # 配置管理（环境变量）
│   │   │   └── database.py          # 异步引擎 & Session
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── translation.py       # SQLModel 模型（同时也是 Pydantic Schema）
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── translator.py        # LangChain 翻译服务
│   │   │   └── history.py           # 历史 CRUD 服务
│   │   └── main.py                  # FastAPI 入口
│   ├── alembic/                     # 迁移文件
│   │   ├── versions/
│   │   ├── env.py
│   │   └── script.py.mako
│   ├── alembic.ini
│   ├── pyproject.toml               # 依赖管理
│   └── .python-version
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   │   └── index.ts             # Axios API 封装
│   │   ├── components/
│   │   │   ├── TranslateForm.vue    # 翻译表单
│   │   │   └── HistoryList.vue      # 历史记录列表
│   │   ├── App.vue
│   │   └── main.ts
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts
│   └── tsconfig.json
├── Plan.md
└── Phase1_项目初始化.md
```

---

## 四、数据库设计

### `translations` 表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK, default=uuid4 | 主键 |
| source_text | Text | NOT NULL | 源文本 |
| source_lang | String(10) | NOT NULL | 源语言代码（如 `en`, `zh-CN`） |
| target_lang | String(10) | NOT NULL | 目标语言代码 |
| translated_text | Text | NULLABLE | 翻译结果（翻译失败时为 None） |
| model_used | String(50) | NULLABLE | 使用的 AI 模型名称 |
| tokens_input | Integer | NULLABLE | 输入 token 数 |
| tokens_output | Integer | NULLABLE | 输出 token 数 |
| cost | Float | NULLABLE | 花费（美元） |
| created_at | DateTime | NOT NULL, default=now | 创建时间 |
| updated_at | DateTime | NOT NULL, onupdate=now | 更新时间 |

---

## 五、API 设计

| 方法 | 路径 | 请求体 | 响应 | 说明 |
|------|------|--------|------|------|
| POST | `/api/v1/translate` | `{source_text, source_lang, target_lang}` | `TranslationResponse` | 翻译文本并保存记录 |
| GET | `/api/v1/history` | query: `?page=1&page_size=20` | `{items: [...], total: int}` | 分页历史列表 |
| GET | `/api/v1/history/{id}` | — | `TranslationResponse` | 单条记录 |
| DELETE | `/api/v1/history/{id}` | — | `204 No Content` | 删除记录 |
| GET | `/api/v1/languages` | — | `{languages: [...]}` | 支持的语言列表 |

### 翻译请求/响应 Schema

**POST /api/v1/translate**
```json
// Request
{
  "source_text": "Hello world",
  "source_lang": "en",
  "target_lang": "zh-CN"
}

// Response 200
{
  "id": "a1b2c3d4-...",
  "source_text": "Hello world",
  "source_lang": "en",
  "target_lang": "zh-CN",
  "translated_text": "你好，世界",
  "model_used": "gpt-4o-mini",
  "tokens_input": 5,
  "tokens_output": 7,
  "cost": 0.00015,
  "created_at": "2026-06-06T12:00:00Z",
  "updated_at": "2026-06-06T12:00:00Z"
}
```

---

## 六、实现步骤（8 个 Phase）

### Phase 1：项目初始化与环境搭建
| 步骤 | 谁做 | 内容 |
|------|------|------|
| 1.1 | 你 | 创建 `backend/`，`uv init`，`uv venv` 创建虚拟环境 |
| 1.2 | 你 | `uv add` 安装所有 Python 依赖 |
| 1.3 | 你 | 创建 backend 目录骨架（`app/` 下所有子目录 + `__init__.py`） |
| 1.4 | 你 | 验证：`uv run python -c "import fastapi"` 不报错 |
| 1.5 | 我 | 创建 `frontend/`，Vite + Vue 3 + TypeScript 初始化 |

### Phase 2：Backend 基础框架
| 步骤 | 谁做 | 内容 |
|------|------|------|
| 2.1 | 你 | `core/config.py` — `pydantic-settings` 读取环境变量 |
| 2.2 | 你 | `core/database.py` — 异步引擎 + SessionLocal 工厂 |
| 2.3 | 你 | `main.py` — FastAPI 应用 + 健康检查接口 |
| 2.4 | 你 | 验证：`uv run uvicorn app.main:app --reload` 启动成功 |

### Phase 3：数据库模型与迁移
| 步骤 | 谁做 | 内容 |
|------|------|------|
| 3.1 | 你 | `models/translation.py` — Translation 模型定义 |
| 3.2 | 你 | 配置 Alembic（`alembic init alembic` + 修改 env.py） |
| 3.3 | 你 | 生成并运行迁移，确认表创建成功 |

### Phase 4：CRUD Service（无需单独 Schema）
| 步骤 | 谁做 | 内容 |
|------|------|------|
| 4.1 | 你 | `services/history.py` — 增删查业务逻辑（直接用 SQLModel 模型做请求/响应） |

> 注意：SQLModel 模型本身就是 Pydantic Schema，所以不需要像 SQLAlchemy 那样再单独写一套 `schemas/translation.py`。模型类可以直接用作 FastAPI 的请求体和响应体。

### Phase 5：LangChain 翻译服务
| 步骤 | 谁做 | 内容 |
|------|------|------|
| 5.1 | 你 | `services/translator.py` — 用 LangChain ChatOpenAI 封装翻译 |
| 5.2 | 你 | 配置 prompt 模板，让 AI 按格式翻译 |
| 5.3 | 你 | 先 mock 翻译做测试，有 API Key 后再接入真实模型 |

### Phase 6：API 路由
| 步骤 | 谁做 | 内容 |
|------|------|------|
| 6.1 | 你 | `api/routes/translate.py` — 翻译路由 |
| 6.2 | 你 | `api/routes/history.py` — 历史路由 |
| 6.3 | 你 | 注册路由到 `main.py` |
| 6.4 | 你 | 验证：Swagger UI 上所有接口可用 |

### Phase 7：Vue 前端开发（我来完成）
| 步骤 | 谁做 | 内容 |
|------|------|------|
| 7.1 | 我 | 配置 Vite proxy 解决跨域 |
| 7.2 | 我 | `api/index.ts` — Axios 请求封装 |
| 7.3 | 我 | `TranslateForm.vue` — 翻译表单组件 |
| 7.4 | 我 | `HistoryList.vue` — 历史记录组件 |
| 7.5 | 我 | 联调验证 |

### Phase 8：打磨与优化
| 步骤 | 谁做 | 内容 |
|------|------|------|
| 8.1 | 你/我 | 错误处理完善 |
| 8.2 | 我 | 前端加载/空状态 UI |
| 8.3 | 你 | `.env` 环境变量管理 |

---

## 七、关于虚拟环境（uv 的管理方式）

`uv` 与 `pip`/`poetry` 不同，它对虚拟环境是**自动管理**的：

| 操作 | 说明 |
|------|------|
| `uv init` | 初始化项目，不会自动创建 .venv |
| `uv venv` | **显式创建** `.venv/` 虚拟环境（我们在 Phase 1 做这一步） |
| `uv add xxx` | 自动在 `.venv/` 中安装依赖 |
| `uv run xxx` | 自动激活 `.venv/` 环境执行命令 |
| `uv sync` | 根据 `pyproject.toml` 同步依赖到 `.venv/` |

你**不需要**手动 `source .venv/bin/activate`，`uv run` 会自动使用虚拟环境。

---

## 八、你需要准备的

- [ ] **一个 AI 模型的 API Key**（推荐 DeepSeek 或通义千问，有免费额度）
- [ ] 没有的话 Phase 5 我们可以先用 mock 翻译替代
