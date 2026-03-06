jQuery.widget('gc.commentRatingWidget', {
	options: {
		max: 5
	},
	_create: function () {
		this._generateRatingBlock();

		if (!this.element.hasClass('readonly')) {
			this._initializeEvents();
		}
	},
	_generateRatingBlock: function () {
		let html = '';
		html += '<ul>';

		let currentRating = this.element.data('rating');
		for (let i = 1; i <= this.options.max; i++) {
			html += '<li class="' + (i <= currentRating ? 'selected' : '') + '" data-rating="' + i + '"><i class="fa fa-star-o"></i><i class="fa fa-star"></i></li>';
		}
		html += '</ul>';
		if (this.element.data('rating-time')) {
			html += '<span class="time">' + this.element.data('rating-time') + '</span>';
		}
		html += '<span class="message"></span>';
		this.element.html(html);
	},
	_initializeEvents: function() {
		let _widget = this;
		let $element = _widget.element;
		let $ratingBlock = $element.find('ul');
		let timerId;
		let isCursorHover = false;

		$element
			.on('gc:comment:rating:rate', function (event, rating) {
				if (rating != $element.data('rating')) {
					ajaxCall('/pl/cms/comment/rate', {commentId: $element.data('comment-id'), rating: rating}, {}, function (response) {
						if (response.data.message) {
							$element.find('.message').text(response.data.message).css('display', 'inline');
							clearTimeout(timerId);
							timerId = setTimeout(function () { $element.find('.message').fadeOut(); }, 3000);
						}

						$element.data('rating', response.data.rating);
						$element.trigger('gc:comment:rating:reset');
					});
				}
			})
			.on('gc:comment:rating:preview', function (event, rating) {
				$.each($(this).find('ul > li'), function (index, item) {
					let $item = $(item);
					if ($item.data('rating') <= rating) {
						$item.addClass('selected');
					} else {
						$item.removeClass('selected');
					}
				});
			})
			.on('gc:comment:rating:reset', function (event) {
				$element.trigger('gc:comment:rating:preview', [$element.data('rating')]);
			})
			.on('gc:comment:rating:hover', function (event, value) {
				isCursorHover = value;
				if (!isCursorHover) {
					$element.trigger('gc:comment:rating:reset');
				}
			})
		;

		$ratingBlock
			.on('touchstart touchmove touchend', function (event) {
				let touches = event.originalEvent.changedTouches,
					first = touches[0],
					type = '';
				switch (event.type) {
					case 'touchstart': // init move on touch
					case 'touchmove':
						type = 'mousemove';
						break;
					case 'touchend':
						type = 'mouseup';
						break;
					default:
						return;
				}

				let simulatedEvent = document.createEvent('MouseEvent');
				simulatedEvent.initMouseEvent(
					type,
					true,
					true,
					window,
					1,
					first.screenX,
					first.screenY,
					first.clientX,
					first.clientY,
					false,
					false,
					false,
					false,
					0,
					null
				);

				first.target.dispatchEvent(simulatedEvent);
				event.preventDefault();
			})
			.on('mouseup', function (event) {
				if (isCursorHover) {
					$element.trigger('gc:comment:rating:rate', [$(this).find('li.selected').last().data('rating')]);
				}
			})
			.on('mousemove', function (event) {
				let pageX = (event.changedTouches) ? event.changedTouches[0].pageX : event.pageX;
				let offsetx = pageX - $(this).offset().left;

				if (isCursorHover) {
					if (offsetx < 0 || offsetx > $ratingBlock.width()) {
						$element.trigger('gc:comment:rating:hover', [false]);
					}
				} else {
					if (offsetx >= 0 && offsetx <= $ratingBlock.width()) {
						$element.trigger('gc:comment:rating:hover', [true]);
					}
				}

				if (isCursorHover) {
					let rating = Math.ceil((offsetx / $ratingBlock.width()) * _widget.options.max);
					rating = rating < 1 ? 1 : rating;
					$element.trigger('gc:comment:rating:preview', [rating]);
				}
			})
			.on('mouseover', function (e) {
				$element.trigger('gc:comment:rating:hover', [true]);
			})
			.on('mouseleave', function (e) {
				$element.trigger('gc:comment:rating:hover', [false]);
			})
		;
	}
});