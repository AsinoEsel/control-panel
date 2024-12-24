import struct
try:
    from enum import IntEnum
except ImportError:
    IntEnum = object


# Constants for Art-Net
ART_NET_HEADER = b"Art-Net\x00"
ART_NET_VERSION = struct.pack(">H", 14)  # Protocol version
ART_NET_OEM = struct.pack("<H", 0x00FF)  # OEM code OemUnknown 0x00ff
ART_NET_ESTA_MAN = struct.pack("<H", 0)  # ESTA Manufacturer code


class OpCode(IntEnum):
    ArtPoll = 0x2000
    ArtPollReply = 0x2100
    ArtCommand = 0x2400
    ArtTrigger = 0x9900
    ArtDmx = 0x5000
    ArtNzs = 0x5100
    ArtSync = 0x5200
    ArtIpProg = 0xF800
    ArtIpProgReply = 0xF900
    ArtAddress = 0x6000


def is_artnet(data: bytes) -> bool:
    return data.startswith(ART_NET_HEADER)


def parse_header(data: bytearray) -> OpCode | None:
    if is_artnet(data) and len(data) >= 10:
        op_code_from_byte = struct.unpack("<H", data[8:10])[0]
        return op_code_from_byte
    else:
        return None


def parse_poll(data: bytes) -> dict[str: any] | None:
    if len(data) < 22:
        return None

    reply = dict(
        ProtVer=struct.unpack("<H", data[10:12])[0],
        Flags=[bool(data[12] >> i & 1) for i in range(8)],
        DiagPriority=data[13],
        TargetPort=[
            struct.unpack("<H", data[16:18])[0],
            struct.unpack("<H", data[14:16])[0],
        ],
        EstaMan=struct.unpack("<H", data[18:20])[0],
        Oem=struct.unpack("<H", data[20:22])[0],
    )

    return reply


def parse_poll_reply(data: bytes) -> dict[str: any] | None:
    if len(data) < 239:
        return None

    reply = dict(
        IpAdress=".".join(map(str, struct.unpack("BBBB", data[10:14]))),
        PortNumber=struct.unpack("<H", data[14:16])[0],
        VersInfo=struct.unpack("<H", data[16:18])[0],
        NetSwitch=data[18],
        SubSwitch=data[19],
        Oem=struct.unpack("<H", data[20:22])[0],
        UbeaVersion=data[22],
        Status1=data[23],
        EstaMan=struct.unpack("<H", data[24:26])[0],
        ShortName=data[26:44].strip(b"\0").decode(),
        LongName=data[44:108].strip(b"\0").decode(),
        NodeReport=data[108:172].strip(b"\0").decode(),
        NumPorts=struct.unpack("<H", data[172:174])[0],
        PortTypes=list(struct.unpack("BBBB", data[174:178])),
        GoodInput=list(struct.unpack("BBBB", data[178:182])),
        GoodOutput=list(struct.unpack("BBBB", data[182:186])),
        SwIn=list(struct.unpack("BBBB", data[186:190])),
        SwOut=list(struct.unpack("BBBB", data[190:194])),
        SwVideo=data[194],
        SwMacro=data[195],
        SwRemote=data[196],
        Spare1=data[197],
        Spare2=data[198],
        Spare3=data[199],
        Style=data[200],
        Mac=":".join(
            map(lambda x: format(x, "02x"), struct.unpack("BBBBBB", data[201:207]))
        ),
        BindIp=".".join(map(str, struct.unpack("BBBB", data[207:211]))),
        BindIndex=data[211],
        Status2=data[212],
        Filler=data[213:239].strip(b"\0"),
    )

    return reply


def parse_artdmx(data: bytes) -> dict[str: any] | None:
    if len(data) < 18:
        return None

    reply = dict(
        ProtVer=struct.unpack("<H", data[10:12])[0],
        Sequence=data[12],
        Physical=data[13],
        Universe=struct.unpack("<H", data[14:16])[0],
        Length=struct.unpack(">H", data[16:18])[0],
        Data=data[18:],
    )

    return reply


def parse_nzs(data: bytes) -> dict[str: any] | None:
    if len(data) < 18:
        return None

    reply = dict(
        ProtVer=struct.unpack("<H", data[10:12])[0],
        Sequence=data[12],
        StartCode=data[13],
        Universe=struct.unpack("<H", data[14:16])[0],
        Length=struct.unpack(">H", data[16:18])[0],
        Data=data[18:],
    )

    return reply


def parse_sync(data: bytes) -> dict[str: any] | None:
    if len(data) < 13:
        return None

    reply = dict(
        ProtVer=struct.unpack("<H", data[10:12])[0],
        Aux1=data[12],
        Aux2=data[13],
    )

    return reply


def parse_trigger(data: bytes) -> dict[str: any] | None:
    if len(data) < 18:
        return None

    reply = dict(
        ProtVer=struct.unpack("<H", data[10:12])[0],
        Oem=struct.unpack("<H", data[14:16])[0],
        Key=data[16],
        SubKey=data[17],
        Data=data[18:],
    )

    return reply


def parse_ip_prog(data: bytes) -> dict[str: any] | None:
    if len(data) < 32:
        return None

    reply = dict(
        ProtVer=struct.unpack("<H", data[10:12])[0],
        Filler1=data[12],
        Filler2=data[13],
        Command=data[14],
        Filler4=data[15],
        ProgIp=".".join(map(str, struct.unpack("BBBB", data[16:20]))),
        ProgSm=".".join(map(str, struct.unpack("BBBB", data[20:24]))),
        ProgPort=struct.unpack("<H", data[24:26])[0],
        ProgDg=".".join(map(str, struct.unpack("BBBB", data[24:28]))),
        Spare=data[28:],
    )

    return reply


def parse_ip_prog_reply(data: bytes) -> dict[str: any] | None:
    if len(data) < 34:
        return None

    reply = dict(
        ProtVer=struct.unpack("<H", data[10:12])[0],
        Filler1=data[12],
        Filler2=data[13],
        Filler3=data[14],
        Filler4=data[15],
        ProgIp=".".join(map(str, struct.unpack("BBBB", data[16:20]))),
        ProgSm=".".join(map(str, struct.unpack("BBBB", data[20:24]))),
        ProgPort=struct.unpack("<H", data[24:26])[0],
        Status=data[26],
        Spare2=data[27],
        ProgDg=".".join(map(str, struct.unpack("BBBB", data[28:32]))),
        Spare7=data[32],
        Spare8=data[33],
    )

    return reply


def parse_address(data: bytes) -> dict[str: any] | None:
    if len(data) < 107:
        return None

    reply = dict(
        ProtVer=struct.unpack("<H", data[10:12])[0],
        NetSwitch=data[12],
        BindIndex=data[13],
        ShortName=data[14:32].decode().strip("\0"),
        LongName=data[32:96].decode().strip("\0"),
        SwIn=list(struct.unpack("BBBB", data[96:100])),
        SwOut=list(struct.unpack("BBBB", data[100:104])),
        SubSwitch=data[104],
        AcnPriority=data[105],
        Command=data[106],
    )

    return reply


def parse_command(data: bytes) -> dict[str: any] | None:
    if len(data) < 14:
        return None

    reply = dict(
        ProtVer=struct.unpack("<H", data[10:12])[0],
        EstaMan=struct.unpack("<H", data[12:14])[0],
        Length=struct.unpack("<H", data[14:16])[0],
        Command=data[16:].decode().strip("\0"),
    )

    """
    Command
    - "SwoutText=Playback&" re-programme the label ArtPollReply->Swout
    - "SwinText=Record&" re-programme the label ArtPollReply->Swout
    """

    return reply


# Dictionary of parsers
ARTNET_REPLY_PARSER = {
    OpCode.ArtPoll: parse_poll,
    OpCode.ArtPollReply: parse_poll_reply,
    OpCode.ArtTrigger: parse_trigger,
    OpCode.ArtDmx: parse_artdmx,
    OpCode.ArtNzs: parse_nzs,
    OpCode.ArtSync: parse_sync,
    OpCode.ArtIpProg: parse_ip_prog,
    OpCode.ArtIpProgReply: parse_ip_prog_reply,
    OpCode.ArtAddress: parse_address,
    OpCode.ArtCommand: parse_command,
}


def pack_ip(
    dhcp: bool = False,
    prog_ip: str | None = None,
    prog_sm: str | None = None,
    prog_gw: str | None = None,
    set_default: bool = False,
    prog_port: int | None = None,
) -> bytes:
    # Convert IP, subnet mask, and gateway to bytes
    ip_bytes = (
        struct.pack("BBBB", *map(int, prog_ip.split(".")))
        if prog_ip
        else b"\x00\x00\x00\x00"
    )
    sm_bytes = (
        struct.pack("BBBB", *map(int, prog_sm.split(".")))
        if prog_sm
        else b"\x00\x00\x00\x00"
    )
    gw_bytes = (
        struct.pack("BBBB", *map(int, prog_gw.split(".")))
        if prog_gw
        else b"\x00\x00\x00\x00"
    )

    # Set the command byte (bit 0 is for DHCP, bits 1-7 are reserved)
    # If all bits are clear, this is an enquiry only.
    #   7   Set to enable any programming.
    #   6   Set to enable DHCP (if set ignore lower bits).
    #   5   Not used, transmit as zero
    #   4   Program Default gateway
    #   3   Set to return all three parameters to default
    #   2   Program IP Address
    #   1   Program Subnet Mask
    #   0   Program Port

    command = 0

    if dhcp:
        command |= 1 << 6
    else:
        if prog_gw:
            command |= 1 << 4

        if set_default:
            command |= 1 << 3

        if prog_ip:
            command |= 1 << 2

        if prog_sm:
            command |= 1 << 1

        if prog_port is not None:
            command |= 1 << 0

    port_bytes = struct.pack("<H", prog_port if prog_port is not None else 0)

    if command > 0:
        command |= 1 << 7

    command_byte = struct.pack("<B", command)

    op_code = struct.pack("<H", OpCode.ArtIpProg)
    packet = (
        ART_NET_HEADER
        + op_code
        + ART_NET_VERSION
        + b"\x00" * 2  # Filler 1 + 2
        + command_byte  # Command
        + b"\x00"  # Filler 4
        + ip_bytes  # Programmed IP
        + sm_bytes  # Programmed subnet mask
        + port_bytes  # Programmed Port (Deprecated)
        + gw_bytes  # Programmed gateway
        + b"\x00" * 4  # Spare
    )

    return packet


def pack_address(
    net: int, sub: int, universe: int, port_name: str = "", long_name: str = ""
) -> bytes:
    if not (0 <= net <= 127):
        raise ValueError("Net must be between 0 and 127")
    if not (0 <= sub <= 15):
        raise ValueError("Sub must be between 0 and 15")
    if not (0 <= universe <= 15):
        raise ValueError("Universe must be between 0 and 15")

    command_byte = b"\x00"

    # universe15bit = (net << 8) | (subnet << 4) | universe4bit
    # Bit 0-3 -> universe4bit
    # Bit 4-7 -> subnet
    # Bit 14-8 -> net
    # 15 bit Port-Address in NetSwitch, SubSwitch and SwIn[] or SwOut[]
    # Their values are ignored unless bit 7 is high.
    # I.e. to program a value 0x07, send the value as 0x87.

    # Universe, Net and SubNet
    net_switch = net & 0b1111111
    net_switch_byte = struct.pack("<B", net_switch)

    sub_switch = 1 << 7 | sub & 0b1111
    sub_switch_byte = struct.pack("<B", sub_switch)

    sw_in = 1 << 7 | universe & 0b1111
    sw_in_byte = struct.pack("<B", sw_in)

    sw_out_byte = sw_in_byte

    port_name_byte = port_name.encode("ascii")
    if len(port_name_byte) > 17:
        port_name_byte = port_name_byte[:17]
    port_name_byte += b"\x00" * (18 - len(port_name_byte))

    long_name_byte = long_name.encode("ascii")
    if len(long_name_byte) > 63:
        long_name_byte = long_name_byte[:63]
    long_name_byte += b"\x00" * (64 - len(long_name_byte))

    op_code = struct.pack("<H", OpCode.ArtAddress)
    packet = (
        ART_NET_HEADER
        + op_code
        + ART_NET_VERSION
        + net_switch_byte  # Net switch: Bits 14-8 in bottom 7 bits
        + b"\x00"  # Bind index
        + port_name_byte  # Short name
        + long_name_byte  # Long name
        + sw_in_byte  # SwIn1: Bits 3-0 for input port in bottom 4 bits
        + b"\x00"  # SwIn2
        + b"\x00"  # SwIn3
        + b"\x00"  # SwIn4
        + sw_out_byte  # SwOut1: Bits 3-0 for output port in bottom 4 bits
        + b"\x00"  # SwOut2
        + b"\x00"  # SwOut3
        + b"\x00"  # SwOut4
        + sub_switch_byte  # Sub switch: Bits 7-4 in bottom 4 bits
        + b"\x00"  # AcnPriority
        + command_byte  # Command
    )

    return packet


def pack_poll() -> bytes:
    """
    Bit 0:  deprecated
        1:  0 = Only respond to ArtPoll or ArtAddress
            1 = ArtPollReply on Node change.
        2:  0 = Do not send diagnostics
            1 = Send diagnostics message
        3:  0 = Diagnostics messages are broadcast
            1 = Diagnostics messages are unicast
        4:  0 = Enable VLC transmission
            1 = Disable VLC transmission
        5:  0 = Disable Targeted Mode
            1 = Enable Targeted Mode
        6-7:Unused, transmit as zero
    """
    flags = b"\x00"
    # The lowest priority of diagnostics message to be sent
    diag_prio = b"\x00"
    # If Targeted Mode is active
    # Top of range of Port-Addresses to be tested
    target_port_address_top = struct.pack("<H", 0)
    # Bottom range
    target_port_address_bottom = struct.pack("<H", 0)

    op_code = struct.pack("<H", OpCode.ArtPoll)
    packet = (
        ART_NET_HEADER
        + op_code
        + ART_NET_VERSION
        + flags
        + diag_prio
        + target_port_address_top
        + target_port_address_bottom
        + ART_NET_ESTA_MAN
        + ART_NET_OEM
    )

    return packet


def pack_dmx(universe15bit: int, seq: int, dmx_data: bytearray) -> bytes:
    # Sequence, physical and universe
    sequence = struct.pack("<B", seq)
    physical = struct.pack("<B", 0)
    universe = struct.pack("<H", universe15bit)

    # size = 512
    size = len(dmx_data)

    if size > 512:
        raise ValueError("data too long")

    # Length of DMX data
    dmx_length = struct.pack(">H", size)

    # OpCode
    op_code = struct.pack("<H", OpCode.ArtDmx)

    # Assemble the packet
    packet = (
        ART_NET_HEADER
        + op_code
        + ART_NET_VERSION
        + sequence
        + physical
        + universe
        + dmx_length
        + dmx_data
    )

    return packet


def pack_nzs(
    universe15bit: int, sequence: int, start_code: int, dmx_data: bytearray
) -> bytes:
    # Sequence, start code and universe
    seq = struct.pack("<B", sequence)
    code = struct.pack("<B", start_code)
    universe = struct.pack("<H", universe15bit)

    # size = 512
    size = len(dmx_data)

    if size > 512:
        raise ValueError("data too long")

    # Length of DMX data
    dmx_length = struct.pack(">H", size)


    # OpCode
    op_code = struct.pack("<H", OpCode.ArtNzs)

    # Assemble the packet
    packet = (
        ART_NET_HEADER
        + op_code
        + ART_NET_VERSION
        + seq
        + code
        + universe
        + dmx_length
        + dmx_data
    )

    return packet


def pack_trigger(key: int, subkey: int, data: bytearray = b"") -> bytes:
    key_byte = struct.pack("<B", key)
    subkey_byte = struct.pack("<B", subkey)
    filler = struct.pack("<H", 0x0000)
    op_code = struct.pack("<H", OpCode.ArtTrigger)
    packet = (
        ART_NET_HEADER
        + op_code
        + ART_NET_VERSION
        + filler
        + ART_NET_OEM
        + key_byte
        + subkey_byte
        + data
    )

    return packet


def pack_sync() -> bytes:
    # Aux1 (Int8) and Aux1 (Int8) - Transmit as zero
    aux = b"\x00" * 2
    op_code = struct.pack("<H", OpCode.ArtSync)
    packet = ART_NET_HEADER + op_code + ART_NET_VERSION + aux

    return packet


def pack_cmd(command_data: bytearray | bytes) -> bytes:
    aux = b"\x00" * 4
    op_code = struct.pack("<H", OpCode.ArtCommand)
    packet: bytes = ART_NET_HEADER + op_code + ART_NET_VERSION + aux + command_data + b"\x00"
    return packet
