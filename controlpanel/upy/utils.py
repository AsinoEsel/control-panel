import os


def rm(d):  # Remove file or tree
    try:
        if os.stat(d)[0] & 0x4000:  # Dir
            for f in os.ilistdir(d):
                if f[0] not in ('.', '..'):
                    rm("/".join((d, f[0])))  # File or Dir
            print(f"Removing directory {d}...")
            os.rmdir(d)
        else:  # File
            print(f"Removing file {d}...")
            os.remove(d)
    except:
        print("rm of '%s' failed" % d)


def rm_all(whitelist: list[str]|None = None):
    if whitelist is None:
        whitelist = []
    whitelist += [f"{__name__}.py", "boot.py", "credentials.py", "webrepl_cfg.py"]
    for d in os.listdir():
        if d in whitelist:
            continue
        rm(d)
    print(f"Removed all files and directories except:\n- {"\n- ".join(file for file in whitelist if file in os.listdir())}")