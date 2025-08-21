#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File    :   vlm.py
@Time    :   2025/08/18 17:32:56
@Author  :   SeeStars
@Version :   1.0
@Desc    :   None
"""
import os
import json
import base64
import aiohttp
import logging
import traceback

logger = logging.getLogger(__name__)

from settings import settings

api_key = os.getenv("CHATGLM_API_KEY", settings.CHATGLM_API_KEY)


def image_to_base64(image_path: str) -> str:
    """
    将图片文件转换为 base64 字符串
    """
    with open(image_path, "rb") as img_file:
        encoded_bytes = base64.b64encode(img_file.read())
        return encoded_bytes.decode("utf-8")


async def get_image_text(
    image_path: str,
    model: str = settings.IMAGE_MODEL,
    system_prompt: str = "你是一个ocr大牛，能够准确识别图片中的文字，并按照他的语义顺序给我。",
) -> str:
    """
    将图片转 base64 并调用大模型提取文字

    :param image_path: 图片路径
    :param model: 使用的模型名称
    :param system_prompt: 系统提示
    :return: 返回识别出的文字
    """

    image_base64 = image_to_base64(image_path)

    try:
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": image_base64}},
                        {"type": "text", "text": "Please extract all text from this image."},
                    ],
                },
            ],
            "temperature": 0.0,
            "stream": False,
            "thinking": {"type": "disabled"},
        }
        # print(payload)
        # logger.info(f"base_url = {settings.LLM_BASE_URL + '/chat/completions'}")
        async with aiohttp.ClientSession(trust_env=True, timeout=aiohttp.ClientTimeout(total=120)) as session:
            async with session.post(
                settings.VLM_BASE_URL + '/chat/completions',
                headers=headers,
                data=json.dumps(payload),
            ) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    logger.error(f"请求失败: {resp.status}, {text}")
                    raise ValueError(f"请求失败: {resp.status}, {text}")

                response = await resp.json()
                content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
                content = content.split("<|begin_of_box|>")[-1].split("<|end_of_box|>")[0]
                return content if content else ""
    except Exception as e:
        logger.error(f"调用模型出错: {repr(e)}")  # 显示异常类名和信息
        logger.error(traceback.format_exc())  # 打印完整堆栈
        raise e
    return ""
