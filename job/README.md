# AudioMind — 基于 Dify 的课堂录音智能检索系统

## 一句话理解

```
学生录音 → 转文字 → 推入 Dify 知识库 → Dify Agent 接管一切 → 前端只管对话
```

**核心思路：所有"智能"由 Dify 完成，项目只负责"喂数据"和"展示"。**

---

## 为什么以 Dify 为中心

老师要求的三件事，Dify 都原生支持：

| 要求 | Dify 对应功能 |
|------|--------------|
| 构建知识库 | 知识库 — 上传文档 / API 写入 |
| 智能体 | Chatflow / Agent 工作流 |
| 智能检索 | 知识库节点 + LLM 节点，自动 RAG |

**不需要自建 ChromaDB、Embedding、向量检索——Dify 全包了。**

---

## 架构

```
┌─────────────────────────────────────────────────────┐
│                    用户浏览器                         │
│              (Svelte / 原生 HTML 均可)                │
└────────────────────────┬────────────────────────────┘
                         │ SSE 流式对话
                         ▼
┌─────────────────────────────────────────────────────┐
│              FastAPI / Express 后端                   │
│                                                     │
│   ① POST /upload    — 音频上传 → ASR 转写             │
│   ② POST /chat      — 用户提问 → 转发 Dify Agent     │
│   ③ 中间层：转写文本自动推入 Dify 知识库               │
└────────┬────────────────────────────┬───────────────┘
         │                            │
         ▼                            ▼
┌──────────────────┐     ┌───────────────────────────┐
│  ASR 服务         │     │       Dify 平台            │
│  (Whisper API)    │     │                           │
│                   │     │  📚 知识库 (转写文本入库)    │
│  音频 → 文字      │     │  🤖 Agent (检索+LLM+回答)  │
│                   │     │  🔍 语义检索 (自动 Embed)  │
└──────────────────┘     └───────────────────────────┘
```

---

## 实现细节

### 第一步：在 Dify 上配置好一切（一次性的工作）

**1. 创建知识库**
- Dify 后台 → 知识库 → 创建
- 命名为"课堂录音"

**2. 创建 Chatflow**
- 节点：`开始 → 知识检索(关联上面知识库) → LLM → 直接回复`
- System Prompt：

```
你是一个课堂录音助手。根据知识库中的课堂转写内容回答学生问题。
回答时：
- 使用简体中文
- 若知识库无相关内容，如实告知
- 引用具体课程时间或文件名作为来源
```

**3. 发布 → 获取 API Key**
- 得到 `app-xxxxxxxxxxxxx`
- API 地址形如 `https://cloud.dify.ai/v1`

---

### 第二步：后端核心逻辑

```
POST /upload 流程：
  音频文件
    → ASR 转写为文字
    → 调用 Dify 知识库 API 写入文档
    → 返回转写结果

POST /chat 流程：
  用户问题
    → 调用 Dify Chatflow API (streaming)
    → 转发 SSE 给前端
```

---

### 第三步：关键代码

#### 转写结果推入 Dify 知识库

```python
# POST /upload 中的关键步骤
import requests

def push_to_dify_knowledge(text: str, filename: str):
    """将转写文本推入 Dify 知识库"""
    resp = requests.post(
        "https://cloud.dify.ai/v1/datasets/{dataset_id}/document/create-by-text",
        headers={
            "Authorization": f"Bearer {DIFY_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "name": filename,
            "text": text,
            "indexing_technique": "high_quality",   # 高质量 Embedding
            "process_rule": {"mode": "automatic"},  # 自动分段
        },
    )
    return resp.json()
```

#### 对话接口（转发 Dify Agent SSE）

```python
# POST /chat — 直接把问题丢给 Dify，原样转发 SSE 流
import httpx
from fastapi.responses import StreamingResponse

@app.post("/chat")
async def chat(query: str):
    async def stream():
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                "https://cloud.dify.ai/v1/chat-messages",
                headers={"Authorization": f"Bearer {DIFY_API_KEY}"},
                json={
                    "query": query,
                    "response_mode": "streaming",
                    "user": "student",
                },
            ) as resp:
                async for line in resp.aiter_lines():
                    if line.startswith("data: "):
                        yield line + "\n\n"  # 直接转发
    return StreamingResponse(stream(), media_type="text/event-stream")
```

---

## 数据流全景（一次完整的"昨天布置了什么作业"）

```
1. 学生录音（课堂上老师讲话）
        │
2. 前端 POST /upload 上传音频文件
        │
3. 后端调用 Whisper API 转写
        │  → "同学们回去把第三章习题做完，下周一交"
        │
4. 推入 Dify 知识库（自动 Embedding 向量化）
        │
5. 第二天，学生在对话界面输入
        │  "昨天老师布置了什么作业？"
        │
6. 后端 POST Dify Chatflow
        │
7. Dify Agent:
        │  知识检索 → 命中"第三章习题做完，下周一交"
        │  LLM 推理  → "昨天老师布置了第三章习题，下周一提交"
        │
8. SSE 流式返回前端，学生看到答案
```

---

## 对比原方案

| | 原方案 | 新方案 |
|------|--------|--------|
| 知识库 | 自建 ChromaDB + 手动 Embedding | **Dify 知识库**，全自动 |
| 检索 | SQLite LIKE 关键字匹配 | **Dify 语义检索** |
| 智能体 | 只有一问一答 | **Dify Chatflow/Agent** |
| RAG 流程 | 自己拼 SQL + 拼接 prompt | **Dify 内置**，拖拽配置 |
| 部署 | 三服务 + GPU | **一个后端 + Dify 云端** |
| 开发量 | 2000+ 行 | **300 行**（ASR + 转发） |

---

## 简化的分工

| 成员 | 职责 | 工作量 |
|------|------|--------|
| **成员1（组长）** | 项目管理、需求文档、PPT答辩、Dify Chatflow 配置 | 中等 |
| **成员2（前端）** | Svelte 对话界面 + 音频上传页 | 中等 |
| **成员3（后端）** | FastAPI：文件上传 + ASR 调用 + Dify 转发 | **少**（核心代码就两个接口） |
| **成员4（ASR + Dify）** | Whisper API 对接 + Dify 知识库写入 | 中等 |
| **成员5（Dify Agent）** | Dify Chatflow 设计 + Prompt 调优 + 测试 | 中等 |
| **成员6（部署）** | Docker 打包 + 云服务器上线 | 少 |

---

## 开发路线图

```
第1-2周  → Dify 上搭好 Chatflow + 知识库，验证"手动输入文本→能问答"
第3-4周  → 后端开发（两个接口）+ 前端开发（对话页 + 上传页）
第5-6周  → 联调：录音→转写→入库→提问→回答，全链路跑通
第7-8周  → Docker 打包、云部署、写文档、做PPT
```
