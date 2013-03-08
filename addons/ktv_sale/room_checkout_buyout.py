# -*- coding: utf-8 -*-
import logging
from room import room
from osv import fields, osv
from datetime import date,datetime
import decimal_precision as dp
import ktv_helper
from fee_type import fee_type

_logger = logging.getLogger(__name__)

def calculate_sum_pay_info(self,cr,uid,ctx_args):
    '''
    计算当前买断应付费用信息
    :param ctx_args['room_id'] integer 当前包厢id required
    :param ctx_args['buyout_config_id'] integer 当前买断设置id required
    :param ctx_args['member_id'] integer 会员卡id optional
    :param ctx_args['discount_card_id'] integer 打折卡id optional
    :param ctx_args['discounter_id'] integer  打折员工id optional
    '''
    pool = self.pool
    sum_pay_info = self.get_default_checkout_dict(cr,uid)
    sum_pay_info.update(ctx_args)
    room_id = ctx_args['room_id']
    room = self.pool.get('ktv.room').browse(cr,uid,room_id)
    buyout_config_id = ctx_args['buyout_config_id']
    member_id = ctx_args.get('member_id')
    discount_card_id = ctx_args.get('discount_card_id')
    discounter_id = ctx_args.get('discounter_id')

    #获取当时可用的买断设置信息
    active_buyout_config = pool.get('ktv.buyout_config').get_active_buyout_fee(cr,uid,buyout_config_id,only_member=member_id)

    total_fee = hourly_fee = active_buyout_config.get('buyout_fee')

    sum_pay_info.update({
                'open_time': active_buyout_config['time_from'],
                'close_time': active_buyout_config['time_to'],
                'consume_minutes' : active_buyout_config['buyout_time'],
                'hourly_fee' : total_fee,
                'total_fee' : total_fee,
                })
    return sum_pay_info


class room_checkout_buyout(osv.osv):
    '''
    买断结账单,买断属于预售,应先付账,继承自ktv.room_checkout
    '''

    _name="ktv.room_checkout_buyout"

    _inherit = "ktv.room_checkout"

    _order = "bill_datetime DESC"

    _columns = {
            "buyout_config_id" : fields.many2one("ktv.buyout_config","buyout_config_id",required = True,select = True,help="买断名称"),
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
                context['buyout_config_id'] integer 新买断id required
                context['member_id'] 会员id,可能为空
                context['discount_card_id'] 打折卡id,可能为空
                context['discounter_id'] 员工id,可能为空
        :return dict 计算后的买断换房结算信息
        """
        #计算应付费用
        sum_pay_info = self.calculate_sum_pay_info(cr,uid,context)

        #计算折扣
        tmp_dict = {k : v for k,v in context.items() if k in ('member_id','discount_card_id','discounter_id')}

        discount_info = self.set_discount_info(cr,uid,sum_pay_info['total_fee'],**tmp_dict)

        sum_pay_info.update(discount_info)

        self.set_calculate_fields(cr,uid,sum_pay_info)

        _logger.debug("sum_pay_info = % s" % sum_pay_info)
        return sum_pay_info

    def process_operate(self,cr,uid,buyout_vals):
        """
        处理买断结账信息
        """
        room_id = buyout_vals["room_id"]
        cur_rp_id = self.pool.get('ktv.room').find_or_create_room_operate(cr,uid,room_id)
        buyout_vals.update({"room_operate_id" : cur_rp_id})
        room_buyout_id = self.create(cr,uid,buyout_vals)
        fields = self.fields_get(cr,uid).keys()
        room_buyout = self.read(cr,uid,room_buyout_id,fields)
        return (room_buyout,room.STATE_BUYOUT,self._build_cron(room_id,room_buyout))

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


room_checkout_buyout.calculate_sum_pay_info = calculate_sum_pay_info
