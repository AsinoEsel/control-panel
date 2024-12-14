try:
    from enum import IntEnum
    const = lambda x: x
except ImportError:
    IntEnum = object
    from micropython import const


# Atomic numbers: iron = 26, oxygen = 8
# Iron(II) oxide (FeO): 32 protons
# Iron(III) oxide (Fe22O3): 76 protons
KEY_CONTROL_PANEL_PROTOCOL = 76


class SubKey(IntEnum):
    PushButton = const(0)
    RotaryEncoder = const(1)
    Integer = const(2)  # 32 bit
    String = const(3)  # null-terminated
    Double = const(4)  # 64 bit
    RFID = const(5)  # UID n bits -> int array
    ASCII = const(6)  # 8 bit
    Digits = const(7)  # 8 bit: 0-9
    BitMask = const(8)  # n bits -> bool array
    Digit = const(9)  # 8 bit: 0-9
    Any = const(255)  # n bits raw bytearray
