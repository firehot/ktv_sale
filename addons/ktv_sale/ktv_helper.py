# -*- coding: utf-8 -*-
from osv import fields
from datetime import date,datetime,time,timedelta
import openerp.tools as tools
import logging
_logger = logging.getLogger(__name__)
#时间段选择
def time_for_selection(self,cr,uid,context = None):
     ret = [("%02i:00" % i,"%02i时30分" % i) for i in range(24)] + [("%02i:30" % i,"%02i时00分" % (i+1)) for i in range(24)]
     ret.sort()
     ret.pop()
     ret.append(("23:59","23时59分"))
     return ret

#价格列表
def price_list_for_selection(self,cr,uid,context = None):
    ret =[("ting_price","大厅价"),("room_price","包厢价"),("member_price","会员价"),("vip_price","贵宾价"),("a_price","A类价"),("b_price","B类价")]
    return ret

#房态定义
def room_states_for_selection(self,cr,uid,context = None):
    ret =[("free","空闲"),("in_use","使用"),("scheduled","预定"),("locked","锁定"),("checkout","已结账"),("buyout","买断"),("buytime","买钟"),("malfunction","故障"),("clean","清洁"),("debug","调试"),("visit","带客")]
    return ret
#男女
def sexes_for_select(self,cr,uid,context = None):
    ret=[("F","女"),("M","男")]
    return ret
#证件类型
def id_types_for_select(self,cr,uid,context = None):
    ret=[(1,"身份证"),(2,"驾驶证"),(3,"其他证件")]
    return ret

#根据0 1 2 3 4 5 6 分别返回星期缩写 min =0 ~ sun= 6
def weekday_str(weekday_int):
    weekday_dict = {
            0 : 'mon',
            1 : 'tue',
            2 : 'wed',
            3 : 'thu',
            4 : 'fri',
            5 : 'sat',
            6 : 'sun'
            }
    return weekday_dict[weekday_int]

def current_user_tz(obj,cr,uid,context = None):
    """
    获取当前登录用户的时区设置
    :param cursor cr 数据库游标
    :params integer uid 当前登录用户id
    """
    the_user = obj.pool.get('res.users').read(cr,uid,uid,['id','tz','name'])
    return the_user['tz']

def user_context_now(obj,cr,uid):
    """
    获取当前登录用户的本地日期时间
    :return 本地化的当前日期
    """
    tz = current_user_tz(obj,cr,uid)
    context_now = fields.datetime.context_timestamp(cr,uid,datetime.now(),{"tz" : tz})
    return context_now

def float_time_to_datetime(float_time):
    """
    将以float方式形式存储的time字段值转换为datetime,
    :params float_time float float方式存储的time字段值
    :return datetime UTC 当日日期 + time
    """
    now=datetime.now()
    h=int(float_time)
    m=int((float_time-h)*60)
    datetime_time=datetime(year=now.year,month=now.month,day=now.day,hour=h,minute=m)
    return datetime_time

def timedelta_minutes(datetime_from,datetime_to):
    '''
    计算给定两个时间的相差分钟数
    :param datetime_from datetime 起始时间
    :param datetime_to datetime 结束时间

    :return integer 两个时间的相差分钟数
    '''
    return int((datetime_to - datetime_from).total_seconds()/60)


def float_time_minutes_delta(float_time_from,float_time_to):
    '''
    计算给定两个时间的相差分钟数
    因为全部使用UTC时间存储,所以可能存在float_time_to < float_time_from的情况,这种情况下,
    float_time_to加1天
    :param float_time_from float 形式是18.09,指的是起始时间
    :param float_time_to float 形式是21.30,指的是结束时间时间

    :return integer 两个时间的相差分钟数
    '''
    time_from = float_time_to_datetime(float_time_from)
    time_to = float_time_to_datetime(float_time_to)
    #判断是否time_to < time_from
    if time_to < time_from:
        time_to = time_to + timedelta(days = 1)
    return int((time_to - time_from).total_seconds()/60)

def utc_time_between(float_time_from,float_time_to,cur_time):
    """
    判断给定的时间字符串是否在给定的时间区间内
    由于对时间统一采用UTC时间保存,可能存在time_to < time_from的情况
    :params float float_time_from 形式类似 9.1的时间字符串
    :params float float_time_to 形式类似 9.2的时间字符串
    :params datetime cur_time 要比较的datetime
    :return True 在范围内 else False
    """
    time_from = float_time_to_datetime(float_time_from)
    time_to = float_time_to_datetime(float_time_to)
    #判断是否time_to < time_from
    #采用UTC时间,可能存在跨天的情况
    if time_to < time_from:
        time_to = time_to + timedelta(days = 1)
        return cur_time + timedelta(days = 1) <= time_to
    else:
        return cur_time >= time_from and cur_time <= time_to


def calculate_present_minutes(buy_minutes,promotion_buy_minutes = 0,promotion_present_minutes = 0):
    """
    根据给定的参数计算赠送时长
    买钟时间(分钟数) / 设定买钟时长(分钟数) * 赠送时长
    :params buy_minutes integer 买钟时间
    :params promotion_buy_minutes integer 买钟优惠设置中设定的买钟时长
    :params promotion_present_minutes integer 买钟优惠设置中设定的赠送时长
    :return integer 赠送时长
    """
    #如果未设置优惠信息,则不赠送,直接返回0
    if  not promotion_buy_minutes or buy_minutes < promotion_buy_minutes:
        return 0

    present_minutes = buy_minutes / promotion_buy_minutes * promotion_present_minutes

    return present_minutes

def strptime(str_datetime):
    """
    以服务器端的格式格式化字符串为datetime类型
    :params str_datetime string 日期字符串 required
    :return datetime
    """
    return datetime.strptime(str_datetime,tools.DEFAULT_SERVER_DATETIME_FORMAT)


