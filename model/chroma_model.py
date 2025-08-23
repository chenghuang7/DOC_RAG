#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File    :   chroma_model.py
@Time    :   2025/08/22 21:23:06
@Author  :   SeeStars
@Version :   1.0
@Desc    :   None
"""
import os
import chromadb
from settings import settings
from chromadb.utils import embedding_functions

chroma_client = chromadb.PersistentClient(path=".chroma")
os.environ["ANONYMIZED_TELEMETRY"] = "False"  # 关闭遥测
default_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name=settings.EMBEDDING_MODEL_LOCAL_PATH if settings.EMBEDDING_MODEL_LOCAL_PATH else settings.EMBEDDING_MODEL,
)

def get_chroma_collection(kb_name: str, embedding_model: str = None):
    '''
    @desc     : 获取或创建一个 Chroma Collection
    @param    : kb_name : 知识库名称
    @return   : Chroma Collection
    '''
    if embedding_model:
        custom_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=embedding_model,
        )
        return chroma_client.get_or_create_collection(name=kb_name, embedding_function=custom_ef)
    return chroma_client.get_or_create_collection(name=kb_name, embedding_function=default_ef)
