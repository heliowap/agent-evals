from userlib.core import fetch_user_name, get_user_name_legacy

def label(user):
    return fetch_user_name(user) + ' / ' + get_user_name_legacy(user)
