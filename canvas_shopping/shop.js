// this is a test

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

var shopping_tool_url = "https://demo.tlt.harvard.edu/tools/shopping";

var current_user_id = ENV['current_user_id'];
console.log(current_user_id);
user_url = '/api/v1/users/' + current_user_id + '/profile';

/*
check to see if the '#authorized_message' id exists on the page.
If so, redirect the user to the shopping tool.
*/

var authorized = $('#unauthorized_message').length > 0 ? false : true
console.log((authorized ? '' : 'un') + 'authorized!')

if (!authorized){
	course_id = get_course_number();
	console.log('course_id = ' + course_id);
	if (course_id > 0) {
		$.getJSON(user_url, function( data ) {
			login_id = data["login_id"].trim();
			url = shopping_tool_url + '/view_course/' + course_id + '?canvas_login_id=' + login_id
			window.location.replace(url);
		});
	}
}
else {

	var un = $('ul#identity > li.user_name > a').text();

	if ( !un ) {
		console.log('-----> user is not logged in');

	} else {
		console.log('-----> user is logged in - username is ' + un);
		var sis_user_id = '';
		$.getJSON(user_url, function( data ) {
			 var sis_user_id = data["login_id"].trim();
			 console.log('----> '+sis_user_id);

			var course_id = get_course_number();
			if (course_id > 0) {
				console.log('-----> course id is ' + course_id);
				var user_enrolled = false;
				var user_can_shop = false;
				var is_shopper = false;
				var is_viewer = false;
				var is_teacher = false;
				var course_is_active = false;
				var user_role = '';
				var url = '/api/v1/courses/' + course_id;

				$.getJSON(url, function( data ) {
					/*
						Check to see the course is in the 'available' (Published) state before showing
						the shopping button.
					*/

					var course_workflow = data['workflow_state'];
					if(course_workflow.localeCompare('available') == 0) {
						console.log('course '+course_id+' is active');
							var c_id = data['id'];
							if ( course_id == c_id ) {
								console.log('MATCH! User is already enrolled in this course. Are they a shopper?');

								// check for shopper
								var num_enrollments = data['enrollments'].length;

								for (var n = 0; n < num_enrollments; n++) {
									var etype = data['enrollments'][n]['type'];
									var erole = data['enrollments'][n]['role'];
									console.log('Type/role is ' + etype + '/' + erole);
									user_enrolled = true;

									if ( erole == 'Shopper' ) {
										is_shopper = true;
									}
									if ( erole == 'Harvard-Viewer' ) {
										is_viewer = true;
									}
									if (erole == 'TeacherEnrollment' ){
										is_teacher = true;
									}
								}
							} else {
								console.log('This course ' + course_id + ' does not match ' + c_id);
							}

						console.log('-----> user enrolled: ' + user_enrolled);

						/*
							If the user is on the settings page, do not show the button
						*/
						var isNotAdminPage = ((window.location.pathname).indexOf('settings') == -1);
						console.log('-----> isNotAdminPage: '+isNotAdminPage);

						if( isNotAdminPage ) {

							/*
								If the user is enrolled as a Harvard-Viewer, they will be shown the shopping button and the remove viewer button.
								If the user is enrolled as a Shopper, the will be shown the remove shopping button.
								If the user is a teacher or other instructor they will be shown the shopping is active message.
							*/

							if ( user_enrolled ) {
							
																/*
									application url endpoints
								*/
								var course_and_query = course_id + '?canvas_login_id=' + sis_user_id;
								var add_shopper_url    = shopping_tool_url + '/shop_course/' + course_and_query;
								var remove_shopper_url = shopping_tool_url + '/remove_shopper_role/' + course_and_query;
								var remove_viewer_url  = shopping_tool_url + '/remove_viewer_role/' + course_and_query;
								var manage_shopping_page_url = shopping_tool_url + '/my_list';
								
								/*
									text messages
								*/
								var shopping_help_doc_url = 'http://www.google.com/';
								var shopper_message_text = 'You are a Shopper - A Shooper is... ';
								var viewer_message_text = 'You are a viewer - A Viewer is... ';
								var shopping_is_active_message = '<h4>Shopping is active!</h4>Lorem ipsum dolor sit amet, consectetur adipiscing elit.';
								
								var shopping_help_doc = jQuery('<a/>', {
									id: 'shopping-help-doc',
									href: shopping_help_doc_url,
									target: '_blank',
									text: 'What is this?'
								});
								
								var shopping_banner = jQuery('<div/>', {
									id: 'shopping-menu',
									class: 'alert alert-block'
								});
								
								var remove_shopping_role = jQuery('<a/>', {
									id: 'remove-shopper-role',
									class: 'btn',
									href: remove_shopper_url,
									text: 'Stop shopping this course'
								});
								
								var add_shopping_role = jQuery('<a/>', {
									id: 'add-shopper-role',
									class: 'btn',
									href: add_shopper_url,
									text: 'Shop this course'
								});
								
								var remove_viewer_role = jQuery('<a/>', {
									id: 'remove-viewer-role',
									class: 'btn',
									href: remove_viewer_url,
									text: 'Remove viewer role'
								});
								
								var manage_shopping_li_item = jQuery('<li/>', {
									id: 'manage-shopping',
									class: 'menu-item'
								});

								var manage_shopping_link = jQuery('<a/>', {
									id: 'manage-shopping-page-link',
									class: 'menu-item-no-drop',
									href: manage_shopping_page_url,
									text: 'Manage Shopping'
								});								
								
								/* build the Manage Shopping menu item */
								manage_shopping_li_item.append(manage_shopping_link);
								
								/*
									for each role display the appropriate banner
								*/
								if ( is_shopper ) {
									$("ul#menu").append(manage_shopping_li_item);
									console.log('is_shopper: true');
									shopping_banner.append(shopper_message_text);
									shopping_banner.append(shopping_help_doc);
									shopping_banner.append(remove_shopping_role);
								}
								else if ( is_viewer ) {
									console.log('is_viewer: true');
									shopping_banner.append(viewer_message_text);
									shopping_banner.append(shopping_help_doc);
									shopping_banner.append(add_shopping_role);
									shopping_banner.append(remove_viewer_role);
								} else if( is_teacher ){
									console.log('is_teacher: true');
									shopping_banner.append(shopping_is_active_message);
								}
								$('#content-wrapper').prepend(shopping_banner);
							}
						}
					} else {
						console.log('course is not published!');
					}
				});
			}
		});
	}
}
