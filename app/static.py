from typing import List
from app import schemas, crud


def check_project_roles(project_participants: List[schemas.ProjectParticipantsInput], db):
    all_users = []
    all_roles = []

    for participant in project_participants:
        all_users.append(participant.userId)
        all_roles.append(participant.roleId)

        if participant.roleId not in [1, 2, 3]:
            return False, f"Role with ID '{participant.roleId}' does not exist"

        db_user = crud.get_user_by_id(db, participant.userId)
        if not db_user:
            return False, f"User with ID '{participant.userId}' does not exist"

    distinct_users = set(all_users)
    distinct_roles = set(all_roles)

    if len(all_users) != len(distinct_users):
        return False, "There is a duplicate user."

    if len(distinct_roles) != 3:
        return False, "Not all project roles have been declared (there are 3)."

    if all_roles.count(1) > 1:
        return False, "Only one product owner can be declared."

    if all_roles.count(2) > 1:
        return False, "Only one scrum master can be declared."

    return True, "OK"
