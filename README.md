# 🎙️ AudioMind — 基于 Dify 的课堂录音智能检索系统

> 录音上传 → 语音转写 → 知识入库 → AI 问答，让课堂录音随时可查、可问、可对话

[![Python](https://img.shields.io/badge/Python-3.10+-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green)](https://fastapi.tiangolo.com/)
[![Dify](https://img.shields.io/badge/Dify-API-purple)](https://api.dify.ai/)
[![SiliconFlow](https://img.shields.io/badge/ASR-SiliconFlow-orange)](https://siliconflow.cn/)

---

## 💡 一句话理解

```
学生录音 → 转文字 → 推入 Dify 知识库 → Dify Agent 回答 → 前端展示
```

---

## 🎯 解决的问题

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
                       │  GET  /records   DELETE /records/{id}
                       ▼
┌──────────────────────────────────────────────────────────┐
│                  FastAPI 后端 (main.py)                    │
│                                                          │
│  ① POST /upload    — 音频上传 → ASR 转写 → 推入知识库       │
│  ② POST /chat      — 用户提问 → 转发 Dify Agent → SSE 流式  │
│  ③ GET  /records   — 查询知识库录音列表                     │
│  ④ DELETE /records/{id} — 删除知识库录音                   │
│  ⑤ GET  /health    — 服务状态与配置检查                     │
└─────────┬───────────────────────────────┬────────────────┘
          │                               │
          ▼                               ▼
┌─────────────────────┐     ┌──────────────────────────────┐
│   ASR 语音转写       │     │        Dify 平台              │
│                     │     │                              │
│  硅基流动            │     │  📚 知识库 (自动 Embedding)   │
│  SenseVoiceSmall    │     │  🤖 Chatflow/Agent (RAG)     │
│                     │     │  🔍 语义检索                  │
└─────────────────────┘     └──────────────────────────────┘
```

---

## 🔄 数据流

```
学生录音（课堂上老师讲话）
    │
    ▼
POST /upload 上传音频文件
    │
    ▼
硅基流动 SenseVoiceSmall 转写 → "同学们回去把第三章习题做完，下周一交"
    │
    ▼
推入 Dify 知识库 → 自动分段 + Embedding 向量化
    │
    ▼
学生提问："昨天老师布置了什么作业？"
    │
    ▼
Dify Agent: 知识检索 → 命中相关内容 → LLM 生成回答
    │
    ▼
SSE 流式返回 → 前端逐字显示
```

---

## 🚀 快速开始

### 1. 前置准备

- **Dify 账号**：在 [Dify](https://cloud.dify.ai) 创建应用，获取 API Key 和知识库 ID
- **硅基流动 API Key**：注册 [SiliconFlow](https://siliconflow.cn) 获取 Key
- **Python 3.10+**

### 2. 配置

```bash
cd audiomind
cp .env.example .env
# 编辑 .env 填入真实的 API Key
```

`.env` 需配置：

```env
# ASR 语音转写（硅基流动）
ASR_MODE=api
OPENAI_API_KEY=sk-xxxxxxxx
OPENAI_BASE_URL=https://api.siliconflow.cn/v1
WHISPER_MODEL=FunAudioLLM/SenseVoiceSmall

# Dify 智能体
DIFY_API_URL=https://api.dify.ai/v1
DIFY_API_KEY=app-xxxxxxxx          # Chatflow 对话用
DIFY_DATASET_ID=xxxxxxxx-xxxx-...  # 知识库 ID
DIFY_DATASET_KEY=dataset-xxxxxxxx  # 知识库写入用

# 代理（如果 Dify API 需要翻墙）
DIFY_PROXY=http://127.0.0.1:7897
```

### 3. 启动

```bash
cd audiomind
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8080
```

### 4. 使用

浏览器打开 `http://localhost:8080`，上传录音并提问。

---

## 📡 API

| 接口 | 方法 | 说明 |
|------|------|------|
| `/upload` | POST | 上传音频文件，转写并推入知识库 |
| `/chat` | POST | 发送问题，SSE 流式返回 Dify Agent 回答 |
| `/records` | GET | 查询知识库中已上传的录音列表 |
| `/records/{id}` | DELETE | 从知识库删除指定录音 |
| `/health` | GET | 服务状态与配置检查 |
| `/` | GET | 前端对话界面 |

---

## 📁 项目结构

```
AudioMind/
├── audiomind/                # 主应用
│   ├── main.py               # FastAPI 后端（~400 行）
│   ├── index.html            # 前端单页应用
│   ├── scripts/
│   │   └── asr_server.py     # 本地 ASR 服务（可选）
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── .env
│   └── .env.example
│
├── job/                      # 项目文档
│   ├── main.py               # 后端简化示例
│   ├── index.html            # 前端简化示例
│   ├── dify_配置指南.md
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── requirements.txt
│   └── docs/
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
| 后端 | FastAPI + httpx | 异步 Web 框架 |
| 语音转写 | SiliconFlow SenseVoiceSmall | 中文转写，按量付费 |
| 知识库 & RAG | **Dify 平台** | 知识库、Embedding、语义检索、Agent |
| LLM | Dify 内置模型 | 由 Dify 统一管理 |
| 部署 | Docker + Docker Compose | 一键部署 |

---

## ✨ 为什么以 Dify 为中心

| 功能 | Dify 实现 |
|------|-------------|
| 构建知识库 | 知识库 — API 写入文档 |
| 智能体 | Chatflow / Agent 工作流 |
| 智能检索 | 知识检索节点 + LLM 节点，自动 RAG |

---

## 🟢 当前进度

| 功能 | 状态 |
|------|------|
| 音频上传 + ASR 转写 | ✅ 完成 |
| Dify 知识库入库（自定义分段 200 token） | ✅ 完成 |
| Dify Agent 智能问答 + SSE 流式 | ✅ 完成 |
| 知识库录音列表查询 / 删除 | ✅ 完成 |
| 前端对话界面 | ✅ 完成 |
| 多轮对话 | 🔜 待实现 |
| 知识库管理面板（前端） | 🔜 待实现 |
| Docker 一键部署 | ✅ 就绪 |
| 项目文档 | ✅ 齐全 |

---

## 📝 License

MIT
