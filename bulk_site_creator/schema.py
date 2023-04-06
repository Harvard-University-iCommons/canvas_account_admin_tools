import datetime
from enum import Enum
from typing import List, Optional

from ulid import ULID

"""
Defines the schema of the dynamodb table.
"""

class JobRecord:
    def __init__(
        self,
        school: str,
        term_id: str,
        term_name: Optional[str],
        department_id: Optional[str],
        department_name: Optional[str],
        course_group_id: Optional[str],
        course_group_name: Optional[str],
        template_id: Optional[str],
        template_name: Optional[str],
        user_id: str,
        user_full_name: str,
        user_email: str,
        workflow_state: str,
    ):
        self.pk = f"SCHOOL#{school.upper()}"
        self.sk = f"JOB#{str(ULID)}"
        self.term_id = term_id
        self.term_name = term_name
        self.department_id = department_id
        self.department_name = department_name
        self.course_group_id = course_group_id
        self.course_group_name = course_group_name
        self.template_id = template_id
        self.template_name = template_name
        self.user_id = user_id
        self.user_full_name = user_full_name
        self.user_email = user_email
        self.created_at = datetime.datetime.now()
        self.updated_at = datetime.datetime.now()

        if not is_valid_state(workflow_state):
            raise ValueError(f"Invalid workflow state: {workflow_state}")
        self.workflow_state = workflow_state.upper()

    def __getitem__(self, key):
        return self.__dict__[key]

    def to_dict(self):
        return {
            "pk": self.pk,
            "sk": self.sk,
            "term_id": self.term_id,
            "department_id": self.department_id,
            "department_name": self.department_name,
            "course_group_id": self.course_group_id,
            "course_group_name": self.course_group_name,
            "template_name": self.template_name,
            "template_id": self.template_id,
            "user_id": self.user_id,
            "user_full_name": self.user_full_name,
            "workflow_state": self.workflow_state,
            "user_email": self.user_email,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class TaskRecord:
    def __init__(
        self,
        job_record: JobRecord,
        course_instance_id: str,
        workflow_state: str,
    ):
        self.pk = job_record.sk
        self.sk = f"TASK#{str(ULID)}"
        self.course_instance_id = course_instance_id
        self.created_at = datetime.datetime.now()
        self.updated_at = datetime.datetime.now()

        if not is_valid_state(workflow_state):
            raise ValueError(f"Invalid workflow state: {workflow_state}")
        self.workflow_state = workflow_state.upper()

    def to_dict(self):
        return {
            "pk": self.pk,
            "sk": self.sk,
            "workflow_state": self.workflow_state,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class States(Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETE = "COMPLETE"

def is_valid_state(workflow_state: str):
    return workflow_state.upper() in [state.value for state in States]