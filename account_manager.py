from setup import LEVEL_LIST
import shelve


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
    
    def save_user_progress(self, user: User|None = None) -> tuple[bool, str]:
        with shelve.open("user_progress.db") as db:
            if user:
                db[user.username] = user
                return True, f'Saved user progress for user "{user.username}".'
            for username, user in self.users.items():
                db[username] = user
                return True, "Saved user progress for all users."
    
    def load_user_progress(self, user: User|None = None) -> tuple[bool, str]:
        with shelve.open("user_progress.db") as db:
            if user and not db.get(user.username):
                return False, f'Could not load progress for user "{user.username}" because user is not in DB.'
            if user:
                self.users[user.username] = db[user.username]
                return True, f'Loaded progress for user "{user.username}".'
            failed_usernames = []
            for username in self.users.keys():
                if not db.get(username):
                    failed_usernames.append(username)
                    continue
                self.users[username] = db[username]
            if not failed_usernames:
                return True, 'Loaded progress for all users.'
            if len(failed_usernames) == len(self.users):
                return False, 'Failed to load progress for all users. DB is probably missing.'
            return True, f'Loaded progress for all users with the exception of: {', '.join(failed_usernames)}'
    
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
