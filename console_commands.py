from esp_requests import ESP_seven_segment
import os.path

class ConsoleCommand:
    def __init__(self, command_string: str, description: str, usage_string: str, expected_args: int|tuple[int]) -> None:
        self.command_string: str = command_string
        self.description: str = description
        self.usage_string: str = f"Usage of {self.command_string}: {self.command_string} {usage_string}"
        self.expected_args: int|tuple[int] = (expected_args,) if type(expected_args) is int else expected_args
    
    def get_usage_string(self) -> str:
        pass
    
    def execute(self, terminal, *args) -> None:
        pass


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
        if len(args) not in self.expected_args:
            print_to_log(self.usage_string, (255,0,0))
            return
        print_to_log(cmd.usage_string, (255,255,0))
        return


class Login(ConsoleCommand):
    def execute(self, terminal, *args: str):
        print_to_log = terminal.log.print_to_log if terminal else print
        
        if not args:
            print_to_log(self.usage_string, (255,255,0))
            return
        if len(args) not in self.expected_args:
            print_to_log(self.usage_string, (255,0,0))
            return
        if not (value := terminal.get_root().control_panel.account_manager.attempt_login(args[0], args[1])):
            print_to_log(f"Could not log in as {args[0]}", (255,0,0))
            return
        print_to_log(f"Logged in as {value.username}", (255,255,0))


class Display(ConsoleCommand):
    def execute(self, terminal, *args) -> None:
        print_to_log = terminal.log.print_to_log if terminal else print

        if not args:
            print_to_log(self.usage_string, (255,255,0))
            return
        terminal.get_root().control_panel.schedule_async_task(ESP_seven_segment, "display", ' '.join(args))


class PlayVideo(ConsoleCommand):
    def execute(self, terminal, *args) -> None:
        print_to_log = terminal.log.print_to_log if terminal else print

        if not args:
            print_to_log(self.usage_string, (255,255,0))
            return
        if len(args) not in self.expected_args:
            print_to_log(self.usage_string, (255,0,0))
            return
        if args[0] in ("VHS14", "14"):
            print_to_log("Playing VHS14...", (255, 255, 0))
            terminal.get_root().add_video_window(os.path.join('media', 'video.mov'))
            return
        print_to_log(f'Could not find video "{args[0]}"', (255, 0, 0))


def handle_user_input(terminal, user_input: str):
    print_to_log = terminal.log.print_to_log if terminal else print
    
    split = user_input.split()
    if not split:
        return
    if not (cmd := cmd_dict.get(split[0])):
        print_to_log(f"{split[0]} is not a recognized command. Try help for help.", (255, 0, 0))
        return
    cmd.execute(terminal, *split[1:])
    return


cmds = (Help("help", "Display this text.", "<command>", (0,1)),
        Login("login", "Log into an account.", "<username> <password>", 2),
        Display("display", "Display a text.", "<text>", 1),
        PlayVideo("play", "Play a video file.", "<video_file>", 1))
cmd_dict = {cmd.command_string: cmd for cmd in cmds}

if __name__ == "__main__":
    while True:
        user_input = input()
        handle_user_input(None, user_input)