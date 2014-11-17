// this is a test

console.log('shopping test');

var un = $('ul#identity > li.user_name > a').text();

if ( !un ) {
    console.log('-----> user is not logged in');

} else {
    var shopping_tool_url = "http://localhost.harvard.edu:8001/tools/shopping";
    console.log('-----> user is logged in - username is ' + un);
    page_url = window.location;
    
    var pat = /\/courses\/(\d+)/g;
    var match = pat.exec(page_url);
    if (match) {
        course_id = match[1];
        console.log('-----> course id is ' + course_id);
        user_enrolled = false;
        user_can_shop = false;
        is_shopper = false;
        is_viewer = false;
        course_is_active = false;
        user_role = '';
        
        /*
        Check to see the course is in the 'available' state before showing
        the shopping button.
        */
        
        url = "/api/v1/courses/"+course_id;
        $.getJSON(url, function( data ) {
            course_workflow = data['workflow_state'];
            if(course_workflow.localeCompare('available') == 0) {
                console.log('course '+course_id+' is active');
                    c_id = data['id'];
                    if ( course_id == c_id ) {
                        console.log('MATCH! User is already enrolled in this course. Are they a shopper?');
                    
                        // check for shopper
                        var num_enrollments = data['enrollments'].length;
                    
                        for (var n = 0; n < num_enrollments; n++) {
                            var etype = data['enrollments'][n]['type'];
                            var erole = data['enrollments'][n]['role'];
                            console.log('Type/role is ' + etype + '/' + erole);
                            if ( erole == 'Shopper' ) {
                                is_shopper = true;
                                user_enrolled = true;
                            }
                            if ( erole == 'Harvard-Viewer' ) {
                                is_viewer = true;
                                user_enrolled = true;
                            }
                        }
                    } else {
                        console.log('This course ' + course_id + ' does not match ' + c_id);
                    }
    
                console.log('-----> user enrolled: ' + user_enrolled);
            
                /*
                If the user is not enrolled, they will be shown the shopping button.
                If the user is enrolled as a Harvard-Viewer, they will be shown the shopping button.
                If the user is enrolled as a Shopper, the will be shown the remove shopping button.
                */
                if ( user_enrolled ) {
                    var rightbar = $('div#content');
                    if ( is_shopper ) {
                        console.log('-----> Shopping! display UNshop' );
                        // add content inside of aside#right-side
                        var shoplink = '<div class="center-button"><a href="'+shopping_tool_url+'/remove_shopper_role/'+course_id+'" class="btn btn-danger">You\'re Shopping this course Stop Shopping</a></div>';
                        rightbar.prepend(shoplink);
                    }
                    else if ( is_viewer ) {
                        console.log('-----> Viewing! display shopping button' );
                        var shoplink = '<div class="center-button"><a href="'+shopping_tool_url+'/shop_course/'+course_id+'" class="btn btn-danger">Shop this course</a></div>';
                        rightbar.prepend(shoplink);
                    }
                    $("#menu").append('<li id="shopping_menu_item" class="menu-item"><a class="menu-item-no-drop" href="'+shopping_tool_url+'/my_list">Manage Shopping</a></li>');

                } else {
                    console.log('-----> display the shopping button 2');
                    // add content inside of aside#right-side
                    var rightbar = $('div#content');
                    var shoplink = '<div class="center-button"><a href="'+shopping_tool_url+'/shop_course/'+course_id+'" class="btn btn-danger">Shop this course</a></div>';
                    rightbar.prepend(shoplink);
                    //$("#menu").append('<li id="shopping_menu_item" class="menu-item"><a class="menu-item-no-drop" href="'+shopping_tool_url+'/my_list">Manage Shopping</a></li>');
                }
                $('.center-button').css('text-align', 'center');
           
            } else {
                console.log('course is not published!');
            }
        });
    }
}

