import os
from constants import ROLE_HE, ROLE_SHE, ROLE_THEY, ROLE_ONE, ROLE_IT, ROLE_NAME

def validate_pronouns(pronouns: str):
    """
    Validate if a pronoun is correct.
    :param pronouns: A singular "she" or collection "she/her" of pronouns.
    :return:
    """
    return len(get_sets_for_pronouns(pronouns)) > 0

ROLE_HE = os.getenv("ROLES_HE")
ROLE_SHE = os.getenv("ROLES_SHE")
ROLE_THEY = os.getenv("ROLES_THEY")
ROLE_ONE = os.getenv("ROLES_ONE")
ROLE_IT = os.getenv("ROLES_IT")
ROLE_NAME = os.getenv("ROLES_NAME")

def get_roles_for_pronouns(pronouns: str) -> list[str]:
    """
    Parse a pronoun string and return a list of role constants using pronoun sets.

    If no recognized pronoun is found, defaults to [ROLE_NAME].
    """
    set_to_role = {
        "she/her": ROLE_SHE,
        "he/him": ROLE_HE,
        "they/them": ROLE_THEY,
        "one/ones": ROLE_ONE,
        "it/its": ROLE_IT,
        "name": ROLE_NAME
    }

    roles: list[str] = []
    sets = get_sets_for_pronouns(pronouns)
    for s in sets:
        if s in set_to_role and set_to_role[s] not in roles:
            roles.append(set_to_role[s])

    return roles if roles else [ROLE_NAME]

def get_sets_for_pronouns(pronouns: str) -> list[str]:
    """
    Parse a pronoun string and return a list of canonical pronoun sets.

    - she -> ["she/her"]
    - he -> ["he/him"]
    - they -> ["they/them"]
    - she/her -> ["she/her"]
    - she/he/they -> ["she/her", "he/him", "they/them"]
    - one -> ["one/ones"]
    - one/it -> ["one/ones", "it/its"]
    - one/one's -> ["one/ones"]

    """
    pron = pronouns.strip().lower()
    if pron == "name":
        return ["name"]

    # Mapping from individual pronoun forms to a canonical set representation
    mapping = {
        "she": "she/her",
        "he": "he/him",
        "they": "they/them",
        "one": "one/ones",
        "it": "it/its",
    }

    result: list[str] = []
    for part in pron.split("/"):
        part = part.strip()
        # Normalize possessive forms like "one's" -> "one"
        if part.endswith("'s"):
            part = part[:-2]
        # Append the canonical set if recognized and not a duplicate
        if part in mapping:
            canon = mapping[part]
            if canon not in result:
                result.append(canon)
    return result
