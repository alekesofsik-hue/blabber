jQuery.widget( 'gc.gcFileSelectorFolderFavorites', $.gc.gcFileSelectorFolder, {
    options: {
    },
    _create: function() {
        var self = this;

        this.filesEl = $('<div class="files-list"></div>')
		this.filesEl.appendTo( this.element )
    },
    init: function() {
        this.loadFiles( "favorites", this.filesEl )
    }
} );
