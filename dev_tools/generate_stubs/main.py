from .get_device import generate_get_device_stub_file
from .callback import generate_callback_stub_file


def generate_all_stubs() -> None:
    print("Generating stub files...")
    generate_get_device_stub_file()
    generate_callback_stub_file()


if __name__ == "__main__":
    generate_all_stubs()
