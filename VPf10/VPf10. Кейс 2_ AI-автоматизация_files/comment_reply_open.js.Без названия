function commentReplyOpen(idCommentReplyFormBox)
{
	var _static = commentReplyOpen;
	
	var elFormBox = $("#" + idCommentReplyFormBox);
	if (! elFormBox)
	{
		alert('div[' + idCommentReplyFormBox + '] not found');
		return;
	}
	if (! $(elFormBox).is(":visible")) {
		if (_static.commentReplyOpened) {
			_static.commentReplyOpened.hide();
		}
		_static.commentReplyOpened = elFormBox;
		elFormBox.show();
	}
	// scroll down to formBox
	var win = $(window);
	var winBottom = win.scrollTop() + win.height();
	var elBottom = elFormBox.offset().top + elFormBox.height() + 10;
	if (elBottom > winBottom)
	{
		$('html, body').animate({ scrollTop: win.scrollTop() + (elBottom - winBottom) }, 500);
	}
	var form = elFormBox.find('form')[0];
	var input = form.elements['GetCourseComment[comment_text]'];
	input.focus();
}
