# Phase 5：LangChain 翻译服务

## 一、本 Phase 目标

创建一个翻译服务模块，用 LangChain 对接 AI 模型（DeepSeek），实现文本翻译功能。

## 二、最终效果

在 Python 中能这样调用：

```python
result = await translate_text("Hello world", "English", "Chinese")
print(result)  # "你好，世界"
```

返回纯文本，不要解释、不要额外内容。

---

## 三、需要理解的关键概念

### 3.1 LangChain 是什么？

LangChain 是一个 AI 应用开发框架，它把调用 AI 的流程标准化了。核心概念有三个：

**① ChatModel（聊天模型）**
封装对 AI 模型的 API 调用。我们用的是 `ChatOpenAI`，虽然对接的是 DeepSeek，但因为 DeepSeek 兼容 OpenAI 的 API 格式，所以可以直接用。

**② PromptTemplate（提示词模板）**
把用户输入的变量（如源文本、源语言、目标语言）填充到固定的提示词模板中。

**③ Chain（链）**
把「模板 → 模型 → 输出解析」串联成一个管道。

```
prompt_template → ChatOpenAI → StrOutputParser
       ↓              ↓              ↓
  填充变量       调用 API       提取文本
```

### 3.2 为什么用 StrOutputParser？

`ChatOpenAI` 返回的是一个 `AIMessage` 对象，而我们只需要其中的文本内容。`StrOutputParser` 的作用就是从 `AIMessage` 中提取出纯文本字符串。

### 3.3 sync 还是 async？

用户请求是异步的（FastAPI 异步处理），所以翻译函数也应该是 `async` 的，用 `ainvoke()` 而不是 `invoke()`。

> 小知识：`a` 前缀代表 `async`，`ainvoke` = async invoke。

### 3.4 DeepSeek 的配置在哪？

在 `core/config.py` 里已经配好了三个关键信息：
- `OPENAI_API_KEY` — API 密钥
- `OPENAI_API_BASE` — 接口地址（`https://api.deepseek.com/v1`）
- `OPENAI_API_VERSION` — 模型名（`deepseek-chat`）

---

## 四、实现步骤

### 步骤 5.1：先写 mock 版本（你做）

**谁做：** 你

**做什么：** 先不要连真实 API，写一个 mock 版本的翻译函数，返回固定的模拟结果。

**为什么先 mock？**
- 确保翻译服务的接口设计是正确的
- 后续写路由时可以独立测试，不受网络/API Key 影响
- 等路由全部调通后，再换成真实模型

**文件位置：** `app/services/translator.py`

**mock 版本的核心思路：**

只是一个 async 函数：
```python
async def translate_text(source_text: str, source_lang: str, target_lang: str) -> str:
    # TODO: 后续接入真实 LLM
    return f"[模拟翻译] {source_text} ({source_lang} → {target_lang})"
```

**验证方法：**
```bash
uv run python -c "from app.services.translator import translate_text; import asyncio; print(asyncio.run(translate_text('Hello', 'English', 'Chinese')))"
```

预期输出：`[模拟翻译] Hello (English → Chinese)`

### 步骤 5.2：接入真实 LLM（你做）

**谁做：** 你

**做什么：** 把 mock 替换成真正的 LangChain + DeepSeek 调用。

**需要安装的依赖：** 已经安装了 `langchain` 和 `langchain-openai`（Phase 1 已配好）。

**实现要点：**

**① 创建 ChatOpenAI 实例**
- `model` 参数填模型名：`"deepseek-chat"`
- `api_key` 从 `settings.OPENAI_API_KEY` 读取
- `base_url` 填 `settings.OPENAI_API_BASE`
- `temperature` 填 `0`（翻译任务要精确，不需要创造性）

```
思考题：为什么翻译任务用 temperature=0？
temperature 控制输出的随机性。0 表示每次都选概率最高的词，
翻译需要准确一致，不需要创意，所以用 0。
```

**② 设计 Prompt 模板**

提示词的质量直接影响翻译效果。一个好的翻译 prompt 应该：
- 明确角色：告诉 AI 它是专业翻译
- 明确任务：源语言 → 目标语言
- 明确约束：只输出翻译结果，不要解释

```python
ChatPromptTemplate.from_messages([
    ("system", "You are a professional translator..."),
    ("human", "{source_text}"),
])
```

```
思考题：为什么用 ChatPromptTemplate.from_messages() 而不是直接写字符串？
因为它区分了 system message（系统指令）和 human message（用户输入），
这是 ChatModel 的标准输入格式，能更好地控制 AI 行为。
```

**③ 组装 Chain**

```python
chain = prompt | llm | StrOutputParser()
```

`|` 运算符是 LangChain 的管道操作符，等价于「先经过 prompt 模板填充 → 再经过 LLM 调用 → 最后提取文本」。

**④ 调用**

```python
result = await chain.ainvoke({...})
```

**验证方法：**
```bash
uv run python -c "from app.services.translator import translate_text; import asyncio; print(asyncio.run(translate_text('Hello world', 'English', 'Chinese')))"
```

预期输出：`你好，世界`

如果报网络错误，可能的原因：
1. `API_BASE` 地址不对 → 检查 config.py
2. 网络环境不通 → 试 `ping api.deepseek.com`
3. API Key 无效 → 检查 Key 是否正确

### 步骤 5.3：验证（你做）

**谁做：** 你

**做什么：** 多测几个翻译场景，确认翻译质量。

```bash
uv run python -c "
from app.services.translator import translate_text
import asyncio

async def test():
    print(await translate_text('Good morning', 'English', 'Chinese'))
    print(await translate_text('晚安', 'Chinese', 'English'))
    print(await translate_text('こんにちは', 'Japanese', 'Chinese'))

asyncio.run(test())
"
```

---

## 五、文件变更清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `app/services/translator.py` | 新建 | 翻译服务 |

---

## 六、提示与常见问题

### Q1：为什么要先 mock 再接入真实模型？

- **开发效率**：写路由时不需要联网，不受 API Rate Limit 影响
- **调试方便**：mock 返回固定结果，容易判断是前端问题还是后端问题
- **分工明确**：一个 Phase 只做一件事，路由和翻译服务解耦

### Q2：`temperature` 是什么意思？

控制 AI 生成文本的随机程度：
- 0 = 每次都选最可能的词，输出稳定可重复
- 1 = 有一定随机性，每次输出可能不同
- 翻译用 0，文案创作可以用 0.7-0.9

### Q3：`deepseek-chat` 这个模型支持翻译吗？

支持。DeepSeek 的 `deepseek-chat` 是一个通用对话模型，中英翻译表现很好。如果以后想换模型，只需改 `config.py` 里的 `OPENAI_API_VERSION`。

### Q4：如果 API 调用失败会怎样？

目前先不做错误处理，调用失败会直接抛出异常。到了 Phase 8 打磨阶段再加 try-catch 和降级逻辑。
