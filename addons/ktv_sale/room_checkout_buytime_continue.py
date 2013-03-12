# -*- coding: utf-8 -*-
#续钟结算,适用于预售-买钟时的续钟操作
import logging
from osv import fields, osv
from datetime import *
from room_checkout_buytime import calculate_sum_pay_info
import ktv_helper

_logger = logging.getLogger(__name__)

class room_checkout_buytime_continue(osv.osv):
    """
    续钟操作,与买钟操作一致
    """
    _name = "ktv.room_checkout_buytime_continue"

    _inherit = "ktv.room_checkout_buytime"

    _order = "bill_datetime DESC"

    def _re_calculate_open_and_close_time(self,cr,uid,ctx_args):
        """
        重新计算续钟时,包厢开启和关闭时间
        :params context[room_id] integer 包厢id,required
        :params context[consume_minutes] integer 续钟时间 required
        :params context[present_minutes] integer 赠送时间 required
        :rtype dict {'open_time' : '','close_time'}
        """
        pool = self.pool
        room_id = ctx_args['room_id']
        consume_minutes = ctx_args['consume_minutes']
        present_minutes = ctx_args.get('present_minutes',0)
        room = pool.get('ktv.room').browse(cr,uid,room_id)
        r_op = room.current_room_operate_id
        last_close_time = r_op.close_time
        #重新计算open_time和close_time
        open_time = last_close_time
        close_time = ktv_helper.strftime(ktv_helper.strptime(open_time) + timedelta(minutes = consume_minutes + present_minutes))
        return {
                'open_time' : open_time,
                'close_time' : close_time,
                }

    #修改calcualte_sum_pay_info
    def _calculate_sum_pay_info_new(self,cr,uid,ctx_args):
        """
        计算续钟应付费用,参数与calculate_sum_pay_info相同
        :params context 包含计算上下问信息,required
        :params context[room_id] integer 包厢id,required
        :params context[consume_minutes] integer 买钟时间 required
        :params context[price_class_id] integer 价格类型 required
        :params context[member_id] integer 会员卡id
        :params context[discount_card_id] integer 打折卡id
        :params context[discounter_id] integer 员工id,用于记录打折员工信息
        """
        sum_pay_info = self.calculate_sum_pay_info_old(cr,uid,ctx_args)

        #需要根据上次包厢操作情况重新计算open_time和close_time
        tmp_dict = {k : v for k, v in sum_pay_info.items() if k in ('room_id','consume_minutes','present_minutes')}

        open_and_close_time = self._re_calculate_open_and_close_time(cr,uid,tmp_dict)

        sum_pay_info.update(open_and_close_time)

        return sum_pay_info


#续钟操作中,open_time和close_time与room_checkout_buytime中的操作稍有不同
#修改原calculate_sum_pay_info函数为calculate_sum_pay_info_org
room_checkout_buytime_continue.calculate_sum_pay_info_old = calculate_sum_pay_info
room_checkout_buytime_continue.calculate_sum_pay_info = room_checkout_buytime_continue._calculate_sum_pay_info_new
