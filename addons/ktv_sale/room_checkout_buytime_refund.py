# -*- coding: utf-8 -*-
#退钟结算,适用于预售-退钟时的续钟操作
import logging
from datetime import *
from osv import fields, osv
from fee_type import fee_type
import ktv_helper

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
        #计算退钟时间
        refund_minutes = ktv_helper.str_timedelta_minutes(ktv_helper.utc_now_str(),r_op.close_time) - r_op.present_minutes
        _logger.debug("refund_minutes = % s" % refund_minutes)
        if refund_minutes <= 0:
            return None


        #计算room_operate.close_time ~ datetime.now()时间内应收费用(折前)
        tmp_dict = {k:v for k,v in context.items() if k not in ('member_id','discount_card_id','discounter_id')}
        tmp_dict['price_class_id'] = getattr(r_op.price_class_id,'id')
        tmp_dict['consume_minutes'] = refund_minutes
        sum_refund_info = self.calculate_sum_pay_info(cr,uid,tmp_dict)

        return sum_refund_info
