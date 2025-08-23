#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File    :   embedding.py
@Time    :   2025/08/17 16:00:58
@Author  :   SeeStars
@Version :   1.0
@Desc    :   None
"""
import os
import logging
import traceback
from fastapi import APIRouter
from settings import settings
from service.async_kb_service import store_files_concurrently
from service.kb_service import (
    delete_by_file,
    delete_kb,
    list_kb,
    list_kb_files,
    list_kb_knowledge,
    create_kb,
)

from libs.message import Message

logger = logging.getLogger(__name__)

kb_router = APIRouter()
UPLOAD_DIR = settings.UPLOAD_DIR


@kb_router.post("/store_file_chunks", summary="存储文件到向量库")
async def store_file_chunks_api(
    filename: list[str],
    kb_name: str = settings.DEFAULT_KNOWLEDGE_BASE,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
):
    """
    @description : 将文件切片并存储到指定的知识库
    """
    num_chunks, NOT_EXIST_FILES = await store_files_concurrently(
        filename,
        kb_name,
        chunk_size,
        chunk_overlap,
    )

    if NOT_EXIST_FILES:
        return Message.error(msg="以下文件未成功存储", data={"not_exist_files": NOT_EXIST_FILES})

    return Message.success(msg="文件已切片并存储到知识库", data={"chunks_count": num_chunks})


@kb_router.post("/create", summary="新建一个知识库")
async def create_kb_api(
    kb_name: str = settings.DEFAULT_KNOWLEDGE_BASE,
):
    """
    @description : 创建一个新的知识库
    """
    try:
        kb_path = await create_kb(kb_name)
        return Message.success(msg="知识库创建成功")
    except Exception as e:
        logger.error(f"创建知识库失败: {str(e)}")
        return Message.error(msg="创建知识库失败", data={"error": str(e)})


@kb_router.get("/list", summary="列出所有知识库")
async def list_kb_api():
    """
    @description : 列出所有知识库
    """
    try:
        kb_list = await list_kb()
        return Message.success(msg="知识库列表", data={"knowledge_bases": kb_list})
    except Exception as e:
        logger.error(f"列出知识库失败: {str(e)}")
        return Message.error(msg="列出知识库失败", data={"error": str(e)})


@kb_router.get("/file_list", summary="列出知识库中的文件")
async def list_files_in_kb_api(
    kb_name: str = settings.DEFAULT_KNOWLEDGE_BASE,
):
    """
    @description : 列出指定知识库中的所有文件
    """
    try:
        files_list = await list_kb_files(kb_name=kb_name)
        return Message.success(msg="文件列表", data={"files": files_list})
    except Exception as e:
        logger.error(f"列出文件失败: {str(e)}")
        return Message.error(msg="列出文件失败", data={"error": str(e)})


@kb_router.delete("/delete_file", summary="删除知识库中的文件")
async def delete_file_from_kb_api(
    filename: list[str],
    kb_name: str = settings.DEFAULT_KNOWLEDGE_BASE,
):
    """
    @description : 删除指定知识库中的文件,以及向量库中的知识
    """
    try:
        success = await delete_by_file(filename, kb_name)

        return Message.success(msg="文件已删除", data={"file": filename})
    except Exception as e:
        logger.error(f"删除文件失败: {str(e)}")
        logger.error(traceback.format_exc())
        return Message.error(msg="删除文件失败", data={"error": str(e)})


@kb_router.delete("/delete_kb", summary="删除知识库")
async def delete_kb_api(
    kb_name: str = settings.DEFAULT_KNOWLEDGE_BASE,
):
    """
    @description : 删除指定的知识库及其所有内容
    """
    try:
        success = await delete_kb(kb_name)
        if not success:
            return Message.error(msg="知识库不存在", data={"knowledge_base": kb_name})

        return Message.success(msg="知识库已删除", data={"knowledge_base": kb_name})
    except Exception as e:
        logger.error(f"删除知识库失败: {str(e)}")
        return Message.error(msg="删除知识库失败", data={"error": str(e)})


@kb_router.get("list_kb", summary="列出所有知识")
async def list_kb_api(kb_name: str = settings.DEFAULT_KNOWLEDGE_BASE):
    """
    @description : 列出指定知识库中的所有知识
    """
    try:
        knowledge_list = await list_kb_knowledge(kb_name)
        return Message.success(msg="知识列表", data={"knowledge": knowledge_list})
    except Exception as e:
        logger.error(f"列出知识失败: {str(e)}")
        return Message.error(msg="列出知识失败", data={"error": str(e)})
