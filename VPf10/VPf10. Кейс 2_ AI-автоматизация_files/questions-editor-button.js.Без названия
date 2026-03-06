/* jshint esversion: 11 */

jQuery.widget( 'gc.questionsEditorButton', {
	options: {
		questionaryId: null,
		newQuestionaryId: null,
		editorOptions: null,
		canDelete: false,
		light: false,
		questionaries: []
	},
	needDelete: false,
	modal: null,
    objectTypeId: null,
	_create: function () {
		//this.element.html("Тестирование")
		var self = this;

		let noTestingStr = 'Create testing';
		let testingStr = 'Testing. Questions';
		let deleteTestStr = 'Удалить тест из урока';
        const tagsPanelId = 'tags-question-select';

		if (typeof Yii != 'undefined') {
			noTestingStr = Yii.t('common', noTestingStr);
			testingStr = Yii.t('common', testingStr);
			deleteTestStr = Yii.t('common', deleteTestStr);
		}

        $('#' + tagsPanelId).remove();

		self.questionsEl = $('<div/>');

		if ( self.options.questionaryId ) {
            ajaxCall("/pl/teach/questionary/get?id=" + self.options.questionaryId, {}, {async: false}, function (response) {
                self.objectTypeId = response.data.objectTypeId;

                var options = self.options.editorOptions;
                options.questionary = response.data.model;
                self.questionsEl.questionsEditor(options);

                if (self.objectTypeId) {
                    self.modal?.getModalEl()
                        .find('.questionnaire_modal_buttons')
                        .append(
                            $(`<span class="gc-tags" id="${tagsPanelId}"
                            data-object-type-id="${self.objectTypeId}"
                            data-object-id="${self.options.questionaryId}"
                            data-tags="${options.questionary.tags.join(',')}"
                            data-show-archived-selector="false"></span>`)
                        );
                    $('#' + tagsPanelId).objectTagsLink({'editable': true});
                }
            });

			ajaxCall("/pl/teach/questionary/get-list", {}, {}, function(response) {
				self.options.questionaries = response.data.models;
				self._initUseExist($('.js__questionary__use_exists'), false);
			});
		}
		else {
			self.questionsEl.questionsEditor(self.options.editorOptions);

			ajaxCall("/pl/teach/questionary/get-list", {}, {}, function(response) {
                self.options.questionaries = response.data.models;
                self.objectTypeId = response.data.objectTypeId;
            });
		}

		var setButtonTitle = function ( onStart ) {
			var value = self.questionsEl.questionsEditor('getValue');

			if ( ( value.questions.length > 0 || value.id > 0 ) && ! value.deleted )  {
				self.element.html(testingStr + ': ' + value.questions.length);
			}
			else {
				self.element.html(noTestingStr);
			}

			if ( ! onStart && self.options.onChange ) {
				self.options.onChange(value);
			}
		};

		self.questionsEl.on('changed', function(e,onStart) {
			//console.log( self.questionsEl.questionsEditor('getValue') );
			setButtonTitle(onStart);
		});
		setTimeout( function() {
			setButtonTitle();
		}, 300 )


		this.element.off('click').on('click', function() {
			if(self.options.questionaryId){
				window.open('/pl/teach/questionary/update-testing?id=' + self.options.questionaryId+ '&part=main');
			} else {
				let $formSelect = $('.js__questionary__use_exists select.js__questionnaire-select');
				let $modalSelect = $('.js__questionnaire_modal_buttons select.js__questionnaire-select');

				if($formSelect.length > 0 && $modalSelect.length > 0) {
					$modalSelect.val($formSelect.val());
					$modalSelect.select2('destroy');
					$modalSelect.select2({
						allowClear: true,
					});
				}
				self.showModal();
			}
		});
	},
	showModal: function() {
		var self = this;

		if ( ! self.modal ) {
			self.modal = window.gcModalFactory.create({show: false});
			self.modal.getModalEl().find('.modal-dialog').width( '600px' )
			if ( this.options.light ) {
				self.modal.getModalEl().find('.modal-dialog').addClass('questionary-light-dialog')
			}

			self.modal.setContent("")
			self.questionsEl.appendTo( self.modal.getContentEl() );

			let acceptStr = 'Accept';
			let addQuestionStr = 'Add question';
			let deleteStr = 'Delete';
			let testSettings ='Настройки тестирования';

			if ( this.options.light ) {
				acceptStr = "Save";
			}
			if (typeof Yii != 'undefined') {
				acceptStr = Yii.t('common', acceptStr);
				deleteStr = Yii.t('common', deleteStr);
				addQuestionStr = Yii.t('common', addQuestionStr);
				testSettings = Yii.t('common', testSettings);
			}

			let $buttonsDiv = $('<div class=""></div>');
			$buttonsDiv.appendTo(self.modal.getFooterEl());
            let $buttonsRow = $('<p></p>');
            if (window.newTestsFeature) {
                $buttonsRow = $('<div style="display: flex; gap: 5px; flex-wrap: wrap;"></div>');
            }

			$buttonsRow.appendTo($buttonsDiv);

			let $btnApply = $('<button class="btn btn-primary pull-left">'+acceptStr+'</button>');
			$btnApply.appendTo($buttonsRow);
			$btnApply.click( function() {
				if($('.js__questionnaire_modal_buttons select.js__questionnaire-select').find('option:selected').val()){
					let newValue = self.options.newQuestionaryId || $('.js__questionnaire_modal_buttons select.js__questionnaire-select').find('option:selected').val();

					if ( self.options.saveExistQuestionary ) {
						self.options.saveExistQuestionary(newValue);
					} else {
						self.options.questionaryId = newValue;

						self._create();
						self.modal.hide();
						if($('.js__update_testing').length >0) {
							let $updateButton = $('<button ' +
								'onclick="window.open(\'/pl/teach/questionary/update-testing?id=' + newValue + '&part=settings\')"' +
								'class="btn" type="button">' +
								'</button>');
							$updateButton.html('<span class="fa fa-cog"></span> ' + testSettings);
							$('.js__update_testing').html($updateButton);
						}

						if($('.js__questionary__use_exists').length >0) {
							self._initUseExist($('.js__questionary__use_exists'), false);
						}
					}
				} else if (self.questionsEl.questionsEditor('validate')) {
					self.questionsEl.questionsEditor('apply');

					if ( self.options.onTrySave ) {
						let newValue = self.questionsEl.questionsEditor('getValue');
						self.options.onTrySave( newValue, function() {
							self.modal.hide();
						});
					}
					else {

						self.modal.hide();
					}
				}
			});

            let $btnAddQuestion;
            let $btnAddQuestionMultipleChoice;
            let $btnAddQuestionTrueFalse;
            let $btnAddQuestionSelectOne;
            let $btnAddQuestionGap;
            let $btnAddQuestionCombination;

            if (window.newTestsFeature) {
                $btnAddQuestionMultipleChoice = $(
                    '<button type="button" class="btn btn-primary pull-left" style="display: flex; height: 34px; margin: 0;">' +
                    '<div style="margin: auto 5px auto auto;">' +
                        '<svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">' +
                            '<path d="M9.34888 8C8.96349 8 8.64233 7.84736 8.3854 7.54207C8.12847 7.23679 8 6.7593 8 6.10959C8 5.53033 8.09804 4.92368 8.29412 4.28963C8.49696 3.64775 8.79446 3.10763 9.18661 2.66928C9.58553 2.22309 10.0588 2 10.6065 2C10.8837 2 11.0899 2.05479 11.2252 2.16438C11.3604 2.27397 11.428 2.41879 11.428 2.59883V2.68102L11.5396 2.05871H13L12.2698 6.05088C12.2427 6.1683 12.2292 6.29354 12.2292 6.42661C12.2292 6.58317 12.2596 6.69667 12.3205 6.76712C12.3881 6.82975 12.4963 6.86106 12.645 6.86106C12.7397 6.86106 12.8141 6.8454 12.8682 6.81409C12.7194 7.25245 12.5774 7.56164 12.4422 7.74168C12.307 7.91389 12.1109 8 11.854 8C11.5767 8 11.3502 7.90607 11.1744 7.7182C11.0054 7.5225 10.9006 7.25245 10.86 6.90802C10.4476 7.63601 9.94388 8 9.34888 8ZM10.0081 6.86106C10.1771 6.86106 10.3428 6.77104 10.5051 6.591C10.6741 6.40313 10.789 6.14873 10.8499 5.82779L11.3367 3.17417C11.3367 3.07241 11.3029 2.97456 11.2353 2.88063C11.1677 2.77886 11.0629 2.72798 10.9209 2.72798C10.6504 2.72798 10.407 2.91194 10.1907 3.27984C9.97431 3.63992 9.80527 4.07828 9.68357 4.59491C9.56187 5.10372 9.50101 5.55382 9.50101 5.94521C9.50101 6.3366 9.54834 6.58708 9.643 6.69667C9.74442 6.80626 9.86613 6.86106 10.0081 6.86106Z" fill="white"/>' +
                            '<path d="M9.69082 19C9.14332 19 8.72464 18.8754 8.43478 18.6261C8.14493 18.3692 8 18.0104 8 17.5496C8 17.3229 8.02818 17.1076 8.08454 16.9037L9.37681 11.2266L11.1643 11L10.5845 13.5496C10.81 13.4212 10.9952 13.3381 11.1401 13.3003C11.285 13.255 11.43 13.2323 11.5749 13.2323C12.525 13.2323 13 13.8782 13 15.17C13 15.6912 12.8913 16.2502 12.6739 16.847C12.4646 17.4363 12.1103 17.9424 11.6111 18.3654C11.12 18.7885 10.4799 19 9.69082 19ZM10.3672 17.9009C10.6167 17.9009 10.8502 17.7573 11.0676 17.4703C11.285 17.1756 11.4581 16.813 11.587 16.3824C11.7158 15.9443 11.7802 15.525 11.7802 15.1246C11.7802 14.8225 11.7238 14.5656 11.6111 14.3541C11.4984 14.1426 11.3414 14.0368 11.1401 14.0368C11.0193 14.0368 10.8824 14.0557 10.7295 14.0935C10.5845 14.1237 10.4839 14.1728 10.4275 14.2408L9.76329 17.119C9.73913 17.2096 9.72705 17.2965 9.72705 17.3796C9.72705 17.7271 9.94042 17.9009 10.3672 17.9009Z" fill="white"/>' +
                            '<path d="M4.5 3L2.5 6L1 5" stroke="white" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>' +
                            '<path d="M4.5 14L2.5 17L1 16" stroke="white" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>' +
                        '</svg>' +
                     '</div>' +
                    '<div style="margin: auto auto auto 0;">' +
                    window.tt('common', 'Множественный выбор') +
                    '</div>' +
                    '</button>'
                );

                $btnAddQuestionMultipleChoice.appendTo($buttonsRow);
                $btnAddQuestionMultipleChoice.click( function() {
                    self.questionsEl.questionsEditor('addQuestion', 'multiple_choice');
                });

                $btnAddQuestionTrueFalse = $(`
<button type="button" class="btn btn-primary pull-left" style="display: flex; height: 34px; margin: 0;">
    <div style="margin: 1px 5px auto auto;">
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M3.34888 13C2.96349 13 2.64233 12.8474 2.3854 12.5421C2.12847 12.2368 2 11.7593 2 11.1096C2 10.5303 2.09804 9.92368 2.29412 9.28963C2.49696 8.64775 2.79446 8.10763 3.18661 7.66928C3.58553 7.22309 4.05882 7 4.60649 7C4.88371 7 5.08993 7.05479 5.22515 7.16438C5.36038 7.27397 5.42799 7.41879 5.42799 7.59883V7.68102L5.53955 7.05871H7L6.26978 11.0509C6.24273 11.1683 6.22921 11.2935 6.22921 11.4266C6.22921 11.5832 6.25963 11.6967 6.32049 11.7671C6.3881 11.8297 6.49628 11.8611 6.64503 11.8611C6.73969 11.8611 6.81406 11.8454 6.86815 11.8141C6.7194 12.2524 6.57742 12.5616 6.44219 12.7417C6.30696 12.9139 6.11089 13 5.85396 13C5.57674 13 5.35024 12.9061 5.17444 12.7182C5.00541 12.5225 4.90061 12.2524 4.86004 11.908C4.4476 12.636 3.94388 13 3.34888 13ZM4.00811 11.8611C4.17715 11.8611 4.3428 11.771 4.50507 11.591C4.6741 11.4031 4.78905 11.1487 4.8499 10.8278L5.33671 8.17417C5.33671 8.07241 5.30291 7.97456 5.23529 7.88063C5.16768 7.77886 5.06288 7.72798 4.92089 7.72798C4.65044 7.72798 4.40703 7.91194 4.19067 8.27984C3.97431 8.63992 3.80527 9.07828 3.68357 9.59491C3.56187 10.1037 3.50101 10.5538 3.50101 10.9452C3.50101 11.3366 3.54834 11.5871 3.643 11.6967C3.74442 11.8063 3.86613 11.8611 4.00811 11.8611Z" fill="white"/>
            <path d="M14.6908 14C14.1433 14 13.7246 13.8754 13.4348 13.6261C13.1449 13.3692 13 13.0104 13 12.5496C13 12.3229 13.0282 12.1076 13.0845 11.9037L14.3768 6.22663L16.1643 6L15.5845 8.54958C15.81 8.42115 15.9952 8.33806 16.1401 8.30028C16.285 8.25496 16.43 8.2323 16.5749 8.2323C17.525 8.2323 18 8.87819 18 10.17C18 10.6912 17.8913 11.2502 17.6739 11.847C17.4646 12.4363 17.1103 12.9424 16.6111 13.3654C16.12 13.7885 15.4799 14 14.6908 14ZM15.3672 12.9009C15.6167 12.9009 15.8502 12.7573 16.0676 12.4703C16.285 12.1756 16.4581 11.813 16.587 11.3824C16.7158 10.9443 16.7802 10.525 16.7802 10.1246C16.7802 9.82247 16.7238 9.56563 16.6111 9.35411C16.4984 9.14259 16.3414 9.03683 16.1401 9.03683C16.0193 9.03683 15.8824 9.05571 15.7295 9.09348C15.5845 9.1237 15.4839 9.17281 15.4275 9.24079L14.7633 12.119C14.7391 12.2096 14.7271 12.2965 14.7271 12.3796C14.7271 12.7271 14.9404 12.9009 15.3672 12.9009Z" fill="white"/>
            <path d="M8 15L13 5" stroke="white" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
    </div>
    <div style="margin: auto auto auto 0;">
        ${window.tt('common', 'Да/нет')}
    </div>
</button>`
                );
                $btnAddQuestionTrueFalse.appendTo($buttonsRow);
                $btnAddQuestionTrueFalse.click(function() {
                    self.questionsEl.questionsEditor('addQuestion', 'true_false');
                });


                $btnAddQuestionSelectOne = $(`
<button type="button" class="btn btn-primary pull-left" style="display: flex; height: 34px; margin: 0;">
    <div style="margin: auto 5px auto auto;">
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M9.34888 8C8.96349 8 8.64233 7.84736 8.3854 7.54207C8.12847 7.23679 8 6.7593 8 6.10959C8 5.53033 8.09804 4.92368 8.29412 4.28963C8.49696 3.64775 8.79446 3.10763 9.18661 2.66928C9.58553 2.22309 10.0588 2 10.6065 2C10.8837 2 11.0899 2.05479 11.2252 2.16438C11.3604 2.27397 11.428 2.41879 11.428 2.59883V2.68102L11.5396 2.05871H13L12.2698 6.05088C12.2427 6.1683 12.2292 6.29354 12.2292 6.42661C12.2292 6.58317 12.2596 6.69667 12.3205 6.76712C12.3881 6.82975 12.4963 6.86106 12.645 6.86106C12.7397 6.86106 12.8141 6.8454 12.8682 6.81409C12.7194 7.25245 12.5774 7.56164 12.4422 7.74168C12.307 7.91389 12.1109 8 11.854 8C11.5767 8 11.3502 7.90607 11.1744 7.7182C11.0054 7.5225 10.9006 7.25245 10.86 6.90802C10.4476 7.63601 9.94388 8 9.34888 8ZM10.0081 6.86106C10.1771 6.86106 10.3428 6.77104 10.5051 6.591C10.6741 6.40313 10.789 6.14873 10.8499 5.82779L11.3367 3.17417C11.3367 3.07241 11.3029 2.97456 11.2353 2.88063C11.1677 2.77886 11.0629 2.72798 10.9209 2.72798C10.6504 2.72798 10.407 2.91194 10.1907 3.27984C9.97431 3.63992 9.80527 4.07828 9.68357 4.59491C9.56187 5.10372 9.50101 5.55382 9.50101 5.94521C9.50101 6.3366 9.54834 6.58708 9.643 6.69667C9.74442 6.80626 9.86613 6.86106 10.0081 6.86106Z" fill="white"/>
            <path d="M9.69082 19C9.14332 19 8.72464 18.8754 8.43478 18.6261C8.14493 18.3692 8 18.0104 8 17.5496C8 17.3229 8.02818 17.1076 8.08454 16.9037L9.37681 11.2266L11.1643 11L10.5845 13.5496C10.81 13.4212 10.9952 13.3381 11.1401 13.3003C11.285 13.255 11.43 13.2323 11.5749 13.2323C12.525 13.2323 13 13.8782 13 15.17C13 15.6912 12.8913 16.2502 12.6739 16.847C12.4646 17.4363 12.1103 17.9424 11.6111 18.3654C11.12 18.7885 10.4799 19 9.69082 19ZM10.3672 17.9009C10.6167 17.9009 10.8502 17.7573 11.0676 17.4703C11.285 17.1756 11.4581 16.813 11.587 16.3824C11.7158 15.9443 11.7802 15.525 11.7802 15.1246C11.7802 14.8225 11.7238 14.5656 11.6111 14.3541C11.4984 14.1426 11.3414 14.0368 11.1401 14.0368C11.0193 14.0368 10.8824 14.0557 10.7295 14.0935C10.5845 14.1237 10.4839 14.1728 10.4275 14.2408L9.76329 17.119C9.73913 17.2096 9.72705 17.2965 9.72705 17.3796C9.72705 17.7271 9.94042 17.9009 10.3672 17.9009Z" fill="white"/>
            <path d="M4.5 3L2.5 6L1 5" stroke="white" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
    </div>
    <div style="margin: auto auto auto 0;">
        ${window.tt('common', 'Единичный выбор')}
    </div>
</button>`
                );
                $btnAddQuestionSelectOne.appendTo($buttonsRow);
                $btnAddQuestionSelectOne.click(function() {
                    self.questionsEl.questionsEditor('addQuestion', 'select_one');
                });

                $btnAddQuestionGap = $(
                    '<button type="button" class="btn btn-primary pull-left" style="display: flex; height: 34px">' +
                    '<div style="margin: auto 5px auto auto;">' +
                    '<svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">' +
                    '<path d="M2.34888 17C1.96349 17 1.64233 16.8474 1.3854 16.5421C1.12847 16.2368 1 15.7593 1 15.1096C1 14.5303 1.09804 13.9237 1.29412 13.2896C1.49696 12.6477 1.79446 12.1076 2.18661 11.6693C2.58553 11.2231 3.05882 11 3.60649 11C3.88371 11 4.08993 11.0548 4.22515 11.1644C4.36038 11.274 4.42799 11.4188 4.42799 11.5988V11.681L4.53955 11.0587H6L5.26978 15.0509C5.24273 15.1683 5.22921 15.2935 5.22921 15.4266C5.22921 15.5832 5.25963 15.6967 5.32049 15.7671C5.3881 15.8297 5.49628 15.8611 5.64503 15.8611C5.73969 15.8611 5.81406 15.8454 5.86815 15.8141C5.7194 16.2524 5.57742 16.5616 5.44219 16.7417C5.30696 16.9139 5.11089 17 4.85396 17C4.57674 17 4.35024 16.9061 4.17444 16.7182C4.00541 16.5225 3.90061 16.2524 3.86004 15.908C3.4476 16.636 2.94388 17 2.34888 17ZM3.00811 15.8611C3.17715 15.8611 3.3428 15.771 3.50507 15.591C3.6741 15.4031 3.78905 15.1487 3.8499 14.8278L4.33671 12.1742C4.33671 12.0724 4.30291 11.9746 4.23529 11.8806C4.16768 11.7789 4.06288 11.728 3.92089 11.728C3.65044 11.728 3.40703 11.9119 3.19067 12.2798C2.97431 12.6399 2.80527 13.0783 2.68357 13.5949C2.56187 14.1037 2.50101 14.5538 2.50101 14.9452C2.50101 15.3366 2.54834 15.5871 2.643 15.6967C2.74442 15.8063 2.86613 15.8611 3.00811 15.8611Z" fill="white"/>' +
                    '<path d="M9.69082 10C9.14332 10 8.72464 9.87535 8.43478 9.62606C8.14493 9.36922 8 9.01039 8 8.54958C8 8.32295 8.02818 8.10765 8.08454 7.90368L9.37681 2.22663L11.1643 2L10.5845 4.54958C10.81 4.42115 10.9952 4.33806 11.1401 4.30028C11.285 4.25496 11.43 4.2323 11.5749 4.2323C12.525 4.2323 13 4.87819 13 6.16997C13 6.69122 12.8913 7.25024 12.6739 7.84703C12.4646 8.43626 12.1103 8.9424 11.6111 9.36544C11.12 9.78848 10.4799 10 9.69082 10ZM10.3672 8.90085C10.6167 8.90085 10.8502 8.75732 11.0676 8.47026C11.285 8.17564 11.4581 7.81303 11.587 7.38244C11.7158 6.94429 11.7802 6.52502 11.7802 6.12465C11.7802 5.82247 11.7238 5.56563 11.6111 5.35411C11.4984 5.14259 11.3414 5.03683 11.1401 5.03683C11.0193 5.03683 10.8824 5.05571 10.7295 5.09348C10.5845 5.1237 10.4839 5.17281 10.4275 5.24079L9.76329 8.11898C9.73913 8.20963 9.72705 8.29651 9.72705 8.3796C9.72705 8.7271 9.94042 8.90085 10.3672 8.90085Z" fill="white"/>' +
                    '<path d="M16.6316 17C16.1193 17 15.7193 16.8524 15.4316 16.5573C15.1439 16.2544 15 15.7845 15 15.1476C15 14.6117 15.0947 14.0214 15.2842 13.3767C15.4807 12.732 15.7895 12.1767 16.2105 11.7107C16.6386 11.2369 17.1789 11 17.8316 11C18.2596 11 18.5614 11.101 18.7368 11.3029C18.9123 11.5049 19 11.765 19 12.0835C19 12.3631 18.9439 12.5728 18.8316 12.7126C18.7263 12.8524 18.5965 12.9223 18.4421 12.9223C18.3088 12.9223 18.186 12.8757 18.0737 12.7825C18.1579 12.534 18.2 12.3049 18.2 12.0951C18.2 11.7767 18.1053 11.6175 17.9158 11.6175C17.7053 11.6175 17.4947 11.8117 17.2842 12.2C17.0737 12.5806 16.8982 13.0388 16.7579 13.5748C16.6246 14.1029 16.5579 14.5612 16.5579 14.9495C16.5579 15.5942 16.7684 15.9165 17.1895 15.9165C17.3789 15.9165 17.5895 15.8544 17.8211 15.7301C18.0596 15.5981 18.2702 15.4466 18.4526 15.2757C18.2632 16.4252 17.6561 17 16.6316 17Z" fill="white"/>' +
                    '<path d="M9 16L12 16" stroke="white" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>' +
                    '</svg>' +
                    '</div>' +
                    '<div style="margin: auto auto auto 0;">' +
                    window.tt('common', 'Заполнение пропусков') +
                    '</div>' +
                    '</button>'
                );
                $btnAddQuestionGap.appendTo($buttonsRow);
                $btnAddQuestionGap.click( function() {
                    self.questionsEl.questionsEditor('addQuestion', 'gap');
                });
                if (window.combinationTestsFeature) {
                    $btnAddQuestionCombination = $(`
<button type="button" class="btn btn-primary pull-left" style="display: flex; height: 34px">
	<div style="margin: auto 5px auto auto;"></div>
	<div style="margin: auto auto auto 0;">
		${window.tt('common', 'Соединение вариантов')}
	</div>
</button>`
                    );
                    $btnAddQuestionCombination.appendTo($buttonsRow);
                    $btnAddQuestionCombination.click(function () {
                        self.questionsEl.questionsEditor('addQuestion', 'combination');
                    });
                }
            } else {
                let $btnAddQuestion = $('<button class="btn btn-default pull-left"> <span class="fa fa-plus"></span>'+addQuestionStr+'</button>');
                $btnAddQuestion.appendTo($buttonsRow);
                $btnAddQuestion.click( function() {
                    self.questionsEl.questionsEditor('addQuestion');
                });
            }

			if ( self.options.canDelete ) {
                let $btnDelete;
                if ($btnAddQuestionTrueFalse || $btnAddQuestionSelectOne) {
                    $btnDelete = $(`<button class="btn btn-delete btn-danger pull-right" style="margin-top: 5px">${deleteStr}</button>`);
                    $btnDelete.appendTo($buttonsDiv);
                } else {
                    $btnDelete = $('<button class="btn btn-delete btn-danger pull-right">'+deleteStr+'</button>');
                    $btnDelete.appendTo ( $buttonsRow );
                }

				$btnDelete.click( function() {
					self._deleteTesting();
				});

			}

			if ( self.options.questionaryId ) {
				//$btnSettings = $('<button class="btn btn-default pull-left"> <span class="fa fa-cog"></span> Настройки тестирования </button>')
				//$btnSettings.appendTo($buttonsRow)
				//$btnSettings.click( function() {
					//window.open( "/pl/teach/questionary/update-testing?id=" + self.options.questionaryId + "&part=settings" )
					//self.modal.hide();
				//})
			}

            $buttonsRow.find('button').on('click', function() {
                self._addTagsPanel();
            });

			if(!self.options.questionaryId) {
				$('<div class="clearfix"></div><p></p>').appendTo(self.modal.getFooterEl());
				let $footerAddExistQuestionnaireRow = $('<div class=""></div>');
				$footerAddExistQuestionnaireRow.appendTo(self.modal.getFooterEl());

				self._initUseExist(
                    $footerAddExistQuestionnaireRow,
                    $btnAddQuestion,
                    $btnAddQuestionMultipleChoice,
                    $btnAddQuestionTrueFalse,
                    $btnAddQuestionSelectOne,
                    $btnAddQuestionGap,
                    $btnAddQuestionCombination
                );
			}
		}

		self.modal.show();
	},
    _addTagsPanel: function() {
        if (!$('#addTagsEl').length && this.objectTypeId) {
            this.modal?.getModalEl()
                .find('.questionnaire_modal_buttons')
                .append(`<div class="gc-tags" id="addTagsEl"
                    data-object-type-id="${this.objectTypeId}"
                    data-object-id=""
                    data-tags=""
                    data-show-archived-selector="false"></div>`);

            $('#addTagsEl').objectTagsLink({
                'editable': true,
                'noSave': true
            });
        }
    },
	_initUseExist: function (
        $footerAddExistQuestionnaireRow,
        $btnAddQuestion = false,
        $btnAddQuestionMultipleChoice = false,
        $btnAddQuestionTrueFalse = false,
        $btnAddQuestionSelectOne = false,
        $btnAddQuestionGap = false,
        $btnAddQuestionCombination = false
    ) {
		var self = this;
		$footerAddExistQuestionnaireRow.empty();
		let useExistQuestionnaireLabel = 'Использовать тестирование';
		let notSelectedQuestionnaire = '--не выбрано--';
		let questionnairies = 'Тестирования';
		let deleteTestStr = 'Удалить тест из урока';

		if (typeof Yii != 'undefined') {
			useExistQuestionnaireLabel = Yii.t('common', useExistQuestionnaireLabel);
			notSelectedQuestionnaire = Yii.t('common', notSelectedQuestionnaire);
			questionnairies = Yii.t('common', questionnairies);
			deleteTestStr = Yii.t('common', deleteTestStr);
		}

		let $useExistQuestionnaireLabel = $('<div class="text-left">' + useExistQuestionnaireLabel + '</div>');
		$useExistQuestionnaireLabel.appendTo($footerAddExistQuestionnaireRow);

		let $useExistQuestionnaire = $('<div class="text-left questionnaire_modal_buttons js__questionnaire_modal_buttons"></div>');
		$useExistQuestionnaire.appendTo($footerAddExistQuestionnaireRow);
		$useExistQuestionnaire.find('select').select2('destroy');
		$useExistQuestionnaire.empty();

		let $selectNode = $('<select class="questionnaire-select js__questionnaire-select" '
			+ 'name="questionnaireId" data-placeholder="'+ notSelectedQuestionnaire
			+'"></select>');
		$selectNode.appendTo($useExistQuestionnaire);

		$('<option></option>').appendTo($selectNode);

		self.options.questionaries.forEach(function(item, i, arr) {
			let selected = (self.options.questionaryId ==  item.value ? 'selected="selected"' : '');
			let $optionAdd = $('<option ' + selected + ' value="'+ item.value +'">' + item.label + '</option>');
			$optionAdd.appendTo($selectNode);
		});

		$selectNode.select2('destroy');
		$selectNode.select2({
			placeholder: notSelectedQuestionnaire,
			allowClear: true,
		});

		if($btnAddQuestion) {
			$selectNode.off('change').on('change', function() {
				let value = $(this).find('option:selected').val();

				self.options.newQuestionaryId = value;
				if(value) {
					$btnAddQuestion.attr('disabled', true);
                    if ($btnAddQuestionMultipleChoice) {
                        $btnAddQuestionMultipleChoice.attr('disabled', true);
                    }
                    if ($btnAddQuestionTrueFalse) {
                        $btnAddQuestionTrueFalse.attr('disabled', true);
                    }
                    if ($btnAddQuestionSelectOne) {
                        $btnAddQuestionSelectOne.attr('disabled', true);
                    }
                    if ($btnAddQuestionGap) {
                        $btnAddQuestionGap.attr('disabled', true);
                    }
                    if ($btnAddQuestionCombination) {
                        $btnAddQuestionCombination.attr('disabled', true);
                    }
                } else {
					$btnAddQuestion.attr('disabled', false);
                    if ($btnAddQuestionMultipleChoice) {
                        $btnAddQuestionMultipleChoice.attr('disabled', false);
                    }
                    if ($btnAddQuestionTrueFalse) {
                        $btnAddQuestionTrueFalse.attr('disabled', false);
                    }
                    if ($btnAddQuestionSelectOne) {
                        $btnAddQuestionSelectOne.attr('disabled', false);
                    }
                    if ($btnAddQuestionGap) {
                        $btnAddQuestionGap.attr('disabled', false);
                    }
                    if ($btnAddQuestionCombination) {
                        $btnAddQuestionCombination.attr('disabled', false);
                    }
				}
				$('select.js__questionnaire-select').val(value);
			});
		} else {
			$selectNode.off('change').on('change', function() {
				self.options.newQuestionaryId = null;
				let value = $(this).find('option:selected').val();
				self.options.questionaryId = value;
				if(!value) {
					$('.js__update_testing').empty();

					self.options.editorOptions.questionary = {};
					self.options.editorOptions.defaultQuestionaryName = null;
				}
				self._create();
			});
		}


		let $questionnairiesLink = $('<a class="questionnaire-link" href="/pl/teach/questionary" '
			+ 'title="" target="_blank">'
			+ questionnairies + '</a>');
		$questionnairiesLink.appendTo($useExistQuestionnaire);

		if ( self.options.canDelete ) {
			$('.js__delete_testing_button').remove();
			let $deleteFromLessonButton = $('<button class="btn btn-danger js__delete_testing_button" type="button"><span class="glyphicon glyphicon-trash"></span> ' + deleteTestStr + '</button>');
			$deleteFromLessonButton.click(function () {
					self._deleteTesting();
				}
			);
			if ($('.js__update_testing').length > 0) {
				$('.js__update_testing').append(' ');
				$('.js__update_testing').append($deleteFromLessonButton);
			}
			if ($('.note-btn-group.btn-group.note-testing').length > 0) {
				$deleteFromLessonButton.addClass('btn-sm');
				$('.note-btn-group.btn-group.note-testing').append($deleteFromLessonButton);
			}
		}

		return $selectNode;
	},
	_deleteTesting: function () {
		var self = this;
		if ( ! confirm( Yii.t( 'common', 'Are you sure?' ) ) ) {
			return;
		}
		self.questionsEl.questionsEditor('deleteQuestionary');

		if ( self.options.onTrySave ) {
			var newValue = self.questionsEl.questionsEditor('getValue');
			self.options.onTrySave( newValue, function() {
				self.modal.hide();

			});
		} else {
			self.options.questionaryId = null;
			var options = self.options.editorOptions;
			options.questionary = {questions: []};
			self.questionsEl.questionsEditor(options);
			$('#questions-value').val(false);
			self._create();
			if(self.modal) {
				self.modal.hide();
			}
			self.modal = false;
		}

		if($('.js__update_testing').length >0) {
			$('.js__update_testing').empty();
		}

		if($('.js__questionary__use_exists').length >0) {
			$('.js__questionary__use_exists select').select2('destroy');
			$('.js__questionary__use_exists').empty();
		}
	}
});
