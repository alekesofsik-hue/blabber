(function () {
	var getProp = function (o, name, defaultValue) {
		return undefined === o[name] ? defaultValue : o[name];
	};
	var mainAjaxUrl = '/user/public/user/json';
	var SocialButton = React.createClass({displayName: "SocialButton",
		handleClick: function (e) {
			var self = this;
			ajaxCall(mainAjaxUrl, {
				action: 'social',
				url: window.location.href,
				notContinueProcess: true, // TODO проверить можно ли здесь безусловное -- ДА
				provider_type: this.props.type
			}, {}, function (response) {
				window.location.href = response.data.redirectUrl;
			});
		},
		render: function () {
			return React.createElement("button", {
				className: 'btn btn-'+this.props.type+' btn-social-icon', 
				type: "button", 
				onClick: this.handleClick
				}, 
				React.createElement("i", {className:  'fa fa-' +this.props.type})
			)
		}
	});
	var UserLoginForm = React.createClass({displayName: "UserLoginForm",
		getInitialState: function () {
			return {
				form: {
					email: undefined,
					password: undefined
				}
			};
		},
		handleInputChange: function (e) {
			var form = this.state.form;
			form[e.target.name] = e.target.value;
			this.setState({form: form});
		},
		render: function () {

			var labelEnter = 'Войти';
			var labelRegistration = 'Регистрация';
			var labelEnterEmail = 'Введите ваш эл. адрес';
			var labelEnterPassword = 'Введите пароль';
			var labelRestorePassword = 'Восстановить пароль';

			if (typeof Yii != 'undefined') {
				labelEnter = Yii.t( "common", "Enter" );
				labelRegistration = Yii.t( "common", "Sign up" );
				labelEnterEmail = Yii.t( "common", "Please enter your email" );
				labelEnterPassword = Yii.t( "common", "Enter password" );
				labelRestorePassword = Yii.t( "common", "Restore password" );

			}

			return (
				React.createElement("div", {className: 'form'}, 
					React.createElement("form", null, 
						React.createElement("h3", null, this.props.getTitle(this.props, labelEnter)),
						React.createElement("button", {
							type: "button", 
							className: "btn btn-link absolute top right", 
							onClick: this.props.onSetTab.bind(null, 'register')
							}, labelRegistration
						), 
						React.createElement("div", {className: 'form-field'}, 
							React.createElement("input", {type: "text", 
								   placeholder: labelEnterEmail,
								   className: 'form-control form-field-email', 
								   name: "email", 
								   onChange: this.handleInputChange}
								)
						), 
						React.createElement("div", {className: 'form-field'}, 
							React.createElement("input", {type: "password", 
								   placeholder: labelEnterPassword,
								   className: 'form-control form-field-password', 
								   name: "password", 
								   onChange: this.handleInputChange}
								)
						), 
						this.props.socialButtons, 
						React.createElement("button", {className: 'btn btn-success', 
								onClick: this.send}, this.props.getButtonTitle(this.props, labelEnter)),
						React.createElement("button", {
							type: "button", 
							className: "btn btn-link", 
							onClick: this.props.onSetTab.bind(null, 'remind')
							}, labelRestorePassword
						)
					)
				)
			);
		},
		send: function (e) {
			var self = this;
			e.preventDefault();
			ajaxCall(mainAjaxUrl, {
				email: this.state.form.email,
				password: this.state.form.password,
				action: 'login'
			}, {}, function (response) {
				self.props.onSuccess(getProp(self.props, 'params', {}), response);
			});
		}
	});

	var UserRegisterForm = React.createClass({displayName: "UserRegisterForm",
		getInitialState: function () {
			return {
				form: {
					email: undefined,
					full_name: undefined,
					phone: undefined
				}
			};
		},
		handleInputChange: function (e) {
			var form = this.state.form;
			form[e.target.name] = e.target.value;
			this.setState({form: form});
		},
		render: function () {

			var labelRegistration = 'Регистрация';
			var labelEnter = 'Вход';
			var labelEnterEmail = 'Введите ваш эл. адрес';
			var labelEnterFullName = 'Введите ваше имя и фамилию';
			var labelEnterPhone = 'Введите ваш телефон';
			var labelSignUp = 'Зарегистрироваться';

			if (typeof Yii != 'undefined') {
				labelRegistration = Yii.t( "common", "Registration" );
				labelEnter = Yii.t("common", "Enter");
				labelEnterEmail = Yii.t( "common", "Please enter your email" );
				labelEnterFullName = Yii.t( "common", "Please enter your full name" );
				labelEnterPhone = Yii.t( "common", "Enter your phone" );
				labelSignUp = Yii.t( "common", "Sign up" );
			}

			return (
				React.createElement("div", {className: 'form'}, 
					React.createElement("form", null, 
						React.createElement("h3", null, this.props.getTitle(this.props, labelRegistration)),
						React.createElement("button", {
							type: "button", 
							className: "btn btn-link absolute top right", 
							onClick: this.props.onSetTab.bind(null, 'login')
							}, labelEnter
						), 

						React.createElement("div", {className: 'form-field'}, 
							React.createElement("input", {
								type: "text", 
								placeholder: labelEnterEmail,
								className: 'form-control form-field-email', 
								name: "email", 
								onChange: this.handleInputChange}
								)
						), 
						React.createElement("div", {className: 'form-field'}, 
							React.createElement("input", {
								type: "text", 
								placeholder: labelEnterFullName,
								className: 'form-control form-field-full_name', 
								name: "full_name", 
								onChange: this.handleInputChange}
								)
						), 
						React.createElement("div", {className: 'form-field'}, 
							React.createElement("input", {
								type: "text", 
								placeholder: labelEnterPhone,
								className: 'form-control form-field-phone', 
								name: "phone", 
								onChange: this.handleInputChange}
								)
						), 
                        this.props.socialButtons, 
						React.createElement("button", {className: 'btn btn-success', 
								onClick: this.send}, this.props.getButtonTitle(this.props, labelSignUp))
					)
				)
			);
		},
		send: function (e) {
			var self = this;
			e.preventDefault();
			var params = getProp(this.props, 'params', {});
			var data = {
				email: this.state.form.email,
				full_name: this.state.form.full_name,
				phone: this.state.form.phone,
				action: 'register',
				skip_user_exists: getProp(params, 'skip_user_exists', false)
			};
			ajaxCall(mainAjaxUrl, data, {"enableSimpleSign":true}, function (response) {
				self.props.onSuccess(params, response);
			});
		}
	});

	var UserRemindForm = React.createClass({displayName: "UserRemindForm",
		getInitialState: function () {
			return {
				form: {
					email: undefined
				}
			};
		},
		handleInputChange: function (e) {
			var form = this.state.form;
			form[e.target.name] = e.target.value;
			this.setState({form: form});
		},
		render: function () {

			var labelForgotPassword = 'Забыли пароль?';
			var labelEmail = 'Эл. адрес';
			var labelEnterEmail = 'Введите ваш эл. адрес';
			var labelSendToMail = 'Отправить на почту';
			var labelReturn = 'Вернуться';

			if (typeof Yii != 'undefined') {
				labelForgotPassword = Yii.t( "common", "Forgot password?" );
				labelEmail = Yii.t( "common", "Email" );
				labelEnterEmail = Yii.t( "common", "Please enter your email" );
				labelSendToMail = Yii.t( "common", "Send to mail" );
				labelReturn = Yii.t( "common", "Return" );
			}

			return (
				React.createElement("div", {className: 'form'}, 
					React.createElement("form", null, 
						React.createElement("h3", null, this.props.getTitle(this.props, labelForgotPassword)),

						React.createElement("div", {className: 'form-group'}, 
							React.createElement("label", null, labelEmail),

							React.createElement("div", null, 
								React.createElement("input", {
									type: "text", 
									placeholder: labelEnterEmail,
									className: 'form-control', 
									name: "email", 
									onChange: this.handleInputChange}
									)
							)
						), 
						React.createElement("button", {className: 'btn btn-primary', 
								onClick: this.send}, this.props.getButtonTitle(this.props, labelSendToMail)),

						React.createElement("button", {
							type: "button", 
							className: "btn btn-link", 
							onClick: this.props.onSetTab.bind(null, 'login')
							}, labelReturn
						)
					)
				)
			);
		},
		send: function (e) {
			var self = this;
			e.preventDefault();
			ajaxCall(mainAjaxUrl, {
				email: this.state.form.email,
				action: 'remind'
			}, {}, function (response) {
				var params = getProp(self.props, 'params', {});
				params.reload = getProp(params, 'reload', false);
				params.callback = getProp(params, 'callback', function (widget, response) {
					widget.setTab('login');
				});
				self.props.onSuccess(params, response);
			});
		}
	});

	var UserForm = React.createClass({displayName: "UserForm",
		getInitialState: function () {
			var params = getProp(this.props, 'params', {});
			return {
				tab: getProp(params, 'tab', 'register'),
				show: getProp(params, 'show', true),
				showSocialAuth: getProp(params, 'showSocialAuth', false)
			};
		},
		_getItems: function () {
			var self = this;
			var params = getProp(this.props, 'params', {});
			var socialButtons = this.renderSocialButtons();
			return [
				{
					id: 'login',
					render: function () {
						return React.createElement(UserLoginForm, {
							onSetTab: self.setTab, 
							params: params.login, 
							onSuccess: self.handleSuccess, 
							getTitle: self.getTitle, 
							getButtonTitle: self.getButtonTitle, 
							socialButtons: socialButtons}
							);
					}
				},
				{
					id: 'register',
					render: function () {
						return React.createElement(UserRegisterForm, {
							onSetTab: self.setTab, 
							params: params.register, 
							onSuccess: self.handleSuccess, 
							getTitle: self.getTitle, 
							getButtonTitle: self.getButtonTitle, 
							socialButtons: socialButtons}
							);
					}
				},
				{
					id: 'remind',
					render: function () {
						return React.createElement(UserRemindForm, {
							onSetTab: self.setTab, 
							params: params.remind, 
							onSuccess: self.handleSuccess, 
							getTitle: self.getTitle, 
							getButtonTitle: self.getButtonTitle}
							);
					}
				}
			].map(function (item) {
					var classes = [];
					if (item.id != self.state.tab) {
						classes.push('hide');
					}
					return React.createElement("div", {className: classes.join(' ')}, item.render());
				});
		},
		render: function () {
			var classes = ['gc-user-form-widget'];
			if (!this.state.show) {
				classes.push('hide');
			}
			return (
				React.createElement("div", {className: classes.join(' ')}, 
					this._getItems()
				)
			);
		},
		setTab: function (id, e) {
			this.setState({
				tab: id
			});
			e && e.preventDefault();
		},
		show: function () {
			this.setState({show: true});
		},
		hide: function () {
			this.setState({show: false});
		},
		toggleShow: function () {
			this.setState({show: !this.state.show});
		},
		handleSuccess: function (params, response) {
			if (params.callback) {
				params.callback(this, response);
			}
			else {
				getProp(params, 'reload', true) && window.location.reload();
				params.hash && $(document).scrollTop($('#' + params.hash).offset().top);
				params.url && (document.location.href = params.url);
			}
		},
		getTitle: function (o, defaultVal) {
			var params = getProp(o, 'params', {});
			return getProp(params, 'title', defaultVal);
		},
		getButtonTitle: function (o, defaultVal) {
			var params = getProp(o, 'params', {});
			return getProp(params, 'buttonTitle', defaultVal);
		},
		renderSocialButtons: function () {
			var buttons = [
				{
					label: 'Facebook',
					type: 'facebook'
				},
				{
					label: 'ВКонтакте',
					type: 'vk'
				},
				{
					label: 'Google+',
					type: 'google-plus'
				}
			];

			return this.state.showSocialAuth ? (React.createElement("div", {className: "social-buttons"}, 
				buttons.map(function (item) {
					return React.createElement(SocialButton, {type: item.type});
				})
			)) : '';
		}
	});

	var uidInit = 0;

	window.UserFormFactory.registerCallback(function (el, params, callback) {
		var id = 'gc-user-form-widget-' + (uidInit++);
		var widget = React.render(React.createElement(UserForm, {
			id: id, 
			params: params}
			), el);
		if (callback) {
			callback(widget);
		}
	});
})();