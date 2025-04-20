import json
import os


def get_data(path: str):
    """
    Read a JSON file at a path. Creates folders and appends .json automatically. Prepends data/
    :param path: Path to the entry. Omit the .json extension.
    :return: Dict with the data.
    """

    path = f"data/{path}"

    # Create folders
    s = ""
    for i in path.split("/")[:-1]:
        s += f"{i}/"
        if not os.path.exists(s):
            os.mkdir(s)

    # Check for existence

    if not os.path.exists(f"{path}.json"):
        return {}

    with open(f"{path}.json", "r") as f:
        return json.load(f)


def set_data(path: str, data: dict):
    """
    Sets data at a location. Creates folders and appends .json automatically. Prepends data/
    :param path: Path to the entry. Omit the .json extension.
    :param data: Dict with the data.
    :return: Nothing
    """

    path = f"data/{path}"

    # Create folders
    s = ""
    for i in path.split("/")[:-1]:
        s += f"{i}/"
        if not os.path.exists(s):
            os.mkdir(s)

    # Write file

    with open(f"{path}.json", "w") as f:
        json.dump(data, f)


def delete_data(path: str):
    """
    Deletes data at a location. Creates folders and appends .json automatically. Prepends data/
    :param path: Path to the entry. Omit the .json extension.
    :return: Nothing
    """

    path = f"data/{path}"

    # Create folders
    s = ""
    for i in path.split("/")[:-1]:
        s += f"{i}/"
        if not os.path.exists(s):
            os.mkdir(s)

    # Delete file
    os.unlink(f"{path}.json")
