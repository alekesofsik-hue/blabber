jQuery.widget('gc.gcVideoStatistics', $.gc.gcFileSelectorFolder, {
	options: {
		mainHash: null,
		previewList: []
	},
	mapFrameHashToSrc: null,
	currentPreview: null,
	watermarkEnableInput: false,
	users: {},
	grids: [],
	popup: null,
	gridData: [],
	gridFilter: [
		-1, -1, -1, -1
	],
	_create: function() {
		var self = this;
		var $messageEl = $('<div><h3>' + Yii.t('common', 'Просмотры') + '</h3></div>');
		self.messageEl = $messageEl;

		ajaxCall('/pl/fileservice/video/info', {
				'file-hash': self.options.mainHash,
				'result-format': 'json'
			}, {crossDomain: true}, function (response) {
			if (response.videoHash !== null) {
				self.options.statisticsUrl = response.statisticsUrl;
				self.options.apiHost = response.apiHost;
				self.options.isVertical = response.isVertical;

				self.generateDatatable();
			} else {
				$messageEl.text(window.tt('common', 'Это видео еще не обработано'));
			}
		});
	},
	init: function() {
		this.gridFilter = [-1, -1, -1, -1];
	},
	generateRows: function(deleted = false) {
		var $users = this.users;
		var $content =  $('<tbody>');
		var self = this;
		$.each($users, function (index, value) {
			var next = false;

			if (deleted && !value.deleted) {
				return;
			}

			if (!deleted && value.deleted) {
				return;
			}

			var grids = '';
			var maxIndex = 0;

			$.each(self.gridFilter, function (index, value) {
				if (value >= 0) {
					maxIndex = index;
				}
			});

			if (value.images.length < maxIndex + 1) {
				return;
			}

			$.each(value.images, function( index, value ) {
				// hack
				var name = parseInt(value) + '.jpg';
				if (self.gridFilter[index] >= 0 && self.gridFilter[index] == parseInt(value)) {
					grids += '<div class="grid-image"><img src="https://vh-asset-static.vhcdn.com/vhstatic/grid-image/1/' + name + '" alt="grid"></div>';
					return;
				}

				if (self.gridFilter[index] == -1) {
					grids += '<div class="grid-image"><img src="https://vh-asset-static.vhcdn.com/vhstatic/grid-image/1/' + name + '" alt="grid"></div>';
					return;
				}

				next = true;
			});

			if (next) {
				return;
			}

			var $grid = '<td>' + grids + '</td>';
			var firstName = value.first_name === null || value.deleted ? '' : value.first_name;
			var lastName = value.last_name === null || value.deleted ? '' : value.last_name;
			var timeCreated = value.time_created === null || value.deleted ? '' : value.time_created;

			$content.append($('<tr>' +
				'<th scope="row">' + (value.deleted ? Yii.t('common', 'Пользователь удален') : value.email) + '</th>' +
				'<td>' + firstName + '</td>' +
				'<td>' + lastName + '</td>' +
				'<td>' + timeCreated + '</td>' + $grid));
		});

		$content.append($('</tbody>'));

		return $content;
	},
	generateHtml: function() {
		var $content = $('<table class="table">');
		var $deletedContent = $content.clone();

		var $tableHead = $('<thead>\n' +
			'    <tr>\n' +
			'      <th scope="col">Email</th>\n' +
			'      <th scope="col">' + Yii.t('common', 'Имя') + '</th>\n' +
			'      <th scope="col">' + Yii.t('common', 'Фамилия') + '</th>\n' +
			'      <th scope="col">' + Yii.t('common', 'Дата визита') + '</th>\n' +
			'      <th scope="col">' + Yii.t('common', 'Вид сетки') + '</th>\n' +
			'    </tr>\n' +
			'  </thead>');

        var $deletedTableHead = $tableHead.clone();

		var $tableRows = this.generateRows(false);
        var $deletedTableRows = this.generateRows(true);

        var $tableEnd = $('</table>');
        var $deletedTableEnd = $tableEnd.clone();

		$content.append($tableHead);
		$content.append($tableRows);
		$content.append($tableEnd);

        $deletedContent.append($deletedTableHead);
        $deletedContent.append($deletedTableRows);
        $deletedContent.append($deletedTableEnd);

		this.mainTable = $content;
        this.deletedTable = $deletedContent;

		return $content;
	},
	generateDatatable: function () {
		var $tables = $('<div class="stat-tables"></div>');
		var $notification = $('<div class="statistics-notification">' +
			Yii.t('common', 'При удалении пользователей статистика просмотров будет удалена') +
			'</div>');
		var $deletedStatistics = $('<a style="color:#ff4c4c" href="#"></a>');
		var $activeStatistics = $('<a style="color:#74cc00" href="#"></a>');
		var $bottomPanel = $('<div class="stat-bottom" style="position: fixed; bottom: 5px;"></div>');

		this.element.addClass("statistics-content");
		this.element.css({
			'padding' : '20px',
			'width' : '85%',
			'display' : 'inline-block',
			'overflow' : 'hidden',
			'overflow-y' : 'auto',
			'height': '590px',
		});

		$notification.css({
			'color' : '#7b7b7b'
		});

		var datatableOptions = {
			"ordering": false,
			"scrollY": '400px',
			"scrollCollapse": true,
			"paging": true,
			"language": {
				"search": Yii.t('common', 'Поиск:'),
				"lengthMenu": Yii.t('common', 'Показать') + ' _MENU_ ' + Yii.t('common', 'записей'),
				"zeroRecords": Yii.t('common', 'Извините, ничего не найдено'),
				"info": Yii.t('common', 'Количество записей') + ': _MAX_',
				"infoEmpty": Yii.t('common', 'Записей не найдено'),
				"infoFiltered": Yii.t('common', '(отфильтровано') + ' _MAX_ ' + Yii.t('common', 'записей') + ')',
				"paginate": {
					"first": Yii.t('common', 'Первая'),
					"last": Yii.t('common', 'Последняя'),
					"next": Yii.t('common', 'Следующая'),
					"previous": Yii.t('common', 'Предыдущая')
				},
			}
		};

		var $firstPositionSelect = this.generateFindFilter('first');
		var $secondPositionSelect = this.generateFindFilter('second');
		var $thirdPositionSelect = this.generateFindFilter('third');
		var $fourthPositionSelect = this.generateFindFilter('fourth');

		var $filter = $('<div class="filter-form"></div>');

		$filter.append($firstPositionSelect);
		$filter.append($secondPositionSelect);
		$filter.append($thirdPositionSelect);
		$filter.append($fourthPositionSelect);

		var $filterWrapper = $('<div id="filter-wrapper"></div>');
		$filterWrapper.append($filter);
		this.element.append($('<div><h3>' + Yii.t('common', 'Фильтр') + '</h3></div>'));
		this.element.append($filterWrapper);
		this.element.append($('<br>'));
		this.element.append(this.messageEl);
		this.element.append($tables);
		this.element.append($bottomPanel);
		var self = this;
		var select2Config = {
			dropdownParent: $(this).find('.modal-content'),
			minimumResultsForSearch: -1,
			formatResult: function (state) {
				if (state.element[0].value === '-1') {
					return $('<div>' + Yii.t('common', 'Без сетки') + '</div>');
				}

				return  $('<div style="float: left; border: 1px solid black;height: 60px;\n' +
					'width: 60px;' +
					'margin: 2px 2px 2px 2px;' +
					'overflow: hidden;"><img style="width: 100%; transform: scale(3);" ' +
					'src="https://vh-asset-static.vhcdn.com/vhstatic/grid-image/1/'
					+ state.element[0].value + '.jpg" /></div>');
			},
		};

		var $selects = [
			$firstPositionSelect.select2(select2Config),
			$secondPositionSelect.select2(select2Config),
			$thirdPositionSelect.select2(select2Config),
			$fourthPositionSelect.select2(select2Config),
		]

		this.selects = $selects;

		var onSelect = function (e) {
			var position = e.target.id;
			var val = e.val;

			switch (position) {
				case 'first_position' :
					self.gridFilter[0] = val;
					break;
				case 'second_position' :
					self.gridFilter[1] = val;
					break;
				case 'third_position' :
					self.gridFilter[2] = val;
					break;
				case 'fourth_position' :
					self.gridFilter[3] = val;
					break;
			}

			self.generateHtml();
			$tables.empty();

			$tables.append(self.mainTable);
			$tables.append(self.deletedTable);

			self.mainTable.DataTable(datatableOptions);
			self.deletedTable.DataTable(datatableOptions);
			self.mainTable.parent().parent().parent().css('height', '400px');
			self.deletedTable.parent().parent().parent().css('height', '400px');

			if (self.currentTable === 'active' || !self.currentTable) {
				self.deletedTable.parent().parent().parent().hide();
			} else {
				self.mainTable.parent().parent().parent().hide();
			}
		}

		$firstPositionSelect.on("select2-selecting", onSelect);
		$secondPositionSelect.on("select2-selecting", onSelect);
		$thirdPositionSelect.on("select2-selecting", onSelect);
		$fourthPositionSelect.on("select2-selecting", onSelect);

		$('.select2-drop').css('z-index', 99999);
		$('.select2-results').css('display', 'grid');

		$('html').click(function(e) {
			if(!$(e.target).hasClass('select2-drop') ) {
				$selects.forEach(el => el.select2('close'));
			}
		});

		$activeStatistics.hide();

		ajaxCall(self.options.statisticsUrl , {}, {}, function (response) {
			let userIds = response.info.map(a => a.payload.replace(/\D/g, ""));
			ajaxCall('/pl/fileservice/video/users-info', {
				'json': JSON.stringify(userIds),
			}, {}, function (resp) {
				self.dictionary = resp.result;
				if (response.info) {
					let users = [];
					for(var i in response.info) {
						let id = response.info[i].payload.replace(/\D/g, "")
						if (!self.dictionary[id]) {
							continue;
						}

						users.push({
							id: id,
							time_created: response.info[i].time_created,
							deleted: !!+self.dictionary[id].deleted,
							email: self.dictionary[id].email,
							first_name: self.dictionary[id].first_name,
							last_name: self.dictionary[id].last_name,
							images: response.info[i].images,
						});
					}

					self.users = users;

					$bottomPanel.append($notification);
					$bottomPanel.append($deletedStatistics);
					$bottomPanel.append($activeStatistics);

					self.generateHtml();

					var deletedUsers = [];
					var activeUsers = [];

					for(var i in self.users) {
						if (self.users[i].deleted) {
							deletedUsers.push([i, self.users[i]]);
						} else {
							activeUsers.push([i, self.users[i]]);
						}
					}

					if (deletedUsers.length) {
						$deletedStatistics.text(
							Yii.t('common', 'Показать статистику ') +
							deletedUsers.length + Yii.t('common', ' удаленных пользователей')
						);
						$deletedStatistics.click(function (e) {
							e.preventDefault();
							$activeStatistics.show();
							$deletedStatistics.hide();

							self.currentTable = 'deleted';
							self.mainTable.parent().parent().parent().hide();
							self.deletedTable.parent().parent().parent().show();
						});

						$activeStatistics.text(
							Yii.t('common', 'Показать статистику ') +
							activeUsers.length +
							Yii.t('common', ' активных пользователей')
						);
						$activeStatistics.click(function (e) {
							e.preventDefault();
							$activeStatistics.hide();
							$deletedStatistics.show();
							self.currentTable = 'active';

							self.mainTable.parent().parent().parent().show();
							self.deletedTable.parent().parent().parent().hide();
						});
					}

					$tables.append(self.mainTable);
					$tables.append(self.deletedTable);

					self.mainTable.DataTable(datatableOptions);
					self.deletedTable.DataTable(datatableOptions);
					self.mainTable.parent().parent().parent().css('height', '400px');
					self.deletedTable.parent().parent().parent().css('height', '400px');

					self.deletedTable.parent().parent().parent().hide();
				} else {
					self.messageEl.text('Статистика недеоступна. Обратитесь в техподдержку.');
				}
			});
		});
	},
	generateFindFilter: function (order) {
		var $selectForm = $('<select id="' + order + '_position" style="width: 12vw; margin-right: 15px;"></select>');
		var $zeroOption = $('<option value="-1">' + Yii.t('common', 'Без сетки') + '</option>');
		$selectForm.append($zeroOption);

		for (var i = 0; i < 22; i++) {
			var $option = $('<option value="' + i + '">' + Yii.t('common', 'Сетка') + ' ' + i + '</option>');
			$selectForm.append($option);
		}
		return $selectForm;
	},
	onSelect: function (e) {


	}
} );
