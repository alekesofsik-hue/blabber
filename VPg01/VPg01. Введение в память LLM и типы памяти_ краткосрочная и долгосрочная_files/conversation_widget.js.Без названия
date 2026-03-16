jQuery.widget( 'gc.conversationWidget', {
	options: {
		conversationParams: null,
	},
	_create: function() {
		this.loadConversation( this.options.conversationParams );
	},
	loadConversation: function( id ) {
		var self = this;
		ajaxCall( "/pl/talks/conversation/get" , this.options.conversationParams, {}, function( response ) {
			self.element.html( response.data.html );
			//var $tree = self.element.find('.comments-tree');
			//var $lastComment = $tree.find('.gc-comment:last');
			//if ($lastComment) {
			//	var settings = JSON.parse($lastComment.find('.comment-user-settings-json').html());
			//	var $lastCommentHtml = $lastComment.find('.comment');
			//	$($tree).trigger('tree:comment:added', [
			//		$lastCommentHtml.data('id'),
			//		settings.values.object_id,
			//		settings.values.object_type_id,
			//		$lastCommentHtml.data('user-id'),
			//		window.gcIsActiveTab
			//	]);
			//}
		} )
	}
} );


jQuery.widget( 'gc.conversationAnnotate', {
	options: {
		conversation: null,
		proLabel: ''
	},
	isHashToastLoaded: false,
	_create: function() {
		this.textEl = this.element.find('.conversation-text')
		this.textEl.addClass("emoji-text")

        this.freshCommentEl = this.element.find('.conversation-fresh-comment-count')
		if ( this.options.conversation ) {
			this.setConversation( this.options.conversation );
		}
	},
	setConversation: function( conversation ) {
		this.element.addClass( 'conversation-' + conversation.id )

		this.showConversation( conversation )
		this.freshCommentEl.html( conversation.fresh_comment_count )
        this.freshCommentEl.data('fresh-comment-count', conversation.fresh_comment_count)

        if ( conversation.fresh_comment_count > 0 ) {
            this.freshCommentEl.show();
        }
        else {
            this.freshCommentEl.hide();
        }

		this.subscribeToConversation( conversation.id )

	},
	showConversation: function( conversation ) {
		let proLabel = this.options.proLabel;

		this.element.find('.conversation-img').html( conversation.image )
		this.element.find('.conversation-title').html(conversation.title + " " + proLabel)
        this.element.find('.conversation-object-title').html( conversation.object_title )

        var onlineEl = this.element.find('.conversation-user-is-online');
        if ( onlineEl.length > 0 ){
            if ( conversation.main_user_is_online ) {
                onlineEl.addClass('is-online');
                onlineEl.removeClass('is-offline');
            }
            else {
                onlineEl.addClass('is-offline');
                onlineEl.removeClass('is-online');
            }
        }

        this.element.find('.conversation-time').html( conversation.last_comment_at_str )

        this.showConversationText(
			conversation.text,
			conversation.last_comment_user_id,
			conversation.last_comment_user_name,
			conversation.last_comment_viewed
		);
	},
	showConversationText: function( text, userId, userName, lastCommentViewed ) {
	    var conversationText = text;

		var labelReaded = 'Прочитано';
		var labelYou = 'Вы';
		if (typeof Yii != 'undefined') {
			labelReaded = Yii.t('common', labelReaded);
			labelYou = Yii.t('common', labelYou);
		}

		var prefix = "";
		if ( userId == window.accountUserId ) {
			prefix = "<span>" + labelYou + ": </span> ";
		}
        else {
            var conversationTitle = this.element.find('.conversation-title').html()
            if( userName != conversationTitle ) {
                prefix = "<span>" + userName + ": </span> ";
            }
        }



		this.textEl.html( prefix + $.emoji(conversationText /*+ (lastCommentViewed ? '<br/>Прочитано' : '') */ ) )
	},
	subscribeToConversation: function( conversation_id ) {

		if ( window.conversationSubscribes && window.conversationSubscribes[ conversation_id ] ) {
			return;
		}
		if ( ! window.accountUserWebSocketConnection ) {
			return;
		}

        var self = this;
		const subscribeFunction = (append = '', callbackFn = null, callbackParam = null) => {
			var channel = "conversation_change_" + conversation_id + append;
			window.accountUserWebSocketConnection.subscribeChannel( channel,
				function(message, json){

					var $block = $('.conversation-' + json.conversation_id )
					if ( json.action == "new_comment" ) {
						if ( json.comment.user_id == window.accountUserId ) {
							self.updateFreshCommentCount( $block, 'set', 0 )
						}
						else {
							self.updateFreshCommentCount( $block, 'inc', 1 )
						}

						self.showConversationText( json.comment.text, json.comment.user_id, json.comment.user_name )
						$(self.element).trigger('comment:added', []);
					}
					if ( json.action == "viewed" ) {
						if ( json.user_id == window.accountUserId ) {
							self.updateFreshCommentCount( $block, 'set', 0 )
						}
					}
				}
			);

			if ( ! window.conversationSubscribes ) {
				window.conversationSubscribes = {};
			}
			window.conversationSubscribes[conversation_id] = 1;
			if (callbackFn) {
				callbackFn(callbackParam);
			}
		};

		ajaxCall('/pl/user/user/get-ws-hash', {id: conversation_id}, {}, (wsResponse) => {
			let wsConversationHash = wsResponse.data.result.hash;
			let wsConversationUntil = parseInt(wsResponse.data.result.seconds_left);
			let isConversationDynamicHashEnabled = !!wsResponse.data.isConversationDynamicHashEnabled;
			if (isConversationDynamicHashEnabled) {
				let callbackFn = (secondsLeft) => {
					setTimeout(() => {
						$.toast(
							Yii.t('apps.users', 'Страница устарела, обновите пожалуйста.'),
							{type: 'danger'}
						);
					}, secondsLeft * 1000);
				};
				subscribeFunction(
					'_' + window.accountId + wsConversationHash,
					callbackFn,
					wsConversationUntil
				);
			} else {
				subscribeFunction();
			}
		});
    },

    updateFreshCommentCount: function( $container, mode, value ) {

        var $freshCommentCountBlock = $container.find( '.conversation-fresh-comment-count' )
        var freshCommentCount = $freshCommentCountBlock.data('fresh-comment-count' )
        if ( mode == 'inc' ) {
            freshCommentCount += value;
        }
        else {
            freshCommentCount = value;
        }

        $freshCommentCountBlock.data('fresh-comment-count', freshCommentCount )
        $freshCommentCountBlock.html( freshCommentCount )

        if ( freshCommentCount > 0 ) {
            $freshCommentCountBlock.show();
        }
        else {
            $freshCommentCountBlock.hide();
        }

    }
} );
