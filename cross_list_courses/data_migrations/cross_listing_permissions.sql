

INSERT INTO lti_permissions_ltipermission (permission, school_id, canvas_role, allow) VALUES
('cross_listing', '*', 'AccountAdmin', TRUE),
('cross_listing', '*', 'Account Admin', TRUE);


-- reverse SQL:
DELETE  FROM lti_permissions_ltipermission WHERE permission="cross_listing";


