jQuery.widget( 'gc.noticeWidget', {
	containerElemDOMSelector: '.gc-both-main-content',

	isRedesign: false,
	options: {
		needLoad: false,
	},

	_create: function() {
		var self = this;
		this.load();
	},
	load: function() {
		//alert("E")
	},

	setContainer: function(selector) {
		this.containerElemDOMSelector = selector;
	},
	setIsRedesign: function (isRedesign) {
		this.isRedesign = isRedesign;
	},

	getContainer: function() {
		return this.containerElemDOMSelector;
	},

	addNotice: function( noticeData ) {
		this.showNotice( noticeData );
	},

	showNotice: function( noticeData ) {

		switch( noticeData.type ) {
			case "modal":
				this.showModal( noticeData );
            	break;
			default:
				this.showTopPanel( noticeData );
				break;
		}
	},

	showTopPanel: function( noticeData ) {
		var self = this;

		var $el = $('<div class="notice-top-panel"></div>')
		$el.addClass( 'gc-into-main-content' );
		if (this.isRedesign) {
			$el.addClass('redesigned-notice-top-panel');
			$el.addClass('redesigned-notice-' + noticeData.messageType);
		}
		//$el.addClass('alert alert-' + noticeData.messageType )

		$el.html( noticeData.text );
		if (this.isRedesign) {
			$el.html('<div class="redesigned-notice-content"><span class="redesigned-notice-text">' + noticeData.text + '</span></div>');
		}

		if ( noticeData.button ) {
			$buttonEl = $('<button class="btn btn-default">' +  noticeData.button + '</button>')
			if (this.isRedesign) {
				$buttonEl.addClass('rd-btn rd-btn-notice');
				$buttonEl.appendTo($el.find('.redesigned-notice-content'));
			} else {
				$buttonEl.appendTo( $el )
			}
		}

        if (this.isRedesign) {
            window.recountInformers = function () {
                const container = $('#redesignedNoticeTopPanel');
                const currentInformers = container.children('.notice-top-panel:visible');
                const counterNode = $('#redesignedNoticeTopPanel .notice-top-panel .notice-count');
                if (!counterNode) return;
                if (currentInformers.length > 1) {
                    counterNode.text(
                        '+' + window.tt('apps.teach', '{n} уведомление|{n} уведомления', (currentInformers.length - 1))
                    );
                } else {
                    counterNode.remove();
                }
            }
        }

		if (noticeData.showCloseControl) {
			$closeEl = $('<span class="close-link">&times;</span>');
            const isRedesign = this.isRedesign;
			if (isRedesign) {
				let fillColor = noticeData.messageType === 'important' ? 'white' : 'black';
				const svgClose = `<svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
				<path fill-rule="evenodd" clip-rule="evenodd" d="M11.4237 10.0005L15.9137 5.51039L14.9945 4.59116L10.5044 9.08124L6.01433
				 4.59116L5.09509 5.51039L9.58517 10.0005L5.09509 14.4906L6.01433 15.4098L10.5044 10.9197L14.9945 15.4098L15.9137 14.4906L11.4237 10.0005Z" fill="${fillColor}"/></svg>`;
				$closeEl = $(`<span class="close-link">${svgClose}</span>`);
			}
			$closeEl.prependTo($el);

			$closeEl.click( function(e) {
				$el.hide();
				e.preventDefault();
				e.stopPropagation();

                if (isRedesign) {
                    window.recountInformers();
                }
			});
		}

		if (self.isRedesign) {
            $el.appendTo($('#redesignedNoticeTopPanel'));

        } else {
			$el.appendTo($(self.getContainer()));
			$(self.getContainer()).prepend($('<div class="margin-top-notice"></div>').css({"margin-top": (Math.floor($el.height() * 2)) + "px"}));
		}

		var isOpen = $('#' + noticeData.popupType).is(':visible');

		if ( noticeData.popupType && noticeData.showPopupByTimeout && !isOpen) {
			if (document.cookie.indexOf(noticeData.popupType) == -1) {
				window.setTimeout(function() {
					document.cookie = noticeData.popupType + "=true";

					if (!isOpen) {
						gcFixIncident('show-modal-by-time', noticeData.showPopupByTimeout + '');
						self.openPopup(noticeData);
					}
				}, noticeData.showPopupByTimeout * 1000);
			}
		}

		if (noticeData.noticeActionJs) {
			eval(noticeData.noticeActionJs);
		}

		$el.click( function() {
			if ( noticeData.popupType ) {
				self.openPopup( noticeData );
			}
			if ( noticeData.callback ) {
				noticeData.callback();
			}
			else {
				eval( noticeData.actionJs );
			}
		} );
	},

	showModal: function( noticeData ) {
	},

	openPopup: function( noticeData ) {
		var self = this;
        var isPageRedesigned = window.isPageRedesigned ?? false;
        if (isPageRedesigned) {
            var url = "/pl/cms/popup/get?isRedesign=1&type=" + noticeData.popupType +
                '&parentUrl=' + window.encodeURIComponent(noticeData.parentUrl);
        } else {
            var url = "/pl/cms/popup/get?type=" + noticeData.popupType +
                '&parentUrl=' + window.encodeURIComponent(noticeData.parentUrl)
        }
		ajaxCall( url, {}, {}, function( response ) {
			if ( ! self.modal ) {
				self.modal = window.gcModalFactory.create({show: false, width: response.data.width });
				self.modal.getModalEl().addClass( 'gc-notice-modal' )
			}
            if ( response.data.title ) {
                self.modal.getHeaderEl().html( response.data.title );
            }
            self.modal.setContent( response.data.html );
            self.modal.getModalEl().find('.modal-dialog').css('top', response.data.topMargin);
            self.modal.show();
            //self.modal.alignVertical();

            self.initModal( noticeData.popupType, self.modal.getContentEl() );

            if (self.isRedesign) {
                $('br').remove();
            }
        });

		//alert( noticeData.popupType )
	},

	initModal: function( type, $contentEl ) {
		var self = this;

		$contentEl.find('.btn-cancel-modal').click( function() {
            self.modal.hide();
        })



		$contentEl.find( 'form' ).submit( function() {

			var data = $(this).serialize();
			var $form = $(this);

			$form.addClass('loading')
			$contentEl.find('.error-block').hide();

			ajaxCall( "/pl/cms/popup/process?type=" + type, data, {}, function( response ) {
				if ( response.data.htmlErrorMessage ) {
                    $contentEl.find('.error-block').html( response.data.htmlErrorMessage );
                    $contentEl.find('.error-block').show();
                }
				if ( response.data.htmlAfterProcess ) {
					var $addEl = $(response.data.htmlAfterProcess);
					$addEl.appendTo( $contentEl );
				}
			}, function() {
				$form.removeClass('loading')
			} );

			return false;
		})
	}
} );

