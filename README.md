# TaskPilot

基于 LangGraph + Claude 的动态 Skill 路由 Agent，支持双层记忆与全链路追踪。

## 架构

```
用户输入
  → memory_node（注入历史上下文）
  → router_node（Claude Haiku 意图分类 → Skill 名称）
  → load_skill_node（动态加载 YAML Skill 工具定义）
  → execute_node（Claude Sonnet 执行 + Langfuse trace）
  → 返回结果

记忆层：Redis 短期（滑动窗口 10 条）+ pgvector 长期（向量检索）
追踪层：Langfuse 全链路可观测
```

## 项目结构

```
TaskPilot/
├── config/
│   ├── settings.py        # 统一配置（.env 驱动）
│   └── init.sql           # memories 表 + HNSW 索引
├── skills/
│   ├── __init__.py        # SkillRegistry：YAML 动态加载
│   ├── weather.yaml
│   ├── calendar.yaml
│   └── code_run.yaml
├── router/agent.py        # 意图分类 Router
├── memory/
│   ├── short_term.py      # Redis 滑动窗口
│   ├── long_term.py       # pgvector 向量检索
│   └── manager.py         # 短期 + 长期融合
├── graph/workflow.py      # LangGraph 执行图 + MemorySaver
├── api/main.py            # FastAPI：/chat /skills /health
├── tests/                 # 7 个单元测试（无需外部服务）
├── docker-compose.yml     # postgres+pgvector / redis / langfuse
├── requirements.txt
├── start.sh
└── .env.example
```

## 快速开始

### 1. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，填入：
# ANTHROPIC_API_KEY=sk-ant-xxx
# OPENAI_API_KEY=sk-xxx（用于向量嵌入）
```

### 2. 启动基础设施

```bash
docker compose up -d postgres redis langfuse
```

验证：
```bash
docker compose exec postgres psql -U taskpilot -d taskpilot \
  -c "SELECT extversion FROM pg_extension WHERE extname='vector';"
# 返回版本号即为成功
```

### 3. 安装依赖并启动

```bash
pip install -r requirements.txt
uvicorn api.main:api --reload --port 8000
```

- API 文档：http://localhost:8000/docs
- Langfuse 追踪：http://localhost:3000

## 接口

### POST /chat

```json
{
  "message": "北京今天天气怎么样",
  "session_id": "user_001"
}
```

返回：
```json
{
  "answer": "北京今天晴，气温 28°C...",
  "skill_used": "weather"
}
```

### GET /skills

返回所有已注册 Skill 列表。

## 测试

```bash
python -m pytest tests/ -v
```

7 个测试全部不依赖外部服务（Router/Memory 用 mock）。

## 添加新 Skill

在 `skills/` 目录下新建 YAML 文件即可，无需改代码：

```yaml
name: translate
description: "翻译文本到指定语言"
tools:
  - name: translate_text
    description: "翻译文本"
    parameters:
      text:
        type: string
      target_language:
        type: string
```

重启服务后自动生效。

## 技术栈

| 层 | 技术 |
|---|---|
| Agent 框架 | LangGraph |
| LLM | Claude Haiku（路由）/ Claude Sonnet（执行） |
| 短期记忆 | Redis |
| 长期记忆 | pgvector（PostgreSQL） |
| 向量嵌入 | OpenAI text-embedding-3-small |
| 追踪 | Langfuse |
| API | FastAPI |
| 容器 | Docker Compose |
