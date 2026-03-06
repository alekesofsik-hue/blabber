function Stopwatch(config) {
	config = config || {};
	this.element = config.element || {};
	this.previousTime = config.previousTime || new Date().getTime();
	this.paused = config.paused && false;
	this.elapsed = config.elapsed || 0;
	this.countingUp = config.countingUp && false;
	this.timeLimit = config.timeLimit || (this.countingUp ? 60 * 10 : 0);
	this.updateRate = config.updateRate || 1000;
	this.timer = null;
	this.onTimeUp = config.onTimeUp || function() {
		this.stop();
		this.loadReloadButton();
		$(this.element).parent().hide();
	};
	this.onTimeUpdate = config.onTimeUpdate || function() {
		var t = this.elapsed,
			d = Math.floor(t / (3600000 * 24)),
			h = ('0' + (Math.floor(t / 3600000) - d * 24)).slice(-2),
			m = ('0' + Math.floor(t % 3600000 / 60000)).slice(-2),
			s = ('0' + Math.floor(t % 60000 / 1000)).slice(-2);
		var formattedTime = h + ':' + m + ':' + s;

		if (d) {
			var formatTranslated = d + ' день';
			if (typeof Yii != 'undefined') {
				formatTranslated = Yii.t('common', '{n} день|{n} дня|{n} дней', {n: d});
			}
			formattedTime = ' ' + formatTranslated + ' ' + formattedTime;
		}
		$(this.element).html(formattedTime);
	};
	if (!this.paused) {
		this.start();
	}
}
jQuery.widget( 'gc.testingWidget', {
	options: {
		questionaryId: null,
		questionaryAnswerId: null,
		objectTypeId: null,
		objectId: null,
		showRestartBtnAlways: false,
		onFinish: null,
		onQuestion: null,
		scrollToQuestionary: false,
		limitTimeAnswer: null,
        questionaryHasGapTestQuestion: false
	},
	_create: function() {
		var self = this;
		this.element.addClass("testing-widget");
		this.testingContent = this.element.find('.testing-content');
		this.qData = {};
		this.isLastQuestion = false;
		this.qrid = null;
		this.intervalAnswerTimer = -1;
		self.initHtml();

		//self.load();

	},
	t: function (type, value) {
		if (typeof Yii != 'undefined') {
			value = Yii.t(type, value);
		}

		return value;
	},
	load: function() {
		var self = this;

		var spinner = $('<span>')
				.addClass('fa')
				.addClass('fa-spin')
				.addClass('fa-spinner'),
			spinnerWrapper = $('<div>')
				.css({'width':'1em','margin':'0 auto'});

		spinnerWrapper.append( spinner );
		this.testingContent.append( spinnerWrapper );
		if ( this.isLastQuestion ) {
			var title = "Preparing the results";
			if (typeof Yii != 'undefined') {
				title = Yii.t("common", title);
			}
			var loadingTitle = $('<div>')
				.css({'text-align':'center'})
				.html(title);
			this.testingContent.append( loadingTitle );
		}

		ajaxCall( "/pl/teach/questionary-public/testing?id=" + this.options.questionaryId, this.options, {}, function( response ) {
			if (response.data.needAuth) {
				self.createAuthErrorBlock();
				return false;
			}

			self.deleteAuthErrorBlock();

			self.testingContent.html( response.data.resultHtml );
			/*
			if ( response.data.resultHash ) {
				self.qData = JSON.parse( window.atob( response.data.resultHash ) );
			}
			*/
			self.isLastQuestion = response.data.isLastQuestion;
			self.qrid = response.data.qrid;
			self.initHtml();


			var startBlock = self.testingContent.find('#startBlock').data('start-questionary-id');
			//	Лимит времени на ответы
			if(self.options.limitTimeAnswer && self.isLastQuestion === 0 && typeof startBlock === 'undefined'){

				if(typeof self.intervalAnswerTimer !== 'undefined' && self.intervalAnswerTimer != -1){
					clearInterval(self.intervalAnswerTimer);
					self.intervalAnswerTimer = -1;
					$("#answerTimer").remove();
					$("#limitProgressBar").remove();
				}

				var limitTimeAnswer = $('<div id="answerTimer">')
					.css({'text-align':'center'})
					.html( "Время на ответ: " + self.options.limitTimeAnswer );

				var limitProgressBar = $('<div id="limitProgressBar">')
					.css({'width':'200px', 'background-color': '#ddd', 'margin': '0 auto', 'margin-top': '10px'});

				var limitBar = $('<div id="limitBar">')
					.css({'width':'200px', 'background-color': '#4CAF50', 'height': '5px'});

				limitProgressBar.append( limitBar );

				self.testingContent.append( limitTimeAnswer );

				self.testingContent.append( limitProgressBar );

				var n = self.options.limitTimeAnswer;
				var w = 200/n;

				self.intervalAnswerTimer  = setInterval(function () {
					$('#answerTimer').html("Время на ответ: " + n);
					self.testingContent.find('#limitBar').width( w * n );
					n--;
					if (n < 0) {
						clearInterval(self.intervalAnswerTimer);
						self.intervalAnswerTimer = -1;
						$("#answerTimer").remove();
						$("#limitProgressBar").remove();

						self.testingContent.find('.btn-send-variant').attr('disabled', true);
						var questionId = self.testingContent.find('.btn-send-variant').data('question-id');

						var params = {
							questionaryId: self.questionaryId,
							questionaryAnswerId: self.questionaryAnswerId,
							questionId: questionId,
							objectTypeId: self.options.objectTypeId,
							objectId: self.options.objectId,
							answerTimeEnd: 1
						};

						ajaxCall("/pl/teach/questionary-public/do-question-answer", params, {}, function (response) {
							self.showResult(response);
						});
					}
				}, 1000);
			}
			if (response.data.restartTimer && response.data.resultHash === undefined) {
				ajaxCall("/pl/teach/questionary-public/restart-timer?id=" + self.options.questionaryId, {}, {}, function (newResponse) {
					if (response.data.needAuth) {
						self.createAuthErrorBlock();
						return false;
					}

					self.deleteAuthErrorBlock();

					if (newResponse.data.restartTimer) {
						self.showRestartTimer(newResponse.data.restartTimer);
					}
				});
			}
		} );

	},
	showResult: function( response ) {
		var self = this;
		if (response.data.needAuth) {
			self.createAuthErrorBlock();
			return false;
		}

		self.deleteAuthErrorBlock();

		if (response.data.questionaryAnswerId) {
			self.options.questionaryAnswerId = response.data.questionaryAnswerId;
		}

		this.testingContent.find('.js__btn-variant').attr('disabled', true);
		if ( response.data.answerStatuses ) {
			for ( var value in response.data.answerStatuses ) {
				this.testingContent.find('.js__btn-variant').each( function( index, el ) {
					if ( $(el).data('value') == value ) {
						$(el).addClass("btn-" + response.data.answerStatuses[value] );
						if( response.data.variantComments[value] ) {
							var comment = $('<div>')
								.addClass( response.data.answerStatuses[value] )
								.html( response.data.variantComments[value] );
							$(el).after( comment );
						}
					}
				});
			}
		}

        const $gapWords = $('.gap-words');
        const $gapText = $('.gap-text');
        if ((response.data.variantRightValues ?? []).length > 0 && $gapText.length === 1 && $gapWords.length === 0) {
            var variantRightValues = $('<div>')
                .html(
                    '<div style="color: #4cae4c; font-weight: bold">' + Yii.t('teach', 'Правильный ответ:') + '</div>'
                    + response.data.variantRightValues.map(item => item.split(':')[1].replace(/\|/g, '/')).join(', ')
                );
            $gapText.after(variantRightValues);
        }

		if ( response.data.answerResult ) {
			var $div = $( '<div class="answer-result"><h3 class="answer-header"></h3><div class="answer-text"></div></div>' );
			$div.find('.answer-text').html( response.data.answerResult.text );
            if (window.newTestsFeature && response.data.answerResult.gapRightText) {
                $div.find('.answer-text').css({'font-size': '20px', 'text-align': 'center'});
                if (response.data.answerResult.type === 'success') {
                    $div.find('.answer-text').css({'color': '#4CAE7B'});
                } else {
                    $div.find('.answer-text').css({'color': '#FF0000'});
                }
            }
			$div.appendTo( self.testingContent.find('.question-answer-block .button-list') );
		}

		if ( response.data.showResultSeconds > 0 ) {
			setTimeout( function() {
				if ( self.isLastQuestion && self.qrid && $('.gc-share-links').length > 0 ) {
					window.location.href = window.location.href + ( window.location.search ? '&' : '?' ) + 'qrid=' + self.qrid;
				} else {
					self.load();
				}
			}, response.data.showResultSeconds * 1000 );
		}
		else {
			var $btnNext = $("<button type='button' class='btn btn-primary btn-default btn-next-question'> <span class='fa fa-angle-double-right'></span> " + (window.language == "en" ? "Next question" : this.t('common', 'Следующий вопрос')) + "</button>");
			if ( self.isLastQuestion ) {
				$btnNext.html("<span class='fa fa-check'></span> " + (window.language == 'en' ? 'Results' : this.t('common', 'Результаты')));
			}
			$btnNext.appendTo(self.testingContent.find('.question-answer-block .button-list'));
			$btnNext.click(function () {
				$(this).prop('disabled', true);
				if ( self.isLastQuestion && self.qrid && $('.gc-share-links').length > 0 ) {
					window.location.href = window.location.href + ( window.location.search ? '&' : '?' ) + 'qrid=' + self.qrid;
				} else {
					self.load();
				}
				if (self.isLastQuestion) {
					ajaxCall("/pl/teach/questionary-public/restart-timer?id=" + self.options.questionaryId, {}, {}, function (newResponse) {
						if (response.data.needAuth) {
							self.createAuthErrorBlock();
							return false;
						}

						self.deleteAuthErrorBlock();

						if (newResponse.data.restartTimer) {
							self.showRestartTimer(newResponse.data.restartTimer);
						}
					});
				}
			});
		}
	},
	initHtml: function() {
		var self = this;

		if ( this.options.scrollToQuestionary && $('.editor-control-panel').length === 0 ) {
			var top = self.testingContent.offset().top;
			if ( top ) {
				$(window).scrollTop( top );
			}
		}

		this.testingContent.find('.btn-mark-variant').on('click', function(e) {
			e.preventDefault();
			var value = $(this).data('value');
			var questionId = $(this).data('question-id');
			var sendAnswerButton = self.testingContent.find('.btn-send-variant');
			var answer = [];

			if (!questionId) {
				alert(window.language == "en" ? "Question not set" : "Не указан вопрос");
				return;
			}

			$(this).attr('data-marked', ($(this).attr('data-marked') == '1' ? '0' : '1'));

			var variants = self.testingContent.find('.btn-mark-variant[data-marked="1"]');

			variants.each(function (i, item){
				answer.push($(item).attr('data-value'));
			});

			if (variants.length > 0) {
				sendAnswerButton.show();
			} else {
				sendAnswerButton.hide();
			}

			sendAnswerButton.attr('data-value', JSON.stringify(answer));
		});

		this.testingContent.find('.btn-send-variant').on('click', function(e) {
			e.preventDefault();
			$(this).closest('.button-list').find('.btn-send-variant').off('click');
			var value = $(this).data('value');
			var questionId = $(this).data('question-id');

			if (!questionId) {
				alert(window.language == "en" ? "Question not set" : "Не указан вопрос");
				return;
			}

			$(this).attr('disabled', true);
			$("#answerTimer").remove();
			$("#limitProgressBar").remove();
			clearInterval(self.intervalAnswerTimer);
			self.intervalAnswerTimer = -1;

			var params = {
				questionaryId: self.questionaryId,
				questionaryAnswerId: self.questionaryAnswerId,
				questionId: questionId,
				objectTypeId: self.options.objectTypeId,
				objectId: self.options.objectId,
				answerValue: value
			};

			ajaxCall("/pl/teach/questionary-public/do-question-answer", params, {}, function (response) {
				self.showResult(response);
			});

		});

		this.testingContent.find('.btn-restart').on('click', function(e) {

			e.preventDefault();
			$(this).attr('disabled', true);

			var questionaryAnswerId = $(this).data('questionary-answer-id');
			var questionaryId = $(this).data('questionary-id');
			let isTestV2Enabled = window.appHandleAction && window.isTestingV2 && window.testingV2VersionCheck
				&& window.isEnabledMobileTesting;
			let isTestModalEnabled = window.appHandleAction && window.isTestingV2 && !window.testingV2VersionCheck
				&& (window.location.search.indexOf('version=old') === -1) && window.isEnabledMobileTesting;

			if (!questionaryId) {
				alert(window.language == 'en' ? 'Error' : 'Ошибка');
				return;
			}

			var isStart = $(this).hasClass('start-btn') ? '1' : '0';

			//TODO: тексты заменить на Yii.t
			var questionlLabel = 'Do you really want to start the test again?';
			if (typeof Yii != 'undefined') {
				questionlLabel = Yii.t("common", questionlLabel);
			}
			if (isStart === '0' && !confirm(questionlLabel)) {
				$(this).attr('disabled', false);
				return false;
			}

			if (isStart === '0') {
				self.options.questionaryAnswerId = null;
			}

            if (isTestV2Enabled && !self.options.questionaryHasGapTestQuestion) {
				if (isStart === '0') {
					window.appHandleAction({
						type: 'navigate',
						url: location.origin
							+ `/c/qa/reset/${questionaryId}/${window.lessonId}`
					});
				} else {
					window.appHandleAction({
						type: 'navigate',
						url: location.origin
							+ `/c/sa/questionaryv2/${questionaryId}/lesson/${window.lessonId}`
					})
				}
				$(this).attr('disabled', false);

				return false;
			}

			var restartData = {
				objectTypeId: self.options.objectTypeId,
				objectId: self.options.objectId
			};
			if (window.declinedAnswerId) {
				restartData['declinedAnswerId'] = window.declinedAnswerId;
			}
			ajaxCall( "/pl/teach/questionary-public/restart?id=" + questionaryId + "&start=" + isStart, restartData, {}, function( response ) {
				if (response.data.needAuth) {
					self.createAuthErrorBlock();
					return false;
				}

				self.deleteAuthErrorBlock();

				if (response.data.restartTimer) {
					self.showRestartTimer(response.data.restartTimer);
					return;
				}
				if (response.data.answerId) {
					self.questionaryAnswerId = response.data.answerId;
				}
				if ( window.location.search.indexOf('qrid=') >= 0 ) {
					var sourceURL = window.location.href;
					var rtn = sourceURL.split("?")[0],
						param,
						params_arr = [],
						queryString = (sourceURL.indexOf("?") !== -1) ? sourceURL.split("?")[1] : "";
					if (queryString !== "") {
						params_arr = queryString.split("&");
						for (var i = params_arr.length - 1; i >= 0; i -= 1) {
							param = params_arr[i].split("=")[0];
							if (param === 'qrid') {
								params_arr.splice(i, 1);
							}
						}
						if ( params_arr.length ) {
							rtn = rtn + "?" + params_arr.join("&");
						}
					}
					window.location.href = rtn;
				} else {
					self.load();
				}
				if (isTestModalEnabled) {
					window.appHandleAction({
						type: 'navigate',
						url: location.origin
							+ `/c/sa/outdated-version-test-v2/${window.lessonId}`
					});
				}
			} );

			$(this).attr('disabled', false);
		});
	},
	isAuthErrorBlockShown: false,
	createAuthErrorBlock: function () {
		if (self.isAuthErrorBlockShown) {
			return;
		}
		let link = '/cms/system/login';
		link += '?returnUrl=' + location.pathname + location.search;
		const styles =
			"padding: 10px;" +
			"font-family: 'Roboto';" +
			"max-width: 600px;" +
			"margin-top: 10px;" +
			"border: 1px solid #ddd;" +
			"border-radius: 3px;" +
			"text-align: center;";
		const wrapperHtml = "";
		const html = "<div style=\"position: fixed; width: 100%; z-index: 9999;\">"
			+ "<div id='auth-error' class='bg-danger center-block mt-3' style=\"" + styles + "\">"
			+ this.t("apps.teach", "Необходимо ")
			+ `<a href=${link}>` + this.t("apps.teach", "авторизоваться") + "</a>"
			+ this.t("apps.teach", " для прохождения тестирования")
			+ "</div>"
			+ "</div>";

		$("body").prepend($(html));
		self.isAuthErrorBlockShown = true;
	},
	deleteAuthErrorBlock: function () {
		$("div#auth-error").remove();
		self.isAuthErrorBlockShown = false;
	},
	showRestartTimer: function (restartTimer) {
		var self = this;
		setTimeout(function () {
			var restartTimerBlock = self.testingContent.find('.has-restart-timer');
			restartTimerBlock.show();
			self.testingContent.find('.has-restart-button').hide();
			self.testingContent.find('.has-restart-button .btn-restart').attr('disabled', false);
			self.testingContent.find('.has-restart-text').hide();
			new Stopwatch({
				element: $('.testing-restart-timer'),
				elapsed: restartTimer * 1000,
			});
		}, 100);
	}
});


Stopwatch.prototype.start = function() {
	this.paused = false;
	this.previousTime = new Date().getTime();
	this.keepCounting();
};

Stopwatch.prototype.getReloadButton = function () {
	var questionaryId = $(this.element).first().attr('data-questionary-id');
	var attemptCount = $(this.element).first().attr('data-attempt-count');

	return '<div class="row">' +
		'<div class="col-md-12" style="text-align: center">' +
		'<button type="button" class="btn btn-default btn-restart" data-questionary-id="' + questionaryId + '">' +
		'<span class="fa fa-refresh"></span>' +
		this.t('apps.teach', 'Начать заново') +
		'</button>' +
		'</div>' +
		'</div>' +
		'<br>' +
		'<div class="text-center pt-1 fsz-14px">' +
		attemptCount +
		'</div>';
};

Stopwatch.prototype.loadReloadButton = function () {
	var testingRestartButton = $(this.element).parent().parent().find('.has-restart-button');
	var testRestartText = $(this.element).parent().parent().find('.has-restart-text');
	if (testingRestartButton === undefined) {
		$(this.element).parent().parent().append(this.getReloadButton());
	} else {
		testingRestartButton.show();
	}
	if (testRestartText) {
		testRestartText.show();
	}
};

Stopwatch.prototype.t = function (type, value) {
	if (typeof Yii != 'undefined') {
		value = Yii.t(type, value);
	}
	return value;
};

Stopwatch.prototype.keepCounting = function() {
	if (this.paused) {
		return true;
	}
	var now = new Date().getTime();
	var diff = (now - this.previousTime);
	if (!this.countingUp) {
		diff = -diff;
	}
	this.elapsed = this.elapsed + diff;
	this.previousTime = now;
	this.onTimeUpdate();
	if ((this.elapsed >= this.timeLimit && this.countingUp) || (this.elapsed <= this.timeLimit && !this.countingUp)) {
		this.stop();
		this.onTimeUp();
		return true;
	}
	var that = this;
	this.timer = setTimeout(function() {
		that.keepCounting();
	}, this.updateRate);
};

Stopwatch.prototype.stop = function() {
	this.paused = true;
	if (this.timer) {
		clearTimeout(this.timer);
	}
};
