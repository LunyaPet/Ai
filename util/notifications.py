import os
from constants import ROLE_VIDEOS, ROLE_STREAMS, ROLE_TIKTOK, ROLE_FEDI, ROLE_SERVER

def notifications_to_roles(notifications: list[str]) -> list[str]:
    result = []

    for i in notifications:
        if i == "videos":
            result.append(ROLE_VIDEOS)
        elif i == "streams":
            result.append(ROLE_STREAMS)
        elif i == "tiktok":
            result.append(ROLE_TIKTOK)
        elif i == "fedi":
            result.append(ROLE_FEDI)
        elif i == "server":
            result.append(ROLE_SERVER)

    if len(notifications) != len(result):
        print("ERROR notifications_to_roles mismatched count of roles! Check input!")

    return result
