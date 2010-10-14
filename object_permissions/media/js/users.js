/**
 * Javascript for object user's view
 */
$(document).ready(function() {
    // unbind all functions, this ensures that they are never bound more
    // than once.  This is a problem when using jquery ajax tabs
    $('#add_user').unbind();
    $('.ajax_form .submit').die();
    $('.user .delete').die();
    $('.group .delete').die();
    $('.permissions').die();
    
    // Add user button
    $('#add_user').click(function(){
        $('.qtip').qtip('destroy');
        $(this).qtip({
            content: {
               url: user_url,
               title: {text:'Add User', button:'close'}
            },
            position: {  corner:{target:'center', tooltip:'center'}},
            style: {name: 'blue', border:{radius:5}},
            show: {when:false, ready:true},
            hide: {fixed: true, when:false}
        });
    });
    
    // Add user submit button
    $(".ajax_form .submit").live("click", function(){
        $("#errors").empty();
        $(this).parent(".ajax_form").ajaxSubmit({success: update});
    });
    
    // Delete user button
    $('.user .delete').live("click", function() {
        $('.qtip').qtip('destroy');
        id = this.parentNode.parentNode.id.substring(5);
        data = {user:id, permissions:[]};
        $.post(user_url, data,
            function(code){
                if (code==1) {
                    $("#user_" + id).remove();
                }
            },
            "json");
    });
    
    // Delete group button
    $('.group .delete').live("click", function() {
        $('.qtip').qtip('destroy');
        id = this.parentNode.parentNode.id.substring(6);
        data = {group:id, permissions:[]};
        $.post(user_url, data,
            function(code){
                if (code==1) {
                    $("#group_" + id).remove();
                }
            },
            "json");
    });
    
    // Update Permission Button
    $(".permissions").live("click", function() {
        // destroy old qtip before showing new one
        $('.qtip').qtip('destroy');
        $(this).qtip({
            content: {
               url: this.href,
               title: {text:'Permissions: ', button:'close'}
            },
            position: {corner:{ target:"topMiddle", tooltip:"bottomMiddle"}},
            style: {name: 'blue',
                    border:{radius:5},
                    width:200,
                    tip: 'bottomMiddle'
                    },
            show: {when:false, ready:true},
            hide: {fixed: true, when:false}
        });
        return false;
    });
});

function update(responseText, statusText, xhr, $form) {
    if (xhr.getResponseHeader('Content-Type') == 'application/json') {
        if (responseText == 1) {
            // 1 code means success but no more permissions
            if (no_perms != undefined && no_perms) {
                $('.qtip').qtip('hide');
                $("#users #" + html.attr('id')).remove();
            }
        } else {
            // parse errors
            errors = responseText
            for (key in errors) {
                $("#errors").append("<li>"+ errors[key] +"</li>")
            }
        }
    } else {
        // successful permissions change.  replace the user row with the
        // newly rendered html
        $('.qtip').qtip('hide');
        html = $(responseText);
        id = html.attr('id')
        $row = $('#users #' + id);
        if ($row.length == 1) {
            $row.replaceWith(html);
        } else {
            $("#users").append(html);
        }
    }
}