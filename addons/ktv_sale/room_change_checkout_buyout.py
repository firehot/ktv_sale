# -*- coding: utf-8 -*-
#换房结算,适用于预售-买断时的换房
import logging
from osv import fields, osv
import decimal_precision as dp
from datetime import *
import ktv_helper
from fee_type import fee_type
from room import room
from room_checkout_buyout import calculate_sum_pay_info

_logger = logging.getLogger(__name__)


class room_change_checkout_buyout(osv.osv):
    """
    换房情况下的结算,在预售时(买钟、买断),如果发生换房业务，则需要进行结算,结算遵循以下业务规则：
    1、预售方式不变,换房时，仍然是买钟、买断，到点关房
    2、换房前支付的现金、抵扣券、信用卡费都作为新开房的预付款处理
    3、换房前的打折卡、会员卡等信息,在换房后结算时还可使用
    4、买断情况下，只补新包厢的当时买断差价即可
    5、买钟情况下，需要根据计费方式补足钟点费、包厢费等费用
    """
    _name = "ktv.room_change_checkout_buyout"
    _inherit = "ktv.room_checkout"

    _order = "bill_datetime DESC"

    _columns = {
            "changed_room_id" : fields.many2one("ktv.room","changed_room_id",required = True,help="新包厢id"),
            #原买断及原包厢信息通过计算获取
            'buyout_config_id' : fields.many2one('ktv.buyout_config',string="买断",required = True,help="新包厢的买断设置id"),
            }

    _defaults = {
            #默认情况下,计费方式是买断
            "fee_type_id" : lambda obj,cr,uid,context: obj.pool.get('ktv.fee_type').get_fee_type_id(cr,uid,fee_type.FEE_TYPE_BUYOUT_FEE)
            }

    def re_calculate_fee(self,cr,uid,context):
        """
        重新计算买断换房信息
        :params context dict required
                context['room_id'] integer 原包厢id required
                context['changed_room_id'] integer 新包厢id required
                context['changed_buyout_config_id'] integer 新买断id required
                context['member_id'] 会员id,可能为空
                context['discount_card_id'] 打折卡id,可能为空
                context['discounter_id'] 员工id,可能为空
        计算方法:
        1 获取已支付费用信息
        2 计算新包厢应收费用信息
        3 计算各项费用应补差额
        4 计算折扣信息

        :return dict 计算后的买断换房结算信息
        """
        pool = self.pool
        room_id = context.get('room_id')
        changed_room_id = context.get('changed_room_id')
        room = pool.get('ktv.room').browse(cr,uid,room_id)
        r_op = room.current_room_operate_id
        changed_room = pool.get('ktv.room').browse(cr,uid,changed_room_id)

        #计算新包厢应付买断费用
        clone_dict = {k : v for k,v in context.items()}
        clone_dict['room_id'] = changed_room_id
        clone_dict['buyout_config_id'] = clone_dict['changed_buyout_config_id']
        clone_dict.pop('changed_room_id')
        clone_dict.pop('changed_buyout_config_id')

        #计算应支付费用
        sum_should_pay_info = self.calculate_sum_pay_info(cr,uid,clone_dict)
        _logger.debug('sum_should_pay_info = %s' % sum_should_pay_info)
        #计算已支付费用
        sum_paid_info = pool.get('ktv.room_operate').calculate_sum_paid_info(cr,uid,r_op.id)
        _logger.debug('sum_paid_info = %s' % sum_paid_info)
        #计算应补差额
        total_fee = sum_should_pay_info['hourly_fee'] - sum_paid_info['hourly_fee'] - sum_paid_info['changed_room_fee'] - sum_paid_info['prepay_fee']
        sum_should_pay_info.update({
            'changed_room_hourly_fee': total_fee,
            'hourly_fee' : 0.0,
            'total_fee' : total_fee,
            })

        #计算折扣信息
        tmp_dict = {k : v for k,v in context.items() if k in ('member_id','discount_card_id','discounter_id')}
        discount_info = self.set_discount_info(cr,uid,sum_should_pay_info['total_fee'],**tmp_dict)

        sum_should_pay_info.update(discount_info)

        #重新计算相关字段
        self.set_calculate_fields(cr,uid,sum_should_pay_info)
        sum_should_pay_info.update(context)
        return sum_should_pay_info

    def process_operate(self,cr,uid,buyout_vals):
        """
        处理换房-买断结账信息
        原包厢关闭,新包厢打开
        :param buyout_vals dict 换房-买断相关信息
        :param buyout_vals['room_id'] 原包厢
        :param buyout_vals['changed_room_id'] 新包厢
        """
        room_id = buyout_vals.get("room_id")
        changed_room_id = buyout_vals['changed_room_id']

        cur_rp_id = self.pool.get('ktv.room').find_or_create_room_operate(cr,uid,room_id)

        buyout_vals.update({"room_operate_id" : cur_rp_id})

        #修改原包厢状态
        self.pool.get('ktv.room').write(cr,uid,room_id,{'state' : room.STATE_FREE,'current_room_operate_id' : None})
        #修改新包厢状态
        self.pool.get('ktv.room').write(cr,uid,changed_room_id,{'state' : room.STATE_BUYOUT,'current_room_operate_id' : cur_rp_id})


        room_buyout_id = self.create(cr,uid,buyout_vals)
        #修改关联的最后一次结账信息中的关闭时间和消费时长
        self.pool.get('ktv.room_operate').update_previous_checkout_for_presale_room_change(cr,uid,cur_rp_id)

        fields = self.fields_get(cr,uid).keys()
        room_buyout = self.read(cr,uid,room_buyout_id,fields)
        #TODO 需要取消原包厢的cron任务
        return (room_buyout,None,self._build_cron(changed_room_id,room_buyout))

    def _build_cron(self,room_id,room_buyout_vals):
        """
        生成cron对象的值
        """
        cron_vals = {
                "name" : room_buyout_vals["room_operate_id"][1],
                "nextcall" : datetime.strptime(room_buyout_vals['close_time'],"%Y-%m-%d %H:%M:%S"),
                "model" : "ktv.room",
                "function" : "write",
                #需要定时修改包厢状态,并清空包厢当前operate_id
                "args" : "(%s,{'state' : '%s','current_room_operate_id' : None})" % (room_id ,room.STATE_FREE)
                }
        return cron_vals

#计算换房后的费用信息,调用room_checkout_buyout#calculate_sum_pay_info
room_change_checkout_buyout.calculate_sum_pay_info = calculate_sum_pay_info
