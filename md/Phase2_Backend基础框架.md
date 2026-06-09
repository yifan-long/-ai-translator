# Phase 2：Backend 基础框架

## 目标
搭建 FastAPI 应用的基础骨架：配置管理、数据库连接、应用入口。

**你要写的 3 个文件：**

| 文件 | 用途 |
|------|------|
| `app/core/config.py` | 读取环境变量（API Key、数据库 URL 等） |
| `app/core/database.py` | 创建异步数据库引擎和 Session |
| `app/main.py` | FastAPI 应用入口 + 健康检查接口 |

---

## Step 2.1：配置管理 — `core/config.py`

### 要做什么

创建一个 `Settings` 类，用 `pydantic-settings` 库从环境变量读取配置。

### 为什么需要这个文件

- 以后你的 API Key、数据库地址、模型名称等配置信息，都集中在这里管理
- 不用把敏感信息硬编码在代码里，通过 `.env` 文件或环境变量传入
- `pydantic-settings` 会自动从环境变量读取，也支持 `.env` 文件

### 你需要写的代码

在 `app/core/config.py` 中：

1. 从 `pydantic-settings` 导入 `BaseSettings`
2. 创建一个 `Settings` 类，继承 `BaseSettings`
3. 在这个类中定义以下字段：
   - `DATABASE_URL` — 数据库连接字符串，默认用 SQLite：`sqlite+aiosqlite:///./translations.db`
   - `OPENAI_API_KEY` — API Key，默认空字符串 `""`
   - `OPENAI_API_BASE` — API 地址（兼容 OpenAI 格式），默认 `""`
   - `MODEL_NAME` — 模型名称，默认 `"gpt-4o-mini"`
4. 添加一个 `model_config` 内部类，设置 `env_file = ".env"`（这样可以从 `.env` 文件读取）
5. 在文件末尾创建全局单例：`settings = Settings()`

> ⚠️ **注意**：SQLite 异步需要 `aiosqlite` 包。我们在 Phase 1 没有装它，所以这里先用 `sqlite+aiosqlite:///`，但需要先安装依赖：
> ```powershell
> cd backend; uv add aiosqlite
> ```

### 思考题（写完验证）
- `pydantic-settings` 的 `BaseSettings` 和普通 Pydantic `BaseModel` 有什么区别？
- 为什么 `DATABASE_URL` 要以 `sqlite+aiosqlite:///` 开头，而不是 `sqlite:///`？

### 知识点：pydantic-settings  vs Pydantic BaseModel

| | `BaseSettings` | `BaseModel` |
|---|---|---|
| 用途 | 读取环境变量/配置文件 | 验证请求/响应 JSON 数据 |
| 数据来源 | 环境变量、`.env` 文件 | 代码中传入的字典 |
| 典型场景 | 配置管理（API Key、数据库地址） | API 请求体、响应体 |

**为什么 `DATABASE_URL` 要用 `sqlite+aiosqlite:///` ？**

- `sqlite:///` 是**同步**驱动，用于同步引擎
- `sqlite+aiosqlite:///` 是**异步**驱动，用于 `create_async_engine()`
- `+aiosqlite` 告诉 SQLAlchemy 使用 aiosqlite 这个异步库来操作 SQLite

---

## Step 2.2：数据库连接 — `core/database.py`

### 要做什么

创建异步 SQLAlchemy 引擎和 Session 工厂。

### 背景知识

SQLAlchemy 2.0 支持异步操作，流程是：

| 组件 | 作用 |
|------|------|
| `create_async_engine()` | 创建数据库引擎（负责真正连接数据库） |
| `async_sessionmaker()` | 创建 Session 工厂（每个请求用它生成一个 Session） |
| `AsyncSession` | 数据库会话，用于执行查询 |

### 你需要写的代码

在 `app/core/database.py` 中：

1. 从 `sqlalchemy.ext.asyncio` 导入 `create_async_engine`, `async_sessionmaker`, `AsyncSession`
2. 从 `sqlalchemy.orm` 导入 `DeclarativeBase`
3. 从 `app.core.config` 导入 `settings`
4. 用 `create_async_engine` 创建引擎，传入 `settings.DATABASE_URL`
5. 用 `async_sessionmaker` 创建 `async_session` 工厂，绑定上面的引擎
6. 创建一个 `Base` 类，继承 `DeclarativeBase` — 这个后面模型定义会用
7. 创建一个异步的 `get_db()` 函数（异步生成器）：
   - 用 `async with async_session() as session:` 创建 session
   - `yield session` 提供给 FastAPI 的依赖注入使用

### 关键代码结构提示

```python
# get_db 的大致结构
async def get_db():
    async with async_session() as session:
        yield session
```

### 思考题
- 为什么 `get_db()` 要用 `yield` 而不是 `return`？
- 异步引擎和同步引擎在使用上有什么不同？

### 知识点：yield vs return

```python
# return：一次性返回，会话立即关闭，但数据库连接可能未释放
async def get_db_bad():
    session = async_session()
    return session  # 连接可能泄漏

# yield：生成器，请求结束后自动执行 async with 块外的代码清理
async def get_db_good():
    async with async_session() as session:
        yield session  # 请求结束后 session 自动关闭
```

**为什么用 `yield`？**
- FastAPI 的依赖注入系统会在生成器函数第一次 `yield` 时暂停，等请求处理完后继续执行 `async with` 块外的代码
- 这确保每个请求的数据库连接都能正确释放回连接池，防止连接泄漏

### 知识点：同步引擎 vs 异步引擎

| | 同步引擎 | 异步引擎 |
|---|---|---|
| 创建方式 | `create_engine()` | `create_async_engine()` |
| 执行方式 | 直接执行 SQL | `await session.execute()` |
| 驱动 | `pysqlite` | `aiosqlite` |
| 适用场景 | Flask（Django）同步框架 | FastAPI（async/await） |
| URL 前缀 | `sqlite:///` | `sqlite+aiosqlite:///` |

---

## Step 2.3：应用入口 — `main.py`

### 要做什么

创建 FastAPI 应用实例，添加一个健康检查接口，验证整个后端能启动。

### 你需要写的代码

在 `app/main.py` 中：

1. 从 `fastapi` 导入 `FastAPI`
2. 创建一个 `FastAPI` 应用实例：
   - `title="AI 在线翻译 API"`
   - `version="1.0.0"`
3. 创建一个根路由 `GET /`，返回一个简单的 JSON：
   ```json
   {"message": "AI 在线翻译 API 已启动", "status": "ok"}
   ```
4. 可选：添加一个 `@app.on_event("startup")` 事件，打印一句启动日志

### 知识点：@app.on_event 事件

```python
@app.on_event("startup")
async def startup():
    print("应用启动了")

@app.on_event("shutdown")
async def shutdown():
    print("应用关闭了")
```

| 事件 | 触发时机 |
|------|---------|
| `startup` | ASGI 服务器启动时 |
| `shutdown` | ASGI 服务器关闭时 |

> ⚠️ **注意**：FastAPI 推荐用 ` lifespan` 上下文管理器代替 `@app.on_event`（新写法），但 `@app.on_event` 仍然可用，两者在开发中效果一样。

### 验证

在 `backend/` 目录下执行：
```powershell
uv run uvicorn app.main:app --reload --port 8000
```

如果启动成功，你会看到类似这样的输出：
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

打开浏览器访问 http://127.0.0.1:8000，应该看到：
```json
{"message": "AI 在线翻译 API 已启动", "status": "ok"}
```

再访问 http://127.0.0.1:8000/docs，你会看到 FastAPI 自动生成的 Swagger 文档页面。

---

## 完成后检查清单

- [ ] `uv add aiosqlite` 安装成功
- [ ] `core/config.py` 定义了 `Settings` 类，有 `DATABASE_URL`、`OPENAI_API_KEY` 等字段
- [ ] `core/database.py` 创建了引擎、Session 工厂、`Base`、`get_async_session()`
- [ ] `main.py` 能启动，`GET /` 返回健康检查 JSON
- [ ] http://127.0.0.1:8000/docs 能打开 Swagger 文档

---

## Phase 2 知识点总结

### 架构概览

```
请求 → FastAPI 路由 → 依赖注入(get_db) → 数据库操作
                          ↓
                    async_sessionmaker
                          ↓
                    create_async_engine
                          ↓
                    SQLite (aiosqlite)
```

### 三层配置体系

| 层级 | 来源 | 示例 |
|------|------|------|
| 默认值 | `Settings` 类字段 | `MODEL_NAME = "gpt-4o-mini"` |
| .env 文件 | pydantic-settings 自动读取 | `OPENAI_API_KEY=sk-xxx` |
| 系统环境变量 | 最高优先级 | `export OPENAI_API_KEY=sk-yyy` |

### 依赖注入流程（FastAPI）

```
请求进入
   ↓
FastAPI 调用 get_async_session()
   ↓
yield session（暂停，等待请求处理）
   ↓
请求处理中使用 session
   ↓
请求结束，yield 后的代码继续执行
   ↓
session 自动关闭（async with 块结束）
```

---

**好，开始写吧！先装 aiosqlite，然后依次写 config.py → database.py → main.py。每写完一个文件可以暂停问我确认。**
