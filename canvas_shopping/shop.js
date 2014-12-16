// TODO: global function should be namespaced and should be run only after everything on page loads
// TODO: do we need to use case-insensitive searches and toLowerCase() for URLs?
// TODO: modularize as much as possible
// TODO: docstrings

function get_dict_val_or_null(dict_obj, key) {
	return (typeof dict_obj[key] != 'undefined') ? dict_obj[key] : null;
}

function get_ENV_attribute(attr_name) {
	return ("ENV" in window) ? get_dict_val_or_null(ENV, attr_name) : null;
}

/*
get the course number for the canvas course based on ENV object supplied by Canvas
*/
function get_course_number() {
	return get_ENV_attribute('COURSE_ID');
}

/*
get the username for the canvas course based on ENV object supplied by Canvas
*/
function get_username() {
	var user = get_ENV_attribute('current_user');
	return get_dict_val_or_null(user, 'display_name');
}

/*
get the user ID for the canvas course based on ENV object supplied by Canvas
*/
function get_current_user_id() {
	return get_ENV_attribute('current_user_id');
}

function get_current_sis_user_id() {
	// TODO: cache this in case we call it twice
	var sis_user_id = null;
	$.getJSON(get_user_profile_url(get_current_user_id()), function( data ) {
		login_id = get_dict_val_or_null(data, 'login_id');
		if (login_id) {
			sis_user_id = login_id.trim();
		}
		else {
			console.error('User is logged in but has no login_in; need login_id for shopping tool.');
		}
	});
	return sis_user_id;
}

function get_user_profile_url(user_id) {
	return "/api/v1/users/" + user_id + "/profile";
}

function get_course_url(course_id) {
	return "/api/v1/courses/" + course_id;
}

// globals required for all functionality, eliminates multiple declarations
var sis_user_id = get_current_sis_user_id();
console.log('----> login_id is ' + sis_user_id);

var course_id = get_course_number();
console.log('course_id = '+course_id);

/*
check to see if the '#authorized_message' id exists on the page.
If so, redirect the user to the shopping tool.
*/

var authorized = ($('#unauthorized_message').length == 0);
console.log((authorized ? '' : 'un') + 'authorized!');

if (!authorized){
	if (course_id > 0) {
		url = 'http://demo.tlt.harvard.edu/tools/shopping/view_course/'+course_id+'/'+sis_user_id;
		window.location.replace(url);
	}
}
else {
	var current_user_id = get_ENV_attribute('current_user_id');

	if ( !current_user_id ) {
		console.log('-----> user is not logged in');

	} else {
		var shopping_tool_url = "https://qa.tlt.harvard.edu/tools/shopping";
		//var shopping_tool_url = "https://demo.tlt.harvard.edu/tools/shopping";
		//var shopping_tool_url = "https://test.tlt.harvard.edu/tools/shopping";
		//var shopping_tool_url = "http://localhost.harvard.edu:8001/tools/shopping";

		console.log('-----> user is logged in - username is ' + get_username() + ' and user id is ' + current_user_id);
		if (course_id > 0) {
			var user_enrolled = false;
			var user_can_shop = false;
			var is_shopper = false;
			var is_viewer = false;
			var is_teacher = false;
			var course_is_active = false;
			var user_role = '';

			// TODO: workflow_state can be found from ENV['CONTEXTS']['courses'][course_id]['available']
			// TODO: Can a user's enrollment data (i.e. if they have a role in this course) come from the Canvas data as well?
			// TODO:   e.g. how does one use ENV['CONTEXTS']['courses']['6264']['permissions']?
			// TODO:   e.g. are current_user_roles enough, or do we also need to explicitly make an enrollment call?
			// TODO:   Can we use backbone models here and let them handle the Ajax calls?
			$.getJSON(get_course_url(course_id), function( data ) {
				/*
					Check to see the course is in the 'available' (Published) state before showing
					the shopping button.
				*/

				course_workflow = data['workflow_state'];
				if(course_workflow.localeCompare('available') == 0) {
					console.log('course '+course_id+' is active');
						c_id = data['id'];
						if ( course_id == c_id ) {
							console.log('MATCH! User is already enrolled in this course. Are they a shopper?');
							user_enrolled = true;

							// check for shopper
							$.each(data['enrollments'], function(index, enrollment) {
								var etype = enrollment['type'];
								var erole = enrollment['role'];
								console.log('Type/role is ' + etype + '/' + erole);
								is_shopper = ( erole == 'Shopper' );
								is_viewer = ( erole == 'Harvard-Viewer' );
							});
						} else {
							// TODO: when does / how can this happen?
							console.log('User is not a shopper. This course ' + course_id + ' does not match ' + c_id);
						}

					/*
						If the user is on the settings page, do not show the button
						TODO: why do we do this?
					*/
					var isNotAdminPage = ((window.location.pathname).indexOf('settings') == -1);
					console.log('-----> isNotAdminPage: '+isNotAdminPage);

					if( isNotAdminPage ) {

						/*
							If the user is not enrolled, they will be shown the shopping button.
							If the user is enrolled as a Harvard-Viewer, they will be shown the shopping button.
							If the user is enrolled as a Shopper, the will be shown the remove shopping button.
						*/

						var page_content = $('div#content');
						if ( user_enrolled ) {

							// TODO: modularize the button & prepending code
							if ( is_shopper ) {
								console.log('-----> Shopping! display UNshop' );
								var shoplink = '<div class="center-button"><a href="'+shopping_tool_url+'/remove_shopper_role/'+course_id+'/'+sis_user_id+'" class="btn btn-danger">Stop shopping this course</a></div>';
								page_content.prepend(shoplink);
							}
							else if ( is_viewer ) {
								console.log('-----> Viewing! display shopping button' );
								var shoplink = '<div class="center-button"><a href="'+shopping_tool_url+'/shop_course/'+course_id+'/'+sis_user_id+'" class="btn btn-success">Students: shop this course</a></div>';
								page_content.prepend(shoplink);
							}

						} else {
							console.log('-----> display the shopping button 2');
							var shoplink = '<div class="center-button"><a href="'+shopping_tool_url+'/shop_course/'+course_id+'/'+sis_user_id+'" class="btn btn-success">Students: shop this course</a></div>';
							page_content.prepend(shoplink);
						}
						// TODO: can probably just chain this to .prepend() call, e.g. .prepend(shoplink).css(...)
						$('.center-button').css('text-align', 'center');
					}
				} else {
					console.log('course is not published!');
				}
			});
		}
	}
}