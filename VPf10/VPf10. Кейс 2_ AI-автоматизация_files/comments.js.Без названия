$(function() {
	var CHANNELS = {
		NEW_COMMENT : 'new_comment'
		,DELETE_COMMENT : 'delete_comment'
		,PAGE_USERS : 'page_users'
		,TYPING : 'typing'
	};
	var CONSTANTS = {
		TYPING_INTERVAL : 3000
		,MAX_SCROLL : 9007199254740991
		,MAX_SHOW_TYPING_USERS : 3
		,MAX_COMMENTS_PER_PAGE_DIRECTION_DESC : 100
	};
	var SHARED_SELECTORS = {
		SCROLL_TO : '.comments-container'
	};

	var DomHelper = {};
	DomHelper.findForms = function($el) {
		return $el.find('.gc-comment-form');
	};

	DomHelper.removeCommentBlock = function($block) {
		$block.hide(500);
		setTimeout(function(){$block.remove()}, 500);
	};

	var TreeWidget = function($tree) {
		var that = this;

		runOneTimeOnElement($tree, 'gc-comments-tree-widget', function($el) {
			var typingWidget = new TypingBlockWidget($el);

			that.getTypingWidget = function() {
				return typingWidget;
			};

			that.init($el);

			return that;
		});

	};

	TreeWidget.create = function($tree) {
		return new this($tree)
	};

	TreeWidget.applyAccess = function (val, role, $html) {
		if (!val) {// todo проверка валидности window.userInfo.isAdmin вынесение таких проверок в какое то одно место
			$('[data-access-content-type=link]', $html).each(function(){
				var $el = $(this);
				$el.replaceWith($el.html());
			});
			$('[data-access*='+role+']', $html).each(function(){
				var $el = $(this);
				$el.remove();
			});
		}
		else {
			$('[data-access*='+role+']', $html).removeClass('hide');
		}
	};

	/**
	 * Показывает спрятанные комментарии (для isCollapsible)
	 * @param obj
	 * @returns {boolean}
	 */
	TreeWidget.moreComments = function(obj) {
		var hiddenComments = $(obj).parent().nextAll('.comment-level.hide');
		if ( hiddenComments.length ) {
			hiddenComments
				.slice(Math.max(hiddenComments.length - 10, 0), hiddenComments.length)
				.removeClass('hide');
		}
		var length = $(obj).parent().nextAll('.comment-level.hide').length;

		if (length < 1) {
			$(obj).hide();
			$(obj).parents('.comments-container:first').find('.more:first').removeClass('hide');
		} else {
			var hiddenCount = length;
			if ($(obj).attr('data-current-count')) {
				hiddenCount = parseInt($(obj).attr('data-current-count')) - length;
			}
			$(obj).find('span.count').html(hiddenCount);
		}

		return false;
	};

	TreeWidget.resize = function($tree) {
		var scrollToBottomSelector = $tree.data('scroll-to-bottom');
		if (scrollToBottomSelector) {
			// debugger;
			var $container = $tree.find('.comments-container:first');
			var formOuterHeight = $tree.find('.gc-comment-form').outerHeight(true);
			var height = $container.parent().height();
			//console.log(height, formOuterHeight);
			if ( $( window ).width() > 767 ) {
				$container.css('height', (height - formOuterHeight) + 'px');
			} else if ( $( window ).height() < ( $container.outerHeight(true) + 44 ) ) {
				$container.css('height', ($( window ).height() - formOuterHeight - 44 ) + 'px');
			}
			else {
				height = $container.parent().parent().height();
				$container.css('height', (height - formOuterHeight) + 'px');
			}


			var first = $tree.find(SHARED_SELECTORS.SCROLL_TO).get(0);
			first.scrollTop = first.scrollHeight;
		}
	};

	function validateUrl(value) {
		return /^\/\/.*fs.*\.(?:getcourse|gcrc).*\/fileservice\/.*\/thumbnail\/.*$/i.test(value)
			|| value === "/public/img/default_profile_50.png";
	}

	function makeThumbnail(thumbnail) {
		let isValid = false;
		const srcMatches = thumbnail.match(/src=["'](.*?)["']/);
		if (srcMatches !== null) {
			if (validateUrl(srcMatches[1])) {
				isValid = true;
			}
		}
		let src = isValid ? srcMatches[1] : "/public/img/default_profile_50.png";
		return '<img loading="lazy" class="user-profile-image user-default-profile-image" src="'
			+ src
			+ '" width="50">';
	}

	TreeWidget.prototype = {
		init : function($tree) {
			this.initScroll($tree);
			this.initForms($tree);
			this.initComments($tree);
			this.initCommentsQueue($tree);
			this.initMoreLinks($tree);
			this.initDownloadComments($tree);
			this.initHelpdesk($tree);
			this.initWebSocket($tree, window.accountUserWebSocketConnection);
		}
		,initScroll : function($tree) {
			TreeWidget.resize($tree);
			$(window).resize(function () {
				TreeWidget.resize($tree);
			});
		}
		,initForms : function($tree) {
			var that = this;
			DomHelper.findForms($tree).each(function (index, el) {
				CommentFormWidget.create($(el));
			});
		}
		,initComments : function($tree) {
			var that = this;
			$tree.find('.gc-comment').each(function (index, el) {
				CommentWidget.create($(el));
			});
		}
		,initCommentsQueue : function($tree) {
			$tree.data('queue', []);
			$tree.data('paused', 0);
			var $button = $tree.find('.pause');
			$tree.data('pause-button', $button);
			$button.click(function() {
				if (!$tree.data('paused')) {
					$tree.data('paused', 1);
					$(this).find('.text').html('<span class="fa fa-play"></span> Включить обновление');
				}
				else {
					$tree.data('paused', 0);
					var l = $tree.data('queue').length;
					for(var i = 0; i < l; i++) {
						var comment = $tree.data('queue').shift();
						addComment(comment.objectId, comment.objectTypeId, comment.settings, comment.html);
					}
					$(this).find('.text').html('<span class="glyphicon glyphicon-pause"></span> ' + ( window.language == 'en' ? "Disable autoupdate" : "Отключить обновление" ));
					$(this).find('.value').html('');
				}
			});

			var chatCollapsed = window.gcGetCookie("chatCollapsed");

			$tree.parent().find('.chat-collapse-btn').click( function(e ) {
				$tree.parent().addClass('chat-collapsed')
				window.gcSetCookie("chatCollapsed", 1)
				$('.gc-both-main-content').removeClass('container-auto-width');

				if ( $tree.parent().find('.chat-expand-btn').length == 0 ) {
					$expandBtn = $('<div class="chat-expand-btn"><span class="glyphicon glyphicon-triangle-left"></span></div>')
					$tree.parent().click(function () {
						$(this).removeClass('chat-collapsed');
						$('.gc-both-main-content').addClass('container-auto-width');
						window.gcSetCookie("chatCollapsed", 0)
					});

					$expandBtn.appendTo($tree.parent());
				}
				e.stopPropagation();
				e.preventDefault();
			})
			if ( chatCollapsed == 1 ) {
				$tree.parent().find('.chat-collapse-btn').click();
			}
		}
		,initMoreLinks : function($tree) {
			$tree.find('.more a').click(function() {
				var that = this;
				$(this).parent().append('<i class="fa fa-spinner fa-spin"></i>');
				var $container = $($(this).parents('.comments-container').get(0));
				var settings = $($container.find('.settings-level-1').get(0)).find('textarea');
				var asChat = $(this).data('as-chat');
				var direction = $(this).data('direction');

				ajaxCall('/cms/comment/getTree', {
					settings : settings.html()
					,page : $(this).data('page') + 1
					,as_chat : asChat
				}, {}, function(response) {
					if (!response.hasNext) {
						$(that).hide();
					}
					$(that).parent().find('.fa-spinner').remove();
					$(that).data('page', $(that).data('page') + 1);
					$(that).data('clicked', 1);
					var $container = $($(that).parents('.comments-container').get(0));
					var $commentsBlock = $($container.find('.comments').get(0));
					var html = [];
					$.each(response.comments, function(index, comment) {
						html.push(comment.html);
					});
					$(that).html(response.linkText);
					if (asChat) {
						var currentTopElement = $commentsBlock.find('.gc-comment').first();
						var currentBlockHeight = $commentsBlock.outerHeight();
						$commentsBlock.prepend(html.join(''));
						// скроллим окно сообщений к последнему прочитанному
						$container.scrollTop( currentBlockHeight + currentTopElement.offset().top + 120 - 40 );
					}
					else {
						if (direction === 'asc') {
							$commentsBlock.prepend(html.reverse().join(''));
						}
						else {
							$commentsBlock.append(html.join(''));
						}
					}
				}, function() {
					if ( typeof window.checkSelectedComment == 'function' ) {
						window.checkSelectedComment();
					}
				});
				return false;
			})
		}
		,initWebSocket : function($tree, connection) {
			if (!connection) {
				return;
			}
			this.initWebSocketPageUsers($tree, connection);
			this.initWebSocketTreeUsers($tree, connection);
			this.initWebSocketNewComments($tree, connection);
			this.initWebSocketUserTyping($tree, connection);
		}
		,initWebSocketPageUsers: function ($tree, connection) {
			connection.subscribeChannel(CHANNELS.PAGE_USERS + connection.pageKey, function (message, json) {
				$tree.find('.online-users-count').html(json.stat.connections.unique + (window.language == 'en' ? ' online' : ' онлайн'));
			});
		}
		,initWebSocketTreeUsers: function ($tree, connection) {
			var treeId = $tree.data('tree-id');
			connection.subscribeChannel(
				CHANNELS.PAGE_USERS + '_' + treeId,
				function (message, json) {
					$('.' + treeId).each(function (index, el) {
						var cnt = json.stat.connections.unique;
						var $el = $(el);
						var html = '';
						if (cnt > 0) {
							html = cnt + ' ' + Yii.t('common','online');
						}
						$el.find('.online-users-count').html(html);
					});
				}
			);
		}
		,initWebSocketNewComments : function($tree, connection, oldTreeId) {
			var that = this;
			if (!connection) {
				console.log('no socket connection');
				return;
			}
			if (oldTreeId) {
				connection.unsubscribeChannel(CHANNELS.NEW_COMMENT+oldTreeId);
				connection.unsubscribeChannel(CHANNELS.NEW_COMMENT+oldTreeId+window.accountUserId);
				connection.unsubscribeChannel(CHANNELS.DELETE_COMMENT+oldTreeId);
			}
			connection.subscribeChannel(CHANNELS.NEW_COMMENT+$tree.data('tree-id'), function(message, json){newComment(json)});
			connection.subscribeChannel(CHANNELS.NEW_COMMENT+$tree.data('tree-id')+window.accountUserId, function(message, json){newComment(json)});
			connection.subscribeChannel(CHANNELS.DELETE_COMMENT+$tree.data('tree-id'), function(message, json){
				$.each(json.comment_ids, function (index, id) {
					DomHelper.removeCommentBlock($('.comment'+id+'top'));
				});
			});
			function newComment(json) {
				if ('string' === (typeof json)) {
					try {
						json = JSON.parse(json);
					} catch (e) {
						console.log(e, json);
					}
				}
				var commentId = json.comment_id;
				if (!commentId) {
					console.log("empty comment id");
					return;
				}
				that.getTypingWidget().removeUser(json.user_id);
				setTimeout(
					function () {
						addComment(json.object_id, json.object_type_id, json.settings, json.html, true);
					},
					//( Math.random() * 2000 ) + 2000
					0
				);
			}
		}
		,initWebSocketUserTyping : function($tree, connection, oldTreeId) {
			if (!connection || $tree.data('tree-id').match(/need_create/)) {
				return;
			}
			if ($tree.hasClass('comments-tree-show-typing')) {
				var that = this;
				if (oldTreeId) {
					connection.unsubscribeChannel(CHANNELS.TYPING+'_'+oldTreeId);
				}
				connection.subscribeChannel(CHANNELS.TYPING + '_' + $tree.data('tree-id'), function(message, json){
					that.getTypingWidget().addUser(json.user_id, json.user_name, makeThumbnail(json.user_user_thumbnail));
				});
			}
		},
		initDownloadComments: function ($tree) {
			$tree.find('a.download-csv').click(function() {
				var that = this;
				var $container = $($tree.find('.comments-container').get(0));
				var settings = $($container.find('.settings-level-1').get(0)).find('textarea');
				if ( settings.html() ) {
					window.location = '/cms/comment/downloadTree?settings=' + settings.html();
				} else {
					alert('Ошибка экспорта');
				}
				return false;
			})
		},
		initHelpdesk: function ($tree) {
			$tree.find('a.helpdesk-btn').click(function() {
                if (!confirm(Yii.t('helpdesk', 'Вы уверены?'))) {
                    return;
                }
				$(this).attr('disabled', 'disabled');
				ajaxCall($(this).data('href'), {}, {}, function(response) {
					window.location.reload();
				});
			});
		},
	};

	var CommentFormWidget = function($form) {
		var that = this;

		runOneTimeOnElement($form, 'gc-comment-form-widget', function($el) {
			that.init($el);

			return that;
		});
	};

	CommentFormWidget.create = function($form) {
		return new this($form)
	};

	CommentFormWidget.THREAD_COMMENT_HEIGHT = 28;
	CommentFormWidget.REPLY_COMMENT_HEIGHT = 28;

	CommentFormWidget.uploadButtonIndex = 0;

	CommentFormWidget.prototype = {
		textAreaHeight : undefined
		,init : function($form) {
			this.initForm($form);
			this.initTextArea($form, window.accountUserWebSocketConnection);
			this.initUploaders($form);
			this.initModalWindow($form);
			this.initTemplates($form);

			if (window.GcEmojiHelper) {
				window.GcEmojiHelper.initEmojiTextAreas($form);
			}
		}
		,initForm: function ($form) {
			$form.find('form').submit(function (event) {

				var buttonTextGo = 'Отправляется';

				if (typeof Yii != 'undefined') {
					buttonTextGo = Yii.t( "common", "Go" );
				}

				var $this = $(this);
				var $button = $this.find('button');
				$button.attr('disabled', 'disabled');
				var $buttonText = $button.find('.text');
				$buttonText.data('old', $buttonText.html());
				$buttonText.html(buttonTextGo);
				var data = $this.serialize();
				commentAddAjax($this, data, null, function () {
					$this.find('button').removeAttr('disabled');
					$buttonText.html($buttonText.data('old'));
				});
				return false;
			});
		}
		,initTextArea : function($form, webSocketConnection) {
			var $f = $form;
			var that = this;
			var $tree = $form.parents('.comments-tree');

			if (!!window.presaveInLocalStorageComments) {
				var answerId = $form.closest('.user-answer').data('id'),
					localStorageKey = 'new-comment-for-answer-' + answerId,
					localStorageValue = localStorage.getItem(localStorageKey);

				if (!!answerId && !!localStorageValue) {
					$form.find('.new-comment-textarea').val(localStorageValue);
				}
			}

			$form.find('.new-comment-textarea')
				.css('max-height', 200 + 'px')
				.autosize()
				.css('min-height', CommentFormWidget.REPLY_COMMENT_HEIGHT + 'px')
				.css('height', CommentFormWidget.REPLY_COMMENT_HEIGHT + 'px')
				.keyup(function(event) {
					var $that = $(this);
					if ($that.val().length > 0) {
						$that.parents('.new-comment').addClass('active');
						var $form = $that.parents('form');
						if( event.keyCode == 13 && ( event.ctrlKey ) && ( ( $f.data('submit-on-enter') && ! event.shiftKey )  || event.ctrlKey ) ) {
							$form.submit();
						}
					}
					else {
						$that.parents('.new-comment').removeClass('active');
					}

					if (that.textAreaHeight != $f.height()) {
						TreeWidget.resize($tree);
						that.textAreaHeight = $f.height();
					}
					if (webSocketConnection && $tree.hasClass('comments-tree-show-typing')) {
						var channel = CHANNELS.TYPING+'_'+$tree.data('tree-id');
						if (!$that.data('typing')) {
							$that.data('typing', 1);
							if (webSocketConnection && webSocketConnection.getSocket()) {
								webSocketConnection.getSocket().emit('message', {
									json: {
										channel: channel,
										user_id: window.accountUserId,
										user_name: window.accountSafeUserName,
										user_user_thumbnail: window.accountUserThumbnail
									}
								});
							}
							setTimeout(function() {
								$that.data('typing', 0)
							}, CONSTANTS.TYPING_INTERVAL);
						}
					}
				}).change(function(event) {
					var value = $(this).val();

					if (value.length > 0) {
						if (!!window.presaveInLocalStorageComments) {
							localStorage.setItem(localStorageKey, value);
						}
						$(this).parents('.new-comment').addClass('active');
					} else {
						if (!!window.presaveInLocalStorageComments) {
							localStorage.removeItem(localStorageKey);
						}
						$(this).parents('.new-comment').removeClass('active');
					}
				}).focus(function(event){
					$tree.trigger('tree:textarea:focused');
				});

			$form.find('.new-comment-textarea-level-1')
				.autosize()
				.css('min-height', CommentFormWidget.THREAD_COMMENT_HEIGHT + 'px')
				.css('height', CommentFormWidget.THREAD_COMMENT_HEIGHT + 'px')
			;
			TreeWidget.resize($form.parents('.comments-tree'));
			this.textAreaHeight = $form.height();
		}
		,initModalWindow : function($form) {
			$form.find('.auth-link').click(function(e) {
				var active = window.gcModalActive();
				active && active.hide();
				window.gcGetDefaultModalAuth().show();

				return false;
			});
		}
		,initUploaders : function(form) {
			if (!window.userInfo.isInAccount) {
				//return;
			}
			this.initUploader(
				form.find('.comment-attach-file-link'), function($el, $uploader) {
					$uploader.insertAfter($el.parents('.new-comment').find('.btn-send'));
				});
			this.initUploader(
				form.find('.comment-attach-file-for-edit-link'),
				function($el, $uploader) {
					$el.append($uploader);
				}
			);
		}
		,initUploader : function($el, insertCallback, afterCreateCallback) {
			var $uploader = $('<div class="file-uploader" style="max-height: 100px; overflow-y: auto;">');
			$uploader.append('<div class="upload-button"></div>');
			$uploader.append('<input type="hidden" class="upload-value" name="GetCourseComment[files]">');
			insertCallback($el, $uploader);
			var $button = $uploader.find('.upload-button');
			$button.attr('id', 'comment-upload-button' + (CommentFormWidget.uploadButtonIndex++));
			var useFileTypes = $el.parents('.comment-form-wrapper').attr('data-use-file-types');

			// в зависимости от useFileTypes меняется поведение виджета (выбор типов аттачей)
			var options = {
				valueElemSelector: $uploader.find('.upload-value'),
				userId: window.accountUserId,
				buttonText: '<i class="glyphicon glyphicon-paperclip"></i>',
				width: 145,
				removeCompleted: true,
				other : {
					onClearQueue : function() {
						setTimeout(function() {
							TreeWidget.resize($el.parents('.comments-tree'));
						}, 1000);
					},
				}
			};
			if (useFileTypes === '1') {
				options = {
					valueElemSelector: $uploader.find('.upload-value'),
					userId: window.accountUserId,
					buttonText: '<i class="glyphicon glyphicon-paperclip"></i>',
					width: 145,
					itemTemplate : '<div class="uploadifive-queue-item"><span class="filename"></span><div class="close"></div>' +
						'<p class="type_block"></p>' +
						'<span class="fileinfo"></span>' +
						'<div class="progress" <div class="progress-bar"></div></div></div>',
					removeCompleted: true,
					other : {
						onClearQueue : function() {
							setTimeout(function() {
								TreeWidget.resize($el.parents('.comments-tree'));
							}, 1000);
						},
						onCancel : function(file) {
							let hash = file.hash;
							$hiddenInputEl = $(options.valueElemSelector);
							let value = $hiddenInputEl.val();
							if (value) {
								let object = JSON.parse(value);
								object.forEach((item, index, array) => {
									if (item.hash === hash) {
										object.splice(index, 1)
									}
								});
								$hiddenInputEl.val(JSON.stringify(object));
							}
						},

						onUploadComplete:  function (file , res) {
							var hash = res;
							file.hash = hash;
							$hiddenInputEl = $(options.valueElemSelector);

							ajaxCall('/pl/telegram/control/file/check-file',
								{hash: hash, validate: false},
								{method: 'get'},
								function (response) {
									if (response.success === true) {
										let newContent = response.data.content;
										var fileinfo_text = $(newContent).find('.fileinfo').html();

										file.queueItem.find('.fileinfo').html(fileinfo_text);

										var select = $(newContent).find('.change-upload-type');
										select.attr('attr_hash', hash);
										var type_block =
											$('<span>'+Yii.t('widgets', 'Отправить в телеграмм как')+': ' +
												'<span class="type_select"></span></span>');
										type_block.find('.type_select').append(select);
										file.queueItem.find('.type_block').html(type_block);

										let newValue = {"attach_type": select.val(), "hash": hash};
										let hiddenInputValue = $hiddenInputEl.val();
										let hiddenInputValueJson = JSON.parse('[]');
										if (hiddenInputValue !== '') {
											hiddenInputValueJson = JSON.parse(hiddenInputValue);
										}
										hiddenInputValueJson.push(newValue);
										$hiddenInputEl.val(JSON.stringify(hiddenInputValueJson));
									}
								});
						},
					}
				};
			}

			if (window.isEnabledSecureUpload && window.fileserviceUploadHost) {
				options.onUpload = function (filesToUpload, settings) {
					var secureDirectUploadUri = '/fileservice/widget/secure-direct-upload';
					try {
						var session = localStorage.getItem('session');
						var requestParams = {"fs_ref": window.location.href};

						if (session !== undefined && session != null){
							var objSession = jQuery.parseJSON(session);

							if (objSession.hasOwnProperty('user_id') && objSession.user_id != null) {
								requestParams.fs_u = objSession.user_id;
							} else {
								requestParams.fs_u = -1;
							}
						}

						secureDirectUploadUri += '?' + jQuery.param(requestParams);
					} catch (err) {
					}

					$.ajax({
						url: '/fileservice/widget/create-secret-link',
						method: 'GET',
						data: {
							host: window.fileserviceUploadHost,
							uri: secureDirectUploadUri,
							expires: 600
						},
						success: function (data, textStatus, jqXHR) {
							if (data.link) {
								settings.uploadScript = data.link;
							}
						},
						error: function (http, message, exc) {sendCreateLinkError(http, message, exc);},
						async: false // to make it synchronous
					});
				};
			}

			initUploadify($button, options);

			var $uploadifiveButton = $uploader.find('.uploadifive-button');

			var $container = $el.parents('.contains-uploadify').find('.attach-file-button-container');

			$uploadifiveButton.appendTo($container);
			$uploadifiveButton.css('line-height', '20px');
			$uploadifiveButton.height('20px');
			$uploadifiveButton.width('15px');
			$uploadifiveButton.css('background', 'transparent');
			$uploadifiveButton.css('color', '#999');
			$uploadifiveButton.css('text-align', 'center');
			$uploadifiveButton.css('padding', '0');
			$uploadifiveButton.css('font-size', '1em');
			$el.data('uploader', $uploader);

			afterCreateCallback && afterCreateCallback($el, $uploader);
		},
		initTemplates: function($el) {
			$el.find('.template-link').click( function() {
				var id = $(this).data('template-id');

				let userId = $el.parents('.answer-content').find('a[data-user-id]').data('user-id');


				ajaxCall("/pl/notifications/skill-question/get-template?id=" + id, { userId: userId }, {method: "get"}, function(response) {
					var val = $el.find('.new-comment-textarea').val();
					if ( val == "" ) {
						val = response.data.answer;
					}
					else {
						val = val + " " + response.data.answer;
					}
					$el.find('.new-comment-textarea').val( val );
					$el.find('.new-comment-textarea').focus();
					$('.new-comment-textarea', $el).trigger('keyup');
					$('.new-comment-textarea', $el).css('min-height', 100);
				})
			})

		}
	};

	var CommentWidget = function($comment) {
		var that = this;

		runOneTimeOnElement($comment, 'gc-comment-widget', function($el) {
			that.init($el);

			return that;
		});
	};

	CommentWidget.create = function($comment) {
		return new this($comment)
	};

	CommentWidget.prototype = {
		init : function($comment) {
			this.initForms($comment);
			this.initActions($comment);
			this.initFilesFrontPopup($comment);

			if (window.GcEmojiHelper) {
				window.GcEmojiHelper.initEmojies($comment);
			}
		}
		,initForms : function($comment) {
			DomHelper.findForms($comment).each(function (index, el) {
				CommentFormWidget.create($(el));
			});
		}
		,initActions : function($comment) {
			this.initActionsVisual($comment);
			this.initEdit($comment);
			this.initDelete($comment);
			this.initTemplateLink($comment);
		}
		,initActionsVisual : function($comment) {
			window.eachAndRunOneTimeOnElement(
				$comment.find('.comment-edit-link, .comment-delete-link, .comment-template-link'),
				'comment-actions-hidden',
				function ($el) {
					$el.addClass('hide');
					return $el;
				}
			);
			window.eachAndRunOneTimeOnElement(
				$comment.find('.comment-edit-link, .comment-delete-link, .comment-template-link'),
				'comment-mouseout-handler',
				function ($el) {
					$comment.find('.comment')
						.mouseover(function() {
							//alert( JSON.stringify(window.userInfo) );
							$(this).find('.comment-edit-link').removeClass('hide');
							if (window.userInfo.isAdmin) {
								$(this).find('.comment-delete-link').removeClass('hide');
							}
							if(window.userInfo.isHumanDesign == "1" && $(this).find('.comment-delete-link').data( "delete" ) == "1"){
								$(this).find('.comment-delete-link').removeClass('hide');
							}
							if ( window.userInfo.isTeacher ) {
								$(this).find('.comment-template-link').removeClass('hide');
							}
						})
						.mouseout(function() {
							$(this).find('.comment-edit-link, .comment-template-link, .comment-delete-link').addClass('hide');
						})
					;
					return $el;
				}
			);
		}
		,initEdit : function($comment) {
			window.eachAndRunOneTimeOnElement(
				$comment.find('.comment-edit-link'),
				'comment-edit-link-handler',
				function ($el) {
					$el.click(function() {
						var $comment = $(this).parents('.comment');
						$comment.find('.edit-comment-active-element').removeClass('hide');
						$comment.find('.edit-comment-inactive-element').addClass('hide');
						var $textarea = $comment.find('.edit-comment-active-element textarea');
						$textarea.css('min-height', 50 + 'px').autosize();
						return false;
					});
					return $el;
				}
			);

			window.eachAndRunOneTimeOnElement(
				$comment.find('.comment-cancel-edit-link'),
				'comment-cancel-edit-link-handler',
				function ($el) {
					$el.click(function() {
						var $comment = $(this).parents('.comment');
						$comment.find('.edit-comment-active-element').addClass('hide');
						$comment.find('.edit-comment-inactive-element').removeClass('hide');
					});
					return $el;
				}
			);

			window.eachAndRunOneTimeOnElement(
				$comment.find('.save-edited-comment-btn'),
				'comment-save-edited-btn-handler',
				function ($el) {
					$el.click(function() {
						var $btn = $(this);
						var $commentEl = $(this).parents('.comment');
						var toDelete = [];
						$commentEl.find('.delete-file-checkbox:checked').each(function(index, el) {
							toDelete.push($(el).val());
						});
						ajaxCall($commentEl.find('.comment-edit-link').data('href'), {
							text : $commentEl.find('.edited-comment-text').val(),
							files_to_delete : toDelete.join(','),
							files_to_add : $commentEl.find('.upload-value').val()
						}, {
							btn : $btn
						}, function(response) {
							$commentEl.find('.emoji-text').html($.emoji(response.html.text));
							var $files = $commentEl.find('.files');
							$files.html(response.html.files);
							if (response.html.files.length > 0) {
								$files.addClass('active');
							}
							else {
								$files.removeClass('active');
							}
							$commentEl.find('.edit-comment-active-element').addClass('hide');
							$commentEl.find('.edit-comment-inactive-element').removeClass('hide');
							$commentEl.find('.upload-value').val('');
							$commentEl.find('.upload-button').uploadifive('clearQueue');
							$(document).trigger('gc:comment:edited');
						});
					});
					return $el;
				}
			);

		}
		,initDelete : function($comment) {
			window.eachAndRunOneTimeOnElement(
				$comment.find('.comment-delete-link'),
				'comment-delete-link-handler',
				function ($el) {
					$el.click(function() {
						var $this = $(this);
						var id = $this.data('id');
						var ids = [
								id
							]
							,blocks = [
								$($this.parents('.gc-comment').get(0))
							]
						;
						if (confirm('Комментарии будут удалены. Вы уверены?')) {
							ajaxCall('/cms/comment/delete', {
								GetCourseCommentIds : ids
							}, {}, function() {
								$.each(blocks, function (index, block) {
									DomHelper.removeCommentBlock(block);
								});
							});
						}
						return false;
					});
					return $el;
				}
			);
		},
		initTemplateLink : function($comment) {
			window.eachAndRunOneTimeOnElement(
				$comment.find('.comment-template-link'),
				'comment-template-link-handler',
				function ($el) {
					$el.click(function() {
						var $this = $(this);
						var id = $this.data('id');

						var questionDialog = new CommentTemplateDialog();
						questionDialog.open( id );

						return false;
					});
					return $el;
				}
			);
		}
		,initFilesFrontPopup : function($comment) {
			window.eachAndRunOneTimeOnElement(
				$comment.find('.files a'),
				'comment-object-front-popup-handler',
				function ($el) {
					var $this = $el;
					var selector = '.' + [
						'gc-object-front-popup',
						$this.data('object-id'),
						$this.data('object-type-id')
					].join('-');

					var $all = $(selector);
					var $tile = $all.filter('.gc-object-front-popup-clickable-tile');

					if ($tile.length > 0) {
						$this.removeClass('gc-object-front-popup-clickable');
						$this.click(function() {
							$tile.trigger('click');
							return false;
						});
					}
					return $el;
				}
			);
		}
	};

	var TypingBlockWidget = function ($tree) {
		var typingUsers = {};
		var timeouts = {};
		var $block = $tree.find('.typing-text');

		var refresh = function() {
			var messages = [];
			var lastTypingUser = null;
			for (var i in typingUsers) {
				lastTypingUser = typingUsers[i]
				messages.push(typingUsers[i].user_name);
			}
			if (messages.length === 0) {
				$block.html('');
			}
			else {
				var maxLen = CONSTANTS.MAX_SHOW_TYPING_USERS;
				if (messages.length > maxLen) {
					var len = messages.length;
					messages = messages.slice(0, maxLen);
					messages.push('еще '+(len - maxLen))
				}

				if ( messages.length > 1 ) {
					$block.html(messages.join(' и ')+' '+(messages.length > 1 ? 'пишут' : 'пишет'));
				} else {
					const darkTheme = gcGetCookie('gc_inc_dark');

					if (parseInt(darkTheme)) {
						$block.html( "<div class='comment-wrapper'> <div class='comment'>" +
							" <div class='user-image-wrapper'> " + lastTypingUser.user_user_thumbnail + '</div>' +
							' <div class="text-content"><img src="/public/img/type.svg"></div>' + "</div></div>");
					} else {
						$block.html( "<div class='comment-wrapper'> <div class='comment'>" +
							" <div class='user-image-wrapper'> " + lastTypingUser.user_user_thumbnail + '</div>' +
							' <div class="text-content"><img src="/public/img/typing.gif"></div>' + "</div></div>");
					}
				}
			}
		};

		this.addUser = function(userId, userName, userThumbnail) {
			if (window.accountUserId != userId) {
				clearTimeout(timeouts[userId]);
				if (!typingUsers.hasOwnProperty(userId)) {
					typingUsers[userId] = {
						user_id : userId
						,user_name : userName
						,user_user_thumbnail : userThumbnail
					};
				}

				timeouts[userId] = setTimeout(function() {
					delete typingUsers[userId];
					var len = 0;
					for (var i in typingUsers) {
						len++;
					}
					if (len === 0) {
						$block.html('');
					}
				}, CONSTANTS.TYPING_INTERVAL + 1000);
			}
			refresh();
		};

		this.removeUser = function(userId) {
			delete typingUsers[userId];
			clearTimeout(timeouts[userId]);
			refresh();
		};
	};
	var addComment = function(objectId, objectTypeId, settings, html, isNode ) {
		var groupId = settings.values.group > 0 ? settings.values.group : 0;
		var blockClass = 'comments-' + [
			settings.values.object_type_id,
			settings.values.object_id,
			groupId
		].join('-');
		var $commentsBlocks = $('.'+blockClass);
		if ( $commentsBlocks.length == 0 ) {
			return;
		}
		$commentsBlocks.each(function(index, el) {
			var $commentsBlock = $(el);
			var $tree = $($commentsBlock.parents('.comments-tree').get(0));
			if (isNode && $tree.data('paused')) {
				$tree.data('queue').push({
					objectId : objectId
					, objectTypeId : objectTypeId
					, settings : settings
					, html : html
				});
				if ($tree.data('queue').length > CONSTANTS.MAX_COMMENTS_PER_PAGE_DIRECTION_DESC) {
					$tree.data('queue').shift();
				}
				$tree.data('pause-button').find('.value').html('(' + $tree.data('queue').length + ')');
				return;
			}
			var $html = $( html );
			var commentId = $html.find('.comment').data('object-id');
			var $commentExist = $commentsBlock.find('#comment' + commentId);
			if ($commentExist.length > 0) {
				var $commentExistFiles = $commentExist.find('.files');
				var $commentNewFiles = $html.find('.files');
				if ( ! $commentExistFiles.hasClass('active') && $commentNewFiles.hasClass('active') ) {
					$commentExistFiles.replaceWith($commentNewFiles);
				}
				return;
			}
			if (window.accountUserId == settings.accountUserId) {
				$html.addClass('my-comment');
			}
			else {
				$html.removeClass('my-comment');
			}

			var invertOwnUser = $commentsBlock.parents('.invert-own-comment').length > 0;
			if ( (settings.accountUserId == settings.values.own_user_id) != invertOwnUser ) {
				//$html.addClass('own-user-comment');
			}
			else {
				$html.removeClass('own-user-comment');
			}


			TreeWidget.applyAccess(window.userInfo.isAdmin, 'admin', $html);
			TreeWidget.applyAccess(window.userInfo.isManager, 'manager', $html);
			TreeWidget.applyAccess(window.userInfo.isInAccount, 'account', $html);
			TreeWidget.applyAccess(window.userInfo.isTeacher, 'teacher', $html);

			$html.find('.owner').each(function(index, el) {
				var $el = $(el);
				if($el.hasClass('admin') && window.userInfo.isAdmin) {
					return true;
				}
				if (!$el.hasClass('owner_'+window.accountUserId)) {
					$el.remove();
				}
			});

			var size = CommentFormWidget.REPLY_COMMENT_HEIGHT;
			var isDesc = $html.data('direction') == 'desc';
			if (isDesc) {

				$commentsBlock.prepend($html);
			}
			else {
				$commentsBlock.append($html);
			}

			if (isDesc || $tree.hasClass('more-link')) {
				//а todo хотелось бы выводить только видимую облать комментов - динамический page size и валидация, знать комменты перед этим и после
				var $commentsContainer = $($commentsBlock.parents('.comments-container').get(0));
				var commentsLevel1 = $commentsContainer.find('.level-1');
				var $more = $commentsContainer.find('.more');
				var pageSize = settings.values.page_size;
				if ($more.length == 0 || $more.find('a').data('clicked') == 0) {
					var max = settings.values.page_size;
					if (commentsLevel1.length > max) {
						var $lastComment = commentsLevel1.get(isDesc ? commentsLevel1.length - 1 : 0);
						$lastComment.remove();
						if ($more.length == 0) {
							var moreHtml = '<div class="more"> <a href="javascript:void(0);"></a>';
							if (isDesc) {
								$commentsContainer.append(moreHtml);
							}
							else {
								$commentsContainer.prepend(moreHtml);
							}
						}
						var $a = $more.find('a');
						$a.html('Еще комментарии');
						$a.data('page', max/pageSize);
					}
				}
			}

			if (objectId != settings.values.object_id) {
				$commentsBlock.removeClass(blockClass);
				$commentsBlock.addClass('comments-' + [
					settings.values.object_type_id,
					objectId,
					groupId
				].join('-'));
				var $settingsValue = $tree.find('.settings-value');
				var oldSettings = JSON.parse($settingsValue.html());
				oldSettings.values.object_id = objectId;
				$settingsValue.html(JSON.stringify(oldSettings));
				var oldTreeId = $tree.data('tree-id');
				$tree.data('tree-id', [
					'comments'
					,objectId
					,settings.values.object_type_id
					,groupId ? groupId : ''
				].join('-'));
				var widget = $tree.data('gc-comments-tree-widget');
				widget.initWebSocketUserTyping(
					$tree,
					window.accountUserWebSocketConnection,
					oldTreeId
				);
				widget.initWebSocketNewComments(
					$tree,
					window.accountUserWebSocketConnection,
					oldTreeId
				);
				$($tree).trigger('tree:comment:created_object', [objectId, objectTypeId, settings.accountUserId]);
			}

			CommentWidget.create($html);

			$html.find('textarea').autosize().css('min-height', size + 'px');
			$html.find('.new-comment-textarea').css('height', size + 'px');

			const darkTheme = window.gcGetCookie('gc_inc_dark');
			if (parseInt(darkTheme)) {
				$html.find('.comment-wrapper').effect('highlight', {color: "#3a3a3a", duration: 1000 });
			} else {
				$html.find('.comment-wrapper').effect('highlight', { duration: 1000 });
			}

			$(document).trigger('gc:comment:added');
			$($tree).trigger('tree:comment:added', [
				$html.find('.comment:first').data('id'),
				objectId,
				objectTypeId,
				settings.accountUserId,
				window.gcIsActiveTab
			]);
			TreeWidget.resize($tree);
		});
	};

	var commentAddAjax = function($form, data, callback, completeAjaxCallback)
	{
		ajaxCall('/cms/comment/add', data, {}, function( response ) {
			if (response.settings && response.html) {
				addComment( response.object_id, response.object_type_id, response.settings, response.html );
			}
			var uploader, uploadButton, audioUploader;

			if ($form) {
				if (!!window.presaveInLocalStorageComments) {
					var answerId = $('.new-comment-textarea', $form).closest('.user-answer').data('id'),
						localStorageKey = 'new-comment-for-answer-' + answerId;
					localStorage.removeItem(localStorageKey);
				}

				$('.new-comment-textarea', $form).val('').css({height: '28px'}).trigger('keyup');
				$('.new-comment-textarea', $form).siblings('.emoji-wysiwyg-editor').empty();
				uploader = $form.parents('.new-comment').find('.comment-attach-file-link').data('uploader');
				uploadButton = $form.parents('.new-comment').find('.upload-button');

				audioUploader = $form.parents('.new-comment').find('.audio-upload');
			}
			if (audioUploader) {
				audioUploader.html('');
			}

			if ( uploader ) {
				uploader.find('.upload-value').val('');
			}

			if (uploadButton) {
				uploadButton.uploadifive('clearQueue');
			}

			// Очистить все подсказки
			$('.gc-comment .qna-text-element').html('');

			callback && callback();
		}, completeAjaxCallback);
	};

	$(document).on('gc:comment:add:ajax', function(event, $form, data, callback, completeAjaxCallback) {
		commentAddAjax($form, data, callback, completeAjaxCallback);
	});

	$(document).on('gc:comment:submit:form', function(event, $form, callback, completeAjaxCallback) {
		commentAddAjax($form, $form.serialize(), callback, completeAjaxCallback);
	});

	$(document).on('gc:comment:tree:resize', function(event, $tree) {
		TreeWidget.resize($tree);
	});

	window.GcCommentsTreeWidget = TreeWidget;
	window.GcCommentWidget = CommentWidget;

	$(document).on('change', '.change-upload-type', function () {
		let newType = $(this).val();
		let hash = $(this).attr('attr_hash');
		let $hiddenInputEl = $('input.upload-value');
		let object = JSON.parse($hiddenInputEl.val());
		object.forEach((item, index, array) => {
			if (item.hash === hash.trim()) {
				item.attach_type = newType;
			}
		});
		$hiddenInputEl.val(JSON.stringify(object));
	});

	if (!!window.presaveInLocalStorageComments) {
		$(window).on('beforeunload', function (e) {
			var e = e || window.event,
				confirm = false;

			if ($('.answers-list').length) {
				$('.new-comment-textarea:focus').change();
				$('.new-comment-textarea:visible').each(function () {
					if ($(this).val()) {
						confirm = true;
					}
				});
			}

			if (confirm) {
				e.returnValue = 'Leaving the page';
				return 'Leaving the page';
			}
		});
	}
});
