import os.path
from window_manager_setup import LEVEL_LIST


class ConsoleCommand:
    def __init__(self, command_string: str, description: str, usage_string: str, expected_args: int|tuple[int], requires_login: bool = False) -> None:
        self.command_string: str = command_string
        self.description: str = description
        self.usage_string: str = f"Usage of {self.command_string}: {self.command_string} {usage_string}"
        self.expected_args: int|tuple[int] = (expected_args,) if type(expected_args) is int else expected_args
        self.requires_login = requires_login
    
    def validate(self, terminal, *args) -> None:
        print_to_log = terminal.log.print_to_log if terminal else print
        if len(args) not in self.expected_args:
            print_to_log(self.usage_string, (255,0,0))
            return False
        if self.requires_login and (account_manager := terminal.get_root().control_panel.account_manager):
            if not account_manager.logged_in_user:
                print_to_log("You are not logged in.", (255,0,0))
                return False
        return True


class Help(ConsoleCommand):
    def execute(self, terminal, *args: str) -> None:
        print_to_log = terminal.log.print_to_log if terminal else print
        
        if not args:
            print_to_log("List of recognized commands:", (255,255,0))
            for cmd in cmds:
                print_to_log(f"{cmd.command_string: <15}- {cmd.description}", (255,255,0))
            return
        if not (cmd := cmd_dict.get(args[0])):
            print_to_log(f'Could not find command "{args[0]}"', (255,0,0))
            return


class Login(ConsoleCommand):
    def execute(self, terminal, *args: str):
        print_to_log = terminal.log.print_to_log if terminal else print        
        account_manager = terminal.get_root().control_panel.account_manager        

        if not (user := account_manager.attempt_login(args[0], args[1])):
            print_to_log(f"Could not log in as {args[0]}", (255,0,0))
            return
        account_manager.login(user)
        print_to_log(f"Logged in as {user.username}", (255,255,0))


class Logout(ConsoleCommand):
    def execute(self, terminal, *args: str):
        print_to_log = terminal.log.print_to_log if terminal else print
        account_manager = terminal.get_root().control_panel.account_manager
        if not (user := account_manager.logged_in_user):
            print_to_log(f"No user is logged in.", (255,0,0))
            return
        print_to_log(f"Logged out of {user.username}.", (255,255,0))
        account_manager.logout()


# class Display(ConsoleCommand):
#     def execute(self, terminal, *args: str) -> None:
#         print_to_log = terminal.log.print_to_log if terminal else print

#         if not args:
#             print_to_log(self.usage_string, (255,255,0))
#             return
#         terminal.get_root().control_panel.schedule_async_task(ESP_seven_segment, "display", ' '.join(args))


class PlayVideo(ConsoleCommand):
    def execute(self, terminal, *args) -> None:
        print_to_log = terminal.log.print_to_log if terminal else print

        if args[0] in ("VHS14", "14"):
            print_to_log("Playing VHS14...", (255, 255, 0))
            terminal.get_root().add_video_window(os.path.join('media', 'video.mov'))
            return
        print_to_log(f'Could not find video "{args[0]}"', (255, 0, 0))


class UnlockLevel(ConsoleCommand):
    def execute(self, terminal, *args) -> None:
        print_to_log = terminal.log.print_to_log if terminal else print
        account_manager = terminal.get_root().control_panel.account_manager
        
        if args[0].lower() not in map(str.lower, LEVEL_LIST):
            print_to_log(f"Could not find level '{args[0]}'", (255,0,0))
            return
        levelname = LEVEL_LIST[list(map(str.lower, LEVEL_LIST)).index(args[0].lower())]
        if account_manager.logged_in_user.progress[levelname] is True:
            print_to_log(f"Level '{levelname}' already unlocked", (255,255,0))
            return
        account_manager.logged_in_user.progress[levelname] = True
        print_to_log(f"Unlocked level '{levelname}'")


class UnlockAll(ConsoleCommand):
    def execute(self, terminal, *args) -> None:
        print_to_log = terminal.log.print_to_log if terminal else print
        account_manager = terminal.get_root().control_panel.account_manager
        user_progress = account_manager.logged_in_user.progress
        if all(user_progress.values()):
            print_to_log(f"All levels are already unlocked", (255,255,0))
            return
        unlocked_levels = []
        for level, unlocked in account_manager.logged_in_user.progress.items():
            if not unlocked:
                user_progress[level] = True
                unlocked_levels.append(level)
        print_to_log(f"Unlocked the following levels: {", ".join(unlocked_levels)}", (255,255,0))


class SaveProgress(ConsoleCommand):
    def execute(self, terminal, *args) -> None:
        print_to_log = terminal.log.print_to_log if terminal else print
        account_manager = terminal.get_root().control_panel.account_manager
        if not args:
            success, message = account_manager.save_user_progress()
            print_to_log(message, (0,255,0,) if success else (255,0,0))
            return
        if not (user := account_manager.users.get(args[0])):
            print_to_log(f'Could not find user "{args[0]}".', (255,0,0))
            return
        success, message = account_manager.save_user_progress(user)
        print_to_log(message, (0,255,0,) if success else (255,0,0))


class LoadProgress(ConsoleCommand):
    def execute(self, terminal, *args) -> None:
        print_to_log = terminal.log.print_to_log if terminal else print
        account_manager = terminal.get_root().control_panel.account_manager
        if not args:
            success, message = account_manager.load_user_progress()
            print_to_log(message, (0,255,0,) if success else (255,0,0))
            return
        if not (user := account_manager.users.get(args[0])):
            print_to_log(f'Could not find user "{args[0]}".', (255,0,0))
            return
        success, message = account_manager.load_user_progress(user)
        print_to_log(message, (0,255,0,) if success else (255,0,0))
        

def handle_user_input(terminal, user_input: str):
    print_to_log = terminal.log.print_to_log if terminal else print
    
    split = user_input.split()
    if not split:
        return
    if not (cmd := cmd_dict.get(split[0])):
        print_to_log(f"{split[0]} is not a recognized command. Try help for help.", (255, 0, 0))
        return
    args = split[1:]
    if not cmd.validate(terminal, *args):
        return
    cmd.execute(terminal, *args)
    return


cmds = (Help("help", "Display this text.", "<command>", (0,1)),
        Login("login", "Log into an account.", "<username> <password>", 2),
        Logout("logout", "Log out of an account.", "", 0),
        # Display("display", "Display a text.", "<text>", 1),
        PlayVideo("play", "Play a video file.", "<video_file>", 1),
        UnlockLevel("unlock", "Unlock a level for the current user.", "<level>", 1, requires_login=True),
        UnlockAll("unlockall", "Unlock all levels for the current user.", "", 0, requires_login=True),
        SaveProgress("save", "Save progress for the specified user or all users.", "<username>", (0,1)),
        LoadProgress("load", "Load progress for the specified user or all users.", "<username>", (0,1)),)
cmd_dict = {cmd.command_string: cmd for cmd in cmds}

if __name__ == "__main__":
    while True:
        user_input = input()
        handle_user_input(None, user_input)