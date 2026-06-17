"""
AudioMind 后端 — 最小可运行示例

两个核心接口：
  POST /upload  — 音频上传 → ASR转写 → 推入Dify知识库
  POST /chat    — 用户提问 → 转发Dify Agent → SSE流式返回

启动:
  pip install fastapi uvicorn httpx python-multipart
  uvicorn main:app --reload --port 8080
"""

import os
import httpx
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="AudioMind", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ── 配置 ──────────────────────────────────────────────────
DIFY_API_URL = os.getenv("DIFY_API_URL", "https://cloud.dify.ai/v1")
DIFY_API_KEY = os.getenv("DIFY_API_KEY", "app-xxxxxxxxxxxxx")
DIFY_DATASET_ID = os.getenv("DIFY_DATASET_ID", "")  # Dify 知识库 ID
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "sk-xxx")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

# ── 1. 音频上传 + 转写 + 入库 ────────────────────────────

@app.post("/upload")
async def upload_audio(file: UploadFile = File(...)):
    """
    上传课堂录音 → Whisper 转写 → 推入 Dify 知识库
    """
    # Step 1: 调用 Whisper API 转写
    transcript = await transcribe_audio(file)

    # Step 2: 推入 Dify 知识库（自动分段+Embedding）
    doc_id = await push_to_dify_kb(
        text=transcript,
        filename=file.filename or "课堂录音",
    )

    return JSONResponse({
        "success": True,
        "text": transcript,
        "document_id": doc_id,
        "message": f"已转写并存入知识库 ({len(transcript)} 字)",
    })


async def transcribe_audio(file: UploadFile) -> str:
    """调用云端 Whisper API 将音频转为文字"""
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            f"{OPENAI_BASE_URL}/audio/transcriptions",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
            files={"file": (file.filename, await file.read(), file.content_type)},
            data={"model": "whisper-1", "language": "zh"},
        )
        data = resp.json()
        return data.get("text", "")


async def push_to_dify_kb(text: str, filename: str) -> str:
    """将文本推入 Dify 知识库，返回 document_id"""
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{DIFY_API_URL}/datasets/{DIFY_DATASET_ID}/document/create-by-text",
            headers={
                "Authorization": f"Bearer {DIFY_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "name": filename,
                "text": text,
                "indexing_technique": "high_quality",
                "process_rule": {"mode": "automatic"},
            },
        )
        data = resp.json()
        return data.get("document", {}).get("id", "")


# ── 2. 对话接口（转发 Dify Agent） ─────────────────────────

@app.post("/chat")
async def chat(query: str = Form(...)):
    """
    用户提问 → 转发 Dify Chatflow → SSE 流式返回
    """
    async def sse_stream():
        async with httpx.AsyncClient(timeout=60) as client:
            async with client.stream(
                "POST",
                f"{DIFY_API_URL}/chat-messages",
                headers={
                    "Authorization": f"Bearer {DIFY_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "query": query,
                    "response_mode": "streaming",
                    "user": "student",
                    "inputs": {},
                },
            ) as dify_resp:
                async for line in dify_resp.aiter_lines():
                    if line and line.startswith("data:"):
                        yield f"{line}\n\n"

    return StreamingResponse(sse_stream(), media_type="text/event-stream")


# ── 3. 健康检查 ──────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "dify_configured": bool(DIFY_API_KEY != "app-xxx")}


# ── 启动入口 ──────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
