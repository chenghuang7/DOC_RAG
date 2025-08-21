# DOCRAG

DOCRAG 是一个文档问答（RAG）系统，支持 LLM 与向量检索集成。

> **注意**: 当前 Redis 暂未使用。

---

## 配置环境变量 (.env)

```bash
# Redis 配置（暂未使用）
REDIS_HOST=172.23.162.242
REDIS_PORT=9531
REDIS_PASSWD=""
REDIS_USER=""
REDIS_DB=8

# LLM 配置
LLM_BASE_URL="https://open.bigmodel.cn/api/paas/v4"
VLM_BASE_URL="https://open.bigmodel.cn/api/paas/v4"
CHATGLM_API_KEY=""
TEXT_LLM="glm-4.5"

# 向量模型配置
EMBEDDING_MODEL="BAAI/bge-large-zh-v1.5"
EMBEDDING_MODEL_LOCAL_PATH=""  # 公网环境可以不设置，需能访问 HuggingFace
TOP_K=15
DEFAULT_KNOWLEDGE_BASE="default"

# 知识库参数
MAX_KEYWORDS=5
NUMS_KNOWLEDGE=15
KEYWORDS_DELAY=0.2
MAX_KNOWLEDGE=20

# 文件上传目录
UPLOAD_DIR="uploads"
```

---

## 部署指南

### 1. 公网环境

```bash
docker pull seestars/docrag:v1.3.0
docker run -d --name doc-rag -v .env:/app/.env seestars/docrag:v1.3.0
```

### 2. 离线环境（需要挂载本地向量模型）

```bash
docker run -d --name doc-rag \
  -v .env:/app/.env \
  -v xxx-emb-model:/model \
  seestars/docrag:v1.3.0
```

---

### 3. 一键部署（Docker Compose）

#### 目录结构

```bash
.
├── bge-large-zh-v1.5
├── docker-compose.yml
└── .env
```

#### docker-compose.yml 示例

```yaml
version: '3.8'

services:
  docrag:
    container_name: docrag_prod
    image: docrag:x.x.x
    restart: always
    ports:
      - "5510:5510"
    volumes:
      - .env:/app/.env
      - ./bge-large-zh-v1.5:/model
      # 如果需要数据持久化，可挂载如下路径
      # - .chroma:/app/.chroma
```

> **提示**: 若希望知识库数据持久化，挂载 `.chroma` 路径即可。
