/**
 * Javascript for object user's view
 */
var user_url;
var obj_id;

$(document).ready(function() {
    // unbind all functions, this ensures that they are never bound more
    // than once.  This is a problem when using jquery ajax tabs that do not cache
    $('#add_user').unbind();
    $('.object_permissions_form .submit').die();
    $('.user .delete').die();
    $('.group .delete').die();
    $('.permissions').die();
    
    // Add user button
    $('#add_user').click(function(event){
        event.preventDefault();
        $('.qtip').qtip('destroy');
        $(this).qtip({
            content: {
               url: user_url,
               title: {text:'Add User: ', button:'close'}
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
    
    // form submit button
    $(".object_permissions_form").live("submit", function(event){
        event.preventDefault();
        $("#errors").empty();
        $(this).ajaxSubmit({success: update_user_permissions});
    });

    // Delete user button
    $('.user .delete').live("click", function(event) {
        event.preventDefault();
        var name = $(this).parent().parent().children('.name');
        if (name.children('a').size() > 0) {
            name = name.children('a').html();
        } else {
            name = name.html();
        }
        if (confirm("Remove this user: " + name)) {
            $('.qtip').qtip('destroy');
            var id = this.parentNode.parentNode.id.substring(5);
            var data = {user:id, obj:obj_id};
            $.post(user_url, data,
                function(code){
                    var type = typeof code;
                    if (type=="string") {
                        $("#user_" + id).remove();
                    }
                },
                "json");
        }
    });
    
    // Delete group button
    $('.group .delete').live("click", function(event) {
        event.preventDefault();
        var name = $(this).parent().parent().children('.name');
        if (name.children('a').size() > 0) {
            name = name.children('a').html();
        } else {
            name = name.html();
        }
        if (confirm("Remove this group: "+ name)) {
            var id = this.parentNode.parentNode.id.substring(6);
            var data = {group:id, obj:obj_id};
            $.post(user_url, data,
                function(code){
                    var type = typeof code;
                    if (type=="string") {
                        $("#group_" + id).remove();
                    }
                },
                "json");
        }
    });
    
    // Update Permission Button
    $(".permissions a").live("click", function(event) {
        event.preventDefault();
        // destroy old qtip before showing new one
        $('.qtip').qtip('destroy');
        $(this).qtip({
            content: {
               url: this.href,
               title: {text:'Permissions: ', button:'close'}
            },
            position: {corner:{ target:"rightMiddle", tooltip:"leftMiddle"}},
            style: {name: 'dark', border:{radius:5}, width:400, background:'#eeeeee', tip: 'leftMiddle'},
            show: {when:false, ready:true},
            hide: {fixed: true, when:false},
            api:{onContentLoad:function(){
                $(".object_permissions_form input[type!=hidden], .object_permissions_form select").first().focus();
            }}
        });
    });
});

function update_user_permissions(responseText, statusText, xhr, $form) {
    if (xhr.getResponseHeader('Content-Type') == 'application/json') {
        var type = typeof responseText;
        if (type == 'string') {
            // 1 code means success but no more permissions
            $('.qtip').qtip('hide');
            $("#op_users #" + responseText).remove();
        } else {
            // parse errors
            for (var key in responseText) {
                $("#errors").append("<li>"+ responseText[key] +"</li>");
            }
        }
    } else {
        // successful permissions change.  replace the user row with the
        // newly rendered html
        $('.qtip').qtip('hide');
        var html = $(responseText);
        var id = html.attr('id');
        var $row = $('#op_users #' + id);
        if ($row.length == 1) {
            $row.replaceWith(html);
        } else {
            $("#op_users").append(html);
        }
    }
}
