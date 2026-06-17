#!/usr/bin/env python3
"""
本地语音识别服务 — faster-whisper
监听 8081 端口，提供 REST API 供 Node.js 后端调用

启动: python3 asr_server.py
API:  POST /transcribe  (multipart: file=音频文件)
返回: {"text": "转写文本", "duration": 12.3, "language": "zh"}
"""

import os
import sys
import json
import time
import argparse
import warnings
import uuid
import tempfile
import re
from http.server import HTTPServer, BaseHTTPRequestHandler
from io import BytesIO
from urllib.parse import urlparse

warnings.filterwarnings("ignore")

# ── faster-whisper ─────────────────────────────────────
try:
    from faster_whisper import WhisperModel
except ImportError:
    print("错误: 需要安装 faster-whisper")
    print("  pip install faster-whisper")
    sys.exit(1)

MODEL_SIZE = os.environ.get("ASR_MODEL", "large-v3")
DEVICE = os.environ.get("ASR_DEVICE", "auto")
COMPUTE_TYPE = os.environ.get("ASR_COMPUTE", "float16")

# 初始化模型（懒加载）
_model = None


def get_model():
    global _model
    if _model is None:
        print(f"[ASR] 加载模型: {MODEL_SIZE} (device={DEVICE}, compute={COMPUTE_TYPE})")
        t0 = time.time()
        _model = WhisperModel(MODEL_SIZE, device=DEVICE, compute_type=COMPUTE_TYPE)
        print(f"[ASR] 模型加载完成: {time.time() - t0:.1f}s")
    return _model


def parse_multipart(body, content_type):
    """简易 multipart/form-data 解析器"""
    boundary_match = re.search(r'boundary=(?:"([^"]+)"|([^;]+))', content_type)
    if not boundary_match:
        raise ValueError("无法解析 boundary")
    boundary = boundary_match.group(1) or boundary_match.group(2)

    parts = body.split(f"--{boundary}".encode())
    for part in parts:
        if b"Content-Disposition" not in part or b"filename" not in part:
            continue

        # 找到文件内容的起始位置
        header_end = part.find(b"\r\n\r\n")
        if header_end == -1:
            continue
        file_data = part[header_end + 4:]
        # 去掉尾部 \r\n-- 或 \r\n
        file_data = file_data.rstrip(b"\r\n- ")

        if len(file_data) > 0:
            return file_data
    raise ValueError("未找到文件数据")


# ── HTTP 处理器 ────────────────────────────────────────

class ASRHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        if self.path == "/health":
            self.send_json({"status": "ok", "model": MODEL_SIZE, "device": DEVICE})
        else:
            self.send_error(404, "Not Found")

    def do_POST(self):
        if self.path != "/transcribe":
            self.send_error(404, "Not Found")
            return

        try:
            content_type = self.headers.get("Content-Type", "")
            content_length = int(self.headers.get("Content-Length", 0))

            if content_length == 0:
                self.send_json({"error": "请求体为空"}, 400)
                return

            body = self.rfile.read(content_length)

            # 解析 multipart 文件
            audio_data = parse_multipart(body, content_type)

            # 保存到临时文件（faster-whisper 需要文件路径）
            tmp_path = os.path.join(tempfile.gettempdir(), f"asr_{uuid.uuid4().hex}.wav")
            with open(tmp_path, "wb") as f:
                f.write(audio_data)

            try:
                # 转写
                t0 = time.time()
                model = get_model()

                segments, info = model.transcribe(
                    tmp_path,
                    beam_size=5,
                    vad_filter=True,
                    vad_parameters=dict(min_silence_duration_ms=500),
                    language="zh",
                )

                text_parts = []
                for seg in segments:
                    text_parts.append(seg.text.strip())

                text = " ".join(text_parts)
                elapsed = time.time() - t0

                print(f"[ASR] → {len(text)}字 ({elapsed:.1f}s)")
                self.send_json({
                    "text": text,
                    "duration": round(elapsed, 2),
                    "language": info.language if info else "zh",
                    "segments": len(text_parts),
                })
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)

        except Exception as e:
            print(f"[ASR Error] {e}")
            self.send_json({"error": str(e)}, 500)

    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass  # 静默


def main():
    parser = argparse.ArgumentParser(description="faster-whisper ASR 服务")
    parser.add_argument("--host", default="0.0.0.0", help="监听地址")
    parser.add_argument("--port", type=int, default=8081, help="监听端口")
    parser.add_argument("--model", default="large-v3", help="模型大小: tiny/base/small/medium/large-v3")
    parser.add_argument("--device", default="auto", help="设备: auto/cuda/cpu")
    parser.add_argument("--compute", default="float16", help="精度: float16/int8_float16/int8")
    args = parser.parse_args()

    global MODEL_SIZE, DEVICE, COMPUTE_TYPE
    MODEL_SIZE = args.model or "large-v3"
    DEVICE = args.device or "auto"
    COMPUTE_TYPE = args.compute or "float16"

    # 启动时预加载模型
    print(f"[ASR] faster-whisper 服务启动中...")
    print(f"  model  = {MODEL_SIZE}")
    print(f"  device = {DEVICE}")
    print(f"  compute= {COMPUTE_TYPE}")
    print(f"  listen = http://{args.host}:{args.port}")
    print()

    # 预热加载
    get_model()

    server = HTTPServer((args.host, args.port), ASRHandler)
    print(f"[ASR] 服务已就绪 http://{args.host}:{args.port}/health")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[ASR] 服务关闭")
        server.server_close()


if __name__ == "__main__":
    main()
