# 🎙️ AudioMind — 基于 Dify 的课堂录音智能检索系统

> 录音上传 → 语音转写 → 知识入库 → AI 问答，让课堂录音随时可查、可问、可对话

[![Python](https://img.shields.io/badge/Python-3.10+-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green)](https://fastapi.tiangolo.com/)
[![Dify](https://img.shields.io/badge/Dify-Cloud-purple)](https://cloud.dify.ai/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED)](https://www.docker.com/)

---

## 💡 一句话理解

```
学生录音 → 转文字 → 推入 Dify 知识库 → Dify Agent 接管一切 → 前端只管对话
```

**核心思路：所有"智能"由 Dify 完成，本项目只负责"喂数据"和"展示"。**

---

## 🎯 解决的问题

大学生在课堂学习中面临三大痛点：

| 痛点 | AudioMind 方案 |
|------|---------------|
| 📝 课堂信息量大，笔记难以完整记录 | 一键上传录音，自动转写为文字 |
| ⏳ 课后复习要反复回听录音，耗时低效 | 转写文本永久保存在知识库中 |
| 🔍 找"老师上次提的某个知识点"只能凭记忆 | AI 对话式检索，用自然语言提问 |

---

## 🏗️ 架构

```
┌──────────────────────────────────────────────────────────┐
│                      用户浏览器                            │
│                  (index.html 单页应用)                      │
└──────────────────────┬───────────────────────────────────┘
                       │  POST /upload    POST /chat (SSE)
                       ▼
┌──────────────────────────────────────────────────────────┐
│                  FastAPI 后端 (main.py)                    │
│                                                          │
│  ① POST /upload  — 音频上传 → ASR 转写 → 推入知识库       │
│  ② POST /chat    — 用户提问 → 转发 Dify Agent → SSE 流式  │
│  ③ GET  /health  — 服务状态与配置检查                     │
└─────────┬───────────────────────────────┬────────────────┘
          │                               │
          ▼                               ▼
┌─────────────────────┐     ┌──────────────────────────────┐
│   ASR 语音转写       │     │        Dify 平台              │
│                     │     │                              │
│  本地: faster-whisper│     │  📚 知识库 (自动 Embedding)   │
│  云端: Whisper API   │     │  🤖 Chatflow/Agent (RAG)     │
│                     │     │  🔍 语义检索                  │
└─────────────────────┘     └──────────────────────────────┘
```

---

## 🔄 数据流演示

以"昨天布置了什么作业"为例：

```
学生录音（课堂上老师讲话）
    │
    ▼
POST /upload 上传音频文件
    │
    ▼
Whisper 转写 → "同学们回去把第三章习题做完，下周一交"
    │
    ▼
推入 Dify 知识库 → 自动 Embedding 向量化
    │
    ▼
第二天学生提问："昨天老师布置了什么作业？"
    │
    ▼
Dify Agent: 知识检索 → 命中相关内容 → LLM 生成回答
    │
    ▼
SSE 流式返回 → 前端显示："昨天老师布置了第三章习题，下周一提交"
```

---

## 🚀 快速开始

### 1. 前置准备

- **Dify 账号**：[cloud.dify.ai](https://cloud.dify.ai) 注册，创建知识库 + Chatflow
  - 详细配置步骤见 [`job/dify_配置指南.md`](job/dify_配置指南.md)
- **OpenAI API Key**（或 Groq 免费额度）：用于 Whisper 语音转写
- **Python 3.10+**

### 2. 配置

```bash
cd audiomind
cp .env.example .env
# 编辑 .env 填入真实的 API Key
```

### 3. 启动

```bash
# 方式一：直接运行
cd audiomind
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8080

# 方式二：Docker
cd audiomind
docker compose up -d
```

### 4. 使用

浏览器打开 `http://localhost:8080`，上传录音并开始对话。

---

## 📡 API

| 接口 | 方法 | 说明 |
|------|------|------|
| `/upload` | POST | 上传音频文件，返回转写结果并推入知识库 |
| `/chat` | POST | 发送问题，SSE 流式返回 Dify Agent 回答 |
| `/health` | GET | 服务状态与配置检查 |
| `/` | GET | 前端对话界面 |

---

## 📁 项目结构

```
AudioMind/
├── audiomind/                # 主应用
│   ├── main.py               # FastAPI 后端（唯一后端文件，~330行）
│   ├── index.html            # 前端单页应用
│   ├── scripts/
│   │   └── asr_server.py     # 本地 ASR 服务
│   ├── requirements.txt      # Python 依赖
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── .env.example          # 环境变量模板
│   └── .gitignore
│
├── job/                      # 项目文档与配置
│   ├── main.py               # 后端简化示例
│   ├── index.html            # 前端简化示例
│   ├── dify_配置指南.md       # Dify 平台配置步骤
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── requirements.txt
│   └── docs/                 # 项目文档
│       ├── 01_需求规格说明书.md
│       ├── 02_系统设计说明书.md
│       ├── 03_项目开发计划.md
│       ├── 04_详细设计说明书.md
│       ├── 05_测试计划.md
│       ├── 06_用户手册.md
│       └── 07_答辩PPT大纲.md
│
└── README.md
```

---

## 🛠️ 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 前端 | 原生 HTML/CSS/JS | 单页应用，零依赖 |
| 后端 | FastAPI + httpx | 异步 Web 框架，~330 行代码 |
| 语音转写 | Whisper API / faster-whisper | 支持云端和本地两种模式 |
| 知识库 & RAG | **Dify 平台** | 知识库、Embedding、语义检索、Agent 全部托管 |
| LLM | Dify 内置模型 | 由 Dify 统一管理，无需额外对接 |
| 部署 | Docker + Docker Compose | 一键部署 |

---

## ✨ 为什么以 Dify 为中心

老师要求的三件事，Dify 都原生支持——**不需要自建 ChromaDB、Embedding、向量检索**：

| 要求 | Dify 对应功能 |
|------|-------------|
| 构建知识库 | 知识库 — 上传文档 / API 写入 |
| 智能体 | Chatflow / Agent 工作流 |
| 智能检索 | 知识库节点 + LLM 节点，自动 RAG |

对比传统自建方案，开发量从 2000+ 行降至 **~300 行**。

---

## 📚 文档

完整项目文档见 [`job/docs/`](job/docs/)：

| 文档 | 内容 |
|------|------|
| [01_需求规格说明书](job/docs/01_需求规格说明书.md) | 项目背景、目标、功能需求 |
| [02_系统设计说明书](job/docs/02_系统设计说明书.md) | 系统架构、模块设计 |
| [03_项目开发计划](job/docs/03_项目开发计划.md) | 开发阶段、时间规划 |
| [04_详细设计说明书](job/docs/04_详细设计说明书.md) | 接口设计、数据库设计 |
| [05_测试计划](job/docs/05_测试计划.md) | 测试策略、用例 |
| [06_用户手册](job/docs/06_用户手册.md) | 使用说明 |
| [07_答辩PPT大纲](job/docs/07_答辩PPT大纲.md) | 答辩材料 |
| [Dify 配置指南](job/dify_配置指南.md) | Dify 平台配置步骤 |

---

## 👥 分工建议

| 角色 | 职责 | 工作量 |
|------|------|--------|
| 组长 | 项目管理、需求文档、PPT答辩、Dify Chatflow 配置 | 中等 |
| 前端 | 对话界面 + 音频上传页 | 中等 |
| 后端 | FastAPI：文件上传 + ASR 调用 + Dify 转发 | **少**（核心就两个接口） |
| ASR + Dify | Whisper API 对接 + Dify 知识库写入 | 中等 |
| Dify Agent | Chatflow 设计 + Prompt 调优 + 测试 | 中等 |
| 部署 | Docker 打包 + 云服务器上线 | 少 |

---

## 📝 License

MIT
