/*
Note:
a)This is related to tlt-2900 and addresses AC #4 which is :
'Run a database query to remove secondary course site associations
from secondary courses for older cross-listed courses
(i.e. all cross-listing relationships up until the release of this enhancement).'

b) Needs to be run when 2900 is released
*/



/*This following SQL displays a list of course_sites and site_maps that are associated with
the all the secondary cross listed courses, that have external 'canvas' links that
do not match the teh corresponding ci.canvas_id (that would be updated with the
primary when they are cross listed)
Currently 763 in production
*/
select  ci.canvas_course_id, sm.*,cs.*
from site_map sm, course_site cs ,xreg_map xm, course_instance ci
where sm.course_instance_id= xm.secondary_course_instance
and sm.course_site_id=cs.course_site_id
and sm.course_instance_id=ci.course_instance_id
and external_id like '%https://canvas%edu/%'  --(only delete canvas links:current count=763)
and instr(external_id,canvas_course_id )<=0
order by sm.course_instance_id desc

/*This SQL is the same as above but only selects the course_site_id, site_map_id
to be used for deleting the records from the 2 tables
*/
select cs.course_site_id, site_map_id
from site_map sm, course_site cs ,xreg_map xm, course_instance ci
where sm.course_instance_id= xm.secondary_course_instance
and sm.course_site_id=cs.course_site_id
and sm.course_instance_id=ci.course_instance_id
and external_id like '%https://canvas.harvard.edu/%'
and instr(external_id,canvas_course_id )<=0
order by sm.course_instance_id desc;