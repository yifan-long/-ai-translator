from sqlmodel import SQLModel, Field
from fastapi import APIRouter, Query
from app.services import history, translator
from app.models.translation import Translation
from app.api.deps import SessionDep

router = APIRouter()


class TranslateRequest(SQLModel):
    source_text: str = Field(min_length=1)  # 至少 1 个字符，防止空串
    source_lang: str
    target_lang: str


# ============ POST /translate ============
@router.post("/translate", response_model=Translation)
async def translate(payload: TranslateRequest, session: SessionDep) -> Translation:
    """
    翻译接口：
    1. 调翻译服务拿译文（失败也不抛异常，而是写库标记为 failed）
    2. 把「原文 + 译文 + 元信息」存进数据库
    3. 返回完整记录（含自动生成的 id、created_at 等）
    """
    # 1) 调 LLM 翻译（耗时操作，async 等）
    # 失败不抛：把异常吞掉，写一条 status="failed" 的记录，方便前端展示
    try:
        translated_text = await translator.translate_text(
            payload.source_text,
            payload.source_lang,
            payload.target_lang,
        )
        status = "success"
    except Exception as e:
        # TODO: 失败原因写日志（Phase 8 之后接 logging）
        print(f"[translate] 翻译失败: {e!r}")
        translated_text = None
        status = "failed"

    # 2) 写入数据库
    record = await history.create_translation(
        session,
        source_text=payload.source_text,
        source_lang=payload.source_lang,
        target_lang=payload.target_lang,
        translated_text=translated_text,
        model_used="deepseek-chat",  # 记录用了哪个模型
        status=status,
    )

    # 3) 返回 DB 记录
    return record


# ============ GET /languages ============
# 硬编码 10 种常用语言；后续要加只需改这里
SUPPORTED_LANGUAGES = [
    {"code": "en",    "name": "English"},
    {"code": "zh-CN", "name": "Chinese (Simplified)"},
    {"code": "ja",    "name": "Japanese"},
    {"code": "ko",    "name": "Korean"},
    {"code": "fr",    "name": "French"},
    {"code": "de",    "name": "German"},
    {"code": "es",    "name": "Spanish"},
    {"code": "pt",    "name": "Portuguese"},
    {"code": "ru",    "name": "Russian"},
    {"code": "ar",    "name": "Arabic"},
]


@router.get("/languages")
async def list_languages() -> dict:
    """返回支持的语言列表（前端下拉框用）"""
    return {"languages": SUPPORTED_LANGUAGES}





