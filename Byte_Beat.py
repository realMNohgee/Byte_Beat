#!/usr/bin/env python3
"""Byte_Beat — Generate .wav audio files with pure Python stdlib.

Subcommands:
    tone    Single-frequency sine wave
    dtmf    DTMF tone sequence from a key string
    morse   Text to Morse code audio
    sweep   Frequency sweep (chirp)
"""

from __future__ import annotations

import argparse
import math
import struct
import sys
import wave

SAMPLE_RATE = 44100
SAMPLE_WIDTH = 2  # 16-bit
NUM_CHANNELS = 1  # mono
MAX_AMPLITUDE = 32767  # 2**15 - 1

# ── DTMF table ────────────────────────────────────────────────────────
DTMF_TABLE = {
    '1': (697, 1209), '2': (697, 1336), '3': (697, 1477), 'A': (697, 1633),
    '4': (770, 1209), '5': (770, 1336), '6': (770, 1477), 'B': (770, 1633),
    '7': (852, 1209), '8': (852, 1336), '9': (852, 1477), 'C': (852, 1633),
    '*': (941, 1209), '0': (941, 1336), '#': (941, 1477), 'D': (941, 1633),
}

# ── Morse code table (ITU standard) ───────────────────────────────────
MORSE_TABLE = {
    'A': '.-',   'B': '-...', 'C': '-.-.', 'D': '-..',  'E': '.',
    'F': '..-.', 'G': '--.',  'H': '....', 'I': '..',   'J': '.---',
    'K': '-.-',  'L': '.-..', 'M': '--',   'N': '-.',   'O': '---',
    'P': '.--.', 'Q': '--.-', 'R': '.-.',  'S': '...',  'T': '-',
    'U': '..-',  'V': '...-', 'W': '.--',  'X': '-..-', 'Y': '-.--',
    'Z': '--..',
    '0': '-----', '1': '.----', '2': '..---', '3': '...--', '4': '....-',
    '5': '.....', '6': '-....', '7': '--...', '8': '---..', '9': '----.',
    '.': '.-.-.-', ',': '--..--', '?': '..--..', "'": '.----.',
    '!': '-.-.--', '/': '-..-.',  '(': '-.--.',  ')': '-.--.-',
    '&': '.-...',  ':': '---...', ';': '-.-.-.', '=': '-...-',
    '+': '.-.-.',  '-': '-....-', '_': '..--.-', '"': '.-..-.',
    '$': '...-..-', '@': '.--.-.',
    ' ': ' ',  # word boundary marker
}

MORSE_FREQ = 800  # Hz — standard CW tone


def _wave_sin(t: float, freq: float, volume: float) -> int:
    """Mono 16-bit sample value at time *t* (seconds)."""
    return int(MAX_AMPLITUDE * volume * math.sin(2 * math.pi * freq * t))


def _write_wav(path: str, samples: list[int]) -> None:
    """Write list of 16-bit samples as a mono WAV file."""
    with wave.open(path, 'w') as wf:
        wf.setnchannels(NUM_CHANNELS)
        wf.setsampwidth(SAMPLE_WIDTH)
        wf.setframerate(SAMPLE_RATE)
        packed = struct.pack(f'<{len(samples)}h', *samples)
        wf.writeframes(packed)


def _total_samples(duration: float) -> int:
    return int(SAMPLE_RATE * duration)


# ── Subcommand handlers ───────────────────────────────────────────────

def cmd_tone(args: argparse.Namespace) -> int:
    """Single-frequency sine wave."""
    n = _total_samples(args.duration)
    samples = [
        _wave_sin(i / SAMPLE_RATE, args.freq, args.volume)
        for i in range(n)
    ]
    _write_wav(args.output, samples)
    print(f"Wrote {n} samples ({args.duration}s @ {args.freq} Hz) → {args.output}")
    return 0


def cmd_dtmf(args: argparse.Namespace) -> int:
    """DTMF tone sequence from key string."""
    keys = args.keys.upper()
    invalid = [k for k in keys if k not in DTMF_TABLE]
    if invalid:
        print(f"Error: invalid DTMF keys: {', '.join(invalid)}", file=sys.stderr)
        return 1

    tone_samples = _total_samples(args.duration)
    gap_samples = _total_samples(args.gap)
    all_samples: list[int] = []

    for key in keys:
        lo, hi = DTMF_TABLE[key]
        for i in range(tone_samples):
            t = i / SAMPLE_RATE
            v = (math.sin(2 * math.pi * lo * t) + math.sin(2 * math.pi * hi * t)) / 2.0
            all_samples.append(int(MAX_AMPLITUDE * args.volume * v))
        # gap (silence) after each tone except the last
        all_samples.extend([0] * gap_samples)

    # Trim trailing gap
    if gap_samples > 0 and all_samples:
        all_samples = all_samples[:-gap_samples]

    _write_wav(args.output, all_samples)
    print(f"Wrote DTMF sequence '{args.keys}' ({len(keys)} tones) → {args.output}")
    return 0


def cmd_morse(args: argparse.Namespace) -> int:
    """Text → Morse code audio."""
    text = args.text.upper()
    invalid = [c for c in text if c not in MORSE_TABLE]
    if invalid:
        print(f"Error: unsupported characters: {', '.join(invalid)}", file=sys.stderr)
        return 1

    # WPM → unit duration (seconds). PARIS standard: "PARIS" = 50 dot-units.
    unit = 1.2 / args.wpm
    dit_len = _total_samples(unit)
    dah_len = _total_samples(unit * 3)
    intra_gap = _total_samples(unit)       # between dits/dahs
    char_gap = _total_samples(unit * 3)    # between characters
    word_gap = _total_samples(unit * 7)    # between words

    samples: list[int] = []
    words = text.split()

    for wi, word in enumerate(words):
        for ci, char in enumerate(word):
            code = MORSE_TABLE[char]
            for si, symbol in enumerate(code):
                # tone
                length = dit_len if symbol == '.' else dah_len
                for i in range(length):
                    samples.append(_wave_sin(i / SAMPLE_RATE, MORSE_FREQ, args.volume))
                # gap between symbols within a character
                if si < len(code) - 1:
                    samples.extend([0] * intra_gap)
            # gap between characters within a word
            if ci < len(word) - 1:
                samples.extend([0] * char_gap)
        # gap between words
        if wi < len(words) - 1:
            samples.extend([0] * word_gap)

    _write_wav(args.output, samples)
    print(f"Wrote Morse for '{text}' ({args.wpm} WPM) → {args.output}")
    return 0


def cmd_sweep(args: argparse.Namespace) -> int:
    """Linear frequency sweep (chirp)."""
    n = _total_samples(args.duration)
    f_start = args.start
    f_end = args.end

    samples: list[int] = []
    for i in range(n):
        t = i / SAMPLE_RATE
        # linear frequency sweep → quadratic phase
        freq = f_start + (f_end - f_start) * (t / args.duration)
        phase = 2 * math.pi * (f_start * t + 0.5 * (f_end - f_start) * t * t / args.duration)
        samples.append(int(MAX_AMPLITUDE * args.volume * math.sin(phase)))
        _ = freq  # unused — phase computed directly above

    _write_wav(args.output, samples)
    print(f"Wrote sweep {f_start}→{f_end} Hz ({args.duration}s) → {args.output}")
    return 0


# ── CLI entry point ───────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog='bytebeat',
        description='Byte_Beat — Generate .wav audio files with pure Python stdlib',
    )

    # Shared parent: --output
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        '-o', '--output', default='out.wav',
        help='Output .wav file (default: out.wav)',
    )

    sub = p.add_subparsers(dest='cmd', required=True)

    # --- tone ---
    st = sub.add_parser('tone', parents=[common],
                        help='Single-frequency sine wave')
    st.add_argument('--freq', type=float, default=440.0,
                    help='Frequency in Hz (default: 440)')
    st.add_argument('--duration', type=float, default=1.0,
                    help='Duration in seconds (default: 1.0)')
    st.add_argument('--volume', type=float, default=0.5,
                    help='Volume 0.0–1.0 (default: 0.5)')

    # --- dtmf ---
    sd = sub.add_parser('dtmf', parents=[common],
                        help='DTMF tone sequence')
    sd.add_argument('keys',
                    help='DTMF key string (e.g. "*123#")')
    sd.add_argument('--duration', type=float, default=0.1,
                    help='Duration per tone in seconds (default: 0.1)')
    sd.add_argument('--gap', type=float, default=0.05,
                    help='Gap between tones in seconds (default: 0.05)')
    sd.add_argument('--volume', type=float, default=0.5,
                    help='Volume 0.0–1.0 (default: 0.5)')

    # --- morse ---
    sm = sub.add_parser('morse', parents=[common],
                        help='Text to Morse code audio')
    sm.add_argument('text',
                    help='Text to encode in Morse')
    sm.add_argument('--wpm', type=float, default=20.0,
                    help='Speed in words per minute (default: 20)')
    sm.add_argument('--volume', type=float, default=0.5,
                    help='Volume 0.0–1.0 (default: 0.5)')

    # --- sweep ---
    sw = sub.add_parser('sweep', parents=[common],
                        help='Frequency sweep')
    sw.add_argument('--start', type=float, default=200.0,
                    help='Start frequency in Hz (default: 200)')
    sw.add_argument('--end', type=float, default=2000.0,
                    help='End frequency in Hz (default: 2000)')
    sw.add_argument('--duration', type=float, default=2.0,
                    help='Duration in seconds (default: 2.0)')
    sw.add_argument('--volume', type=float, default=0.5,
                    help='Volume 0.0–1.0 (default: 0.5)')

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    handlers = {
        'tone':  cmd_tone,
        'dtmf':  cmd_dtmf,
        'morse': cmd_morse,
        'sweep': cmd_sweep,
    }

    handler = handlers.get(args.cmd)
    if handler is None:
        parser.print_help()
        return 1

    return handler(args)


if __name__ == '__main__':
    sys.exit(main())
