//helper method方法定义
openerp.ktv_sale.helper = function(erp_instance) {
	var helper = erp_instance.ktv_sale.helper = {
		//判断给定的日期是周几
		//返回星期缩写mon/tue/wed等
		get_week_day: function(a_date) {
			var dx = ("sun mon tue wed thu fri sat").split(/\s/);
			var day_of_week = _.find(dx, function(w_day) {
				return a_date().is()[w_day]();
			});
			return day_of_week;
		},
		//得到当日是周几
		today_week_day: function() {
			return helper.get_week_day(Date.today);
		},
        //获取房态描述
        get_room_state_desc : function(r_state){
            var states_desc = {
                "free" : "空闲",
                "in_use" : "使用",
                "scheduled" : "预定",
                "locked" : "锁定",
                "checkout" : "已结账",
                "buyout" : "买断",
                "buytime" : "买钟",
                "malfunction" : "故障",
                "visit" : "带客看房",
                "clean" : "清洁",
                "debug" : "调试"
            };
            return states_desc[r_state];
        },
        //获取所有room action
        all_room_actions : function(){
            ret = '.action_room_opens,.action_room_scheduled,.action_room_scheduled_cancel,.action_room_checkout,.action_room_reopen,.action_room_change,.action_room_merge,.action_room_buytime_continue,.action_room_buytime_back,.action_room_buytime,.action_room_buyout';
            return ret;
        },
        //获取所有操作数组
        all_room_actions_array : function(){
            var actions_str = helper.all_room_actions();
            var actions_array = actions_str.split(',');
            return actions_array;

        },
        //根据当前房态获取操作列表
        get_room_actions_list : function(r_state){
            ret = "";
            //空闲-带客看房-清洁
            if(r_state == 'free' || r_state == 'visit' || r_state == 'clean' || r_state == 'checkout')
                ret = '.action_room_opens,.action_room_scheduled,.action_room_buytime,.action_room_buyout';
            //预定-取消预定、继续预定
            if(r_state == 'scheduled')
                ret = ".action_room_opens,.action_room_scheduled,.action_room_buytime,.action_room_buyout,.action_room_scheduled_cancel";
            //使用中
            if(r_state == 'in_use')
                ret = ".action_room_checkout,.action_room_reopen,.action_room_change,.action_room_merge";
            //买断:可换房、并房、结账重开
            if(r_state == 'buyout')
                ret = '.action_room_change,.action_room_merge';
            //买钟:可换房 并房 续钟 退钟
            if(r_state == 'buytime')
                ret = '.action_room_change,.action_room_merge,.action_room_buytime_continue,.action_room_buytime_back';

            //锁定-故障-调试,所有操作均不可用,只能在后台设置状态
            if(r_state == 'locked' || r_state == 'malfunction' || r_state == 'debug')
                ret = '';
            return ret;

        },
        //获取当前房态可用的操作列表,返回array
        get_room_actions_array : function(r_state) {
            var actions_string = helper.get_room_actions_list(r_state);
            var actions_array = actions_string.split(",");
            return actions_array;
        }
	}
};

