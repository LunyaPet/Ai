import os

VALID_PRONOUNS_SINGLE = [
    'she', 'he', 'it', 'one', 'they', 'name'
]

VALID_PRONOUNS_COLLECTION = [
    'she/her',
    'he/him',
    'it/its',
    'one/ones',
    'they/them',
    'she/it',
    'he/it',
    'name',
    'he/they',
    'she/they'
]

def validate_pronouns(pronouns: str):
    """
    Validate if a pronoun is correct.
    :param pronouns: A singular "she" or collection "she/her" of pronouns.
    :return:
    """
    if pronouns in VALID_PRONOUNS_SINGLE:
        return True
    elif pronouns in VALID_PRONOUNS_COLLECTION:
        return True
    else:
        return False

ROLE_HE = os.getenv("ROLES_HE")
ROLE_SHE = os.getenv("ROLES_SHE")
ROLE_THEY = os.getenv("ROLES_THEY")
ROLE_ONE = os.getenv("ROLES_ONE")
ROLE_IT = os.getenv("ROLES_IT")
ROLE_NAME = os.getenv("ROLES_NAME")

def get_roles_for_pronouns(pronouns: str):
    pronouns = pronouns.strip()
    if pronouns == "name":
        return ROLE_NAME


    for i in pronouns.split("/"):
        if i == "she":
            return ROLE_SHE
        elif i == "he":
            return ROLE_HE
        elif i == "they":
            return ROLE_THEY
        elif i == "one":
            return ROLE_ONE
        elif i == "it":
            return ROLE_IT

    return ROLE_NAME

def get_sets_for_pronouns(pronouns: str):
    pronouns = pronouns.strip()
    if pronouns == "name":
        return ["name"]

    pronouns_coll = []

    for i in pronouns.split("/"):
        if i == "she":
            pronouns_coll.append("she/her")
        elif i == "he":
            pronouns_coll.append("he/him")
        elif i == "they":
            pronouns_coll.append("they/them")
        elif i == "one":
            pronouns_coll.append("one/ones")
        elif i == "it":
            pronouns_coll.append("it/its")

    return pronouns_coll
