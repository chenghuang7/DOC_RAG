#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :   app.py
@Time    :   2025/08/15 17:27:01
@Author  :   Shouyi Xu 
@Version :   1.0
@Desc    :   None
'''

import uvicorn

from fastapi import FastAPI,Request
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.staticfiles import StaticFiles
import logging
from CustemException.CustomException import CustomException
from libs.message import Message
from api import api_router
from settings import settings
from fastapi.responses import JSONResponse

import logging
# 配置日志
logging.basicConfig(
    level=logging.INFO,  # 日志级别
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        # logging.FileHandler("app.log"),  # 输出到文件
        logging.StreamHandler()          # 输出到控制台
    ]
)

app = FastAPI(
    description=settings.DESCRIPTION,
    docs_url=None
)

@app.get(
    "/default",
    status_code=200,
    summary="api探活接口",
)
def default():
    """
    探活接口
    """
    return Message.info("程序运行中...")

@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
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
    path=settings.API_PREFIX + "/static",
    app=StaticFiles(directory=settings.COMMON_STATIC_DIR),
    name="static",
)

@app.exception_handler(CustomException)
async def custom_exception_handler(request, exc: CustomException):
    return JSONResponse(Message.error(
            msg=exc.msg,
            data=exc.data
        ))
     
@app.exception_handler(RequestValidationError)
async def _r_exception_handler(request: Request, exc):
    try:
        body = await request.body()
        print(f"Body: {body.decode('utf-8')}")
    except Exception as e:
        print(f"Error reading body: {e}")

    print("校验失败了")
    print(str(exc))
    return JSONResponse(Message.error(
            msg=str(exc),
        ))   
@app.exception_handler(Exception)
async def _exception_handler(request, exc):
    print(request)
    print(exc)
    
    return JSONResponse(Message.error(
            msg=str(exc),
        ))

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=settings.API_PORT,
        log_level="info",
        workers=1,
        reload=True,
        reload_excludes="*.log"
    )
