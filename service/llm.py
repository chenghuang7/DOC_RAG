#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File    :   llm.py
@Time    :   2025/08/15 18:04:36
@Author  :   Shouyi Xu
@Version :   1.0
@Desc    :   调用LLM服务的函数
"""

import os
from settings import settings
from openai import AsyncOpenAI
import logging

logger = logging.getLogger(__name__)
api_key = os.getenv("CHATGLM_API_KEY", settings.CHATGLM_API_KEY)


async def get_llm_response(
    query: str,
    model: str = settings.TEXT_LLM,
    history: list[dict] = None,
    system_prompt: str = "You are a helpful assistant.",
    temperature: float = 0.7,
    stream: bool = False,
):
    """
    @desc     : 得到大模型的回答，支持流式和非流式响应
    @param    : query: 用户的查询内容
    @param    : model: 使用的模型名称
    @param    : temperature: 控制生成文本的随机性
    @param    : stream: 是否启用流式响应
    @return   : 非流式返回完整回答字符串；流式返回异步生成器
    """

    llm_client = AsyncOpenAI(
        api_key=api_key,
        base_url=settings.LLM_BASE_URL,
    )
    messages = [{"role": "system", "content": system_prompt}]
    if history:
        messages.extend(history)

    messages.append({"role": "user", "content": query})

    try:
        async for chunk in process_response(llm_client, model, messages, temperature, stream):
            yield chunk
    except Exception as e:
        print(f"请求发生错误: {str(e)}")
        raise
    finally:
        await llm_client.close()


async def process_response(client, model, messages, temperature, stream):
    """
    @desc     : 处理流式响应，返回异步生成器
    @param    : client: LLM客户端实例
    @param    : model: 使用的模型名称
    @param    : messages: 消息列表，包含系统提示和用户查询
    @param    : temperature: 控制生成文本的随机性
    @return   : 异步生成器，产生每个内容块
    """
    response = await client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        stream=stream,
    )
    if stream:
        async for chunk in response:
            delta = chunk.choices[0].delta
            try:
                if delta.content:
                    yield delta.content

            except Exception as e:
                print(f"处理流式响应时发生错误: {str(e)}")

    else:
        yield response.choices[0].message.content
