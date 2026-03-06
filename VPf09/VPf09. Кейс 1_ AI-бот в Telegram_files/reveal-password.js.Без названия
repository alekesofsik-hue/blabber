$(document).ready(function () {
	if (allowRevealPassword) {
		setInterval(initRevealPassword, 500);
	}

	function initRevealPassword() {
		if (!$('input[type="password"]:not(.added-reveal-button)').length) {
			return;
		}

		$('input[type="password"]:not(.added-reveal-button)')
			.each(function (index) {
				var revealPassword = $('<div>')
					.addClass('reveal-password')
					.attr('data-index', index)
					.append(
						$('<i>')
							.addClass('glyphicon')
							.addClass('glyphicon-eye-open')
					);

				$(this).attr('data-index', index);
				$(this).after(revealPassword);
			})
			.addClass('added-reveal-button');

		$('.reveal-password:not(.added-reveal-handler)')
			.on('click', function (event) {
				event.preventDefault();

				var index = $(this).data('index'),
					input = $('input[data-index="' + index + '"]'),
					type = $(input).attr('type');

				$('input[data-index="' + index + '"]').attr('type', type === 'password' ? 'text' : 'password');
				$('.glyphicon', this).toggleClass('glyphicon-eye-open').toggleClass('glyphicon-eye-close');
			})
			.addClass('added-reveal-handler');
	}
});
