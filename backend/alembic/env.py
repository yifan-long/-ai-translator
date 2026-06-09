from logging.config import fileConfig

from sqlalchemy import engine_from_config, create_engine
from sqlalchemy import pool

from alembic import context


import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from sqlmodel import SQLModel
from app.core.config import settings
from app.models.translation import Translation

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = SQLModel.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_item=render_item,
    )

    with context.begin_transaction():
        context.run_migrations()


def render_item(type_, obj, autogen_context):
    """自定义 alembic autogenerate 的类型渲染。

    SQLModel 把 AutoString、GUID 等类型包了一层（sqlmodel.sql.sqltypes.xxx），
    alembic 默认会把它们写成 `sqlmodel.sql.sqltypes.AutoString(length=10)`，
    但不会在文件头加 `import sqlmodel`，运行时报 NameError。

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
    """使用同步引擎跑迁移（Alembic 不支持异步驱动）。"""
    # 把异步 URL 转成同步 URL（去掉 +aiosqlite）
    sync_url = settings.DATABASE_URL.replace("+aiosqlite", "")
    connectable = create_engine(sync_url, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,  # SQLite 需要：让 ALTER TABLE 重写为"新建表+拷贝"
            render_item=render_item,
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
