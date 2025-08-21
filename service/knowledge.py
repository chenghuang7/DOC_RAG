#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File    :   knowledge.py
@Time    :   2025/08/17 16:02:31
@Author  :   SeeStars
@Version :   1.0
@Desc    :   None
"""

import os
from settings import settings

UPLOAD_DIR = settings.UPLOAD_DIR


async def create_kb_path(knowledge_base: str) -> str:
    """
    @desc     : 创建知识库的专属路径
    @param    : knowledge_base: str - 知识库名称
    @return   : 知识库的路径地址
    """
    kb_path = os.path.join(UPLOAD_DIR, knowledge_base)
    os.makedirs(kb_path, exist_ok=True)
    return kb_path

async def list_knowledge_bases() -> list[str]:
    """
    @desc     : 列出所有知识库
    @return   : 知识库名称列表
    """
    return [d for d in os.listdir(UPLOAD_DIR) if os.path.isdir(os.path.join(UPLOAD_DIR, d))]

async def list_files_in_knowledge_base(knowledge_base: str) -> list[str]:
    """
    @desc     : 列出指定知识库中的所有文件
    @param    : knowledge_base: str - 知识库名称
    @return   : 文件名称列表
    """
    kb_path = os.path.join(UPLOAD_DIR, knowledge_base)
    if not os.path.exists(kb_path):
        return []

    return [f for f in os.listdir(kb_path) if os.path.isfile(os.path.join(kb_path, f))]

async def delete_file(filename: str, knowledge_base: str) -> bool:
    """
    @desc     : 删除指定知识库中的文件
    @param    : filename: str - 文件名
    @param    : knowledge_base: str - 知识库名称
    @return   : bool - 删除是否成功
    """
    kb_path = os.path.join(UPLOAD_DIR, knowledge_base)
    file_path = os.path.join(kb_path, filename)

    if not os.path.exists(file_path):
        return False

    os.remove(file_path)
    return True

async def delete_knowledge_base(knowledge_base: str) -> bool:
    """
    @desc     : 删除指定的知识库及其所有内容
    @param    : knowledge_base: str - 知识库名称
    @return   : bool - 删除是否成功
    """
    kb_path = os.path.join(UPLOAD_DIR, knowledge_base)

    if not os.path.exists(kb_path):
        return False

    for root, dirs, files in os.walk(kb_path, topdown=False):
        for name in files:
            os.remove(os.path.join(root, name))
        for name in dirs:
            os.rmdir(os.path.join(root, name))

    os.rmdir(kb_path)
    
    return True

