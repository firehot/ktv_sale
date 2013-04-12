# -*- coding: utf-8 -*-
import logging
from room import room
from osv import fields, osv
from datetime import date,datetime,timedelta
import decimal_precision as dp
import ktv_helper
from fee_type import fee_type

_logger = logging.getLogger(__name__)

def calculate_sum_pay_info(self,cr,uid,ctx_args):
    """
    根据给定的数值,计算买钟费用
    :params context 包含计算上下问信息,required
    :params context[room_id] integer 包厢id,required
    :params context[consume_minutes] integer 买钟时间 required
    :params context[price_class_id] integer 价格类型 required
    :params context[member_id] integer 会员卡id
    :params context[discount_card_id] integer 打折卡id
    :params context[discounter_id] integer 员工id,用于记录打折员工信息
    """
    #获取当前包厢费用信息
    room_id = ctx_args.get('room_id')
    consume_minutes = ctx_args['consume_minutes']

    sum_should_pay_info = self.get_default_checkout_dict(cr,uid)
    #获取包厢费用信息
    r_id,room_fee,minimum_fee,minimum_fee_p,minimum_persons,is_member_hourly_fee,room_hourly_fee,hourly_discount,hourly_fee_p,hourly_p_discount = self.pool.get('ktv.room').get_current_fee_tuple(cr,uid,room_id,ctx_args)

    #买钟优惠
    promotion_consume_minutes,promotion_present_minutes = (0,0)
    #买钟优惠信息
    hourly_fee_promotions = self.pool.get('ktv.hourly_fee_promotion').get_active_configs(cr,uid)

    if hourly_fee_promotions:
        promotion_consume_minutes,promotion_present_minutes = (hourly_fee_promotions[0]['buy_minutes'],hourly_fee_promotions[0]['present_minutes'])

    #钟点费
    hourly_fee = room_hourly_fee*consume_minutes/60.0

    #时长合计 = 买钟时间 + 赠送时间
    present_minutes = ktv_helper.calculate_present_minutes(consume_minutes,promotion_consume_minutes,promotion_present_minutes)

    sum_minutes = consume_minutes + present_minutes
    #计算包厢关闭时间
    open_time = datetime.now()
    close_time = open_time + timedelta(minutes = sum_minutes)
    #更新返回值
    sum_should_pay_info.update({
        'open_time' : ktv_helper.strftime(open_time),
        'close_time' : ktv_helper.strftime(close_time),
        'consume_minutes' : consume_minutes,
        'present_minutes' : present_minutes,
        #包厢钟点费
        'room_hourly_fee' : room_hourly_fee,
        'hourly_fee' : hourly_fee,
        'total_fee' : hourly_fee,
        })

    sum_should_pay_info.update(ctx_args)

    return sum_should_pay_info


class room_checkout_buytime(osv.osv):
    """
    预售-买钟,继承自 ktv.room_checkout
    1、可按照优惠金额购买消费时间
    2、如果有设置买钟优惠信息,还可享受优惠
    3、如果是会员,可可享受会员特殊折扣
    """

    _name = "ktv.room_checkout_buytime"

    _inherit = "ktv.room_checkout"

    _order = "bill_datetime DESC"

    _columns = {
        "room_hourly_fee" : fields.float("room_hourly_fee",digits_compute = dp.get_precision('ktv_fee'),help="包厢当前钟点费"),
        }

    _defaults = {
        "room_hourly_fee" : 0.0, 
        "fee_type_id" : lambda obj,cr,uid,context: obj.pool.get('ktv.fee_type').get_fee_type_id(cr,uid,fee_type.FEE_TYPE_ONLY_HOURLY_FEE)
            }

    def re_calculate_fee(self,cr,uid,context):
        """
        客户端的数据发生改变时,重新计算费用信息
        计算步骤:
        1、获取当前包厢低消信息
        2、获取当前包厢钟点费优惠信息(普通、会员、按位)
        3、获取买钟优惠信息(普通、会员)
        4、根据买钟时间计算赠送时间
        4、根据买钟时间和赠送时间计算到钟时间
        5、返回计算结果
        :params context 包含计算上下问信息,required
        :params context[room_id] integer 包厢id,required
        :params context[buy_minutes] integer 买钟时间 required
        :params context[price_class_id] integer 价格类型 required
        :params context[member_id] integer 会员卡id
        :params context[discount_card_id] integer 打折卡id
        :params context[discounter_id] integer 员工id,用于记录打折员工信息
       """
        _logger.debug(context)
        #计算应付费用
        sum_pay_info = self.calculate_sum_pay_info(cr,uid,context)

        #计算折扣
        tmp_dict = {k : v for k,v in context.items() if k in ('member_id','discount_card_id','discounter_id')}

        discount_info = self.set_discount_info(cr,uid,sum_pay_info['total_fee'],**tmp_dict)

        sum_pay_info.update(discount_info)

        self.set_calculate_fields(cr,uid,sum_pay_info)

        _logger.debug("sum_pay_info = % s" % sum_pay_info)

        return sum_pay_info

    def process_operate(self,cr,uid,buytime_vals):
        """
        处理买钟结账事件
        :params dict buytime_vals 买钟信息相关字段
        :return  tuple  room_buytime 处理过后的买钟信息对象
                        room_state  当前操作包厢所在状态
                        cron dict 定时操作对象
        """
        room_id = buytime_vals.get("room_id")
        cur_rp_id = self.pool.get('ktv.room').find_or_create_room_operate(cr,uid,room_id)
        buytime_vals.update({"room_operate_id" : cur_rp_id})
        room_buytime_id = self.create(cr,uid,buytime_vals)
        #fields = self.fields_get(cr,uid).keys()
        room_buytime = self.read(cr,uid,room_buytime_id)
        return (room_buytime,room.STATE_BUYTIME,self._build_cron(room_id,room_buytime))

    def _build_cron(self,room_id,buytime_vals):
        """
        生成买钟对象的cron信息,由于买钟要到点自动关闭包厢
        :params integer room_id 包厢id
        :params dict buytime_vals 当前买钟对象数据
        :return dict 构造出的ir.cron对象的属性dict
        """
        cron_vals = {
                "name" : buytime_vals["room_operate_id"][1],
                "nextcall" : datetime.strptime(buytime_vals['close_time'],"%Y-%m-%d %H:%M:%S"),
                "model" : "ktv.room",
                "function" : "write",
                #需要定时修改包厢状态,并清空包厢当前operate_id
                "args" : "(%s,{'state' : '%s','current_room_operate_id' : None})" % (room_id ,room.STATE_FREE)
                }
        return cron_vals

room_checkout_buytime.calculate_sum_pay_info = calculate_sum_pay_info
