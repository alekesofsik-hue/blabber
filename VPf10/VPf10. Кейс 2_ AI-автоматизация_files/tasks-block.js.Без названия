var TasksBlock = React.createClass({displayName: "TasksBlock",
    getInitialState: function() {
        return {
            loaded: false,
            opened: false,
            data: {}
        }
    },
    render: function() {
        if ( ! this.state.loaded ) {
            return null;
        }
        if ( ! this.state.data.totalTasksCount || this.state.data.totalTasksCount == 0 ) {
            return null;
        }

        if ( $('.top-notification').length > 0 ) {
            return null;
        }

        var tasksBlocks = [];
        var groupLabels = []
        var i = 0;
        var linkToAllBlock = "";
        var stop = false;

        for ( key in this.state.data.groups ) {
            var groupData = this.state.data.groups[key]
            if ( groupData.tasksCount <= 0 ) {
                continue;
            }
            groupLabels.push( groupData.tasksCountLabel )
            if ( stop ) {
                            break;
                        }

            tasksBlocks.push(
                React.createElement("div", {className: "tasks-group-label"}, 
                    groupData.groupLabel
                )
            )
            for( taskKey in groupData.tasks ) {
                i++;
                if ( i > 5 ) {
                    linkToAllBlock = (
                        React.createElement("a", {href: "/pl/tasks/task/my", className: "all-tasks-link-block"}, 
                            window.tt('common', 'All active tasks')
                        )
                    );
                    stop = true;
                    break;
                }

				var managerLabel = 'менеджер';
				var expiredLabel = 'Просрочена';
				var closeLabel = 'Завершить';
				if (typeof Yii != 'undefined') {
					managerLabel = Yii.t('common', managerLabel);
					expiredLabel = Yii.t('common', expiredLabel);
					closeLabel = Yii.t('common', closeLabel);
				}
                var taskData = groupData.tasks[taskKey];
                if(taskData.normal_time_expired === null) {
                    taskData.normalTimeStatus = "";
                    taskData.normalTimeText = "";
                    taskData.normalTime = "";
                }else if (taskData.normal_time_expired < 0) {
                    taskData.normalTime = "normal-time";
                    taskData.normalTimeStatus = "expired";
                    taskData.normalTimeText = expiredLabel + " " + taskData.normal_time_expired_at;
                }else{
                    taskData.normalTime = "normal-time";
                    taskData.normalTimeStatus = "not-expired";
                    taskData.normalTimeText = closeLabel + " " + taskData.normal_time_expired_at;
                }
                tasksBlocks.push(
                    React.createElement("a", {className: "task-block " + taskData.normalTime + " " + taskData.normalTimeStatus, "data-url": taskData.url, href: taskData.url}, 
                        React.createElement("div", {className: "image"}, React.createElement("img", {src: taskData.image_url})), 
                        React.createElement("div", {className: "status-wrapper"}, 
                            React.createElement("div", {className:  "label label-" + taskData.status_class}, taskData.status_label)
                        ), 
                        React.createElement("div", {className: "task-text-data"}, 
                            React.createElement("div", {className: "object-name small text-muted"}, taskData.object_name), 
                            React.createElement("div", {className: "title"}, taskData.title), 
                            React.createElement("div", {className: "manager-name"}, managerLabel + ": ", taskData.manager_user_name),
                            React.createElement("div", {className:  "expired-time"}, taskData.normalTimeText)
                        )
                    )
                )
            }
        }

        var tasksCountLabel = [];
        for ( key in groupLabels ) {
            var val = groupLabels[key]
            tasksCountLabel.push(
                React.createElement("div", null, 
                    val
                )
            )
        }

        return (
            React.createElement("div", {className:  "gc-tasks-block " + ( this.state.opened ? "opened" : "closed") }, 
                React.createElement("div", {className: "annotate-block", onClick: this.handleClickAnnotate}, 
                    tasksCountLabel
                ), 
                React.createElement("div", {className: "tasks-block"}, 
                    tasksBlocks, 
                    linkToAllBlock
                )
            )
        );
    },
    handleTaskClick: function( url ) {
        location.href = url;
    },
    componentDidMount: function() {
        this.loadNotifications();
    },
    handleClickAnnotate: function() {
        var self = this;
        if ( ! this.state.opened && ! this.windowClickHandler ) {
            this.loadTasksData( function() {

                $(window).click( function(e) {
                    if ( self.state.opened && $(e.target).parents('.gc-tasks-block').length == 0 ) {
                        self.setState({opened: false});
                    }
                });
                this.windowClickHandler = true;
                self.setState( { opened: ! self.state.opened });
            })

        }
        else {
            this.setState( { opened: ! this.state.opened });
        }

    },
    loadTasksData: function( callback ) {
        var self = this;
        if ( ! this.state.data.tasks ) {
            ajaxCall( "/pl/tasks/task/get-data?full=1", {}, {}, function( response ) {
                console.log( response )
                data = response.data;
                self.setState( {data: data } )
                callback();
            } );

        } else {
            callback();
        }
    },
    loadNotifications: function() {
        var self = this;
        ajaxCall( "/pl/tasks/task/get-data", {}, {}, function( response ) {
            newParams = {}
            newParams.loaded = true;
            newParams.data = response.data;
            self.setState( newParams )
        } );
    },
    refresh: function() {
        this.loadNotifications();
    }
});

$( function() {
    if ( window.disableTasksBlock ) {
        return false;
    }
    if ( $(window).width() < 700 ) {
        return false;
    }

    var $blockEl = $("<div></div>")
    $blockEl.appendTo ( $(document.body) );
    if ( window.userInfo.isAdmin || window.userInfo.isManager || window.userInfo.canViewTasksBlock ) {
        window.tasksBlockComponent = React.render(
            React.createElement(TasksBlock, {params: window.activeBlockMenu}), $blockEl.get(0)
        );
    }
});
