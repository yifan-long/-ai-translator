
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from app.core.config import settings



from langchain.chat_models import init_chat_model

model = init_chat_model(
                            model = settings.OPENAI_API_VERSION,
                            api_key=settings.OPENAI_API_KEY,
                            base_url=settings.OPENAI_API_BASE,
                            temperature=0,  # 翻译任务用 0 最稳定
                            max_tokens = 1024,
                            timeout = 30
                        )

prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are a professional translator. "
        "Translate the following text from {source_lang} to {target_lang}. "
        "Output ONLY the translated text, with no explanations, quotes, or extra content.",
    ),
    ("human", "{source_text}"),
])

chain = prompt | model | StrOutputParser()

async def translate_text(
        source_text: str,
        source_lang: str,
        target_lang: str,
    ) -> str: # type: ignore
    result = await chain.ainvoke({
        "source_text": source_text,
        "source_lang": source_lang,
        "target_lang": target_lang,
    })
    return result
