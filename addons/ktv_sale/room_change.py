# -*- coding: utf-8 -*-
import logging
from osv import fields, osv
from datetime import date,datetime
import decimal_precision as dp
import ktv_helper

_logger = logging.getLogger(__name__)

class room_change(osv.osv):
    """换房操作-正常开房"""
    _name = "ktv.room_change"
    _description = "正常开房的换房操作"

    _columns = {
            "room_operate_id" : fields.many2one("ktv.room_operate","room_operate_id",required = True,help="本操作所对应的room_operate对象"),
            "changed_room_id" : fields.many2one("ktv.room","changed_room_id",required = True,help="新包厢id"),
            "bill_datetime" : fields.datetime("bill_datetime",required = True,readonly = True,help="换房时间"),
            "open_time" : fields.datetime("open_time",required = True,help="开房时间"),
            "close_time" : fields.datetime("close_time",required = True,help="关房时间"),
            }
