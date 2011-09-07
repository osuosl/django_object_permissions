//* autocomplete_user_search creates an autocompleting search box for selecting users or groups
//* It replaces one or more existing selection fields, importing various attributes from the originals
//*
//*     Arguments:
//* search_box is the jquery object that will be replaced by the new search box
//* search_url is a url that returns search suggestions given the user-given search tem
//* handlers is an object of the format {'userTypeToHandle':$('jqueryObjectToHandleThatType'),etc:etc}
//*     and is used in the event that the search needs to encompass more than one existing selector field
//*     where each listed jquery object will be used when selecting a user of the corresponding type

function autocomplete_user_search(search_box, search_url, handlers) {
    
    function deselectOption()
    {   $("#selector").removeClass("user").removeClass("group").removeClass("other");
        search_box.val(0);
        for(type in handlers)
        {   handlers[type].val(0);
        }
    } 

    function selectOption(value, type, id)
    {   deselectOption(); 
        $("#selector").addClass(type);
        $("#selector input").val(value);
        
        if(handlers && handlers[type]) 
        {   handlers[type].children("option:contains('"+value+"')").attr("selected", "selected");
        }
        else if(handlers)
        {   search_box.children("option:contains('"+value+"')").attr("selected", "selected");
        }
        else
        {   search_box.val(id);
        }
    }
    
    // Hide the primary search box, leaving its parent visible
    // Then create the autocompleting search box using the old search box's attributes
    search_box.hide().parent().append("<span id=\"selector\"><input type=\"text\"/></span>");
    $("#selector input").attr("id",search_box.attr("id")).attr("name",search_box.attr("name")+"_");

    // Move the label, if any, inside the span so that it can apply to the new search box 
    $("#selector").prepend($("label[for=\""+search_box.attr("id")+"\"]"));
    search_box.attr("id", search_box.attr("id")+"-hidden"); 

    // Hide the parent container for each secondary search box that the new box is replacing
    for(type in handlers)
    {   handlers[type].parents("."+type).hide();
    }

    // Create, initialize, and manage the new autocompleting search field
    if( search_box.val() > 0 )
    {   selectOption( search_box.find("option:selected").text(), "other", search_box.val() );
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
                        {   selectOption(data.results[0][0], data.results[0][1], data.results[0][2]); 
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
                selectOption(ui.item.value, ui.item.type, ui.item.id);
                first = null;            
            }

    }).keydown(function(event){
            if( first && event.keyCode == 9 )
            {   selectOption( first[0], first[1], first[2]);
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
