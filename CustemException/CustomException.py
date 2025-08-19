# -*- coding: utf-8 -*-
class CustomException(Exception):
    def __init__(self, msg: str = "", data=None, **kwargs):
        self.msg = msg
        self.data = data

    @staticmethod
    def exception(msg: str = "", data=None):
        return CustomException(msg, data)