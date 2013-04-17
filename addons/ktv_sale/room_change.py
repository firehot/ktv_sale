# -*- coding: utf-8 -*-
import logging
from osv import osv,fields
from room import room
import decimal_precision as dp
import ktv_helper



_logger = logging.getLogger(__name__)

class room_change(osv.osv):
    """换房操作-正常开房"""
    _name = "ktv.room_change"
    _description = "正常开房的换房操作"

    _order = "bill_datetime DESC"

    _columns = {
            "room_operate_id" : fields.many2one("ktv.room_operate","room_operate_id",required = True,help="本操作所对应的room_operate对象"),
            "room_id" : fields.many2one("ktv.room","room_id",required = True,help="原包厢id"),
            "changed_room_id" : fields.many2one("ktv.room","changed_room_id",required = True,help="新包厢id"),
            "bill_datetime" : fields.datetime("bill_datetime",required = True,readonly = True,help="换房时间"),
            "open_time" : fields.datetime("open_time",required = True,help="开房时间"),
            "close_time" : fields.datetime("close_time",help="关房时间"),
            }

    _defaults = {
            "open_time" : fields.datetime.now,
            "bill_datetime" : fields.datetime.now,
            }

    def process_operate(self,cr,uid,room_change_vals):
        """
        处理正常开房-换房信息
        :param room_change_vals dict 换房对象数据
        :return  (room_change,包厢状态,cron定时任务对象)
        """
        room_id = room_change_vals.get("room_id")
        changed_room_id = room_change_vals['changed_room_id']

        cur_rp_id = self.pool.get('ktv.room').find_or_create_room_operate(cr,uid,room_id)

        #获取最近一次的换房(room_change)或开房(room_opens)信息
        room_opens,room_change = self.pool.get('ktv.room_operate').last_room_opens_and_change(cr,uid,cur_rp_id)

        #修改room_opens或上次room_change的close_time
        close_time = ktv_helper.utc_now_str()
        if room_change:
            self.pool.get('ktv.room_change').write(cr,uid,room_change.id,{"close_time" : close_time})
        elif room_opens:
            self.pool.get('ktv.room_opens').write(cr,uid,room_opens.id,{"close_time" : close_time})

        #修改原包厢状态
        self.pool.get('ktv.room').write(cr,uid,room_id,{'state' : room.STATE_FREE,'current_room_operate_id' : None,})
        #修改新包厢状态
        self.pool.get('ktv.room').write(cr,uid,changed_room_id,{'state' : room.STATE_IN_USE,'current_room_operate_id' : cur_rp_id})
        room_change_vals["room_operate_id"] = cur_rp_id

        room_change_id = self.create(cr,uid,room_change_vals)
        fields = self.fields_get(cr,uid).keys()
        room_change = self.read(cr,uid,room_change_id,fields)
        return (room_change,None,None)
