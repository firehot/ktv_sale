# -*- coding: utf-8 -*-
#换房结算,适用于预售-买钟时的换房
from datetime import *
import logging
from osv import fields, osv
import decimal_precision as dp
import ktv_helper
from fee_type import fee_type
from room import room
from room_checkout_buytime import calculate_sum_pay_info

_logger = logging.getLogger(__name__)

class room_change_checkout_buytime(osv.osv):
    """
    换房情况下的结算,在预售时(买钟、买断),如果发生换房业务，则需要进行结算,结算遵循以下业务规则：
    1、预售方式不变,换房时，仍然是买钟、买断，到点关房
    2、换房前支付的现金、抵扣券、信用卡费都作为新开房的预付款处理
    3、换房前的打折卡、会员卡等信息,在换房后结算时还可使用
    4、买断情况下，只补新包厢的当时买断差价即可
    5、买钟情况下，需要根据计费方式补足钟点费、包厢费等费用
    """
    _name = "ktv.room_change_checkout_buytime"

    _inherit = "ktv.room_checkout"

    _order = "bill_datetime DESC"

    _columns = {
            #原结账id,可以是room_checkout_buyout或room_checkout_buytime
            'changed_room_id' : fields.many2one('ktv.room',string="新包厢",required = True,help="换房新换包厢"),
            }

    _defaults = {
        "fee_type_id" : lambda obj,cr,uid,context: obj.pool.get('ktv.fee_type').get_fee_type_id(cr,uid,fee_type.FEE_TYPE_ONLY_HOURLY_FEE)
        }



    def re_calculate_fee(self,cr,uid,context):
        '''
        买钟换房重新计算费用
        原系统中,对于买钟换房费用的计算,有两种方式：
        1、按照新包厢全额补差价
        2、按照在原包厢、新包厢中的不同消费时间计算后补差价
        由于第2种方式计算比较复杂,本系统中暂不实现
        :param context['room_id'] integer 原包厢id required
        :param context['changed_room_id'] integer 新包厢id required
        :param context['member_id'] integer 会员卡id
        :param context['discount_card_id'] integer 打折卡id
        :param context['discounter_id'] integer 员工id
        :return dict 重新计算后的买钟换房对象
        '''
        pool = self.pool
        room_id = context.get('room_id')
        changed_room_id = context.get('changed_room_id')
        room = pool.get('ktv.room').browse(cr,uid,room_id)
        r_op = room.current_room_operate_id
        changed_room = pool.get('ktv.room').browse(cr,uid,changed_room_id)
        #原买钟时长
        ori_consume_minutes = r_op.ori_consume_minutes
        #当前实际消费时长
        consume_minutes = r_op.consume_minutes - r_op.left_minutes

        #计算新包厢应付买钟费用
        clone_dict = {k : v for k,v in context.items()}
        clone_dict['room_id'] = changed_room_id
        clone_dict['consume_minutes'] = ori_consume_minutes
        clone_dict.pop('changed_room_id')
        #计算应支付费用
        sum_should_pay_info = self.calculate_sum_pay_info(cr,uid,clone_dict)
        _logger.debug('sum_should_pay_info = %s' % sum_should_pay_info)

        #计算已支付费用
        sum_paid_info = pool.get('ktv.room_operate').calculate_sum_paid_info(cr,uid,r_op.id)
        #_logger.debug('sum_paid_info = %s' % sum_paid_info)

        #换房需要重新计算买钟时长和到钟时间
        changed_room_minutes =  ori_consume_minutes - consume_minutes
        present_minutes = sum_paid_info['present_minutes']
        sum_should_pay_info['consume_minutes'] = 0
        sum_should_pay_info['changed_room_minutes'] = changed_room_minutes
        sum_should_pay_info['close_time'] = ktv_helper.strftime(datetime.now() + timedelta(minutes = sum_paid_info['left_minutes']))

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

    def process_operate(self,cr,uid,buytime_vals):
        """
        处理换房-买钟结账信息
        原包厢关闭,新包厢打开
        :param buytime_vals dict 换房-买买钟相关信息
        :param buyout_vals['room_id'] 原包厢
        :param buyout_vals['changed_room_id'] 新包厢
        """
        room_id = buytime_vals.get("room_id")
        changed_room_id = buytime_vals.get('changed_room_id')

        cur_rp_id = self.pool.get('ktv.room').find_or_create_room_operate(cr,uid,room_id)

        #修改原包厢状态
        self.pool.get('ktv.room').write(cr,uid,room_id,{'state' : room.STATE_FREE,'current_room_operate_id' : None})
        #修改新包厢状态
        self.pool.get('ktv.room').write(cr,uid,changed_room_id,{'state' : room.STATE_BUYTIME,'current_room_operate_id' : cur_rp_id})

        buytime_vals.update({"room_operate_id" : cur_rp_id})

        room_change_buytime_id = self.create(cr,uid,buytime_vals)

        #修改关联的最后一次结账信息中的关闭时间和消费时长
        self.pool.get('ktv.room_operate').update_previous_checkout_for_presale_room_change(cr,uid,cur_rp_id)

        fields = self.fields_get(cr,uid).keys()
        room_change_buytime = self.read(cr,uid,room_change_buytime_id,fields)
        #TODO 删除原cron任务
        return (room_change_buytime,None,self._build_cron(changed_room_id,room_change_buytime))

    def _build_cron(self,changed_room_id,room_buytime_vals):
        """
        生成cron对象的值
        """
        cron_vals = {
                "name" : room_buytime_vals["room_operate_id"][1],
                "nextcall" : ktv_helper.strptime(room_buytime_vals['close_time']),
                "model" : "ktv.room",
                "function" : "write",
                #需要定时修改包厢状态,并清空包厢当前operate_id
                "args" : "(%s,{'state' : '%s','current_room_operate_id' : None})" % (changed_room_id ,room.STATE_FREE)
                }
        return cron_vals

room_change_checkout_buytime.calculate_sum_pay_info = calculate_sum_pay_info
