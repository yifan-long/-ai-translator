from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.translation import Translation
from datetime import datetime
from uuid import UUID
from sqlmodel import select, func, col

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
    status: str = "success",
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
        status=status,
    ) # type: ignore
    session.add(translation)
    await session.commit()
    await session.refresh(translation)  # 拉回 DB 生成的 id、created_at、updated_at
    return translation


async def get_translation(
    session: AsyncSession,
    id: UUID,
) -> Translation | None:
    """根据 ID 获取翻译记录。"""
    return await session.get(Translation, id)

async def list_translations(
        session: AsyncSession,
        page: int = 1,
        page_size: int = 20,
) -> tuple[list[Translation], int]:
    # SQLModel AsyncSession 用 execute() + scalars() 代替 exec()
    count_stmt = select(func.count()).select_from(Translation)
    total = (await session.execute(count_stmt)).scalar_one()

    # 查当页数据，按创建时间倒序
    offset = (page - 1) * page_size
    stmt = (
        select(Translation)
        .order_by(col(Translation.created_at).desc())
        .offset(offset)
        .limit(page_size)
    )
    result = await session.execute(stmt)
    items = list(result.scalars().all())
    return items, total




async def delete_translation(session: AsyncSession, id: UUID) -> bool:
    """删除一条记录；返回是否真的删了。"""
    translation = await session.get(Translation, id)
    if translation is None:
        return False  # 没找到，不删
    await session.delete(translation)
    await session.commit()
    return True
    
