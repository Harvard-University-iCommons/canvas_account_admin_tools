// this is a test

/*
get the course number for the canvas course
*/
function get_course_number() {
	var page_url = window.location;
	var pat = /\/courses\/(\d+)/g;
	var match = pat.exec(page_url);
	if (match) {
		course_id = match[1];
		return course_id;
	}
	return 0;
}

var shopping_tool_url = "https://qa.tlt.harvard.edu/tools/shopping";
//var shopping_tool_url = "https://demo.tlt.harvard.edu/tools/shopping";
//var shopping_tool_url = "https://test.tlt.harvard.edu/tools/shopping";
//var shopping_tool_url = "http://localhost.harvard.edu:8001/tools/shopping";

var current_user_id = ENV['current_user_id'];
console.log(current_user_id);
user_url = "/api/v1/users/"+current_user_id+"/profile";

/*
check to see if the '#authorized_message' id exists on the page. 
If so, redirect the user to the shopping tool.
*/

var authorized = $('#unauthorized_message').length > 0 ? false : true
console.log((authorized ? '' : 'un') + 'authorized!')

if (!authorized){
	course_id = get_course_number();
	console.log('course_id = '+course_id);
	if (course_id > 0) {
		url = shopping_tool_url+'/view_course/'+course_id+'?canvas_user_id='+current_user_id
		window.location.replace(url);
	}
}
else {

	var un = $('ul#identity > li.user_name > a').text();

	if ( !un ) {
		console.log('-----> user is not logged in');

	} else {
		console.log('-----> user is logged in - username is ' + un);
		//page_url = window.location;
		var sis_user_id = '';
		$.getJSON(user_url, function( data ) {
			 sis_user_id = data["login_id"].trim();
			 console.log('----> '+sis_user_id);
	
			//var pat = /\/courses\/(\d+)/g;
			//var match = pat.exec(page_url);
			course_id = get_course_number();
			if (course_id > 0) {
				//course_id = match[1];
				console.log('-----> course id is ' + course_id);
				user_enrolled = false;
				user_can_shop = false;
				is_shopper = false;
				is_viewer = false;
				is_teacher = false;
				course_is_active = false;
				user_role = '';
		
				url = "/api/v1/courses/"+course_id;
				$.getJSON(url, function( data ) {
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
					
								// check for shopper
								var num_enrollments = data['enrollments'].length;
					
								for (var n = 0; n < num_enrollments; n++) {
									var etype = data['enrollments'][n]['type'];
									var erole = data['enrollments'][n]['role'];
									console.log('Type/role is ' + etype + '/' + erole);
									user_enrolled = true;
							
									if ( erole == 'Shopper' ) {
										is_shopper = true;
										//user_enrolled = true;
									}
									if ( erole == 'Harvard-Viewer' ) {
										is_viewer = true;
										//user_enrolled = true;
									}
								}
							} else {
								console.log('This course ' + course_id + ' does not match ' + c_id);
							}
	
						console.log('-----> user enrolled: ' + user_enrolled);
			
						/*
							If the user is on the settings page, do not show the button
						*/
						var isNotAdminPage = (String(page_url).indexOf('settings') == -1);
						console.log('-----> isNotAdminPage: '+isNotAdminPage);
				
						if( isNotAdminPage ) {
				
							/*
								If the user is not enrolled, they will be shown the shopping button.
								If the user is enrolled as a Harvard-Viewer, they will be shown the shopping button.
								If the user is enrolled as a Shopper, the will be shown the remove shopping button.
							*/
				
							if ( user_enrolled ) {
					
								var page_content = $('div#content');
								//sis_user_id = temp.trim();
								if ( is_shopper ) {
									console.log('-----> Shopping! display UNshop' );
									// add content inside of aside#right-side
									var shoplink = '<div class="center-button"><a href="'+shopping_tool_url+'/remove_shopper_role/'+course_id+'/'+sis_user_id+'" class="btn btn-danger">Stop shopping this course</a></div>';
									page_content.prepend(shoplink);
								}
								else if ( is_viewer ) {
									console.log('-----> Viewing! display shopping button' );
									var shoplink = '<div class="center-button"><a href="'+shopping_tool_url+'/shop_course/'+course_id+'/'+sis_user_id+'" class="btn btn-success">Students: shop this course</a></div>';
									page_content.prepend(shoplink);
								}
					
								//if( is_shopper || is_viewer ){
								//    $("#menu").append('<li id="shopping_menu_item" class="menu-item"><a class="menu-item-no-drop" href="'+shopping_tool_url+'/my_list">Manage Shopping</a></li>');
								//}
					
							} else {
								console.log('-----> display the shopping button 2');
								// add content inside of aside#right-side
								var page_content = $('div#content');
								console.log(shopping_tool_url+'/shop_course/'+course_id+'/'+sis_user_id);
								var shoplink = '<div class="center-button"><a href="'+shopping_tool_url+'/shop_course/'+course_id+'/'+sis_user_id+'" class="btn btn-success">Students: shop this course</a></div>';
								page_content.prepend(shoplink);
								//$("#menu").append('<li id="shopping_menu_item" class="menu-item"><a class="menu-item-no-drop" href="'+shopping_tool_url+'/my_list">Manage Shopping</a></li>');
							}
							$('.center-button').css('text-align', 'center');
						}
					} else {
						console.log('course is not published!');
					}
				});
			}
		});
	}
}