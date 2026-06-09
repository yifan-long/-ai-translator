# Phase 3：数据库模型与迁移

## 目标
创建 `Translation` 数据库模型，配置 Alembic 自动管理表结构变更，生成并运行第一次迁移。

**你要完成的 3 个步骤：**

| 步骤 | 文件/操作 | 内容 |
|------|-----------|------|
| 3.1 | `models/translation.py` | SQLModel 模型定义 |
| 3.2 | Alembic 配置 | `alembic init alembic` + 修改 `env.py` |
| 3.3 | 生成迁移 | 自动检测模型变更，生成迁移脚本，建表 |

---

## Step 3.1：定义 Translation 模型

### 背景知识

回顾一下数据库设计（Plan.md 中已有）：

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| source_text | str | 源文本 |
| source_lang | str(10) | 源语言代码 |
| target_lang | str(10) | 目标语言代码 |
| translated_text | str | 翻译结果 |
| model_used | str(50) | 使用的模型 |
| tokens_input | int | 输入 token |
| tokens_output | int | 输出 token |
| cost | float | 花费 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

### 要做什么

在 `app/models/translation.py` 中定义 `Translation` 类，使用 **SQLModel** 语法。

### SQLModel vs SQLAlchemy：区别在哪里

普通 SQLAlchemy 写法：
```python
from sqlalchemy import Column, String, Text
class Translation(Base):
    source_text = Column(Text, nullable=False)
```

SQLModel 写法：
```python
from sqlmodel import SQLModel, Field
class Translation(SQLModel, table=True):
    source_text: str = Field(sa_type=Text, nullable=False)
```

**核心变化**：
- 用类型注解 (`str`, `int`, `Optional[str]`) 代替 `Column` 声明
- 用 `Field()` 代替 `Column()`，额外信息（约束、默认值）通过参数传入
- `table=True` 告诉 SQLModel 这是一个数据库表（不是纯 Pydantic 模型）
- **模型同时也是 Pydantic Schema** — 不需要再单独写一套请求/响应模型

### 你需要用到的组件

| 组件 | 从哪里导入 | 作用 |
|------|-----------|------|
| `SQLModel, Field` | `sqlmodel` | 模型基类和字段定义 |
| `Optional` | `typing` | 声明可选字段 |
| `uuid4` | `uuid`（Python 内置） | 生成 UUID 默认值 |
| `datetime` | `datetime`（Python 内置） | 时间字段类型注解 |
| `Column, DateTime, Text, func` | `sqlalchemy` | 一些特殊列类型还需 SQLAlchemy 的 `sa_column` 参数 |

### 关键实现思路

1. 定义 `Translation(SQLModel, table=True)` 类
2. 设置 `__tablename__ = "translations"`
3. 每个字段用 `类型注解 = Field(...)` 的方式定义：
   - `id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)`
   - 字符串字段：`source_lang: str = Field(max_length=10, nullable=False)`
   - 可选字段：`model_used: Optional[str] = Field(max_length=50, default=None)`
   - 特殊类型（Text, DateTime）：`source_text: str = Field(sa_type=Text, nullable=False)`
4. 对于 `created_at` 和 `updated_at`，需要用 `sa_column=Column(...)` 传入数据库级别的默认值：
   ```python
   created_at: datetime = Field(
       sa_column=Column(DateTime, default=func.now(), nullable=False)
   )
   ```

### 需要注意的点

- `translated_text` 允许为空：`Optional[str] = Field(sa_type=Text, default=None)`
- `tokens_input`, `tokens_output`, `cost` 允许为空
- `model_used` 允许为空
- 注意文件名是 `translation.py`（之前有拼写错误 `tanslation.py`）

### 验证方式

写完后在 `backend/` 下运行：
```powershell
uv run python -c "from app.models.translation import Translation; print('Model OK')"
```

---

## Step 3.2：配置 Alembic

### 要做什么

用 Alembic 管理数据库表结构的版本。第一次需要初始化，然后配置让它能识别你的 SQLAlchemy 模型。

### 3.2.1 安装并初始化

等一下 — 你的 `backend/pyproject.toml` 里已经有 `alembic` 了（Phase 1 装的）。直接初始化：

```powershell
cd backend; uv run alembic init alembic
```

这会生成：
- `backend/alembic/` 目录（含 `env.py`, `script.py.mako`）
- `backend/alembic.ini`

### 3.2.2 修改 alembic.ini

打开 `alembic.ini`，找到这一行：
```
sqlalchemy.url = driver://user:pass@localhost/dbname
```

**改成**（注意：这里写同步 URL，因为 Alembic 迁移脚本本身是同步的，真正的异步连接在 env.py 里配置）：
```
sqlalchemy.url = sqlite:///./translation.db
```

### 3.2.3 修改 alembic/env.py

这是最关键的一步 — 告诉 Alembic 你的模型在哪里，以及如何异步连接数据库。

打开 `alembic/env.py`，找到以下几处修改：

**修改 1** — 在文件顶部添加导入代码（在 `from alembic import context` 行之后）：
```python
import sys
from pathlib import Path
# 把 backend/ 目录加入 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.translation import Translation  # 导入模型让 Alembic 检测到
from sqlmodel import SQLModel  # SQLModel.metadata 就是表的元数据
```

**修改 2** — 找到 `target_metadata = None`，改为：
```python
target_metadata = SQLModel.metadata
```

**修改 3** — 因为我们的数据库引擎是异步的，需要修改 Alembic 的 `run_migrations_online()` 函数，让它使用异步引擎。找到文件末尾的 `run_migrations_online()` 函数，修改为：

```python
def run_migrations_online():
    """Run migrations in 'online' mode using async engine."""
    from app.core.database import async_engine
    
    with async_engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        
        with context.begin_transaction():
            context.run_migrations()
```

> **注意**：如果你的 Alembic 版本在 `env.py` 中使用了 `asyncio.run()` 的方式，则按照模板里的异步写法即可。关键点是：Alembic 的同步 `connect()` 对 SQLite 是兼容的，因为我们实际用的是 `aiosqlite` 的同步回退模式。

这告诉 Alembic："用 Base.metadata 来比对数据库当前状态和模型定义，自动生成迁移脚本"。

### 验证

```powershell
uv run alembic check
```

如果输出类似 `No new migrations to create` 或者能正常执行不报错，说明配置正确。

---

## Step 3.3：生成并运行第一次迁移

### 3.3.1 生成迁移脚本

```powershell
uv run alembic revision --autogenerate -m "init translations table"
```

这会：
1. 读取 `Base.metadata` 中的所有模型定义
2. 比对数据库当前状态（还没有表）
3. 在 `alembic/versions/` 下生成一个迁移脚本

你可以在 `alembic/versions/` 下找到生成的 `.py` 文件，打开看看内容，里面有 `upgrade()` 和 `downgrade()` 两个函数。

### 3.3.2 运行迁移（真正建表）

```powershell
uv run alembic upgrade head
```

### 3.3.3 验证表已创建

**方式 1** — 直接检查 SQLite 文件：
```powershell
uv run python -c "
import sqlite3
conn = sqlite3.connect('translation.db')
cursor = conn.execute(\"SELECT name FROM sqlite_master WHERE type='table'\")
for row in cursor.fetchall():
    print(row[0])
conn.close()
"
```

**方式 2** — 用 SQLAlchemy 检查：
```powershell
uv run python -c "
from app.core.database import async_engine
from sqlalchemy import text
import asyncio

async def check():
    async with async_engine.connect() as conn:
        result = await conn.execute(text(\"SELECT name FROM sqlite_master WHERE type='table'\"))
        for row in result:
            print(f'表: {row[0]}')

asyncio.run(check())
"
```

你应该能看到 `translations` 和 `alembic_version` 两个表。

---

## 完成后检查清单

- [ ] `models/translation.py` 定义了 `Translation` 模型
- [ ] `uv run python -c "from app.models.translation import Translation"` 不报错
- [ ] `alembic.ini` 中 `sqlalchemy.url` 已修改
- [ ] `alembic/env.py` 中已导入模型和设置 `target_metadata`
- [ ] `uv run alembic check` 不报错
- [ ] `uv run alembic revision --autogenerate -m "init"` 成功生成迁移文件
- [ ] `uv run alembic upgrade head` 成功执行
- [ ] `translation.db` 文件已生成，且包含 `translations` 表

---

**好，从 Step 3.1 开始吧！先创建 `models/translation.py`，写完了告诉我。**
