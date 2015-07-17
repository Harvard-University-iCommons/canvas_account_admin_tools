// allowed_terms is a whitelist of Canvas enrollment_term_ids where shopping is allowed
// NOTE - the term ids in allowed_terms must be strings, not ints
var allowed_terms = [];
var shopping_tool_url = "https://icommons-tools.tlt.harvard.edu/shopping";    // the url of the shopping tool

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

function is_course_available(course_workflow) {
  return course_workflow.localeCompare('available') == 0;
}

function term_allowed(term_id) {
  return jQuery.inArray(term_id, allowed_terms) > -1;
}

var current_user_id = ENV['current_user_id'];							// the canvas id if the current user
var user_url = '/api/v1/users/' + current_user_id + '/profile';			// the url to the user profile api call

var course_id = get_course_number();
var course_url = '/api/v1/courses/' + course_id ;

var data_tooltip = 'More info about access during shopping period';
var shopping_help_doc_url = 'https://wiki.harvard.edu/confluence/display/canvas/Course+Shopping';
var tooltip_link = '<a data-tooltip title="' + data_tooltip + '" target="_blank" href="' + shopping_help_doc_url + '"><i class="icon-question"></i></a>';
var login_url = window.location.origin+"/login";
var no_user_canvas_login = "<div class='tltmsg tltmsg-shop'><p class='participate-text'>Students: <a href=\""+login_url+"\">login</a> to get more access during shopping period." + tooltip_link + "</p></div>";

var on_admin_page = ((window.location.pathname).indexOf('settings') != -1);
var on_speed_grader_page = ((window.location.pathname).indexOf('speed_grader') != -1);
var on_submissions_page = ((window.location.pathname).indexOf('submissions') != -1);
var on_special_page = on_admin_page || on_speed_grader_page || on_submissions_page;

var user_enrolled = false;
var is_shopper = false;
var is_teacher = false;
var is_student = false;

var shopping_banner = jQuery('<div/>', {
  id: 'course-shopping',
  class: 'tltmsg'
});

/*
 check to see if the '#unauthorized_message' is being rendered  and only proceed
 with additional checks to show shopping messages if authorized
 */
var authorized = $('#unauthorized_message').length > 0 ? false : true;

if (authorized){

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

      if(is_course_available(data['workflow_state']) && !on_special_page) {
        /*
         TLT-668 - only allow shopping for terms that are in the whitelist.
         */
        if (term_allowed(data['enrollment_term_id'])) {
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

          if(is_course_available(data['workflow_state']) && !on_special_page) {

            /*
             TLT-668 - only allow shopping for terms that are in the whitelist.
             */
            if (term_allowed(data['enrollment_term_id'])) {

              var c_id = data['id'];

              if (course_id == c_id) {

                var num_enrollments = data['enrollments'].length;

                for (var n = 0; n < num_enrollments; n++) {
                  var erole = data['enrollments'][n]['role'];
                  var type =  data['enrollments'][n]['type'];
                  user_enrolled = true;

                  is_shopper = (erole == 'Shopper');
                  is_student = (erole == 'StudentEnrollment-Viewer');
                  /* Base the teacher check on 'type' instead of 'role' to capture most teacher roles. Since Designer and
                  	TA have their own special type, they are checked separately. Student/Shopper
                   check would still use role as they are both of type 'student'
                  */
                  is_teacher =  (type == 'teacher' || type == 'ta' ||type == 'designer' );
                }
              }

              /*
               If the user is enrolled as a Shopper, they will be shown the remove shopping button.
               If the user is enrolled as  Teacher (Teacher, Ta, Designer, etc), they will be shown the shopping is active message.

               TLT-668 - if the term_id of the course is in the allowed_terms whitelist display the shopping
               options to the user. Otherwise do not show the shopping options.
               */

              /*
               application url endpoints
               */
              var login_id = '?canvas_login_id=' + sis_user_id;
              var course_and_user_id_param = course_id + login_id;
              var add_shopper_url = shopping_tool_url + '/shop_course/' + course_and_user_id_param;
              var remove_shopper_url = shopping_tool_url + '/remove_shopper_role/' + course_and_user_id_param;
              var manage_shopping_page_url = shopping_tool_url + '/my_list' + login_id;

              /*
               text messages
               */
              var shopper_message_text = '<h1>You have full access to this course site ' + tooltip_link + '</h1><p><em>Note: During shopping period you can access course site materials and tools that are normally restricted to the class list. Your contributions may be visible to other students and visitors to this course site. <a href="' + remove_shopper_url + '">I want to be removed.</a></em></p>';
              var viewer_message_text = '<h1>You have limited access during shopping period ' + tooltip_link + '</h1><p>You can view the site but not receive email notifications.</p>';
              var participate_text = "<div class='tltmsg tltmsg-shop'><p class='participate-text'>Want to participate and continue to receive email notifications?<em>(students only)</em> <a class='btn btn-small btn-primary' href='" + add_shopper_url + "'>Get full access</a></p></div>";
              var shopping_is_active_message = '<h1>All Harvard ID holders can view this course site during shopping period ' + tooltip_link + '</h1>In addition, all students can access course site materials and tools that are normally restricted to the class list. Student contributions may be visible to other students and visitors to this course site.';

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
              if (user_enrolled) {
                manage_shopping_li_item.append(manage_shopping_link);

                /*
                 for each role format the appropriate banner
                 */
                if (is_shopper) {
                  $("ul#menu").append(manage_shopping_li_item);
                  shopping_banner.append(shopper_message_text);
                }
                else if (is_teacher) {
                  shopping_banner.append(shopping_is_active_message);
                }
                /*
                 display the banner formatted above
                 */
                if (is_shopper || is_teacher) {
                  $('#breadcrumbs').after(shopping_banner);
                }
              }else{
                /*
                 If logged in user is not enrolled, then display generic shopping message to authorized user
                 */
                $("ul#menu").append(manage_shopping_li_item);
                shopping_banner.append(viewer_message_text);
                shopping_banner.append(participate_text);
                $('#breadcrumbs').after(shopping_banner);
              }
            }
          } else if (on_admin_page && term_allowed(data['enrollment_term_id'])) {
            // on course admin page for course in a whitelisted term --> disable is_public_to_auth_users
            var $iptau_checkbox = $('#course_is_public_to_auth_users');
            $iptau_checkbox.closest("div").addClass("selection-disabled");
            $iptau_checkbox.closest("span").after('<span> <em>(this option is disabled during shopping)</em></span>');
            $iptau_checkbox.attr("disabled", true);
          }
        });
      }
    });
  }
}
