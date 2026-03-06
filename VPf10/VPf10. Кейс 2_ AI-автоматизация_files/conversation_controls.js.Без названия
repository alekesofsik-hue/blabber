jQuery.widget( 'gc.conversationControls', {
	activeTab: "templates",
	noAnimate: true,
	tabsContents: {},
	_create: function () {
		if ( ! window.userInfo.isTeacher ) {
			return;
		}


		this.commentsContainer = this.options.commentsContainer;

		let $el = this.element;
		let self = this;
		setTimeout( function() {
			self.noAnimate = false;
		}, 500 );

		//let $collapsedContent = $('<div class="expand-link"><div class="expand-link-border"></div> <div class="expand-link-title"></div> </div>').appendTo( $el );

		let $tabs = this.tabs = $('<div class="conversation-controls-tabs"/>');
		$tabs.appendTo( $el );

		//$('<div data-tab="templates" class="tab">Шаблоны</div>').appendTo( $tabs );
		$('<div data-tab="notes" class="tab">' + Yii.t('common', 'Добавить заметку') + '</div>').appendTo( $tabs );

		this.element.parents('.conversation-widget').addClass('with-controls')

		$tabs.find('.tab').click( function() {
			if ( $(this).hasClass('active')) {
				self.selectTab(null)
			}
			else {
				self.selectTab($(this).data('tab'))
			}
		});

		this.tabContentBlock = $('<div class="tab-content conversation-control-tab text-right">');
		this.tabContentBlock.hide();
		this.parentBlock = $el.parents('.gc-comment-form');
		this.tabContentBlock.prependTo( this.parentBlock );


		this.setHistory( this.options.history );

		//$collapsedContent.show();
		//this.collapsedContent = $collapsedContent;

		/*(
		$collapsedContent.find('.expand-link-title').click( function() {
			gcSetCookie('conversationControlsExpanded', 1);

			$collapsedContent.hide();
			self.showContent();
		});


		if ( gcGetCookie('conversationControlsExpanded') == "1" ) {
			this.showContent();
		}
		 */


	},
	selectTab: function( tab ) {
		this.tabContentBlock.show();
		this.activeTab = tab;


		this.tabs.find('.tab').removeClass('active');
		this.tabs.find('.tab[data-tab="' + tab + '"]').addClass('active');
		let content = null;
		if ( this.activeTab == "templates" ) {
			 content = this.createTemplatesContent();
		}
		else if ( this.activeTab == "notes" ) {
			content = this.createNotesContent();
		}


		this.tabContentBlock.hide();
		this.tabContentBlock.empty();
		if ( this.activeTab ) {
			content.appendTo(this.tabContentBlock);
			this.tabContentBlock.show('fade');
		}
		if ( this.activeTab == "notes") {
			this.parentBlock.find('.new-comment').hide();
		}
		else {
			this.parentBlock.find('.new-comment').show();
		}
		if ( content ) {
			content.find('.main-input').focus();
		}




		let self = this;
		self.doScroll();

	},
	doScroll: function() {
		let $div = $('.conversation-widget .comments-container');
		if ( this.noAnimate ) {
			$div.prop({scrollTop: $div.prop("scrollHeight")});
		}
		else {
			$div.animate({scrollTop: $div.prop("scrollHeight")}, 300);
		}
	},
	createContentBlock: function() {
		let self = this;

		let $expandedContent = $('<div class="expanded-content"></div>').appendTo( this.element );

		return $expandedContent;
	},
	setHistory: function(history) {
		let $comments = this.commentsContainer.find('.gc-comment');
		let somethingChanged = false;
		for ( let row of history ) {
			let itemId = 'actionHistory' + row.id;
			if( $('#' + itemId ).length > 0 ) {
				continue;
			}
			let $historyHtml = $('<div class="history-action ' + row.history_class + '"><div class="line"></div><div class="inner-html">' + row.by_user + " &bullet; " + row.created_at + " &bullet;  " + row.title + '</div> </div> </div>');
			$historyHtml.data('id', row.id)
			let needClick = false;
			$('<div id="actionHistory' + row.id + '" class="date-info">' +  + '</div>').appendTo( $historyHtml );
			if ( row.html && row.html.length > 0  ) {
				$historyHtml.data('text', row.text );
				let $item = $('<div class="inner-html-data"><div class="inner-html-content">' + row.html + '</div></div>');
				$item.appendTo( $historyHtml );
				needClick = true;
			}
			let doBreak = false;
			let $lastComment = null;
			$comments.each(function (index, commentEl) {
				if ( doBreak ) {
					return;
				}
				let $commentEl = $(commentEl);
				let commentTimestamp = $commentEl.data('timestamp');
				if ( commentTimestamp > row.timestamp ) {
					$historyHtml.insertBefore( $commentEl );
					somethingChanged = true;
					doBreak = true;
				}
				$lastComment = $commentEl;
			});
			if ( ! doBreak ) {
				$historyHtml.appendTo(this.commentsContainer.find('> .comments'));
				somethingChanged = true;
			}
			if ( needClick ) {
				$historyHtml.find('.inner-html-content').dblclick( function() {
					let $viewContent = $(this);
					let $parentContainer = $(this).parents('.inner-html-data');

					$viewContent.hide();

					let $editCont = $("<div/>")
					$editCont.appendTo( $parentContainer );
					let $historyActionCont = $editCont.parents('.history-action');

					let $textarea = $('<textarea style="min-height: 40px; margin-bottom: 10px;" class="form-control"/>');
					$textarea.val( $historyActionCont.data('text') );
					$textarea.height( 100 );
					//$textarea.autosize();

					$textarea.appendTo( $editCont );


					$('<button class="btn btn-success">Save</button>').click( function() {
						let text = $textarea.val();
						let id = $historyActionCont.data('id');
						ajaxCall("/pl/tasks/resp/edit-note?actionHistoryId=" + id, { text: text }, {}, function( response ) {
							if ( response.data.deleted ) {
								$editCont.parents('.history-action').detach();
							}
							else {
								$editCont.detach();
								$viewContent.html(response.data.html).show();
								$historyActionCont.data('text', response.data.text);
							}
						} );

					}).appendTo( $editCont );
					$('<button class="btn btn-link">Cancel</button>').click( function() {
						$editCont.detach();
						$viewContent.show();
					}).appendTo( $editCont );


				})
			}
		}
		if ( somethingChanged ) {
			//this.doScroll();
		}
	},
	doSearchTemplates: function( string, $searchList ) {
		//$searchList.html('<span class="/public/img/loading.gif"/> Поиск');
		let searchResults = this.searchResults = {};

		let showItems = function(items) {
			$searchList.empty();
			$searchList.hide();
			if ( items.length == 0 ) {
				$searchList.html( '<div class="info">Поиск ничего не дал</div>').show('fade')
			}
			for (let item of items) {
				let $itemEl = $("<li> <span class='fa fa-list'></span> " + item.title + "</li>").appendTo($searchList);

				$itemEl.click(function () {
					let questionDialog = new SkillQuestionDialog();
					questionDialog.open(item.id, window.accountUserId, function (text) {
						$('.gc-comment-form .new-comment-textarea').val(text);
						$('.gc-comment-form .new-comment-textarea').css('min-height', 100).focus();
					});
				});
				$searchList.show('fade');

			}
		};
		if ( searchResults[string]) {
			showItems(searchResults[string]);
		}
		else {
			ajaxCall("/pl/notifications/skill-question/search-templates", {string: string}, {method: "get"}, function( response ) {
				searchResults[string] = response.data.items;
				showItems( searchResults[string] );
			});
		}

	},
	createTemplatesContent: function() {
		let self = this;

		let $result = $("<div class='content-block'>");

		let $searchInput = $('<input class="main-input form-control" size="40" placeholder="Поиск по шаблонам ответов">');
		$searchInput.appendTo($result);
		let $searchList = $("<ul class='search-list'>").appendTo($result);

		let currentTimeout = null;

		$searchInput.keyup(function () {
			clearTimeout(currentTimeout);
			let string = $(this).val();
			if ( ! string ) string = "";
			string = string.trim();
			if (string.length > 2 ) {
				$searchList.html('<div class="info"><img src="/public/img/loading.gif"/> Поиск</div>');
				if ( !self.searchResults[string] ) {
					currentTimeout = setTimeout(function () {
						self.doSearchTemplates(string, $searchList);
					}, 200);
				}
				else {
					self.doSearchTemplates(string, $searchList);
				}
			}
			else if (string && string.length > 0) {
				$searchList.html('<div class="info">Введите как минимум 3 символа</div>');
			}
			else {
				self.doSearchTemplates( "", $searchList );
			}
		});

		self.doSearchTemplates( "", $searchList );

		return $result;
	},
	createNotesContent: function() {
		let self = this;
		let $result = $("<div class='content-block'><textarea rows=2 class='form-control main-input' style='margin-bottom: 5px; background: lightyellow' placeholder='" +
			Yii.t('common', 'Оставить пометку, которая видна только сотрудникам') +
			"'></textarea></div>");
		$result.find('textarea').autosize();
		$result.find('textarea').css('minHeight', 40);
		$result.find('textarea').keyup(function(event) {
			if( event.keyCode == 13 && ( event.ctrlKey )  ) {
				$button.click();
			}
		});

		let $button = $('<button class="btn btn-success">' + Yii.t('common', 'Добавить') + '</button>').appendTo( $result );
		$button.click( function() {
			let text = $result.find('textarea').val();
			ajaxCall("/pl/tasks/resp/note?id=" + self.options.responsibilityId, { text: text }, {}, function( response ) {
				self.setHistory( response.data.history );
				$result.find('textarea').val("");
				self.selectTab(null)
			} );
		});

		let $buttonCancel = $('<button class="btn btn-link">' + Yii.t('common', 'Отмена') + '</button>').appendTo( $result );
		$buttonCancel.click( function() {
			self.selectTab(null)
		});

		return $result;
	}
});
