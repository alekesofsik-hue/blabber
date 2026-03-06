jQuery.widget( 'gc.gcFilePixabayFolder', {
    options: {
        owner: null,
        folder: null
    },

    _create: function() {
        var self = this;
        this.element.addClass("pixabay-folder")

        this.panel = this.createPanel();
        this.panel.appendTo( this.element )

		var searchLabel = 'Поиск по фотобанку Pixabay';
		var licenseLabel = 'Все изображения опубликованы под лицензией Creative Commons CC0 (бесплатно доступны к использованию)';
		if (typeof Yii != 'undefined') {
			searchLabel = Yii.t("common", searchLabel);
			licenseLabel = Yii.t("common", licenseLabel);
		}

		this.pixabayEl = $('<div class="clearfix pixabay-info-label"><a target="_blank" href="http://pixabay.com"><img  src="https://pixabay.com/static/img/public/leaderboard_b.png"></a> ' + searchLabel + ' <br/>' + licenseLabel + ' </div>')
                this.pixabayEl.appendTo( this.element )

        this.filesEl = $('<div class="files-list"></div>')
        this.filesEl.appendTo( this.element )


    },
    checkNeedToRefresh: function() {
        var self = this;
        //this.panel = this.createPanel();
    },
    createPanel: function() {

        var self = this;

		var searchSimpleLabel = 'Поиск';
		var allImagesLabel = 'все изображения';
		var photoLabel = 'фото';
		var ilustrationLabel = 'иллюстрации';
		var vectorLabel = 'векторные';
		var allOrintationLabel = 'любая ориентация';
		var horizontalLabel = 'горизонтальные';
		var verticalLabel = 'вертикальные';
		var findLabel = 'Найти';
		var wordLabel = 'прибой';

		if (typeof Yii != 'undefined') {
			searchSimpleLabel = Yii.t("common", searchSimpleLabel);
			allImagesLabel = Yii.t("common", allImagesLabel);
			photoLabel = Yii.t("common", photoLabel);
			ilustrationLabel = Yii.t("common", ilustrationLabel);
			vectorLabel = Yii.t("common", vectorLabel);
			allOrintationLabel = Yii.t("common", allOrintationLabel);
			horizontalLabel = Yii.t("common", horizontalLabel);
			verticalLabel = Yii.t("common", verticalLabel);
			findLabel = Yii.t("common", findLabel);
			wordLabel = Yii.t("common", wordLabel);
		}

        var $panel = $(
           "<form class='search-panel'>"
           + "<div class='results-nav'> <span class='results-count text-muted' style='padding-right: 10px'></span> <span class='btn-prev-page fa fa-chevron-left'></span> <span class='page-num'></span> / <span class='page-count'></span> <span class='btn-next-page fa fa-chevron-right'></span> </div>"
           + "<div class='filter'>"+searchSimpleLabel+" <input class='search-input' type=text size=50 > <select class='type-select'><option value='all'>"+allImagesLabel+"</option><option selected value='photo'>"+photoLabel+"</option><option value='illustration'>"+ilustrationLabel+"</option><option value='vector'>"+vectorLabel+"</option></select> <select class='orientation-select'><option value='all'>"+allOrintationLabel+"</option><option value='horizontal'>"+horizontalLabel+"</option><option value='vertical'>"+verticalLabel+"</option></select>  <button type='submit' class='btn btn-primary btn-xs'>"+findLabel+"</button></div>"
           + "</form>"
        )

        this.searchInput = $panel.find('.search-input')
        this.searchInput.val(wordLabel)
        this.typeSelect = $panel.find('.type-select')
        this.orientationSelect = $panel.find('.orientation-select')

        this.pageNumEl = $panel.find('.page-num')
        this.pageCountEl = $panel.find('.page-count')
        this.resultsCountEl = $panel.find('.results-count')
        this.nextPageBtn = $panel.find('.btn-next-page')
        this.prevPageBtn = $panel.find('.btn-prev-page')

        this.nextPageBtn.hide();
        this.prevPageBtn.hide();

        this.nextPageBtn.click( function() {
            self.loadFiles( self.pageNum + 1)
        })

        this.prevPageBtn.click( function() {
            self.loadFiles( self.pageNum - 1)
        })

        $panel.submit( function() {
            self.loadFiles();
            return false;
        })

        return $panel;
    },

    createFileEl: function( hit ) {
        var $el = $('<div class="file-item pixabay-file-item"></div>')
        var self = this;

        $el.data('webformat-url', hit.webformatURL)
        $el.data('hit', hit)

        $imgWrapper = $('<div class="img-wrapper"></div>')
        $imgWrapper.appendTo( $el );
        //$imgWrapper = $imgWrapper.find('span')

        var $img = $('<img>')
        $img.attr( "src", hit.previewURL )
        $img.appendTo( $imgWrapper )

        //$selectBtn = $('<button class="btn btn-select btn-primary">Выбрать</button>')
        //$selectBtn.appendTo( $el )

        $favBtn = $('<button class="btn btn-link btn-favorites"><span class="to-favorites glyphicon glyphicon-folder-close"></span><span class="from-favorites glyphicon glyphicon-folder-open"></span></button>')
        //$favBtn.appendTo( $el )
        self.favBtn = $favBtn


        var $previewDiv = $('<div class="preview-div"></div>')
        $previewDiv.appendTo( $el )
        $previewDiv.hide();

        $el.mouseover( function() {
            $previewEl = $(this).find('.preview-div');
            var webformatURL = $(this).data('webformat-url')
            if ( ! $previewEl.data('loaded')) {
                var $img = $("<div><img src='" + webformatURL + "'/></div>")
				var inCommonLabel = 'в общие';
				if (typeof Yii != 'undefined') {
					inCommonLabel = Yii.t("common", inCommonLabel);
				}
				var $buttons = $('<div class="buttons"> <a class="to-fav" href="javascript:void(0)"> <span class="glyphicon glyphicon-folder-close"></span> ' + inCommonLabel + '</a></div>')

                var $toFavBtn = $buttons.find( '.to-fav' )

                $toFavBtn.click( function(e ) {
                    self.toFavorites( $el )
                    e.stopPropagation();
                    e.preventDefault();
                })

                $previewEl.click( function() {
                    self.selectFile( $el );
                } );

                $img.appendTo( $previewEl )
                $buttons.appendTo( $previewEl )

                $previewEl.data('loaded', true)
            }
            if ( ! $el.hasClass('loading')) {
                $previewEl.show();
            }
        } );

        $el.mouseout( function() {
            $(this).find('.preview-div').hide();
        } );



        return $el;
    },
    startLoading: function( $el ) {
        $el.find('.preview-div').hide();
        $el.addClass('loading')

        $loader = $("<div class='loader' style='position: absolute; top: 10px; left: 10px; '></div>")
        setElLoading( $loader )
        $loader.appendTo( $el )
    },
    stopLoading: function( $el ) {
        $el.find('.loader').remove();
        $el.removeClass('loading')
    },
    toFavorites: function( $el ) {
        var self = this;
        var hit = $el.data('hit')
        if ( hit.webformatURL ) {


            self.startLoading( $el );

            self.getFileFromPixabay( hit, function( hash ) {
                self.markFile( hash, "favorites", true, function() {
                    self.stopLoading( $el );
                    $('.folder-picker-favorites').effect('highlight', { duration: 1000})
                })
            })

        }
    },

    selectFile: function( $el ) {

        var self = this;
        var hit = $el.data('hit')
        if ( hit.largeImageURL ) {
            self.startLoading( $el );

            self.getFileFromPixabay( hit, function( hash ) {
                self.stopLoading( $el );
                self.options.owner.fileSelected( hash )
            })
        }

    },


    getFileFromPixabay: function( hit, callback ) {
        var data = { link:hit.largeImageURL }
        ajaxCall( "/pl/fileservice/widget/load-link", data, {}, function( response ) {
            if ( callback ) {
                callback( response.data.hash )
            }
        } )
    },

    markFile: function( hash, mark, positive, callback ) {
        var data = {
            hash: hash,
            mark: mark,
            positive: positive ? 1 : 0
        }

        ajaxCall( "/pl/fileservice/widget/mark", data, {}, function() {
            if ( callback ) {
                callback( positive );
            }
        } )
    },
    loadFiles: function( pageNum ) {
        var self = this;

        $toElement = this.filesEl;

        $toElement.empty();

        if ( ! pageNum ) {
            pageNum = 1;
        }

        var perPage = 40;
        var searchParamsStr = "";
        searchParamsStr += "q=" + encodeURIComponent( this.searchInput.val() )
        searchParamsStr += "&image_type=" + this.typeSelect.val()
        searchParamsStr += "&orientation=" + this.orientationSelect.val()
        searchParamsStr += "&page=" + pageNum;
        searchParamsStr += "&per_page=" + perPage;

        $.get( "https://pixabay.com/api/?key=2495655-17a65303269e60a85dbeaffe8&" + searchParamsStr, {}, function( response ) {
            for( key in response.hits) {
                var hit = response.hits[key];
                var $el = self.createFileEl( hit )
                $el.appendTo( $toElement )
            }

            var pagesCount = Math.ceil( response.totalHits / perPage );

            self.pageNum = pageNum;

            self.pageNumEl.html( pageNum )
            self.pageCountEl.html( pagesCount )
            if ( pageNum < pagesCount ) {
                self.nextPageBtn.show();
            }
            else {
                self.nextPageBtn.hide();
            }
            if ( pageNum > 1 ) {
                self.prevPageBtn.show();
            } else {
                self.prevPageBtn.hide();
            }

			var isoLabel = 'изображений';

			if (typeof Yii != 'undefined') {
				isoLabel = Yii.t("common", isoLabel);
			}

			self.resultsCountEl.html(isoLabel + ": " + response.totalHits);
        })
    },
    /*selectFile: function( hash ) {
        this.options.owner.fileSelected( hash )
    },*/
    init: function() {
        this.loadFiles()
    }
} );
