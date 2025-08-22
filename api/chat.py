#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File    :   chat.py
@Time    :   2025/08/15 17:26:36
@Author  :   SeeStars
@Version :   1.0
@Desc    :   None
"""
import json
import logging
from datetime import datetime
from settings import settings
from fastapi import APIRouter, Body
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from service.prompt import DOC_RAG_PROMPT

from service.llm import get_llm_response
from service.chroma import recall_knowledge
logger = logging.getLogger(__name__)
qa_router = APIRouter()


class HMessage(BaseModel):
    role: str = Field(..., description="消息角色，'user' 或 'assistant'")
    content: str = Field("", description="消息内容")
    
@qa_router.post("/chat", status_code=200, summary="用户问答")
async def chat(
    query: str = Body(..., description="问题"),
    history: list[HMessage] = Body(None, description="对话历史"),
    knowledge_base: str = Body(settings.DEFAULT_KNOWLEDGE_BASE, description="用到的知识库"),
    session_id: int = Body(int(datetime.now().timestamp()), description="会话ID，时间戳"),
    stream: bool = Body(True, description="是否启用流式响应"),
):
    """
    @description : 进行用户的问答
    """
    knowledges, ids = await recall_knowledge(query, knowledge_base=knowledge_base, top_k=settings.TOP_K)
    knowledges_text = ""
    
    logger.info(f"查询到{len(knowledges)}条知识")

    for idx, knowledge in enumerate(knowledges):
        knowledges_text += f"{idx}、{knowledge}\n"

    async def process_chat(
        query,
        history,
        system_prompt=DOC_RAG_PROMPT.format(knowledges=knowledges_text, user_question=query),
        stream=stream,
    ):
        # 知识库溯源
        yield {"event": "start", "data": json.dumps([{id.split("/")[-1]: k}for k, id in zip(knowledges, ids)] , ensure_ascii=False)}
        text = ""
        async for response in get_llm_response(
            query=query,
            model=settings.TEXT_LLM,
            history=history,
            system_prompt=system_prompt,
            temperature=0.7,
            stream=stream,
        ):
            
            text += response
            yield {"event": "add", "data": json.dumps({"content": text}, ensure_ascii=False)}
        yield {"event": "finish", "data": json.dumps({"content": text}, ensure_ascii=False)}

    return EventSourceResponse(process_chat(query, history), media_type="text/event-stream")
