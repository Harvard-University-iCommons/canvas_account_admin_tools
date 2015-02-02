
// allowed_terms is a whitelist of Canvas enrollment_term_ids where shopping is allowed
var allowed_terms = ['46'];

/*
get the course number for the canvas course
*/
function get_course_number() {
	var page_url = window.location.pathname;
	var pat = /\/courses\/(\d+)/g;
	var match = pat.exec(page_url);
	if (match) {
		course_id = match[1];
		return course_id;
	}
	return 0;
}

function get_sis_user_id(canvas_user_api_data) {
	var user_id = null;
    if (canvas_user_api_data) {
        if (canvas_user_api_data['sis_user_id'] && canvas_user_api_data['sis_user_id'].trim()) {
            user_id = canvas_user_api_data['sis_user_id'].trim();
        } else if (canvas_user_api_data['login_id'] && canvas_user_api_data['login_id'].trim()) {
            user_id = canvas_user_api_data['login_id'].trim();
        }
    }
    return user_id;
}


var shopping_tool_url = "https://icommons.harvard.edu/tools/shopping";	// the url of the shopping tool
var current_user_id = ENV['current_user_id'];							// the canvas id if the current user
var user_url = '/api/v1/users/' + current_user_id + '/profile';			// the url to the user profile api call

var course_id = get_course_number();
var course_url = '/api/v1/courses/' + course_id;

var data_tooltip = 'More info about access during shopping period';
var shopping_help_doc_url = 'https://wiki.harvard.edu/confluence/display/canvas/Course+Shopping';
var tooltip_link = '<a data-tooltip title="' + data_tooltip + '" target="_blank" href="' + shopping_help_doc_url + '"><i class="icon-question"></i></a>';
var login_url = window.location.origin+"/login";
var no_user_canvas_login = "<div class='tltmsg tltmsg-shop'><p class='participate-text'>Students: <a href=\""+login_url+"\">login</a> to get more access during shopping period." + tooltip_link + "</p></div>";

var is_not_admin_page = ((window.location.pathname).indexOf('settings') == -1);
var is_not_speed_grader_page = ((window.location.pathname).indexOf('speed_grader') == -1);
var is_not_submissions_page = ((window.location.pathname).indexOf('submissions') == -1);

var user_enrolled = false;
var is_shopper = false;
var is_viewer = false;
var is_teacher = false;

var shopping_banner = jQuery('<div/>', {
						id: 'course-shopping',
						class: 'tltmsg'
						});

/*
	check to see if the '#authorized_message' id exists on the page.
	If so, redirect the user to the shopping tool.
*/
var authorized = $('#unauthorized_message').length > 0 ? false : true;

if (!authorized){
	if (course_id > 0) {
		$.getJSON(user_url, function( data ) {
			var login_id = get_sis_user_id(data);
			var url = shopping_tool_url + '/view_course/' + course_id + '?canvas_login_id=' + login_id;
			window.location.replace(url);
		});
	}
}
else {

	var un = $('ul#identity > li.user_name > a').text();

	if ( !un ) {
		/*
			user is not logged in to Canvas.
		*/
		$.getJSON(course_url, function( data ) {
			/*
				Check to see the course is in the 'available' (Published) state before showing
				the shopping button.
			*/

			var course_workflow = data['workflow_state'];

			if(course_workflow.localeCompare('available') == 0 && is_not_admin_page && is_not_speed_grader_page && is_not_submissions_page) {
				/*
					TLT-668 - only allow shopping for terms that are in the whitelist.
				*/
				var term_id = data['enrollment_term_id'];
				var term_allowed = jQuery.inArray( term_id, allowed_terms ) > -1;

				if (term_allowed) {

        			shopping_banner.append(no_user_canvas_login);
        			$('#breadcrumbs').after(shopping_banner);
        		}
        	}
        });
	}
	else {
		var sis_user_id = '';
		$.getJSON(user_url, function( data ) {
			sis_user_id = get_sis_user_id(data);

			if (course_id > 0) {

				$.getJSON(course_url, function( data ) {
					/*
						Check to see the course is in the 'available' (Published) state before showing
						the shopping button.
					*/

					var course_workflow = data['workflow_state'];

					if(course_workflow.localeCompare('available') == 0 && is_not_admin_page && is_not_speed_grader_page && is_not_submissions_page) {

						/*
							TLT-668 - only allow shopping for terms that are in the whitelist.
						*/
						var term_id = data['enrollment_term_id'];
                        var term_allowed = jQuery.inArray( term_id, allowed_terms ) > -1;
                        if (term_allowed) {

                            var c_id = data['id'];

                            if (course_id == c_id) {

                                var num_enrollments = data['enrollments'].length;

                                /*
                                	if this is a public site and the user has no enrollments, send
                                	them to the view_course url to add them as a Harvard-Viewer.
                                */
                                if(num_enrollments == 0){
									url = shopping_tool_url + '/view_course/' + course_id + '?canvas_login_id=' + sis_user_id
									window.location.replace(url);
                                }

                                for (var n = 0; n < num_enrollments; n++) {
                                    var erole = data['enrollments'][n]['role'];
                                    user_enrolled = true;

                                    if (erole == 'Shopper') {
                                        is_shopper = true;
                                    }
                                    if (erole == 'Harvard-Viewer') {
                                        is_viewer = true;
                                    }
                                    if (erole == 'TeacherEnrollment' || erole == 'TaEnrollment' || erole == 'DesignerEnrollment') {
                                        is_teacher = true;
                                    }
                                }
                            }

                            /*
                             	If the user is enrolled as a Harvard-Viewer, they will be shown the shopping button and the remove viewer button.
                             	If the user is enrolled as a Shopper, the will be shown the remove shopping button.
                             	If the user is enrolled as TeacherEnrollment,  TaEnrollment, or DesignerEnrollment they will be shown the shopping is active message.

                             	TLT-668 - if the term_id of the course is in the allowed_terms whitelist display the shopping
                             	options to the user. Otherwise do not show the shopping options.
                             */

                            if (user_enrolled) {

                                /*
                                 	application url endpoints
                                 */
                                var login_id = '?canvas_login_id=' + sis_user_id;
                                var course_and_user_id_param = course_id + login_id;
                                var add_shopper_url = shopping_tool_url + '/shop_course/' + course_and_user_id_param;
                                var remove_shopper_url = shopping_tool_url + '/remove_shopper_role/' + course_and_user_id_param;
                                var remove_viewer_url = shopping_tool_url + '/remove_viewer_role/' + course_and_user_id_param;
                                var manage_shopping_page_url = shopping_tool_url + '/my_list' + login_id;

                                /*
                                 	text messages
                                 */
                                var shopper_message_text = '<h1>You have full access to this course site ' + tooltip_link + '</h1><p><em>Note: During shopping period you can access course site materials and tools that are normally restricted to the class list. Your contributions may be visible to other students and visitors to this course site. <a href="' + remove_shopper_url + '">I want to be removed.</a></em></p>';
                                var viewer_message_text = '<h1>You have limited access during shopping period ' + tooltip_link + '</h1><p>You can view this site and may receive email notifications for one day. <a href="' + remove_viewer_url + '">I want to be removed.</a></p>';
                                var participate_text = "<div class='tltmsg tltmsg-shop'><p class='participate-text'>Want to participate and continue to receive email notifications?<em>(students only)</em> <a class='btn btn-small btn-primary' href='" + add_shopper_url + "'>Get full access</a></p></div>";
                                var shopping_is_active_message = '<h1>All Harvard ID holders can view this course site during shopping period ' + tooltip_link + '</h1>In addition, all students can access course site materials and tools that are normally restricted to the class list. Student contributions may be visible to other students and visitors to this course site.';

                                var shopping_help_doc = jQuery('<a/>', {
                                    id: 'shopping-help-doc',
                                    href: shopping_help_doc_url,
                                    target: '_blank',
                                    text: 'What is this?'
                                });

                                var remove_shopping_role = jQuery('<a/>', {
                                    id: 'remove-shopper-role',
                                    href: remove_shopper_url,
                                    text: 'I want to be removed.'
                                });

                                var add_shopping_role = jQuery('<a/>', {
                                    id: 'add-shopper-role',
                                    class: 'btn btn-small Button Button--primary',
                                    href: add_shopper_url,
                                    text: 'Get full access'
                                });

                                var remove_viewer_role = jQuery('<a/>', {
                                    id: 'remove-viewer-role',
                                    href: remove_viewer_url,
                                    text: 'I want to be removed.'
                                });

                                var manage_shopping_li_item = jQuery('<li/>', {
                                    id: 'manage-shopping',
                                    class: 'menu-item'
                                });

                                var manage_shopping_link = jQuery('<a/>', {
                                    id: 'manage-shopping-page-link',
                                    class: 'menu-item-no-drop',
                                    href: manage_shopping_page_url,
                                    text: "Courses I'm Shopping"
                                });

                                /*
                                	build the Manage Shopping menu item
                                */
                                manage_shopping_li_item.append(manage_shopping_link);

                                /*
                                 	for each role format the appropriate banner
                                 */
                                if (is_shopper) {
                                    $("ul#menu").append(manage_shopping_li_item);
                                    shopping_banner.append(shopper_message_text);
                                }
                                else if (is_viewer) {
                                    $("ul#menu").append(manage_shopping_li_item);
                                    shopping_banner.append(viewer_message_text);
                                    shopping_banner.append(participate_text);
                                }
                                else if (is_teacher) {
                                    shopping_banner.append(shopping_is_active_message);
                                }

                                /*
                                	display the banner formatted above
                                */
                                if (is_shopper || is_viewer || is_teacher) {
                                    $('#breadcrumbs').after(shopping_banner);
                                }
                            }
                        }
					}
				});
			}
		});
	}
}
