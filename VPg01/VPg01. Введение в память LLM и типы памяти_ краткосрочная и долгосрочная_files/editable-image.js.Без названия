jQuery.widget( 'gc.editableImage', {
	options: {},
	_create: function () {
		let self = this;

		let saveUrl = this.element.data('save-url');


		let $buttonsBlock = $('<div class="buttons-block"></div>');
		if ( saveUrl ) {
			$buttonsBlock.appendTo(this.element);
			$buttonsBlock.hide();
		}

		let $btnSave = $('<button type="button" class="btn btn-success">Save</button>');
		$btnSave.appendTo($buttonsBlock);

		let $btnCancel = $('<button type="button" class="btn btn-default btn-cancel">Cancel</button>');
		$btnCancel.appendTo($buttonsBlock);

		let $input = this.element.find('input');

		this.value = $input.val();
		let inputName = $input.attr('name');

		if ( saveUrl ) {
			$input.change(function () {
				$buttonsBlock.show();
			});
		}

		$btnCancel.click( function() {
			$input.gcFileWidget( 'setValue', self.value );
			$buttonsBlock.hide();
		});

		let callback = function() {
			$buttonsBlock.hide();
		};

		$btnSave.click( function() {
			self.value = $input.val();
			if ( saveUrl ) {
				let data = {};
				data[inputName] = self.value;
				ajaxCall(saveUrl, data, {}, function( response ) {
					callback();
				});
			}
			else {
				callback();
			}

		});
	}
});

$( function() {
	$('.editable-image').editableImage();
});