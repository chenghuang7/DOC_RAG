#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import math
import threading as thread_out
import time
from concurrent.futures import ThreadPoolExecutor
from typing import List, Any

class Threading:
    @staticmethod
    def backgroud_run(callback, *args, **kw):
        """
        把某个方法放到backgroud 后运行
        :param callback:
        :param args:
        :param kw:
        :return:
        """
        thread_out.Thread(target=callback, args=args, kwargs=kw).start()

    @staticmethod
    def decorate_backgroud_run(origin_func):
        """
        把某个方法放到backgroud 后运行
        使用方法：在方法上面使用@decorate_backgroud_run
        :param origin_func:
        :return:
        """

        def wrapper(*args, **kw):
            # 需要对参数的顺序进行唯一化调整
            return Threading.backgroud_run(origin_func, *args, **kw)
        return wrapper

    @staticmethod
    def bulk_run(callback, params:None or List[List[Any]]=None, threading_nums=10, is_backgroud=False):
        """
        :param callback: 是数组callable或者单个callable
        :param params: 每个callable 的参数。 使用数组的形式。不支持**kw 的形式
        :param threading_nums: 需要开启的线程的个数
        :param is_backgroud: 是否需要backgroud运行
        :return: None
       """
        if params:
            assert isinstance(params, list)
        if isinstance(callback, list):
            if params:
                assert len(params) == len(callback)
            threading_nums = len(callback)
        if params:
            threading_nums = len(params)
        _t = []
        for i in range(threading_nums):
            _t.append(thread_out.Thread(target=callback[i] if isinstance(callback, list) else callback,
                                        args=params[i] if params else []))
        for item in _t:
            item.start()
        if not is_backgroud:
            for item in _t:
                item.join()

    @staticmethod
    def bulk_run_simple(callback,all_num,bulk_num,is_backgroud=False):
        '''
        callback 的 参数 的格式需要是：（start_pos,each_num）的格式
        bulk_num: 把数据分成多少批进行处理。实际就是多少个线程进行处理
        callback(skip_num, num)
        > **return**:
        '''
        each = math.ceil(all_num / bulk_num)
        params = [[each * i, each] for i in range(bulk_num)]
        Threading.bulk_run(callback, params, is_backgroud)

    @staticmethod
    def bulk_run_with_result(callback,params:None or List[List[Any]],threading_nums=1):
        """
        这个bulk_run 不同的地方，这个函数使用线程池收集返回数据。
        :param callback:
        :param params:
        :param threading_nums:
        :return:
        """
        if params:
            assert isinstance(params, list)
        if isinstance(callback, list):
            if params:
                assert len(params) == len(callback)
            threading_nums = len(callback)
        if params:
            threading_nums = len(params)
        # 以上代码校验 callback 与 params要对应起来
        # 创建包含2个线程的线程池
        pool = ThreadPoolExecutor(max_workers=threading_nums)
        # 向线程池提交一个任务, 20和10会作为action_a/b()方法的参数
        futures = []
        t_start = time.time()
        for i in range(threading_nums):
            if params:
                futures.append(pool.submit(callback[i] if isinstance(callback, list) else callback, *params[i]))
            else:
                futures.append(pool.submit(callback[i] if isinstance(callback, list) else callback))
        result = [future.result() for future in futures]
        print("time", time.time() - t_start)
        # 关闭线程池
        pool.shutdown()
        return result

if __name__=="__main__":

    # 多线程 对某个大数据块进行批量处理
    def callback(start_pos,each_num):
        pass
    Threading.bulk_run_simple(callback,102 ,10, is_backgroud=False)
