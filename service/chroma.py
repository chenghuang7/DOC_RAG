#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File    :   chroma.py
@Time    :   2025/08/15 17:26:22
@Author  :   Shouyi Xu
@Version :   1.0
@Desc    :   None
"""
import os
import logging
import chromadb
from typing import List
import asyncio

logger = logging.getLogger(__name__)

from langchain.text_splitter import RecursiveCharacterTextSplitter
from chromadb.utils import embedding_functions

from settings import settings
from service.file_process import read_file_content
from service.llm import get_llm_response
from service.prompt import search_key_prompt

UPLOAD_DIR = settings.UPLOAD_DIR
os.environ["ANONYMIZED_TELEMETRY"] = "False" # 关闭遥测
chroma_client = chromadb.PersistentClient(path=".chroma")

default_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name=settings.EMBEDDING_MODEL_LOCAL_PATH if settings.EMBEDDING_MODEL_LOCAL_PATH else settings.EMBEDDING_MODEL,
)

async def store_to_knowledge_base(
    filenames: list[str],
    knowledge_base: str = settings.DEFAULT_KNOWLEDGE_BASE,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
    embedding_model: str = None,
):
    """
    @desc     : 将文件存储到向量库
    @param    : 上传的文件的列表
    """
    if embedding_model:
        custom_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=embedding_model,
        )
        collection = chroma_client.get_or_create_collection(
            name=knowledge_base,
            embedding_function=custom_ef,
        )
    else:
        collection = chroma_client.get_or_create_collection(
            name=knowledge_base,
            embedding_function=default_ef,
        )

    all_chunks = []
    all_ids = []
    all_metadatas = []

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    NOT_EXIST_FILES = []
    for filename in filenames:
        file_path = filename
        if not os.path.exists(file_path):
            NOT_EXIST_FILES.append(filename)
            continue

        content = await read_file_content(file_path)

        chunks = await asyncio.to_thread(splitter.split_text, content)

        for i, chunk in enumerate(chunks):
            all_chunks.append(f"{chunk}")
            all_ids.append(f"{filename}_{i}")
            all_metadatas.append({"file_name": filename})

    logger.info(f"准备存储 {len(all_chunks)} 个文本块到知识库 '{knowledge_base}'")

    await asyncio.to_thread(collection.add, documents=all_chunks, ids=all_ids, metadatas=all_metadatas)

    return NOT_EXIST_FILES if len(NOT_EXIST_FILES) > 0 else None, len(all_chunks)


def search_from_knowledge_base(
    query: str,
    knowledge_base: str = settings.DEFAULT_KNOWLEDGE_BASE,
    top_k: int = 5,
):
    """
    @desc     : 从向量库中搜索
    @param    : query: 查询内容
    @param    : knowledge_base: 知识库名称
    @param    : top_k: 返回的结果数量
    """
    collection = chroma_client.get_collection(name=knowledge_base)
    results = collection.query(query_texts=[query], n_results=top_k)

    return results["documents"][0], results["ids"][0]


async def recall_knowledge(
    query: str,
    knowledge_base: str = settings.DEFAULT_KNOWLEDGE_BASE,
    top_k: int = settings.TOP_K,
) -> List[str]:
    """
    @desc     : 从知识库中召回相关内容
    @param    : query: 查询内容
    @param    : knowledge_base: 知识库名称
    @param    : top_k: 返回的最大结果数量
    @return   : 去重后的知识列表，最多包含top_k条记录
    """

    ans_top_k = top_k
    top_k = top_k * 2

    try:
        keywords = await _extract_keywords(query)
        if not keywords:
            logger.warning("未提取到有效关键词")
            return []

        knowledge_list = []
        idx_list = []
        initial_num = min(settings.NUMS_KNOWLEDGE if settings.NUMS_KNOWLEDGE > 0 else settings.MAX_KNOWLEDGE, top_k)
        num_knowledges = initial_num

        for idx, keyword in enumerate(keywords):
            if len(knowledge_list) >= top_k or num_knowledges <= 0:
                break

            current_num = min(num_knowledges, top_k - len(knowledge_list))

            try:
                k, i = search_from_knowledge_base(keyword, knowledge_base, current_num)
                logger.debug(f"关键词 '{keyword}' 召回 {len(k)} 条知识")

                knowledge_list.extend(k)
                idx_list.extend(i)

                num_knowledges = max(int(num_knowledges * (1 - settings.KEYWORDS_DELAY)), 1)

            except Exception as e:
                logger.error(f"关键词 '{keyword}' 搜索失败: {str(e)}")
                continue

        return _deduplicate_knowledge(knowledge_list, idx_list, ans_top_k)

    except Exception as e:
        logger.error(f"知识召回过程异常: {str(e)}")
        return []


async def _extract_keywords(query: str) -> List[str]:
    """
    @desc     : 从查询中提取关键词
    @param    : query: 查询内容
    @return   : 提取到的关键词列表
    """
    try:
        keywords = []
        async for response in get_llm_response(
            query=query,
            system_prompt=search_key_prompt,
            model=settings.TEXT_LLM,
            stream=False,
        ):
            keywords.extend(response.split(","))

        keywords = [kw.strip() for kw in keywords if kw.strip()]
        return keywords[: settings.MAX_KEYWORDS]

    except Exception as e:
        logger.error(f"关键词提取失败: {str(e)}")
        return []


def _deduplicate_knowledge(
    knowledge_list: List[str],
    idx_list: List[int],
    top_k: int,
) -> List[str]:
    """
    @desc     : 知识去重并限制数量
    @param    : knowledge_list: 知识列表
    @param    : idx_list: 知识对应的索引列表
    @param    : top_k: 返回的最大数量
    @return   : 去重后的知识列表
    """
    unique_knowledge = {}
    for k, idx in zip(knowledge_list, idx_list):
        if idx not in unique_knowledge:
            unique_knowledge[idx] = k

    return list(unique_knowledge.values())[:top_k]


async def delete_knowledge(file_name: str, knowledge_base: str):
    """
    @desc     : 删除指定的知识
    @param    : file_name: 文件名
    """
    file_name = file_name.split("\\")[-1]
    collection = chroma_client.get_collection(name=knowledge_base)
    collection.delete(where={"file_name": {"$eq": file_name}})
async def delete_all_knowledge(knowledge_base: str):
    """
    @desc     : 删除指定的知识
    @param    : knowledge_base: 知识库名称
    """
    chroma_client.delete_collection(name=knowledge_base)

async def list_knowledge(knowledge_base: str) -> list[str]:
    """
    @desc     : 列出指定知识库中的所有知识
    @param    : knowledge_base: str - 知识库名称
    @return   : 知识列表
    """
    collection = chroma_client.get_collection(name=knowledge_base)
    # knowledge_lists = collection.get()
    all_docs = collection.get(
        ids=None,
        include=["documents", "metadatas"]
    )
    
    return all_docs