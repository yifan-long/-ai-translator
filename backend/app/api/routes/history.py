from fastapi import APIRouter
from app.services import history
from app.models.translation import Translation
from app.api.deps import SessionDep
from typing import Annotated
from fastapi import Query, Response
from uuid import UUID
from sqlmodel import SQLModel
from fastapi import HTTPException



router = APIRouter()

class HistoryResponse(SQLModel):
    items: list[Translation]
    total: int

@router.get("/history", response_model=HistoryResponse)
async def get_history(
    session: SessionDep,
    page: Annotated[int, Query( ge=1, description="页码，默认第一页")] = 1,
    page_size: Annotated[int, Query( ge=1, description="每页数量，默认 10 条")] = 10,
) -> HistoryResponse:
    """
    获取翻译记录列表
    """
    items, total= await history.list_translations(
        session,
        page=page,
        page_size=page_size,
    )
    return HistoryResponse(
        items=items,
        total=total,
    )



@router.get("/history/{id}", response_model=Translation)
async def get_translation(
    session: SessionDep,
    id: UUID,
) -> Translation | None: 
    """
    根据 ID 获取翻译记录
    """
    record = await history.get_translation(
        session,
        id,
    )
    if not record:
        raise HTTPException(status_code=404, detail="翻译记录不存在")
    return record


@router.delete("/history/{id}")
async def delete_translation(
    session: SessionDep,
    id: UUID,
) -> Response:
    """
    根据 ID 删除翻译记录
    """
    record = await history.get_translation(
        session,
        id,
    )
    if not record:
        raise HTTPException(status_code=404, detail="翻译记录不存在")
    await history.delete_translation(
        session,
        id,
    )
    return Response(status_code=204)

