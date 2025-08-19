#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File    :   file_process.py
@Time    :   2025/08/15 17:26:28
@Author  :   Shouyi Xu
@Version :   1.0
@Desc    :   None
"""

import os
import fitz
import asyncio
import aiofiles
import docx
import logging
import re
from asyncio import Semaphore
from pdf2image import convert_from_path

from service.vlm import get_image_text

logger = logging.getLogger(__name__)

async def read_file_content(file_path: str) -> str:
    """
    @desc     : 读取文件内容
    @param    : file_path: 文件路径
    @return   : 文件内容字符串
    """

    logger.info(f"正在读取文件: {file_path}")
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".txt" or ext == ".md":
        async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
            return await f.read()
        # with open(file_path, "r", encoding="utf-8") as f:
        #     return f.read()

    elif ext == ".pdf":
        text = await read_pdf_content(file_path)
        return text

    elif ext == ".docx":
        doc = docx.Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs])

    else:
        raise ValueError(f"不支持的文件类型: {ext}")


async def split_pdf(filename: str, output_dir: str, max_concurrent: int = 8) -> list[str]:
    '''
    @desc     : 将 PDF 文件按页拆分为多个单独的 PDF 文件
    @param    : filename: PDF 文件路径
    @param    : output_dir: 输出目录
    @return   : 拆分后的 PDF 文件列表
    '''
    try:
        os.makedirs(output_dir, exist_ok=True)
        pages = convert_from_path(filename, dpi=300)
    except Exception as e:
        logger.error(f"pdf转图片失败: {e}")
    tasks = []

    saved_files = []
    sem = Semaphore(max_concurrent)

    async def save_page_image(page, image_path: str, sem: Semaphore):
        async with sem:
            # page.save 是阻塞操作，用 to_thread 放到线程池
            await asyncio.to_thread(page.save, image_path, "PNG")
            logger.info(f"已保存图片: {image_path}")

    for i, page in enumerate(pages):
        image_path = os.path.join(output_dir, f"page_{i+1}.png")
        saved_files.append(image_path)
        tasks.append(save_page_image(page, image_path, sem))

    await asyncio.gather(*tasks)
    
    logger.info(f"共 {len(pages)} 页已保存到 {output_dir} 文件夹")

async def ocr_image(image_path: str, max_concurrent: int = 5) -> str:
    """
    对图片进行 OCR 识别（并发控制）

    :param image_path: 图片文件夹路径
    :param max_concurrent: 最大并发数
    :return: 识别出的文本内容
    """
    logger.info(f"正在对图片进行 OCR 识别: {image_path}")
    
    files = [f for f in os.listdir(image_path) if f.endswith('.png')]
    sorted_files = sorted(files, key=lambda x: int(re.search(r'\d+', x).group()))
    
    sem = asyncio.Semaphore(max_concurrent)

    async def ocr_worker(img_file: str) -> str:
        async with sem:
            img_path = os.path.join(image_path, img_file)
            text = await get_image_text(img_path)
            logger.info(f"已识别图片 {img_file} 的文字内容")
            return text

    tasks = [ocr_worker(f) for f in sorted_files]
    results = await asyncio.gather(*tasks)

    return "".join(results)

async def read_pdf_content(file_path: str) -> str:
    """
    读取 PDF 文件内容

    :param file_path: PDF 文件路径
    :return: PDF 文本内容
    """
    logger.info(f"正在将文件{file_path}转换成图片")
    output_path = file_path.replace(".pdf", "")
    await split_pdf(file_path, output_path)
    text = await ocr_image(output_path)

    return text
