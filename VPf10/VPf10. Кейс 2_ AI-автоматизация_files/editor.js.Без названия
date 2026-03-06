$(function(){
    var gc = {
        fabric : {
            utils: {}
            ,editor : {
                button : {
                }
            }
        }
    };

    gc.fabric.utils.getRandomLeftTop = function (canvasWidth, canvasHeight) {
        var offset = Math.min(canvasHeight, canvasWidth) * 0.2;
        return {
            left: fabric.util.getRandomInt(offset, canvasWidth - offset),
            top: fabric.util.getRandomInt(offset, canvasHeight - offset)
        };
    };

    gc.fabric.editor.button.Button = fabric.util.createClass({
        initialize : function(options) {
            this.options = options;
        }
        ,click : function(canvas) {
            canvas.isDrawingMode = this.isDrawingMode();
            this.editor.clearButtonListeners();
            this.editor.lockObjects();
            this.editor.addButtonListeners(this._doClick(canvas));
            this._initSettings();
        }
        ,getStrokeWidth : function() {
            return this.strokeWidth === undefined ? 3 : this.strokeWidth;
        }
        ,setStrokeWidth : function(width) {
            this.strokeWidth = width;
        }
        ,_initSettings : function() {
            var that = this
                , $container = $('.settings', this.editor.$container)
                ,$settings = $('.'+this.getName(), $container);
            $('.content', $container).hide();
            if ($settings.length === 0) {
                $container.append('<div class="content '+this.getName()+'"></div>');
                if (this._doInitSettings !== undefined) {
                    $settings = $('.' + this.getName(), $container);
                    this._doInitSettings($settings);
                }
                if (this.options.strokeWidthEditable !== undefined && this.options.strokeWidthEditable) {
                    var labelWidth = 'Ширина';
                    if (typeof Yii != 'undefined') {
                        labelWidth = Yii.t('common', 'Width');
                    }
                    $settings.append([
                        '<div class="setting stroke-width">'
                        ,'<span class"label">' + labelWidth + ': <span class="val">'+that.getStrokeWidth()+'</span> '
                        ,'<span class="control"><input type="range" name="strokeWidth" min="1" max="10" value="'+that.getStrokeWidth()+'"></span>'
                        ,'</div>'
                    ].join(''));
                    $('input[name=strokeWidth]', $settings).on('input', function(){
                        var width = $(this).val();
                        $.each(that.editor.getButtons(), function(index, group) {
                            $.each(group.buttons, function(buttonIndex, button) {
                                button.setStrokeWidth(width);
                            });
                        });
                        $('.stroke-width .val', that.editor.$container).html(width);
                        $('input[name=strokeWidth]', that.editor.$container).val(width);
                    });
                }
            }
            else {
                $settings.show();
            }
            return $settings;
        }
        ,isDrawingMode : function() {
            return this.options.isDrawingMode !== undefined && this.options.isDrawingMode;
        }
        ,isActive : function() {
            return this.options.isActive !== undefined && this.options.isActive;
        }
        ,getName : function() {
            return this.options.name;
        }
        ,getIcons : function() {
            return this.options.icons;
        }
        ,setEditor : function(editor) {
            this.editor = editor;
        }
        ,getHtml : function() {
            var icons = this.getIcons()
                ,$html = $('<span class="fa-stack button '+this.getName()+'-action '+(
                    this.isActive() ? 'button-active' : ''
                )+'"></span>')
                ;
            for(var index in icons) {
                var zIndex = (index + 1);
                $html.append('<i class="fa '+icons[index]+' fa-stack-'+(parseInt(index) + 1)+'x">');
            }
            return $html;
        }
        ,getHtmlElement : function() {
            return $('.'+this.getName()+'-action ', this.editor.$container);
        }
    });

    gc.fabric.editor.button.Colored = fabric.util.createClass(gc.fabric.editor.button.Button, {
        getHtml : function() {
            var $html = gc.fabric.editor.button.Button.prototype.getHtml.call(this);
            $html.css('color', this.getColor());
            return $html;
        }
        ,setColor : function(color) {
            this.color = color;
            this.getHtmlElement().css('color', color);
        }
        ,_doInitSettings : function($settings) {
            var that = this;
            var $colorSetting = $('.color-setting', that.editor.$container);
            if ($colorSetting.length === 0) {
                var labelColor = 'Цвет';
                if (typeof Yii != 'undefined') {
                    labelColor = Yii.t('common', 'Color');
                }
                $settings.append(
                    '<div class="setting color-setting">' + labelColor + ': <button class="colpicker" style="border:none;background-color: '+this.getColor()+';width:10px;height:10px;"></button></div>'
                );
                $('.colpicker', $settings).colpick( {
                    layout:'hex',
                    submit:0,
                    colorScheme:'dark',
                    onChange: function(hsb,hex,rgb,el,bySetColor) {
                        $('.colpicker', that.editor.$container).css('background-color','#'+hex);
                        $.each(that.editor.getButtons(), function(index, group) {
                            $.each(group.buttons, function(buttonIndex, button) {
                                if (button instanceof gc.fabric.editor.button.Colored) {
                                    button.setColor('#'+hex);
                                }
                            });
                        });
                    }
                }).keyup(function(){
                    $(this).colpickSetColor(this.value);
                });
            }
        }
        ,getColor : function() {
            return this.color === undefined ? 'red' : this.color;
        }
        ,_initSettings : function() {
            var $settings = gc.fabric.editor.button.Button.prototype._initSettings.call(this);
            var $colorSetting = $('.color-setting', this.editor.$container);
            $settings.prepend($colorSetting);
        }
    });

    gc.fabric.editor.button.Remove = fabric.util.createClass(gc.fabric.editor.button.Button, {
        _doClick : function(canvas) {
            this.editor.removeSelectedGroup();
            $('.move-action', this.editor.$container).trigger('click');
        }
    });

    gc.fabric.editor.button.Clear = fabric.util.createClass(gc.fabric.editor.button.Button, {
        _doClick : function(canvas) {
            if (window.confirm('Удалить все объекты')) {
                canvas.clear();
                this.editor.showMessage('Все объекты удалены');
            }
            $('.move-action', this.editor.$container).trigger('click');
        }
    });

    gc.fabric.editor.button.Arrow = fabric.util.createClass(gc.fabric.editor.button.Colored, {
        _doClick : function(canvas) {
            var that = this
                ,xInit = 0
                ,yInit = 0
                ,path = null;
            var designer = new gc.fabric.editor.MouseDesigner(
                this.editor,
                function(mouse){
                    xInit = mouse.x;
                    yInit = mouse.y;
                    path = null;
                    //l1.set('x1', mouse.x - 10).set('y1', mouse.y - 10).set('x2', mouse.x).set('y2', mouse.y);
                    //l2.set('x1', mouse.x - 10).set('y1', mouse.y + 10).set('x2', mouse.x).set('y2', mouse.y);
                    path = new fabric.Path('M '+(mouse.x - 5)+' '+(mouse.y - 5)+' L '+mouse.x+' '+mouse.y+' L '+(mouse.x - 5)+' '+(mouse.y + 5)+' z', {
                        stroke: that.getColor(),
                        strokeWidth: that.getStrokeWidth(),
                        fill: that.getColor(),
                        originX: 'center',
                        originY: 'center'
                    });
                    that.editor.addObject(canvas, path);
                    return new fabric.Line([mouse.x, mouse.y, mouse.x, mouse.y], {
                        stroke: that.getColor()
                        , strokeWidth: that.getStrokeWidth()
                        , top: mouse.y
                        , left: mouse.x
                    });
                },
                function(mouse, object, x, y) {
                    object.set('x2', mouse.x).set('y2', mouse.y);
                    var angle = Math.atan2(object.get('y2')-object.get('y1'),object.get('x2')-object.get('x1'))*180/Math.PI;
                    var k = that.getStrokeWidth() / 2.5;
                    path.set('angle', angle).set('top', mouse.y +k).set('left', mouse.x+k);
                    //l1.set('x1', mouse.x - 10).set('y1', mouse.y - 10).set('x2', mouse.x).set('y2', mouse.y);
                    //l2.set('x1', mouse.x - 10).set('y1', mouse.y + 10).set('x2', mouse.x).set('y2', mouse.y);
                },
                function(object){
                    if (object.get('x2') == xInit && object.get('y2') == yInit) {
                        canvas.remove(object);
                        canvas.remove(path);
                    }
                    else {
                        var group = new fabric.Group();
                        group.addWithUpdate(path);
                        group.addWithUpdate(object);
                        path.set('selectable', false);
                        path.set('borderColor', 'transparent');
                        canvas.remove(path);
                        canvas.remove(object);
                        group.set('selectable', false);
                        canvas.add(group);
                    }
                }
            );

            return designer.start();

//                var path = new fabric.Path('M 0 0 L 50 0 M 0 0 L 4 -3 M 0 0 L 4 3 z', {
//                    stroke: 'red',
//                    strokeWidth: 1,
//                    fill: false,
//                    originX: 'left',
//                    originY: 'top'
//                });
//                //path.setAngle(100).set({ left: 100, top: 100 });
//                path.set({ left: 100, top: 100 });
//                path.set('width', 400);
//                canvas.add(path);
//                canvas.setActiveObject(path);
//                $('.move-action', this.editor.$container).trigger('click');
        }
    });

    gc.fabric.editor.button.Line = fabric.util.createClass(gc.fabric.editor.button.Colored, {
        _doClick : function(canvas) {
            var that = this
                ,xInit = 0
                ,yInit = 0;
            var designer = new gc.fabric.editor.MouseDesigner(
                this.editor,
                function(mouse){
                    xInit = mouse.x;
                    yInit = mouse.y;
                    return new fabric.Line([mouse.x, mouse.y, mouse.x, mouse.y], {
                        stroke: that.getColor()
                        ,strokeWidth: that.getStrokeWidth()
                        ,top: mouse.y
                        , left: mouse.x
                    });
                },
                function(mouse, object, x, y) {
                    object.set('x2', mouse.x).set('y2', mouse.y);
                },
                function(object){
                    if (object.get('x2') == xInit && object.get('y2') == yInit) {
                        canvas.remove(object);
                    }
                }
            );

            return designer.start();
//            var line = new fabric.Line([100, 100, 300, 100], {
//                stroke: this.getColor()
//                ,strokeWidth: 5
//                ,top: canvas.height * 0.3
//                , left: canvas.width * 0.3
//            });
//
//            canvas.add(line);
//            canvas.setActiveObject(line);
//            $('.move-action', this.editor.$container).trigger('click');
        }
    });

    gc.fabric.editor.button.Circle = fabric.util.createClass(gc.fabric.editor.button.Colored, {
        _doClick : function(canvas) {
            var that = this;
            var designer = new gc.fabric.editor.MouseDesigner(
                this.editor,
                function(mouse){
                    return new fabric.Circle({
                        stroke: that.getColor()
                        ,fill : 'transparent'
                        ,strokeWidth: that.getStrokeWidth()
                        ,radius: 0
                        ,top: mouse.y
                        , left: mouse.x
                        ,originX: 'center'
                        , originY: 'center'
                    });
                },
                function(mouse, object, x, y) {
                    var r = Math.sqrt(Math.pow(mouse.x - x, 2) + Math.pow(mouse.y - y, 2));//todo костыль для красоты поидее делить надо на 2
                    if (!r) {
                        return false;
                    }
                    object.set('radius', r);
                },
                function(object){
                    if (object.get('radius') == 0) {
                        canvas.remove(object);
                    }
                }
            );
            return designer.start();
        }
    });

    gc.fabric.editor.button.Ellipse = fabric.util.createClass(gc.fabric.editor.button.Colored, {
        _doClick : function(canvas) {
            var that = this;
            var designer = new gc.fabric.editor.MouseDesigner(
                this.editor,
                function(mouse){
                    return new fabric.Ellipse({
                        stroke: that.getColor()
                        ,fill : 'transparent'
                        ,strokeWidth: that.getStrokeWidth()
                        ,top: mouse.y
                        , left: mouse.x
                        ,rx: 0
                        ,ry: 0
                    });
                },
                function(mouse, object, x, y) {
                    var rx = mouse.x - x;
                    var ry = mouse.y - y;
                    object.set('rx', Math.abs(rx) / 2);
                    object.set('ry', Math.abs(ry) / 2);
                    object.set('originX', rx > 0 ? 'left' : 'right');
                    object.set('originY', ry > 0 ? 'top' : 'bottom');
                },
                function(object){
                    if (object.get('rx') == 0 || object.get('ry') == 0) {
                        canvas.remove(object);
                    }
                }
            );
            return designer.start();
        }
    });

    gc.fabric.editor.button.Move = fabric.util.createClass(gc.fabric.editor.button.Button, {
        _doClick : function(canvas) {
            this.editor.unlockObjects();
        }
    });

    gc.fabric.editor.button.Pencil = fabric.util.createClass(gc.fabric.editor.button.Colored, {
        _doClick : function(canvas) {
            this.setColor(this.getColor());
            this.setStrokeWidth(this.getStrokeWidth());
        }
        ,setColor : function(color) {
            gc.fabric.editor.button.Colored.prototype.setColor.call(this, color);
            this.editor.canvas.freeDrawingBrush.color = color;
        }
        ,setStrokeWidth : function(width) {
            gc.fabric.editor.button.Button.prototype.setStrokeWidth.call(this, width);
            this.editor.canvas.freeDrawingBrush.width = width;
        }
    });

    gc.fabric.editor.button.Rectangle = fabric.util.createClass(gc.fabric.editor.button.Colored, {
        _doClick : function(canvas) {
            var that = this;
            var designer = new gc.fabric.editor.MouseDesigner(
                this.editor,
                function(mouse){
                    return new fabric.Rect({
                        width: 0
                        ,height: 0
                        ,left: mouse.x
                        ,top: mouse.y
                        ,fill : 'transparent'
                        ,stroke: that.getColor()
                        ,strokeWidth: that.getStrokeWidth()
                    });
                },
                function(mouse, object, x, y) {
                    var w = (mouse.x - x)
                        ,h = (mouse.y - y);
                    if (!w || !h) {
                        return false;
                    }
                    object.set('width', w).set('height', h);
                },
                function(object){
                    if (object.get('width') == 0 && object.get('height') == 0) {
                        canvas.remove(object);
                    }
                }
            );
            return designer.start();

//            var coord = gc.fabric.utils.getRandomLeftTop(canvas.width * 0.2, canvas.height * 0.2);
//            var rect = new fabric.Rect({
//                top : coord.top,
//                left : coord.left,
//                width : canvas.width * 0.3,
//                height : canvas.width * 0.3,
//                fill : 'transparent',
//                stroke: this.getColor(),
//                strokeWidth: 5
//            });
//
//            canvas.add(rect);
//            canvas.setActiveObject(rect);
//            $('.move-action', this.editor.$container).trigger('click');
        }
    });

    gc.fabric.editor.button.Text = fabric.util.createClass(gc.fabric.editor.button.Colored, {
        _doClick : function(canvas) {
            var that = this;
            function mouseDown(e) {
                var mouse = canvas.getPointer(e.e);
                var object = new fabric.IText('Ваш тест', {
                    left:mouse.x
                    ,top:mouse.y-30
                    ,stroke:that.getColor()
                    ,fill:that.getColor()
                    ,borderColor:that.getColor()
                    ,cursorWidth : 2
                    ,cursorColor : that.getColor()
                    ,fontSize : 30
                });
                //var border = undefined;
                //object.on('editing:entered', function(o) {
                //   // object.set('textBackgroundColor', 'transparent');
                //    border = new fabric.Rect({
                //        width: object.get('width')
                //        ,height: object.get('height')
                //        ,left: mouse.x
                //        ,top: mouse.y
                //        ,fill : 'transparent'
                //        ,stroke: that.getColor()
                //        ,strokeWidth: that.getStrokeWidth()
                //    })
                //});
                //canvas.on('text:changed', function(o) {
                //    console.log(o);
                //});
                //object.on('editing:exited', function(o) {
                //    object.set('textBackgroundColor', 'transparent');
                //});

                that.editor.addObject(canvas, object);
                object.set('selectable', false);
                //canvas.setActiveObject(object);
                var group = new fabric.Group();
                group.addWithUpdate(object);
                group.removeWithUpdate(object);
                $('.move-action', that.editor.$container).trigger('click');

                canvas.renderAll();
                //$('.text-action', that.editor.$container).trigger('click');
                //object.trigger('click');
            }

            var listeners = {};
            listeners['mouse:up'] = mouseDown;
            for (var event in listeners) {
                canvas.on(event, listeners[event]);
            }
            return listeners;

//            var text = new fabric.IText('             ', {// todo хачина чтобы расширить поле
//                top : canvas.height * 0.2
//                ,left : canvas.width * 0.2
//                ,stroke : this.getColor()
//                ,fill : this.getColor()
//                ,borderColor: this.getColor()
//            });
//            canvas.add(text);
//            canvas.setActiveObject(text);
            //$('.move-action', this.editor.$container).trigger('click');
        }
        ,_doInitSettings : function($settings) {
            gc.fabric.editor.button.Colored.prototype._doInitSettings.call(this, $settings);
            //$settings.append(
            //    '<div class="setting">Цвет: <button class="colpicker" style="border:none;background-color: '+this.getColor()+';width:10px;height:10px;"></button></div>'
            //);
            //var that = this;
            //$('.colpicker', $settings).colpick( {
            //    layout:'hex',
            //    submit:0,
            //    colorScheme:'dark',
            //    onChange:function(hsb,hex,rgb,el,bySetColor) {
            //        $(el).css('background-color','#'+hex);
            //        $(el).colpickHide();
            //        that.setColor('#'+hex);
            //        $('.'+that.getName()+'-action .button-color').css('background-color','#'+hex);
            //    }
            //}).keyup(function(){
            //    $(this).colpickSetColor(this.value);
            //});
        }
    });

    gc.fabric.editor.ButtonGroup = fabric.util.createClass({
        initialize : function(buttons, options) {
            this.buttons = buttons;
            this.options = undefined === options ? {} : options;
        }
    });

    gc.fabric.editor.MouseDesigner = fabric.util.createClass({
        initialize : function(editor, mouseDown, mouseMove, mouseUp) {
            this.editor = editor;
            this.mouseDown = mouseDown;
            this.mouseMove = mouseMove;
            this.mouseUp = mouseUp;
        }
        ,start : function() {
            var started = false
                ,x = 0
                ,y = 0
                ,canvas = this.editor.canvas
                ,that = this;
            function mouseDown(o) {
                var mouse = canvas.getPointer(o.e);
                started = true;
                x = mouse.x;
                y = mouse.y;
                var object = that.mouseDown(mouse);
                that.editor.addObject(canvas, object);
                canvas.renderAll();
                canvas.setActiveObject(object);
            }

            function mouseMove(o) {
                if(!started) {
                    return false;
                }
                var mouse = canvas.getPointer(o.e);
                var object = canvas.getActiveObject();
                var result = that.mouseMove(mouse, object, x, y);
                if (false === result) {
                    return result;
                }
                canvas.renderAll();
            }

            function mouseUp(e) {
                if(started) {
                    started = false;
                }
                var object = canvas.getActiveObject();
                that.mouseUp(object);
                canvas.setActiveObject(object);
                canvas.renderAll();
            }

            var listeners = {};
            listeners['mouse:down'] = mouseDown;
            listeners['mouse:move'] = mouseMove;
            listeners['mouse:up'] = mouseUp;
            for (var event in listeners) {
                canvas.on(event, listeners[event]);
            }
            return listeners;
        }
    });

    gc.fabric.editor.Editor = fabric.util.createClass({
        initialize : function (options) {
            this._init(options);
            this.buttonListeners = {};
        }
        ,_init : function(options) {
            if (options === undefined) {
                throw new Error('Undefined options');
            }
            if (options.id === undefined) {
                throw new Error('Undefined id');
            }
            this.options = options;
            this._initSize();
        }
        ,addButtonListeners : function(listeners) {
            if (listeners === undefined) {
                return;
            }
            for (var event in listeners) {
                this.buttonListeners[event] = listeners[event];
            }
        }
        ,clearButtonListeners : function() {
            for (var event in this.buttonListeners) {
                this.canvas.off(event, this.buttonListeners[event]);
            }
            this.buttonListeners = {};
        }
        ,_initSize : function() {
            var options = this.options.canvasOptions === undefined ? {} : this.options.canvasOptions;
            if (this.options.backgroundImage !== undefined) {
                var id = this.id + 'bgimage';
                $('body').append('<img src="' + this.options.backgroundImage + '" style="display:none;" id="'+id+'">');
                options.backgroundImage = this.options.backgroundImage;
            }
            var tryCount = 10
                ,callCount = 0
                ,$img = $('#' + id)
                ,that = this;
            var interval = setInterval(function(){
                var width = $img.width()
                    ,height = $img.height();
                if (width != 0 || tryCount <= ++callCount) {
                    try {
                        that._initHtml();
                        $('.loader', that.$container).remove();
                        that._applyWidthHeight(width+'px', height+'px');
                        options.width = width;
                        options.height = height;
                        that._initCanvas(options);
                        clearInterval(interval);
                        $img.remove();
                        //that.$container.css('width', width+160+'px');
                        //that.$container.css('width', width + 60 + "px");

                        if ( $(window).width() < 767 ) {
                            that.$container.css('height', 'auto');
                        }
                        else {
                            that.$container.css('height', height + 'px');
                            $('.editor', that.$container).css('height', height+'px');
                        }
                        if (that.options.afterLoadCallback !== undefined) {
                            that.options.afterLoadCallback(that);
                        }
                    }
                    catch (e) {
                        clearInterval(interval);
                        $img.remove();
                        throw e;
                    }
                }
            }, 1000);
        }
        ,_initHtml : function()
        {
            this.$container = $('#'+this.options.id);
            this.$container.addClass('gc-fabric-editor').append('<i class="loader fa fa-spinner fa-spin"></i>');
            var html = [
                '<div class="editor">'
                    ,'<div class="canvas-wrapper">'
                        ,'<canvas id="canvas_'+this.options.id+'"  class="canvas"></canvas>'
                    ,'</div>'
                    ,'<div class="controls">'
                        //,'<div class="settings">'
                        //,'</div>'
                        ,'<div class="buttons">'
                        ,'</div>'
                    ,'</div>'
                    ,'<div class="settings"></div>'
                    ,'<div class="message-block"></div>'
                ,'</div>'
            ];
            this.$container.append(html.join(''));
            this.$canvas = $('#canvas_' + this.options.id);
        }
        ,getButtons : function() {
            return this.options.buttons === undefined ? [] : this.options.buttons;
        }
        ,_initButtons : function(canvas)
        {
            var buttons = this.getButtons()
                ,$buttons = $('.buttons', this.$container)
                ,html = []
                ,that = this
                ,listeners = {}
                ;
            $.each(buttons, function(index, group) {
                html.push('<div class="group">');
                $.each(group.buttons, function(index, button) {
                    html.push(button.getHtml().prop('outerHTML'));
                    button.setEditor(that);
                    listeners['.'+button.getName()+'-action'] = function(){
                        button.click(canvas);
                    };
                });
                html.push('</div>');
            });
            $buttons.append(html.join(''));
            $('.button', this.$container).click(function(){
                $('.button').removeClass('button-active');
                $(this).addClass('button-active');
            });

            for(var selector in listeners) {
                $(selector, this.$container).click(listeners[selector]);
            }
        }
        ,_initCanvas : function(options) {
            this.canvas = new fabric.Canvas(
                'canvas_'+this.options.id,
                options
            );
//                function onObjectSelected(e) {
//                    console.log(e.target);
//                }
//                this.canvas.on('object:selected', onObjectSelected);

            this._initButtons(this.canvas);
        }
        ,_applyWidthHeight : function(width, height) {
            this.$canvas.css('width', width);
            this.$canvas.css('height', height);
            //this.$canvas.parent().css('width', width);
            this.$canvas.parent().css('height', height);
        }
        ,removeSelectedGroup : function() {
            var that = this;
            if(this.canvas.getActiveGroup()){
                this.canvas.getActiveGroup().forEachObject(function(o){ that.canvas.remove(o) });
                this.canvas.discardActiveGroup().renderAll();
            } else {
                this.canvas.remove(this.canvas.getActiveObject());
            }
        }
        ,addObject : function(canvas, object) {
            object.set('selectable', false);
            canvas.add(object);
        }
        ,lockObjects : function() {
            var objects = this.canvas.getObjects();
            for (var index in objects) {
                objects[index].set('selectable', false);
            }
        }
        ,unlockObjects : function() {
            var group = new fabric.Group();
            this.canvas.forEachObject(function(o, i) {
                o.set('selectable', true);
                group.addWithUpdate(o);// todo хачина, без добавления в группу не получается выделить объект, видимо еще какое то свойство надо обновить
                group.removeWithUpdate(o);
            });
        }
        ,showMessage : function(message) {
            var $messageBlock = $('.message-block', this.$container);
            $messageBlock.html(message);
            $messageBlock.show(500);
            setTimeout(function() {
                $messageBlock.hide(500);
            }, 1500);
        }
    });

    jQuery.widget('gc.imageEditor', {
        _create: function () {
            var editor = new gc.fabric.editor.Editor({
                id : this.options.id
                ,backgroundImage : this.options.backgroundImage
                ,afterLoadCallback : this.options.afterLoadCallback
                ,buttons : [
                    new gc.fabric.editor.ButtonGroup([
                        new gc.fabric.editor.button.Move({
                            name:'move'
                            ,icons: ['fa-arrows']
                            ,isActive : true
                        })
                        ,new gc.fabric.editor.button.Remove({
                            name:'remove'
                            ,icons: ['fa-trash-o']
                        })
                        ,new gc.fabric.editor.button.Clear({
                            name:'clear'
                            ,icons: ['fa-trash']
                        })
                    ])
                    ,new gc.fabric.editor.ButtonGroup([
                        new gc.fabric.editor.button.Rectangle({
                            name:'rect'
                            ,icons: ['fa-square-o']
                            ,strokeWidthEditable : true
                        })
                        ,new gc.fabric.editor.button.Ellipse({
                            name:'ellipse'
                            ,icons: ['fa-circle-o']
                            ,strokeWidthEditable : true
                        })
                        ,new gc.fabric.editor.button.Arrow({
                            name:'arrow'
                            ,icons: ['fa-long-arrow-right']
                            ,strokeWidthEditable : true
                        })
                        ,new gc.fabric.editor.button.Line({
                            name:'line'
                            ,icons: ['fa-minus']
                            ,strokeWidthEditable : true
                        })
                        ,new gc.fabric.editor.button.Pencil({
                            name:'pencil'
                            ,icons: ['fa-pencil']
                            ,isDrawingMode : true
                            ,strokeWidthEditable : true
                        })
                        ,new gc.fabric.editor.button.Text({
                            name:'text'
                            ,icons: ['fa-file-text-o']
                        })
                    ])
                ]
            });
        }
    } );
});
