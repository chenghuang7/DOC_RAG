#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File    :   app.py
@Time    :   2025/08/15 17:27:01
@Author  :   SeeStars
@Version :   1.1
@Desc    :   FastAPI 主入口
"""

import logging
import uvicorn
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

from CustemException.CustomException import CustomException
from libs.message import Message
from api import api_router
from settings import settings
from service import sys_init

sys_init()

# ==============================
# 日志配置
# ==============================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# ==============================
# FastAPI 应用初始化
# ==============================
app = FastAPI(
    description=settings.DESCRIPTION,
    docs_url=None,
)  # 禁用默认 /docs


# ==============================
# 路由 & 静态文件
# ==============================
@app.get("/default", summary="api探活接口")
def default():
    """探活接口"""
    return Message.info("程序运行中...")


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    """自定义 Swagger UI"""
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="/api/static/swagger-ui/swagger-ui-bundle.js",
        swagger_css_url="/api/static/swagger-ui/swagger-ui.css",
    )


# 挂载全局路由
app.include_router(
    api_router,
    prefix=settings.API_PREFIX,
)

# 挂载静态资源
app.mount(
    f"{settings.API_PREFIX}/static",
    StaticFiles(directory=settings.COMMON_STATIC_DIR),
    name="static",
)


# ==============================
# 全局异常处理
# ==============================
@app.exception_handler(CustomException)
async def custom_exception_handler(request: Request, exc: CustomException):
    return JSONResponse(Message.error(msg=exc.msg, data=exc.data))


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    try:
        body = await request.body()
        logger.info(f"Invalid Request Body: {body.decode('utf-8')}")
    except Exception as e:
        logger.error(f"Error reading body: {e}")

    logger.error(f"校验失败: {exc}")
    return JSONResponse(Message.error(msg=str(exc)))


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled Exception: {exc}", exc_info=True)
    return JSONResponse(Message.error(msg=str(exc)))


# ==============================
# 启动入口
# ==============================
if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=settings.API_PORT,
        log_level="info",
        workers=1,
        reload=True,
        reload_excludes="*.log",
    )
