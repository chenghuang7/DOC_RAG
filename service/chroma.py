#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File    :   chroma.py
@Time    :   2025/08/15 17:26:22
@Author  :   SeeStars
@Version :   1.0
@Desc    :   None
"""
import logging
from model.chroma_model import chroma_client
from settings import settings

logger = logging.getLogger(__name__)
UPLOAD_DIR = settings.UPLOAD_DIR


def search_from_chroma(
    query: str,
    kb_name: str = settings.DEFAULT_KNOWLEDGE_BASE,
    top_k: int = 5,
):
    """
    @desc     : 从向量库中搜索
    @param    : query: 查询内容
    @param    : kb_name: 知识库名称
    @param    : top_k: 返回的结果数量
    """
    collection = chroma_client.get_collection(name=kb_name)
    results = collection.query(query_texts=[query], n_results=top_k)

    return results["documents"][0], results["ids"][0], results["distances"][0]


async def delete_by_file_chroma(file_name: list[str], kb_name: str):
    """
    @desc     : 删除指定的知识
    @param    : file_name: 文件名
    """
    for name in file_name:
        name = name.split("/")[-1]
        collection = chroma_client.get_collection(name=kb_name)
        collection.delete(where={"file_name": {"$eq": name}})


async def delete_kb_chroma(kb_name: str):
    """
    @desc     : 删除指定的知识
    @param    : kb_name: 知识库名称
    """
    try :
        chroma_client.delete_collection(name=kb_name)
    except Exception as e:
        logger.error(f"删除知识库 {kb_name} 失败: {e}")
        return False
    return True


async def list_knowledge(kb_name: str) -> list[str]:
    """
    @desc     : 列出指定知识库中的所有知识
    @param    : kb_name: str - 知识库名称
    @return   : 知识列表
    """
    collection = chroma_client.get_collection(name=kb_name)
    # knowledge_lists = collection.get()
    all_docs = collection.get(ids=None, include=["documents", "metadatas"])
    for doc, meta in zip(all_docs["documents"], all_docs["metadatas"]):
        logger.debug(f"Chroma 知识库 {meta['file_name']} 中的文档: {doc[:10]}...")
    return all_docs
