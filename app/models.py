class User:
    def __init__(self, id, username, token):
        self.id = id
        self.username = username
        self.token = token


class LoggedUser:
    def __init__(self, username):
        self.username = username
        self.logged = True
