$( function() {
	let $itemsListEl = null;
	let $submenuBarEl  = null;
	let $fade = null;
	let counters = null;

	let handleItemClick = function( $itemEl, item ) {
		if (item.id === 'marathon') {
			window.open(item.subitems[0].url);
			return;
		}

		/*
		if ( item.id == "notifications_button_small" ) {
			return;
		}
		*/


		setSelectedItem( item.id );
		if( item.subitems.length == 1 ) {
			location.href = item.subitems[0].url;
		}
		else {
			showSubmenu(item);
		}

	};

	let balances = null;
	let loadBalances = function( $headerEl ) {

		let showBalances = function() {
			let $balanceEl = $('<div class="user-balance"/>');
			for( let balance of balances ) {
				let $balanceStr = $("<p>" + balance.label + ": <b>" + balance.value + "</b></p>");
				$balanceStr.appendTo( $balanceEl );
			}
			$balanceEl.appendTo( $headerEl );
		};

		if ( balances === null ) {
			ajaxCall("/pl/user/user/get-balance?id=" + window.accountUserId, {}, {}, function (data) {
				if ( data.balances && data.balances.length ) {
					balances = data.balances;
					showBalances();
				}
			});
		}
		else {
			showBalances();
		}
	};

	updateNotificationsData = function( data ) {

		let count = data.count;
		let $notificationsContentEl = $submenuBarEl;

		$notificationsContentEl.empty();




		let groups = data.groups;
		if ( groups.length > 0 ) {

			let $headerEl = $('<div class="header"/>').appendTo( $notificationsContentEl );
			let $headerLinkWrapper = $('<div class="all-notifications-header-link-wrapper"/>').appendTo( $headerEl );

			let $groupsEl = $('<div/>').appendTo( $notificationsContentEl );

			var notificationsLabel =  (typeof Yii != 'undefined') ? Yii.t( "common", "Notifications" ) : 'Уведомления';
			let $headerLink = $('<a href="/notifications/notifications/all" class="all-notifications-header-link"/>').html( count.new > 0 ? notificationsLabel + ' (' + count.new + ')' : notificationsLabel);
			$headerLink.appendTo( $headerLinkWrapper );


			let markAsReadLabel = (typeof Yii != 'undefined') ? Yii.t( "common", "Mark as read" ) : 'Отметить прочитанными';
			let $markViewedAllLink = $( '<div class="mark-viewed-all"/>' );
			$markViewedAllLink.html( markAsReadLabel ).appendTo( $headerEl );
			$('<div class="clear"/>').appendTo( $headerEl );

			let markViewedAllInProcess = false;
			$markViewedAllLink.click( function() {
				if ( markViewedAllInProcess ) {
					return;
				}
				$("<img src='/public/img/loading.gif'/>").prependTo( $(this));
				markViewedAllInProcess = true;
				ajaxCall('/notifications/notifications/viewedAll', {}, {suppressErrors: true}, function (response) {
					markViewedAllInProcess = false;
					updateNotificationsData(response.groups);
					updateCounters();
				});

			});

			for (let group of groups) {

				let helper = group.helper ? group.helper : {};

				let $el = $("<a/>");
				$el.addClass('notification-group notification-click-area notification-status-' + group.status);
				$el.attr('href', helper.click_url);

				$('<span class="user-image"/>').html(helper.first_user_thumbnail).appendTo($el);
				$('<div class="content"/>').html(helper.content).appendTo($el);
				$('<div class="date"/>').html(helper.display_date).appendTo($el);
				$('<div class="clear"/>').appendTo($el);

				let $markAsViewedLink = $('<div class="mark-viewed" style="top: 5px">&times;</div>');
				$markAsViewedLink.appendTo($el);
				$markAsViewedLink.data('group-id', group.id);

				$markAsViewedLink.click(function (e) {
					let groupId = $(this).data('group-id');
					if ($(this).data('processing')) {
						return;
					}
					$(this).data('processing', true)
					e.stopPropagation();
					e.preventDefault();
					$markAsViewedLink.html("<img src='/public/img/loading.gif'/>");

					ajaxCall('/notifications/notifications/viewed', {
						id: groupId
					}, {suppressErrors: true}, function (resp) {
						$(this).data('processing', false);
						updateNotificationsData(resp.groups);
						updateCounters();
					});

				});

				$el.appendTo($groupsEl);
			}

			var allNotificationsLabel = (typeof Yii != 'undefined') ? Yii.t("common", "All notifications") : 'Все уведомления';
			if (data.count.all > 10) {
				$('<a class="all-notifications-footer-link" href="/notifications/notifications/all"/>').html(allNotificationsLabel).appendTo($notificationsContentEl);
			}
		}
		else {
			var noNotificationMessagesLabel = (typeof Yii != 'undefined') ? Yii.t( "common", "No notification messages" ) : 'Уведомлений для вас еще нет';

			$("<div class='no-notifications-message'>" + noNotificationMessagesLabel + "</div>").appendTo($notificationsContentEl);
		}

	};


	loadNotifications = function() {
		$submenuBarEl.html("<div class='text-center'><img style='margin-top: 20px;' src='/public/img/loading.gif'/></div>");
		ajaxCall( "/notifications/notifications/get", {}, {method: "GET"}, function(response) {
			updateNotificationsData( response.data );
		});
	};

	let updateCounters = function() {
		$itemsListEl.find('.notify-count').hide();
		for ( let key in counters ) {
			let value = counters[key];
			if (value> 0) {
				if ($itemsListEl.find('.menu-item-' + key)) {
					let $notifyCount = $itemsListEl.find('.menu-item-' + key + ' .notify-count');
					$notifyCount.html( value ).show();

					if (key == 'notifications_button_small') {
						$itemsListEl.find('.menu-item-' + key + ' .menu-item-icon').hide();
					}
				}
			}
		}

	};

	let setSelectedItem = function( itemId ) {
		let $currentSelected = $itemsListEl.find('.menu-item.selected');
		if ( $currentSelected.length > 0 ) {
			if ($currentSelected.hasClass('menu-item-' + itemId)) {
				return;
			}
			let currentSelectedItem = $currentSelected.data('item');
			$currentSelected.find('.menu-item-icon').attr( 'src', currentSelectedItem.iconUrl );
			$currentSelected.removeClass('selected');
		}

		if ( ! itemId ) {
			return;
		}


		let $newSelected = $itemsListEl.find('.menu-item.menu-item-' + itemId );
		if ( $newSelected.hasClass( 'active') ) {
			return;
		}
		let newSelectedItem = $newSelected.data('item');
		$newSelected.find('.menu-item-icon').attr( 'src', newSelectedItem.activeIconUrl );
		$newSelected.addClass('selected');
	};


	let showSubmenu = function( item ) {

		$submenuBarEl.empty();
		$submenuBarEl.attr('class', 'gc-account-user-submenu-bar');
		$submenuBarEl.addClass( 'gc-account-user-submenu-bar-' + item.id );


		if ( item.id == 'notifications_button_small' ) {
			loadNotifications();
		}
		else {
			let $header = $("<div><h3>" + item.label + "</h3></div>");
			$header.appendTo( $submenuBarEl );



			if ( item.id == 'profile' ) {
				loadBalances( $header );
			}



			let $submenuEl = $("<ul class='gc-account-user-submenu'>").appendTo($submenuBarEl);



			for ( let subitem of item.subitems ) {

				var subItemFullId = item.id + '-' + subitem.id;


				var itemClassName = "menu-item-" + subitem.id;
				//var notifyCountClass = 'notify-count ' + (this.props.notifyCount > 0 ? '' : 'hide');
				if (subitem.params.hasDelimiter === true) {
					itemClassName = itemClassName + ' ' + 'menu-item-delimiter';
				}

				let $subitemEl = $("<li class='" + itemClassName + "'/>");
				$subitemEl.appendTo( $submenuEl );

				let target = item.target ? item.target : '_self';

				if (subitem.id.indexOf('gus-') !== -1) {
					target = subitem.target ? subitem.target : target;
				}

				let $subitemLink = $("<a class='subitem-link' target='" + target + "' href='" + subitem.url + "'>" + subitem.label + "</a>");
				$subitemLink.appendTo( $subitemEl );

				if ( subitem.imageUrl ) {
					$('<img src="' + subitem.imageUrl + '"/>').prependTo($subitemLink);
				}



				var notifyCount = counters ? counters[subItemFullId] : 0;
				if ( notifyCount > 0 ) {
					let $notifyEl = $( "<span class='notify-count'>" + notifyCount + "</span>" );
					$notifyEl.appendTo( $subitemLink );
				}

				$subitemEl.appendTo( $submenuEl );
			}
		}


		$submenuBarEl.show();
		$fade.show();
	};



	var initMenu = function() {
		$fade = $('<div class="gc-fade-wrapper"><div class="gc-fade"></div></div>');
		$fade.hide();
		$fade.appendTo($(document.body));
		$fade.click(function () {
			$('.gc-account-leftbar').removeClass("expanded")
			setSelectedItem(null);
			$fade.hide();
			$submenuBarEl.hide();
		});

		$('.gc-main-content').addClass("with-left-menu");
		ajaxCall('/cms/counters/menu', {}, {suppressErrors: true}, function (response) {

			counters = response.counters;
			updateCounters();

			var $elem = $('.talks-widget.activated-talks-widget');
			if ( $elem.length > 0 ) {
				$elem.talksWidget( 'setCounter', response.counters.conversationsData )
			}
		});
	};

	var renderPageMenu = function ( menu ) {
		let $leftbarEl = $('<div class="gc-account-leftbar"/>');
		let $toggleLink = $('<a href="javascript:void(0)" class="toggle-link without-icon"><img src="/public/img/bars.svg" width="35"/></span></a>');
		$toggleLink.appendTo ( $leftbarEl )
		$toggleLink.click( function() {
			$leftbarEl.toggleClass("expanded")
			if ( $leftbarEl.hasClass('expanded')) {
				$leftbarEl.find('.gc-account-user-menu').show();
				$fade.show();
			}
			else {
				$leftbarEl.find('.gc-account-user-menu').hide();
				$leftbarEl.find('.gc-account-user-submenu-bar').hide();
				$fade.hide();
			}
		} );

		let $gcAccountUserMenu = $('#gcAccountUserMenu');

		if (menu.customClass) {
			$gcAccountUserMenu.addClass(menu.customClass);
		}

		if( menu.navMenuItems && menu.navMenuItems.subitems && menu.navMenuItems.subitems.length > 0 ) {
			let $navItemsMenu = $("<div class='gc-page-nav-items-menu lt-page-edit-link'/>");
			$navItemsMenu.appendTo($gcAccountUserMenu);
			//$navItemsMenu.hide();
			for( let item of menu.navMenuItems.subitems ) {
				let $navItem = $('<a class="item ' + item.id + '-link" href="' + item.url + '">' + item.label + '</a>')
				$navItem.appendTo( $navItemsMenu )
			}


			var togglerLabel =  (typeof Yii != 'undefined') ? Yii.t( "common", "Actions" ) : 'Действия';
			let $togglerNavItem = $('<a class="toggler-item" >' + togglerLabel + '</a>');
			$togglerNavItem.appendTo( $navItemsMenu );

			$togglerNavItem.click( function() {
				$navItemsMenu.toggleClass('expanded');
			})
		}

		initMenu();

		$submenuBarEl = $("<div class='gc-account-user-submenu-bar'/>");
		$submenuBarEl.appendTo( $leftbarEl );
		$submenuBarEl.hide();

		$itemsListEl = $('<ul class="gc-account-user-menu">');
		$itemsListEl.appendTo( $leftbarEl );

		$leftbarEl.appendTo($gcAccountUserMenu);
		for( let item of menu.items ) {

			/*
			if ( item.id == "notifications" ) {
				continue;
			}
			*/

			let $itemEl = $('<li/>');
			$itemEl.data('item', item );

			//$itemEl.html( item.label );
			$itemEl.addClass("menu-item" );
			$itemEl.addClass("menu-item-" + item.id);
			if (item.id === 'profile') {
				const worksheetClass = item.params.worksheetClass ?? null;
				if (worksheetClass !== null) {
					$itemEl.addClass(`worksheet__${worksheetClass}`);
				}
			}
			if ( menu.activeItem == item.id ) {
				$itemEl.addClass('active')
			}


			let $linkEl = $("<a href='javascript:void(0)'/>");
			$linkEl.appendTo( $itemEl );
			$linkEl.attr('title', item.label);
			$linkEl.click( function() {
				handleItemClick( $itemEl, item );

			});

			let $img = $("<img class='menu-item-icon' src='" + ( ( item.id == menu.activeItem ) ? item.activeIconUrl : item.iconUrl ) + "'/>");
			$img.appendTo( $linkEl );



			$itemEl.appendTo( $itemsListEl );

			if ( item.subIconHtml ) {
				let $subIcon = $("<span class='sub-icon'>" + item.subIconHtml + "</span>");
				$subIcon.appendTo( $itemEl )
			}

			let $notifyCountEl = $("<span class='notify-count'/>");
			$notifyCountEl.appendTo( $itemEl.find('a') );
			$notifyCountEl.hide();

			if (!item.hideLabel) {
				let $labelEl = $(`<span class='menu-item-label'>${item.label}</span>`);
				if (item.label.length > 9) {
					$labelEl.css('margin', 0);
				}
				$labelEl.appendTo($linkEl);
				$notifyCountEl.addClass('with-label');
				$linkEl.addClass('with-label');
			}
		}

		$gcAccountUserMenu.removeClass('not-inited');

		//$(".menu-item-notifications_button_small a").click();
	};



	if (window.gcAccountUserMenu) {
		renderPageMenu(window.gcAccountUserMenu);
	}
});
