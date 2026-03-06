jQuery.widget( 'gc.missionAddfieldsEditor', {
	options: {
		fields: [],
		types: [],
		isChecklist: false
	},

	needDelete: false,
	modal: null,
	_create: function () {
		var self = this;
		this.element.click( function() {
			self.showModal();
		});

		let title = this.isChecklist()
			? this.t('Чеклист', 'common')
			: this.t('Дополнительные поля', 'common');

		if ( this.options.fields.length > 0 ) {
			title = title + " (" + this.options.fields.length + ")";
		}
		this.element.html( title );


	},
	t: function (string, category) {
		return (typeof Yii != 'undefined') ? Yii.t(category ? category : 'common', string) : string;
	},
	isChecklist: function() {
		for( var field of this.options.fields ) {
			if ( field.type != "checkbox" ) {
				return false;
			}
			if ( ! field.required ) {
				return false;
			}
		}
		return true;
	},
	showModal: function() {
		var self = this;

		if ( ! self.modal ) {
			self.modal = window.gcModalFactory.create({show: false});
			self.modal.getModalEl().find('.modal-dialog').width( '600px' )

			self.itemsEl = this.createList();

			for( var item of this.options.fields ) {
				this.addItemToList(item);
			}


			self.modal.setContent("");
			self.itemsEl.appendTo( self.modal.getContentEl() );

			let $btnApply = $('<button class="btn btn-primary pull-left">'+this.t( 'Сохранить' )+'</button>');
			$btnApply.appendTo ( self.modal.getFooterEl() )
			$btnApply.click( function() {
				if ( self.options.onTrySave ) {
					var newValue = self.getValue();
					self.options.onTrySave( newValue, function() {
						self.modal.hide();
					});
				}
			});

			let $btnAddItem = $('<button class="btn btn-default pull-left"> <span class="fa fa-plus"></span>'+this.t( 'Добавить поле', 'common' )+'</button>').appendTo ( self.modal.getFooterEl() );
			$btnAddItem.click( function() {
				self.addNewItem();
			});

			let $btnSwithType = $('<button class="btn btn-link pull-right">'+this.t( 'Редактор дополнительных полей', 'common' )+'</button>').appendTo ( self.modal.getFooterEl() );
			$btnSwithType.click( function() {
				if (self.options.onRedactorClick) {
					self.options.onRedactorClick();
				}
			});

			if ( self.options.onDelete ) {
				let $btnDelete = $('<button class="btn btn-delete btn-danger pull-right">' + self.t('Delete', 'common') + '</button>');
				$btnDelete.appendTo ( self.modal.getFooterEl() );

				$btnDelete.click( function() {
					if (!confirm(self.t('Are you sure?', 'common'))) {
						return;
					}

					if ( self.options.onDelete ) {
						self.options.onDelete();
					}
				})

			}
		}

		self.modal.show();
	},

	createList: function () {
		//this.element.html("EHL")
		let self = this;

		this.fieldsListTable = $('<table class="table table-fields-list"><tbody></tbody></table>');
		if ( this.isChecklist() ) {
			this.fieldsListTable.addClass('is-checklist')
		}
		$('<thead><tr><th>' + self.t('Дополнительные поля', 'common') + '</th><th colspan="2" class="text-right">' +  self.t('Обязательное', 'common') +  '</th></tr></thead>').appendTo(this.fieldsListTable);
		//this.fieldsListTable.appendTo( $el );
		this.fieldsListTable.find("tbody").sortable();

		return this.fieldsListTable;
	},

	addNewItem: function() {

		var item = {
			id: Math.round( Math.random() * 100000 ),
			type: "checkbox",
			title: this.t( 'Поле', 'common' ) + ' ' + this.fieldsListTable.find('.addfield-row').length,
			required: true
		};
		if (  ! this.isChecklist() ) {
			item.type = "checkbox";
			item.required = false;
		}


		var $itemEl = this.addItemToList( item );
		$itemEl.find('.title-td input').focus();
	},

	createTypesSelect: function() {
		var self = this;
		var $result = $("<select class='type-select form-control'></select>");
		for ( var key in self.options.types ) {
			var $option = $("<option/>");
			$option.val( key );
			$option.html( self.options.types[key] );
			$option.appendTo( $result )
		}
		return $result;
	},
	getValue: function() {
		var value = { fields: [] };
		this.fieldsListTable.find('.addfield-row').each( function( index, el ) {
			var $row = $(el);
			var field = {};
			field.id = $row.data('id');
			field.type = $row.find('.type-select').val();
			field.title = $row.find('.title-input').val();
			field.required = $row.find('.required-checkbox').prop('checked');
			value.fields.push( field )
		});
		return value;
	},

	addItemToList: function( item ) {
		var self = this;
		var $typesSelect = this.createTypesSelect();

		var $itemEl = $('<tr class="addfield-row"/>');
		$itemEl.data('id', item.id);

		var $typeTd = $('<td class="type-td"/>').appendTo( $itemEl );
		var $titleTd = $('<td class="title-td"/>').appendTo( $itemEl );
		var $requiredTd = $('<td  class="required-td"/>').appendTo( $itemEl );
		var $trashTd = $('<td  class="trash-td"/>').appendTo( $itemEl );

		$typesSelect.appendTo( $typeTd );
		$typesSelect.val( item.type )

		var $titleInput = $('<input type="text" class="form-control title-input" placeholder="'+self.t('Название поля', 'common')+'"/>').appendTo( $titleTd );

		var $requiredCheckbox = $('<input type="checkbox" class="required-checkbox" placeholder="'+self.t('Название поля', 'common')+'"/>').appendTo( $requiredTd );
		if ( item.required ) {
			$requiredCheckbox.prop('checked', true);
		}
		$titleInput.val( item.title );

		$('<span class="btn-delete fa fa-trash"/>').appendTo( $trashTd ).click( function() {
			$itemEl.detach();
		});



		$itemEl.appendTo(self.fieldsListTable.find('tbody'));
		return $itemEl;

	}


});
