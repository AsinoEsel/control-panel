from enum import IntEnum

# Atomic numbers: iron = 26, oxygen = 8
# Iron(II) oxide (FeO): 32 protons
# Iron(III) oxide (Fe22O3): 76 protons
KEY_CONTROL_PANEL_PROTOCOL = 76


class SubKey(IntEnum):
    PushButton = 0
    RotaryEncoder = 1
    Integer = 2  # 32 bit
    String = 3  # null-terminated
    Double = 4  # 64 bit
    RFID = 5  # UID n bits -> int array
    ASCII = 6  # 8 bit
    Digits = 7  # 8 bit: 0-9
    BitMask = 8  # n bits -> bool array
    Digit = 9  # 8 bit: 0-9
    BananaPlugs = 10  # 2 times 8 bit -> tuple[int, int]
    Any = 255  # n bits raw bytearray
