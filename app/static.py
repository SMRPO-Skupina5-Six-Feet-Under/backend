from typing import List
from app import schemas, crud


def check_project_roles(project_participants: List[schemas.ProjectParticipantsInput], db):
    product_owner_user = 0
    product_owner_counter = 0
    scrum_master_counter = 0
    developers = []

    for participant in project_participants:
        if participant.roleId == 1:
            product_owner_user = participant.userId
            product_owner_counter += 1

        if participant.roleId == 2:
            scrum_master_counter += 1

        if participant.roleId == 3:
            developers.append(participant.userId)

        if participant.roleId not in [1, 2, 3]:
            return False, f"Role with ID '{participant.roleId}' does not exist"

        db_user = crud.get_user_by_id(db, participant.userId)
        if not db_user:
            return False, f"User with ID '{participant.userId}' does not exist"

    if product_owner_counter == 0 or scrum_master_counter == 0 or len(developers) == 0:
        return False, "Not all project roles have been declared (there are 3)."

    if product_owner_counter > 1:
        return False, "Only one product owner can be declared."

    if scrum_master_counter > 1:
        return False, "Only one scrum master can be declared."

    if product_owner_user in developers:
        return False, "Product owner cannot be developer at the same time on the same project."

    return True, "OK"
