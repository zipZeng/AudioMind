"""
AudioMind — 基于 Dify 的课堂录音智能检索系统
==============================================
FastAPI 后端，两个核心接口:
  POST /upload  — 上传音频 → Whisper 转写 → 推入 Dify 知识库
  POST /chat    — 提问 → 转发 Dify Agent → SSE 流式返回

启动:
  pip install -r requirements.txt
  uvicorn main:app --host 0.0.0.0 --port 8080
"""

import os
import logging
from typing import Optional

from dotenv import load_dotenv
load_dotenv()

import httpx
from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

# ── 日志 ──────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="[AudioMind] %(message)s")
log = logging.getLogger(__name__)

# ── 配置（全部通过环境变量注入） ──────────────────────────
DIFY_API_URL     = os.getenv("DIFY_API_URL",     "https://cloud.dify.ai/v1")
DIFY_API_KEY     = os.getenv("DIFY_API_KEY",     "")
DIFY_DATASET_ID  = os.getenv("DIFY_DATASET_ID",  "")
DIFY_DATASET_KEY = os.getenv("DIFY_DATASET_KEY", "")  # 知识库写入用
DIFY_PROXY       = os.getenv("DIFY_PROXY",       "")  # 代理

# ASR 模式: "local" = 本地 faster-whisper(:8081) | "api" = 云端 Whisper API
ASR_MODE         = os.getenv("ASR_MODE",         "local")
LOCAL_ASR_URL    = os.getenv("LOCAL_ASR_URL",    "http://localhost:8081")

# 云端 ASR 配置（仅 ASR_MODE=api 时需要）
OPENAI_API_KEY   = os.getenv("OPENAI_API_KEY",   "")
OPENAI_BASE_URL  = os.getenv("OPENAI_BASE_URL",  "https://api.openai.com/v1")
WHISPER_MODEL    = os.getenv("WHISPER_MODEL",    "whisper-1")
MAX_FILE_SIZE    = 25 * 1024 * 1024  # 25MB

SUPPORTED_AUDIO = {
    "audio/mpeg", "audio/mp3", "audio/wav", "audio/x-wav",
    "audio/mp4", "audio/m4a", "audio/x-m4a",
    "audio/webm", "audio/ogg", "audio/flac", "audio/x-flac",
}

# ── FastAPI 应用 ──────────────────────────────────────────
app = FastAPI(title="AudioMind", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


# ═══════════════════════════════════════════════════════════
# 工具函数
# ═══════════════════════════════════════════════════════════

def _check_config():
    """检查必要配置是否已设置"""
    missing = []
    if not DIFY_API_KEY or DIFY_API_KEY == "app-xxx":
        missing.append("DIFY_API_KEY")
    if not DIFY_DATASET_ID:
        missing.append("DIFY_DATASET_ID")
    if ASR_MODE == "api":
        if not OPENAI_API_KEY or OPENAI_API_KEY == "sk-xxx":
            missing.append("OPENAI_API_KEY")
    return missing


async def _transcribe(file: UploadFile) -> str:
    """
    音频转文字。
    本地模式: 调 faster-whisper 服务 (:8081)
    API 模式: 调云端 Whisper API
    """
    content = await file.read()
    if len(content) == 0:
        raise HTTPException(400, "文件为空")
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(413, f"文件超过 {MAX_FILE_SIZE // 1024 // 1024}MB 限制")

    if ASR_MODE == "local":
        return await _transcribe_local(content, file.filename or "audio")
    else:
        return await _transcribe_api(content, file.filename or "audio", file.content_type)


async def _transcribe_local(content: bytes, filename: str) -> str:
    """
    调本地 faster-whisper 服务进行转写。
    POST http://localhost:8081/transcribe
    """
    # 构造 multipart/form-data
    boundary = f"----FormBoundary{id(content)}"
    header = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f"Content-Type: audio/wav\r\n\r\n"
    ).encode()
    footer = f"\r\n--{boundary}--\r\n".encode()
    body = header + content + footer

    async with httpx.AsyncClient(timeout=300) as client:
        resp = await client.post(
            f"{LOCAL_ASR_URL}/transcribe",
            content=body,
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        )

    if resp.status_code != 200:
        detail = resp.text[:300]
        log.error(f"本地 ASR 失败 ({resp.status_code}): {detail}")
        raise HTTPException(502, f"语音转写失败: {detail}")

    data = resp.json()
    if data.get("error"):
        raise HTTPException(500, data["error"])

    text = (data.get("text") or "").strip()
    if not text:
        raise HTTPException(500, "转写结果为空，请检查音频是否包含中文语音")
    log.info(f"转写完成 ({ASR_MODE}): {len(text)} 字")
    return text


async def _transcribe_api(content: bytes, filename: str, content_type: str) -> str:
    """
    调云端 Whisper API 进行转写。
    POST {OPENAI_BASE_URL}/audio/transcriptions
    """
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            f"{OPENAI_BASE_URL}/audio/transcriptions",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
            files={"file": (filename, content, content_type)},
            data={"model": WHISPER_MODEL, "language": "zh"},
        )

    if resp.status_code != 200:
        detail = resp.text[:300]
        log.error(f"Whisper API 失败 ({resp.status_code}): {detail}")
        raise HTTPException(502, f"语音转写失败: {detail}")

    data = resp.json()
    text = (data.get("text") or "").strip()
    if not text:
        raise HTTPException(500, "转写结果为空，请检查音频是否包含中文语音")
    log.info(f"转写完成 (api): {len(text)} 字")
    return text


async def _push_to_dify(text: str, filename: str) -> dict:
    """
    将转写文本推入 Dify 知识库，Dify 自动:
    1. 按语义分段
    2. Embedding 向量化
    3. 入库立即可检索
    """
    body = {
        "name": filename,
        "text": text,
        "indexing_technique": "high_quality",
        "process_rule": {"mode": "automatic"},
    }

    async with httpx.AsyncClient(timeout=60, proxy=DIFY_PROXY or None) as client:
        resp = await client.post(
            f"{DIFY_API_URL}/datasets/{DIFY_DATASET_ID}/document/create-by-text",
            headers={
                "Authorization": f"Bearer {DIFY_DATASET_KEY or DIFY_API_KEY}",
                "Content-Type": "application/json",
            },
            json=body,
        )

    if resp.status_code not in (200, 201):
        detail = resp.text[:300]
        log.error(f"Dify 入库失败 ({resp.status_code}): {detail}")
        raise HTTPException(502, f"知识库写入失败: {detail}")

    data = resp.json()
    doc_id = data.get("document", {}).get("id", "")
    log.info(f"已推入 Dify 知识库: {doc_id}")
    return data


# ═══════════════════════════════════════════════════════════
# API 接口
# ═══════════════════════════════════════════════════════════

@app.post("/upload")
async def upload_audio(file: UploadFile = File(...)):
    """
    上传课堂录音 → ASR 转写 → (可选)推入 Dify 知识库

    curl -X POST http://localhost:8080/upload -F "file=@录音.mp3"
    """
    # 校验文件类型
    content_type = file.content_type or ""
    if content_type not in SUPPORTED_AUDIO and not any(
        content_type.startswith(t.split("/")[0] + "/") for t in SUPPORTED_AUDIO
    ):
        log.warning(f"未知音频类型: {content_type}，尝试转写")

    # 转写（不依赖 Dify）
    text = await _transcribe(file)

    # 入库 Dify（可选，配置了才推）
    filename = file.filename or "课堂录音"
    doc_id = ""
    dify_ok = not ("DIFY_API_KEY" in _check_config() or "DIFY_DATASET_ID" in _check_config())
    if dify_ok:
        try:
            dify_result = await _push_to_dify(text, filename)
            doc_id = dify_result.get("document", {}).get("id", "")
        except Exception as e:
            log.warning(f"知识库写入失败（转写不受影响）: {e}")
    else:
        log.info("Dify 未配置，跳过知识库入库")

    return JSONResponse({
        "success": True,
        "text": text,
        "chars": len(text),
        "document_id": doc_id,
        "dify_synced": bool(doc_id),
        "message": f"已转写 ({len(text)} 字)" + (", 已存入知识库" if doc_id else ""),
    })


@app.post("/chat")
async def chat(query: str = Form(...)):
    """
    提问 → 转发 Dify Chatflow → SSE 流式返回

    curl -N -X POST http://localhost:8080/chat -d "query=布置了什么作业"
    """
    missing = _check_config()
    if missing:
        raise HTTPException(503, f"服务未配置: {', '.join(missing)}")

    if not query or not query.strip():
        raise HTTPException(400, "问题不能为空")

    async def sse_generator():
        """异步生成器：逐行转发 Dify 的 SSE 流"""
        try:
            async with httpx.AsyncClient(timeout=120, proxy=DIFY_PROXY or None) as client:
                async with client.stream(
                    "POST",
                    f"{DIFY_API_URL}/chat-messages",
                    headers={
                        "Authorization": f"Bearer {DIFY_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "query": query.strip(),
                        "response_mode": "streaming",
                        "user": "student",
                        "inputs": {"user_input": query.strip()},
                    },
                ) as dify_resp:
                    if dify_resp.status_code != 200:
                        body = await dify_resp.aread()
                        log.error(f"Dify Chatflow 失败 ({dify_resp.status_code}): {body[:300]}")
                        yield f'data: {{"event":"error","message":"智能问答服务异常: {dify_resp.status_code}"}}\n\n'
                        return

                    async for line in dify_resp.aiter_lines():
                        if line and line.startswith("data:"):
                            yield f"{line}\n\n"

        except httpx.ConnectError:
            yield f'data: {{"event":"error","message":"无法连接 Dify 服务，请检查 DIFY_API_URL"}}\n\n'
        except Exception as e:
            log.error(f"SSE 流异常: {e}")
            yield f'data: {{"event":"error","message":"服务异常: {str(e)[:200]}"}}\n\n'

    return StreamingResponse(
        sse_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # 禁用 nginx 缓冲
            "Connection": "keep-alive",
        },
    )


@app.get("/")
async def index():
    """返回前端页面"""
    import os as _os
    html_path = _os.path.join(_os.path.dirname(__file__), "index.html")
    if not _os.path.exists(html_path):
        raise HTTPException(404, "前端页面不存在")
    return HTMLResponse(open(html_path, encoding="utf-8").read())


@app.get("/health")
async def health():
    """健康检查 + 配置状态"""
    missing = _check_config()
    return {
        "status": "degraded" if missing else "ok",
        "service": "AudioMind",
        "version": "1.0.0",
        "asr_mode": ASR_MODE,
        "config": {
            "dify": not ("DIFY_API_KEY" in missing or "DIFY_DATASET_ID" in missing),
            "asr": "OPENAI_API_KEY" not in missing if ASR_MODE == "api" else True,
        },
        "missing": missing,
    }


# ═══════════════════════════════════════════════════════════
# 启动入口
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn

    missing = _check_config()
    if missing:
        log.warning(f"⚠️  缺少配置: {', '.join(missing)}")
        log.warning("请设置环境变量后重启，详见 .env.example")
    else:
        log.info("✅ 配置检查通过")

    uvicorn.run(app, host="0.0.0.0", port=8080)
