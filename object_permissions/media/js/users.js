/**
 * Javascript for object user's view
 */
$(document).ready(function() {
    // unbind all functions, this ensures that they are never bound more
    // than once.  This is a problem when using jquery ajax tabs
    $('#add_user').unbind();
    $('.object_permissions_form .submit').die();
    $('.user .delete').die();
    $('.group .delete').die();
    $('.permissions').die();
    
    // Add user button
    $('#add_user').click(function(){
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
            api:{onShow:function(){
                $(".object_permissions_form input[type!=hidden], .object_permissions_form select").first().focus();
                bind_user_perm_form();
            }}
        });
    });
    
    // form submit button
    function bind_user_perm_form() {
        $(".object_permissions_form").submit(function(){
            $("#errors").empty();
            $(this).ajaxSubmit({success: update_user_permissions});
            return false;
        });
    }
    
    // Delete user button
    $('.user .delete').live("click", function() {
        name = $(this).parent().parent().children('.name').html();
        if (confirm("Remove this user: " + name)) {
            $('.qtip').qtip('destroy');
            id = this.parentNode.parentNode.id.substring(5);
            data = {user:id, permissions:[], obj:obj_id};
            $.post(user_url, data,
                function(code){
                    type = typeof code
                    if (type=="string") {
                        $("#user_" + id).remove();
                    }
                },
                "json");
        }
    });
    
    // Delete group button
    $('.group .delete').live("click", function() {
        name = $(this).parent().parent().children('.name').html();
        if (confirm("Remove this group: "+ name)) {
            id = this.parentNode.parentNode.id.substring(6);
            data = {group:id, permissions:[], obj:obj_id};
            $.post(user_url, data,
                function(code){
                    type = typeof code
                    if (type=="string") {
                        $("#group_" + id).remove();
                    }
                },
                "json");
        }
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
            position: {corner:{ target:"rightMiddle", tooltip:"leftMiddle"}},
            style: {name: 'dark', border:{radius:5}, width:400, background:'#eeeeee', tip: 'leftMiddle'},
            show: {when:false, ready:true},
            hide: {fixed: true, when:false},
            api:{onShow:function(){
                $(".object_permissions_form input[type!=hidden], .object_permissions_form select").first().focus();
                bind_user_perm_form();
            }}
        });
        return false;
    });
});

function update_user_permissions(responseText, statusText, xhr, $form) {
    if (xhr.getResponseHeader('Content-Type') == 'application/json') {
        type = typeof responseText;
        if (type == 'string') {
            // 1 code means success but no more permissions
            $('.qtip').qtip('hide');
            $("#op_users #" + responseText).remove();
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
        $row = $('#op_users #' + id);
        if ($row.length == 1) {
            $row.replaceWith(html);
        } else {
            $("#op_users").append(html);
        }
    }
}