import sys
import os
import importlib
from .services import Services


def load_scripts(args: list[str]) -> None:
    """
    This is where we load our "user scripts" on boot, by taking in a list of script file names, and then importing them.
    """

    # First, we "unpack" all .txt files
    while any(arg.endswith(".txt") for arg in args):
        for arg in args:
            if arg.endswith(".txt"):
                with open(os.path.join(os.path.dirname(__file__), arg), "r") as f:
                    entries = f.readlines()
                for entry in entries:
                    entry = entry.strip()
                    if entry:
                        args.append(entry)
                args.remove(arg)
                break

    failed: list[tuple[str, Exception, str]] = []
    success: list[tuple[str, set[str]]] = []
    for arg in args:
        if arg.endswith(".py"):
            arg = arg.removesuffix(".py")
        try:
            original_modules = set(sys.modules.keys())
            imported_module = importlib.import_module(f"controlpanel.scripts.{arg}", package=__name__)
            Services.loaded_scripts[arg] = imported_module
            new_modules = set(sys.modules.keys()) - original_modules
            if not new_modules:
                continue  # Skip this module because it has apparently already been imported before as a dependency
            dependencies = set()
            for new_module in new_modules:
                if not new_module.startswith("controlpanel.scripts."):  # are only interested in our scripts
                    continue
                new_module_name = new_module.removeprefix("controlpanel.scripts.")
                script_name, *submodules = new_module_name.split(".", maxsplit=1)
                if arg == script_name:  # Don't count imported module as dependency of itServices
                    continue
                dependencies.add(script_name)
                if not submodules:
                    Services.loaded_scripts[script_name] = sys.modules.get(new_module)

            success.append((arg, dependencies))
        except (ModuleNotFoundError, ImportError) as e:
            import traceback
            failed.append((arg, e, traceback.format_exc()))

    if success:
        print("Successfully loaded the following scripts:")
        for script, dependencies in success:
            print(f"- {script}")
            for dependency in dependencies:
                print(f"- {dependency:<15} (dependency of {script})")

    if failed:
        import traceback
        print("Failed to load the following scripts:")
        for script, error, traceback in failed:
            print(f"- {script} ({error.__class__.__name__}: {str(error)})")
            for line in traceback.split("\n"):
                print(line)
