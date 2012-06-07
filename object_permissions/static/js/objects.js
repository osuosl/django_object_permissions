var is_user;
var persona_pk;

$(function(){
    // Add object button
    $('.button.add.permission').click(function(event){
        event.preventDefault();

        // Check for specific object type, or use default "Add Object" instead
        // Uses the id of the next permissions table (if any) as the object type
        var permissions_table = $(this).next("table.permissions");
        var qtip_header = "Add Object: ";
        if (permissions_table) {
            qtip_header = "Add " + permissions_table.attr("id") + ": ";
        }
        
        $('.qtip').qtip('destroy');
        $(this).qtip({
            content: {
               url: this.href,
               title: {text:qtip_header, button:'close'}
            },
            position: {  corner:{target:'center', tooltip:'center'}},
            style: {name: 'dark', border:{radius:5}, width:400, background:'#eeeeee'},
            show: {when:false, ready:true},
            hide: {fixed: true, when:false},
            api:{onContentLoad:function(){
                $(".object_permissions_form input[type!=hidden], .object_permissions_form select").first().focus();
            }}
        });
    });

    $(".object_permissions_form").live('submit', function(event){
        event.preventDefault();
        $("#errors").empty();
        $(this).ajaxSubmit({success: update_object_permission});
    });

    // Delete user button
    $('.object_permissions .delete').live("click", function(event) {
        event.preventDefault();
        var class_name = this.parentNode.parentNode.parentNode.parentNode.id;
        var name = $(this).parent().parent().children('.obj');
        if (name.children('a').size() > 0) {
            name = name.children('a').html();
        } else {
            name = name.html();
        }
        if (confirm("Remove this " + class_name +": "+ name)) {
            $('.qtip').qtip('destroy');
            var id = this.parentNode.parentNode.id;
            id = id.substring(id.lastIndexOf('_')+1);
            var data = {obj:id};
            if (is_user) {
                data['user'] = persona_pk;
            } else {
                data['group'] = persona_pk;
            }
            var href = $(this).children('a').attr('href');
            $.post(href, data, update_object_permission, "json");
        }
    });

    function update_object_permission(responseText, statusText, xhr, $form) {
        if (xhr.getResponseHeader('Content-Type') == 'application/json') {
            var type = typeof responseText;
            if (type == 'string') {
                // 1 code means success but no more permissions
                $('.qtip').qtip('hide');
                $("#" + responseText).remove();
            } else {
                // parse errors
                for (var key in responseText) {
                    $("#errors").append("<li>"+ responseText[key] +"</li>")
                }
            }
        } else {
            // successful permissions change.  replace the user row with the
            // newly rendered html
            $('.qtip').qtip('hide');
            var html = $(responseText);
            var id = html.attr('id');
            var $row = $('#' + id);
            if ($row.length == 1) {
                $row.replaceWith(html);
            } else {
                var class_name = id.substring(0, id.lastIndexOf('_'));
                $("#" + class_name).append(html);
            }
        }
    }

    $('table.permissions tr td.perms a').live('click', function(event){
        // destroy old qtip before showing new one
        event.preventDefault();
        $('.qtip').qtip('destroy');
        $(this).qtip({
            content: {
               url: this.href,
               title: {text:'Permissions: ', button:'close'}
            },
            position: {corner:{ target:"topMiddle", tooltip:"bottomMiddle"}},
            style: {name: 'dark', border:{radius:5}, width:400, background:'#eeeeee', tip: 'bottomMiddle'},
            show: {when:false, ready:true},
            hide: {fixed: true, when:false},
            api:{onContentLoad:function(){
                $(".object_permissions_form input[type!=hidden], .object_permissions_form select").first().focus();
            }}
        });
    });
});
