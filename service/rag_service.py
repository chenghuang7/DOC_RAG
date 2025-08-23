#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File    :   rag_service.py
@Time    :   2025/08/22 21:19:17
@Author  :   SeeStars
@Version :   1.0
@Desc    :   None
"""
import os
import asyncio
import logging
import traceback
from settings import settings
from typing import List, Tuple
from service.chroma import search_from_chroma
from service.bm25_service import bm25_search
from service.llm import get_llm_response
from service.prompt import search_key_prompt
from langchain.text_splitter import RecursiveCharacterTextSplitter
from service.file_process import read_file_content
from model.chroma_model import get_chroma_collection
from service.bm25_service import save_to_bm25_file

logger = logging.getLogger(__name__)


async def store_to_knowledge_base(
    filenames: list[str],
    kb_name: str = settings.DEFAULT_KNOWLEDGE_BASE,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
    embedding_model: str = None,
):
    """
    @desc     : 将文件存储到向量库
    @param    : 上传的文件的列表
    """
    collection = get_chroma_collection(kb_name, embedding_model)

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
            all_metadatas.append({"file_name": filename.split("/")[-1], "chunk_index": i})

    logger.info(f"准备存储 {len(all_chunks)} 个文本块到知识库 '{kb_name}'")

    await asyncio.gather(
        asyncio.to_thread(collection.add, documents=all_chunks, ids=all_ids, metadatas=all_metadatas),
        asyncio.to_thread(save_to_bm25_file, kb_name, all_ids, all_chunks),
    )

    return NOT_EXIST_FILES if len(NOT_EXIST_FILES) > 0 else None, len(all_chunks)


async def recall_knowledge(
    query: str,
    kb_name: str = settings.DEFAULT_KNOWLEDGE_BASE,
    top_k: int = settings.TOP_K,
) -> Tuple[List[str], List[int]]:
    """
    @desc     : 从知识库中召回相关内容
    @param    : query: 查询内容
    @param    : kb_name: 知识库名称
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
                k, i, d = search_from_chroma(keyword, kb_name, current_num)

                logger.debug(f"关键词 '{keyword}' chro召回 {len(k)} 条知识")
                texts, ids, ranked_scores = bm25_search(keyword, kb_name, current_num)
                logger.debug(f"关键词 '{keyword}' bm25召回 {len(texts)} 条知识")

                knowledge_list.extend(k)
                knowledge_list.extend(texts)
                idx_list.extend(i)
                idx_list.extend(ids)

                num_knowledges = max(int(num_knowledges * (1 - settings.KEYWORDS_DELAY)), 1)

            except Exception as e:
                logger.error(f"关键词 '{keyword}' 搜索失败: {str(e)}")
                logger.error(traceback.format_exc())
                continue

        return _deduplicate_knowledge(knowledge_list, idx_list, ans_top_k)

    except Exception as e:
        logger.error(f"知识召回过程异常: {str(e)}")
        logger.error(traceback.format_exc())
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
        logger.error(traceback.format_exc())
        return []


def _deduplicate_knowledge(
    knowledge_list: List[str],
    idx_list: List[int],
    top_k: int,
) -> Tuple[List[str], List[int]]:
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

    dedup_knowledge = list(unique_knowledge.values())[:top_k]
    dedup_ids = list(unique_knowledge.keys())[:top_k]

    return dedup_knowledge, dedup_ids
