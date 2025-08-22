#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :   router.py
@Time    :   2025/08/15 17:26:40
@Author  :   SeeStars 
@Version :   1.0
@Desc    :   None
'''

from fastapi import APIRouter

from api.chat import qa_router
from api.upload_file import file_router
from api.embedding import kb_router

api_router = APIRouter()
api_router.include_router(qa_router, tags=["chat/问答"])
api_router.include_router(file_router, tags=["文件上传"], prefix="/files")
api_router.include_router(kb_router, tags=["知识库"], prefix="/kb")