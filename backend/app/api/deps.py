from typing import Annotated

from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_async_session

# 把「依赖注入的 AsyncSession」抽成一个类型别名
# 路由函数里写 session: SessionDep 就等价于：
#   session: AsyncSession = Depends(get_async_session)
# 这样多个路由文件复用同一份声明，也方便以后统一换实现
SessionDep = Annotated[AsyncSession, Depends(get_async_session)]
