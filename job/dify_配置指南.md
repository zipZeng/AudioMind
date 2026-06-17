# Dify 配置指南 — AudioMind 核心

> 这一步是项目的**核心**。Dify 配置好了，项目就完成了 70%。

---

## 一、创建知识库

1. 登录 [Dify 控制台](https://cloud.dify.ai)（或用学校自建的 Dify）
2. 左侧菜单 → **知识库** → 右上角 **创建知识库**
3. 填写：
   - 名称：`AudioMind 课堂录音`
   - 描述：存储课堂转写文本
4. 创建完成后，记下知识库 ID（URL 里的那串字符）

---

## 二、创建 Chatflow（核心）

1. 左侧菜单 → **工作室** → **从空白创建** → 选择 **Chatflow**
2. 画布上拖入以下 4 个节点，按顺序连线：

```
┌────────┐    ┌──────────┐    ┌─────┐    ┌──────────┐
│  开始   │───→│ 知识检索  │───→│ LLM │───→│ 直接回复  │
└────────┘    └──────────┘    └─────┘    └──────────┘
```

### 节点配置

#### 节点 1：开始
- 无需配置，保留默认

#### 节点 2：知识检索
- 知识库：选择上面创建的 `AudioMind 课堂录音`
- 检索设置：
  - Top-K：**5**
  - 分数阈值：**0.5**
  - 召回策略：**混合检索**（向量 + 关键词）

#### 节点 3：LLM
- 模型：DeepSeek-V3 或 DeepSeek-R1（便宜且效果好）
- System Prompt：

```
你是一个课堂录音智能助手，帮助大学生复习课程内容。

你的知识来源是学生上传的课堂录音转写文本。

回答规则：
1. 始终使用简体中文
2. 如果知识库中有相关答案，基于知识库内容回答
3. 如果知识库中没有相关内容，如实说"课堂录音中未找到相关信息"
4. 回答时注明信息来源（如"根据X月X日的课堂录音..."）
5. 如果问题是关于作业、考试等，给出具体内容而非笼统描述
```

- Temperature：0.3
- 上下文：勾选「知识检索」节点的输出

#### 节点 4：直接回复
- 输出变量：选择 LLM 节点的 `text` 输出

---

## 三、测试 Chatflow

在 Chatflow 编辑页面右侧的「预览」面板中测试：

```
你：昨天老师布置了什么作业？
AI：根据昨天的课堂录音，老师布置了第三章的习题1-5题...
```

确认能正确从知识库检索并回答后，点 **发布**。

---

## 四、获取 API Key

1. 发布后，左侧菜单 → **API 访问**
2. 复制 **API Secret Key**（格式 `app-xxxxxxxxxxxxx`）
3. 记下 **API Endpoint**（通常是 `https://cloud.dify.ai/v1`）

---

## 五、配置到项目

编辑 `docker-compose.yml` 或 `.env`：

```env
DIFY_API_URL=https://cloud.dify.ai/v1
DIFY_API_KEY=app-xxxxxxxxxxxxx
DIFY_DATASET_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
OPENAI_API_KEY=sk-xxxxxxxxxxxxx
```

---

## 六、Dify 知识库自动写入

后端 `/upload` 接口在转写完成后，自动调用以下 Dify API 将文本推入知识库：

```
POST /v1/datasets/{dataset_id}/document/create-by-text
Authorization: Bearer {DIFY_API_KEY}
Content-Type: application/json

{
  "name": "2024-03-15_软件工程课.wav",
  "text": "转写后的全文...",
  "indexing_technique": "high_quality",
  "process_rule": { "mode": "automatic" }
}
```

Dify 收到后自动：
1. 按语义分段
2. 调用 Embedding 模型向量化
3. 存入知识库
4. 立即可检索
