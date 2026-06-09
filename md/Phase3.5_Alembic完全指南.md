# Phase 3.5：Alembic 完全指南（零基础版）

> 配套文件：[Phase3_数据库模型与迁移.md](Phase3_数据库模型与迁移.md) — 这份文档是它的"深度讲解版"。
> 读完这份，你不仅会跑通本项目的 alembic，以后任何 SQLAlchemy / SQLModel 项目都能上手。

---

## 目录

- [0. 在开始之前：你必须建立的心智模型](#0-在开始之前你必须建立的心智模型)
- [1. 为什么要 Alembic？](#1-为什么要-alembic)
- [2. 6 个核心概念（背下来）](#2-6-个核心概念背下来)
- [3. 准备工作：确认本项目当前状态](#3-准备工作确认本项目当前状态)
- [4. Step 1：`alembic init alembic` — 创建迁移骨架](#4-step-1alembic-init-alembic--创建迁移骨架)
- [5. Step 2：修改 `alembic.ini` — 配置数据库 URL](#5-step-2修改-alembicini--配置数据库-url)
- [6. Step 3：修改 `env.py` — 最关键的一步（教你看懂每一行）](#6-step-3修改-envpy--最关键的一步教你看懂每一行)
- [7. Step 4：生成第一次迁移（autogenerate）](#7-step-4生成第一次迁移autogenerate)
- [8. Step 5：执行迁移，建表](#8-step-5执行迁移建表)
- [9. Step 6：验证表真的建好了](#9-step-6验证表真的建好了)
- [10. 未来的工作流：3 步循环（最重要）](#10-未来的工作流3-步循环最重要)
- [11. 常用命令清单（速查）](#11-常用命令清单速查)
- [12. 常见坑（提前预警）](#12-常见坑提前预警)
- [13. 如果你只记 3 件事](#13-如果你只记-3-件事)
- [14. 完成检查清单](#14-完成-checklist)

---

## ⚠️ Windows 必读：alembic 命令的写法

**如果你在 Windows 上，看到 `error: uv trampoline failed to canonicalize script path` 这个错误，不要慌。**

这是 `uv` 在 Windows 上的一个已知问题：当脚本路径包含空格或特殊字符时，uv 的 PEP 397 trampoline 启动器无法解析路径。

**解决办法**：本 MD 里所有 alembic 命令都用 `python -m alembic` 这种"模块调用"形式，**绕过 trampoline**：

```powershell
# ❌ Windows 上会报 trampoline 错
uv run alembic init alembic
uv run alembic revision --autogenerate -m "init"

# ✅ 通用写法（Windows / Mac / Linux 都行）
uv run python -m alembic init alembic
uv run python -m alembic revision --autogenerate -m "init"
```

**原理（一句话）**：
- `uv run alembic xxx` → 走 trampoline 启动器（Windows 上不稳）
- `uv run python -m alembic xxx` → uv 启动 Python → Python 用 `-m` 加载 alembic 模块（标准、稳）

> **本 MD 的所有 alembic 命令都已统一用 `python -m alembic` 形式。** 你直接复制粘贴就行，不用改。

---

## 0. 在开始之前：你必须建立的心智模型

**Alembic = 数据库的 Git。**


|                | Git            | Alembic                              |
| -------------- | -------------- | ------------------------------------ |
| 管理对象       | 源代码         | 数据库表结构                         |
| 一次"提交"叫啥 | commit         | revision / migration                 |
| 怎么看历史     | `git log`      | `alembic history`                    |
| 回到过去       | `git checkout` | `alembic downgrade`                  |
| 走到最新       | `git pull`     | `alembic upgrade head`               |
| 状态文件       | `.git/`        | `alembic_version` 表（存在数据库里） |
| 配置文件       | `.gitconfig`   | `alembic.ini`                        |
| 工作目录       | 仓库根         | `alembic/` + `alembic/versions/`     |

记住这一行：**Alembic 不存数据，只存"表结构怎么从版本 A 变到版本 B"的指令。**

---

## 1. 为什么要 Alembic？

### 场景对比

**没有 Alembic 的痛苦：**

```
第 1 周：手动在数据库里建了 translations 表
第 2 周：加了 model_used 字段 → 手动 ALTER TABLE
第 3 周：把 source_lang 长度从 10 改到 20 → 手动 ALTER
...
第 8 周：新人入职，小明本地跑代码 → 报错：表不存在
       小明找你：怎么建表？
       你：把那段 SQL 跑一下
       小明：哪段？
       你：emmm... 应该在群里发过...
```

**有 Alembic 的优雅：**

```
git clone 整个项目
cd backend
uv sync
uv run python -m alembic upgrade head    # 跑完所有迁移，建好所有表
python main.py                  # 启动！
```

### Alembic 解决的核心问题

1. **可重现**：任何人 clone 项目 + 跑两条命令，就能得到一模一样的数据库结构
2. **可追溯**：每次表结构变更都是一次"提交"，能看历史、能回滚
3. **可协作**：A 改了表，B 拉代码后 alembic 自动把 B 的库同步成最新
4. **可自动化**：生产环境部署时，只需要 `alembic upgrade head` 一行命令

---

## 2. 6 个核心概念（背下来）


| 概念         | 英文      | 是什么                                                  | 类比 Git         |
| ------------ | --------- | ------------------------------------------------------- | ---------------- |
| **迁移**     | Migration | 一次"建表/改表/删表"的完整动作                          | 一次 commit      |
| **修订版本** | Revision  | 一个迁移文件，文件名是一串 hash（如`a1b2c3d4_init.py`） | commit hash      |
| **当前版本** | Current   | 数据库现在处于哪个迁移                                  | HEAD             |
| **头**       | Head      | 最新的那个迁移（多个分支时指最近的祖先）                | HEAD（默认分支） |
| **升级**     | Upgrade   | 向前走一步或几步                                        | 前进             |
| **降级**     | Downgrade | 向后退一步或几步                                        | 后退             |

**还有一个会自动出现的概念：**

- **`alembic_version` 表**：Alembic 在你的数据库里自动建的"记账本"，只有一列 `version_num`，记录"当前数据库在哪个 revision"。每次 `upgrade` 都会更新这个表。

---

## 3. 准备工作：确认本项目当前状态

在开始之前，确认三件事。我们已经都准备好了，但你得**亲眼看到**：

```powershell
cd backend
uv run python -c "import alembic; print('Alembic 版本:', alembic.__version__)"
uv run python -c "import sqlmodel; print('SQLModel 版本:', sqlmodel.__version__)"
uv run python -c "from app.models.translation import Translation; print('Translation 模型已就绪')"
```

如果三个都输出版本号 / "已就绪"，继续。如果有报错，**先回 Phase 3 排查**。

> **检查清单（已经做完的事）：**
>
> - [X]  `pyproject.toml` 里有 `alembic>=1.18.4`
> - [X]  `app/core/config.py` 有 `settings.DATABASE_URL = "sqlite+aiosqlite:///./translation.db"`
> - [X]  `app/core/database.py` 导出了 `async_engine`（FastAPI 运行时用，alembic 不用它）
> - [X]  `app/models/translation.py` 定义了 `Translation(SQLModel, table=True)`

---

## 4. Step 1：`alembic init alembic` — 创建迁移骨架

### 执行命令

```powershell
cd backend
uv run python -m alembic init alembic
```

### 会发生什么

Alembic 在 `backend/` 下生成这些东西：

```
backend/
├── alembic/                    # 新建：迁移的"工作目录"
│   ├── env.py                  # 新建：迁移脚本的"运行时环境"（最复杂）
│   ├── script.py.mako          # 新建：迁移文件的"模板"（不用动）
│   ├── README                  # 新建：alembic 自带说明（可以删）
│   └── versions/               # 新建：所有迁移文件放在这里（现在是空的）
└── alembic.ini                 # 新建：alembic 的配置文件
```

### 不要慌，先看一眼

- **`alembic.ini`** — 纯文本配置，几十行
- **`alembic/env.py`** — Python 文件，控制迁移怎么跑（**我们后面主要改这个**）
- **`alembic/script.py.mako`** — 模板，新迁移文件都从这里复制
- **`alembic/versions/`** — 空目录，新建的迁移文件都会进来

### 思考题

- 为什么不直接 `git init` 一样用 `alembic init`？它跟 git init 一样吗？
  <details>
  <summary>答案</summary>
  `alembic init` 不会自动做"第一次提交"（不像 git init 后还要 git add）。它只是创建"工具和工作区"。我们要手动用 `alembic revision --autogenerate` 才会生成第一个迁移文件。
  </details>

---

## 5. Step 2：修改 `alembic.ini` — 配置数据库 URL

### 为什么

`alembic.ini` 里有一行 `sqlalchemy.url`，告诉 alembic "连哪个数据库"。Alembic 用它**只用来读出连接信息**，实际连接是在 `env.py` 里完成的（因为我们要走异步引擎）。

### 找到这行

打开 `alembic.ini`，搜索 `sqlalchemy.url`（大概在第 60-80 行之间）：

```ini
sqlalchemy.url = driver://user:pass@localhost/dbname
```

### 改成

```ini
sqlalchemy.url = sqlite:///./translation.db
```

### ⚠️ 关键细节

- 这里写的是**同步** URL：`sqlite:///`，**没有** `+aiosqlite`
- 原因：alembic 实际连接数据库时，会从 `app.core.database` 拿异步引擎，所以这一行其实**只是个占位**，保证 alembic 不报"没设置 url"的错
- 数据库文件名要和 `config.py` 里的 `DATABASE_URL` 一致（都是 `translation.db`）

### 思考题

- 为什么 alembic.ini 里写的是 `sqlite:///`，而 `config.py` 里是 `sqlite+aiosqlite:///`？两个地方不一致有问题吗？
  <details>
  <summary>答案</summary>
  没问题。因为 alembic.ini 这行我们不会真的用 — 我们会在 env.py 里**从 `settings.DATABASE_URL` 派生同步 URL**，然后 `create_engine` 一个全新的同步引擎，绕开 ini 里的 url。ini 这行写什么都不会影响实际行为，写一个能通过语法校验的值即可。
  </details>

---

## 6. Step 3：修改 `env.py` — 最关键的一步（教你看懂每一行）

打开 `alembic/env.py`，我们要做 **3 处修改**。

### 6.1 先看原文件的结构

```python
# --- 顶部：导入 ---
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# --- 中间：读取 alembic.ini 配置 ---
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# --- target_metadata：告诉 alembic 用哪个元数据对比 ---
target_metadata = None  # ← 我们要改这里

# --- 底部：两个函数 run_migrations_offline / run_migrations_online ---
```

### 6.2 修改 1 — 在顶部加导入

在 `from alembic import context` **之后**插入：

```python
# === 新增开始 ===
import sys
from pathlib import Path

# 把 backend/ 加入 Python 路径，这样 alembic 才能 `from app.xxx import yyy`
# 用 insert(0, ...) 把它放到最前面，避免和其他同名包冲突
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlmodel import SQLModel
from sqlalchemy import create_engine     # 同步引擎工厂
from sqlalchemy import pool              # 连接池配置（用 NullPool）
from app.core.config import settings     # 拿 DATABASE_URL
# 必须导入模型，模型才会"注册"到 SQLModel.metadata
from app.models.translation import Translation
# === 新增结束 ===
```

> **注意**：我们**不再 import `app.core.database` 里的 `async_engine`**——alembic 走的是同步路径，不复用异步引擎。

**为什么这么写？**

- `sys.path.insert(...)`：`alembic` 命令是在 `backend/` 目录下运行的，但 Python 默认找不到 `app/` 这个包。手动加路径让 `from app.xxx import yyy` 能工作。
- `from app.models.translation import Translation`：**这一步最关键**！如果模型没被 import，`SQLModel.metadata` 就是空的，autogenerate 就生成不出东西。

### 6.3 修改 2 — 设置 target_metadata

找到 `target_metadata = None`，改成：

```python
target_metadata = SQLModel.metadata
```

**为什么是 `SQLModel.metadata`？**

- 所有继承 `SQLModel, table=True` 的类，SQLModel 都会把它们注册到 `SQLModel.metadata`
- `metadata` 是 SQLAlchemy 的概念，存放"所有表结构信息的清单"
- Alembic 拿到这个 metadata，才能和"数据库实际状态"做对比

> 类比：你写了一份"理想户型图"（`SQLModel.metadata`），Alembic 比对"实际房子"（数据库），发现少了什么就生成"装修指令"（迁移文件）。

### 6.4 修改 3 — 修改 `run_migrations_online()` + 加 `render_item` 函数

找到原文件末尾的 `run_migrations_online()` 函数，**整段替换**为：

```python
def render_item(type_, obj, autogen_context):
    """自定义 alembic autogenerate 的类型渲染。

    SQLModel 把 AutoString、GUID 等类型包了一层（sqlmodel.sql.sqltypes.xxx），
    alembic 默认会原样写出这些类型，但不会在文件头加 `import sqlmodel`，
    运行迁移时报 NameError。

    我们把它们映射回纯 SQLAlchemy 类型，生成的迁移更干净：
        sqlmodel.sql.sqltypes.AutoString(length=10)  →  sa.String(length=10)
        sqlmodel.sql.sqltypes.GUID()                 →  sa.Uuid()
    """
    if type_ == "type":
        cls = obj.__class__
        if cls.__module__.startswith("sqlmodel.sql.sqltypes"):
            if cls.__name__ == "AutoString":
                return f"sa.String(length={obj.length})"
            if cls.__name__ == "GUID":
                return "sa.Uuid()"
    return False


def run_migrations_online() -> None:
    """使用同步引擎跑迁移（Alembic 本身是同步工具，必须配同步驱动）。"""
    # 1) 把异步 URL 里的 "+aiosqlite" 去掉，得到同步 URL
    #    例: "sqlite+aiosqlite:///./translation.db" -> "sqlite:///./translation.db"
    sync_url = settings.DATABASE_URL.replace("+aiosqlite", "")

    # 2) 单独为 alembic 创建一个全新的同步引擎
    #    - poolclass=pool.NullPool：每次连接用完即关，不进连接池（迁移脚本场景最干净）
    #    - 不复用 async_engine，因为 alembic 不在异步上下文里跑
    connectable = create_engine(sync_url, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,  # SQLite 需要：让 ALTER TABLE 重写为"新建表+拷贝"
            render_item=render_item,  # SQLModel 类型映射
        )

        with context.begin_transaction():
            context.run_migrations()
```

**⚠️ 关键原理（必须理解）：**

> **Alembic 本身是一个同步工具**。它用 `with connectable.connect() as connection:` 同步方式拿连接，调用 `context.run_migrations()` 同步跑迁移脚本。
> 所以驱动也必须是**同步**的：
> - ✅ 同步：sqlite3（pysqlite，写成 `sqlite:///...`）
> - ❌ 异步：aiosqlite（写成 `sqlite+aiosqlite:///...`）
>
> 不能把 `async_engine` 直接喂给 alembic，也不能用 `async_engine.sync_engine` 这种"伪同步"。

**为什么不用 `async_engine.sync_engine`？**

- aiosqlite 本质是异步驱动，从 `AsyncEngine` 拿出的"同步版"走的是异步驱动的同步回退路径
- 在 SQLite + alembic 场景下经常出边界问题（autogenerate 检测字段时会漏类型）
- **正确做法**：从同一个 `DATABASE_URL` 派生 sync URL，单独 `create_engine` 一个干净的同步引擎

**逐行解释：**

| 行 | 作用 |
|---|---|
| `sync_url = settings.DATABASE_URL.replace("+aiosqlite", "")` | 把异步 URL 转成同步 URL（去掉 `+aiosqlite`） |
| `connectable = create_engine(sync_url, poolclass=pool.NullPool)` | 为 alembic 单独建一个全新的同步引擎，连接用完即关 |
| `with connectable.connect() as connection` | 打开一个**同步**数据库连接 |
| `context.configure(connection=..., target_metadata=...)` | 告诉 alembic 用这个连接 + 这份元数据来工作 |
| `render_as_batch=True` | **SQLite 专属**：SQLite 的 ALTER TABLE 能力有限，加了这个参数 alembic 会用"建临时表→拷数据→改名"的方式重写表 |
| `with context.begin_transaction():` | 包在一个事务里，迁移失败能回滚 |
| `context.run_migrations()` | 真正执行迁移 |

### 6.5 完整版 env.py（参考）

替换后，env.py 的关键区域应该是这样：

```python
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# === 修改 1：新增的导入 ===
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from sqlmodel import SQLModel
from sqlalchemy import create_engine
from sqlalchemy import pool
from app.core.config import settings
from app.models.translation import Translation
# === 导入结束 ===

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# === 修改 2：target_metadata ===
target_metadata = SQLModel.metadata
# === 修改结束 ===

def run_migrations_offline() -> None:
    """离线模式（生成 SQL 脚本不连库，本项目用不到，先不管）"""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


# === 修改 3：替换 run_migrations_online ===
def run_migrations_online() -> None:
    """使用同步引擎跑迁移（Alembic 本身是同步工具）。"""
    sync_url = settings.DATABASE_URL.replace("+aiosqlite", "")
    connectable = create_engine(sync_url, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,
        )
        with context.begin_transaction():
            context.run_migrations()
# === 替换结束 ===

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

### 6.6 验证 env.py 没改坏

```powershell
uv run python -m alembic check
```

- ✅ **没有 alembic/versions/ 下的迁移文件时**，输出 `No new upgrade operations detected.` 或类似"无新操作"的消息 = 配置正确
- ❌ 如果报 `ModuleNotFoundError: No module named 'app'` → 检查 `sys.path.insert` 那一行
- ❌ 如果报 `AttributeError: ... has no attribute 'sync_engine'` → 你的 SQLAlchemy 版本太老，升到 2.0+ 即可

---

## 7. Step 4：生成第一次迁移（autogenerate）

### 执行命令

```powershell
uv run python -m alembic revision --autogenerate -m "init translations table"
```

### 拆解这个命令


| 部分                           | 含义                                 |
| ------------------------------ | ------------------------------------ |
| `alembic revision`             | 创建一个新的修订版本                 |
| `--autogenerate`               | 自动生成（对比模型 vs 数据库）       |
| `-m "init translations table"` | 给这次迁移起个名字（commit message） |

### 发生了什么（黑盒拆开看）

1. Alembic 启动，import 了 `app.models.translation.Translation`
2. SQLModel 把这个类注册到 `SQLModel.metadata`
3. Alembic 连接到 `translation.db`（现在还没有任何表）
4. 读取数据库当前所有表（结果：空）
5. 对比 `SQLModel.metadata` 里的表（结果：1 个 `translations`）
6. 算出差异："需要创建 translations 表"
7. 在 `alembic/versions/` 下生成一个新文件

### 看一眼生成的文件

`alembic/versions/` 里会多一个类似 `a1b2c3d4_init_translations_table.py` 的文件。打开它：

```python
"""init translations table

Revision ID: a1b2c3d4e5f6
Revises:
Create Date: 2026-06-07 ...

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
import sqlmodel

revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'translations',
        sa.Column('id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column('source_text', sa.Text(), nullable=False),
        sa.Column('source_lang', sqlmodel.sql.sqltypes.AutoString(length=10), nullable=False),
        # ... 其他列 ...
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('translations')
```

**重点看 3 个东西：**

1. **`revision` / `down_revision`**：版本链。`down_revision = None` 表示这是第一个
2. **`upgrade()`**：向前走要做什么（建表）
3. **`downgrade()`**：向后回退要做什么（删表）— 这就是版本控制

> ⚠️ **永远要在执行迁移前读一遍 autogenerate 生成的文件！**
> 有时候它漏字段、有时候它猜错类型、有时候它加了你不要的索引。
> 看到不认识的就去 SQLModel 文档查一下。

### 思考题

- 如果你改了 `translation.py` 加了一个字段，但忘了 `alembic revision --autogenerate`，数据库会怎样？
  <details>
  <summary>答案</summary>
  数据库完全不知道。代码里模型说有这个字段，但数据库里没这列，运行时就会报 `OperationalError: no such column: xxx`。
  </details>

---

## 8. Step 5：执行迁移，建表

```powershell
uv run python -m alembic upgrade head
```

### 拆解

- `upgrade`：向前走
- `head`：走到"头"（最新版本）

输出应该类似：

```
INFO  [alembic.runtime.migration] Context impl SQLiteImpl.
INFO  [alembic.runtime.migration] Will assume non-transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> a1b2c3d4e5f6, init translations table
```

### 背后做了什么

1. 连数据库
2. 检查 `alembic_version` 表（不存在就创建）
3. 看 `alembic_version` 当前记录的版本号（空 = 第一次）
4. 看 `head` 指向哪个文件（刚生成的 `a1b2c3d4...`）
5. 从"当前"跑到"head"：执行 `upgrade()` 里的 SQL
6. 把 `alembic_version.version_num` 改成 `a1b2c3d4e5f6`

### 跑完去看一眼

```powershell
ls backend/
# 应该能看到：translation.db  ← 新出现的！
```

---

## 9. Step 6：验证表真的建好了

### 方式 1：直接看 SQLite 文件

```powershell
uv run python -c "
import sqlite3
conn = sqlite3.connect('translation.db')
for row in conn.execute(\"SELECT name FROM sqlite_master WHERE type='table'\"):
    print('表:', row[0])
conn.close()
"
```

应该看到：

```
表: translations
表: alembic_version
```

### 方式 2：看 translations 表的列结构

```powershell
uv run python -c "
import sqlite3
conn = sqlite3.connect('translation.db')
for row in conn.execute('PRAGMA table_info(translations)'):
    print(row)
conn.close()
"
```

应该看到所有 11 个字段（id, source_text, source_lang, ...）。

### 方式 3：用 SQLAlchemy（更工程化）

```powershell
uv run python -c "
from app.core.database import async_engine
from sqlalchemy import text
import asyncio

async def check():
    async with async_engine.connect() as conn:
        result = await conn.execute(text(\"SELECT name FROM sqlite_master WHERE type='table'\"))
        for row in result:
            print('表:', row[0])

asyncio.run(check())
"
```

---

## 10. 未来的工作流：3 步循环（最重要）

**Alembic 一旦配好，你 99% 的时间都在重复这个循环：**

```
┌──────────────────────────────────────┐
│ 1. 改 model：                        │
│    app/models/translation.py 加字段  │
└──────────────┬───────────────────────┘
               ↓
┌──────────────────────────────────────┐
│ 2. 让 alembic 检测：                  │
│    uv run python -m alembic revision           │
│      --autogenerate -m "加xxx字段"    │
│    → 看一下生成的迁移文件对不对        │
└──────────────┬───────────────────────┘
               ↓
┌──────────────────────────────────────┐
│ 3. 应用迁移：                        │
│    uv run python -m alembic upgrade head       │
└──────────────────────────────────────┘
```

**举例：我们要给 Translation 加一个 `status` 字段**

```python
# 1. 改 model
class Translation(SQLModel, table=True):
    # ... 原有字段 ...
    status: str = Field(default="pending", max_length=20)  # 新增
```

```bash
# 2. 生成迁移
uv run python -m alembic revision --autogenerate -m "add status field"
# 检查 alembic/versions/ 下的新文件，upgrade() 应该有 add_column
```

```bash
# 3. 应用
uv run python -m alembic upgrade head
```

**搞定了。** 数据库已经更新，本地不用手动改任何东西，部署到生产也只跑一行命令。

### ⚠️ 三条铁律

1. **改 model 必改 alembic** — 不然代码和数据库会脱节
2. **必看生成的迁移文件** — autogenerate 不是 100% 准确
3. **必提交到 git** — `alembic/versions/` 下的文件必须 commit，否则别人拉了代码也跑不起来

---

## 11. 常用命令清单（速查）

```powershell
# === 看状态 ===
uv run python -m alembic current              # 当前数据库是哪个版本
uv run python -m alembic history              # 所有迁移历史（倒序）
uv run python -m alembic history --verbose    # 带详细描述

# === 生成迁移 ===
uv run python -m alembic revision -m "msg"                     # 手动写（空 upgrade/downgrade）
uv run python -m alembic revision --autogenerate -m "msg"      # 自动检测差异

# === 执行迁移 ===
uv run python -m alembic upgrade head         # 走到最新
uv run python -m alembic upgrade +1           # 向前走一步
uv run python -m alembic upgrade a1b2c3d      # 走到指定版本

# === 回退 ===
uv run python -m alembic downgrade -1         # 向后退一步
uv run python -m alembic downgrade base       # 回到最初（删所有表！）
uv run python -m alembic downgrade a1b2c3d    # 回到指定版本

# === 工具 ===
uv run python -m alembic check                # 检查模型和数据库是否一致
uv run python -m alembic stamp head           # 不跑迁移，只把版本号改成 head（慎用）
uv run python -m alembic show a1b2c3d         # 显示某个版本的详情
```

### 记忆口诀

- `upgrade` = 向前 = "升级"数据库到新版本
- `downgrade` = 向后 = "降级"到旧版本
- `head` = 最新 = "头"是新的（头在最上面）
- `base` = 最初 = "基"是最早的

---

## 12. 常见坑（提前预警）

### 坑 1：autogenerate 漏字段

**症状**：改了 model 里的字段，运行 `alembic revision --autogenerate`，生成的 upgrade() 居然是空的。

**原因**：可能你的模型没有被 import 到 `env.py` 里。

**解决**：

```python
# env.py 里必须有这一行（或类似的多行）
from app.models.translation import Translation
```

没有 import，SQLModel.metadata 就是空的。

### 坑 2：改了 model 但忘跑 alembic

**症状**：跑代码报 `sqlalchemy.exc.OperationalError: no such column: xxx`。

**解决**：跑 `alembic revision --autogenerate -m "..."` → 检查 → `alembic upgrade head`。

### 坑 3：两个人同时改了 model 并 commit

**症状**：pull 代码后跑 `alembic upgrade head` 报"找不到上一步的版本"。

**解决**：两个迁移文件 `down_revision` 都指向同一个父版本，形成"分支" → 用 `alembic merge` 合并（高阶话题，以后再说）。

### 坑 4：SQLite 上 ALTER TABLE 失败

**症状**：用 alembic 改字段类型时 SQLite 报错。

**解决**：我们已经在 `env.py` 里加了 `render_as_batch=True`，alembic 会自动用"建临时表→拷数据"的方式绕过 SQLite 的限制。

### 坑 5：误操作 downgrade base 把数据删了

**症状**：`alembic downgrade base` 之后所有表都没了。

**预防**：

- 生产环境**永远不要** `downgrade`
- 本地玩玩无所谓，重要的数据先备份
- `alembic_version` 表的 `version_num` 也能告诉你"现在在哪"

### 坑 6：env.py 里路径错

**症状**：`ModuleNotFoundError: No module named 'app'`

**解决**：检查 `sys.path.insert(0, str(Path(__file__).resolve().parent.parent))` 这一行。

- `__file__` 是 `alembic/env.py`
- `.parent` 是 `alembic/`
- `.parent.parent` 是 `backend/`（app/ 所在目录）✅

### 坑 7：把 async_engine 喂给 Alembic（或用 async_engine.sync_engine）

**症状**：
- `alembic check` 跑着跑着报奇怪错（甚至 hang 住）
- `alembic revision --autogenerate` 漏字段、漏类型
- 日志里 `aiosqlite` 相关的警告

**根因**：Alembic 本身是**同步工具**，必须配**同步驱动**（`sqlite` 而不是 `sqlite+aiosqlite`）。

**错示范**：

```python
# ❌ 把异步引擎直接给 alembic（async 上下文，alembic 不认识）
from app.core.database import async_engine
connectable = async_engine  # 错！

# ❌ 用 sync_engine 拿"伪同步"（走 aiosqlite 同步回退，SQLite 上有 bug）
connectable = async_engine.sync_engine  # 错！
```

**正确做法**：

```python
# ✅ 从 async URL 派生 sync URL，单独建全新的同步引擎
from sqlalchemy import create_engine
sync_url = settings.DATABASE_URL.replace("+aiosqlite", "")  # 去掉异步标记
connectable = create_engine(sync_url, poolclass=pool.NullPool)
```

**记忆口诀**：
- alembic = 同步工具 → 必须用同步驱动 → `sqlite` / `pysqlite` / `psycopg2` / `pymysql`
- 异步驱动（`aiosqlite` / `asyncpg` / `aiomysql`）只在 FastAPI 运行时使用
- 这两套**互不通用**，配置两套 URL（一个带 `+ai...`，一个不带）

### 坑 8：Windows 上 `uv run alembic` 报 "trampoline failed to canonicalize"

**症状**：
```
$ uv run alembic init alembic
error: uv trampoline failed to canonicalize script path
```

**根因**：uv 在 Windows 上用 PEP 457 "trampoline" 启动器来跑 venv 里的脚本。当路径含空格或特殊字符（如 `C:\Users\Administrator\Desktop\...`）时，trampoline 解析路径失败。

**解决**：永远用 `python -m alembic` 模块调用形式：

```powershell
# ❌ 别这么写（Windows 上必报）
uv run alembic init alembic
uv run alembic revision --autogenerate -m "..."

# ✅ 这么写（跨平台都稳）
uv run python -m alembic init alembic
uv run python -m alembic revision --autogenerate -m "..."
```

**原理**：
- `uv run alembic xxx` → uv 调 trampoline 启动器 → 路径解析失败 ❌
- `uv run python -m alembic xxx` → uv 调 Python → Python 加载模块 → 标准稳定 ✅

> 本 MD 的所有 alembic 命令都已是模块调用形式，照抄即可。

### 坑 9：autogenerate 生成的迁移里 `NameError: name 'sqlmodel' is not defined`

**症状**：

```powershell
$ uv run python -m alembic upgrade head
...
File ".../alembic/versions/xxxx_init_translations_table.py", line 27, in upgrade
    sa.Column('source_lang', sqlmodel.sql.sqltypes.AutoString(length=10), nullable=False),
                             ^^^^^^^^
NameError: name 'sqlmodel' is not defined
```

**根因**：SQLModel 把 `AutoString`、`GUID` 等类型包了一层（`sqlmodel.sql.sqltypes.xxx`），alembic autogenerate 会原样输出这种类型写法，**但不会**在文件头加 `import sqlmodel`。

**解决**（永久方案）：在 env.py 里加一个 `render_item` 函数，把 SQLModel 类型映射回纯 SQLAlchemy 类型，让生成的迁移更干净：

```python
# === 在 env.py 里加这个函数 ===
def render_item(type_, obj, autogen_context):
    """自定义 alembic autogenerate 的类型渲染。"""
    if type_ == "type":
        cls = obj.__class__
        if cls.__module__.startswith("sqlmodel.sql.sqltypes"):
            if cls.__name__ == "AutoString":
                return f"sa.String(length={obj.length})"
            if cls.__name__ == "GUID":
                return "sa.Uuid()"
    return False
```

然后在 `run_migrations_online()` 的 `context.configure(...)` 里加上：

```python
context.configure(
    connection=connection,
    target_metadata=target_metadata,
    render_as_batch=True,
    render_item=render_item,  # <-- 这一行
)
```

**效果**：

```python
# 之前（错）
sa.Column('source_lang', sqlmodel.sql.sqltypes.AutoString(length=10), nullable=False),

# 之后（对）
sa.Column('source_lang', sa.String(length=10), nullable=False),
```

**临时补救**（如果已经生成了错的迁移）：在迁移文件头手动加一行 `import sqlmodel`：

```python
from alembic import op
import sqlalchemy as sa
import sqlmodel  # <-- 手动加这行
```

**记忆口诀**：
- 用 SQLModel 一定要加 `render_item`，不然 autogenerate 出的文件一定跑不动
- 临时办法是手动加 `import sqlmodel`，永久办法是加 `render_item`

---

## 13. 如果你只记 3 件事

1. **Alembic = 数据库的 Git**：表结构变更要"提交"，才能追溯和共享
2. **改 model 必跑 alembic**：3 步循环（改 → autogenerate → upgrade）
3. **`SQLModel.metadata` 是入口**：env.py 里必须正确指向它，autogenerate 才能工作

---

## 14. 完成检查清单

跑完所有步骤后，逐项打勾：

- [ ]  `backend/alembic/` 目录存在
- [ ]  `backend/alembic.ini` 文件存在
- [ ]  `alembic.ini` 里 `sqlalchemy.url = sqlite:///./translation.db`
- [ ]  `alembic/env.py` 顶部有 `sys.path.insert` 和模型 import
- [ ]  `alembic/env.py` 里 `target_metadata = SQLModel.metadata`
- [ ]  `alembic/env.py` 里 `run_migrations_online()` 用 `create_engine(sync_url, poolclass=pool.NullPool)`（**独立同步引擎**，不复用 async_engine）
- [ ]  `alembic/env.py` 里 `render_as_batch=True`
- [ ]  `alembic/env.py` 里有 `render_item` 函数（防 SQLModel 类型的 `NameError`）
- [ ]  `alembic/env.py` 的 `context.configure(...)` 里传了 `render_item=render_item`
- [ ]  `uv run python -m alembic check` 不报错
- [ ]  `alembic/versions/` 下有第一个迁移文件
- [ ]  打开迁移文件看 `upgrade()` 包含 `op.create_table('translations', ...)`
- [ ]  `uv run python -m alembic upgrade head` 成功
- [ ]  `translation.db` 文件出现在 `backend/`
- [ ]  查表能看到 `translations` 和 `alembic_version` 两张表
- [ ]  `uv run python -m alembic current` 能显示当前版本号

---

**好，文档到此为止。准备好跟着 Phase3 MD 的 Step 3.2 一步步操作了。如果某一步卡住，把报错贴给我。**
