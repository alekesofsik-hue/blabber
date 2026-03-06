function CommentTemplateDialog() {
	var modal = this.modal = window.gcModalFactory.create({show: false, width: 900 });
	var self = this;

	var saveTemplate = 'Сохранить шаблон';
	if (typeof Yii != 'undefined') {
		saveTemplate = Yii.t('common', saveTemplate);
	}
	var $saveBtn = $('<button class="pull-left btn btn-use btn-success">' + saveTemplate + '</button>')
	$saveBtn.appendTo( modal.getFooterEl() );

	/*
	var $editBtn = $('<button class="pull-right btn btn-use btn-link">Редактировать</button>')
	$editBtn.appendTo( modal.getFooterEl() );
	*/

	$saveBtn.click( function() {

		$('.owner-type-id-value').val( $('.owner-type-selector:checked').data('owner-type-id'));
		$('.owner-id-value').val( $('.owner-type-selector:checked').data('owner-id'));

		ajaxCall( '/pl/notifications/skill-question/save-ajax', $('.skill-question-form').serialize(), { btn: $saveBtn }, function( response ) {

			/*
			self.modal.setContent( response.data.html );
			self.data = response.data;
			self.id = id;
			*/
			self.modal.hide();
			location.href = location.href;
		} );


	} );

	/*
	$editBtn.click( function() {
		window.open( "/pl/notifications/skill-question/update?id=" + self.id)
	});
	*/

	/*$deleteBtn = $('<button class="pull-right btn btn-danger">Удалить</button>')
	 $deleteBtn.appendTo( modal.getFooterEl() );
	 $deleteBtn.click( function() {
	 self.setValue({selected_id: null})
	 self.doSelect()
	 })*/

	this.open = function( id, userId ) {
		this.modal.reset();
		$('.skill-question-form').detach();


		ajaxCall( '/pl/notifications/skill-question/create-from-comment?id=' + id, { }, {}, function( response ) {
			self.modal.setContent( response.data.html );
			self.data = response.data;
			self.id = id;
		} );

		this.modal.show();
		setTimeout( function() {
			$('.owner-type-selector').eq(0).click();
		}, 100 )

	}
}
