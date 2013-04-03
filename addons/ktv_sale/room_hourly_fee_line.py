# -*- coding: utf-8 -*-
#包厢钟点费明细
import logging
from osv import fields,osv
import decimal_precision as dp

_logger = logging.getLogger(__name__)

class room_hourly_fee_line(osv.osv):
  """
  记录包厢钟点费明细,在正常开房结账时使用
  """
  _name="ktv.room_hourly_fee_line"

  _columns = {
      "room_checkout_id" : fields.many2one("ktv.room_checkout","room_checkout_id",required = True,help="包厢结账主表"),
      "hourly_fee" : fields.float("hourly_fee",digits_compute = dp.get_precision('ktv_fee'),help="钟点费"),
      "consume_minutes" : fields.integer("consume_minutes",help="消费时长(分钟)"),
      "hourly_discount" : fields.float("hourly_fee_discount",digits_compute = dp.get_precision('ktv_fee'),help="钟点费折扣"),
      "sum_hourly_fee" : fields.float("sum_hourly_fee",digits_compute = dp.get_precision('ktv_fee'),help="合计钟点费"),
      "time_from" : fields.datetime("time_from",required = True,help="开房时间"),
      "time_to" : fields.datetime("time_to",required = True,help="关房时间"),
      }

  _defaults = {
      "hourly_fee" : 0.0,
      "hourly_discount" : 0.0,
      "consume_minutes" : 0.0,
      "sum_hourly_fee" : 0.0,
      }
