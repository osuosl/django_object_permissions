// Add object button
$('.button.add.permission').click(function(){
    $('.qtip').qtip('destroy');
    $(this).qtip({
        content: {
           url: this.href,
           title: {text:'Add Object: ', button:'close'}
        },
        position: {  corner:{target:'center', tooltip:'center'}},
        style: {name: 'dark', border:{radius:5}, width:400, background:'#eeeeee'},
        show: {when:false, ready:true},
        hide: {fixed: true, when:false},
        api:{onShow:function(){
            $(".object_permissions_form input[type!=hidden], .object_permissions_form select").first().focus();
            bind_form();
        }}
    });
    return false;
});

function bind_form(){
    // form submit button
    $(".object_permissions_form").submit(function(){
        $("#errors").empty();
        $(this).ajaxSubmit({success: update_object_permission});
        return false;
    });
}

// Delete user button
$('.object_permissions .delete').live("click", function() {
    class_name = this.parentNode.parentNode.parentNode.parentNode.id;
    name = $(this).parent().parent().children('.obj').html();
    if (confirm("Remove this " + class_name +": "+ name)) {
        $('.qtip').qtip('destroy');
        id = this.parentNode.parentNode.id;
        id = id.substring(id.lastIndexOf('_')+1);
        data = {permissions:[], obj:id};
        if (is_user) {
            data['user'] = persona_pk;
        } else {
            data['group'] = persona_pk;
        }
        href = $(this).children('a').attr('href');
        $.post(href, data, update_object_permission, "json");
    }
    return false;
});

function update_object_permission(responseText, statusText, xhr, $form) {
    if (xhr.getResponseHeader('Content-Type') == 'application/json') {
        type = typeof responseText;
        if (type == 'string') {
            // 1 code means success but no more permissions
            $('.qtip').qtip('hide');
            $("#" + responseText).remove();
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
        $row = $('#' + id);
        if ($row.length == 1) {
            $row.replaceWith(html);
        } else {
            class_name = id.substring(0, id.lastIndexOf('_'));
            $("#" + class_name).append(html);
        }
    }
}

$('table.permissions tr td.perms a').live('click', function(){
    // destroy old qtip before showing new one
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
        api:{onShow:function(){
            $(".object_permissions_form input[type!=hidden], .object_permissions_form select").first().focus();
            bind_form();
        }}
    });
    return false;
});