from setup import LEVEL_LIST


class User:
    def __init__(self, username: str, password: str) -> None:
        self.username = username
        self.password = password
        self.progress = {level: False for level in LEVEL_LIST}
    
    def serialize(self):
        return {
            'username': self.username,
            'password': self.password,
            'progress': self.progress,
        }


class AccountManager:
    def __init__(self):
        self.users: dict[str:User] = {
            "admin": User("admin", "password"),
            "horse" : User("horse", "hay"),
        }
        self.logged_in_user: User = None
        self.users["admin"].progress["Maschinenraum"] = True
        self.users["horse"].progress["Cockpit"] = True
    
    def attempt_login(self, username: str, password: str) -> None|User:
        user = self.users.get(username)
        if not user:
            return None
        if not user.password == password:
            return None
        self.login(user)
        return user
    
    def login(self, user):
        self.logged_in_user = user
    
    def logout(self):
        self.logged_in_user = None


if __name__ == "__main__":
    account_manager = AccountManager()
    print(account_manager.users)
