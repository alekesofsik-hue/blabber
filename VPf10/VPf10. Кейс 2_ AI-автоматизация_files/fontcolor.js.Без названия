if (!RedactorPlugins) var RedactorPlugins = {};

RedactorPlugins.fontcolor = function()
{
    return {
        init: function() {

            var buttons = {
                fontcolor: {name: 'fontcolor', icon: 'fa-pencil', property: 'color'},
                backcolor: {name: 'backcolor', icon: 'fa-paint-brush', property: 'background-color'}
            };

            var self = this;

            for (var i in buttons) {
                var button = this.button.addAfter('link', i, this.lang.get(i));

                this.button.setIcon(button, '<i class="fa ' + buttons[i].icon + '"></i></i>');

                this.button.addCallback(button, function (button) {
                    $(self.button.get(button)).colpick({
                        submit: 0,
                        onChange: function(hsb, hex) {
                            self.fontcolor.set(buttons[button].property, '#' + hex);
                        }
                    });
                });
            }
        },
        set: function(rule, type) {
            if (rule == 'color') {
                this.inline.format('span', 'style', rule + ':' + type, 'add');
            } else if (rule == 'background-color') {
                this.inline.format('span', 'style', rule + ':' + type, 'add');
            }

        },
        remove: function(rule) {}
    };
};
