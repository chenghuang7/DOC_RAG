#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :   async_kb_service.py
@Time    :   2025/08/18 20:14:28
@Author  :   SeeStars 
@Version :   1.0
@Desc    :   None
'''
import asyncio
from asyncio import Semaphore
from typing import List, Tuple
from service.rag_service import store_to_knowledge_base

async def store_file_worker(
    filename: str,
    kb_name: str,
    chunk_size: int,
    chunk_overlap: int,
    sem: Semaphore
) -> Tuple[str, int, list]:
    async with sem:
        try:
            not_exist_files, num_chunks = await store_to_knowledge_base(
                [filename], kb_name, chunk_size, chunk_overlap
            )
            return filename, num_chunks, not_exist_files
        except Exception:
            return filename, 0, [filename]


async def store_files_concurrently(
    filenames: List[str],
    kb_name: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
    max_concurrent: int = 8
) -> Tuple[int, List[str]]:
    sem = Semaphore(max_concurrent)
    tasks = [store_file_worker(fn, kb_name, chunk_size, chunk_overlap, sem) for fn in filenames]
    results = await asyncio.gather(*tasks)
    total_chunks = sum(nc for _, nc, _ in results)
    not_exist_files = [fn for fn, _, ne in results if ne]
    return total_chunks, not_exist_files
