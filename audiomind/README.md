# AudioMind — 基于 Dify 的课堂录音智能检索系统

```
录音上传 → Whisper 转写 → Dify 知识库 → Agent 智能检索 → 流式回答
```

---

## 快速开始

### 1. 前置准备

- **Dify 账号**：[cloud.dify.ai](https://cloud.dify.ai) 注册，创建知识库 + Chatflow（详见 `../job/docs/dify_配置指南.md`）
- **OpenAI API Key**（或 Groq 免费额度）：用于 Whisper 语音转写

### 2. 配置

```bash
cp .env.example .env
# 编辑 .env 填入真实的 API Key
```

### 3. 启动

```bash
# 方式一：直接运行
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8080

# 方式二：Docker
docker compose up -d
```

### 4. 使用

浏览器打开 `http://localhost:8080`

---

## API

| 接口 | 方法 | 说明 |
|------|------|------|
| `/upload` | POST | 上传音频文件，返回转写结果并推入知识库 |
| `/chat` | POST | 发送问题，SSE 流式返回 Dify Agent 回答 |
| `/health` | GET | 服务状态与配置检查 |

---

## 架构

```
用户浏览器 (index.html)
    │  POST /upload     POST /chat (SSE)
    ▼
FastAPI (main.py, 300行)
    │  httpx               httpx stream
    ▼                       ▼
Whisper API              Dify Chatflow
(语音→文字)               (知识检索 + LLM + 回复)
```

---

## 项目结构

```
audiomind/
├── main.py              # FastAPI 后端（唯一后端文件）
├── index.html           # 前端单页应用
├── requirements.txt     # Python 依赖（4个）
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── .gitignore
```
