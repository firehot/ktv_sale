# -*- coding: utf-8 -*-
#续钟结算,适用于预售-买钟时的续钟操作
import logging
from osv import fields, osv

_logger = logging.getLogger(__name__)

class room_checkout_buytime_continue(osv.osv):
    """
    续钟操作,与买钟操作一致

    """
    _name = "ktv.room_checkout_buytime_continue"

    _inherit = "ktv.room_checkout_buytime"

    _order = "bill_datetime DESC"
