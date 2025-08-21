#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File    :   upload_file.py
@Time    :   2025/08/17 16:01:04
@Author  :   SeeStars
@Version :   1.0
@Desc    :   None
"""

import os
import time
import shutil
from typing import List
from libs.message import Message
from fastapi import APIRouter, File, UploadFile

from settings import settings

file_router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@file_router.post("/upload/", summary="上传文件")
async def upload_files(
    files: List[UploadFile] = File(...),
    knowledge_base: str = settings.DEFAULT_KNOWLEDGE_BASE,
):
    """
    @description : 上传文件
    """
    file_paths = []
    for file in files:
        file_location = os.path.join(UPLOAD_DIR, knowledge_base, str(int(time.time() * 100)) + "-" + file.filename)
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        file_paths.append(file_location)
    return Message.success(msg="文件上传成功", data={"file_paths": file_paths})
