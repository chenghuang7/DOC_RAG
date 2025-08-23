#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :   kb_service.py
@Time    :   2025/08/22 22:45:44
@Author  :   SeeStars 
@Version :   1.0
@Desc    :   None
'''

import os
import logging
import traceback
from service.chroma import list_knowledge
from service.chroma import delete_by_file_chroma, delete_kb_chroma
from service.bm25_service import delete_by_file_bm25, delete_kb_bm25

from settings import settings

logger = logging.getLogger(__name__)

UPLOAD_DIR = settings.UPLOAD_DIR

async def list_kb() -> list[str]:
    """
    @desc     : 列出所有知识库
    @return   : 知识库名称列表
    """
    return [d for d in os.listdir(UPLOAD_DIR) if os.path.isdir(os.path.join(UPLOAD_DIR, d))]


async def list_kb_files(kb_name: str) -> list[str]:
    """
    @desc     : 列出指定知识库中的所有文件
    @param    : kb_name: str - 知识库名称
    @return   : 文件名称列表
    """
    kb_path = os.path.join(UPLOAD_DIR, kb_name)
    if not os.path.exists(kb_path):
        return []

    return [f for f in os.listdir(kb_path) if os.path.isfile(os.path.join(kb_path, f)) and f != settings.BM25_INDEX_NAME]

async def list_kb_knowledge(kb_name: str):
    return await list_knowledge(kb_name)

async def create_kb(kb_name: str) -> str:
    """
    @desc     : 创建知识库的专属路径,并同步创建bm25的索引文件，json格式
    @param    : kb_name: str - 知识库名称
    @return   : 知识库的路径地址
    """
    
    kb_path = os.path.join(UPLOAD_DIR, kb_name)
    try:
        # 创建一个文件夹
        os.makedirs(kb_path, exist_ok=False)
        with open(os.path.join(kb_path, settings.BM25_INDEX_NAME), "w", encoding="utf-8") as f:
            f.write("{}")
    except FileExistsError:
        logger.error(f"知识库 {kb_name} 已存在")
        raise
    return kb_path

async def delete_by_ids():
    pass

async def delete_by_file(file_names: list[str], kb_name: str):
    """
    @desc     : 删除指定知识库中的文件
    @param    : filename: str - 文件名
    @param    : kb_name: str - 知识库名称
    @return   : bool - 删除是否成功
    """
    await delete_by_file_chroma(file_names, kb_name)
    await delete_by_file_bm25(file_names, kb_name)
    try :
        for filename in file_names:
            kb_path = os.path.join(UPLOAD_DIR, kb_name)
            file_path = os.path.join(kb_path, filename)

            if os.path.exists(file_path):
                os.remove(file_path)
    except Exception as e:
        logger.error(f"删除文件 {file_names} 失败: {e}")
        logger.error(traceback.format_exc())
        return False

    return True

async def delete_kb(kb_name: str):
    """
    @desc     : 删除指定的知识库及其所有内容
    @param    : kb_name: str - 知识库名称
    @return   : bool - 删除是否成功
    """
    success = await delete_kb_chroma(kb_name)
    # success &= await delete_kb_bm25(kb_name) # 不需要删除的操作，下边的一步会覆盖操作
    kb_path = os.path.join(UPLOAD_DIR, kb_name)

    if not os.path.exists(kb_path):
        return False

    for root, dirs, files in os.walk(kb_path, topdown=False):
        for name in files:
            os.remove(os.path.join(root, name))
        for name in dirs:
            os.rmdir(os.path.join(root, name))

    os.rmdir(kb_path)
    return True & success