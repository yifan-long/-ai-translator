# Phase 1：项目初始化与环境搭建

## 目标
创建 `backend/` 和 `frontend/` 两个子项目，配置好 uv 虚拟环境，安装所有依赖，搭建好目录骨架。

---

## Step 1：初始化 Backend（你来完成）

### 1.1 创建 backend 目录并初始化
```powershell
cd backend
uv init
```

`uv init` 会生成：
- `pyproject.toml` — 项目元数据和依赖配置
- `README.md` — 项目说明
- `.python-version` — Python 版本锁定
- `hello.py` — 示例入口文件（可以删掉）

### 1.2 创建虚拟环境
```powershell
uv venv
```

这会创建 `.venv/` 目录，里面是独立的 Python 虚拟环境。

> **注意**：`uv venv` 只是创建环境，不需要 `activate`。后续所有的 `uv run xxx` 会自动使用这个虚拟环境。

### 1.3 安装后端依赖
```powershell
uv add fastapi uvicorn[standard] sqlalchemy alembic langchain langchain-openai pydantic-settings
```

每条依赖的作用：
| 包 | 作用 |
|------|------|
| `fastapi` | Web 框架 |
| `uvicorn[standard]` | ASGI 服务器（带 `--reload` 热重载） |
| `sqlalchemy` | ORM（我们用 async 异步模式） |
| `alembic` | 数据库迁移管理 |
| `langchain` | AI 模型编排框架 |
| `langchain-openai` | LangChain 的 OpenAI / 兼容接口封装 |
| `pydantic-settings` | 环境变量/配置管理（替代 pydantic.BaseSettings） |

### 1.4 创建 backend 目录结构
在 `backend/` 目录下执行以下 PowerShell 命令，创建所有子目录：

```powershell
# 创建所有子目录
New-Item -ItemType Directory -Force -Path app, app/api, app/api/routes, app/core, app/models, app/schemas, app/services

# 创建所有 __init__.py 空文件
New-Item -ItemType File -Path app/__init__.py, app/api/__init__.py, app/api/routes/__init__.py, app/core/__init__.py, app/models/__init__.py, app/schemas/__init__.py, app/services/__init__.py

# 创建 deps.py（占位文件）
New-Item -ItemType File -Path app/api/routes/deps.py

# 删除 uv init 自带的 hello.py（可选）
Remove-Item hello.py -ErrorAction SilentlyContinue
```

最终 `backend/app/` 下的目录结构：

```
backend/
├── app/
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes/
│   │       ├── __init__.py
│   │       └── deps.py
│   ├── core/
│   │   └── __init__.py
│   ├── models/
│   │   └── __init__.py
│   ├── schemas/
│   │   └── __init__.py
│   └── services/
│       └── __init__.py
├── .venv/
├── pyproject.toml
└── .python-version
```

### 1.5 验证安装
```powershell
uv run python -c "import fastapi; print('FastAPI OK')"
uv run python -c "import sqlalchemy; print('SQLAlchemy OK')"
uv run python -c "import langchain; print('LangChain OK')"
uv run python -c "import alembic; print('Alembic OK')"
```

如果每个命令都输出了 `OK`，说明依赖安装成功且虚拟环境可用。

---

## Step 2：初始化 Frontend（我来完成）

### 2.1 用 Vite 创建 Vue 3 + TypeScript 项目
```powershell
npm create vite@latest frontend -- --template vue-ts
```

### 2.2 安装基础依赖
```powershell
cd frontend
npm install
npm install axios
```

### 2.3 清理模板文件
删除 Vite 默认生成的无用文件（如 `HelloWorld.vue`、默认样式等），保留干净的项目骨架。

---

## Step 3：验证整体结构

```
在线翻译项目/
├── backend/
│   ├── .venv/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   └── routes/
│   │   │       ├── __init__.py
│   │   │       └── deps.py
│   │   ├── core/
│   │   │   └── __init__.py
│   │   ├── models/
│   │   │   └── __init__.py
│   │   ├── schemas/
│   │   │   └── __init__.py
│   │   └── services/
│   │       └── __init__.py
│   ├── pyproject.toml
│   └── .python-version
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   ├── components/
│   │   ├── App.vue
│   │   └── main.ts
│   ├── package.json
│   └── vite.config.ts
├── Plan.md
└── Phase1_项目初始化.md
```

---

## 完成后检查清单

- [ ] `backend/pyproject.toml` 存在且包含所有 7 个依赖
- [ ] `backend/.venv/` 虚拟环境已创建
- [ ] `uv run python -c "import fastapi"` 不报错
- [ ] `backend/app/` 下所有 `__init__.py` 已创建
- [ ] `frontend/package.json` 存在（含 axios 依赖）
- [ ] `npm install` 成功

---

**准备好了吗？从 Step 1.1 开始！**
