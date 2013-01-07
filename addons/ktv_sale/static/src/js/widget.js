//widget定义
//erp_instance openerp的客户端实例对象，在boot.js中初始化
openerp.ktv_sale.widget = function(erp_instance) {
	//引用model和helper
	var model = erp_instance.ktv_sale.model;
	var helper = erp_instance.ktv_sale.helper;
	//扩展通用的模板方法
	var QWeb = erp_instance.web.qweb;
	var qweb_template = function(template) {
		return function(ctx) {
			return QWeb.render(template, _.extend({},
			ctx, {
				//以下定义需要在界面上显示的数据
				'company': erp_instance.ktv_sale.ktv_room_point.get('company').toJSON(),
				'all_rooms': erp_instance.ktv_sale.ktv_room_point.get('all_rooms').toJSON(),
				'display_rooms': erp_instance.ktv_sale.ktv_room_point.get('display_rooms').toJSON(),
				'room_types': erp_instance.ktv_sale.ktv_room_point.get('room_types').toJSON(),
				'room_areas': erp_instance.ktv_sale.ktv_room_point.get('room_areas').toJSON(),
				'fee_types': erp_instance.ktv_sale.ktv_room_point.get('fee_types').toJSON(),
				'price_classes': erp_instance.ktv_sale.ktv_room_point.get('price_classes').toJSON(),
				'member_classes': erp_instance.ktv_sale.ktv_room_point.get('member_classes').toJSON(),
				'pay_types': erp_instance.ktv_sale.ktv_room_point.get('pay_types').toJSON(),
				'currency': erp_instance.ktv_sale.ktv_room_point.get('currency'),
				'format_amount': function(amount) {
					if (erp_instance.ktv_sale.ktv_room_point.get('currency').position == 'after') {
						return amount + ' ' + erp_instance.ktv_sale.ktv_room_point.get('currency').symbol;
					} else {
						return erp_instance.ktv_sale.ktv_room_point.get('currency').symbol + ' ' + amount;
					}
				},
			}));
		};
	};
	var _t = erp_instance.web._t;

	var widget = erp_instance.ktv_sale.widget = {};
	//定义基于bootstrap的modal的dialog类
	widget.BootstrapModal = erp_instance.web.Widget.extend({
		/**
                 * @constructs openerp.web.Dialog
                 * @extends openerp.web.Widget
                 *
                 * @param parent
                 * @param options
                 */
		init: function(parent, options) {
			var self = this;
			this._super(parent);
			this.dialog_options = {
				width: 'auto',
				backdrop: 'static',
				keyboard: true,
				show: true,
				remote: false
			};
			if (options) {
				_.extend(this.dialog_options, options);
			}
			if (this.dialog_options.show) this.open();

		},
		open: function(options) {
			var self = this;
			this.appendTo($('body'));
			this.$(".modal").modal(self.dialog_options).on('hidden', _.bind(self.destroy, self)).modal('show').css({
				width: self.dialog_options.width,
				'margin-left': function() {
					return - ($(this).width() / 2);
				}
			}).on("shown", _.bind(this.post_open, this));
			return this;
		},
		//打开后的处理,用于焦点设置等等
		post_open: function() {},
		close: function() {
			this.$(".modal").modal('hide');
		},
		destroy: function() {
			// Destroy widget
			this.close();
			this._super();
		}
	});
	//提示对话框
	widget.AlertWidget = erp_instance.web.Widget.extend({
		template_fct: qweb_template("alert-template"),
		init: function(parent, options) {
			this._super(parent, options);
			this.alert_class = options.alert_class;
			this.info = options.info;
			this.title = options.title;
			this.timer = $.timer(_.bind(this._auto_close, this), 10000, false);
		},
		renderElement: function() {
			this.$el.html(this.template_fct({
				title: this.title,
				info: this.info
			}));
			return this;
		},
		start: function() {
			this.$(".alert").addClass(this.alert_class);
			this.$el.on('click',".close",_.bind(this._auto_close, this));
			this.timer.play();
		},
		//自动关闭
		_auto_close: function() {
			console.log("auto close alert widget");
			this.timer.stop();
			this.timer = null;
			this.destroy();
		}
	});

	//roomWidget
	widget.RoomWidget = erp_instance.web.Widget.extend({
		tagName: 'li',
		template_fct: qweb_template('room-template'),
		init: function(parent, options) {
			this._super(parent);
			this.model = options.model;
		},
		start: function() {
			this.model.bind('change', _.bind(this.renderElement, this));
			this.$el.click(_.bind(this.on_click, this));
			//预定事件

            this.$el.on("click",".action_room_scheduled",_.bind(this.action_room_scheduled,this));
			this.$el.on('click',".action_room_scheduled",_.bind(this.action_room_scheduled, this));
			this.$el.on("click",".action_room_opens",_.bind(this.action_room_opens, this));
			this.$el.on("click",".action_room_buyout",_.bind(this.action_room_buyout, this));
			this.$el.on("click",".action_room_buytime",_.bind(this.action_room_buytime, this));
			//换房
			this.$el.on('click','.action_room_change',_.bind(this.action_room_change, this));
		},
		//包厢预定
		action_room_scheduled: function() {
			var win = new widget.RoomScheduledWidget(null, {
				room: this.model,
			});
			$('#operate_area').html(win.$el);
			win.renderElement();
			win.start();
		},
		//开房
		action_room_opens: function() {
			console.log("打开开房界面");
			var r = new widget.RoomOpensWidget(null, {
				room: this.model
			});
			$('#operate_area').html(r.$el);
			r.renderElement();
			r.start();
		},
		//买断
		action_room_buyout: function() {
			var r = new widget.RoomCheckoutBuyoutWidget(null, {
				room: this.model
			});
			r.ready.then(function() {
				$('#operate_area').html(r.$el);
				r.renderElement();
				r.start();
			});
		},
		//买钟
		action_room_buytime: function() {
			var r = new widget.RoomCheckoutBuytimeWidget(null, {
				room: this.model
			});
			r.ready.then(function() {
				$('#operate_area').html(r.$el);
				r.renderElement();
				r.start();
			});
		},
		//包厢换房-买断
		action_room_change: function() {
			console.log("enter into action_room_change");
			var win = new widget.RoomChangeCheckoutBuyoutWidget(null, {
				room: this.model,
			});
			win.ready.then(function() {
				$('#operate_area').html(win.$el);
				win.renderElement();
				win.start();
			});
		},

		//当前包厢点击事件
		on_click: function() {
			erp_instance.ktv_sale.ktv_room_point.set({
				"current_room": this.model
			});
		},
		renderElement: function() {
			this.$el.empty();
			this.$el.html(this.template_fct(this.model.export_as_json()));
		}
	});
	//房间列表
	widget.RoomListWidget = erp_instance.web.Widget.extend({
		init: function(parent, options) {
			this._super(parent);
			erp_instance.ktv_sale.ktv_room_point.get('display_rooms').bind('reset', this.renderElement, this);
		},
		renderElement: function() {
			this.$el.empty();
			erp_instance.ktv_sale.ktv_room_point.get('display_rooms').each(_.bind(function(r) {
				var r_widget = new widget.RoomWidget(null, {
					model: r
				});
				r_widget.appendTo(this.$el);
			},
			this), this);
			return this;
		}
	});
	//房态统计
	//RoomStatusWidget
	widget.RoomStatusWidget = erp_instance.web.Widget.extend({
		template_fct: qweb_template('room-status-template'),
		init: function(parent, options) {
			this._super(parent);
		},
		start: function() {
			//ktv_shop中的包厢数据发生变化时,重绘房态组件
			erp_instance.ktv_sale.ktv_room_point.bind('change:room_status', this.renderElement, this);
		},
		renderElement: function() {
			this.$el.empty();
			this.$el.html(this.template_fct(erp_instance.ktv_sale.ktv_room_point.get('room_status')));
			return this;
		}
	});

	//包厢过滤 widget
	widget.RoomFilterWidget = erp_instance.web.Widget.extend({
		template_fct: qweb_template('room-filter'),
		init: function(parent, options) {
			this._super(parent);
		},
		start: function() {
			//绑定按钮点击事件
			$('.btn-room-type-filter,.btn-room-area-filter,.btn-room-state-filter').click(_.bind(this._filter_room, this));
		},
		//根据前端的操作过滤包厢的显示
		_filter_room: function(evt) {
			var click_btn = $(evt.target);
			var btn_class = "";
			if (click_btn.hasClass('btn-room-type-filter')) btn_class = ".btn-room-type-filter";
			if (click_btn.hasClass('btn-room-state-filter')) btn_class = ".btn-room-state-filter";
			if (click_btn.hasClass('btn-room-area-filter')) btn_class = ".btn-room-area-filter";

			$(btn_class).removeClass('active')
			if (!click_btn.hasClass('active')) click_btn.addClass('active');
			var room_state = $('.btn-room-state-filter').filter('.active').data('room-state');
			var room_area_id = $('.btn-room-area-filter').filter('.active').data('room-area-id');
			var room_type_id = $('.btn-room-type-filter').filter('.active').data('room-type-id');
			//所有房间
			var rooms = erp_instance.ktv_sale.ktv_room_point.get('all_rooms').toJSON();
			var filtered_rooms = rooms;
			if (room_state != - 1) filtered_rooms = _.filter(rooms, function(r) {
				return r.state == room_state;
			});
			if (room_type_id != - 1) filtered_rooms = _.filter(filtered_rooms, function(r) {
				return r.room_type_id[0] == room_type_id;
			});
			if (room_area_id != - 1) filtered_rooms = _.filter(filtered_rooms, function(r) {
				return r.room_area_id[0] == room_area_id;
			});
			erp_instance.ktv_sale.ktv_room_point.get('display_rooms').reset(filtered_rooms);
		},

		renderElement: function() {
			this.$el.html(this.template_fct({}));
			return this;
		}
	});

	//KtvRoomPointWidget
	widget.KtvRoomPointWidget = erp_instance.web.Widget.extend({
		init: function(parent, options) {
			this._super(parent);
		},
		start: function() {
			this.room_list_view = new widget.RoomListWidget();
			this.room_list_view.$el = $('#room_list');
			this.room_list_view.renderElement();
			this.room_list_view.start();

			this.room_status_view = new erp_instance.ktv_sale.widget.RoomStatusWidget();
			this.room_status_view.$el = $('#room_status');
			this.room_status_view.renderElement();
			this.room_status_view.start();

			//room filter
			this.room_filter_view = new erp_instance.ktv_sale.widget.RoomFilterWidget();
			this.room_filter_view.$el = $('#room_filter');
			this.room_filter_view.renderElement();
			this.room_filter_view.start();

			//room info
			this.room_info_tab_view = new widget.RoomInfoWidget();
			this.room_info_tab_view.$el = $('#room_info_tab');
			this.room_info_tab_view.renderElement();
			this.room_info_tab_view.start();
		}
	});

	//右侧显示的包厢信息对象
	widget.RoomInfoWidget = erp_instance.web.Widget.extend({
		template_fct: qweb_template('room-info-wrapper-template'),
		init: function(parent, options) {
			this._super(parent);
			erp_instance.ktv_sale.ktv_room_point.bind("change:current_room", this.renderElement, this);
		},
		start: function() {},
		set_display_by_fee_type: function() {
			var self = this;
			//需要根据计费方式不同显示不同的费用信息
			var cur_room = erp_instance.ktv_sale.ktv_room_point.get("current_room");
			if (!cur_room) return false;

			var fee_type_id = cur_room.get("fee_type_id")[0];
			new erp_instance.web.Model("ktv.fee_type").get_func("read")(fee_type_id, ['id', 'fee_type_code', 'name']).pipe(function(fee_type) {

				self.$(".room_fee,.minimum_fee,.minimum_fee_p,.buyout_fieldset,.buffet_fieldset,.buyout_config_lines,.buffet_config_lines,.buytime_fieldset,.hourly_fee_promotion_lines,.hourly_fee_lines,.member_hourly_fee_lines,.hourly_fee_p_lines").hide();
				//只收包厢费
				if (fee_type.fee_type_code == "only_room_fee") {
					self.$(".room_fee").show();
				}
				//只收钟点费
				if (fee_type.fee_type_code == "only_hourly_fee") {
					self.$(".hourly_fee,.hourly_fee_lines,.buytime_fieldset,.hourly_fee_promotion_lines").show();
				}

				//钟点费+包厢费
				if (fee_type.fee_type_code == "room_fee_plus_hourly_fee") {
					self.$(".room_fee,.hourly_fee,.hourly_fee_lines,.buytime_fieldset,.hourly_fee_promotion_lines").show();
				}
				//最低消费
				if (fee_type.fee_type_code == "minimum_fee") {
					self.$(".minimum_fee,.buytime_fieldset,.hourly_fee_promotion_lines").show();
				}

				//包厢费+最低消费
				if (fee_type.fee_type_code == "room_fee_plus_minimum_fee") {
					self.$(".room_fee,.minimum_fee,.buytime_fieldset").show();
				}

				//钟点费+最低消费
				if (fee_type.fee_type_code == "hourly_fee_plus_minimum_fee") {
					self.$(".hourly_fee_lines,.minimum_fee,.buytime_fieldset,.hourly_fee_promotion_lines").show();
				}

				//包厢费+钟点费+最低消费
				if (fee_type.fee_type_code == "room_fee_plus_hourly_fee_plus_minimum_fee") {
					self.$(".room_fee,.hourly_fee,.hourly_fee_lines,.minimum_fee,.buytime_fieldset,.hourly_fee_promotion_lines").show();
				}
				//按位钟点费
				if (fee_type.fee_type_code == "hourly_fee_p") {
					self.$(".hourly_fee_p_lines,.buytime_fieldset,.hourly_fee_promotion_lines").show();
				}

				//按位最低消费
				if (fee_type.fee_type_code == "minimum_fee_p") {
					self.$(".minimum_fee_p").show();
				}
				//买断
				if (fee_type.fee_type_code == "buyout_fee") {
					self.$(".buyout_config_lines,.buyout_fieldset").show();
					self.$(".buytime_fieldset").hide();
				}
				//自助餐
				if (fee_type.fee_type_code == "buffet") {
					self.$(".buffet_config_lines,.buffet_fieldset").show();
					self.$(".buytime_fieldset").hide();
				}
			});
		},
		renderElement: function() {
			var self = this;
			var the_room = erp_instance.ktv_sale.ktv_room_point.get("current_room");
			var the_room_fee_info = the_room.get_room_fee_info();
			the_room_fee_info.ready.then(function() {
				self.$el.html(self.template_fct({
					"room_info": the_room.export_as_json(),
					"room_fee_info": the_room_fee_info.export_as_json()
				}));
				self.set_display_by_fee_type();
			});
			return this;
		}
	});

	//预定widget
	widget.RoomScheduledWidget = erp_instance.web.Widget.extend({
		template_fct: qweb_template('room-scheduled-form-template'),
		init: function(parent, options) {
			this.room = options.room;
			this.model = new erp_instance.ktv_sale.model.RoomScheduled({
				room_id: this.room.get("id")
			});
			this._super(parent, options);
		},
		start: function() {
			//隐藏其他元素
			$('#room_status').hide();
			$('#room_filter').hide();
			$('#room_list').hide();

			this.$el.on("click",'.btn-close-room-scheduled',_.bind(this.close, this));

			this.$form = $(this.$el).find("#room_scheduled_form");
			this.$form.find('#scheduled_time').datetimepicker();
			this.$form.find('#scheduled_time').val(this.model.get('scheculed_time'));
			//包厢改变事件
			this.$form.find("#room_id").change(_.bind(this.on_change_room, this));
			//设置初始值
			if (this.room) this.$form.find('#room_id').val(this.room.id);
			//保存事件
			this.$(".btn-save").click(_.bind(this.save, this));
			return this;
		},
		close: function() {
			$('#room_status').show();
			$('#room_filter').show();
			$('#room_list').show();
			this.destroy();
		},

		renderElement: function() {
			this.$el.html(this.template_fct({
				rooms: erp_instance.ktv_sale.ktv_room_point.get_rooms_by_state('free').toJSON(),
				model: this.model.toJSON()
			}));
			return this;
		},
		//修改包厢
		on_change_room: function() {
			var changed_room = erp_instance.ktv_sale.ktv_room_point.get("all_rooms").get(this.$form.find('#room_id').val());
			this.room = changed_room;
			this.model.set({
				"room_id": changed_room.get("id")
			});
		},
		//验证录入数据是否有效
		validate: function() {
			return this.$form.validate().form();
		},
		//保存预定信息
		save: function() {
			var self = this;
			if (!this.validate()) {
				return false;
			}
			//自界面获取各项值
			this.model.set(this.$form.form2json());
			var scheduled_time = this.$form.find("#scheduled_time").val();

			this.model.set({
				"context_scheduled_time": scheduled_time
			});
			var success_func = function() {
				erp_instance.ktv_sale.ktv_room_point.app.alert({
					'alert_class': "alert-success",
					'info': "保存预定信息成功!"
				});
				self.close();
			};
			var fail_func = function() {
				erp_instance.ktv_sale.ktv_room_point.app.alert({
					'alert_class': "alert-error",
					'info': "保存预定信息失败!"
				});

			};
			this.model.push().pipe(function(result) {
				//更新包厢状态
				self.room.set(result["room"]);
				self.close();
			}).then(success_func, fail_func);
		}
	});

	//RoomOpensWidget 开房widget
	widget.RoomOpensWidget = erp_instance.web.Widget.extend({
		template_fct: qweb_template("room-opens-template"),
		init: function(parent, options) {
			//当前包厢
			this.room = options.room;
			this.model = new model.RoomOpens();
			this.member = new model.Member();
			this.member.bind("change", this.render_member_card_no, this);
			this._super(parent, options);
		},
		start: function() {
			//隐藏其他元素
			$('#room_status').hide();
			$('#room_filter').hide();
			$('#room_list').hide();
			this.$el.on('click','.btn-close-room-opens',_.bind(this.close, this));
			//会员卡扫描
			this.$el.on('click','.btn-member-card-read',_.bind(this.open_member_card_read_win, this));
			this.$el.on('click','.btn-member-card-clear',_.bind(this.clear_member_card, this));
			//绑定相关事件
			this.$form = this.$("#room_opens_form");
			this.$("#room_id").val(this.room.get("id"));
			this.$el.on('change',"#room_id",_.bind(this.on_change_room, this));
			this.$el.on('click',".btn-save-room-opens",_.bind(this.save, this));
		},
		close: function() {
            this.$el.off();
			$('#room_status').show();
			$('#room_filter').show();
			$('#room_list').show();
			this.destroy();
		},
		//打开会员卡读取窗口
		open_member_card_read_win: function() {
			var m_win = new widget.MemberCardReadWidget(null, {
				show: false,
				model: this.member
			});
			m_win.open();
		},
		//清除会员信息
		clear_member_card: function() {
			this.member.clear();
		},
		//重新显示会员信息
		render_member_card_no: function() {
			if (this.member.get("id")) {
				var member_card_no = this.member.get("member_card_no");
				var member_class = this.member.get("member_class_id");
				var member_name = this.member.get("name");
				var info = member_card_no + "[" + member_class[1] + "]" + "[" + member_name + "]";
				this.$("#member-card-no").html(info);
				this.$('.member-card-wrapper').removeClass('hide');
			}
			else {
				this.$("#member-card-no").empty();
				this.$('.member-card-wrapper').addClass('hide');
			}
		},

		renderElement: function() {
			this.$el.html(this.template_fct({
				rooms: erp_instance.ktv_sale.ktv_room_point.get_rooms_by_state('free').toJSON(),
				model: this.model.toJSON()
			}));
			this.render_member_card_no();
			return this;
		},
		validate: function() {
			//验证模型数据
			return this.$form.validate().form();
		},
		on_change_room: function() {
			var changed_room = erp_instance.ktv_sale.ktv_room_point.get("all_rooms").get(this.$form.find('#room_id').val());
			this.room = changed_room;
			this.model.set({
				"room_id": changed_room.get("id")
			});

		},
		save: function() {
			var self = this;
			//保存数据
			if (!this.validate()) return false;
			this.model.set(this.$form.form2json());
			if (this.member.get("id")) this.model.set({
				"member_id": this.member.get("id")
			});
			var success_func = function() {
				erp_instance.ktv_sale.ktv_room_point.app.alert({
					'alert_class': "alert-success",
					'info': "保存开房信息成功,请打印开房条!"
				});
				self.close();
				self.print();
			};
			var fail_func = function() {
				erp_instance.ktv_sale.ktv_room_point.app.alert({
					'alert_class': "alert-error",
					'info': "保存开房信息失败!"
				});

			};
			this.model.push().pipe(function(result) {
				//更新包厢状态
				self.room.set(result["room"]);
				//更新操作结果
				self.model.set(result['room_operate']);
				self.close();
			}).then(success_func, fail_func);
		},
		//打印开房条
		print: function() {
			var self = this;
			var room_fee_info = this.room.get_room_fee_info();
			room_fee_info.ready.then(function() {
				var template_var = {
					"room": self.room.export_as_json(),
					'room_fee_info': room_fee_info.export_as_json(),
					'room_opens': self.model.toJSON()
				};
				var print_doc = $(qweb_template("room-opens-bill-print-template")(template_var));
				//处理可见元素
				var print_doc = print_doc.jqprint();
			});
		}
	});

	//单个抵用券信息显示
	widget.SalesVoucherWidget = erp_instance.web.Widget.extend({
		tagName: "tr",
		template_fct: qweb_template('sales-voucher-template'),
		init: function(parent, options) {
			this.model = options.model;
			//model属性发生变化时,删除该信息
			this._super(parent, options);
		},
		renderElement: function() {
			this.$el.html(this.template_fct(this.model.toJSON()));
			return this;
		},
		start: function() {
			this.$(".btn-sales-voucher-clear").click(_.bind(this._remove, this));
		},
		//删除当前数据
		_remove: function() {
			this.model.clear();
			this.destroy();
		}
	});
	//抵用券列表显示界面
	widget.SalesVoucherListWidget = erp_instance.web.Widget.extend({
		template_fct: qweb_template("sales-voucher-list-template"),
		init: function(parent, options) {
			this.model = options.model;
			this.model.bind('change', this._on_change, this);
			this._super(parent, options)
		},
		_on_change: function(the_sv) {
			var a = arguments;
			console.log(a);
			if (!the_sv.get("id")) this.model.remove(the_sv);
			this.renderElement();

		},
		renderElement: function() {
			this.$el.empty();
			this.$el.html(this.template_fct({}));
			this.model.each(function(s) {
				var w = new widget.SalesVoucherWidget(this, {
					model: s
				});
				w.appendTo(this.$('.table'));
			},
			this);
			return this;
		}
	});

	//结账基础类界面
	widget.BaseRoomCheckoutWidget = erp_instance.web.Widget.extend({
		//当前model
		model: new Backbone.Model(),
		//定义时间
		events: {
			"re_calculate_fee": this.on_re_calculate_fee
		},
		init: function(parent, options) {
			this._super(parent, options);
			this.room = options.room;
			//会员信息
			this.member = new model.Member();
			//打折卡信息
			this.discount_card = new model.DiscountCard();
			//信用卡信息
			this.credit_card = new Backbone.Model();
			//抵用券,可以使用多张抵用券
			this.sales_voucher_collection = new Backbone.Collection();
			this.sales_voucher_list_view = new widget.SalesVoucherListWidget(null, {
				model: this.sales_voucher_collection
			});
			//获取结账包厢费用信息
			this.room_fee_info = this.room.get_room_fee_info();
			this.ready = this.room_fee_info.ready;

			//model发生变化时,重新显示计费信息
			this.model.bind('change', this._refresh_fee_table, this);
			//this.on('re_calculate_fee', this, this._refresh_fee_table);

			//抵用券发生变化时,计算抵用券费用
			this.sales_voucher_collection.bind('change', this._re_calculate_sales_voucher_fee, this);

			// table-bordered table-bordered table-bordered会员信息发生变化时重新计算费用
			this.member.bind("change", this.render_member_card_no, this);
			this.member.bind("change", this._re_calculate_fee, this);
			//打折卡信息发生变化时,重新计算费用
			this.discount_card.bind("change", this.render_discount_card_no, this);
			this.discount_card.bind("change", this._re_calculate_fee, this);

			//信用卡支付发生变化时,重绘界面
			this.credit_card.bind("change", this.render_credit_card_no, this);

			//当向服务器端重新请求计算费用时,需要保持客户端目前的信息,包括
			//当前的抵扣券信息
			//信用卡支付被自动设置为0
			//添加re_calculate_fee callback
			//计算优先级别1 免单 2 挂账 3 抵扣券 4 会员卡 5 信用卡
		},
		//向服务器端发起请求,子类可覆盖
		call_server_func: function() {
			return $.Deferred().done().promise();
		},

		//重新计算费用
		_re_calculate_fee: function() {
			var self = this;
			return this.call_server_func().pipe(function(ret) {
				self.model.set(ret);
			}).then(function() {
				self.trigger('re_calculate_fee');
			});
		},
		//re_calculate_fee callback
		//子类可添加callback函数
		on_re_calculate_fee: function() {
			this._re_calculate_sales_voucher_fee();
			this._autoset_pay_type_member_card_fee();
		},
		//重新计算抵用券费用
		_re_calculate_sales_voucher_fee: function() {
			var sales_voucher_fee = 0;
			this.sales_voucher_collection.each(function(s) {
				sales_voucher_fee += s.get("as_money");
			});
			this.model.set({
				'sales_voucher_fee': sales_voucher_fee
			});
		},
		//重新显示费用列表
		_refresh_fee_table: function() {
			//需要将时间转换为本地时间
			console.debug("in _refresh_fee_table:" + this.model.toJSON());
			this.$('.open_time').html(this.model.get('context_open_time'));
			this.$('.close_time').html(this.model.get('context_close_time'));
			this.$('.consume_minutes').html(this.model.get('consume_minutes'));
			this.$('.room_fee').html(this.model.get('room_fee'));
			this.$('.service_fee_rate').html(this.model.get('service_fee_rate'));
			this.$('.service_fee').html(this.model.get('service_fee'));
			this.$('.sum_hourly_fee').html(this.model.get('sum_hourly_fee'));
			this.$('.minimum_fee').html(this.model.get('minimum_fee'));
			this.$('.minimum_fee_diff').html(this.model.get('minimum_fee_diff'));
			this.$('.changed_room_sum_hourly_fee').html(this.model.get('changed_room_sum_hourly_fee'));
			this.$('.changed_room_minutes').html(this.model.get('changed_room_minutes'));
			this.$('.merged_room_hourly_fee').html(this.model.get('merged_room_hourly_fee'));
			this.$('.sum_fee').html(this.model.get('sum_fee'));
			this.$('.discount_fee').html(this.model.get('discount_fee'));
			this.$('.discount_rate').html(this.model.get('discount_rate'));
			this.$('.sum_should_fee').html(this.model.get('sum_should_fee'));
			this.$('.cash_fee').val(this.model.get('cash_fee'));
			this.$('.member_card_fee').val(this.model.get('member_card_fee'));
			this.$('.credit_card_fee').val(this.model.get('credit_card_fee'));
			this.$('.sales_voucher_fee').val(this.model.get('sales_voucher_fee'));
			this.$('.free_fee').val(this.model.get('free_fee'));
			this.$('.act_pay_fee').val(this.model.get('act_pay_fee'));
			this.$('.change_fee').html(this.model.get('change_fee'));
		},
		//自动设置会员卡支付费用
		_autoset_pay_type_member_card_fee: function() {
			if (this.member.get("id")) {
				var balance = this.member.get('balance');
				//当前现金支付和会员卡支付金额合计
				var cash_fee = this.model.get('cash_fee');
				var member_card_fee = this.model.get('member_card_fee');
				//查看member_card余额,
				//如果余额大于当前应支付费用,则直接使用会员卡支付全部款项
				//如果余额小于当期应支付费用,则直接使用全部余额支付
				//如果余额为0,则不支付
				if (balance == 0.0) this.model.set({
					'member_card_fee': 0.0
				});
				else if (balance >= cash_fee + member_card_fee) this.model.set({
					'member_card_fee': cash_fee + member_card_fee
				});
				else this.model.set({
					'member_card_fee': balance
				});
			}
		},
		//重新显示会员信息
		render_member_card_no: function() {
			if (this.member.get("id")) {
				//显示member-card-wrapper
				var member_card_no = this.member.get("member_card_no");
				var member_class = this.member.get("member_class_id");
				var member_name = this.member.get("name");
				var info = member_card_no + "[" + member_class[1] + "]" + "[" + member_name + "]";
				this.$("#member-card-no").html(info);
				this.$('.member-card-wrapper').removeClass('hide');
				//会员卡/储值卡支付方式可用
				if (this.member.get('balance') > 0) {
					this.$('.member_card_fee').attr('disabled', false).focus().select();
				}
				this.$('.member_card_balance').html(this.member.get('balance'));
			}
			else {
				//隐藏member-card-wrapper
				this.$("#member-card-no").html(null);
				this.$('.member_card_fee').attr('disabled', true);
				this.$('.member_card_balance').html(0.0);
				this.$('.member-card-wrapper').addClass('hide');
				this.$('.member-card-balance-warning').addClass('hide');
				this.$('.btn-print,.btn-checkout').removeClass('disabled');
			}
		},
		//重新显示打折卡信息
		render_discount_card_no: function() {
			if (this.discount_card.get("id")) {
				//显示member-card-wrapper
				var card_no = this.discount_card.get("card_no");
				var card_type_id = this.discount_card.get("discount_card_type_id");
				var name = card_type_id[1];
				var info = name + "[" + card_no + "]";
				this.$("#discount-card-no").html(info);
				this.$('.discount-card-wrapper').removeClass('hide');
			}
			else {
				//隐藏member-card-wrapper
				this.$("#discount-card-no").html(null);
				this.$('.discount-card-wrapper').addClass('hide');
			}
		},
		//自动设置信用卡支付费用
		_autoset_pay_type_credit_card_fee: function() {
			if (this.credit_card.get("card_no")) {
				//默认设置信用卡支付金额为全款
				this.model.set({
					'credit_card_fee': this.model.get('cash_fee')
				});
			}
			else this.model.set({
				'credit_card_fee': 0.0
			});
		},
		//显示信用卡信息
		render_credit_card_no: function() {
			if (this.credit_card.get("card_no")) {
				var card_no = this.credit_card.get("card_no");
				this.$("#credit-card-no").html(card_no);
				this.$('.credit-card-wrapper').removeClass('hide');
				this.$('.credit_card_fee').attr('disabled', false).focus().select();
			}
			else {
				this.$("#credit-card-no").html(null);
				this.$('.credit_card_fee').attr('disabled', true);
				this.$('.credit-card-wrapper').addClass('hide');
			}
			this._autoset_pay_type_credit_card_fee();
		},

		start: function() {
			//隐藏其他元素
			$('#room_status').hide();
			$('#room_filter').hide();
			$('#room_list').hide();

			//抵扣券列表
			this.sales_voucher_list_view.$el = this.$('.sales-voucher-list');
			this.sales_voucher_list_view.renderElement();
			this.sales_voucher_list_view.start();

			//会员刷卡绑定
			this.$el.on('click','.btn-member-card-read',_.bind(this.read_member_card, this));
			this.$el.on('click','.btn-discount-card-read',_.bind(this.read_discount_card, this));
			this.$el.on('click','.btn-member-card-clear',_.bind(this.member_card_clear, this));
			this.$el.on('click','.btn-discount-card-clear',_.bind(this.discount_card_clear, this));
			this.$el.on("click",'.btn-credit-card-clear',_.bind(this.credit_card_clear, this));
			//
			this.$el.on("click",'.btn-checkout',_.bind(this._checkout, this));
			this.$el.on("click",'.btn-cancel',_.bind(this.close, this));
			//信用卡支付方式点击
			this.$el.on("click",'.btn-credit-card-input',_.bind(this.open_credit_card_input, this));
			//抵用券方式点击
			this.$el.on("click",'.btn-sales-voucher-input',_.bind(this.open_sales_voucher_input, this));
			//不同付款方式费用变化
			this.$el.on('change','.member_card_fee',_.bind(this._onchange_member_card_fee, this));
			this.$el.on('change','.credit_card_fee',_.bind(this._onchange_credit_card_fee, this));
			this.$el.on('change','.act_pay_fee',_.bind(this._onchange_act_pay_fee, this));
			//TODO 暂时注释
			//this.$('.free_fee').change(_.bind(this._onchange_member_card_fee,this));
			//this.$('.on_credit_fee').change(_.bind(this._onchange_member_card_fee,this));
		},
		close: function() {
            this.$el.off();
			$('#room_status').show();
			$('#room_filter').show();
			$('#room_list').show();
			this.destroy();
		},
		//结账操作
		_checkout: function() {
			var self = this;
			//设置相关属性到model中去,不触发change事件
			this.model.set({
				'member_card': this.member_card,
				'discount_card': this.discount_card,
				'credit_card': this.credit_card,
				'sales_voucher_collection': this.sales_voucher_collection
			},
			{
				silent: true
			});
			var success_func = function() {
				erp_instance.ktv_sale.ktv_room_point.app.alert({
					'alert_class': "alert-success",
					'info': "结账成功,请打印结账单!"
				});
				self.close();
			}
			var fail_func = function() {
				erp_instance.ktv_sale.ktv_room_point.app.alert({
					'alert_class': "alert-error",
					'info': "结账失败,请重新操作!"
				});

			};
			this.model.push().pipe(function(result) {
				self.room.set(result['room']);
				self.model.set(result['room_operate']);

			}).then(success_func, fail_func);
		},
		//会员卡款金额变化的处理
		_onchange_member_card_fee: function() {
			var member_card_fee = parseFloat(this.$('.member_card_fee').val());
			var origin_member_card_fee = this.model.get('member_card_fee');
			if (member_card_fee > this.member.get('balance')) {
				this.$('.member-card-balance-warning').removeClass('hide');
				this.model.set({
					'member_card_fee': origin_member_card_fee
				});
				this.$('.member_card_fee').focus().select();
				this.$('.btn-print').addClass('disabled');
				this.$('.btn-checkout').addClass('disabled');
			}
			else {
				this.$('.member-card-balance-warning').addClass('hide');
				this.model.set({
					'member_card_fee': member_card_fee
				});
				this.$('.btn-print').removeClass('disabled');
				this.$('.btn-checkout').removeClass('disabled');

			}
		},
		//信用卡付款金额变化的处理
		_onchange_credit_card_fee: function() {
            console.debug("credit_card_fee changed");
			var credit_card_fee = parseFloat(this.$('.credit_card_fee').val());
			this.model.set({
				'credit_card_fee': credit_card_fee
			});
		},
		//实付金额变化
		_onchange_act_pay_fee: function() {
			var act_pay_fee = parseFloat(this.$('.act_pay_fee').val());
			this.model.set({
				'act_pay_fee': act_pay_fee
			});

		},
		//读取会员卡
		read_member_card: function() {
			var w = new widget.MemberCardReadWidget(null, {
				model: this.member
			});
		},
		//读取打折卡
		read_discount_card: function() {
			var w = new widget.DiscountCardReadWidget(null, {
				model: this.discount_card
			});

		},
		//打开信用卡录入界面
		open_credit_card_input: function() {
			var w = new widget.CreditCardInputWidget(null, {
				model: this.credit_card
			});
		},
		//打开抵用券录入界面
		open_sales_voucher_input: function() {
			var w = new widget.SalesVoucherInputWidget(null, {
				model: this.sales_voucher_collection
			});

		},
		//清除信用卡记录
		credit_card_clear: function() {
			this.$('#credit_card_no').attr("disabled", true);
			this.credit_card.clear();
			this.model.set({
				'credit_card_fee': 0
			});
		},

		//清除会员卡信息
		member_card_clear: function() {
			this.$('#member_card_no').attr("disabled", true);
			this.member.clear();
			this.model.set({
				'member_card_fee': 0
			});
		},
		//清除打折卡信息
		discount_card_clear: function() {
			this.$('#discount_card_no').attr("disabled", true);
			this.discount_card.clear();
		}
	});

	//包厢买断界面
	widget.RoomCheckoutBuyoutWidget = widget.BaseRoomCheckoutWidget.extend({
		template_fct: qweb_template("room-buyout-template"),
		model: new model.RoomCheckoutBuyout(),
		renderElement: function() {
			var self = this;
			this.$el.html(self.template_fct({
				"model": self.model.toJSON(),
				"room": self.room.toJSON(),
				"room_fee_info": self.room_fee_info.export_as_json(),
				"rooms": erp_instance.ktv_sale.ktv_room_point.get_rooms_by_state('free').toJSON()
			}));
			return this;
		},
		//买断设置发生变化
		_onchange_buyout_config_id: function() {
			this._re_calculate_fee();
		},

		call_server_func: function() {
			var self = this;
			var context = this._get_context();
			return new erp_instance.web.Model('ktv.room_checkout_buyout').get_func('re_calculate_fee')(context);
		},
		//获取当前上下文环境
		_get_context: function() {
			var buyout_config_id = this.$('#buyout_config_id').val();
			var context = {
				room_id: this.room.get("id"),
				buyout_config_id: parseInt(buyout_config_id)
			};
			if (this.member.get("id")) context.member_id = this.member.get("id");

			if (this.discount_card.get("id")) context.discount_card_id = this.discount_card.get("id");

			return context;
		},
		start: function() {
			this._super();
			//买断变化事件
			this.$('#buyout_config_id').change(_.bind(this._onchange_buyout_config_id, this));
			//如果当前无可用买断,则确定按钮不可用
			if (this.room_fee_info.get_active_buyout_config_lines().length == 0) {
				erp_instance.ktv_sale.ktv_room_point.app.alert({
					'alert_class': "alert-error",
					'info': "当前时间没有可用的买断设置!"
				});
				this.close();
			}
			else this._onchange_buyout_config_id();
		}
	});
	//包厢换房-买断界面
	widget.RoomChangeCheckoutBuyoutWidget = widget.BaseRoomCheckoutWidget.extend({
		template_fct: qweb_template("room-change-checkout-buyout-template"),
		model: new model.RoomChangeCheckoutBuyout(),
		init: function(parent, options) {
			this._super(parent, options);
			//获取当前包厢最后一次结账信息
			//重新计算云覅时,刷新界面上的相关显示
			this.on('re_calculate_fee', this, this._refresh_last_checkout);
		},
		renderElement: function() {
			var self = this;
			this.$el.html(self.template_fct({
				//包厢换房-买断对象
				"model": self.model.toJSON(),
				//原包厢对象
				"origin_room": self.room.toJSON(),
				//原包厢费用信息
				"origin_room_fee_info": self.room_fee_info.export_as_json(),
				//当前空闲包厢
				"free_rooms": erp_instance.ktv_sale.ktv_room_point.get_rooms_by_state('free').toJSON()
			}));
			return this;
		},
		//显示买断列表
		_render_buyout_select: function(buyout_list) {
			this.$('.buyout-select-placeholder').empty();
			this.$('.buyout-select-placeholder').html(qweb_template("buyout-select-template")({
				'buyout_config_lines': buyout_list
			}));
			this.$('#changed_buyout_config_id').off();
			this.$('#changed_buyout_config_id').on('change', _.bind(this._onchange_buyout_config_id, this));
		},
		//刷新包厢最后一次结账信息
		_refresh_last_checkout: function() {},

		//选择包厢发生变化
		_onchange_room_id: function() {
			var self = this;
			var changed_room_id = this.$("#changed_room_id").val();
			var changed_room = erp_instance.ktv_sale.ktv_room_point.get("all_rooms").get(changed_room_id);
			var changed_room_fee_info = changed_room.get_room_fee_info();
			self.changed_room = changed_room;
			self.changed_room_fee_info = changed_room_fee_info;
			changed_room_fee_info.ready.then(function() {
				info = changed_room_fee_info.export_as_json();
				self._render_buyout_select(info.active_buyout_config_lines);
				self._re_calculate_fee();
			});
		},
		//买断设置发生变化
		_onchange_buyout_config_id: function() {
			this._re_calculate_fee();
		},

		call_server_func: function() {
			var self = this;
			var context = this._get_context();
			return new erp_instance.web.Model('ktv.room_change_checkout_buyout').get_func('re_calculate_fee')(context);
		},
		//获取当前上下文环境
		_get_context: function() {
			var buyout_config_id = this.$('#changed_buyout_config_id').val();
			var context = {
				origin_room_id: this.room.get("id"),
				changed_room_id: this.changed_room.get("id"),
				changed_buyout_config_id: parseInt(buyout_config_id)
			};
			if (this.member.get("id")) context.member_id = this.member.get("id");
			if (this.discount_card.get("id")) context.discount_card_id = this.discount_card.get("id");

			return context;
		},
		start: function() {
			this._super();
			//买断变化事件
			this.$('#changed_room_id').change(_.bind(this._onchange_room_id, this));
			//如果当前无可用买断,则确定按钮不可用
			if (this.room_fee_info.get_active_buyout_config_lines().length == 0) {
				erp_instance.ktv_sale.ktv_room_point.app.alert({
					'alert_class': "alert-error",
					'info': "当前时间没有可用的买断设置!"
				});
				this.close();
			}
			else this._onchange_room_id();
		}
	});

	//预售-买钟界面
	widget.RoomCheckoutBuytimeWidget = widget.BaseRoomCheckoutWidget.extend({
		template_fct: qweb_template("room-buytime-template"),
		model: new model.RoomCheckoutBuytime(),
		init: function(parent, options) {
			this._super(parent, options);
			this.on('re_calculate_fee', this, this._refresh);
		},
		//重绘制界面
		_refresh: function() {
			//更新赠送时长,到钟时间
			console.debug("重新计算赠送时间:" + this.model.get('present_minutes'));
			this.$("#present_minutes").val(this.model.get("present_minutes"));
			this.$("#close_time").val(this.model.get("context_close_time_str"));
		},

		renderElement: function() {
			var self = this;
			this.$el.html(self.template_fct({
				"model": self.model.toJSON(),
				"room": self.room.toJSON(),
				"room_fee_info": self.room_fee_info.export_as_json()
			}));
			return this;
		},
		//相关字段发生变化
		_onchange_fields: function() {
			this._re_calculate_fee();
		},

		call_server_func: function() {
			var self = this;
			var context = this._get_context();
			return new erp_instance.web.Model('ktv.room_checkout_buytime').get_func('re_calculate_fee')(context);
		},
		//获取当前上下文环境
		_get_context: function() {
			var persons_count = parseInt(this.$('#persons_count').val());
			var fee_type_id = parseInt(this.$("#fee_type_id").val());
			var price_class_id = parseInt(this.$("#price_class_id").val());
			var buy_minutes = parseInt(this.$("#buy_minutes").val());
			var context = {
				"room_id": this.room.get("id"),
				"fee_type_id": fee_type_id,
				"price_class_id": price_class_id,
				"buy_minutes": buy_minutes,
				'persons_count': persons_count
			};
			if (this.member.get("id")) context.member_id = this.member.get("id");

			if (this.discount_card.get("id")) context.discount_card_id = this.discount_card.get("id");

			return context;
		},
		start: function() {
			this._super();
			//设置计费方式为当前包厢默认计费方式
			this.$("#fee_type_id,#price_class_id,#buy_minutes,#persons_count").change(_.bind(this._onchange_fields, this));
			this.$("#fee_type_id").val(this.room.get("fee_type_id")[0])
			this._onchange_fields();
		}
	});

	//刷卡界面
	widget.ScanCardWidget = widget.BootstrapModal.extend({
		template_fct: qweb_template("scan-card-template"),
		osv_name: 'ktv.member',
		domain: function() {
			var input_card_no = this.$('#input_card_no').val();
			return [["member_card_no", '=', input_card_no]]
		},
		init: function(parent, options) {
			//传入界面的对象
			this.model = options.model;
			//当前查询到的对象信息
			this.searched_model = new Backbone.Model();
			this.searched_model.bind("change", this._ok_close, this);
			this._super(parent, options);
		},
		post_open: function() {
			this.$('#input_card_no').focus();
		},

		renderElement: function() {
			this.$el.html(this.template_fct());
			return this;
		},
		start: function() {
			this.$el.on("click",'#btn_search',_.bind(this._search, this));
		},
		//确认关闭
		_ok_close: function() {
			if (this.searched_model.get("id") || this.searched_model.get('card_no')) {
				this.model.set(this.searched_model.attributes);
				this.close();
			}
		},
		//根据member_code查找member
		_search: function() {
			var self = this;
			if (input_card_no != "") {
				model.fetch_by_osv_name(this.osv_name, {
					"domain": this.domain()
				}).pipe(function(result) {
					//未查到卡信息
					if (result.length == 0) {
						self.searched_model.clear();
						self.$(".alert").removeClass('hide');
					}
					else {
						self.$(".alert").addClass('hide');
						self.searched_model.set(result[0]);
					}
				})
			}
			this.$("#input_card_no").focus().select();
		}
	});

	//会员查询界面
	widget.MemberCardReadWidget = widget.ScanCardWidget.extend();
	//打折卡查询界面
	widget.DiscountCardReadWidget = widget.ScanCardWidget.extend({
		osv_name: 'ktv.discount_card',
		domain: function() {
			var input_card_no = this.$('#input_card_no').val();
			return [['card_no', '=', input_card_no]]
		}
	});
	//信用卡卡号录入
	widget.CreditCardInputWidget = widget.ScanCardWidget.extend({
		//重写search方法
		_search: function() {
			var self = this;
			var input_card_no = this.$('#input_card_no').val();
			if (input_card_no != "") {
				self.$(".alert").addClass('hide');
				self.searched_model.set({
					'card_no': input_card_no
				});
			}
			else self.searched_model.clear();
			this.$("#input_card_no").focus().select();
		}
	});
	//抵用券录入
	widget.SalesVoucherInputWidget = widget.ScanCardWidget.extend({
		//重写search 方法
		_search: function() {
			var self = this;
			var input_card_no = this.$('#input_card_no').val();
			if (input_card_no != "") {
				new erp_instance.web.Model('ktv.sales_voucher').get_func('get_active_sales_voucher')(input_card_no).pipe(function(result) {
					//未查到卡信息
					if (!result.id) {
						self.searched_model.clear();
						self.$(".alert").removeClass('hide');
					}
					else {
						self.$(".alert").addClass('hide');
						self.searched_model.set(result);
					}

				});
			}
			else self.searched_model.clear();
			this.$("#input_card_no").focus().select();

		},
		//确认关闭
		_ok_close: function() {
			var id = this.searched_model.get("id");
			if (id) {
				if (!this.model.get(id)) this.model.add(this.searched_model);

				this.close();
			}
		},

	});
	//openerp的入口组件,用于定义系统的初始入口处理
	erp_instance.web.client_actions.add('ktv_room_pos.ui', 'erp_instance.ktv_sale.widget.MainRoomPointOfSale');
	widget.MainRoomPointOfSale = erp_instance.web.Widget.extend({
		template: "RoomPointOfSale",
		init: function() {
			this._super.apply(this, arguments);
			if (erp_instance.ktv_sale.ktv_room_point) throw "ktv_room_point 已初始化.";
			erp_instance.ktv_sale.ktv_room_point = new erp_instance.ktv_sale.model.KtvRoomPoint();
		},
		start: function() {
			var self = this;
			return erp_instance.ktv_sale.ktv_room_point.ready.then(function() {
				self.renderElement();
				erp_instance.ktv_sale.ktv_room_point.app = new erp_instance.ktv_sale.App(self.$el);
				self.$el.on("click",".btn-close",_.bind(self.close, self));
			});
		},
		render: function() {
			return qweb_template("RoomPointOfSale")();
		},
		close: function() {
			erp_instance.ktv_sale.ktv_room_point.timer.stop();
			erp_instance.ktv_sale.ktv_room_point = undefined;
			this.destroy();
		}
	});
};

			//会员信息发生变化时重新计算费用
