/**
 * Functions for adding an autocompleting text field for user searches.
 * Hides any form elements with "user" or "group" as their ID, replacing
 * the "user" field with the autocompleting text box.
 *
 * The arguments for the ajax_user_search function are as follows:
 *   searchServiceUrl: a string containing the url for the user search service
 *   groups: a boolean indicating whether to include (true), or exclude (false)
 *           groups in the search results. The default value is true.
 */

(function( $ ){
    $.fn.ajax_user_search = function(searchServiceUrl, groups) {
        if(groups == false) {
            searchServiceUrl += "?groups=False";
        }
        $("#id_user, ").parent().hide().parent().append("<div id=\"selector\"><input type=\"text\"/></div>");
        $("#id_group, ").parent().parent().hide();
        $("#selector input").autocomplete({
            serviceUrl:searchServiceUrl,
            minChars:2,
            maxHeight:400,
            width:300,
            zIndex: 9999,
            noCache: false, //default is false, set to true to disable caching
            onSelect: select_value,
            fnFormatResult:format_search_result,
            fnDeselect:deselect_value
        });
    };
})( jQuery );

    
function deselect_value(){
    $("#id_user").val('');
    $("#id_group").val('');
    $("#selector").removeClass('user').removeClass('group');
}

function select_value(value, data) {
    var type = data[0];
    var id = data[1];
    if (type=="user"){
        $("#selector")
            .removeClass('group')
            .addClass(type);
        $("#id_user").val(id);
          $("#id_group").val('');
    } else {
        $("#selector")
            .removeClass('user')
             .addClass(type);
        $("#id_group").val(id);
        $("#id_user").val('');
    }
    $("#selector input").val(value);
}

var reEscape = new RegExp('(\\' + ['/', '.', '*', '+', '?', '|', '(', ')', '[', ']', '{', '}', '\\'].join('|\\') + ')', 'g');
function format_search_result(value, data, currentValue) {
    var type = data[0];
    var id = data[1];
    var pattern = '(' + currentValue.replace(reEscape, '\\$1') + ')';
    value = value.replace(new RegExp(pattern, 'gi'), '<strong>$1<\/strong>');

    return "<div class='search_result "+type+"'>"+value+"</div>";
}
