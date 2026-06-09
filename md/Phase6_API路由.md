# Phase 6：API 路由

## 一、本 Phase 目标

把前面做好的 **CRUD Service**（`services/history.py`）和 **翻译服务**（`services/translator.py`）通过 FastAPI 路由暴露成 RESTful API，让前端可以调用。

## 二、最终效果

启动后打开 Swagger UI（`http://localhost:8000/docs`），能看到 5 个接口：

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/translate` | 翻译文本并保存记录 |
| GET | `/api/v1/history` | 分页历史列表 |
| GET | `/api/v1/history/{id}` | 单条记录详情 |
| DELETE | `/api/v1/history/{id}` | 删除记录 |
| GET | `/api/v1/languages` | 支持的语言列表 |

---

## 三、需要理解的关键概念

### 3.1 APIRouter 是什么？

FastAPI 提供了 `APIRouter` 来组织路由。它不是把所有的 `@app.get()` 写在 `main.py` 里，而是：

```
main.py          ← 创建 FastAPI 实例，挂载子路由
  └─ routes/
      ├─ translate.py   ← 翻译相关路由（用 APIRouter）
      └─ history.py     ← 历史相关路由（用 APIRouter）
```

好处：
- 每个文件只关心自己的路由
- 可以统一加前缀（如 `/api/v1`）
- 便于测试和维护

### 3.2 依赖注入 — Depends

FastAPI 的 `Depends` 允许你在路由函数中声明「我需要一个数据库会话」，框架会自动帮你创建和关闭。

在我们的项目里，已经定义了 `get_async_session`（在 `database.py`），它是一个异步生成器，每次请求时：
1. 创建新的 `AsyncSession`
2. 交给路由函数使用
3. 请求结束后自动关闭

### 3.3 Response Model

FastAPI 允许在路由装饰器中用 `response_model` 声明返回的数据结构。我们直接用 `SQLModel` 模型（即 `Translation` 类）作为响应模型，因为它本身就是 Pydantic 模型。

### 3.4 Path 和 Query 参数

- `/{id}` — 路径参数，从 URL 路径中获取
- `?page=1&page_size=20` — 查询参数，从 URL 问号后面获取

---

## 四、实现步骤

### 步骤 6.1：创建 `api/deps.py`（我写）

**谁做：** 我

**做什么：** 创建一个公共的依赖模块，把「获取数据库会话」的逻辑抽出来。

**为什么：** 多个路由文件都需要 `AsyncSession`，放在一个公共文件里可以复用，而不是每个路由文件都去 import `database.py`。

**内容核心：**
- 从 `app.core.database` 导入 `get_async_session`
- 用 `from typing import Annotated` + `Depends` 创建一个类型别名 `SessionDep`
- 这样路由文件里写 `session: SessionDep` 就等价于 `session: AsyncSession = Depends(get_async_session)`

### 步骤 6.2：`api/routes/translate.py`（你做）

**谁做：** 你

**做什么：** 创建翻译接口。

包含一个路由：
- `POST /translate` — 接收 `{source_text, source_lang, target_lang}`，调用翻译服务，保存历史记录，返回翻译结果

**你需要知道的：**

**请求体** — 翻译接口需要接收三个字段：
- `source_text: str` — 源文本
- `source_lang: str` — 源语言（如 "English"）
- `target_lang: str` — 目标语言（如 "Chinese"）

你可以用 `Translation` 模型作为请求体吗？**不能直接复用**，因为 `Translation` 有 `id`、`created_at`、`translated_text` 等字段，用户不应该传这些。

所以你需要创建一个 **纯粹的请求体模型**。可以用 Pydantic 的 `BaseModel`，也可以直接写一个不带 `table=True` 的 SQLModel。

SQLModel 有一个特性：如果你定义类时不加 `table=True`，它就是纯 Pydantic 模型（不会被映射到数据库）。所以你可以写：

```python
from sqlmodel import SQLModel

class TranslateRequest(SQLModel):
    source_text: str
    source_lang: str
    target_lang: str
```

这样它只用作请求体验证，不会生成数据库表。

**路由函数逻辑：**
```
1. 接收请求体 TranslateRequest
2. 调用 translator.translate_text() 获取翻译结果
3. 调用 history.create_translation() 保存到数据库
4. 返回 Translation 对象
```

**思考题：** 返回给前端时，`Translation` 对象里的所有字段都会暴露吗？`id`、`created_at` 等字段应不应该让前端看到？

答案：应该。前端需要 `id` 来做详情/删除操作，需要时间戳来展示。`Translation` 模型没有敏感字段，直接作为响应模型是安全的。

### 步骤 6.3：`api/routes/history.py`（你做）

**谁做：** 你

**做什么：** 创建历史记录 CRUD 接口。

包含三个路由：
- `GET /history` — 分页列表
- `GET /history/{id}` — 单条详情
- `DELETE /history/{id}` — 删除

**三个路由分别的逻辑：**

**GET /history — 分页列表**
- 从查询参数获取 `page`（默认 1）和 `page_size`（默认 20）
- 调用 `history.list_translations()`
- 返回 `{"items": [...], "total": int}`

这里有一个问题：`list_tanslations()` 返回的是 `tuple[list[Translation], int]`，你需要把它组装成 FastAPI 能正确序列化的格式。

**思考题：** FastAPI 怎么知道返回的数据结构？你需要定义一个响应模型吗？

提示：可以用 `response_model` 定义一个包含 `items: list[Translation]` 和 `total: int` 的模型。

**GET /history/{id} — 单条详情**
- 从路径参数获取 `id`（类型 `uuid.UUID`）
- 调用 `history.get_translation()`
- 如果找不到，返回 `404`
- FastAPI 中返回 404 的方式：`from fastapi import HTTPException`，然后 `raise HTTPException(status_code=404, detail="...")`

**DELETE /history/{id} — 删除**
- 从路径参数获取 `id`
- 调用 `history.delete_translation()`
- 如果返回 `False`（没找到），raise 404
- 如果删除成功，返回 **204 No Content**

在 FastAPI 中返回 204 的方法：`return Response(status_code=204)`（需要 `from fastapi import Response`）。

```
小知识：为什么 DELETE 返回 204 而不是 200？
RESTful 规范中，204 No Content 表示「操作成功，但没有内容返回」。
删除后没有数据需要返回给客户端，所以用 204 比 200 更语义化。
```

### 步骤 6.4：注册路由到 `main.py`（你做）

**谁做：** 你

**做什么：** 在 `main.py` 中把两个 `APIRouter` 挂载到 FastAPI 实例上。

**核心代码思路：**
```python
from app.api.routes import translate, history

app.include_router(translate.router, prefix="/api/v1")
app.include_router(history.router, prefix="/api/v1")
```

注意：`translate.py` 和 `history.py` 中的路由路径不要重复。比如：
- `translate.py` 里用 `@router.post("/translate")`
- `history.py` 里用 `@router.get("/history")`

加上前缀 `/api/v1` 后就变成了 `/api/v1/translate` 和 `/api/v1/history`。

### 步骤 6.5：创建 languages 接口（你做）

**谁做：** 你

**做什么：** 添加一个 GET `/api/v1/languages` 接口，返回支持的语言列表。

**为什么需要这个接口？** 前端的下拉菜单需要知道有哪些语言选项。与其在前端硬编码，不如后端提供一个接口，方便以后扩充。

返回格式：
```json
{
  "languages": [
    {"code": "en", "name": "English"},
    {"code": "zh-CN", "name": "Chinese (Simplified)"},
    {"code": "ja", "name": "Japanese"},
    {"code": "ko", "name": "Korean"},
    {"code": "fr", "name": "French"},
    {"code": "de", "name": "German"},
    {"code": "es", "name": "Spanish"},
    {"code": "pt", "name": "Portuguese"},
    {"code": "ru", "name": "Russian"},
    {"code": "ar", "name": "Arabic"}
  ]
}
```

这个接口可以放在 `translate.py` 里（因为和翻译功能相关），也可以单独放。**建议放在 `translate.py` 里**。

### 步骤 6.6：验证（你做）

**谁做：** 你

**做什么：** 启动服务器，打开 Swagger UI，测试 5 个接口。

命令：
```bash
uv run uvicorn app.main:app --reload
```

打开浏览器访问 `http://localhost:8000/docs`

**验证清单：**
- [ ] Swagger UI 正常加载，能看到 5 个接口
- [ ] POST /api/v1/translate — 输入 "Hello world" / "English" / "Chinese"，返回翻译结果和完整记录
- [ ] GET /api/v1/languages — 返回语言列表
- [ ] GET /api/v1/history — 能看到刚才翻译的记录
- [ ] GET /api/v1/history/{id} — 用上一步返回的 id 查询，能查到
- [ ] DELETE /api/v1/history/{id} — 删除后再次查询返回 404

---

## 五、文件变更清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `app/api/deps.py` | 新建 | 公共依赖 |
| `app/api/routes/translate.py` | 新建 | 翻译 + 语言列表路由 |
| `app/api/routes/history.py` | 新建 | 历史记录 CRUD 路由 |
| `app/main.py` | 修改 | 注册 router |

---

## 六、提示与常见问题

### Q1：为什么不把 `SessionDep` 直接放在 `database.py` 里？

技术上可以，但 `database.py` 属于 `core` 层，`Depends` 是 FastAPI 框架的特性，放在 `api/deps.py` 更符合分层逻辑。

### Q2：为什么用 `uuid.UUID` 类型而不是 `str`？

FastAPI 自动支持 `uuid.UUID` 类型，它会自动把路径参数中的字符串（如 `"a1b2c3d4-..."`）解析成 Python 的 UUID 对象。如果格式不合法，自动返回 422 错误。

### Q3：如果翻译接口调用 DeepSeek 超时怎么办？

目前我们先不做超时处理，到了 Phase 8 打磨阶段再统一加错误处理。翻译失败时，`translated_text` 会留空。

### Q4：`response_model` 有什么用？

FastAPI 会根据 `response_model`：
1. 自动序列化返回数据
2. 在 Swagger UI 中生成文档
3. 过滤掉不在模型中的字段（安全）
