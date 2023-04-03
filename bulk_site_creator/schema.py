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
        template_canvas_course_id: int,
        created_by_user_id: str,
        course_instance_ids: List[str],
        status: str
    ):
        self.pk = f"SCHOOL#{school}"
        self.sk = f"JOB#{str(ULID)}"
        self.sis_term_id = sis_term_id
        self.sis_department_id = sis_department_id
        self.sis_course_group_id = sis_course_group_id
        self.template_canvas_course_id = template_canvas_course_id
        self.created_by_user_id = created_by_user_id
        self.course_instance_ids = course_instance_ids
        self.status = status

    def __getitem__(self, key):
        return self.__dict__[key]

    def to_dict(self):
        return {
            "pk": self.pk,
            "sk": self.sk,
            "sis_term_id": self.sis_term_id,
            "sis_department_id": self.sis_department_id,
            "sis_course_group_id": self.sis_course_group_id,
            "template_canvas_course_id": self.template_canvas_course_id,
            "created_by_user_id": self.created_by_user_id,
            "course_instance_ids": self.course_instance_ids,
            "status": self.status
        }


class TaskRecord:
    def __init__(
        self, job_record: JobRecord, sis_course_id: str, created_by_user_id: str, status: str
    ):
        self.pk = job_record.sk
        self.sk = f"TASK#{str(ULID)}"
        self.sis_course_id = sis_course_id
        self.created_by_user_id = created_by_user_id,
        self.status = status

    def to_dict(self):
        return {
            "pk": self.pk,
            "sk": self.sk,
            "sis_course_id": self.sis_course_id,
            "created_by_user_id": self.created_by_user_id,
            "status": self.status
        }

