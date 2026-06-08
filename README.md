# 智能点餐系统 - SmartOrderingAgent

## 项目概述

这是一个基于 **LangChain + LangGraph** 的智能点餐系统，通过 **Agent（智能代理）** 实现自主决策和工具调用，让 AI 能够理解用户需求、搜索菜品、完成预订等任务。

## 项目结构

```
SmartOrderingAgent/
├── agent/                          # AI Agent 相关代码
│   ├── langchain_assitant.py       # 核心 Agent 逻辑
│   ├── milvus_data_sync.py         # Milvus 数据同步
│   ├── redis.demo.py               # Redis 演示
│   └── prompts/
│       └── system_prompt.txt       # 系统提示词
├── api/
│   └── main.py                     # FastAPI 后端接口
├── models/
│   └── bge-m3/                     # 本地 Embedding 模型
├── ui/                             # 前端代码
├── run.py                          # 启动文件
├── main.py                         # 主程序入口
├── .env                            # 环境变量配置
├── pyproject.toml                  # 项目依赖
└── menu.sql                        # 菜品数据库
```

## 技术栈

| 组件 | 技术 | 说明 |
|------|------|------|
| **后端框架** | FastAPI | 提供 RESTful API 接口 |
| **AI 框架** | LangChain + LangGraph | 构建 Agent 智能代理 |
| **AI 模型** | 小米 MiMo API | 大语言模型，负责理解和生成 |
| **文本嵌入** | BGE-M3（本地） | 将文本转为向量，用于语义搜索 |
| **向量数据库** | Milvus | 存储和检索向量数据 |
| **关系型数据库** | MySQL | 存储菜品、订单等业务数据 |
| **缓存数据库** | Redis | 存储 FAQ 等缓存数据 |
| **前端** | Vue 3 + Vite | 用户界面 |
| **外部服务** | 高德地图（MCP） | 提供地图、导航服务 |

## 和传统开发的区别

### 传统开发 vs Agent 开发

```
传统开发：用户 → API → 程序员写死的业务逻辑 → 数据库 → 返回结果
Agent 开发：用户 → API → Agent（大模型自主决策）→ 调用工具 → 返回结果
```

### 核心区别

| 组件 | 传统开发 | Agent 开发 |
|------|----------|------------|
| **决策方式** | 程序员写死 if-else 逻辑 | 大模型自主推理决策 |
| **代码结构** | 固定的业务流程 | 工具调用 + 动态规划 |
| **智能程度** | 机械执行 | 理解语义 + 灵活应对 |
| **扩展性** | 需要改代码 | 添加工具即可扩展 |

## 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                    前端 (Vue 3 + Vite)                   │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                   后端 (FastAPI)                         │
│                    api/main.py                          │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│               Agent 核心 (LangChain + LangGraph)        │
│                agent/langchain_assitant.py              │
└─────────────────────────────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
    ┌──────────┐   ┌──────────┐   ┌──────────┐
    │ 大模型   │   │  工具    │   │ 记忆存储  │
    │ (小米API)│   │ (工具集) │   │ (Redis)  │
    └──────────┘   └──────────┘   └──────────┘
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
    ┌──────────┐   ┌──────────┐   ┌──────────┐
    │ MySQL    │   │ Milvus   │   │ 高德地图  │
    │ (业务数据)│   │ (向量库) │   │ (MCP)    │
    └──────────┘   └──────────┘   └──────────┘
```

## LangChain + LangGraph 的作用

### LangChain（基础框架）

**作用**：提供基础零件

- **LLM 接口**：统一调用各种大模型（小米、OpenAI、智谱等）
- **Tool 抽象**：定义和调用外部工具
- **Prompt 模板**：管理和优化提示词

### LangGraph（状态管理）

**作用**：组装零件，管理状态

- **状态管理**：跟踪对话历史和 Agent 状态
- **工作流**：定义 Agent 的执行流程
- **记忆存储**：保存对话上下文（InMemorySaver）

### 它们如何组合

```python
# 1. LangChain 提供工具
@tool
def search_main_dishes(): ...  # LangChain 的 @tool 装饰器

# 2. LangChain 提供模型
llm = ChatOpenAI(model="mimo-v2.5-pro")  # LangChain 的 ChatOpenAI

# 3. LangGraph 管理状态
from langgraph.checkpoint.memory import InMemorySaver
checkpointer = InMemorySaver()  # LangGraph 的状态存储

# 4. LangGraph 创建 Agent
agent = create_agent(
    model=llm,
    tools=[search_main_dishes, user_flavor_search],
    checkpointer=checkpointer
)
```

### 一句话总结

- **LangChain** = 乐高积木的基础零件
- **LangGraph** = 乐高的组装说明书
- **Agent** = 会思考、会决策的智能程序

## Agent 的核心概念

### 什么是 Agent？

**Agent（智能代理）** 是能够根据情况自主决策、调用工具的智能程序。它不是一个固定的流程，而是一个会"思考"的大脑。

### 核心组件

| 组件 | 说明 | 类比 |
|------|------|------|
| **LLM** | 大语言模型，负责理解和生成 | 服务员的大脑 |
| **Tool** | Agent 可以调用的外部功能 | 服务员的工具（菜单、收银台） |
| **Memory** | 存储对话历史 | 服务员的记性 |
| **Prompt** | 系统提示词，定义 Agent 角色 | 服务员的工作指南 |
| **Checkpointer** | 对话状态持久化 | 服务员的笔记本 |

### 工作流程

```
用户输入 → Agent 分析意图 → 选择工具 → 执行工具 → 返回结果
    ↑                                              │
    └────────────── 记住对话历史 ←─────────────────┘
```

### 本项目中的工具

| 工具 | 功能 |
|------|------|
| `search_main_dishes` | 从 MySQL 搜索特色主菜 |
| `user_flavor_search` | 基于语义从 Milvus 搜索菜品 |
| `make_reservation` | 完成餐厅预订 |
| 高德地图 MCP | 查询地图、导航、天气等 |

## BGE-M3 文本嵌入模型

### 什么是 BGE-M3？

**BGE-M3** 是智源研究院（BAAI）开发的**多语言文本嵌入模型**，能够将文本转换为向量表示，用于语义理解和检索。

**项目位置**：`models/bge-m3/`

### 核心能力

| 能力 | 说明 | 用途 |
|------|------|------|
| **Dense Embedding** | 将文本转为 1024 维稠密向量 | 语义相似度计算、语义搜索 |
| **Sparse Embedding** | 生成稀疏向量（类似 BM25） | 关键词匹配、传统检索 |
| **ColBERT 向量** | 多向量表示 | 更精细的语义匹配、重排序 |

### 为什么需要 Embedding 模型？

```
用户输入："我想吃点辣的，有推荐吗？"
菜品描述："麻辣香锅，麻辣鲜香，口感丰富"
```

传统关键词匹配无法理解"辣的"和"麻辣鲜香"是相关的，但 **Embedding 模型可以**！

### 工作原理

```
用户需求 → BGE-M3 → 查询向量 ─┐
                                ├─ 相似度计算 → 返回匹配的菜品
菜品描述 → BGE-M3 → 菜品向量 ─┘
```

## Milvus 向量数据库

### 什么是 Milvus？

**Milvus** 是一个开源的**向量数据库**，专门用于存储、管理和检索向量数据。

### HuggingFace 与 Milvus 的关系

```
HuggingFace（BGE-M3）  →  面粉厂（生产向量）
Milvus                 →  仓库（存储和检索向量）
```

### 完整工作流程

```
文本 ──→ [BGE-M3] ──→ 向量 ──→ [Milvus存储]
                                 │
查询 ──→ [BGE-M3] ──→ 向量 ──→ [Milvus搜索] ──→ 结果
```

### 与 MySQL 的区别

| 特性 | MySQL | Milvus |
|------|-------|--------|
| **数据类型** | 结构化数据（文本、数字） | 向量数据 |
| **查询方式** | SQL（精确匹配） | 相似度搜索（语义匹配） |
| **适用场景** | 订单、用户等业务数据 | 语义搜索、推荐系统 |

**两者配合使用**：MySQL 存储业务数据，Milvus 存储向量数据。

## 环境变量配置

在项目根目录创建 `.env` 文件：

```bash
# AI 模型配置（小米 MiMo）
OPENAI_BASE_URL=https://token-plan-sgp.xiaomimimo.com/v1
OPENAI_API_KEY=你的API密钥

# 数据库配置
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USERNAME=root
MYSQL_PASSWORD=你的密码
MYSQL_DATABASE=menu

# Milvus 配置
MILVUS_URI=http://127.0.0.1:19530
MILVUS_TOKEN=

# Redis 配置
REDIS_URL=redis://127.0.0.1:6379
```

## 运行说明

### 1. 安装依赖

```bash
# 激活虚拟环境
.venv\Scripts\activate

# 安装 Python 依赖
uv sync

# 安装前端依赖
cd ui
npm install
```

### 2. 启动服务

```bash
# 启动后端（端口 8000）
.venv\Scripts\python.exe run.py

# 启动前端（端口 3000）
cd ui
npm run dev
```

### 3. 测试 Agent

```bash
# 测试 Agent 功能
.venv\Scripts\python.exe agent/langchain_assitant.py
```

## 学习资源

- LangChain 官方文档：https://python.langchain.com/
- LangChain GitHub：https://github.com/langchain-ai/langchain
- LangGraph 文档：https://langchain-ai.github.io/langgraph/
- BGE-M3 GitHub：https://github.com/FlagOpen/FlagEmbedding
- Milvus 官方文档：https://milvus.io/docs
- Milvus GitHub：https://github.com/milvus-io/milvus
- FastAPI 官方文档：https://fastapi.tiangolo.com/
