#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File    :   bm25_index.py
@Time    :   2025/08/22 21:11:36
@Author  :   SeeStars
@Version :   1.0
@Desc    :   None
"""

import os
import json
import logging
from rank_bm25 import BM25Okapi
from collections import OrderedDict

logger = logging.getLogger(__name__)

from settings import settings

UPLOAD_DIR = settings.UPLOAD_DIR


class BM25Manager:
    """
    @name     : BM25Manager
    @desc     : 管理单个知识库的 BM25 索引
    """

    def __init__(self, kb_name: str, bm25_file: str = settings.BM25_INDEX_NAME):
        self.kb_name = kb_name
        self.bm25_file = os.path.join(UPLOAD_DIR, kb_name, bm25_file)

        self.docs = []
        self.tokenized_docs = []
        self.bm25 = None
        self.load_index()

    def load_index(self):
        """
        @description : 加载文件
        """
        if os.path.exists(self.bm25_file):
            with open(self.bm25_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.docs = list(data.values())
            self.ids = list(data.keys())
        else:
            self.docs = []
            self.ids = []

        self.tokenized_docs = [doc.split() for doc in self.docs]
        if self.tokenized_docs:
            self.bm25 = BM25Okapi(self.tokenized_docs)

    def add(self, ids: list[str], texts: list[str]):
        """
        @description : 新增文档，同时更新 JSON 文件和内存索引
        """
        # 更新 JSON 文件
        if os.path.exists(self.bm25_file):
            with open(self.bm25_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                logger.info(f"加载 BM25 知识库 {self.kb_name}，当前记录数 {len(data)}")
        else:
            data = {}

        for i, t in zip(ids, texts):
            data[str(i)] = t

        with open(self.bm25_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"BM25 知识库 {self.kb_name} 已更新，新增 {len(texts)} 条记录")

        # 更新内存
        self.docs.extend(texts)
        self.tokenized_docs = [doc.split() for doc in self.docs]
        self.bm25 = BM25Okapi(self.tokenized_docs)

    def search(self, query: str, top_k: int = 5, min_score: float = 0.1):
        """
        @desc     : BM25 查询
        @param    : query: 查询内容
        @param    : top_k: 返回前 top_k 个结果
        @return   : (文本列表, id列表, 分数列表)
        """
        if not self.bm25:
            return [], [], []

        tokenized_query = query.split()
        scores = self.bm25.get_scores(tokenized_query)

        # 排序，得到索引和分数
        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)[:top_k]

        docs, ids, final_scores = [], [], []
        for i, score in ranked[:top_k]:
            if score >= min_score:
                docs.append(self.docs[i])
                ids.append(self.ids[i])
                final_scores.append(score)
        return docs, ids, final_scores
    
    def delete_file(self, file_names: list[str]):
        """
        @desc     : 删除指定文件的文档
        @param    : file_name: 要删除的文件名列表
        """
        if not os.path.exists(self.bm25_file):
            return

        with open(self.bm25_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        for file_name in file_names:
            temp_num = 0
            for ids_name in list(data.keys()):
                if file_name in ids_name:
                    del data[ids_name]
                    temp_num +=1
            logger.info(f"从 BM25 知识库 {self.kb_name} 删除文档文件: {file_name}, 共{temp_num}条")

        with open(self.bm25_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        self.load_index()
    def delete_ids(self, ids: list[str]):
        """
        @desc     : 删除指定 ID 的文档
        @param    : ids: 要删除的文档 ID 列表
        """
        if not os.path.exists(self.bm25_file):
            return

        with open(self.bm25_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        for id in ids:
            if str(id) in data:
                del data[str(id)]
                logger.info(f"从 BM25 知识库 {self.kb_name} 删除文档 ID: {id}")

        with open(self.bm25_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        self.load_index()


class BM25Registry:
    """
    @name     : BM25Registry
    @desc     : 全局 BM25 缓存管理器（支持多知识库、LRU 缓存）
    """

    def __init__(self, max_cached_kb: int = settings.MAX_CACHED_KB):
        self.max_cached_kb = max_cached_kb
        self.cache: OrderedDict[str, BM25Manager] = OrderedDict()

    def get(self, kb_name: str) -> BM25Manager:
        # 如果缓存里有，提升到最新
        if kb_name in self.cache:
            self.cache.move_to_end(kb_name)
            return self.cache[kb_name]

        # 不在缓存 → 延迟加载
        manager = BM25Manager(kb_name)
        self.cache[kb_name] = manager
        self.cache.move_to_end(kb_name)

        # 超过上限 → 移除最久未使用的
        if len(self.cache) > self.max_cached_kb:
            removed_kb, _ = self.cache.popitem(last=False)
            logger.info(f"释放 BM25 索引: {removed_kb}")

        return manager


# 全局唯一实例，可在 service 层直接调用
BM25_REGISTRY = BM25Registry(max_cached_kb=3)
