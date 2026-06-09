# Phase 4：CRUD Service（业务逻辑层）

## 目标
在 `app/services/history.py` 写 4 个 CRUD 函数：增、查单条、查列表、删。

**你要完成的文件：**

| 文件 | 用途 |
|------|------|
| `app/services/history.py` | 翻译历史记录的增删查业务逻辑 |

> 注意：本项目**没有 `schemas/` 目录**。SQLModel 模型本身既是 SQLAlchemy 表模型，又是 Pydantic Schema（请求/响应体），一鱼两吃。

---

## Step 4.1：写 `services/history.py`

### 4.1.1 为什么需要 service 层

直接想一下：FastAPI 路由（Phase 6 写）拿到 HTTP 请求，**应该直接调数据库吗？**

```
❌ 路由直接调数据库：
   路由代码 = 解析参数 + 业务逻辑 + SQL 拼接 + 异常处理 + 响应格式化
   路由函数会变成"什么都干"的大泥球
   测试时必须启数据库，单元测试很慢

✅ 路由调 service、service 调数据库：
   路由 = 解析参数 + 调 service + 格式化响应（薄）
   service = 业务逻辑（厚，但纯函数，可独立测试）
   model   = 表结构（只管存数据）
```

**service 层的好处**：
- 路由变薄，HTTP 解析和业务逻辑解耦
- 业务逻辑可以独立测试（不依赖 HTTP）
- 同一段业务逻辑可以被多个路由复用（比如 `/translate` 和 `/history` 都要用"创建记录"）

### 4.1.2 SQLModel 异步 CRUD 用法速查

| 想要做什么 | 用什么 API | 备注 |
|---|---|---|
| 新增一行 | `session.add(obj)` + `await session.commit()` + `await session.refresh(obj)` | add 只是入队，commit 才真写库；refresh 把 DB 生成的字段（id、created_at）拉回对象 |
| 按主键查 | `await session.get(Translation, id)` | 没找到返回 None |
| 自定义条件查 | `stmt = select(Translation).where(...)` + `await session.exec(stmt)` | exec 返回 `Result` 对象，要 `.first()` / `.all()` |
| 分页 | `stmt.offset((page-1)*page_size).limit(page_size)` | SQLAlchemy 标准语法 |
| 删一行 | `await session.delete(obj)` + `await session.commit()` | delete 前要先把对象查出来 |
| 统计总数 | `stmt = select(func.count()).select_from(Translation)` + `await session.exec(stmt).one()` | 列表接口要返回 `total`，必须查 |

### 4.1.3 你要写什么

打开 `app/services/history.py`，依次写 4 个函数。

#### 函数 1：创建翻译记录

```python
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.translation import Translation
from datetime import datetime


async def create_translation(
    session: AsyncSession,
    source_text: str,
    source_lang: str,
    target_lang: str,
    translated_text: str | None = None,
    model_used: str | None = None,
    tokens_input: int | None = None,
    tokens_output: int | None = None,
    cost: float | None = None,
) -> Translation:
    """创建一条翻译记录，返回写入后的对象。"""
    translation = Translation(
        source_text=source_text,
        source_lang=source_lang,
        target_lang=target_lang,
        translated_text=translated_text,
        model_used=model_used,
        tokens_input=tokens_input,
        tokens_output=tokens_output,
        cost=cost,
    )
    session.add(translation)
    await session.commit()
    await session.refresh(translation)  # 拉回 DB 生成的 id、created_at、updated_at
    return translation
```

**关键点**：
- 不用手动传 `id`（`Field(default_factory=uuid.uuid4)` 自动生成）
- 不用手动传 `created_at` / `updated_at`（数据库层 `func.now()` 自动填）
- `session.refresh()` 是 SQLAlchemy 异步里**特有**的：commit 后对象是"过期"的，要 refresh 才能拿到 DB 生成的字段

#### 函数 2：按 ID 查询

```python
from uuid import UUID


async def get_translation(session: AsyncSession, id: UUID) -> Translation | None:
    """按主键查询；找不到返回 None。"""
    return await session.get(Translation, id)
```

**关键点**：
- `session.get(Model, primary_key)` 是 SQLAlchemy 提供的快速方法，**不会发 SQL 直到真的调用**（但这里是 await，所以会发）
- 找不到返回 `None`，调用方自己处理

#### 函数 3：分页列表

```python
from sqlmodel import select
from sqlalchemy import func


async def list_translations(
    session: AsyncSession,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Translation], int]:
    """分页查询翻译历史，返回 (items, total)。"""
    # 1) 查总数
    count_stmt = select(func.count()).select_from(Translation)
    total = (await session.exec(count_stmt)).one()

    # 2) 查当页数据，按创建时间倒序
    offset = (page - 1) * page_size
    stmt = (
        select(Translation)
        .order_by(Translation.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    result = await session.exec(stmt)
    items = list(result.all())

    return items, total
```

**关键点**：
- 返回 `tuple[list, int]` —— 列表 API 的标准返回结构（前端要算"第几页/共几页"）
- `order_by(created_at.desc())` —— 最新的在前面
- `offset` / `limit` —— SQLAlchemy 标准分页
- `select(func.count()).select_from(Translation)` —— 单独查总数（不去当页数据里数）

#### 函数 4：按 ID 删除

```python


async def delete_translation(session: AsyncSession, id: UUID) -> bool:
    """删除一条记录；返回是否真的删了。"""
    translation = await session.get(Translation, id)
    if translation is None:
        return False  # 没找到，不删
    await session.delete(translation)
    await session.commit()
    return True
```

**关键点**：
- 先 `get` 再 `delete` —— SQLAlchemy 没提供"按主键直接删"的方法
- 返回 `bool` 让调用方知道"是删了/本来就没"（HTTP 层据此返回 204 vs 404）

### 4.1.4 把代码串起来

最终 `app/services/history.py` 长这样（你可以直接照着写，或者自己先写再对比）：

```python
from datetime import datetime
from uuid import UUID

from sqlmodel import select
from sqlalchemy import func
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.translation import Translation


async def create_translation(
    session: AsyncSession,
    source_text: str,
    source_lang: str,
    target_lang: str,
    translated_text: str | None = None,
    model_used: str | None = None,
    tokens_input: int | None = None,
    tokens_output: int | None = None,
    cost: float | None = None,
) -> Translation:
    translation = Translation(
        source_text=source_text,
        source_lang=source_lang,
        target_lang=target_lang,
        translated_text=translated_text,
        model_used=model_used,
        tokens_input=tokens_input,
        tokens_output=tokens_output,
        cost=cost,
    )
    session.add(translation)
    await session.commit()
    await session.refresh(translation)
    return translation


async def get_translation(session: AsyncSession, id: UUID) -> Translation | None:
    return await session.get(Translation, id)


async def list_translations(
    session: AsyncSession,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Translation], int]:
    count_stmt = select(func.count()).select_from(Translation)
    total = (await session.exec(count_stmt)).one()

    offset = (page - 1) * page_size
    stmt = (
        select(Translation)
        .order_by(Translation.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    result = await session.exec(stmt)
    items = list(result.all())

    return items, total


async def delete_translation(session: AsyncSession, id: UUID) -> bool:
    translation = await session.get(Translation, id)
    if translation is None:
        return False
    await session.delete(translation)
    await session.commit()
    return True
```

---

## Step 4.2：验证（用 REPL 直接调）

写完后，**不通过 HTTP** 也能验证 —— 直接在 Python REPL 里调这 4 个函数：

```powershell
cd backend
uv run python
```

进入 REPL 后执行：

```python
import asyncio
from app.core.database import async_session
from app.services.history import (
    create_translation, get_translation,
    list_translations, delete_translation,
)

async def test():
    async with async_session() as session:
        # 1) 创建
        t = await create_translation(
            session,
            source_text="Hello world",
            source_lang="en",
            target_lang="zh-CN",
            translated_text="你好世界",
            model_used="gpt-4o-mini",
            tokens_input=2,
            tokens_output=3,
            cost=0.0001,
        )
        print("✅ 创建成功，id =", t.id)
        print("   created_at =", t.created_at)

        # 2) 按 ID 查
        got = await get_translation(session, t.id)
        assert got is not None
        assert got.source_text == "Hello world"
        print("✅ 查询成功，source_text =", got.source_text)

        # 3) 列表
        items, total = await list_translations(session, page=1, page_size=10)
        print(f"✅ 列表查询成功，total = {total}, 本页 {len(items)} 条")
        for item in items:
            print(f"   - {item.id}: {item.source_text} → {item.translated_text}")

        # 4) 删除
        ok = await delete_translation(session, t.id)
        assert ok is True
        print("✅ 删除成功")

        # 5) 再查应该没了
        gone = await get_translation(session, t.id)
        assert gone is None
        print("✅ 删后再查返回 None")

asyncio.run(test())
```

**预期输出**：

```
✅ 创建成功，id = 11065b6d-xxxx-xxxx-xxxx-xxxxxxxxxxxx
   created_at = 2026-06-07 21:30:00.xxx
✅ 查询成功，source_text = Hello world
✅ 列表查询成功，total = 1, 本页 1 条
   - 11065b6d-xxxx-...: Hello world → 你好世界
✅ 删除成功
✅ 删后再查返回 None
```

> ⚠️ 第一次跑可能看到一些 SQL 日志（因为 `database.py` 里 `echo=True`）。这是正常的。

---

## 思考题（写完验证时思考）

1. 为什么 `create_translation` 里要 `await session.refresh(translation)`，不 refresh 会怎样？
2. `session.get(Translation, id)` 和 `session.exec(select(Translation).where(Translation.id == id)).first()` 有什么区别？什么时候用哪个？
3. 为什么删除要先 get 再 delete？SQLAlchemy 不支持"按主键直接 delete 吗"？
4. 列表函数返回 `tuple[list, int]` 而不是 `dict` 或自定义类，这样设计有什么好处？

<details>
<summary>答案 1</summary>
- `commit()` 之后，SQLAlchemy 默认会让对象"过期"（expire），所有字段值会被清空（但不会从内存里删掉）
- 下次访问 `t.id` / `t.created_at` 时，会**自动**再发一次 SQL 重新查（lazy load）
- 但如果 session 已经关闭了，再访问就报错
- `refresh()` 主动把 DB 生成的字段（id、created_at、updated_at）拉回来，避免 lazy load
- 在 FastAPI 这种"commit 后立刻返回对象给响应"的场景下，refresh 是必须的
</details>

<details>
<summary>答案 2</summary>
- `session.get()` 是 SQLAlchemy 提供的**专门**方法，**优先从 session 的 identity map 里找**（就是这会话里刚 add 过的对象），找不到才发 SQL
- `session.exec(select(...).where(...))` 每次都发 SQL
- 性能：`session.get` 更快（缓存命中时不发 SQL）
- 灵活性：`select` 可以加任意条件（`where`、`order_by`、`join`），`get` 只能按主键
- 经验法则：按主键查用 `get`，其他用 `select`
</details>

<details>
<summary>答案 3</summary>
- SQLAlchemy 2.0 提供了 `session.get(Model, id)`，但**没有** `session.delete_by_id(Model, id)`
- 因为 `session.delete(obj)` 需要一个 ORM 对象（它要追踪对象状态）
- 这是设计选择：ORM 鼓励"先 get 出来看一眼，确认存在再删"，而不是"盲删"
- 实际场景：这个流程符合"删之前给用户一个二次确认"的好习惯
</details>

<details>
<summary>答案 4</summary>
- `tuple` 是 Python 内置结构，调用方直接 `items, total = await list_translations(...)` 解包，最简洁
- 性能：`tuple` 比 `dataclass` / `dict` 都轻量
- 缺点：调用方要记顺序（`[0]` 是 items 还是 total？）
- Phase 6 的路由层会再包一层 `{"items": [...], "total": N}` 响应结构
</details>

---

## 知识点总结

### 架构（三层）

```
┌──────────────────────────────┐
│ Phase 6 写：FastAPI 路由层     │   解析 HTTP、调用 service、返回 JSON
├──────────────────────────────┤
│ Phase 4 写：Service 业务逻辑层 │   ★ 你在这里 ★  增删查业务逻辑
├──────────────────────────────┤
│ Phase 3 写：SQLModel 模型层    │   表结构
└──────────────────────────────┘
```

### SQLModel 异步操作关键 API

| 操作 | 代码 |
|---|---|
| **新增** | `session.add(obj)` → `await session.commit()` → `await session.refresh(obj)` |
| **查主键** | `await session.get(Model, pk)` |
| **查条件** | `result = await session.exec(select(Model).where(...))` → `result.all()` / `result.first()` |
| **查总数** | `total = (await session.exec(select(func.count()).select_from(Model))).one()` |
| **分页** | `.offset((page-1)*page_size).limit(page_size)` |
| **排序** | `.order_by(Model.field.desc())` |
| **删除** | `await session.delete(obj)` → `await session.commit()` |

### SQLModel 的"双重身份"

```python
class Translation(SQLModel, table=True):
    source_text: str = Field(...)

# 同一个类：
t = Translation(source_text="hi")           # 1) 当 Pydantic 模型用：构造实例
session.add(t)                              # 2) 当 SQLAlchemy 模型用：ORM 操作
return t                                    # 3) 又当响应模型用：FastAPI 自动 JSON 序列化
```

这就是为什么本项目**不需要** `schemas/` 目录。

---

## 完成后检查清单

- [ ]  `app/services/history.py` 写完，包含 4 个函数：`create_translation` / `get_translation` / `list_translations` / `delete_translation`
- [ ]  所有函数都是 `async def`
- [ ]  函数参数带类型注解（`session: AsyncSession`、`id: UUID` 等）
- [ ]  REPL 测试 4 个函数都跑通
- [ ]  创建后能查到、列表能返回正确的 total、删除后返回 None

---

**好，从 Step 4.1 开始吧！把 `app/services/history.py` 写完，然后跑 REPL 测试。**
