$(function(){
    // Update Permission Button
    $("#op_users .permissions").live("click", function(event) {
        event.preventDefault();
        var id = this.parentNode.parentNode.id.substring(5);
        var name = $(this).parent().parent().children('.name');
        if (name.children('a').size() > 0) {
            name = name.children('a').html();
        } else {
            name = name.html();
        }
        $('.qtip').qtip('destroy');
        $(this).qtip({
            content: {
               url: this.href,
               title: {text:'Permissions: '+name, button:'close'}
            },
            position: {target:$("body"), corner:{ target:"center", tooltip:"center"}},
            style: {name: 'dark', border:{radius:5}, width:400, background:'#eeeeee', tip: false},
            show: {when:false, ready:true},
            hide: {fixed: true, when:false},
            api:{onShow:function(){
                $(".ajax_form input[type!=hidden], .ajax_form select").first().focus();

                // submit button
                $(".object_permissions_form").submit(function(event){
                    event.preventDefault();
                    $("#errors").empty();
                    $(this).ajaxSubmit({success:
                        function update_group_user_permissions(responseText, statusText, xhr, $form) {
                            if (xhr.getResponseHeader('Content-Type') == 'application/json') {
                                // parse errors
                                for (var key in responseText) {
                                    $("#errors").append("<li>"+ responseText[key] +"</li>")
                                }
                            } else {
                                // successful permissions change.  replace the permissions cell with the
                                // newly rendered html
                                $('.qtip').qtip('hide');
                                var $td = $('#op_users #user_' + id + ' .permissions');
                                $td.replaceWith(responseText);
                            }
                        }
                    });
                });
            }}
        });
        return false;
    });
});