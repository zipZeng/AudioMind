# 🎙️ AudioMind — 基于 Dify 的课堂录音智能检索系统

> 录音上传 → 语音转写 → 知识入库 → AI 问答，让课堂录音随时可查、可问、可对话

[![Python](https://img.shields.io/badge/Python-3.10+-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green)](https://fastapi.tiangolo.com/)
[![Dify](https://img.shields.io/badge/Dify-API-purple)](https://api.dify.ai/)

---

## 💡 一句话理解

```
学生录音 → 转文字 → 推入 Dify 知识库 → Dify Agent 回答 → 前端展示
```

---

## 🏗️ 架构

```
用户浏览器
    │
    ├── /             对话界面 (index.html)
    ├── /manage       知识库管理 (records.html)
    │
    ▼
FastAPI 后端 (main.py)
    │                    │
    ▼                    ▼
SiliconFlow ASR      Dify 平台
SenseVoiceSmall      知识库 + Chatflow Agent
```

---

## 🚀 快速开始

### 1. 前置准备

- **Dify 账号**：创建 Chatflow 应用 + 知识库，获取 API Key
- **硅基流动 API Key**：[SiliconFlow](https://siliconflow.cn) 注册获取
- **Python 3.10+**

### 2. 配置

```bash
cd audiomind
cp .env.example .env
# 编辑 .env 填入真实值
```

`.env` 核心配置：

```env
ASR_MODE=api
OPENAI_API_KEY=sk-xxx
OPENAI_BASE_URL=https://api.siliconflow.cn/v1
WHISPER_MODEL=FunAudioLLM/SenseVoiceSmall

DIFY_API_URL=https://api.dify.ai/v1
DIFY_API_KEY=app-xxx           # Chatflow 对话
DIFY_DATASET_ID=xxx-xxx        # 知识库 ID
DIFY_DATASET_KEY=dataset-xxx   # 知识库读写
```

### 3. 启动

```bash
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8080
```

### 4. 使用

| 页面 | 地址 | 功能 |
|------|------|------|
| 对话 | `/` | 上传录音、提问 |
| 知识库管理 | `/manage` | 查看/搜索/删除录音 |

---

## 📡 API

| 接口 | 方法 | 说明 |
|------|------|------|
| `/upload` | POST | 上传音频，ASR 转写并推入知识库 |
| `/chat` | POST | 提问，SSE 流式返回 Dify 回答 |
| `/records` | GET | 知识库录音列表（含本地缓存的转写正文） |
| `/records/{id}` | GET | 单条录音详情 + 完整转写文本 |
| `/records/{id}` | DELETE | 删除知识库录音 |
| `/health` | GET | 服务状态检查 |
| `/` | GET | 对话界面 |
| `/manage` | GET | 知识库管理界面 |

---

## 🛠️ 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | 原生 HTML/CSS/JS |
| 后端 | FastAPI + httpx |
| ASR | SiliconFlow SenseVoiceSmall |
| 知识库 & RAG | Dify 平台 |
| LLM | Dify 内置模型 |
| 本地存储 | JSON 文件（转写正文缓存） |

---

## 📁 项目结构

```
AudioMind/
├── audiomind/                # 主应用
│   ├── main.py               # FastAPI 后端
│   ├── index.html            # 对话界面
│   ├── records.html          # 知识库管理界面
│   ├── data/                 # 本地转写缓存
│   ├── scripts/asr_server.py # 本地 ASR（可选）
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── .env.example
├── job/                      # 项目文档
│   ├── docs/                 # 需求/设计/测试/用户手册/PPT大纲
│   └── dify_配置指南.md
└── README.md
```

---

## 🟢 当前进度

| 功能 | 状态 |
|------|------|
| 音频上传 + ASR 转写 | ✅ |
| Dify 知识库入库 | ✅ |
| Dify Agent 对话 + SSE 流式 | ✅ |
| 知识库管理面板（查看/搜索/删除） | ✅ |
| Docker 部署 | ✅ 就绪 |
| 多轮对话 | 🔜 |
| 课程名称标注 | 🔜 |

---

## 📝 License

MIT
