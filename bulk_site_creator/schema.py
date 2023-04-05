import datetime
from typing import List, Optional

from ulid import ULID

"""
Defines the schema of the dynamodb table.
"""


class JobRecord:
    def __init__(
        self,
        school: str,
        sis_term_id: int,
        sis_department_id: Optional[int],
        sis_course_group_id: Optional[int],
        created_by_user_id: str,
        course_instance_ids: List[str],
        workflow_state: str,
        creator_email: str,
        user_full_name: str,
        template_name: Optional[str],
        template_id: Optional[int],
    ):
        self.pk = f"SCHOOL#{school}"
        self.sk = f"JOB#{str(ULID)}"
        self.sis_term_id = sis_term_id
        self.sis_department_id = sis_department_id
        self.sis_course_group_id = sis_course_group_id
        self.created_by_user_id = created_by_user_id
        self.course_instance_ids = course_instance_ids
        self.workflow_state = workflow_state
        self.created_at = datetime.datetime.now()
        self.creator_email = creator_email
        self.user_full_name = user_full_name
        self.template_name = template_name
        self.template_id = template_id

    def __getitem__(self, key):
        return self.__dict__[key]

    def to_dict(self):
        return {
            "pk": self.pk,
            "sk": self.sk,
            "sis_term_id": self.sis_term_id,
            "sis_department_id": self.sis_department_id,
            "sis_course_group_id": self.sis_course_group_id,
            "created_by_user_id": self.created_by_user_id,
            "course_instance_ids": self.course_instance_ids,
            "workflow_state": self.workflow_state,
        }


class TaskRecord:
    def __init__(
        self,
        job_record: JobRecord,
        workflow_state: str,
        created_by_user_id: str,
    ):
        self.pk = job_record.sk
        self.sk = f"TASK#{str(ULID)}"
        self.workflow_state = workflow_state
        self.created_by_user_id = created_by_user_id
        self.created_at = datetime.datetime.now()

    def to_dict(self):
        return {
            "pk": self.pk,
            "sk": self.sk,
            "created_by_user_id": self.created_by_user_id,
            "workflow_state": self.workflow_state,
            "created_at": self.created_at,
        }
