from util.storage import get_data, set_data


def add_member_to_quarantine(user_id: int):
    existing_data = get_data("quarantine")

    if "quarantine" not in existing_data:
        existing_data["quarantine"] = []

    existing_data["quarantine"].append(user_id)

    set_data("quarantine", existing_data)


def is_member_in_quarantine(user_id: int):
    existing_data = get_data("quarantine")
    if "quarantine" not in existing_data:
        return False
    return user_id in existing_data["quarantine"]


def delete_member_from_quarantine(user_id: int):
    existing_data = get_data("quarantine")

    if "quarantine" not in existing_data:
        existing_data["quarantine"] = []

    existing_data["quarantine"].remove(user_id)

    set_data("quarantine", existing_data)
