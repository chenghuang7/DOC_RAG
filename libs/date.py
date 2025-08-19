#!/usr/bin/env python
# -*- encoding: utf-8 -*-


import calendar
import time
from datetime import datetime, timedelta, date, time as dt_time
import math
import pandas as pd
from enum import Enum
from typing import Union, Any, Optional
from dateutil.relativedelta import relativedelta

class TimedeltaEnum(str, Enum):
    years = "years"
    months = "months"
    weeks = "weeks"
    days = "days" # 自然日
    hours = "hours"
    minutes = "minutes"
    seconds = "seconds"

class TimeSeriesEnum(str, Enum):
    weekdays = "weekdays" # 工作日
    weekends = "weekends" # 休息日


class Date:
    """
    @name     : Date
    @desc     : 日期处理类。 注意里面的时区默认与主机的时区保持一致。如果涉及到时区的问题，请注意修改此底层工具函数即可
    """

    max_timestamp = 32000000000

    @staticmethod
    def now_format(format="%Y-%m-%d %H:%M:%S"):
        return datetime.now().strftime(format)

    @staticmethod
    def datetime2str(date_time, format="%Y-%m-%d %H:%M:%S"):
        return date_time.strftime(format)

    @staticmethod
    def timestamp2datetime(timestamp):
        if timestamp > Date.max_timestamp:
            return datetime.fromtimestamp(Date.max_timestamp)
        return datetime.fromtimestamp(timestamp)

    @staticmethod
    def timestamp2date(timestamp):
        if timestamp > Date.max_timestamp:
            return date.fromtimestamp(Date.max_timestamp)
        return date.fromtimestamp(timestamp)

    @staticmethod
    def str2timestamp(timestr, format="%Y-%m-%d %H:%M:%S"):
        """
        指定日期格式，转换成时间戳
        例如： ("Thu Aug 23 19:45:07 +0000 2012","%a %b %d %H:%M:%S %z %Y")
        format 见： https://www.cnblogs.com/xunhanliu/p/14005947.html
        """
        return int(datetime.strptime(timestr, format).timestamp())
        # return int(time.mktime(time.strptime(timestr, format)))

    @staticmethod
    def timestamp2str(timestamp, format="%Y-%m-%d %H:%M:%S"):
        """
        指定时间戳,转换成日期格式
        """
        if timestamp > Date.max_timestamp:
            return (
                time.strftime(
                    format.encode("unicode_escape").decode("utf8"),
                    time.localtime(Date.max_timestamp),
                )
                .encode("utf-8")
                .decode("unicode_escape")
            )
        return (
            time.strftime(
                format.encode("unicode_escape").decode("utf8"),
                time.localtime(timestamp),
            )
            .encode("utf-8")
            .decode("unicode_escape")
        )

    @staticmethod
    def str2str(timestr, format1="%Y-%m-%d %H:%M:%S", format2="%Y-%m-%d %H:%M:%S"):
        return Date.timestamp2str(Date.str2timestamp(timestr, format1), format2)

    @staticmethod
    def get_today_start_timestamp(utc=0):
        """
        东8区的话，就传+8
        获取当天开始的时间戳。以UTC 时间为准
        > **return**:
        """
        if utc == 0:
            return math.floor(int(time.time()) / (24 * 3600)) * (24 * 3600)
        else:  # utc 的0点 是东8区的8点。 所有东8区的0点比 utc 的0 点要小
            return math.floor(int(time.time()) / (24 * 3600)) * (24 * 3600) - utc * 3600

    @staticmethod
    def get_current_week_startend(timestamp=False):
        """
        @desc           : 获取当前周的起始时间
        @param timestamp: 是否使用时间戳类型, 默认使用datetime类型
        """
        # 获取当前时间
        now = datetime.now()
        # 获取本周的开始时间
        week_start = now - timedelta(days=now.weekday())
        # 获取本周的结束时间
        week_end = week_start + timedelta(days=6)
        # 获取本周的第一天的开始时间和结束时间
        week_start_time = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        week_end_time = week_end.replace(
            hour=23, minute=59, second=59, microsecond=9999
        )
        if timestamp:
            week_start_time = int(week_start_time.timestamp())
            week_end_time = int(week_end_time.timestamp())
        return week_start_time, week_end_time

    @staticmethod
    def get_last_week_startend(timestamp=False):
        """
        @desc           : 获取上一个自然周的起始时间
        @param timestamp: 是否使用时间戳类型, 默认使用datetime类型
        """
        # 获取当前时间
        now = datetime.now()
        # 获取本周的开始时间
        week_start = (now - timedelta(days=now.weekday())).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        # 获取上周开始时间
        last_week_start = week_start - timedelta(weeks=1)
        # 获取上周结束时间
        last_week_end = last_week_start + timedelta(
            days=6, hours=23, minutes=59, seconds=59
        )
        if timestamp:
            last_week_start = int(last_week_start.timestamp())
            last_week_end = int(last_week_end.timestamp())
        return last_week_start, last_week_end

    @staticmethod
    def get_time_series(
        start_date: Union[datetime, str],
        end_date: Union[datetime, str],
        d_type: Union[TimedeltaEnum, TimeSeriesEnum] = TimedeltaEnum.days,
        *,
        tz: str = 'Asia/Shanghai',
        **kw
    ) -> list[datetime]:
        """
        @desc             : 获取指定区间指定频率的时间序列
        @param start_date : str | datetime-like 开始日期
        @param end_date   : str | datetime-like 截止日期
        @param d_type     : 返回值结构类型
        @param tz         : 时区
        @param kw         : date_range其他配置参数，详见 pandas.date_range(inclusive设置时间区间，默认both全闭合（左右都包含），还可取值left、right)
        """
        series = []
        if d_type == TimeSeriesEnum.weekdays:
            series = pd.date_range(start_date, end_date, tz=tz, freq="B", **kw)
        elif d_type == TimeSeriesEnum.weekends:
            series = pd.date_range(start_date, end_date, tz=tz, freq="D", **kw).difference(pd.date_range(start_date, end_date, tz=tz, freq="B", **kw))
        elif d_type == TimedeltaEnum.minutes:
            series = pd.date_range(start_date, end_date, tz=tz, freq="T", **kw)
        else:
            series = pd.date_range(start_date, end_date, tz=tz, freq=d_type.value[0].upper(), **kw)
        
        return [i.to_pydatetime() for i in series]
    
    @staticmethod
    def get_monthly_dates_of_last_year(base_date):
        monthly_dates = [base_date]
        for i in range(1, 13):
            monthly_dates.insert(0, base_date - relativedelta(months=i))
        return monthly_dates


class commonDate:

    today = date.today()  # datetime.now().date()

    def getToday(self):
        """
        @desc     : 获取今天
        """
        return self.today

    def getYesterday(self):
        """
        @desc     : 获取昨天
        """
        return self.today - timedelta(days=1)

    def getTommorow(self):
        """
        @desc     : 获取明天
        """
        return self.today + timedelta(days=1)

    def getFirstDayOfThisWeek(self):
        """
        @desc     : 获取本周第一天
        """
        return self.today - timedelta(days=self.today.weekday())

    def getLastDayOfThisWeek(self):
        """
        @desc     : 获取本周最后一天
        """
        return self.today + timedelta(days=6 - self.today.weekday())

    def getFirstDayOfLastWeek(self):
        """
        @desc     : 获取上周第一天
        """
        return self.today - timedelta(days=self.today.weekday() + 7)

    def getLastDayOfLastWeek(self):
        """
        @desc     : 获取上周最后一天
        """
        return self.today - timedelta(days=self.today.weekday() + 1)

    def getFirstDayOfThisMonth(self):
        """
        @desc     : 获取本月第一天
        """
        return datetime(self.today.year, self.today.month, 1)

    def getLastDayOfThisMonth(self):
        """
        @desc     : 获取本月最后一天
        """
        return datetime(
            self.today.year,
            self.today.month,
            calendar.monthrange(self.today.year, self.today.month)[1],
        )

    def getFirstDayOfLastMonth(self):
        """
        @desc     : 获取上月第一天
        """
        return self.getFirstDayOfThisMonth() - timedelta(days=1)

    def getLastDayOfLastMonth(self):
        """
        @desc     : 获取上月最后一天
        """
        return datetime(
            self.getFirstDayOfLastMonth(), self.getFirstDayOfLastMonth().month, 1
        )

    def getFirstDayOfThisQuarter(self):
        """
        @desc     : 获取本季第一天
        """
        month = self.today - (self.today - 1) % 3  # -1的作用是让余数按 0 1 2的顺序出现
        return datetime(self.today.year, month, 1)

    def getLastDayOfThisQuarter(self):
        """
        @desc     : 获取本季最后一天
        """
        month = self.today - (self.today - 1) % 3
        return datetime(
            self.today.year, month, calendar.monthrange(self.today.year, self.month)[1]
        )

    def getFirstDayOfLastQuarter(self):
        """
        @desc     : 获取上季第一天
        """
        return datetime(
            self.getFirstDayOfThisQuarter().year,
            self.getFirstDayOfThisQuarter().month - 2,
            1,
        )

    def getLastDayOfLastQuarter(self):
        """
        @desc     : 获取上季最后一天
        """
        return self.getFirstDayOfThisQuarter() - timedelta(days=1)

    def getFirstDayOfThisYear(self):
        """
        @desc     : 获取今年第一天
        """
        return datetime(self.today.year, 1, 1)

    def getLastDayOfThisYear(self):
        """
        @desc     : 获取今年最后一天
        """
        return datetime(self.today.year, 12, 31)

    def getFirstDayOfLastYear(self):
        """
        @desc     : 获取去年第一天
        """
        return datetime(self.today.year - 1, 1, 1)

    def getLastDayOfLastYear(self):
        """
        @desc     : 获取去年最后一天
        """
        return datetime(self.today.year - 1, 12, 31)
