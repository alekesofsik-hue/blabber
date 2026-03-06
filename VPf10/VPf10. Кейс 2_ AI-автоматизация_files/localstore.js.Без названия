/**
 * Для использования
 * $(document).ready(function(){
 *     $('form').FormCache({'form': 'селектор формы', attr: 'Элемент который хранит постоянный id формы'});
 * });
 */
// console.log('модуль кеширования');
(function ($) {
	$.fn.FormCache = function (options) {
		var settings = $.extend({
			'form' : 'form:first',
			// id формы/ не всегда хранится в id
			'attr' : 'id',
			// Признак того что анкета создана в редакторе страницы и нужно обновить surveyData и отделить анкету
			// от данных клиента
			'surveyData': null,
			'autoResetCache': true
		}, options);
		var multidata = {};
		function on_change(event) {
			var input = $(event.target);
			window.Xin = input;
			var formID = input.parents(settings.form).attr(settings.attr);
			var currentpartindex = input.parents('[data-block-id=' + formID + ']').attr('data-currentpartindex');
			// Данные по всем полям
			var data = loadLocalStore(formID);
			multidata = data.multidata !== undefined ? data.multidata : {};

			if (input.attr('id') !== undefined) {
				if (input.attr('type') === 'radio' || input.attr('type') === 'checkbox') {
					data[input.attr('id')] = input.is(':checked');
				} else {
					data[input.attr('id')] = input.val();
				}
			} else {
				if (input.attr('type') === 'checkbox' || input.attr('type') === 'radio') {
					// Это множественное поле выбора
					var name = input.attr('name');
					if (!(name in multidata)) {
						multidata[name] = [];
					}
					input.parents(settings.form).find('input[name="' + name + '"]').each(function (index, el) {
						var val = $(el).is(':checked');
						multidata[name][index] = val;
					})
					data.multidata = multidata;
					window.data = data;
				} else if (input.attr('type') === 'text') {
					var name = input.attr('name');
					if (!(name in multidata)) {
						multidata[name] = [];
					}
					input.parents(settings.form).find('input[name="' + name + '"]').each(function (index, el) {
						multidata[name][index] = $(el).val();
					})
					data.multidata = multidata;
					window.data = data;
				}
			}
			if (currentpartindex !== undefined) {
				data['currentpartindex'] = currentpartindex;
			}

			updateLocalStore(formID, data);
		}
		function on_submit(event) {
			var input = $(event.target);
			var formID = input.parents(settings.form).attr(settings.attr);
			if (options.autoResetCache) {
				localStorage.removeItem(formID);
			}
		}

		function updateLocalStore(formID, data) {
			localStorage[formID] = JSON.stringify(data);
		}

		function loadLocalStore(formID) {
			var data = false;
			if (localStorage[formID]) {
				data = JSON.parse(localStorage[formID]);
			}
			if (!data) {
				localStorage[formID] = JSON.stringify({});
				data = JSON.parse(localStorage[formID]);
			}
			return data;
		}

		return this.each(function () {
			var element = $(this);
			if (typeof (Storage) !== "undefined") {
				var formID = element.attr(settings.attr);
				var data = loadLocalStore(formID);

				var cacheInputs = element.find('input, select, textarea');
				if (settings.surveyData !== null) {
					cacheInputs = element.find(settings.surveyData).find('input, select, textarea');
				}

				cacheInputs.change(on_change);
				cacheInputs.keyup(on_change);
				// Эксперементально в ContextHelpLink элементы могут добавляться динамически
				element.on('change','input', on_change);

				if (element.find('button.btn-send').length > 0) {
					element.find('button.btn-send').on('click', on_submit);
				} else {
					element.find('button[type="submit"]').on('click', on_submit);
				}
				cacheInputs.each(function () {
					if ($(this).attr('type') !== 'submit') {
						var input = $(this);
						if (input.attr('readonly') === 'readonly') {
							return;
						}
						var value = data[input.attr('id')];
						// Есть данные только с бэка
						var onlyDataFromBack = input.attr('id') !== undefined && value === undefined;

						// Есть введенные ранее значения которые подгрузились с формой
						// инпуты
						if (
							onlyDataFromBack
							&& input.attr('type') !== 'checkbox' && input.attr('type') !== 'radio'
							&& input.val() !== ''
						) {
							return;
						}
						// чекбоксы
						if (
							onlyDataFromBack
							&& (input.attr('type') === 'checkbox' || input.attr('type') === 'radio')
							&& input.is(':checked')
						) {
							return;
						}
						//
						if (input.attr('id') !== undefined) {
							if (input.attr('type') === 'radio') {
								if (value) {
									input.attr('checked', input.is(':checked'));
								} else {
									input.removeAttr('checked');
								}
							} else if (input.attr('type') === 'checkbox') {
								if (value) {
									input.attr('checked', 'checked');
								} else {
									input.attr('checked', false);
								}
							} else {
								input.val(value);
								if (
									input.attr('id') !== 'CustomFormValue'
									&& input.parent().find('div.uploadifive-button').length === 1
								) {
									if (value !== undefined && input.fileWidget !== undefined) {
										input.fileWidget('showPreview');
									}
								}
							}
						}
					}
				});
				if (data.multidata !== undefined ) {
					for (var i in data.multidata) {
						if (i === 'ContextHelpLink[]') {
							var countEl = data.multidata[i].length;
							var countPage = element.find('input[name="' + i + '"]').length;
							var def = countEl - countPage;

							if (def > 0 && window.addRowLink !== undefined) {
								for (var j = 0; j < def; j++) {
									window.addRowLink();
								}
							}
						}
						if (element.find('input[name="' + i + '"]').length > 0) {
							element.find('input[name="' + i + '"]').each(function (index, el) {
								if ($(el).attr('type') === 'text') {
									$(el).val(data.multidata[i][index]);
								} else {
									$(el).prop('checked', data.multidata[i][index]);
								}
							})
						}
					}
				}
				// установить нужную вкладку
				if (data['currentpartindex'] !== undefined) {
					$('#' + element.parents('[data-block-id=' + formID + ']').attr('id'))
						.liteSinglyForm({currentPartIndex: parseInt(data['currentpartindex'])});
				}
				var widget = element.find('.custom-form');
				if (settings.surveyData !== null && widget.length) {
					$('#' + widget.attr('id')).customForm('changed')
				}
			} else {
				console.log('local storage is not available');
			}
		});
	};
	$.fn.resetLocalCache = function (options) {
		var settings = $.extend({
			'attr' : 'id'
		}, options);
		localStorage.removeItem(this.attr(settings.attr));
	};
}(jQuery));
