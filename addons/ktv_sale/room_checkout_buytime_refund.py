# -*- coding: utf-8 -*-
#退钟结算,适用于预售-退钟时的续钟操作
import logging
from datetime import *
from osv import fields, osv
from fee_type import fee_type
import ktv_helper
from room import room

_logger = logging.getLogger(__name__)

class room_checkout_buytime_refund(osv.osv):
    """
    退钟操作,与买钟操作一致
    """
    _name = "ktv.room_checkout_buytime_refund"

    _inherit = "ktv.room_checkout_buytime"

    _order = "bill_datetime DESC"

    def re_calculate_fee(self,cr,uid,context):
        """
        重新计算应退费用
        :params context 包含计算上下问信息,required
        :params context[room_id] integer 包厢id,required
        """
        #计算以往客户付费合计
        pool = self.pool
        room_id = context.get('room_id')
        room = pool.get('ktv.room').browse(cr,uid,room_id)
        r_op = room.current_room_operate_id

        sum_refund_info = self.get_default_checkout_dict(cr,uid)
        #在实际消费时长 < 买钟时长(不包括赠送时长)时，可以退钟
        #计算退钟时间,退钟时长 =
        refund_minutes = ktv_helper.str_timedelta_minutes(ktv_helper.utc_now_str(),r_op.close_time) - r_op.present_minutes
        _logger.debug("refund_minutes = % s" % refund_minutes)
        if refund_minutes <= 0:
            return None

        #计算room_operate.close_time ~ datetime.now()时间内应收费用(折前)
        tmp_dict = {k:v for k,v in context.items() if k not in ('member_id','discount_card_id','discounter_id')}
        tmp_dict['price_class_id'] = getattr(r_op.price_class_id,'id')
        tmp_dict['consume_minutes'] = refund_minutes
        sum_refund_info = self.calculate_sum_pay_info(cr,uid,tmp_dict)

        #退钟时,open_time = now close_time = close_time - refund_minutes
        sum_refund_info['open_time'] = ktv_helper.utc_now_str()
        sum_refund_info['close_time'] = ktv_helper.strftime(datetime.now() + timedelta(minutes = refund_minutes))


        self.set_calculate_fields(cr,uid,sum_refund_info)

        return sum_refund_info

    def process_operate(self,cr,uid,refund_vals):
        """
        处理退钟结账事件
        :params dict refund_vals 退钟信息相关字段
        :param refund_vals['room_id'] 要退钟的包厢id
        :return  tuple  room_buytime 处理过后的买钟信息对象
                        room_state  当前操作包厢所在状态
                        cron dict 定时操作对象
        """
        room_id = refund_vals.get("room_id")
        cur_rp_id = self.pool.get('ktv.room').find_or_create_room_operate(cr,uid,room_id)
        refund_vals.update({"room_operate_id" : cur_rp_id})
        refund_id = self.create(cr,uid,refund_vals)
        #修改关联的最后一次结账信息中的关闭时间和消费时长
        self.pool.get('ktv.room_operate').update_previous_checkout_for_presale_room_change(cr,uid,cur_rp_id)

        fields = self.fields_get(cr,uid).keys()
        room_refund = self.read(cr,uid,refund_id,fields)
        #修改包厢状态
        self.pool.get('ktv.room').write(cr,uid,room_id,{'state' : room.STATE_FREE,'current_room_operate_id' : None,})
        return (room_refund,None,None)


