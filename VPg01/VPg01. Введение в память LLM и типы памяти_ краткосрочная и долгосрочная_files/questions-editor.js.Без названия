jQuery.widget( 'gc.questionsEditor', {
	options: {
		questionary: {},
		light: false,
		showAddButton: false,
		inputName: null,
		defaultQuestionaryName: null,
		ownerType: null,
		onChange: null
	},
	deleted: false,
	initRedactor: function( $el, full ) {
		if ( ! ( $el.val().indexOf('<p>') > -1 ) ) {
			return;
		}
		if ( $('#redactorToolbar').length == 0 ) {
			$( '<div  id="redactorToolbar" class="gc-into-main-content redactor-main-toolbar out"></div>' ).appendTo( $(document.body));
		}

		$el.redactor({
			lang: (typeof Yii != 'undefined') ? Yii.translate.config.language : 'ru',
			toolbarExternal: '#redactorToolbar',
			buttonSource: full ? true : null ,
			minHeight: 28,
			plugins: full ? ['source', 'fontcolor', 'fontsize', 'typograph'] : ['source','typograph']
		});

	},
	_create: function () {
		var self = this;
		this.element.addClass("questions-editor");
		if ( this.options.light ) {
			this.element.addClass('questions-editor-light')
		}

		this.element.empty();


		if ( this.options.valueInputSelector ) {
			this.valInput = $(this.options.valueInputSelector);
			if ( this.options.inputName ) {
				this.valInput.attr('name', this.options.inputName)
			}
		}
		else if ( this.options.inputName ) {
			this.valInput = $('<input type="hidden"/>');
			this.valInput.attr('name', this.options.inputName);
			this.valInput.appendTo( this.element )
		}

		this.questionListEl = $('<div class="question-list"></div>');
		this.questionListEl.appendTo( this.element );

		// conflicts with redactor
		this.questionListEl.sortable({
			update: function(e, ui) {
				self.disableClickEvent = true;
				self.preSave();
				//alert("E")
			}
		});

		//this.addStartSettingsToList();
		//this.addFinishSettingsToList();

		if ( this.options.questionary.questions ) {
			for ( var i = 0; i < this.options.questionary.questions.length; i++ ) {
				var question = this.options.questionary.questions[i];
				this.addQuestionToList( question )

			}
		}

		if ( this.options.showAddButton ) {
            if (window.newTestsFeature) {
                const buttonBlock = $('<div style="display: flex; margin-top: 10px;"></div>');

                const addQuestionBtnMultiplyChoiceBlock = $(
                    '<div style="margin-right: 15px">' +
                    '</div>'
                );
                const addQuestionBtnMultiplyChoice = $(
                    '<button type="button" class="btn btn-primary btn-add-question" style="display: flex;">' +
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
                addQuestionBtnMultiplyChoice.appendTo(addQuestionBtnMultiplyChoiceBlock);
                addQuestionBtnMultiplyChoiceBlock.appendTo(buttonBlock);
                addQuestionBtnMultiplyChoiceBlock.click(() => {
                    self.addQuestion('multiple_choice');
                });


                const addQuestionBtnTrueFalseBlock = $(`
<div style="margin-right: 15px">
    <button type="button" class="btn btn-primary btn-add-question" style="display: flex; height: 39px">
        <div style="margin: 4px 5px auto auto;">
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M3.34888 13C2.96349 13 2.64233 12.8474 2.3854 12.5421C2.12847 12.2368 2 11.7593 2 11.1096C2 10.5303 2.09804 9.92368 2.29412 9.28963C2.49696 8.64775 2.79446 8.10763 3.18661 7.66928C3.58553 7.22309 4.05882 7 4.60649 7C4.88371 7 5.08993 7.05479 5.22515 7.16438C5.36038 7.27397 5.42799 7.41879 5.42799 7.59883V7.68102L5.53955 7.05871H7L6.26978 11.0509C6.24273 11.1683 6.22921 11.2935 6.22921 11.4266C6.22921 11.5832 6.25963 11.6967 6.32049 11.7671C6.3881 11.8297 6.49628 11.8611 6.64503 11.8611C6.73969 11.8611 6.81406 11.8454 6.86815 11.8141C6.7194 12.2524 6.57742 12.5616 6.44219 12.7417C6.30696 12.9139 6.11089 13 5.85396 13C5.57674 13 5.35024 12.9061 5.17444 12.7182C5.00541 12.5225 4.90061 12.2524 4.86004 11.908C4.4476 12.636 3.94388 13 3.34888 13ZM4.00811 11.8611C4.17715 11.8611 4.3428 11.771 4.50507 11.591C4.6741 11.4031 4.78905 11.1487 4.8499 10.8278L5.33671 8.17417C5.33671 8.07241 5.30291 7.97456 5.23529 7.88063C5.16768 7.77886 5.06288 7.72798 4.92089 7.72798C4.65044 7.72798 4.40703 7.91194 4.19067 8.27984C3.97431 8.63992 3.80527 9.07828 3.68357 9.59491C3.56187 10.1037 3.50101 10.5538 3.50101 10.9452C3.50101 11.3366 3.54834 11.5871 3.643 11.6967C3.74442 11.8063 3.86613 11.8611 4.00811 11.8611Z" fill="white"/>
                <path d="M14.6908 14C14.1433 14 13.7246 13.8754 13.4348 13.6261C13.1449 13.3692 13 13.0104 13 12.5496C13 12.3229 13.0282 12.1076 13.0845 11.9037L14.3768 6.22663L16.1643 6L15.5845 8.54958C15.81 8.42115 15.9952 8.33806 16.1401 8.30028C16.285 8.25496 16.43 8.2323 16.5749 8.2323C17.525 8.2323 18 8.87819 18 10.17C18 10.6912 17.8913 11.2502 17.6739 11.847C17.4646 12.4363 17.1103 12.9424 16.6111 13.3654C16.12 13.7885 15.4799 14 14.6908 14ZM15.3672 12.9009C15.6167 12.9009 15.8502 12.7573 16.0676 12.4703C16.285 12.1756 16.4581 11.813 16.587 11.3824C16.7158 10.9443 16.7802 10.525 16.7802 10.1246C16.7802 9.82247 16.7238 9.56563 16.6111 9.35411C16.4984 9.14259 16.3414 9.03683 16.1401 9.03683C16.0193 9.03683 15.8824 9.05571 15.7295 9.09348C15.5845 9.1237 15.4839 9.17281 15.4275 9.24079L14.7633 12.119C14.7391 12.2096 14.7271 12.2965 14.7271 12.3796C14.7271 12.7271 14.9404 12.9009 15.3672 12.9009Z" fill="white"/>
                <path d="M8 15L13 5" stroke="white" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
        </div>
        <div style="margin: auto auto auto 0;">
            ${window.tt('common', 'Да/нет')}
        </div>
    </button>
</div>`
                );
                addQuestionBtnTrueFalseBlock.appendTo(buttonBlock);
                addQuestionBtnTrueFalseBlock.find('button').click(() => {
                    self.addQuestion('true_false');
                });


                const addQuestionBtnSelectOneBlock = $(`
<div style="margin-right: 15px">
	<button type="button" class="btn btn-primary btn-add-question" style="display: flex; height: 39px">
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
	</button>
</div>`
                );
                addQuestionBtnSelectOneBlock.appendTo(buttonBlock);
                addQuestionBtnSelectOneBlock.find('button').click(() => {
                    self.addQuestion('select_one');
                });

                const addQuestionBtnGapBlock = $('<div style="margin-right: 15px"></div>');
                const addQuestionBtnGap = $(
                    '<button type="button" class="btn btn-primary btn-add-question" style="display: flex;">' +
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
                addQuestionBtnGap.appendTo(addQuestionBtnGapBlock);
                addQuestionBtnGapBlock.appendTo(buttonBlock);
                addQuestionBtnGap.click(() => {
                    self.addQuestion('gap');
                });

                if (window.combinationTestsFeature) {
                    const addQuestionBtnCombinationBlock = $(`
    <div style="margin-right: 15px">
        <button type="button" class="btn btn-primary btn-add-question" style="display: flex; height: 39px">
            <div style="margin: auto 5px auto auto;">
            </div>
            <div style="margin: auto auto auto 0;">
                ${window.tt('common', 'Соединение вариантов')}
            </div>
        </button>
    </div>`
                    );
                    addQuestionBtnCombinationBlock.appendTo(buttonBlock);
                    addQuestionBtnCombinationBlock.find('button').click(() => {
                        self.addQuestion('combination');
                    });
                }

                buttonBlock.appendTo(this.element);
            } else {
                this.addQuestionBtn = $(
                    '<button type="button" class="btn btn-primary btn-add-question">'
                    +'<span class="fa fa-plus"></span> ' + window.tt('common', 'Add question')
                    + '</button>'
                );
                this.addQuestionBtn.appendTo(this.element);
                this.addQuestionBtn.click( function() {
                    self.addQuestion();
                });
            }
        }




		self.preSave(true);

		//this.addQuestion()
	},
	addStartSettingsToList: function() {
		let $result = $('<div class="questionary-settings questionary-list-item">');

		let label = window.tt('common', 'Начало  тестирования');

		$('<div class="toggle-expand-link collapsed-data"> <span class="fa fa-play-circle"/> ' + label + '</div>').appendTo( $result )

		let $expandedData = $('<div class="expanded-data"/>').appendTo( $result );
		$('<label class="toggle-expand-link"><span class="fa fa-caret-down"/>'+ label +' </label>').appendTo( $expandedData );

		$(
			'<div class="field-item">'
			+ '<label>'+window.tt('common', 'Заголовок')+'</label>'
			+ '<input type="text" class="form-control questionary-title-input">'
			+'</div>'
		).appendTo( $expandedData );

		$(
			'<div class="field-item">'
			+'<label>'+window.tt('common', 'Описание')+'</label>'
			+'<textarea type="text" class="form-control questionary-description-input"/>'
			+'</div>'
		).appendTo( $expandedData );

		var questionary = this.options.questionary;
		$result.find('.questionary-title-input').val( questionary.before_start_header );
		$result.find('.questionary-description-input').val( questionary.before_start_text );

		this.initQuestionaryListItem( $result );

		$result.appendTo( this.questionListEl );

	},
	addFinishSettingsToList: function() {
		let $result = $('<div class="questionary-settings questionary-list-item">');
		let label = window.tt('common', 'Результаты тестирования');

		$('<div class="toggle-expand-link collapsed-data"> <span class="fa fa-check-circle"/> ' + label + '</div>').appendTo( $result )

		let $expandedData = $('<div class="expanded-data"/>').appendTo( $result );

		$('<label class="toggle-expand-link"><span class="fa fa-caret-down"/> '+ label +' </label>').appendTo( $expandedData );

		let $minPoints = $(
			'<div><label>'
			+ '<input type="checkbox"> '
			+window.tt(
				'common',
				'Не принимать ответ на задание если набрано менее {n} баллов',
				{n: '<input type="text" size="4">'}
			)
			+ '</label></div>'
		);
		$minPoints.appendTo( $expandedData )

		let $maxPoints = $(
			'<div><label>'
			+ '<input type="checkbox"> '
			+window.tt(
				'common',
				'Автоматически принимать ответ на задание если набрано {n} баллов и более',
				{n: '<input type="text" size="4">'}
			)
			+ '</label></div>'
		);
		$maxPoints.appendTo( $expandedData );

		$(
			'<div>'
			+ '<label>'+window.tt('common', 'Текст после результатов')+'</label>'
			+ '<textarea type="text" class="form-control text-after-results"/>'
			+ '</div>'
		).appendTo( $expandedData);



		$result.appendTo( this.questionListEl );
		this.finishSettingsEl = $result;
		this.initQuestionaryListItem( $result );


		return $result;
	},
	addQuestionToList: function( question ) {
        if (window.newTestsFeature) {
            const type = question.params.type;
            if (type === 'true_false') {
                return this.addQuestionToListTrueFalse(question);
            } else if (type === 'select_one') {
                return this.addQuestionToListSelectOne(question);
            } else if (type === 'combination') {
                return this.addQuestionToListCombination(question);
            }
        }

		var self = this;

		let strings = {
			question: 'Question',
			deleteQuestion: 'Delete question',
			questionNumber: 'Question number',
			questionDescription: 'question text (optionally)',
			questionVideo: 'Видео вопроса',
			changeQuestionVideo: 'Изменить',
			uploadQuestionVideo: 'Загрузить',
			uploadMaxSize: 'Макс. размер 6 ГБ',
			deleteQuestionVideo: 'Удалить',
			questionPicture: 'Question picture',
			pointsForRightAnswer: 'Points for right answer',
			answerChoice: 'Answer choice',
			right: 'Right',
			actions: 'Actions',
			addAnswer: 'Add answer',
			textInCaseOfRightAnswer: 'Text in case of right answer',
			textInCaseOfError: 'Text in case of error',
			option: 'Option',
			addDescription: 'Description',
			answerMode: 'Ученик должен выбрать все правильные варианты ответа',
			requiredQuestion: 'Обязательный вопрос',
			failVideoSelect: 'Видео в процессе транскодирования',
		};
        if (window.newTestsFeature) {
            if (question.params.gap_test) {
                strings.question = '';
            }
            strings.gapTestModeDrag = 'Вставить значения';
            strings.gapTestModeText = 'Заполнить пробелы текстом';
            strings.gapTestText = 'Вопрос';
            strings.gapTestModeTextCaseSensitive = 'Учитывать регистр ответов';
            strings.gapTestAddWrongVariant = 'Добавить лишний ответ';
            strings.gapTestPointsForRightAnswer = 'Баллов за правильных ответ на вопрос';
            strings.gapTestPointsForGap = 'Баллов за каждый правильно заполненный пропуск';
            strings.gapTestUnnecessaryQuestions = 'Лишние ответы';
            strings.gapTestTextInCaseOfRightAnswer = 'Text in case of right answer';
            strings.gapTestTextInCaseOfError = 'Text in case of error';
            strings.gapTestDisplayMessageAfterReply = 'Отображать сообщение после ответа';
            strings.gapTestMode = 'Вид вопроса';
        }
		strings = self.translateStrings(strings);

		var variantsList =
			'<table class="table variants-table">' +
				'<thead><tr>' +
				'<th>'+strings.answerChoice+'</th>' +
				'<th width="100" class="text-center">'+strings.right+'</th>' +
				'<th width="100" class="text-center">'+strings.actions+'</th>' +
				'</tr></thead>' +
				'<tbody class="variant-list"></tbody>' +
			'</table>';

		if ( this.options.light ) {
            if (window.newTestsFeature) {
                variantsList = '<div class="variant-list">' +
                    '<div class="gap-test-unnecessary-questions-label" style="display: none; margin-bottom: 5px;">' +
                    '<span>' + strings.gapTestUnnecessaryQuestions + ' </span>' +
                    '<a target="_blank" href="/pl/help-proxy?url=/help/extraanswers">' +
                    '<span class="glyphicon glyphicon-question-sign" style="color: #999; margin: 0 2px;">' +
                    '	</a>' +
                    '</div>' +
                    '</div>';
            } else {
                variantsList = '<div class="variant-list"></div>'
            }
		}
		var questionVideoInputId = 'questionVideoInput' + Math.floor(Math.random() * 10000) + Date.now();

		var questionRequiredBlock = '<label class="question-required-label">'
			+ '<input type="checkbox" class="question-required"/> ' + strings.requiredQuestion + '</label>'
			+ '<a target="_blank" href="/pl/help-proxy?url=/help/obligatoryquestion">'
			+ '<span class="glyphicon glyphicon-question-sign" style="color: #999; margin: 0 2px;"></a>'
			+ '<br>';


        if (window.newTestsFeature) {
            var gapTestModeRadioName = Math.random().toString(36).substring(2, 10);
            var gapTestPointsRadioName = Math.random().toString(36).substring(2, 10);
        }

		var $questionEl = $(
			'<div class="question questionary-list-item js__questionary-list-item">' +
                (window.newTestsFeature ? '<input type="hidden" class="question-type" />' : '') +
				'<div class="toggle-expand-link collapsed-data"><span class="fa fa-caret-right"></span> <span class="question-title"></span></div>' +
				'<div class="expanded-data">' +
					'<button type="button" class="btn btn-sm btn-link btn-delete-question pull-right">'+strings.deleteQuestion+'</button>' +
					'<div class="form-group">' +
                        '<div>' +
                            '<label class="toggle-expand-link"> <span class="fa fa-caret-down"/> ' + strings.question + ' </label>' +
                            '<div class="question-number">'+strings.questionNumber+': <input class="form-control text-center question-order-input" style="width: 50px; display: inline-block"></div>' +
                            '<input class="form-control question-title-input" placeholder="' + strings.question + '"/>' +
                        '</div>' +
						questionRequiredBlock +
                        '<label class="question-mode-input-label"><input type="checkbox" class="question-mode-input"/> '+ strings.answerMode +'</label>' +
                        (window.newTestsFeature ? (
                            '<input type="hidden" class="gap-test" /> ' +
                            '<div class="gap-test-mode" style="margin-left: 15px; display: none;">' +
                            '<div>' +
                            '<span>' + strings.gapTestMode + ' </span>' +
                            '<a target="_blank" href="/pl/help-proxy?url=/help/fillintheblanks">' +
                            '<span class="glyphicon glyphicon-question-sign" style="color: #999; margin: 0 2px;">' +
                            '</a>' +
                            '</div>' +
                            '<div style="margin-left: 5px; margin-top: 5px;">' +
                            '<label>' +
                            '<input type="radio" name="' + gapTestModeRadioName + '" class="gap-test-mode-drag" checked/> ' +
                            strings.gapTestModeDrag +
                            '</label>' +
                            '<br/>' +
                            '<label>' +
                            '<input type="radio" name="' + gapTestModeRadioName + '" class="gap-test-mode-text"/> ' +
                            strings.gapTestModeText +
                            '</label>' +
                            '</div>' +
                            '<div style="margin-left: 5px;">' +
                            '<label class="gap-test-mode-text-case-sensitive-label">' +
                            '<input type="checkbox" class="gap-test-mode-text-case-sensitive"/> ' + strings.gapTestModeTextCaseSensitive +
                            '</label>' +
                            '</div>' +
                            '</div>'
                        ) : '') +
						'<textarea class="form-control question-description-input" rows=3 placeholder="'+strings.questionDescription+'"/>' +
						'<div class="question-video-wrapper">' +
							strings.questionVideo +
							'<br/><input type="hidden" class="question-video-input" id="' + questionVideoInputId + '">' +
							'<div>' +
							'<div class="question-video-preview"></div>' +
							'<a href="javascript:void(0)" class="question-video-input-changer dotted-link">' +
							strings.changeQuestionVideo +
							'</a>' +
							'<div class="question-upload-wrapper" style="display: none;">' +
								'<a href="javascript:void(0)" class="question-video-input-upload">' +
								strings.uploadQuestionVideo +
								'</a>' +
								'<p class="text-muted">' + strings.uploadMaxSize + '</p>' +
							'</div>' +
							'<a href="javascript:void(0)" class="question-video-input-delete dotted-link" style="display: none;">' +
							strings.deleteQuestionVideo +
							'</a>' +
							'</div>' +
						'</div>' +
						'<div class="question-picture-wrapper">' + strings.questionPicture + '<br/><input type="hidden" class="question-image-input"></div>' +
						'<div class="question-points-wrapper">' + strings.pointsForRightAnswer + ': <input placeholder="1" class="text-center form-control question-points-input" style="width: 50px; display: inline-block"></div>' +
                        (window.newTestsFeature ? (
                            '<div class="question-points-wrapper-gap" style="display: none;">' +
                            '<label>' +
                            '<input type="radio" name="' + gapTestPointsRadioName + '" class="gap-test-points-mode-question"/> ' +
                            strings.gapTestPointsForRightAnswer +
                            ': <input placeholder="1" class="text-center form-control gap-test-points-mode-question-input" style="width: 50px; display: inline-block">' +
                            '</label>' +
                            '<br/>' +
                            '<label>' +
                            '<input type="radio" name="' + gapTestPointsRadioName + '" class="gap-test-points-mode-gap"/> ' +
                            strings.gapTestPointsForGap +
                            ': <input placeholder="1" class="text-center form-control gap-test-points-mode-gap-input" style="width: 50px; display: inline-block">' +
                            '</label>' +
                            '</div>'
                        ) : '') +
					'</div>' +
                    (window.newTestsFeature ? (
                        '<div class="form-group gap-test-text-container" style="display: none;">' +
                        '<label>' + strings.gapTestText + '</label>' +
                        '<div class="gap-test-text-container question-variant" style="padding: 0">' +
                        '<textarea class="form-control gap-test-text"/>' +
                        '</div>' +
                        '</div>'
                    ) : '') +
					'<div class="buttons questionary-buttons">' +
                        (window.newTestsFeature ? (
                            '<button type="button" class="btn btn-sm btn-link gap-test-btn-add-wrong-variant" style="display: none"> ' + strings.gapTestAddWrongVariant + '</button>'
                        ) : '') +
						'<button type="button" class="btn btn-sm btn-link btn-add-variant"> '+strings.addAnswer+'</button>' +
						'<button type="button" class="btn btn-sm btn-link btn-add-description">  '+strings.addDescription +'</button>' +
						'<div class="btn-free-space"></div>' +
						'<button type="button" class="btn btn-sm btn-link btn-set-points">  ' +
							'<span class="button-label"><span class="question-points-html"/> ' +
								window.tt('common', 'балл') +
							'</span>' +
						'</button>' +
						'<button type="button" class="btn btn-sm btn-link btn-set-image question-btn-set-image">  ' +
						'<span class="button-label">' +
							window.tt('common', 'Картинка') +
						'</span>' +
						'</button>' +
						'<button type="button" class="btn btn-sm btn-link question-btn-set-video">  ' +
						'<span class="button-label">' +
						window.tt('common', 'Видео') +
						'</span>' +
						'</button>' +
					'</div>' +

					variantsList +



					'<div class="answer-text-params">' +

                        (window.newTestsFeature ? (
                            '<div style="margin-top: 15px; margin-bottom: 10px; display: none" class="gap-test-display-message-after-reply">' +
                            '<span>' + strings.gapTestDisplayMessageAfterReply + ' </span>' +
                            '<a target="_blank" href="/pl/help-proxy?url=/help/messageafteranswer">' +
                            '<span class="glyphicon glyphicon-question-sign" style="color: #999; margin: 0 2px;">' +
                            '</a>' +
                            '</div>'
                        ) : '') +
                        '<div class="form-group" style="margin-top: 5px">' +
                            '<label class="text-in-case-of-right-answer">' +
                            strings.textInCaseOfRightAnswer +
                            '</label>' +
							'<textarea class="form-control question-answer-right-input" placeholder=""/>' +
						'</div>' +

						'<div class="form-group">' +
                            '<label class="text-in-case-of-error">' +
                            strings.textInCaseOfError +
                            '</label>' +
							'<textarea class="form-control question-answer-error-input" placeholder=""/>' +
						'</div>' +
					'</div>' +

				'</div>' +
			'</div>'
		);
		$questionEl.appendTo( this.questionListEl );

		if ( ! this.options.questionary.isUseAnswerText ) {
			$questionEl.find('.answer-text-params').hide();
		}

		$questionEl.find('.btn-add-description').click( function() {
			$questionEl.find('.question-description-input').show();
			$questionEl.find('.question-description-input').focus();
			$(this).hide();

		});

		$questionEl.find('.btn-set-points').click( function() {
            if (window.newTestsFeature && self.isGapTest($questionEl)) {
                $questionEl.find('.question-points-wrapper-gap').show();
            } else {
                $questionEl.find('.question-points-wrapper').show();
            }
			$(this).hide();

		});

		$questionEl.find('.btn-set-image').click( function() {
			$questionEl.find('.question-picture-wrapper').show();
			$questionEl.find('.question-video-wrapper').hide();
			if ($questionEl.find('.question-image-input').val() === '') {
				$questionEl.find('.question-btn-set-video').show();
			}
			$(this).hide();

		});
		$questionEl.find('.question-video-input-changer').click(function () {
			$(this).hide();
			$questionEl.find('.question-upload-wrapper').show();
		});
		$questionEl.find('.question-video-input-upload').click(function () {
			window.gcSelectFiles({
				selectedHash: $questionEl.find('.question-video-input').val(),
				type: 'video',
				accept: '.mkv,.mov,.mp4,.avi',
				isShowHint: true,
				callback: function (hash) {
					self.setQuestionVideo($questionEl, hash);
				},
			});
		});
		$questionEl.find('.question-video-input-delete').click(function () {
			self.setQuestionVideo($questionEl, '');
			$questionEl.find('.question-video-preview').text('');
			$questionEl.find('.question-video-wrapper').show();
			$questionEl.find('.question-upload-wrapper').show();
			$questionEl.find('.question-video-input-changer').hide();
			$questionEl.find('.question-btn-set-video').hide();
			$(this).hide();
		})

		$questionEl.find('.question-btn-set-video').click(function () {
			$questionEl.find('.question-video-wrapper').show();
			$questionEl.find('.question-picture-wrapper').hide();
			$questionEl.find('.question-btn-set-video').hide();
			$questionEl.find('.question-btn-set-image').show();
			$(this).hide();
		});

		var noName = 'Question';
		if (typeof Yii != 'undefined') {
			noName = Yii.t('common', noName);
		}

		$questionEl.find( '.question-title-input' ).val( question.title );
		$questionEl.find('.question-mode-input').prop( 'checked',  question.params.right_if_all);

        if (window.newTestsFeature) {
            $questionEl.find('.gap-test').val(question.params.gap_test ? '1' : '0');
        }

		$questionEl.find('.question-required').prop( 'checked',  question.params.required_question);
		$questionEl.find( '.question-title' ).html( question.title ? question.title : noName );
		$questionEl.find( '.question-answer-right-input' ).val( question.params.right_text );
		$questionEl.find( '.question-answer-error-input' ).val( question.params.error_text );

        if (window.newTestsFeature) {
            $questionEl.find('.question-type').val(question.params.type);
        }

		$questionEl.find( '.question-description-input' ).val( question.description );
		if( question.description && question.description != "<p></p>" ) {
			$questionEl.find('.btn-add-description').click();
		}

		this.initRedactor( $questionEl.find( '.question-description-input' ), true );
		$questionEl.find( '.question-points-input' ).val( question.params.right_points );

		var points = 1;
		if ( question.params.right_points &&  question.params.right_points.trim() != "" ) {
			points = question.params.right_points;
			$questionEl.find('.btn-set-points').click();
		}
		if ( question.params.image &&  question.params.image.trim() != "" ) {
			$questionEl.find('.btn-set-image').click();
		}
		$questionEl.find( '.question-points-html' ).html(points)

		$questionEl.find( '.question-title-input' ).change( function() {
			var val = $(this).val();
			$questionEl.find( '.question-title' ).html( val.length > 0 ? val : noName );
		});

		self.initQuestionaryListItem( $questionEl );

		$questionEl.data('question', question);
		$questionEl.data( 'id', question.id );
		$questionEl.find(".question-image-input").val( question.params.image );
		$questionEl.find(".question-image-input").trigger('change');
		$questionEl.find(".question-image-input").fileWidget({showButtonOnStart:true});
		$questionEl.find('.question-order-input').val( this.questionListEl.find( '.question' ).length );

		$questionEl.find(".question-video-input").on('change', function() {
			if ($(this).val() !== '') {
				$
					.get('/pl/teach/questionary/questionary-video?hash=' + $(this).val())
					.done(function (response) {
						$questionEl.find('.question-video-preview').html('<div class="questions-video-player">' + response + '</div>');
						var questionModal = $questionEl.parents('.modal');
						if (questionModal && questionModal.length > 0) {
							// фикс для скролла
							questionModal.modal('hide');
							questionModal.modal('show');
						}
					})
					.fail(function () {
						$questionEl.find('.question-video-preview').html(strings.failVideoSelect);
					})
				;
				$questionEl.find('.question-image-input').val('');
				$questionEl.find('.question-image-input').trigger('change');
				$questionEl.find('.question-video-wrapper').show();
				$questionEl.find('.question-picture-wrapper').hide();
				$questionEl.find('.question-picture-wrapper').find('.question-image-input').next().find('div').first().text('');
				$questionEl.find('.question-picture-wrapper').find('.uploadifive-queue-item.complete').hide();
				$questionEl.find('.question-btn-set-image').hide();
				$questionEl.find('.question-btn-set-video').hide();
				$questionEl.find('.question-video-input-delete').show();
				$questionEl.find('.question-upload-wrapper').hide();
				$questionEl.find('.question-video-input-changer').show();
			} else {
				$questionEl.find('.question-video-wrapper').hide();
				$questionEl.find('.question-btn-set-image').show();
				$questionEl.find('.question-btn-set-video').show();
				if ($questionEl.find('.question-image-input').val() !== '') {
					$questionEl.find('.question-btn-set-image').hide();
					$questionEl.find('.question-btn-set-video').hide();
				}
			}
		});
		this.setQuestionVideo($questionEl, question.params.video);
		$questionEl.find('.question-image-input').on('change', function () {
			if ($(this).val() !== '') {
				self.setQuestionVideo($questionEl, '');
			}
			$questionEl.find('.question-video-input-delete').hide();
			$questionEl.find('.question-video-preview').text('');
			$questionEl.find('.question-btn-set-video').hide();
			$questionEl.find('.question-btn-set-image').hide();
			if ($(this).val() === '') {
				$questionEl.find('.question-btn-set-video').show();
			}
		});

		if ( question.variants ) {
			for (var i = 0; i < question.variants.length; i++ ) {
				var variant = question.variants[i];
				self.addVariantToQuestion( $questionEl, variant )
			}
		}
		$questionEl.find('.variant-list').sortable({
			handle: '.variant-sort-handler'

		});

		var addVariantBtn = $questionEl.find('.btn-add-variant');
		addVariantBtn.click( function() {
			var val = strings.option;
			if ( self.options.light ) {
				val = "";
			}
			let variant = {id: null, value: val, points: null, is_right: false, params: {right_text: null, error_text: null}};

			var $variantEl = self.addVariantToQuestion($questionEl, variant);
			$variantEl.find('.variant-value').focus();
		});

		$questionEl.find( '.btn-delete-question' ).click( function() {
			$questionEl.remove();
			self.globalElementsControl();
		});

        if (this.isGapTest($questionEl)) {
            $questionEl.find('.gap-test-display-message-after-reply').show();
            $questionEl.find('.gap-test-mode-drag').prop('checked', question.params.gap_test_mode === 'drag');
            $questionEl.find('.gap-test-mode-text').prop('checked', question.params.gap_test_mode === 'text');
            $questionEl.find('.gap-test-mode-text-case-sensitive').prop('checked', question.params.gap_test_mode_text_case_sensitive);
            $questionEl.find('.gap-test-points-mode-gap-input').val(question.params.gap_points);
            $questionEl.find('.gap-test-points-mode-question-input').val(question.params.right_points);
            $questionEl.find('.gap-test-text')
                .prop('placeholder', Yii.t('common', 'Например: Мне нравится [ходить\\бегать] у озера по утрам и я [люблю] это делать.').replace('\\', '|'))
                .val(question.params.gap_test_text)
                .on('change', () => {
                    $questionEl.find('.question-title-input').val($questionEl.find('.gap-test-text').val());
                });

            $questionEl.find('.question-title-input').hide();
            $questionEl.find('.question-mode-input-label').hide();
            $questionEl.find('.gap-test-mode').show();
            $questionEl.find('.btn-add-variant').hide();
            $questionEl.find('.gap-test-text-container').show();
            $questionEl.find('.question-points-wrapper-simple').hide();

            const gapTestModeOnChange = () => {
                if ($questionEl.find('.gap-test-mode-text').prop('checked')) {
                    $questionEl.find('.gap-test-mode-text-case-sensitive-label').show();
                    $questionEl.find('.variant-list').hide();
                    $questionEl.find('.gap-test-btn-add-wrong-variant').hide();
                } else {
                    $questionEl.find('.gap-test-mode-text-case-sensitive-label').hide();
                    $questionEl.find('.variant-list').show();
                    $questionEl.find('.gap-test-btn-add-wrong-variant').show();
                }
            }

            $questionEl.find('input[name="' + gapTestModeRadioName +  '"]').on('change', gapTestModeOnChange);
            gapTestModeOnChange();

            const gapTestPointsModeOnChange = () => {
                if ($questionEl.find('.gap-test-points-mode-question').prop('checked')) {
                    $questionEl.find('.gap-test-points-mode-question-input').prop('disabled', false);
                    $questionEl.find('.gap-test-points-mode-gap-input').prop('disabled', true);
                } else {
                    $questionEl.find('.gap-test-points-mode-question-input').prop('disabled', true);
                    $questionEl.find('.gap-test-points-mode-gap-input').prop('disabled', false);
                }
            }

            $questionEl.find('.gap-test-points-mode-question').prop('checked', question.params.gap_test_points_mode === 'question');
            $questionEl.find('.gap-test-points-mode-gap').prop('checked', question.params.gap_test_points_mode === 'gap');
            if (question.params.gap_test_points_mode === 'gap') {
                $questionEl.find('.btn-set-points').click();
            }

            $questionEl.find('input[name="' + gapTestPointsRadioName +  '"]').on('change', gapTestPointsModeOnChange);
            gapTestPointsModeOnChange();

            const gapTestAddWrongVariantBtn = $questionEl.find('.gap-test-btn-add-wrong-variant');
            gapTestAddWrongVariantBtn.click(() => {
                const variant = {id: null, value: '', points: null, is_right: false, params: {right_text: null, error_text: null}};
                const $variantEl = self.addVariantToQuestion($questionEl, variant);
                $variantEl.find('.variant-value').focus();
            });
        }

		return $questionEl;

	},
    addQuestionToListTrueFalse: function(question) {
        var self = this;

        let strings = {
            question: 'Question',
            deleteQuestion: 'Delete question',
            questionNumber: 'Question number',
            questionDescription: 'question text (optionally)',
            questionVideo: 'Видео вопроса',
            changeQuestionVideo: 'Изменить',
            uploadQuestionVideo: 'Загрузить',
            uploadMaxSize: 'Макс. размер 6 ГБ',
            deleteQuestionVideo: 'Удалить',
            questionPicture: 'Question picture',
            pointsForRightAnswer: 'Points for right answer',
            answerChoice: 'Answer choice',
            addAnswer: 'Add answer',
            textInCaseOfRightAnswer: 'Text in case of right answer',
            textInCaseOfError: 'Text in case of error',
            option: 'Option',
            addDescription: 'Description',
            answerMode: 'Ученик должен выбрать все правильные варианты ответа',
            requiredQuestion: 'Обязательный вопрос',
            failVideoSelect: 'Видео в процессе транскодирования',
        };
        strings = self.translateStrings(strings);

        var questionVideoInputId = 'questionVideoInput' + Math.floor(Math.random() * 10000) + Date.now();
        const questionElId = Math.floor(Math.random() * 10000) + Date.now();

        const template = `
<div class="question questionary-list-item js__questionary-list-item" id="${questionElId}">
	<input type="hidden" class="question-type" />
	<div class="toggle-expand-link collapsed-data">
		<span class="fa fa-caret-right"></span>
		<span class="question-title"></span>
	</div>
	<div class="expanded-data">
		<button type="button" class="btn btn-sm btn-link btn-delete-question pull-right">${strings.deleteQuestion}</button>
		<div class="form-group">
			<div>
				<label class="toggle-expand-link">
					<span class="fa fa-caret-down"/> ${strings.question}
				</label>
				<div class="question-number">
					${strings.questionNumber}: <input class="form-control text-center question-order-input" style="width: 50px; display: inline-block">
				</div>
				<input class="form-control question-title-input" placeholder="${strings.question}"/>
			</div>
			<label class="question-required-label">
				<input type="checkbox" class="question-required"/> ${strings.requiredQuestion}
			</label>
			<a target="_blank" href="/pl/help-proxy?url=/help/obligatoryquestion">
				<span class="glyphicon glyphicon-question-sign" style="color: #999; margin: 0 2px;">
			</a>
			<br>
			<textarea class="form-control question-description-input" rows=3 placeholder="${strings.questionDescription}"/>
			<div class="question-video-wrapper">
				${strings.questionVideo}
				<br/>
				<input type="hidden" class="question-video-input" id="${questionVideoInputId}">
				<div>
					<div class="question-video-preview"></div>
					<a href="javascript:void(0)" class="question-video-input-changer dotted-link">
						${strings.changeQuestionVideo}
					</a>
					<div class="question-upload-wrapper" style="display: none;">
						<a href="javascript:void(0)" class="question-video-input-upload">
							${strings.uploadQuestionVideo}
						</a>
						<p class="text-muted">
							${strings.uploadMaxSize}
						</p>
					</div>
					<a href="javascript:void(0)" class="question-video-input-delete dotted-link" style="display: none;">
						${strings.deleteQuestionVideo}
					</a>
				</div>
			</div>
			<div class="question-picture-wrapper">
				${strings.questionPicture}
				<br/>
				<input type="hidden" class="question-image-input">
			</div>
			<div class="question-points-wrapper">
				<div class="question-points-wrapper-simple">
					${strings.pointsForRightAnswer}: <input placeholder="1" class="text-center form-control question-points-input" style="width: 50px; display: inline-block">
				</div>
			</div>
		</div>
		<div class="buttons questionary-buttons">
			<button type="button" class="btn btn-sm btn-link btn-add-description">
				${strings.addDescription}
			</button>
			<div class="btn-free-space"></div>
			<button type="button" class="btn btn-sm btn-link btn-set-points">
				<span class="button-label">
				<span class="question-points-html"/>
					${window.tt('common', 'балл')}
				</span>
			</button>
			<button type="button" class="btn btn-sm btn-link btn-set-image question-btn-set-image">
				<span class="button-label">
					${window.tt('common', 'Картинка')}
				</span>
			</button>
			<button type="button" class="btn btn-sm btn-link question-btn-set-video">
				<span class="button-label">
					${window.tt('common', 'Видео')}
				</span>
			</button>
		</div>
		<div class="variant-list"></div>
		<div class="answer-text-params">
			<div class="form-group" style="margin-top: 5px">
				<label class="text-in-case-of-right-answer">
					${strings.textInCaseOfRightAnswer}
				</label>
				<textarea class="form-control question-answer-right-input" placeholder=""/>
			</div>
			<div class="form-group">
				<label class="text-in-case-of-error">
					${strings.textInCaseOfError}
				</label>
				<textarea class="form-control question-answer-error-input" placeholder=""/>
			</div>
		</div>
	</div>
</div>`;

        var $questionEl = $(template);
        $questionEl.appendTo( this.questionListEl );

        if ( ! this.options.questionary.isUseAnswerText ) {
            $questionEl.find('.answer-text-params').hide();
        }

        $questionEl.find('.btn-add-description').click( function() {
            $questionEl.find('.question-description-input').show();
            $questionEl.find('.question-description-input').focus();
            $(this).hide();

        });

        $questionEl.find('.btn-set-points').click( function() {
            $questionEl.find('.question-points-wrapper').show();
            $(this).hide();

        });

        $questionEl.find('.btn-set-image').click( function() {
            $questionEl.find('.question-picture-wrapper').show();
            $questionEl.find('.question-video-wrapper').hide();
            if ($questionEl.find('.question-image-input').val() === '') {
                $questionEl.find('.question-btn-set-video').show();
            }
            $(this).hide();

        });
        $questionEl.find('.question-video-input-changer').click(function () {
            $(this).hide();
            $questionEl.find('.question-upload-wrapper').show();
        });
        $questionEl.find('.question-video-input-upload').click(function () {
            window.gcSelectFiles({
                selectedHash: $questionEl.find('.question-video-input').val(),
                type: 'video',
                accept: '.mkv,.mov,.mp4,.avi',
                isShowHint: true,
                callback: function (hash) {
                    self.setQuestionVideo($questionEl, hash);
                },
            });
        });
        $questionEl.find('.question-video-input-delete').click(function () {
            self.setQuestionVideo($questionEl, '');
            $questionEl.find('.question-video-preview').text('');
            $questionEl.find('.question-video-wrapper').show();
            $questionEl.find('.question-upload-wrapper').show();
            $questionEl.find('.question-video-input-changer').hide();
            $questionEl.find('.question-btn-set-video').hide();
            $(this).hide();
        })

        $questionEl.find('.question-btn-set-video').click(function () {
            $questionEl.find('.question-video-wrapper').show();
            $questionEl.find('.question-picture-wrapper').hide();
            $questionEl.find('.question-btn-set-video').hide();
            $questionEl.find('.question-btn-set-image').show();
            $(this).hide();
        });

        var noName = 'Question';
        if (typeof Yii != 'undefined') {
            noName = Yii.t('common', noName);
        }

        $questionEl.find( '.question-title-input' ).val( question.title );

        $questionEl.find('.question-type').val(question.params.type);

        $questionEl.find('.question-required').prop( 'checked',  question.params.required_question);
        $questionEl.find( '.question-title' ).html( question.title ? question.title : noName );
        $questionEl.find( '.question-answer-right-input' ).val( question.params.right_text );
        $questionEl.find( '.question-answer-error-input' ).val( question.params.error_text );

        $questionEl.find( '.question-description-input' ).val( question.description );
        if( question.description && question.description != "<p></p>" ) {
            $questionEl.find('.btn-add-description').click();
        }

        this.initRedactor( $questionEl.find( '.question-description-input' ), true );
        $questionEl.find( '.question-points-input' ).val( question.params.right_points );

        var points = 1;
        if ( question.params.right_points &&  question.params.right_points.trim() != "" ) {
            points = question.params.right_points;
            $questionEl.find('.btn-set-points').click();
        }
        if ( question.params.image &&  question.params.image.trim() != "" ) {
            $questionEl.find('.btn-set-image').click();
        }
        $questionEl.find( '.question-points-html' ).html(points)

        $questionEl.find( '.question-title-input' ).change( function() {
            var val = $(this).val();
            $questionEl.find( '.question-title' ).html( val.length > 0 ? val : noName );
        });

        self.initQuestionaryListItem( $questionEl );

        $questionEl.data('question', question);
        $questionEl.data( 'id', question.id );
        $questionEl.find(".question-image-input").val( question.params.image );
        $questionEl.find(".question-image-input").trigger('change');
        $questionEl.find(".question-image-input").fileWidget({showButtonOnStart:true});
        $questionEl.find('.question-order-input').val( this.questionListEl.find( '.question' ).length );

        $questionEl.find(".question-video-input").on('change', function() {
            if ($(this).val() !== '') {
                $
                    .get('/pl/teach/questionary/questionary-video?hash=' + $(this).val())
                    .done(function (response) {
                        $questionEl.find('.question-video-preview').html('<div class="questions-video-player">' + response + '</div>');
                        var questionModal = $questionEl.parents('.modal');
                        if (questionModal && questionModal.length > 0) {
                            // фикс для скролла
                            questionModal.modal('hide');
                            questionModal.modal('show');
                        }
                    })
                    .fail(function () {
                        $questionEl.find('.question-video-preview').html(strings.failVideoSelect);
                    })
                ;
                $questionEl.find('.question-image-input').val('');
                $questionEl.find('.question-image-input').trigger('change');
                $questionEl.find('.question-video-wrapper').show();
                $questionEl.find('.question-picture-wrapper').hide();
                $questionEl.find('.question-picture-wrapper').find('.question-image-input').next().find('div').first().text('');
                $questionEl.find('.question-picture-wrapper').find('.uploadifive-queue-item.complete').hide();
                $questionEl.find('.question-btn-set-image').hide();
                $questionEl.find('.question-btn-set-video').hide();
                $questionEl.find('.question-video-input-delete').show();
                $questionEl.find('.question-upload-wrapper').hide();
                $questionEl.find('.question-video-input-changer').show();
            } else {
                $questionEl.find('.question-video-wrapper').hide();
                $questionEl.find('.question-btn-set-image').show();
                $questionEl.find('.question-btn-set-video').show();
                if ($questionEl.find('.question-image-input').val() !== '') {
                    $questionEl.find('.question-btn-set-image').hide();
                    $questionEl.find('.question-btn-set-video').hide();
                }
            }
        });
        this.setQuestionVideo($questionEl, question.params.video);
        $questionEl.find('.question-image-input').on('change', function () {
            if ($(this).val() !== '') {
                self.setQuestionVideo($questionEl, '');
            }
            $questionEl.find('.question-video-input-delete').hide();
            $questionEl.find('.question-video-preview').text('');
            $questionEl.find('.question-btn-set-video').hide();
            $questionEl.find('.question-btn-set-image').hide();
            if ($(this).val() === '') {
                $questionEl.find('.question-btn-set-video').show();
            }
        });

        if ( question.variants ) {
            for (var i = 0; i < question.variants.length; i++ ) {
                var variant = question.variants[i];
                self.addVariantToQuestionTrueFalse( $questionEl, variant )
            }
        }
        $questionEl.find('.variant-list').sortable({
            handle: '.variant-sort-handler'

        });

        $questionEl.find( '.btn-delete-question' ).click( function() {
            $questionEl.remove();
            self.globalElementsControl();
        });

        return $questionEl;
    },
    addQuestionToListSelectOne: function(question) {
        var self = this;

        let strings = {
            question: 'Question',
            deleteQuestion: 'Delete question',
            questionNumber: 'Question number',
            questionDescription: 'question text (optionally)',
            questionVideo: 'Видео вопроса',
            changeQuestionVideo: 'Изменить',
            uploadQuestionVideo: 'Загрузить',
            uploadMaxSize: 'Макс. размер 6 ГБ',
            deleteQuestionVideo: 'Удалить',
            questionPicture: 'Question picture',
            pointsForRightAnswer: 'Points for right answer',
            answerChoice: 'Answer choice',
            addAnswer: 'Add answer',
            textInCaseOfRightAnswer: 'Text in case of right answer',
            textInCaseOfError: 'Text in case of error',
            option: 'Option',
            addDescription: 'Description',
            answerMode: 'Ученик должен выбрать все правильные варианты ответа',
            requiredQuestion: 'Обязательный вопрос',
            failVideoSelect: 'Видео в процессе транскодирования',
        };
        strings = self.translateStrings(strings);

        var questionVideoInputId = 'questionVideoInput' + Math.floor(Math.random() * 10000) + Date.now();
        const questionElId = Math.floor(Math.random() * 10000) + Date.now();

        const template = `
<div class="question questionary-list-item js__questionary-list-item" id="${questionElId}">
	<input type="hidden" class="question-type" />
	<div class="toggle-expand-link collapsed-data">
		<span class="fa fa-caret-right"></span>
		<span class="question-title"></span>
	</div>
	<div class="expanded-data">
		<button type="button" class="btn btn-sm btn-link btn-delete-question pull-right">${strings.deleteQuestion}</button>
		<div class="form-group">
			<div>
				<label class="toggle-expand-link">
					<span class="fa fa-caret-down"/> ${strings.question}
				</label>
				<div class="question-number">
					${strings.questionNumber}: <input class="form-control text-center question-order-input" style="width: 50px; display: inline-block">
				</div>
				<input class="form-control question-title-input" placeholder="${strings.question}"/>
			</div>
			<label class="question-required-label">
				<input type="checkbox" class="question-required"/> ${strings.requiredQuestion}
			</label>
			<a target="_blank" href="/pl/help-proxy?url=/help/obligatoryquestion">
				<span class="glyphicon glyphicon-question-sign" style="color: #999; margin: 0 2px;">
			</a>
			<br>
			<textarea class="form-control question-description-input" rows=3 placeholder="${strings.questionDescription}"/>
			<div class="question-video-wrapper">
				${strings.questionVideo}
				<br/>
				<input type="hidden" class="question-video-input" id="${questionVideoInputId}">
				<div>
					<div class="question-video-preview"></div>
					<a href="javascript:void(0)" class="question-video-input-changer dotted-link">
						${strings.changeQuestionVideo}
					</a>
					<div class="question-upload-wrapper" style="display: none;">
						<a href="javascript:void(0)" class="question-video-input-upload">
							${strings.uploadQuestionVideo}
						</a>
						<p class="text-muted">
							${strings.uploadMaxSize}
						</p>
					</div>
					<a href="javascript:void(0)" class="question-video-input-delete dotted-link" style="display: none;">
						${strings.deleteQuestionVideo}
					</a>
				</div>
			</div>
			<div class="question-picture-wrapper">
				${strings.questionPicture}
				<br/>
				<input type="hidden" class="question-image-input">
			</div>
			<div class="question-points-wrapper">
				<div class="question-points-wrapper-simple">
					${strings.pointsForRightAnswer}: <input placeholder="1" class="text-center form-control question-points-input" style="width: 50px; display: inline-block">
				</div>
			</div>
		</div>
		<div class="buttons questionary-buttons">
			<button type="button" class="btn btn-sm btn-link btn-add-variant">${strings.addAnswer}</button>
			<button type="button" class="btn btn-sm btn-link btn-add-description">
				${strings.addDescription}
			</button>
			<div class="btn-free-space"></div>
			<button type="button" class="btn btn-sm btn-link btn-set-points">
				<span class="button-label">
				<span class="question-points-html"/>
					${window.tt('common', 'балл')}
				</span>
			</button>
			<button type="button" class="btn btn-sm btn-link btn-set-image question-btn-set-image">
				<span class="button-label">
					${window.tt('common', 'Картинка')}
				</span>
			</button>
			<button type="button" class="btn btn-sm btn-link question-btn-set-video">
				<span class="button-label">
					${window.tt('common', 'Видео')}
				</span>
			</button>
		</div>
		<div class="variant-list"></div>
		<div class="answer-text-params">
			<div class="form-group" style="margin-top: 5px">
				<label class="text-in-case-of-right-answer">
					${strings.textInCaseOfRightAnswer}
				</label>
				<textarea class="form-control question-answer-right-input" placeholder=""/>
			</div>
			<div class="form-group">
				<label class="text-in-case-of-error">
					${strings.textInCaseOfError}
				</label>
				<textarea class="form-control question-answer-error-input" placeholder=""/>
			</div>
		</div>
	</div>
</div>`;

        var $questionEl = $(template);
        $questionEl.appendTo( this.questionListEl );

        if ( ! this.options.questionary.isUseAnswerText ) {
            $questionEl.find('.answer-text-params').hide();
        }

        $questionEl.find('.btn-add-variant').click( function() {
            let variant = {id: null, value: '', points: null, is_right: false, params: {right_text: null, error_text: null}};
            var $variantEl = self.addVariantToQuestionSelectOne($questionEl, variant);
            $variantEl.find('.variant-value').focus();
        });

        $questionEl.find('.btn-add-description').click( function() {
            $questionEl.find('.question-description-input').show();
            $questionEl.find('.question-description-input').focus();
            $(this).hide();

        });

        $questionEl.find('.btn-set-points').click( function() {
            $questionEl.find('.question-points-wrapper').show();
            $(this).hide();

        });

        $questionEl.find('.btn-set-image').click( function() {
            $questionEl.find('.question-picture-wrapper').show();
            $questionEl.find('.question-video-wrapper').hide();
            if ($questionEl.find('.question-image-input').val() === '') {
                $questionEl.find('.question-btn-set-video').show();
            }
            $(this).hide();

        });
        $questionEl.find('.question-video-input-changer').click(function () {
            $(this).hide();
            $questionEl.find('.question-upload-wrapper').show();
        });
        $questionEl.find('.question-video-input-upload').click(function () {
            window.gcSelectFiles({
                selectedHash: $questionEl.find('.question-video-input').val(),
                type: 'video',
                accept: '.mkv,.mov,.mp4,.avi',
                isShowHint: true,
                callback: function (hash) {
                    self.setQuestionVideo($questionEl, hash);
                },
            });
        });
        $questionEl.find('.question-video-input-delete').click(function () {
            self.setQuestionVideo($questionEl, '');
            $questionEl.find('.question-video-preview').text('');
            $questionEl.find('.question-video-wrapper').show();
            $questionEl.find('.question-upload-wrapper').show();
            $questionEl.find('.question-video-input-changer').hide();
            $questionEl.find('.question-btn-set-video').hide();
            $(this).hide();
        })

        $questionEl.find('.question-btn-set-video').click(function () {
            $questionEl.find('.question-video-wrapper').show();
            $questionEl.find('.question-picture-wrapper').hide();
            $questionEl.find('.question-btn-set-video').hide();
            $questionEl.find('.question-btn-set-image').show();
            $(this).hide();
        });

        var noName = 'Question';
        if (typeof Yii != 'undefined') {
            noName = Yii.t('common', noName);
        }

        $questionEl.find( '.question-title-input' ).val( question.title );

        $questionEl.find('.question-type').val(question.params.type);

        $questionEl.find('.question-required').prop( 'checked',  question.params.required_question);
        $questionEl.find( '.question-title' ).html( question.title ? question.title : noName );
        $questionEl.find( '.question-answer-right-input' ).val( question.params.right_text );
        $questionEl.find( '.question-answer-error-input' ).val( question.params.error_text );

        $questionEl.find( '.question-description-input' ).val( question.description );
        if( question.description && question.description != "<p></p>" ) {
            $questionEl.find('.btn-add-description').click();
        }

        this.initRedactor( $questionEl.find( '.question-description-input' ), true );
        $questionEl.find( '.question-points-input' ).val( question.params.right_points );

        var points = 1;
        if ( question.params.right_points &&  question.params.right_points.trim() != "" ) {
            points = question.params.right_points;
            $questionEl.find('.btn-set-points').click();
        }
        if ( question.params.image &&  question.params.image.trim() != "" ) {
            $questionEl.find('.btn-set-image').click();
        }
        $questionEl.find( '.question-points-html' ).html(points)

        $questionEl.find( '.question-title-input' ).change( function() {
            var val = $(this).val();
            $questionEl.find( '.question-title' ).html( val.length > 0 ? val : noName );
        });

        self.initQuestionaryListItem( $questionEl );

        $questionEl.data('question', question);
        $questionEl.data( 'id', question.id );
        $questionEl.find(".question-image-input").val( question.params.image );
        $questionEl.find(".question-image-input").trigger('change');
        $questionEl.find(".question-image-input").fileWidget({showButtonOnStart:true});
        $questionEl.find('.question-order-input').val( this.questionListEl.find( '.question' ).length );

        $questionEl.find(".question-video-input").on('change', function() {
            if ($(this).val() !== '') {
                $
                    .get('/pl/teach/questionary/questionary-video?hash=' + $(this).val())
                    .done(function (response) {
                        $questionEl.find('.question-video-preview').html('<div class="questions-video-player">' + response + '</div>');
                        var questionModal = $questionEl.parents('.modal');
                        if (questionModal && questionModal.length > 0) {
                            // фикс для скролла
                            questionModal.modal('hide');
                            questionModal.modal('show');
                        }
                    })
                    .fail(function () {
                        $questionEl.find('.question-video-preview').html(strings.failVideoSelect);
                    })
                ;
                $questionEl.find('.question-image-input').val('');
                $questionEl.find('.question-image-input').trigger('change');
                $questionEl.find('.question-video-wrapper').show();
                $questionEl.find('.question-picture-wrapper').hide();
                $questionEl.find('.question-picture-wrapper').find('.question-image-input').next().find('div').first().text('');
                $questionEl.find('.question-picture-wrapper').find('.uploadifive-queue-item.complete').hide();
                $questionEl.find('.question-btn-set-image').hide();
                $questionEl.find('.question-btn-set-video').hide();
                $questionEl.find('.question-video-input-delete').show();
                $questionEl.find('.question-upload-wrapper').hide();
                $questionEl.find('.question-video-input-changer').show();
            } else {
                $questionEl.find('.question-video-wrapper').hide();
                $questionEl.find('.question-btn-set-image').show();
                $questionEl.find('.question-btn-set-video').show();
                if ($questionEl.find('.question-image-input').val() !== '') {
                    $questionEl.find('.question-btn-set-image').hide();
                    $questionEl.find('.question-btn-set-video').hide();
                }
            }
        });
        this.setQuestionVideo($questionEl, question.params.video);
        $questionEl.find('.question-image-input').on('change', function () {
            if ($(this).val() !== '') {
                self.setQuestionVideo($questionEl, '');
            }
            $questionEl.find('.question-video-input-delete').hide();
            $questionEl.find('.question-video-preview').text('');
            $questionEl.find('.question-btn-set-video').hide();
            $questionEl.find('.question-btn-set-image').hide();
            if ($(this).val() === '') {
                $questionEl.find('.question-btn-set-video').show();
            }
        });

        if ( question.variants ) {
            for (var i = 0; i < question.variants.length; i++ ) {
                var variant = question.variants[i];
                self.addVariantToQuestionSelectOne( $questionEl, variant )
            }
        }
        $questionEl.find('.variant-list').sortable({
            handle: '.variant-sort-handler'

        });

        $questionEl.find( '.btn-delete-question' ).click( function() {
            $questionEl.remove();
            self.globalElementsControl();
        });

        return $questionEl;
    },
    addQuestionToListCombination: function(question) {
        var self = this;

        let strings = {
            question: 'Question',
            deleteQuestion: 'Delete question',
            questionNumber: 'Question number',
            questionDescription: 'question text (optionally)',
            questionVideo: 'Видео вопроса',
            changeQuestionVideo: 'Изменить',
            uploadQuestionVideo: 'Загрузить',
            uploadMaxSize: 'Макс. размер 6 ГБ',
            deleteQuestionVideo: 'Удалить',
            questionPicture: 'Question picture',
            pointsForRightAnswer: 'Points for right answer',
            answerChoice: 'Answer choice',
            addAnswer: 'Add answer',
            textInCaseOfRightAnswer: 'Text in case of right answer',
            textInCaseOfError: 'Text in case of error',
            option: 'Option',
            addDescription: 'Description',
            answerMode: 'Ученик должен выбрать все правильные варианты ответа',
            requiredQuestion: 'Обязательный вопрос',
            failVideoSelect: 'Видео в процессе транскодирования',
            testPointsForRightAnswer: 'Баллов за правильный ответ на вопрос',
            testPointsForRightCombination: 'Баллов за каждую правильно выбранную пару',
        };
        strings = self.translateStrings(strings);


        const questionVideoInputId = 'questionVideoInput' + Math.floor(Math.random() * 10000) + Date.now();
        const questionElId = Math.floor(Math.random() * 10000) + Date.now();
        const combinationTestPointsRadioName = Math.random().toString(36).substring(2, 10);

        const template = `
<div class="question questionary-list-item js__questionary-list-item" id="${questionElId}">
	<input type="hidden" class="question-type" />
	<div class="toggle-expand-link collapsed-data">
		<span class="fa fa-caret-right"></span>
		<span class="question-title"></span>
	</div>
	<div class="expanded-data">
	    <input type="hidden" class="combination-data">
		<button type="button" class="btn btn-sm btn-link btn-delete-question pull-right">${strings.deleteQuestion}</button>
		<div class="form-group">
			<div>
				<label class="toggle-expand-link">
					<span class="fa fa-caret-down"/> ${strings.question}
				</label>
				<div class="question-number">
					${strings.questionNumber}: <input class="form-control text-center question-order-input" style="width: 50px; display: inline-block">
				</div>
				<div class="question-combination-input" style="position: relative;">
                    <input class="form-control question-title-input" placeholder="${strings.question}"/>
                    <span class="variant-settings-link fa fa-cog gap-test-text-setting-btn" style="right: 5px"></span>
			    </div>
			</div>
			<label class="question-required-label">
				<input type="checkbox" class="question-required"/> ${strings.requiredQuestion}
			</label>
			<a target="_blank" href="/pl/help-proxy?url=/help/obligatoryquestion">
				<span class="glyphicon glyphicon-question-sign" style="color: #999; margin: 0 2px;">
			</a>
			<br>
			<textarea class="form-control question-description-input" rows=3 placeholder="${strings.questionDescription}"/>
			<div class="question-video-wrapper">
				${strings.questionVideo}
				<br/>
				<input type="hidden" class="question-video-input" id="${questionVideoInputId}">
				<div>
					<div class="question-video-preview"></div>
					<a href="javascript:void(0)" class="question-video-input-changer dotted-link">
						${strings.changeQuestionVideo}
					</a>
					<div class="question-upload-wrapper" style="display: none;">
						<a href="javascript:void(0)" class="question-video-input-upload">
							${strings.uploadQuestionVideo}
						</a>
						<p class="text-muted">
							${strings.uploadMaxSize}
						</p>
					</div>
					<a href="javascript:void(0)" class="question-video-input-delete dotted-link" style="display: none;">
						${strings.deleteQuestionVideo}
					</a>
				</div>
			</div>
			<div class="question-picture-wrapper">
				${strings.questionPicture}
				<br/>
				<input type="hidden" class="question-image-input">
			</div>
			<div class="question-points-wrapper">
				<div class="question-points-wrapper-simple">
                <div class="question-points-wrapper-combination">
                <label>
                <input type="radio" name="${combinationTestPointsRadioName}" class="combination-test-points-mode-question"/>
                ${strings.testPointsForRightAnswer}
                : <input placeholder="1" class="text-center form-control combination-test-points-mode-question-input" style="width: 50px; display: inline-block">
                </label>
                <br/>
                <label>
                <input type="radio" name="${combinationTestPointsRadioName}" class="combination-test-points-mode-combination"/>
                ${strings.testPointsForRightCombination}
                : <input placeholder="1" class="text-center form-control combination-test-points-mode-combination-input" style="width: 50px; display: inline-block">
                </label>
                </div>
                </div>
			</div>
		</div>
		<div class="buttons questionary-buttons">
			<button type="button" class="btn btn-sm btn-link btn-add-variant">${strings.addAnswer}</button>
			<button type="button" class="btn btn-sm btn-link btn-add-description">
				${strings.addDescription}
			</button>
			<div class="btn-free-space"></div>
			<button type="button" class="btn btn-sm btn-link btn-set-points">
				<span class="button-label">
				<span class="question-points-html"/>
					${window.tt('common', 'балл')}
				</span>
			</button>
			<button type="button" class="btn btn-sm btn-link btn-set-image question-btn-set-image">
				<span class="button-label">
					${window.tt('common', 'Картинка')}
				</span>
			</button>
			<button type="button" class="btn btn-sm btn-link question-btn-set-video">
				<span class="button-label">
					${window.tt('common', 'Видео')}
				</span>
			</button>
		</div>
		<div class="answer-text-params">
			<div class="form-group" style="margin-top: 5px">
				<label class="text-in-case-of-right-answer">
					${strings.textInCaseOfRightAnswer}
				</label>
				<textarea class="form-control question-answer-right-input" placeholder=""/>
			</div>
			<div class="form-group">
				<label class="text-in-case-of-error">
					${strings.textInCaseOfError}
				</label>
				<textarea class="form-control question-answer-error-input" placeholder=""/>
			</div>
		</div>
		<div class="variant-list"></div>
	</div>
</div>`;

        var $questionEl = $(template);
        $questionEl.appendTo( this.questionListEl );

        if ( ! this.options.questionary.isUseAnswerText ) {
            $questionEl.find('.answer-text-params').hide();
        }

        $questionEl.find('.btn-add-variant').click( function() {
            let variant = {id: null, value: '', points: null, is_right: false, params: {right_text: null, error_text: null}};
            var $variantEl = self.addVariantToQuestionCombination($questionEl, variant);
            $variantEl.find('.variant-value').focus();
        });

        $questionEl.find('.btn-add-description').click( function() {
            $questionEl.find('.question-description-input').show();
            $questionEl.find('.question-description-input').focus();
            $(this).hide();

        });

        $questionEl.find('.btn-set-points').click( function() {
            $questionEl.find('.question-points-wrapper').show();
            $(this).hide();
        });
        const combinationTestPointsModeOnChange = () => {
            if ($questionEl.find('.combination-test-points-mode-question').prop('checked')) {
                $questionEl.find('.combination-test-points-mode-question-input').prop('disabled', false);
                $questionEl.find('.combination-test-points-mode-combination-input').prop('disabled', true);
            } else {
                $questionEl.find('.combination-test-points-mode-question-input').prop('disabled', true);
                $questionEl.find('.combination-test-points-mode-combination-input').prop('disabled', false);
            }
        }
        $questionEl.find('.combination-test-points-mode-question').prop('checked', question.params.gap_test_points_mode === 'question');
        $questionEl.find('.combination-test-points-mode-combination').prop('checked', question.params.gap_test_points_mode === 'gap');

        $questionEl.find('input[name="' + combinationTestPointsRadioName +  '"]').on('change', combinationTestPointsModeOnChange);
        combinationTestPointsModeOnChange();

        $questionEl.find('.combination-test-points-mode-question-input').val(question.params.right_points);
        $questionEl.find('.combination-test-points-mode-combination-input').val(question.params.gap_points);

        $questionEl.find('.btn-set-image').click( function() {
            $questionEl.find('.question-picture-wrapper').show();
            $questionEl.find('.question-video-wrapper').hide();
            if ($questionEl.find('.question-image-input').val() === '') {
                $questionEl.find('.question-btn-set-video').show();
            }
            $(this).hide();

        });
        $questionEl.find('.question-video-input-changer').click(function () {
            $(this).hide();
            $questionEl.find('.question-upload-wrapper').show();
        });
        $questionEl.find('.question-video-input-upload').click(function () {
            window.gcSelectFiles({
                selectedHash: $questionEl.find('.question-video-input').val(),
                type: 'video',
                accept: '.mkv,.mov,.mp4,.avi',
                isShowHint: true,
                callback: function (hash) {
                    self.setQuestionVideo($questionEl, hash);
                },
            });
        });
        $questionEl.find('.question-video-input-delete').click(function () {
            self.setQuestionVideo($questionEl, '');
            $questionEl.find('.question-video-preview').text('');
            $questionEl.find('.question-video-wrapper').show();
            $questionEl.find('.question-upload-wrapper').show();
            $questionEl.find('.question-video-input-changer').hide();
            $questionEl.find('.question-btn-set-video').hide();
            $(this).hide();
        })

        $questionEl.find('.question-btn-set-video').click(function () {
            $questionEl.find('.question-video-wrapper').show();
            $questionEl.find('.question-picture-wrapper').hide();
            $questionEl.find('.question-btn-set-video').hide();
            $questionEl.find('.question-btn-set-image').show();
            $(this).hide();
        });

        var noName = 'Question';
        if (typeof Yii != 'undefined') {
            noName = Yii.t('common', noName);
        }

        $questionEl.find( '.question-title-input' ).val( question.title );

        $questionEl.find('.question-type').val(question.params.type);

        $questionEl.find('.question-required').prop( 'checked',  question.params.required_question);
        $questionEl.find( '.question-title' ).html( question.title ? question.title : noName );
        $questionEl.find( '.question-answer-right-input' ).val( question.params.right_text );
        $questionEl.find( '.question-answer-error-input' ).val( question.params.error_text );

        $questionEl.find( '.question-description-input' ).val( question.description );
        if( question.description && question.description != "<p></p>" ) {
            $questionEl.find('.btn-add-description').click();
        }

        this.initRedactor( $questionEl.find( '.question-description-input' ), true );
        $questionEl.find( '.question-points-input' ).val( question.params.right_points );

        var points = 1;
        if ( question.params.right_points &&  question.params.right_points.trim() != "" ) {
            points = question.params.right_points;
            $questionEl.find('.btn-set-points').click();
        }
        if ( question.params.image &&  question.params.image.trim() != "" ) {
            $questionEl.find('.btn-set-image').click();
        }
        $questionEl.find( '.question-points-html' ).html(points)

        $questionEl.find( '.question-title-input' ).change( function() {
            var val = $(this).val();
            $questionEl.find( '.question-title' ).html( val.length > 0 ? val : noName );
        });

        self.initQuestionaryListItem( $questionEl );

        $questionEl.data('question', question);
        $questionEl.data( 'id', question.id );
        $questionEl.find(".question-image-input").val( question.params.image );
        $questionEl.find(".question-image-input").trigger('change');
        $questionEl.find(".question-image-input").fileWidget({showButtonOnStart:true});
        $questionEl.find('.question-order-input').val( this.questionListEl.find( '.question' ).length );

        $questionEl.find(".question-video-input").on('change', function() {
            if ($(this).val() !== '') {
                $
                    .get('/pl/teach/questionary/questionary-video?hash=' + $(this).val())
                    .done(function (response) {
                        $questionEl.find('.question-video-preview').html('<div class="questions-video-player">' + response + '</div>');
                        var questionModal = $questionEl.parents('.modal');
                        if (questionModal && questionModal.length > 0) {
                            // фикс для скролла
                            questionModal.modal('hide');
                            questionModal.modal('show');
                        }
                    })
                    .fail(function () {
                        $questionEl.find('.question-video-preview').html(strings.failVideoSelect);
                    })
                ;
                $questionEl.find('.question-image-input').val('');
                $questionEl.find('.question-image-input').trigger('change');
                $questionEl.find('.question-video-wrapper').show();
                $questionEl.find('.question-picture-wrapper').hide();
                $questionEl.find('.question-picture-wrapper').find('.question-image-input').next().find('div').first().text('');
                $questionEl.find('.question-picture-wrapper').find('.uploadifive-queue-item.complete').hide();
                $questionEl.find('.question-btn-set-image').hide();
                $questionEl.find('.question-btn-set-video').hide();
                $questionEl.find('.question-video-input-delete').show();
                $questionEl.find('.question-upload-wrapper').hide();
                $questionEl.find('.question-video-input-changer').show();
            } else {
                $questionEl.find('.question-video-wrapper').hide();
                $questionEl.find('.question-btn-set-image').show();
                $questionEl.find('.question-btn-set-video').show();
                if ($questionEl.find('.question-image-input').val() !== '') {
                    $questionEl.find('.question-btn-set-image').hide();
                    $questionEl.find('.question-btn-set-video').hide();
                }
            }
        });
        this.setQuestionVideo($questionEl, question.params.video);
        $questionEl.find('.question-image-input').on('change', function () {
            if ($(this).val() !== '') {
                self.setQuestionVideo($questionEl, '');
            }
            $questionEl.find('.question-video-input-delete').hide();
            $questionEl.find('.question-video-preview').text('');
            $questionEl.find('.question-btn-set-video').hide();
            $questionEl.find('.question-btn-set-image').hide();
            if ($(this).val() === '') {
                $questionEl.find('.question-btn-set-video').show();
            }
        });

        if ( question.variants ) {
            for (var i = 0; i < question.variants.length; i++ ) {
                var variant = question.variants[i];
                self.addVariantToQuestionCombination( $questionEl, variant )
            }
        }
        $questionEl.find('.variant-list').sortable({
            handle: '.variant-sort-handler'

        });

        $questionEl.find( '.btn-delete-question' ).click( function() {
            $questionEl.remove();
            self.globalElementsControl();
        });
        $questionEl.find('.gap-test-text-setting-btn').click(() => {
            $questionEl.find('.answer-text-params').toggle(0);
        });


        return $questionEl;
    },
    setQuestionVideo: function($el, $video_hash) {
        $el.find(".question-video-input").val($video_hash).trigger('change');
    },
    setVariantVideo: function($el, $video_hash) {
        $el.find('.variant-video-input').val($video_hash).trigger('change');
    },
    initQuestionaryListItem: function( $el ) {
        var self = this;

        $el.find('.toggle-expand-link').click( function(e) {
            if ( self.disableClickEvent ) {
                self.disableClickEvent = false;
                return;
            }

            if ( ! $el.hasClass('expanded' )) {
                $('.questionary-list-item.expanded').removeClass('expanded')

            }

            $el.toggleClass( "expanded" );
            if ( $el.hasClass('expanded') ) {
                $el.find('.question-title-input').focus()
            }
            self.afterQuestionExpand();
        });

    },
    addVariantToQuestionLight: function( $questionEl, variant ) {
        var self = this;

        let strings = {
            noteIfYouChooseThisAnswerOption: 'Notice if you choose this answer option',
            noteIfThisOptionIsCorrectButYouChooseAnother: 'Notice if this option is correct but you choose another',
            points: 'points',
            variantPicture: 'Variant picture',
            variantVideo: 'Видео ответа',
            changeVariantVideo: 'Изменить',
            uploadVariantVideo: 'Загрузить',
            uploadMaxSize: 'Макс. размер 6 ГБ',
            deleteVariantVideo: 'Удалить',
            failVideoSelect: 'Видео в процессе транскодирования',
        };
        strings = self.translateStrings(strings);


        /*var hiddenInputs = '<input class="variant-points" type="hidden">' +
            '<input class="variant-answer-right-input" type="hidden">' +
            '<input class="variant-answer-error-input" type="hidden">';*/

        var additionalFields = $('<div class="additional-field"/>');

        $( '<div>'
            + '<label>' + strings.noteIfYouChooseThisAnswerOption + '</label>'
            + '<textarea class="form-control variant-answer-right-input" placeholder=""></textarea>'
            + '</div>').appendTo( additionalFields );

        //$( '<div><label>' + strings.noteIfThisOptionIsCorrectButYouChooseAnother + '</label>' +
        //	'<textarea class="form-control variant-answer-error-input" placeholder=""></textarea>' + ' </div>').appendTo( additionalFields );

        $('<input class="variant-answer-error-input" type="hidden">').appendTo( additionalFields );

        $(
            '<div>'
            + window.tt(
                'common',
                'за этот ответ дается {n} баллов',
                {n: '<input class="variant-points" type="text" size="3">'}
            )
            + '</div>'
        ).appendTo( additionalFields );


        var $variantEl = $('<div class="question-variant">'
            + '<input class="variant-is-right" type="checkbox" />'
            + '<textarea rows="1" placeholder="'+window.tt('common', 'Вариант ответа')
            + '" type="text" class="variant-value" />'
            + '<span class="variant-sort-handler fa fa-arrows"></span>'
            + '<span class="variant-settings-link fa fa-cog"></span>'
            + '<span class="btn-delete variant-delete-link fa fa-trash"></span>'
            + '<div class="variant-video-wrapper">' + strings.variantVideo
            + '<br/><input type="hidden" class="variant-video-input">'
            + '<div class="variant-video-preview"></div>'
            + '<a href="javascript:void(0)" class="variant-video-input-changer dotted-link">'
            + strings.changeVariantVideo
            + '</a>'
            + '<div class="variant-upload-wrapper" style="display: none;">'
            + '<a href="javascript:void(0)" class="variant-video-input-upload">'
            + strings.uploadVariantVideo
            + '</a>'
            + '<p class="text-muted">' + strings.uploadMaxSize + '</p>'
            + '</div>'
            + '<a href="javascript:void(0)" class="variant-video-input-delete dotted-link" style="display: none;">'
            + strings.deleteVariantVideo
            + '</a>'
            + '</div>'
            + '<div class="variant-picture-wrapper">' + strings.variantPicture
            + '<br/><input type="hidden" class="variant-image-input">'
            + '</div>'
            + '<button type="button" class="btn btn-sm btn-link btn-set-image variant-btn-set-image">  '
            + '<span class="button-label">' + window.tt('common', 'Картинка') + '</span>'
            + '</button>'
            + '<button type="button" class="btn btn-sm btn-link variant-btn-set-video">  '
            + '<span class="button-label">' + window.tt('common', 'Видео') + '</span>'
            + '</button>'
            + '</div>'
        );
        additionalFields.appendTo( $variantEl );

        var splittedVariantValue = variant.value.split('image_')[0];
        splittedVariantValue = splittedVariantValue.split('video_')[0];
        $variantEl.find('.variant-value').val( splittedVariantValue );
        $variantEl.find('.variant-is-right').prop( 'checked', variant.is_right )
        $variantEl.find('.variant-points').prop( 'disabled', !variant.is_right );
        $variantEl.find('.variant-settings-link').click( function() {
            additionalFields.toggle(300);

        });
        $variantEl.find(".variant-image-input").val( variant.params.image );
        $variantEl.find(".variant-image-input").trigger('change');
        $variantEl.find(".variant-image-input").fileWidget({showButtonOnStart:true});
        $variantEl.find(".variant-video-input").on('change', function () {
            if ($(this).val() !== '') {
                $
                    .get('/pl/teach/questionary/questionary-video?hash=' + $(this).val())
                    .done(function (response) {
                        $variantEl.find('.variant-video-preview').html('<div class="questions-video-player">' + response + '</div>');
                        var questionModal = $variantEl.parents('.modal');
                        if (questionModal && questionModal.length > 0) {
                            // фикс для скролла
                            questionModal.modal('hide');
                            questionModal.modal('show');
                        }
                    })
                    .fail(function () {
                        $variantEl.find('variant-video-preview').html(strings.failVideoSelect);
                    })
                ;
                $variantEl.find('.variant-image-input').val('');
                $variantEl.find('.variant-image-input').trigger('change');
                $variantEl.find('.variant-video-wrapper').show();
                $variantEl.find('.variant-picture-wrapper').hide();
                $variantEl.find('.variant-picture-wrapper').find('.variant-image-input').next().find('div').first().text('');
                $variantEl.find('.variant-picture-wrapper').find('.uploadifive-queue-item.complete').hide();
                $variantEl.find('.variant-btn-set-image').hide();
                $variantEl.find('.variant-btn-set-video').hide();
                $variantEl.find('.variant-video-input-delete').show();
                $variantEl.find('.variant-upload-wrapper').hide();
                $variantEl.find('.variant-video-input-changer').show();
            } else {
                $variantEl.find('.variant-video-wrapper').hide();
                $variantEl.find('.variant-btn-set-image').show();
                $variantEl.find('.variant-btn-set-video').show();
                if ($variantEl.find('.variant-image-input').val() !== '') {
                    $variantEl.find('.variant-btn-set-image').hide();
                    $variantEl.find('.variant-btn-set-video').hide();
                }
            }
        });
        $variantEl.find('.variant-image-input').on('change', function () {
            if ($(this).val() !== '') {
                self.setVariantVideo($variantEl, '');
            }
            $variantEl.find('.variant-video-input-delete').hide();
            $variantEl.find('.variant-video-preview').text('');
            $variantEl.find('.variant-btn-set-video').hide();
            $variantEl.find('.variant-btn-set-image').hide();
            if ($(this).val() === '') {
                $variantEl.find('.variant-btn-set-video').show();
            }
        });
        this.setVariantVideo($variantEl, variant.params.video);

        $variantEl.find('.btn-set-image').click( function() {
            $variantEl.find('.variant-picture-wrapper').show();
            $variantEl.find('.variant-video-wrapper').hide();
            if ($variantEl.find('.variant-image-input').val() === '') {
                $variantEl.find('.variant-btn-set-video').show();
            }
            $(this).hide();
        });
        $variantEl.find('.variant-btn-set-video').click( function() {
            $variantEl.find('.variant-video-wrapper').show();
            $variantEl.find('.variant-picture-wrapper').hide();
            $variantEl.find('.variant-btn-set-image').show();
            $(this).hide();
        });
        $variantEl.find('.variant-video-input-changer').click(function () {
            $(this).hide();
            $variantEl.find('.variant-upload-wrapper').show();
        });

        $variantEl.find('.variant-video-input-upload').click(function () {
            window.gcSelectFiles({
                selectedHash: $variantEl.find('.variant-video-input').val(),
                type: 'video',
                accept: '.mkv,.mov,.mp4,.avi',
                isShowHint: true,
                callback: function (hash) {
                    self.setVariantVideo($variantEl, hash);
                },
            });
        });

        $variantEl.find('.variant-video-input-delete').click(function () {
            self.setVariantVideo($variantEl, '');
            $variantEl.find('.variant-video-preview').text('');
            $variantEl.find('.variant-video-wrapper').show();
            $variantEl.find('.variant-upload-wrapper').show();
            $variantEl.find('.variant-video-input-changer').hide();
            $variantEl.find('.variant-btn-set-video').hide();
            $(this).hide();
        });

        if (variant.params.image && variant.params.image.trim() !== '') {
            $variantEl.find('.btn-set-image').click();
        }

        var changeVariantsIsRight = function() {
            var variantIsRight = $variantEl.find('.variant-is-right').prop('checked');
            if (variantIsRight) {
                $variantEl.addClass('is-right');
            }
            else {
                $variantEl.removeClass('is-right');
            }
            $variantEl.find('.variant-points').prop('disabled', !variantIsRight);
        };

        $variantEl.find('.variant-is-right').change(changeVariantsIsRight);

        changeVariantsIsRight();
        return $variantEl;

    },
	setQuestionVideo: function($el, $video_hash) {
		$el.find(".question-video-input").val($video_hash).trigger('change');
	},
	setVariantVideo: function($el, $video_hash) {
		$el.find('.variant-video-input').val($video_hash).trigger('change');
	},
	initQuestionaryListItem: function( $el ) {
		var self = this;

		$el.find('.toggle-expand-link').click( function(e) {
			if ( self.disableClickEvent ) {
				self.disableClickEvent = false;
				return;
			}

			if ( ! $el.hasClass('expanded' )) {
				$('.questionary-list-item.expanded').removeClass('expanded')

			}

			$el.toggleClass( "expanded" );
			if ( $el.hasClass('expanded') ) {
				$el.find('.question-title-input').focus()
			}
			self.afterQuestionExpand();
		});

	},
	addVariantToQuestionLight: function( $questionEl, variant ) {
		var self = this;

		let strings = {
			noteIfYouChooseThisAnswerOption: 'Notice if you choose this answer option',
			noteIfThisOptionIsCorrectButYouChooseAnother: 'Notice if this option is correct but you choose another',
			points: 'points',
			variantPicture: 'Variant picture',
			variantVideo: 'Видео ответа',
			changeVariantVideo: 'Изменить',
			uploadVariantVideo: 'Загрузить',
			uploadMaxSize: 'Макс. размер 6 ГБ',
			deleteVariantVideo: 'Удалить',
			failVideoSelect: 'Видео в процессе транскодирования',
		};
		strings = self.translateStrings(strings);


		/*var hiddenInputs = '<input class="variant-points" type="hidden">' +
			'<input class="variant-answer-right-input" type="hidden">' +
			'<input class="variant-answer-error-input" type="hidden">';*/

		var additionalFields = $('<div class="additional-field"/>');

		$( '<div>'
			+ '<label>' + strings.noteIfYouChooseThisAnswerOption + '</label>'
			+ '<textarea class="form-control variant-answer-right-input" placeholder=""></textarea>'
			+ '</div>').appendTo( additionalFields );

		//$( '<div><label>' + strings.noteIfThisOptionIsCorrectButYouChooseAnother + '</label>' +
		//	'<textarea class="form-control variant-answer-error-input" placeholder=""></textarea>' + ' </div>').appendTo( additionalFields );

		$('<input class="variant-answer-error-input" type="hidden">').appendTo( additionalFields );

		$(
			'<div>'
				+ window.tt(
					'common',
					'за этот ответ дается {n} баллов',
					{n: '<input class="variant-points" type="text" size="3">'}
				)
			+ '</div>'
		).appendTo( additionalFields );


		var $variantEl = $('<div class="question-variant">'
			+ '<input class="variant-is-right" type="checkbox" />'
			+ '<textarea rows="1" placeholder="'+window.tt('common', 'Вариант ответа')
			+ '" type="text" class="variant-value" />'
			+ '<span class="variant-sort-handler fa fa-arrows"></span>'
			+ '<span class="variant-settings-link fa fa-cog"></span>'
			+ '<span class="btn-delete variant-delete-link fa fa-trash"></span>'
			+ '<div class="variant-video-wrapper">' + strings.variantVideo
			+ '<br/><input type="hidden" class="variant-video-input">'
			+ '<div class="variant-video-preview"></div>'
			+ '<a href="javascript:void(0)" class="variant-video-input-changer dotted-link">'
			+ strings.changeVariantVideo
			+ '</a>'
			+ '<div class="variant-upload-wrapper" style="display: none;">'
			+ '<a href="javascript:void(0)" class="variant-video-input-upload">'
			+ strings.uploadVariantVideo
			+ '</a>'
			+ '<p class="text-muted">' + strings.uploadMaxSize + '</p>'
			+ '</div>'
			+ '<a href="javascript:void(0)" class="variant-video-input-delete dotted-link" style="display: none;">'
			+ strings.deleteVariantVideo
			+ '</a>'
			+ '</div>'
			+ '<div class="variant-picture-wrapper">' + strings.variantPicture
			+ '<br/><input type="hidden" class="variant-image-input">'
			+ '</div>'
			+ '<button type="button" class="btn btn-sm btn-link btn-set-image variant-btn-set-image">  '
			+ '<span class="button-label">' + window.tt('common', 'Картинка') + '</span>'
			+ '</button>'
			+ '<button type="button" class="btn btn-sm btn-link variant-btn-set-video">  '
			+ '<span class="button-label">' + window.tt('common', 'Видео') + '</span>'
			+ '</button>'
			+ '</div>'
		);
		additionalFields.appendTo( $variantEl );

		var splittedVariantValue = variant.value.split('image_')[0];
		splittedVariantValue = splittedVariantValue.split('video_')[0];
		$variantEl.find('.variant-value').val( splittedVariantValue );
		$variantEl.find('.variant-is-right').prop( 'checked', variant.is_right )
		$variantEl.find('.variant-points').prop( 'disabled', !variant.is_right );
		$variantEl.find('.variant-settings-link').click( function() {
			additionalFields.toggle(300);

		});
		$variantEl.find(".variant-image-input").val( variant.params.image );
		$variantEl.find(".variant-image-input").trigger('change');
		$variantEl.find(".variant-image-input").fileWidget({showButtonOnStart:true});
		$variantEl.find(".variant-video-input").on('change', function () {
			if ($(this).val() !== '') {
				$
					.get('/pl/teach/questionary/questionary-video?hash=' + $(this).val())
					.done(function (response) {
						$variantEl.find('.variant-video-preview').html('<div class="questions-video-player">' + response + '</div>');
						var questionModal = $variantEl.parents('.modal');
						if (questionModal && questionModal.length > 0) {
							// фикс для скролла
							questionModal.modal('hide');
							questionModal.modal('show');
						}
					})
					.fail(function () {
						$variantEl.find('variant-video-preview').html(strings.failVideoSelect);
					})
				;
				$variantEl.find('.variant-image-input').val('');
				$variantEl.find('.variant-image-input').trigger('change');
				$variantEl.find('.variant-video-wrapper').show();
				$variantEl.find('.variant-picture-wrapper').hide();
				$variantEl.find('.variant-picture-wrapper').find('.variant-image-input').next().find('div').first().text('');
				$variantEl.find('.variant-picture-wrapper').find('.uploadifive-queue-item.complete').hide();
				$variantEl.find('.variant-btn-set-image').hide();
				$variantEl.find('.variant-btn-set-video').hide();
				$variantEl.find('.variant-video-input-delete').show();
				$variantEl.find('.variant-upload-wrapper').hide();
				$variantEl.find('.variant-video-input-changer').show();
			} else {
				$variantEl.find('.variant-video-wrapper').hide();
				$variantEl.find('.variant-btn-set-image').show();
				$variantEl.find('.variant-btn-set-video').show();
				if ($variantEl.find('.variant-image-input').val() !== '') {
					$variantEl.find('.variant-btn-set-image').hide();
					$variantEl.find('.variant-btn-set-video').hide();
				}
			}
		});
		$variantEl.find('.variant-image-input').on('change', function () {
			if ($(this).val() !== '') {
				self.setVariantVideo($variantEl, '');
			}
			$variantEl.find('.variant-video-input-delete').hide();
			$variantEl.find('.variant-video-preview').text('');
			$variantEl.find('.variant-btn-set-video').hide();
			$variantEl.find('.variant-btn-set-image').hide();
			if ($(this).val() === '') {
				$variantEl.find('.variant-btn-set-video').show();
			}
		});
		this.setVariantVideo($variantEl, variant.params.video);

		$variantEl.find('.btn-set-image').click( function() {
			$variantEl.find('.variant-picture-wrapper').show();
			$variantEl.find('.variant-video-wrapper').hide();
			if ($variantEl.find('.variant-image-input').val() === '') {
				$variantEl.find('.variant-btn-set-video').show();
			}
			$(this).hide();
		});
		$variantEl.find('.variant-btn-set-video').click( function() {
			$variantEl.find('.variant-video-wrapper').show();
			$variantEl.find('.variant-picture-wrapper').hide();
			$variantEl.find('.variant-btn-set-image').show();
			$(this).hide();
		});
		$variantEl.find('.variant-video-input-changer').click(function () {
			$(this).hide();
			$variantEl.find('.variant-upload-wrapper').show();
		});

		$variantEl.find('.variant-video-input-upload').click(function () {
			window.gcSelectFiles({
				selectedHash: $variantEl.find('.variant-video-input').val(),
				type: 'video',
				accept: '.mkv,.mov,.mp4,.avi',
				isShowHint: true,
				callback: function (hash) {
					self.setVariantVideo($variantEl, hash);
				},
			});
		});

		$variantEl.find('.variant-video-input-delete').click(function () {
			self.setVariantVideo($variantEl, '');
			$variantEl.find('.variant-video-preview').text('');
			$variantEl.find('.variant-video-wrapper').show();
			$variantEl.find('.variant-upload-wrapper').show();
			$variantEl.find('.variant-video-input-changer').hide();
			$variantEl.find('.variant-btn-set-video').hide();
			$(this).hide();
		});

		if (variant.params.image && variant.params.image.trim() !== '') {
			$variantEl.find('.btn-set-image').click();
		}

		var changeVariantsIsRight = function() {
			var variantIsRight = $variantEl.find('.variant-is-right').prop('checked');
			if (variantIsRight) {
				$variantEl.addClass('is-right');
			}
			else {
				$variantEl.removeClass('is-right');
			}
			$variantEl.find('.variant-points').prop('disabled', !variantIsRight);
		};

		$variantEl.find('.variant-is-right').change(changeVariantsIsRight);

		changeVariantsIsRight();
		return $variantEl;

	},
    addVariantToQuestionTrueFalse: function($questionEl, variant) {
        var self = this;

        let strings = {
            noteIfYouChooseThisAnswerOption: 'Notice if you choose this answer option',
            noteIfThisOptionIsCorrectButYouChooseAnother: 'Notice if this option is correct but you choose another',
            points: 'points',
            variantPicture: 'Variant picture',
            variantVideo: 'Видео ответа',
            changeVariantVideo: 'Изменить',
            uploadVariantVideo: 'Загрузить',
            uploadMaxSize: 'Макс. размер 6 ГБ',
            deleteVariantVideo: 'Удалить',
            failVideoSelect: 'Видео в процессе транскодирования',
        };
        strings = self.translateStrings(strings);

        const pointLabel = window.tt(
            'common',
            'за этот ответ дается {n} баллов',
            {n: '<input class="variant-points" type="text" size="3">'}
        );

        const radioName = 'radio' + $questionEl.prop('id');

        var $variantEl = $(`
<div class="question-variant">
	<input class="variant-is-right" type="radio" name="${radioName}" />
	<textarea rows="1" placeholder="${window.tt('common', 'Вариант ответа')}" type="text" class="variant-value" />
	<span class="variant-sort-handler fa fa-arrows" style="right: 25px"></span>
	<span class="variant-settings-link fa fa-cog" style="right: 5px"></span>
	<div class="variant-video-wrapper">
		${strings.variantVideo}
		<br/>
		<input type="hidden" class="variant-video-input">
		<div class="variant-video-preview"></div>
		<a href="javascript:void(0)" class="variant-video-input-changer dotted-link">
			${strings.changeVariantVideo}
		</a>
		<div class="variant-upload-wrapper" style="display: none;">
			<a href="javascript:void(0)" class="variant-video-input-upload">
				${strings.uploadVariantVideo}
			</a>
			<p class="text-muted">
				${strings.uploadMaxSize}
			</p>
		</div>
		<a href="javascript:void(0)" class="variant-video-input-delete dotted-link" style="display: none;">
			${strings.deleteVariantVideo}
		</a>
	</div>
	<div class="variant-picture-wrapper">
		${strings.variantPicture}
		<br/>
		<input type="hidden" class="variant-image-input">
	</div>
	<button type="button" class="btn btn-sm btn-link btn-set-image variant-btn-set-image">
		<span class="button-label">
			${window.tt('common', 'Картинка')}
		</span>
	</button>
	<button type="button" class="btn btn-sm btn-link variant-btn-set-video">
		<span class="button-label">
			${window.tt('common', 'Видео')}
		</span>
	</button>
	<div class="additional-field">
		<div>
			<label>${strings.noteIfYouChooseThisAnswerOption}</label>
			<textarea class="form-control variant-answer-right-input" placeholder=""></textarea>
		</div>
		<input class="variant-answer-error-input" type="hidden">
		<div>${pointLabel}</div>
	</div>
</div>`);

        var splittedVariantValue = variant.value.split('image_')[0];
        splittedVariantValue = splittedVariantValue.split('video_')[0];
        $variantEl.find('.variant-value').val( splittedVariantValue );
        $variantEl.find('.variant-is-right').prop( 'checked', variant.is_right )
        $variantEl.find('.variant-points').prop( 'disabled', !variant.is_right );
        $variantEl.find('.variant-settings-link').click( function() {
            $variantEl.find('.additional-field').toggle(300);

        });
        $variantEl.find(".variant-image-input").val( variant.params.image );
        $variantEl.find(".variant-image-input").trigger('change');
        $variantEl.find(".variant-image-input").fileWidget({showButtonOnStart:true});
        $variantEl.find(".variant-video-input").on('change', function () {
            if ($(this).val() !== '') {
                $
                    .get('/pl/teach/questionary/questionary-video?hash=' + $(this).val())
                    .done(function (response) {
                        $variantEl.find('.variant-video-preview').html('<div class="questions-video-player">' + response + '</div>');
                        var questionModal = $variantEl.parents('.modal');
                        if (questionModal && questionModal.length > 0) {
                            // фикс для скролла
                            questionModal.modal('hide');
                            questionModal.modal('show');
                        }
                    })
                    .fail(function () {
                        $variantEl.find('variant-video-preview').html(strings.failVideoSelect);
                    })
                ;
                $variantEl.find('.variant-image-input').val('');
                $variantEl.find('.variant-image-input').trigger('change');
                $variantEl.find('.variant-video-wrapper').show();
                $variantEl.find('.variant-picture-wrapper').hide();
                $variantEl.find('.variant-picture-wrapper').find('.variant-image-input').next().find('div').first().text('');
                $variantEl.find('.variant-picture-wrapper').find('.uploadifive-queue-item.complete').hide();
                $variantEl.find('.variant-btn-set-image').hide();
                $variantEl.find('.variant-btn-set-video').hide();
                $variantEl.find('.variant-video-input-delete').show();
                $variantEl.find('.variant-upload-wrapper').hide();
                $variantEl.find('.variant-video-input-changer').show();
            } else {
                $variantEl.find('.variant-video-wrapper').hide();
                $variantEl.find('.variant-btn-set-image').show();
                $variantEl.find('.variant-btn-set-video').show();
                if ($variantEl.find('.variant-image-input').val() !== '') {
                    $variantEl.find('.variant-btn-set-image').hide();
                    $variantEl.find('.variant-btn-set-video').hide();
                }
            }
        });
        $variantEl.find('.variant-image-input').on('change', function () {
            if ($(this).val() !== '') {
                self.setVariantVideo($variantEl, '');
            }
            $variantEl.find('.variant-video-input-delete').hide();
            $variantEl.find('.variant-video-preview').text('');
            $variantEl.find('.variant-btn-set-video').hide();
            $variantEl.find('.variant-btn-set-image').hide();
            if ($(this).val() === '') {
                $variantEl.find('.variant-btn-set-video').show();
            }
        });
        this.setVariantVideo($variantEl, variant.params.video);

        $variantEl.find('.btn-set-image').click( function() {
            $variantEl.find('.variant-picture-wrapper').show();
            $variantEl.find('.variant-video-wrapper').hide();
            if ($variantEl.find('.variant-image-input').val() === '') {
                $variantEl.find('.variant-btn-set-video').show();
            }
            $(this).hide();
        });
        $variantEl.find('.variant-btn-set-video').click( function() {
            $variantEl.find('.variant-video-wrapper').show();
            $variantEl.find('.variant-picture-wrapper').hide();
            $variantEl.find('.variant-btn-set-image').show();
            $(this).hide();
        });
        $variantEl.find('.variant-video-input-changer').click(function () {
            $(this).hide();
            $variantEl.find('.variant-upload-wrapper').show();
        });

        $variantEl.find('.variant-video-input-upload').click(function () {
            window.gcSelectFiles({
                selectedHash: $variantEl.find('.variant-video-input').val(),
                type: 'video',
                accept: '.mkv,.mov,.mp4,.avi',
                isShowHint: true,
                callback: function (hash) {
                    self.setVariantVideo($variantEl, hash);
                },
            });
        });

        $variantEl.find('.variant-video-input-delete').click(function () {
            self.setVariantVideo($variantEl, '');
            $variantEl.find('.variant-video-preview').text('');
            $variantEl.find('.variant-video-wrapper').show();
            $variantEl.find('.variant-upload-wrapper').show();
            $variantEl.find('.variant-video-input-changer').hide();
            $variantEl.find('.variant-btn-set-video').hide();
            $(this).hide();
        });

        if (variant.params.image && variant.params.image.trim() !== '') {
            $variantEl.find('.btn-set-image').click();
        }

        $variantEl.appendTo( $questionEl.find('.variant-list') );

        const changeVariantsIsRight = function() {
            $questionEl.find('.question-variant').each(function () {
                const variantEl = $(this);
                const variantIsRight = variantEl.find('.variant-is-right').prop('checked');
                if (variantIsRight) {
                    variantEl.addClass('is-right');
                }
                else {
                    variantEl.removeClass('is-right');
                }
                variantEl.find('.variant-points').prop('disabled', !variantIsRight);
            });
        };

        $variantEl.find('.variant-is-right').change(changeVariantsIsRight);

        changeVariantsIsRight();

        var _variantValue = variant.value.split('image_')[0];
        _variantValue = _variantValue.split('video_')[0];
        this.initRedactor( $variantEl.find('.variant-value').val(_variantValue), false );
        this.initRedactor( $variantEl.find('.variant-answer-right-input').val( variant.params.right_text ) );
        this.initRedactor( $variantEl.find('.variant-answer-error-input').val( variant.params.error_text ) );
        $variantEl.find('.variant-points').val( variant.points );

        $variantEl.data( 'id', variant.id );

        $variantEl.data( 'variants', $variantEl );
        return $variantEl;
    },
    addVariantToQuestionSelectOne: function($questionEl, variant) {
        var self = this;

        let strings = {
            noteIfYouChooseThisAnswerOption: 'Notice if you choose this answer option',
            noteIfThisOptionIsCorrectButYouChooseAnother: 'Notice if this option is correct but you choose another',
            points: 'points',
            variantPicture: 'Variant picture',
            variantVideo: 'Видео ответа',
            changeVariantVideo: 'Изменить',
            uploadVariantVideo: 'Загрузить',
            uploadMaxSize: 'Макс. размер 6 ГБ',
            deleteVariantVideo: 'Удалить',
            failVideoSelect: 'Видео в процессе транскодирования',
        };
        strings = self.translateStrings(strings);

        const pointLabel = window.tt(
            'common',
            'за этот ответ дается {n} баллов',
            {n: '<input class="variant-points" type="text" size="3">'}
        );

        const radioName = 'radio' + $questionEl.prop('id');
        var $variantEl = $(`
<div class="question-variant">
	<input class="variant-is-right" type="radio" name="${radioName}" />
	<textarea rows="1" placeholder="${window.tt('common', 'Вариант ответа')}" type="text" class="variant-value" />
	<span class="variant-sort-handler fa fa-arrows"></span>
	<span class="variant-settings-link fa fa-cog"></span>
	<span class="btn-delete variant-delete-link fa fa-trash"></span>
	<div class="variant-video-wrapper">
		${strings.variantVideo}
		<br/>
		<input type="hidden" class="variant-video-input">
		<div class="variant-video-preview"></div>
		<a href="javascript:void(0)" class="variant-video-input-changer dotted-link">
			${strings.changeVariantVideo}
		</a>
		<div class="variant-upload-wrapper" style="display: none;">
			<a href="javascript:void(0)" class="variant-video-input-upload">
				${strings.uploadVariantVideo}
			</a>
			<p class="text-muted">
				${strings.uploadMaxSize}
			</p>
		</div>
		<a href="javascript:void(0)" class="variant-video-input-delete dotted-link" style="display: none;">
			${strings.deleteVariantVideo}
		</a>
	</div>
	<div class="variant-picture-wrapper">
		${strings.variantPicture}
		<br/>
		<input type="hidden" class="variant-image-input">
	</div>
	<button type="button" class="btn btn-sm btn-link btn-set-image variant-btn-set-image">
		<span class="button-label">
			${window.tt('common', 'Картинка')}
		</span>
	</button>
	<button type="button" class="btn btn-sm btn-link variant-btn-set-video">
		<span class="button-label">
			${window.tt('common', 'Видео')}
		</span>
	</button>
	<div class="additional-field">
		<div>
			<label>${strings.noteIfYouChooseThisAnswerOption}</label>
			<textarea class="form-control variant-answer-right-input" placeholder=""></textarea>
		</div>
		<input class="variant-answer-error-input" type="hidden">
		<div>${pointLabel}</div>
	</div>
</div>`);
        var splittedVariantValue = variant.value.split('image_')[0];
        splittedVariantValue = splittedVariantValue.split('video_')[0];
        $variantEl.find('.variant-value').val( splittedVariantValue );
        $variantEl.find('.variant-is-right').prop( 'checked', variant.is_right )
        $variantEl.find('.variant-points').prop( 'disabled', !variant.is_right );
        $variantEl.find('.variant-settings-link').click( function() {
            $variantEl.find('.additional-field').toggle(300);

        });
        $variantEl.find(".variant-image-input").val( variant.params.image );
        $variantEl.find(".variant-image-input").trigger('change');
        $variantEl.find(".variant-image-input").fileWidget({showButtonOnStart:true});
        $variantEl.find(".variant-video-input").on('change', function () {
            if ($(this).val() !== '') {
                $
                    .get('/pl/teach/questionary/questionary-video?hash=' + $(this).val())
                    .done(function (response) {
                        $variantEl.find('.variant-video-preview').html('<div class="questions-video-player">' + response + '</div>');
                        var questionModal = $variantEl.parents('.modal');
                        if (questionModal && questionModal.length > 0) {
                            // фикс для скролла
                            questionModal.modal('hide');
                            questionModal.modal('show');
                        }
                    })
                    .fail(function () {
                        $variantEl.find('variant-video-preview').html(strings.failVideoSelect);
                    })
                ;
                $variantEl.find('.variant-image-input').val('');
                $variantEl.find('.variant-image-input').trigger('change');
                $variantEl.find('.variant-video-wrapper').show();
                $variantEl.find('.variant-picture-wrapper').hide();
                $variantEl.find('.variant-picture-wrapper').find('.variant-image-input').next().find('div').first().text('');
                $variantEl.find('.variant-picture-wrapper').find('.uploadifive-queue-item.complete').hide();
                $variantEl.find('.variant-btn-set-image').hide();
                $variantEl.find('.variant-btn-set-video').hide();
                $variantEl.find('.variant-video-input-delete').show();
                $variantEl.find('.variant-upload-wrapper').hide();
                $variantEl.find('.variant-video-input-changer').show();
            } else {
                $variantEl.find('.variant-video-wrapper').hide();
                $variantEl.find('.variant-btn-set-image').show();
                $variantEl.find('.variant-btn-set-video').show();
                if ($variantEl.find('.variant-image-input').val() !== '') {
                    $variantEl.find('.variant-btn-set-image').hide();
                    $variantEl.find('.variant-btn-set-video').hide();
                }
            }
        });
        $variantEl.find('.variant-image-input').on('change', function () {
            if ($(this).val() !== '') {
                self.setVariantVideo($variantEl, '');
            }
            $variantEl.find('.variant-video-input-delete').hide();
            $variantEl.find('.variant-video-preview').text('');
            $variantEl.find('.variant-btn-set-video').hide();
            $variantEl.find('.variant-btn-set-image').hide();
            if ($(this).val() === '') {
                $variantEl.find('.variant-btn-set-video').show();
            }
        });
        this.setVariantVideo($variantEl, variant.params.video);

        $variantEl.find('.btn-set-image').click( function() {
            $variantEl.find('.variant-picture-wrapper').show();
            $variantEl.find('.variant-video-wrapper').hide();
            if ($variantEl.find('.variant-image-input').val() === '') {
                $variantEl.find('.variant-btn-set-video').show();
            }
            $(this).hide();
        });
        $variantEl.find('.variant-btn-set-video').click( function() {
            $variantEl.find('.variant-video-wrapper').show();
            $variantEl.find('.variant-picture-wrapper').hide();
            $variantEl.find('.variant-btn-set-image').show();
            $(this).hide();
        });
        $variantEl.find('.variant-video-input-changer').click(function () {
            $(this).hide();
            $variantEl.find('.variant-upload-wrapper').show();
        });

        $variantEl.find('.btn-delete').click( function() {
            if ( confirm( Yii.t( 'common', 'Are you sure?' ) ) ) {
                $variantEl.detach();
            }
        });

        $variantEl.find('.variant-video-input-upload').click(function () {
            window.gcSelectFiles({
                selectedHash: $variantEl.find('.variant-video-input').val(),
                type: 'video',
                accept: '.mkv,.mov,.mp4,.avi',
                isShowHint: true,
                callback: function (hash) {
                    self.setVariantVideo($variantEl, hash);
                },
            });
        });

        $variantEl.find('.variant-video-input-delete').click(function () {
            self.setVariantVideo($variantEl, '');
            $variantEl.find('.variant-video-preview').text('');
            $variantEl.find('.variant-video-wrapper').show();
            $variantEl.find('.variant-upload-wrapper').show();
            $variantEl.find('.variant-video-input-changer').hide();
            $variantEl.find('.variant-btn-set-video').hide();
            $(this).hide();
        });

        if (variant.params.image && variant.params.image.trim() !== '') {
            $variantEl.find('.btn-set-image').click();
        }

        $variantEl.appendTo( $questionEl.find('.variant-list') );

        const changeVariantsIsRight = function() {
            $questionEl.find('.question-variant').each(function () {
                const variantEl = $(this);
                const variantIsRight = variantEl.find('.variant-is-right').prop('checked');
                if (variantIsRight) {
                    variantEl.addClass('is-right');
                }
                else {
                    variantEl.removeClass('is-right');
                }
                variantEl.find('.variant-points').prop('disabled', !variantIsRight);
            });
        };

        $variantEl.find('.variant-is-right').change(changeVariantsIsRight);

        changeVariantsIsRight();

        var _variantValue = variant.value.split('image_')[0];
        _variantValue = _variantValue.split('video_')[0];
        this.initRedactor( $variantEl.find('.variant-value').val(_variantValue), false );
        this.initRedactor( $variantEl.find('.variant-answer-right-input').val( variant.params.right_text ) );
        this.initRedactor( $variantEl.find('.variant-answer-error-input').val( variant.params.error_text ) );
        $variantEl.find('.variant-points').val( variant.points );

        $variantEl.data( 'id', variant.id );

        $variantEl.data( 'variants', $variantEl );
        return $variantEl;
    },
    addVariantToQuestionCombination: function($questionEl, variant) {
        var self = this;

        let strings = {
            noteIfYouChooseThisAnswerOption: 'Notice if you choose this answer option',
            noteIfThisOptionIsCorrectButYouChooseAnother: 'Notice if this option is correct but you choose another',
            points: 'points',
            variantPicture: 'Variant picture',
            variantVideo: 'Видео ответа',
            changeVariantVideo: 'Изменить',
            uploadVariantVideo: 'Загрузить',
            uploadMaxSize: 'Макс. размер 6 ГБ',
            deleteVariantVideo: 'Удалить',
            failVideoSelect: 'Видео в процессе транскодирования',
        };
        strings = self.translateStrings(strings);

        const pointLabel = window.tt(
            'common',
            'за этот ответ дается {n} баллов',
            {n: '<input class="variant-points" type="text" size="3">'}
        );

        const leftName = 'left' + $questionEl.prop('id');
        const rightName = 'right' + $questionEl.prop('id');
        var $variantEl = $(`
<div class="question-variant-title">Пара <span>` + ($questionEl.find('.question-variant').length + 1) + `</span></div>
<div class="question-variant question-variant-combination">
	<input class="variant-value combination-left" type="text" name="${leftName}"/>
	<input class="variant-value combination-right" type="text" name="${rightName}"/>
	<span class="btn-delete variant-delete-link fa fa-trash"></span>
	<div class="additional-field">
		<div>
			<label>${strings.noteIfYouChooseThisAnswerOption}</label>
			<textarea class="form-control variant-answer-right-input" placeholder=""></textarea>
		</div>
		<input class="variant-answer-error-input" type="hidden">
		<div>${pointLabel}</div>
	</div>
</div>`);
        var splittedVariantValue = variant.value.split('image_')[0];
        splittedVariantValue = splittedVariantValue.split('video_')[0];
        combinationVariantValue = splittedVariantValue.split('|');
        $variantEl.find('.variant-value.combination-left').val(combinationVariantValue[0]);
        $variantEl.find('.variant-value.combination-right').val(combinationVariantValue[1]);
        $variantEl.find('.variant-is-right').prop( 'checked', variant.is_right )
        $variantEl.find('.variant-points').prop( 'disabled', !variant.is_right );
        $variantEl.find('.variant-settings-link').click( function() {
            $variantEl.find('.additional-field').toggle(300);

        });
        $variantEl.find(".variant-image-input").val( variant.params.image );
        $variantEl.find(".variant-image-input").trigger('change');
        $variantEl.find(".variant-image-input").fileWidget({showButtonOnStart:true});
        $variantEl.find(".variant-video-input").on('change', function () {
            if ($(this).val() !== '') {
                $
                    .get('/pl/teach/questionary/questionary-video?hash=' + $(this).val())
                    .done(function (response) {
                        $variantEl.find('.variant-video-preview').html('<div class="questions-video-player">' + response + '</div>');
                        var questionModal = $variantEl.parents('.modal');
                        if (questionModal && questionModal.length > 0) {
                            // фикс для скролла
                            questionModal.modal('hide');
                            questionModal.modal('show');
                        }
                    })
                    .fail(function () {
                        $variantEl.find('variant-video-preview').html(strings.failVideoSelect);
                    })
                ;
                $variantEl.find('.variant-image-input').val('');
                $variantEl.find('.variant-image-input').trigger('change');
                $variantEl.find('.variant-video-wrapper').show();
                $variantEl.find('.variant-picture-wrapper').hide();
                $variantEl.find('.variant-picture-wrapper').find('.variant-image-input').next().find('div').first().text('');
                $variantEl.find('.variant-picture-wrapper').find('.uploadifive-queue-item.complete').hide();
                $variantEl.find('.variant-btn-set-image').hide();
                $variantEl.find('.variant-btn-set-video').hide();
                $variantEl.find('.variant-video-input-delete').show();
                $variantEl.find('.variant-upload-wrapper').hide();
                $variantEl.find('.variant-video-input-changer').show();
            } else {
                $variantEl.find('.variant-video-wrapper').hide();
                $variantEl.find('.variant-btn-set-image').show();
                $variantEl.find('.variant-btn-set-video').show();
                if ($variantEl.find('.variant-image-input').val() !== '') {
                    $variantEl.find('.variant-btn-set-image').hide();
                    $variantEl.find('.variant-btn-set-video').hide();
                }
            }
        });
        $variantEl.find('.variant-image-input').on('change', function () {
            if ($(this).val() !== '') {
                self.setVariantVideo($variantEl, '');
            }
            $variantEl.find('.variant-video-input-delete').hide();
            $variantEl.find('.variant-video-preview').text('');
            $variantEl.find('.variant-btn-set-video').hide();
            $variantEl.find('.variant-btn-set-image').hide();
            if ($(this).val() === '') {
                $variantEl.find('.variant-btn-set-video').show();
            }
        });
        this.setVariantVideo($variantEl, variant.params.video);

        $variantEl.find('.btn-set-image').click( function() {
            $variantEl.find('.variant-picture-wrapper').show();
            $variantEl.find('.variant-video-wrapper').hide();
            if ($variantEl.find('.variant-image-input').val() === '') {
                $variantEl.find('.variant-btn-set-video').show();
            }
            $(this).hide();
        });
        $variantEl.find('.variant-btn-set-video').click( function() {
            $variantEl.find('.variant-video-wrapper').show();
            $variantEl.find('.variant-picture-wrapper').hide();
            $variantEl.find('.variant-btn-set-image').show();
            $(this).hide();
        });
        $variantEl.find('.variant-video-input-changer').click(function () {
            $(this).hide();
            $variantEl.find('.variant-upload-wrapper').show();
        });

        $variantEl.find('.btn-delete').click( function() {
            if ( confirm( Yii.t( 'common', 'Are you sure?' ) ) ) {
                $variantEl.detach();
                $('.question-variant-title').each(function (index, element) {
                    $(element).find('span').html(index+1);
                });
            }
        });

        $variantEl.find('.variant-video-input-upload').click(function () {
            window.gcSelectFiles({
                selectedHash: $variantEl.find('.variant-video-input').val(),
                type: 'video',
                accept: '.mkv,.mov,.mp4,.avi',
                isShowHint: true,
                callback: function (hash) {
                    self.setVariantVideo($variantEl, hash);
                },
            });
        });

        $variantEl.find('.variant-video-input-delete').click(function () {
            self.setVariantVideo($variantEl, '');
            $variantEl.find('.variant-video-preview').text('');
            $variantEl.find('.variant-video-wrapper').show();
            $variantEl.find('.variant-upload-wrapper').show();
            $variantEl.find('.variant-video-input-changer').hide();
            $variantEl.find('.variant-btn-set-video').hide();
            $(this).hide();
        });

        if (variant.params.image && variant.params.image.trim() !== '') {
            $variantEl.find('.btn-set-image').click();
        }

        $variantEl.appendTo( $questionEl.find('.variant-list') );

        this.initRedactor( $variantEl.find('.variant-answer-right-input').val( variant.params.right_text ) );
        this.initRedactor( $variantEl.find('.variant-answer-error-input').val( variant.params.error_text ) );
        $variantEl.find('.variant-points').val( variant.points );

        $variantEl.data( 'id', variant.id );

        $variantEl.data( 'variants', $variantEl );
        return $variantEl;
    },
	addVariantToQuestion: function( $questionEl, variant ) {
		var self = this;


		var $variantEl = null;
		if ( this.options.light ) {
			$variantEl = this.addVariantToQuestionLight( $questionEl, variant )
		}
		else {
			let strings = {
				noteIfYouChooseThisAnswerOption: 'Notice if you choose this answer option',
				noteIfThisOptionIsCorrectButYouChooseAnother: 'Notice if this option is correct but you choose another',
				points: 'points',
				variantPicture: 'Variant picture'
			};
			strings = self.translateStrings(strings);

			$variantEl = $(
				'<tr class="question-variant">' +
				'<td>' +
				'<textarea placeholder="'+window.tt('common', 'Вариант ответа')+'" rows=1 type="text" class="variant-value form-control"/>' +
				'<div class="additional-field"><label>' + strings.noteIfYouChooseThisAnswerOption + '</label>' +
				'<textarea class="form-control variant-answer-right-input" placeholder=""></textarea></div>' +
				'<div class="additional-field"><label>' + strings.noteIfThisOptionIsCorrectButYouChooseAnother + '</label>' +
				'<textarea class="form-control variant-answer-error-input" placeholder=""></textarea></div>' +
				'</td>' +
				'<td class="text-center">' +
				'<input class="variant-is-right" type="checkbox">' +
				'<div class="variant-points-wrapper additional-field">' +
				'<div class="variant-points-wrapper additional-field">' +
				'<input class="variant-points" type="text" size="3"> <br/> ' + strings.points +
				'</div>' +
				'</td>' +
				'<td class="text-center"><span class="btn btn-link btn-delete"><span class="fa fa-times"></span></span></td>' +
				'</tr>'
			);
			$variantEl.find('.variant-is-right').prop( 'checked',  variant.is_right );
		}

        if (this.isGapTest($questionEl)) {
            $variantEl.find('.variant-is-right').hide();
            $variantEl.find('.variant-sort-handler').hide();
            $variantEl.find('.variant-settings-link').hide();
            $variantEl.find('.variant-btn-set-image').hide();
            $variantEl.find('.variant-btn-set-video').hide();
            $variantEl.css('padding-left', '0');
            $variantEl.find('.variant-value').css('background', '#FFFFFF');
            $variantEl.find('.variant-value').css('border', '0');
        }

		$variantEl.appendTo( $questionEl.find('.variant-list') );
		var _variantValue = variant.value.split('image_')[0];
		_variantValue = _variantValue.split('video_')[0];
		this.initRedactor( $variantEl.find('.variant-value').val(_variantValue), false );
		this.initRedactor( $variantEl.find('.variant-answer-right-input').val( variant.params.right_text ) );
		this.initRedactor( $variantEl.find('.variant-answer-error-input').val( variant.params.error_text ) );
		$variantEl.find('.variant-points').val( variant.points );


		$variantEl.data( 'id', variant.id );

		$variantEl.find('.btn-delete').click( function() {
			if ( confirm( Yii.t( 'common', 'Are you sure?' ) ) ) {
				$variantEl.detach();
                if (self.isGapTest($questionEl)) {
                    self.updateUnnecessaryQuestionsLabel($questionEl);
                }
			}
		});

		$variantEl.data( 'variants', $variantEl );
        if (self.isGapTest($questionEl)) {
            this.updateUnnecessaryQuestionsLabel($questionEl);
        }
		return $variantEl;
	},

    updateUnnecessaryQuestionsLabel: function ($questionEl) {
        if ($questionEl.find('.variant-value').length === 0) {
            $questionEl.find('.gap-test-unnecessary-questions-label').hide();
        } else {
            $questionEl.find('.gap-test-unnecessary-questions-label').show();
        }
    },

	getValue: function() {
		var self = this;

		var result = {
			id: self.options.questionary.id,
			questions: [],
			deleted: self.deleted,
			defaultQuestionaryName: self.options.defaultQuestionaryName,
			ownerType: self.options.ownerType,
            tagsNames: this.element.closest('.modal-content').find('#addTagsEl').data('tags')
		};

		this.element.find('.question').each( function( index, el ) {
			var $el = $(el);

			var question = { };
			question.order = $el.find( '.question-order-input' ).val();
			question.title = $el.find('.question-title-input').val();
			question.description = $el.find('.question-description-input').val();
			question.order_pos = index;
			question.id = $el.data('id');
			question.params = {
				right_text: $el.find('.question-answer-right-input').val(),
				error_text: $el.find('.question-answer-error-input').val(),
				right_points: $el.find('.question-points-input').val(),
				image: $el.find('.question-image-input').val(),
				video: $el.find('.question-video-input').val()
			};

            if (window.newTestsFeature) {
                question.params.type = $el.find('.question-type').val();
            }
            if (question.params.type === 'true_false' || question.params.type === 'select_one') {
                question.params.right_if_all = false;
            } else {
                question.params.right_if_all= $el.find('.question-mode-input').prop('checked');
            }

            if (question.params.type === 'combination') {
                if ($el.find('.combination-test-points-mode-question').prop('checked')) {
                    question.params.gap_test_points_mode = 'question';
                } else {
                    question.params.gap_test_points_mode = 'gap';
                }
                question.params.gap_points = $el.find('.combination-test-points-mode-combination-input').val();
                question.params.right_points = $el.find('.combination-test-points-mode-question-input').val();
            }

			question.params.required_question = $el.find('.question-required').prop('checked');

            question.params.gap_test = $el.find('.gap-test').val() === '1';
            if (question.params.gap_test) {
                if ($el.find('.gap-test-mode-drag').prop('checked')) {
                    question.params.gap_test_mode = 'drag';
                } else {
                    question.params.gap_test_mode = 'text';
                }
                question.params.right_if_all = true;
                if ($el.find('.gap-test-points-mode-question').prop('checked')) {
                    question.params.gap_test_points_mode = 'question';
                } else {
                    question.params.gap_test_points_mode = 'gap';
                }
                question.params.gap_test_text = $el.find('.gap-test-text').val();
                question.params.gap_test_mode_text_case_sensitive = $el.find('.gap-test-mode-text-case-sensitive').prop('checked');
                question.params.gap_points = $el.find('.gap-test-points-mode-gap-input').val();
                question.params.right_points = $el.find('.gap-test-points-mode-question-input').val();
            }

			question.variants = [];

			var variants = [];
			$el.find('.question-variant').each( function( index, varEl ) {
				var variant = {};
				var $varEl = $(varEl);
                if (window.newTestsFeature && $varEl.is('.gap-test-text-container')) {
                    return;
                }
				variant.value = $varEl.find('.variant-value').val();
				variant.points = $varEl.find('.variant-points').val();
				variant.id = $varEl.data('id');
                var isRightChecked = $varEl.find('.variant-is-right').prop('checked');
                if (!isRightChecked && $varEl.hasClass('is-right')) {
                    $varEl.find('.variant-is-right').prop('checked', true);
                    isRightChecked = true;
                }
				variant.is_right = isRightChecked;
				variant.params = {
					right_text: $varEl.find('.variant-answer-right-input').val(),
					error_text: $varEl.find('.variant-answer-error-input').val(),
					image: $varEl.find('.variant-image-input').val(),
					video: $varEl.find('.variant-video-input').val()
				};
                if (question.params.type === 'combination') {
                    variant.value = $varEl.find('.variant-value.combination-left').val() + '|' + $varEl.find('.variant-value.combination-right').val();
                }

				question.variants.push( variant )
			});

			result.questions.push( question );
		});

		result.setParams = {};
		result.setParams.before_start_header = this.element.find('.questionary-title-input').val();
		result.setParams.before_start_text = this.element.find('.questionary-description-input').val();

		return result;
	},

    /**
     * @param {null|'multiple_choice'|'true_false'|'select_one'|'gap'} type
     */
	addQuestion: function(type = null) {
		let newQuestionStr = 'New question';
		if (typeof Yii != 'undefined') {
			newQuestionStr = Yii.t('common', newQuestionStr);
		}
		if ( this.options.light ) {
			newQuestionStr = "";
		}
		var question = {
			id: null,
			title: "",
			variants: [],
			params: {}
		};

		question.params = {
			right_if_all: true
		};

        if (window.newTestsFeature) {
            question.params.type = type;

            if (type === 'true_false') {
                question.variants.push({
                    id: null,
                    is_right: 1,
                    params: {
                        error_text: '',
                        image: '',
                        right_text: '',
                        video: '',
                    },
                    points: null,
                    value: '',
                });
                question.variants.push({
                    id: null,
                    is_right: 0,
                    params: {
                        error_text: '',
                        image: '',
                        right_text: '',
                        video: '',
                    },
                    points: null,
                    value: '',
                });
            }

            if (type === 'select_one') {
                question.variants.push({
                    id: null,
                    is_right: 1,
                    params: {
                        error_text: '',
                        image: '',
                        right_text: '',
                        video: '',
                    },
                    points: null,
                    value: '',
                });
                question.variants.push({
                    id: null,
                    is_right: 0,
                    params: {
                        error_text: '',
                        image: '',
                        right_text: '',
                        video: '',
                    },
                    points: null,
                    value: '',
                });
                question.variants.push({
                    id: null,
                    is_right: 0,
                    params: {
                        error_text: '',
                        image: '',
                        right_text: '',
                        video: '',
                    },
                    points: null,
                    value: '',
                });
            }

            if (type === 'gap') {
                question.params.gap_test = true;
                question.params.gap_test_mode = 'drag';
                question.params.gap_test_text = '';
                question.params.gap_test_mode_text_case_sensitive = false;
                question.params.gap_points = '';
                question.params.gap_test_points_mode = 'question';
            }
        }
        if (type === 'combination') {
            question.variants.push({
                id: null,
                is_right: 0,
                params: {
                    error_text: '',
                    image: '',
                    right_text: '',
                    video: '',
                },
                points: null,
                value: '',
            });
            question.variants.push({
                id: null,
                is_right: 0,
                params: {
                    error_text: '',
                    image: '',
                    right_text: '',
                    video: '',
                },
                points: null,
                value: '',
            });
            question.variants.push({
                id: null,
                is_right: 0,
                params: {
                    error_text: '',
                    image: '',
                    right_text: '',
                    video: '',
                },
                points: null,
                value: '',
            });
        }

		$(".questionary-list-item.expanded").removeClass('expanded')

		var $questionEl = this.addQuestionToList( question );
		$questionEl.addClass("expanded")
		$questionEl.find('.question-title-input').focus();
		this.afterQuestionExpand();
		this.selectControl();
	},
	afterQuestionExpand: function() {
		if ( $(".question.expanded").length > 0 ) {
			this.questionListEl.sortable('disable');
		}
		else {
			this.questionListEl.sortable('enable');
		}

	},
	changed: function() {
		//this.preSave();
	},
	preSave: function( onStart) {
		if( this.options.inputName ) {
			this.element.trigger('changed', onStart );
			this.valInput.val( JSON.stringify( this.getValue() ) )
		}
	},
	validate: function() {
		let formValue = this.getValue();
		let success = true;
		let message = '';
		let isYii = (typeof Yii != 'undefined');
		formValue.questions.forEach(function(question) {
			let questionNumber = '#'+question.order;
			if (question.title.length > ((question.params.type === 'gap' || question.params.gap_test) ? 1000 : 255)) {
				if (isYii) {
					message = Yii.t('common', 'Question title greater than 255 symbols: {n}', {n: questionNumber});
				}
				success = false;
			}
			if (success === false) {
				return;
			}
            if (window.newTestsFeature) {
                if (question.params.type === 'select_one') {
                    if (question.variants.length < 2) {
                        message = window.tt('common', 'Не заданы варианты для вопроса') + ':' + questionNumber;
                        success = false;
                        return;
                    }
                    let isRightExists = false;
                    for (const variant of question.variants) {
                        if (variant.is_right) {
                            isRightExists = true;
                            break;
                        }
                    }
                    if (!isRightExists) {
                        message = window.tt('common', 'Не заданы варианты для вопроса') + ':' + questionNumber;
                        success = false;
                        return;
                    }
                }

                if (question.params.type === 'gap' || question.params.gap_test) {
                    const gapRegExp = new RegExp('\\[(.+)\\]')
                    if (!gapRegExp.test(question.params.gap_test_text)) {
                        message = Yii?.t('common', 'There are no variants for question: {n}', {n: questionNumber})
                            ?? ('There are no variants for question: ' + questionNumber);
                        success = false;
                        return;
                    }
                }
                if (question.params.type === 'combination') {
                    for (const variant of question.variants) {
                        variant.value.split('|').forEach(function(combination) {
                            if (combination.length === 0) {
                                success = false;
                                message = window.tt('common', 'Не заданы варианты для вопроса') + ':' + questionNumber;
                            }
                        });
                    }
                    if (!success) {
                        return;
                    }
                }
            } else if (question.params.type !== 'combination') {
                if (question.variants.length === 0) {
                    message = window.tt('common', 'Не заданы варианты для вопроса') + ':' + questionNumber;
                    if (isYii) {
                        message = Yii.t('common', 'There are no variants for question: {n}', {n: questionNumber});
                    }
                    success = false;
                } else {
                    let variants = question.variants;
                    let variantValues = [];
                    variants.forEach(function(variant, index) {
                        let variantValue = variant.value.split('image_')[0].trim();
                        variantValue = variantValue.split('video_')[0].trim();
                        let variantImage = variant.params.image;
                        let variantVideo = variant.params.video;
                        if (variantImage && variantImage.length > 0) {
                            variantValue = variantImage;
                        }
                        if (variantVideo && variantVideo.length > 0) {
                            variantValue = variantVideo;
                        }
                        if (variantValue.length === 0) {
                            if (isYii) {
                                message = Yii.t('common', 'There are empty variant for question: {n}', {n: questionNumber});
                            }
                            success = false;
                            return;
                        }

                        if(variant.points < 0) {
                            if (isYii) {
                                message = Yii.t('common', 'Некорректное количество баллов за вариант {index} в вопросе {n}', {n: questionNumber, index: index+1});
                            }
                            success = false;
                            return;
                        }

                        variantValues.push(variantValue);
                    });
                    if (success === false) {
                        return;
                    }
                    let uniqueValues = variantValues.filter((v, i, a) => a.indexOf(v) === i);
                    if (variantValues.length !== uniqueValues.length) {
                        if (isYii) {
                            message = Yii.t('common', 'There are non-unique variants for question: {n}', {n: questionNumber});
                        }
                        success = false;
                    }
                }
            }

			if(question.params.right_points < 0) {
				if (isYii) {
					message = Yii.t('common', 'Некорректное количество баллов за правильный ответ в вопросе {n}', {n: questionNumber});
				}
				success = false;
				return;
			}

			return success;
		});

		if (success === false) {
			if ($.toast) {
				$.toast(message, {type: 'danger'});
			} else {
				alert(message);
			}
		}

		return success;
	},
	deleteQuestionary: function() {
		this.deleted = true;
		this.preSave();
	},
	apply: function() {
		this.deleted = false;
		return this.preSave();
	},
    globalElementsControl: function () {
        this.selectControl();
        this.tagsControl();
    },
	selectControl: function () {
		if($('.js__questionary-list-item').length > 0) {
			$('.js__questionnaire-select').prop("disabled", true);
		} else {
			$('.js__questionnaire-select').prop("disabled", false);
		}
	},
	tagsControl: function () {
		if($('.js__questionary-list-item').length == 0) {
            $('#addTagsEl').remove();
		}
	},
	translateStrings: function(strings) {
		if (typeof Yii != 'undefined') {
			for (let key in strings) {
				if (!strings.hasOwnProperty(key)) continue;
				strings[key] = Yii.t('common', strings[key]);
			}
		}

		return strings;
	},
    isGapTest: function ($questionEl) {
        return window.newTestsFeature && $questionEl.find('.gap-test').val() === '1';
    },
});
