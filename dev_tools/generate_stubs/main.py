from .get_device import generate_device_stub_file


def generate_all_stubs() -> None:
    print("Generating stub files...")
    generate_device_stub_file()


if __name__ == "__main__":
    generate_all_stubs()
