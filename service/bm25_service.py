#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File    :   bm25_service.py
@Time    :   2025/08/22 21:11:27
@Author  :   SeeStars
@Version :   1.0
@Desc    :   None
"""
import logging
import traceback
from settings import settings
from typing import List, Tuple

logger = logging.getLogger(__name__)

UPLOAD_DIR = settings.UPLOAD_DIR
from model.bm25_index import BM25_REGISTRY


def bm25_search(
    query: str,
    kb_name: str,
    top_k: int = 5,
) -> Tuple[List[str], List[int], List[float]]:
    """
    @desc   : 使用 BM25 从知识库中检索
    @param  : query: 查询内容
    @param  : kb_name: 知识库名称
    @param  : top_k: 返回结果数量
    @return : (文本列表, id列表, 分数列表)
    """
    bm25_indexes = BM25_REGISTRY.get(kb_name)

    # if kb_name not in bm25_indexes:
    #     raise ValueError(f"知识库 {kb_name} 不存在")

    texts, ids, ranked_scores = bm25_indexes.search(query, top_k)

    return texts, ids, ranked_scores


def save_to_bm25_file(kb_name: str, ids: list[str], texts: list[str]):
    """
    @desc     : 存储知识库内容到json文件
    @param    : kb_name: str - 知识库名称
    @param    : ids: list[str] - 文档ID列表
    @param    : texts: list[str] - 文档内容列表
    @return   : None
    """

    try:
        bm25_indexes = BM25_REGISTRY.get(kb_name)
        bm25_indexes.add(ids, texts)
    except Exception as e:
        logger.error(f"保存 BM25 知识库 {kb_name} 时出错: {e}")

async def delete_by_file_bm25(file_name: list[str], kb_name: str):
    """
    @desc     : 从知识库中删除文档
    @param    : kb_name: str - 知识库名称
    @param    : ids: list[str] - 文档ID列表
    @return   : None
    """

    try:
        print(type(kb_name))
        bm25_indexes = BM25_REGISTRY.get(kb_name)
        bm25_indexes.delete_file(file_name)
    except Exception as e:
        logger.error(f"删除 BM25 知识库 {kb_name} 时出错: {e}")
        logger.error(traceback.format_exc())
        return False
    return True

def delete_kb_bm25(kb_name: str, ids: list[str]):
    """
    @desc     : 从知识库中删除文档
    @param    : kb_name: str - 知识库名称
    @param    : ids: list[str] - 文档ID列表
    @return   : None
    """

    pass