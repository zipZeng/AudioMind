# AudioMind——API 接口文档

> 版本：v1.0 | 日期：2026-06-09 | 基础路径：`http://localhost:8000/api`

---

## 1. 通用规范

### 1.1 认证方式

```
Authorization: Bearer <JWT_TOKEN>
```

### 1.2 统一响应格式

```json
{
  "code": 200,
  "message": "success",
  "data": {}
}
```

错误响应：

```json
{
  "code": 400,
  "message": "错误描述",
  "data": null
}
```

### 1.3 状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 201 | 创建成功 |
| 400 | 请求参数错误 |
| 401 | 未认证 |
| 403 | 无权限 |
| 404 | 资源不存在 |
| 413 | 文件过大 |
| 422 | 请求体验证失败 |
| 500 | 服务器内部错误 |

---

## 2. 用户模块 API

### 2.1 用户注册

```
POST /api/auth/register
```

**请求体：**

```json
{
  "email": "student@university.edu.cn",
  "username": "张三",
  "password": "SecurePass123!"
}
```

**响应：**

```json
{
  "code": 201,
  "message": "注册成功",
  "data": {
    "id": 1,
    "email": "student@university.edu.cn",
    "username": "张三"
  }
}
```

### 2.2 用户登录

```
POST /api/auth/login
```

**请求体：**

```json
{
  "email": "student@university.edu.cn",
  "password": "SecurePass123!"
}
```

**响应：**

```json
{
  "code": 200,
  "message": "登录成功",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer",
    "expires_in": 86400,
    "user": {
      "id": 1,
      "username": "张三",
      "email": "student@university.edu.cn"
    }
  }
}
```

### 2.3 获取当前用户信息

```
GET /api/user/me
```

**Headers:** `Authorization: Bearer <token>`

**响应：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "username": "张三",
    "email": "student@university.edu.cn",
    "avatar_url": null,
    "created_at": "2026-06-01T10:00:00Z"
  }
}
```

---

## 3. 课程模块 API

### 3.1 创建课程

```
POST /api/courses
```

**请求体：**

```json
{
  "name": "云计算技术",
  "teacher": "李教授",
  "semester": "2026春",
  "description": "云计算基础概念与技术实践"
}
```

**响应：**

```json
{
  "code": 201,
  "message": "课程创建成功",
  "data": {
    "id": 1,
    "name": "云计算技术",
    "teacher": "李教授",
    "semester": "2026春",
    "created_at": "2026-06-09T10:00:00Z"
  }
}
```

### 3.2 获取课程列表

```
GET /api/courses?semester=2026春&page=1&page_size=20
```

**响应：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 1,
        "name": "云计算技术",
        "teacher": "李教授",
        "semester": "2026春",
        "audio_count": 3,
        "created_at": "2026-06-09T10:00:00Z"
      }
    ],
    "total": 1,
    "page": 1,
    "page_size": 20
  }
}
```

### 3.3 获取课程详情

```
GET /api/courses/{course_id}
```

**响应：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "name": "云计算技术",
    "teacher": "李教授",
    "semester": "2026春",
    "description": "云计算基础概念与技术实践",
    "audio_files": [...],
    "knowledge_ready": true,
    "created_at": "2026-06-09T10:00:00Z"
  }
}
```

### 3.4 删除课程

```
DELETE /api/courses/{course_id}
```

**响应：**

```json
{
  "code": 200,
  "message": "课程已删除",
  "data": null
}
```

---

## 4. 音频上传 API

### 4.1 上传音频

```
POST /api/upload
```

**请求：** `multipart/form-data`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | File | 是 | 音频文件 (.mp3/.wav/.m4a) |
| course_id | Integer | 是 | 所属课程ID |

**响应：**

```json
{
  "code": 201,
  "message": "上传成功，正在转写",
  "data": {
    "id": 1,
    "original_name": "cloud_computing_lec3.mp3",
    "file_size": 52428800,
    "file_type": "mp3",
    "status": "transcribing",
    "course_id": 1,
    "uploaded_at": "2026-06-09T10:00:00Z"
  }
}
```

### 4.2 获取音频列表

```
GET /api/files?course_id=1&status=completed&page=1&page_size=20
```

**响应：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 1,
        "original_name": "cloud_computing_lec3.mp3",
        "file_size": 52428800,
        "file_type": "mp3",
        "duration_seconds": 5400.0,
        "status": "completed",
        "course_id": 1,
        "uploaded_at": "2026-06-09T10:00:00Z",
        "processed_at": "2026-06-09T10:15:00Z"
      }
    ],
    "total": 1,
    "page": 1,
    "page_size": 20
  }
}
```

### 4.3 获取转写状态

```
GET /api/files/{file_id}/status
```

**响应：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "status": "transcribing",
    "progress": 45.5,
    "estimated_remaining_seconds": 180
  }
}
```

### 4.4 删除音频

```
DELETE /api/files/{file_id}
```

**响应：**

```json
{
  "code": 200,
  "message": "音频及关联数据已删除",
  "data": null
}
```

---

## 5. 智能问答 API

### 5.1 发起提问（RAG问答）

```
POST /api/chat
```

**请求体：**

```json
{
  "course_id": 1,
  "question": "老师上节课布置的作业是什么？",
  "conversation_id": null
}
```

**响应：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 42,
    "question": "老师上节课布置的作业是什么？",
    "answer": "根据上节课（云计算技术 第3讲）的内容，李教授布置了以下作业：\n\n1. **阅读作业**：阅读教材第5章\"虚拟化技术\"，重点理解KVM和Docker的区别\n2. **实践作业**：在本地搭建Docker环境，运行一个Nginx容器\n3. **提交时间**：下周三（6月16日）课前提交\n\n作业具体要求可以查看课件第45-48页。",
    "sources": [
      {
        "chunk_id": 128,
        "content": "本次作业：1. 阅读教材第5章虚拟化技术...",
        "start_time": 4980.0,
        "end_time": 5100.0
      },
      {
        "chunk_id": 132,
        "content": "下周三课前提交，大家不要忘记...",
        "start_time": 5220.0,
        "end_time": 5280.0
      }
    ],
    "conversation_id": "conv_abc123",
    "created_at": "2026-06-09T15:30:00Z"
  }
}
```

### 5.2 获取对话历史

```
GET /api/chat/history?course_id=1&page=1&page_size=50
```

**响应：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 42,
        "role": "user",
        "content": "老师上节课布置的作业是什么？",
        "created_at": "2026-06-09T15:30:00Z"
      },
      {
        "id": 43,
        "role": "assistant",
        "content": "根据上节课（云计算技术 第3讲）的内容...",
        "sources": [...],
        "created_at": "2026-06-09T15:30:05Z"
      }
    ],
    "total": 20,
    "page": 1,
    "page_size": 50
  }
}
```

### 5.3 清除对话历史

```
DELETE /api/chat/history?course_id=1
```

**响应：**

```json
{
  "code": 200,
  "message": "对话历史已清除",
  "data": null
}
```

---

## 6. 课程总结 API

### 6.1 生成/获取课程总结

```
GET /api/summary/{course_id}
```

**查询参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| refresh | Boolean | 否 | 是否重新生成（默认false） |

**响应：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "course_id": 1,
    "course_name": "云计算技术",
    "summary": "本课程涵盖云计算核心概念，包括IaaS/PaaS/SaaS服务模型、虚拟化技术、容器化部署、云原生架构等主题。重点讲解了Docker与Kubernetes的实际应用...",
    "key_points": [
      {
        "topic": "虚拟化技术",
        "importance": "high",
        "description": "理解Hypervisor和容器运行时的区别"
      },
      {
        "topic": "Docker基础",
        "importance": "high",
        "description": "镜像构建、容器管理、Dockerfile编写"
      },
      {
        "topic": "Kubernetes入门",
        "importance": "medium",
        "description": "Pod、Service、Deployment概念"
      }
    ],
    "homework": [
      {
        "content": "搭建Docker环境并运行Nginx容器",
        "deadline": "2026-06-16",
        "week": 3
      }
    ],
    "generated_at": "2026-06-09T16:00:00Z"
  }
}
```

---

## 7. 学习规划 API

### 7.1 生成/获取学习规划

```
GET /api/plan/{course_id}
```

**查询参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| refresh | Boolean | 否 | 是否重新生成（默认false） |
| days_until_exam | Integer | 否 | 距考试天数（用于倒推计划） |

**响应：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "course_id": 1,
    "plan_content": "# 云计算技术 学习计划\n\n## 第1周（6月10日-6月16日）\n### 目标\n- 掌握虚拟化基础概念\n- 完成Docker环境搭建\n\n### 学习内容\n1. 虚拟化技术原理（第1-2讲）\n2. Docker安装与基本使用（第3讲）\n\n### 重点复习\n- KVM vs Docker 架构差异\n- Dockerfile 编写规范\n\n## 第2周（6月17日-6月23日）\n...",
    "phases": [
      {
        "week": 1,
        "title": "虚拟化基础",
        "objectives": ["掌握虚拟化基础概念", "完成Docker环境搭建"],
        "key_topics": ["KVM", "Docker架构", "Dockerfile"],
        "estimated_hours": 6
      },
      {
        "week": 2,
        "title": "容器编排",
        "objectives": ["理解Kubernetes核心概念", "完成集群部署实验"],
        "key_topics": ["Pod", "Service", "Deployment", "Ingress"],
        "estimated_hours": 8
      }
    ],
    "generated_at": "2026-06-09T16:30:00Z"
  }
}
```

---

## 8. 知识库管理 API

### 8.1 构建知识库

```
POST /api/knowledge/build
```

**请求体：**

```json
{
  "course_id": 1
}
```

**响应：**

```json
{
  "code": 200,
  "message": "知识库构建任务已启动",
  "data": {
    "course_id": 1,
    "status": "building"
  }
}
```

### 8.2 查询知识库状态

```
GET /api/knowledge/{course_id}/status
```

**响应：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "course_id": 1,
    "status": "ready",
    "chunk_count": 450,
    "total_duration": 5400.0,
    "last_updated": "2026-06-09T10:15:00Z"
  }
}
```

### 8.3 删除知识库

```
DELETE /api/knowledge/{course_id}
```

**响应：**

```json
{
  "code": 200,
  "message": "知识库已删除",
  "data": null
}
```

---

## 9. 健康检查

### 9.1 系统健康检查

```
GET /api/health
```

**响应：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "status": "healthy",
    "version": "1.0.0",
    "services": {
      "database": "connected",
      "chromadb": "connected",
      "asr_service": "ready",
      "embedding_service": "ready",
      "deepseek_api": "available"
    },
    "timestamp": "2026-06-09T12:00:00Z"
  }
}
```

---

## 10. WebSocket 事件

### 10.1 连接

```
ws://localhost:8000/ws/{user_id}?token=<JWT_TOKEN>
```

### 10.2 推送事件

| 事件类型 | 方向 | 数据格式 |
|----------|------|----------|
| asr.progress | 服务端→客户端 | `{"type": "asr.progress", "file_id": 1, "progress": 45.5}` |
| asr.completed | 服务端→客户端 | `{"type": "asr.completed", "file_id": 1}` |
| asr.failed | 服务端→客户端 | `{"type": "asr.failed", "file_id": 1, "error": "..."}` |
| index.completed | 服务端→客户端 | `{"type": "index.completed", "course_id": 1, "chunk_count": 450}` |
| summary.completed | 服务端→客户端 | `{"type": "summary.completed", "course_id": 1}` |
```

---

## 11. API 错误码对照表

| 业务码 | HTTP状态码 | 说明 |
|--------|-----------|------|
| 10001 | 400 | 参数校验失败 |
| 10002 | 401 | Token 过期 |
| 10003 | 401 | Token 无效 |
| 10004 | 403 | 无权访问该课程 |
| 10005 | 404 | 课程不存在 |
| 10006 | 404 | 音频文件不存在 |
| 10007 | 413 | 文件大小超限 |
| 10008 | 415 | 不支持的音频格式 |
| 10009 | 429 | 请求频率超限 |
| 10010 | 500 | ASR 服务异常 |
| 10011 | 500 | DeepSeek API 异常 |
| 10012 | 503 | 知识库未就绪 |
