def fetch_user_name(user):
    return user['first'] + ' ' + user['last']

def get_user_name_legacy(user):
    return user['last'] + ', ' + user['first']
