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

var shopping_tool_url = "https://qa.tlt.harvard.edu/tools/shopping";

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
									if (erole == 'TeacherEnrollment' || erole == 'TaEnrollment' || erole == 'DesignerEnrollment'){
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
								If the user is enrolled as TeacherEnrollment,  TaEnrollment, or DesignerEnrollment they will be shown the shopping is active message.
							*/

							if ( user_enrolled ) {

																/*
									application url endpoints
								*/
								var login_id = '?canvas_login_id=' + sis_user_id
								var course_and_user_id_param = course_id + login_id;
								var add_shopper_url    = shopping_tool_url + '/shop_course/' + course_and_user_id_param;
								var remove_shopper_url = shopping_tool_url + '/remove_shopper_role/' + course_and_user_id_param;
								var remove_viewer_url  = shopping_tool_url + '/remove_viewer_role/' + course_and_user_id_param;
								var manage_shopping_page_url = shopping_tool_url + '/my_list' + login_id;

								/*
									text messages
								*/
								var data_tooltip = 'More info. about access during shopping period';
								var shopping_help_doc_url = 'https://wiki.harvard.edu/confluence/display/canvas/Course+Shopping';
								var tooltip_link = '<a data-tooltip title="' + data_tooltip + '" target="_blank" href="' + shopping_help_doc_url + '"><i class="icon-question"></i></a>'
								var shopper_message_text = '<h1>You have full access to this course site ' + tooltip_link + '</h1><p><em>Note: During shopping period you can access course site materials and tools that are normally restricted to the class list. Your contributions may be visible to other students and visitors to this course site. <a href="' + remove_shopper_url + '">I want to be removed.</a></em></p>';
								var viewer_message_text = '<h1>You have limited access during shopping period ' + tooltip_link + '</h1><p>You can view this site and may receive email notifications for one day. <a href="' + remove_viewer_url + '">I want to be removed.</a></p>';
								var participate_text = "<div class='tltmsg tltmsg-shop'><p class='participate-text'>Want to participate and continue to receive email notifications?<em>(students only)</em> <a class='btn btn-small btn-primary' href='" + add_shopper_url + "'>Get full access</a></p></div>";
								var shopping_is_active_message = '<h1>All Harvard ID holders can view this course site during shopping period ' + tooltip_link + '</h1>In addition, all students can access course site materials and tools that are normally restricted to the class list. Student contributions maybe be visible to other students and visitors to this course site.';

								var shopping_help_doc = jQuery('<a/>', {
									id: 'shopping-help-doc',
									href: shopping_help_doc_url,
									target: '_blank',
									text: 'What is this?'
								});

								var shopping_banner = jQuery('<div/>', {
									id: 'course-shopping',
									class: 'tltmsg'
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

								/* build the Manage Shopping menu item */
								manage_shopping_li_item.append(manage_shopping_link);

								/*
									for each role display the appropriate banner
								*/
								if ( is_shopper ) {
									console.log('is_shopper: true');
									$("ul#menu").append(manage_shopping_li_item);
									shopping_banner.append(shopper_message_text);
									//shopping_banner.append(shopping_help_doc);
									//shopping_banner.append(remove_shopping_role);
								}
								else if ( is_viewer ) {
									console.log('is_viewer: true');
									$("ul#menu").append(manage_shopping_li_item);
									shopping_banner.append(viewer_message_text);
									shopping_banner.append(participate_text);
									//shopping_banner.append(shopping_help_doc);
									//shopping_banner.append(add_shopping_role);
									//shopping_banner.append(remove_viewer_role);
								} else if( is_teacher ){
									console.log('is_teacher: true');
									shopping_banner.append(shopping_is_active_message);
								}
								$('#breadcrumbs').after(shopping_banner);
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
