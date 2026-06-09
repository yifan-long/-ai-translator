# AI 在线翻译

一个能跑、能看、能用的翻译小项目。后端用 FastAPI 调 DeepSeek，前端是 Vue 3 写的单页应用。

## 它能干什么

- 输入一段文本，调用大模型翻译
- 查看、删除历史翻译记录
- 多语言互译（中/英/日/法等）

## 怎么跑起来

### 后端

```bash
cd backend
uv sync
```

把 `backend/.env.example` 复制一份改名 `.env`，填上你的 DeepSeek key：

```bash
cp .env.example .env
# 然后编辑 .env，把 OPENAI_API_KEY 改成你的真实 key
```

```bash
uv run alembic upgrade head   # 建表
uv run uvicorn app.main:app --reload
```

后端跑在 http://127.0.0.1:8000，接口文档在 http://127.0.0.1:8000/docs

### 前端

```bash
cd frontend
npm install
npm run dev
```

浏览器打开 http://localhost:5173 就能用了。

### DeepSeek key 哪里搞

去 https://platform.deepseek.com/ 注册，开通后创建一个 API key，复制到 `.env` 里就行。

## 技术选型

没什么特别的，就是当下写 Web 应用比较顺手的几个：

- **FastAPI**：写接口快，自动有 Swagger 文档
- **SQLModel**：把 SQLAlchemy 和 Pydantic 合一起了，模型定义一处用
- **Alembic**：数据库改表用，不用手动 `ALTER TABLE`
- **LangChain**：拼大模型调用链用的
- **DeepSeek**：便宜的中文大模型，翻译够用
- **Vue 3 + Vite**：前端框架，前者写组件后者打包

## 目录长这样

```
translate/
├── backend/
│   ├── app/
│   │   ├── api/         # 路由
│   │   ├── core/        # 配置、数据库
│   │   ├── models/      # 数据模型
│   │   └── services/    # 业务逻辑
│   ├── alembic/         # 迁移文件
│   └── .env.example
├── frontend/
│   └── src/
│       ├── api/
│       ├── components/
│       └── App.vue
└── md/                  # 我自己写的学习笔记
```

## API 列表

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/translate` | 翻译，返回一条记录 |
| GET | `/api/v1/history` | 翻译历史，支持分页 |
| GET | `/api/v1/history/{id}` | 查一条 |
| DELETE | `/api/v1/history/{id}` | 删一条 |
| GET | `/api/v1/languages` | 支持的语言列表 |

## 我踩过的坑

- **SQLite 加 NOT NULL 字段**：SQLite 不让你给已有表加 NOT NULL 列，得分两步——先加可空的带默认值，再 alter 改成非空。详见 [Alembic 迁移指南](./md/Alembic迁移指南.md)。
- **Pydantic 必填字段**：`Field(...)`（三个点）是"必填"的标志，不是 `Field()`。
- **FastAPI 默认值的坑**：`page: Annotated[int, Query(ge=1)] = 1` 这样写对，`page: Annotated[int, Query(1, ge=1)]` 报错。

## License

MIT
