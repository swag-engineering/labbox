#!/usr/bin/env python3
import argparse
import logging
import math
import os
import pty
from time import sleep

from labbox.defines import Cmd

VALID_SIGNALS = {"sin", "sqr", "tri", "saw"}

def _parse_signals(s: str) -> list[str]:
    parts = s.split(";")
    for sig in parts:
        if sig not in VALID_SIGNALS:
            raise argparse.ArgumentTypeError(f"Unsupported signal: {sig}")
    return parts

def _parse_freqs(s: str) -> list[int]:
    try:
        parts = [int(x) for x in s.split(";")]
    except ValueError:
        raise argparse.ArgumentTypeError("Frequencies must be integers")
    for f in parts:
        if f < 1 or f > 10:
            raise argparse.ArgumentTypeError("Frequency must be in [1, 10]")
    return parts

def _validate_pairing(signals: list[str], freqs: list[int]) -> None:
    if len(signals) != len(freqs):
        raise argparse.ArgumentTypeError(
            f"Got {len(signals)} signal(s) but {len(freqs)} frequency value(s)"
        )

def sqr_func(freq: int, t: float, min_val: int, max_val: int) -> bytes:
    p = 1.0 / freq
    value = max_val if (t % p) > (p / 2.0) else min_val
    return int(value).to_bytes(2, signed=True, byteorder="little")

def tri_func(freq: int, t: float, min_val: int, max_val: int) -> bytes:
    p = 1.0 / freq
    tr = t % p
    span = max_val - min_val
    if tr <= p / 2.0:
        value = int((2 * span * tr) / p) + min_val
    else:
        value = int((2 * span * (p - tr)) / p) + min_val
    return int(value).to_bytes(2, signed=True, byteorder="little")

def saw_func(freq: int, t: float, min_val: int, max_val: int) -> bytes:
    p = 1.0 / freq
    tr = t % p
    value = int(((max_val - min_val) * tr) / p) + min_val
    return int(value).to_bytes(2, signed=True, byteorder="little")

def sin_func(freq: int, t: float, min_val: int, max_val: int) -> bytes:
    amp = (max_val - min_val) / 2.0
    mid = (max_val + min_val) / 2.0
    value = int(math.sin(2.0 * math.pi * freq * t) * amp + mid)
    return int(value).to_bytes(2, signed=True, byteorder="little")

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Signals wave generator. Emulates a USB serial port.",
        epilog=(
            "Examples:\n"
            "  generate a sine at 115200 baud:\n"
            "    labbox-generator -b 115200\n"
            "  two signals at 3 Hz and 4 Hz:\n"
            '    labbox-generator -b 115200 -s "sin;sqr" -f "3;4"\n'
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "-b",
        "--baudrate",
        help="Baudrate used to send data",
        choices=[1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200],
        required=True,
        type=int,
        dest="baudrate",
    )
    parser.add_argument(
        "-f",
        "--frequency",
        help="Frequencies for each signal, integers in [1, 10]. Use ';' to separate multiple values",
        type=_parse_freqs,
        default="1",
        dest="frequency",
    )
    parser.add_argument(
        "-s",
        "--signal",
        help="Signal types. Options: sin, sqr, tri, saw. Use ';' for multiple",
        type=_parse_signals,
        default="sin",
        dest="signals",
    )

    args = parser.parse_args()
    signals = args.signals if isinstance(args.signals, list) else _parse_signals(args.signals)
    freqs = args.frequency if isinstance(args.frequency, list) else _parse_freqs(args.frequency)
    _validate_pairing(signals, freqs)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)s] %(message)s")

    inc_time = 0.01
    max_val = 3000
    min_val = -3000

    master, slave = pty.openpty()
    logging.info("Pseudo serial device: %s", os.ttyname(slave))
    logging.info("Signals: %s  Frequencies: %s", signals, freqs)

    # handshake
    while True:
        cmd = int.from_bytes(os.read(master, 4), byteorder="little")
        if cmd == Cmd.PC_HELLO:
            arr = Cmd.CFG_START.to_bytes(4, byteorder="little")
            arr += len(signals).to_bytes(1, byteorder="little")
            arr += max_val.to_bytes(2, byteorder="little", signed=True)
            arr += min_val.to_bytes(2, byteorder="little", signed=True)
            arr += int(inc_time * 1000).to_bytes(1, byteorder="little")
            for s in signals:
                arr += len(s).to_bytes(1, byteorder="little")
                for ch in s:
                    arr += ord(ch).to_bytes(1, byteorder="little")
            os.write(master, arr)
            break

    # stream
    t = 0.0
    while True:
        arr = Cmd.DATA_START.to_bytes(4, byteorder="little")
        for s, f in zip(signals, freqs):
            f = int(f)
            if s == "sin":
                arr += sin_func(f, t, min_val, max_val)
            elif s == "sqr":
                arr += sqr_func(f, t, min_val, max_val)
            elif s == "saw":
                arr += saw_func(f, t, min_val, max_val)
            elif s == "tri":
                arr += tri_func(f, t, min_val, max_val)
        t += inc_time
        os.write(master, arr)
        sleep(inc_time)

if __name__ == "__main__":
    main()
