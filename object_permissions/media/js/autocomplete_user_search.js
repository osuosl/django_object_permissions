//* search_box is the jquery object to replace with the search box, and the default handler
//* search_url is the url of the search function
//* handlers is an object of the format {'userTypeToHandle':$('jqueryObjectToHandleThatType'),etcetc}

function autocomplete_user_search(search_box, search_url, handlers) {
    
    function selectOption(value, type)
    {   
        $("#selector").removeClass("user").removeClass("group").removeClass("other");
        $("#selector").addClass(type);
        $("#selector input").val(value);
        
        if(handlers && handlers[type]) 
        {   handlers[type].children("option:contains('"+value+"')").attr("selected", "selected");
        }
        else
        {   search_box.children("option:contains('"+value+"')").attr("selected", "selected");
        }
    }

    function deselectOption()
    {   $("#selector").removeClass("user").removeClass("group").removeClass("other");
        search_box.val(0);
        for(type in handlers)
        {   handlers[type].val(0);
        }
    } 
    
    // Hide the primary search box, leaving its parent visible
    // Then hide the parent element with class equal to each handler type
    search_box.hide().parent().append("<span id=\"selector\"><input type=\"text\" name=\""+search_box.attr("name")+"_\"/></span>");
    for(type in handlers)
    {   handlers[type].parents("."+type).hide();
    }
    if( search_box.val() > 0 )
    {   selectOption( search_box.find("option:selected").text(), "other" );
    }
    var first = null; 
    $("#selector input").autocomplete({
            source: function(request, response) {
                $.getJSON(search_url,{
                        term: request.term
                    }, 
                    function(data) {
                        first = data.results[0];
                        
                        if(data.results[0] && !data.results[1] && data.query.toLowerCase() == data.results[0][0].toLowerCase())
                        {   selectOption(data.results[0][0], data.results[0][1]); 
                        } 
                        else
                        {   deselectOption();
                        }
                        response($.map(data.results, function(item) {
                            return {
                                term: data.query,
                                value: item[0],
                                type: item[1],
                                id: item[2]
                            };
                        }));
                    }
                );
            },
            select: function(event, ui) { 
                selectOption(ui.item.value, ui.item.type);
                first = null;            
            }

    }).keydown(function(event){
            if( first && event.keyCode == 9 )
            {   selectOption( first[0], first[1] );
            }        

    }).data("autocomplete")._renderItem = function(ul, item){
            var type = item.type;
            var value = item.value;
            return $("<li></li>")
            .data("item.autocomplete", item)
            .append("<a><div class='search_result "+type+"'>"+value+"</div></a>")
            .appendTo(ul);
    };
};
