# Alembic 数据库迁移完全指南

> 这份文档是为本项目（AI 在线翻译）量身定制的，配套 `Phase3.5_Alembic完全指南.md` 一起看。读完本文你能回答：迁移是什么、为什么必须用、它在我们项目里扮演什么角色。

---

## 一句话回答：在项目构建中很重要吗？

**非常重要——它是项目从"玩具"变成"产品"的分水岭。**

没有迁移：
- 你改了 `Translation` 加个字段，**每个开发者的本地数据库都坏了**——必须删库重建
- 上线的时候**没有任何机制把新表结构同步到生产数据库**
- 团队协作时，**谁的数据库是最新状态？鬼知道**

有迁移：
- `git pull` → 跑一行命令 → 数据库自动同步到最新
- 上线时 `alembic upgrade head` 一行命令搞定
- 每次改表都有 Git 历史，**可以回滚**

---

## 一、什么是数据库迁移（Migration）？

### 1.1 没有迁移的日常（你肯定经历过）

```python
# Phase 3 写好模型
class Translation(SQLModel, table=True):
    id: UUID
    source_text: str
    translated_text: str | None
    # ...

# 跑一下，建表成功
# → translation.db 里有 translations 表了
```

第二天加个字段：
```python
class Translation(SQLModel, table=True):
    id: UUID
    source_text: str
    translated_text: str | None
    status: str = "success"  # ← 新加的
    # ...
```

**重新跑代码会怎样？**
- **不会**自动加字段
- 表还是老结构
- 插入带 status 的数据 → `OperationalError: no such column: status`

**怎么办？**
- 删 `translation.db` → 重建 → **数据全没了**
- 或者手动连数据库执行 `ALTER TABLE` → **不可持续**

这就是"没有迁移"的开发体验：**改一次表，删一次库**。

### 1.2 有了迁移的日常

```bash
# 1. 改完模型后
uv run alembic revision --autogenerate -m "add status field"

# 2. 看一眼生成的迁移文件（确认 SQL 正确）
# 文件在 alembic/versions/xxxxxx_add_status_field.py

# 3. 应用到数据库
uv run alembic upgrade head
```

**3 行命令，表结构自动更新。**

下次别人 `git pull`：
```bash
uv run alembic upgrade head
```
**他的数据库也同步了。**

---

## 二、Alembic 是什么？

> 官方定义：Alembic is a lightweight database migration tool for usage with SQLAlchemy.

**翻译**：Alembic 是 SQLAlchemy 官方出品的数据库迁移工具。

我们项目用 SQLModel（基于 SQLAlchemy），所以天然用 Alembic。

### 2.1 三个核心概念

| 概念 | 作用 | 现实比喻 |
|------|------|---------|
| **Migration Script（迁移脚本）** | 一个 Python 文件，记录"从 A 状态到 B 状态要执行什么 SQL" | 一张施工图纸 |
| **Revision ID（版本号）** | 每个迁移脚本的唯一标识（哈希字符串） | 施工图纸的编号 |
| **alembic_version 表** | 数据库里的一张表，记录"当前数据库运行到哪个版本了" | 工地门口的进度牌 |

### 2.2 关键工作流

```
改 SQLModel 模型
       ↓
alembic revision --autogenerate  ← 自动对比"模型"和"数据库"，生成迁移脚本
       ↓
人工 review 迁移脚本（autogenerate 不是 100% 准的）
       ↓
alembic upgrade head  ← 执行迁移，更新数据库
       ↓
git add alembic/versions/  ← 把迁移脚本提交到 Git
```

---

## 三、在我们项目里的具体应用

### 3.1 项目里的 3 个迁移文件

```bash
backend/alembic/versions/
├── 11065b6dc19f_init_translations_table.py   # Phase 3：建初始表
└── 93d4226949a7_add_status_field_to_translations.py  # Phase 8.1：加 status 字段
```

**每个文件都是一个 Git 提交里的"不可变历史"**——一旦 merge 到主分支，就**不要修改**了。

### 3.2 一个迁移文件长什么样？

刚才 Phase 8.1 加 `status` 字段生成的迁移：

```python
"""add status field to translations

Revision ID: 93d4226949a7
Revises: 11065b6dc19f   ← 上一个版本号
Create Date: 2026-06-09 17:26:59.241402

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '93d4226949a7'
down_revision: Union[str, Sequence[str], None] = '11065b6dc19f'  # 链向上一版本


def upgrade() -> None:
    """Upgrade schema. — 升级时执行的 SQL"""
    # SQLite 不支持直接加 NOT NULL 列
    with op.batch_alter_table('translations', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('status', sa.String(length=20), nullable=True, server_default='success')
        )
    with op.batch_alter_table('translations', schema=None) as batch_op:
        batch_op.alter_column('status', nullable=False, server_default='success')


def downgrade() -> None:
    """Downgrade schema. — 回滚时执行的 SQL（一般不写，但写了能救命）"""
    with op.batch_alter_table('translations', schema=None) as batch_op:
        batch_op.drop_column('status')
```

**两个函数**：
- `upgrade()`：从老版本升级到这版本要做什么
- `downgrade()`：从这版本回滚到老版本要做什么（**强烈建议每次都写**，灾难时救命）

### 3.3 关键命令速查

```bash
# 生成迁移（自动对比模型 vs 数据库）
uv run alembic revision --autogenerate -m "描述改了什么"

# 应用所有未执行的迁移
uv run alembic upgrade head

# 回滚一个版本
uv run alembic downgrade -1

# 看当前数据库版本
uv run alembic current

# 看所有迁移历史
uv run alembic history

# 跑到指定版本
uv run alembic upgrade 93d4226949a7
```

### 3.4 一个完整的开发循环

```bash
# 1. 改模型
vim app/models/translation.py   # 加个字段

# 2. 生成迁移
uv run alembic revision --autogenerate -m "add xxx field"

# 3. 看一眼迁移文件！  ← 容易忘，但很重要
cat alembic/versions/xxxxx_add_xxx_field.py

# 4. 应用迁移
uv run alembic upgrade head

# 5. 验证模型能用
uv run python -c "from app.models.translation import Translation; print(Translation.xxx)"

# 6. 提交代码（迁移文件必须提交）
git add app/models/translation.py alembic/versions/xxxxx_add_xxx_field.py
git commit -m "feat: add xxx field to translation"
```

---

## 四、踩过的坑（本项目真实经验）

### 坑 1：SQLite 不能直接加 NOT NULL 列

**症状**：
```
sqlalchemy.exc.OperationalError: Cannot add a NOT NULL column with default value NULL
```

**原因**：SQLite 旧版本限制——加 NOT NULL 列时必须有"已有行的值"，不能依赖 server_default。

**解决**：分两步——先加可空 + server_default，再 alter 改成 NOT NULL：
```python
# 第一步：加可空 + 默认值（已有行自动填 'success'）
batch_op.add_column(sa.Column('status', sa.String(20), nullable=True, server_default='success'))

# 第二步：把可空改成非空（数据已经填好了）
batch_op.alter_column('status', nullable=False, server_default='success')
```

**为什么 PG/MySQL 不需要这样**：它们原生支持加 NOT NULL 列并填默认值。

### 坑 2：autogenerate 不是 100% 准确

**autogenerate 会漏的**：
- 列重命名（它会生成"删列 + 加列"，丢失数据）
- 数据迁移（只是改表结构，不会动数据）
- 复杂约束变更

**autogenerate 会误报的**：
- 字段类型在 SQLAlchemy 内部表示有差异时
- 枚举类型

**所以第 3 步"看一眼迁移文件"绝对不能省**。

### 坑 3：删表后迁移状态混乱

**症状**：`translation.db` 删了重建，但 `alembic_version` 表认为还在老版本。

**解决**：
```bash
# 标记数据库为最新版本（不实际执行迁移）
uv run alembic stamp head
```

**什么时候用**：
- 删库重建后
- 从别处导入数据后想跳过迁移
- 测试环境想直接 reset

---

## 五、迁移在团队协作中的价值

### 场景 A：新同事加入项目

```bash
git clone https://github.com/xxx/translate.git
cd backend
uv sync
uv run alembic upgrade head   # ← 数据库自动到最新
uv run uvicorn app.main:app --reload
```

**没有迁移的话**：新同事得手动连数据库，按老同事口述"先建个表，再加这个字段"操作 30 分钟。

### 场景 B：生产环境部署

```bash
# 在服务器上
git pull origin main
uv sync
uv run alembic upgrade head   # ← 关键这一行
systemctl restart uvicorn
```

**没有迁移的话**：DBA 手动跑 SQL，**有任何一个字段忘了就 500 报错**。

### 场景 C：线上出 bug，要回滚

```bash
uv run alembic downgrade -1   # ← 回滚一个版本
```

**没有迁移的话**："先备份数据库，再手动改表结构，再改代码，再部署"——可能 1 小时。

---

## 六、最佳实践（建议作为团队规范）

| 规范 | 原因 |
|------|------|
| 每次改 model 必须同时改迁移 | 单一来源（Git） |
| 迁移脚本必须**写完整**的 `downgrade()` | 灾难回滚用得上 |
| 迁移脚本**不要回头修改**已合并的版本 | 一旦其他同事 apply 了，改了会冲突 |
| 改 schema 的 PR 单独提 | 方便 review 和回滚 |
| 长文本描述写在 docstring 顶部 | `revision --autogenerate -m "短描述"` 不够时补充 |
| 大数据量表加字段分批执行 | 1000 万行的表 `ALTER TABLE` 可能锁表几小时 |

---

## 七、我们项目还可以怎么用 Alembic

### 7.1 数据迁移（Data Migration）

`status` 字段加了 `server_default='success'`，**新插入的行自动是 success**。
**但已经有 5 行老数据**——它们的 status 是 `server_default` 填的 'success'，也是正确的。

但如果以后想"给所有 status=success 的记录加个 is_archived=False 字段"——这就是数据迁移：
```python
def upgrade() -> None:
    # 1. 加列
    op.add_column('translations', sa.Column('is_archived', sa.Boolean, default=False))
    
    # 2. 数据迁移
    op.execute("UPDATE translations SET is_archived = false")
```

### 7.2 种子数据

新装的数据库想塞点测试数据，可以做个迁移：
```python
def upgrade() -> None:
    op.execute("""
        INSERT INTO translations (id, source_text, source_lang, target_lang, translated_text, status)
        VALUES
        ('00000000-0000-0000-0000-000000000001', 'Hello', 'en', 'zh-CN', '你好', 'success')
    """)
```

---

## 八、一句话总结

> **Alembic = 数据库的 Git**。
> 代码改了什么，迁移文件就记录什么，数据库永远是"和当前代码匹配"的状态。

对于你这个项目：
- 单人开发：迁移让你的"改 schema → 重新跑"流程变得无痛
- 上线 / 部署：迁移是**唯一可靠**的数据库同步方式
- 团队协作：迁移让"谁的数据库是最新的"不再是问题

**重要程度：⭐⭐⭐⭐⭐（满分 5 星）**

不学可以，但只要你想认真做项目，**必须学**。我们 Phase 3 已经让你跑过一遍完整流程了，再回头看本文应该会有"哦原来是这样"的体感。
