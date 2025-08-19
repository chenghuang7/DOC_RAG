#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :   settings.py
@Time    :   2025/08/15 17:26:50
@Author  :   Shouyi Xu 
@Version :   1.0
@Desc    :   None
'''

import os
from enum import Enum

from pydantic import Field, BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DESCRIPTION: str = """
备注

## 统一返回字段

### 格式

>JSON

### 返回参数

|字段|功能|类型|字段值|
|--|--|--|--|
|type|返回状态|str|'info','warning','error','success'|
|message|返回消息|str||
|data|返回数据|Object|根据不同接口|
|code|返回状态码|int|200:代表success,201:代表info,202:代表warn,3xx:代表error类型，根据不同接口|
    """
    API_PREFIX: str = Field("/api", description="所有api接口都有的前缀")
    API_PORT: int = Field(5510, description="API服务端口号")

    REDIS_HOST: str=Field("",description="")
    REDIS_PORT: int=Field(9531)
    REDIS_PASSWD: str=Field("",description="")
    REDIS_USER: str = ""
    REDIS_DB: int = 8

    LLM_BASE_URL: str = Field("", description="LLM服务的基础URL")
    CHATGLM_API_KEY: str = Field("", description="ChatGLM API Key")

    UPLOAD_DIR: str = Field("uploads", description="文件上传目录")
    
    IMAGE_MODEL: str = Field("glm-4.5v", description="默认的图像识别模型")
    
    TEXT_LLM: str = Field("glm-4", description="默认的文本生成模型")
    EMBEDDING_MODEL: str = Field("BAAI/bge-large-zh-v1.5", description="默认的文本嵌入模型")
    EMBEDDING_MODEL_LOCAL_PATH: str|None = Field(None, description="默认的文本嵌入模型本地路径")

    TOP_K: int = Field(15, description="召回知识的最大数量")
    
    DEFAULT_KNOWLEDGE_BASE: str = Field("default", description="默认的知识库名称")
    
    MAX_KEYWORDS: int = Field(5, description="最大关键词数量")
    NUMS_KNOWLEDGE: int = Field(15, description="每个知识库的最大知识数量")
    KEYWORDS_DELAY: float = Field(0.2, description="关键词提取延迟时间，单位秒")
    MAX_KNOWLEDGE: int = Field(20, description="最大知识数量")

    # all_knowledge = 
    # all_knowledge = max(NUMS_KNOWLEDGE, MAX_KNOWLEDGE)

    COMMON_RESOURCE_DIR: str = Field(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources"),
        description="公共资源目录",
    )
    COMMON_STATIC_DIR: str = Field(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "static"),
        description="公共静态资源目录",
    )
    SYSTEM_BASE_DIR: str = Field(
        os.path.dirname(os.path.abspath(__file__)),
        description="系统的根目录",
    )

settings = Settings(
        _case_sensitive=True,
        _env_file=os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"),
        _env_file_encoding="utf-8",
    )
import json

for k,v in json.loads(settings.json()).items():
    print(k,":",v)

