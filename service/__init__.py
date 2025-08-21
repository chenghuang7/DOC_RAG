#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :   __init__.py
@Time    :   2025/08/21 16:06:39
@Author  :   SeeStars 
@Version :   1.0
@Desc    :   None
'''

import os
from settings import settings

UPLOAD_DIR = settings.UPLOAD_DIR
DEFAULT_KNOWLEDGE_BASE = settings.DEFAULT_KNOWLEDGE_BASE

def sys_init() :
    '''
    @description : 系统初始化
    '''
    os.makedirs(os.path.join(UPLOAD_DIR, DEFAULT_KNOWLEDGE_BASE), exist_ok=True)