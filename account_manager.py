class AccountManager:
    def __init__(self):
        self.users = {
            "admin": User("admin", "password")
        }
    
    def attempt_login(self, username: str, password: str):
        if not self.users.get(username):
            return False
        if not self.users.get(username).password == password:
            return False
        return self.users.get(username)


class User:
    def __init__(self, username: str, password: str) -> None:
        self.username = username
        self.password = password
        self.progress = None


if __name__ == "__main__":
    account_manager = AccountManager()
    print(account_manager.users)
