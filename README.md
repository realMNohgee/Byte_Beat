# Byte_Beat 🔊

**Zero-dependency WAV audio generator — pure Python stdlib.**

Generate `.wav` audio files from the command line using nothing but `wave`, `math`, and `struct`. No pip installs, no system deps, no network calls. Runs anywhere Python 3 runs.

🧰 **[Tool on Hermtica Marketplace](https://hermtica.com/marketplace)**

---

## Quick Start

```bash
python Byte_Beat.py tone                          # 440 Hz, 1 second → out.wav
python Byte_Beat.py dtmf '*123#'                  # DTMF dial sequence
python Byte_Beat.py morse 'SOS'                   # Morse code audio
python Byte_Beat.py sweep --start 200 --end 8000  # Frequency chirp
```

## Subcommands

### `tone` — Single-frequency sine wave

| Flag | Default | Description |
|------|---------|-------------|
| `--freq` | 440 | Frequency in Hz |
| `--duration` | 1.0 | Duration in seconds |
| `--volume` | 0.5 | Amplitude 0.0–1.0 |
| `--output` / `-o` | out.wav | Output file |

```bash
python Byte_Beat.py tone --freq 1000 --duration 0.5 --volume 0.8 -o beep.wav
```

### `dtmf` — DTMF tone sequence

Generates dual-tone multi-frequency signals from a key string. Supports 0–9, *, #, A–D.

| Arg / Flag | Default | Description |
|------------|---------|-------------|
| `keys` | *(required)* | Key string, e.g. `*123#` |
| `--duration` | 0.1 | Duration per tone (seconds) |
| `--gap` | 0.05 | Silence between tones (seconds) |
| `--volume` | 0.5 | Amplitude 0.0–1.0 |
| `--output` / `-o` | out.wav | Output file |

```bash
python Byte_Beat.py dtmf '8675309' --duration 0.08 --gap 0.03
```

### `morse` — Text to Morse code audio

Encodes text as ITU-standard Morse code at 800 Hz. Uses the PARIS standard for WPM timing.

| Arg / Flag | Default | Description |
|------------|---------|-------------|
| `text` | *(required)* | Text to encode |
| `--wpm` | 20 | Words per minute |
| `--volume` | 0.5 | Amplitude 0.0–1.0 |
| `--output` / `-o` | out.wav | Output file |

```bash
python Byte_Beat.py morse 'HELLO WORLD' --wpm 15
```

### `sweep` — Frequency sweep (chirp)

Linear frequency ramp from start to end.

| Flag | Default | Description |
|------|---------|-------------|
| `--start` | 200 | Start frequency (Hz) |
| `--end` | 2000 | End frequency (Hz) |
| `--duration` | 2.0 | Duration (seconds) |
| `--volume` | 0.5 | Amplitude 0.0–1.0 |
| `--output` / `-o` | out.wav | Output file |

```bash
python Byte_Beat.py sweep --start 20 --end 20000 --duration 5 -o chirp.wav
```

## Technical Specs

- **Sample rate**: 44,100 Hz
- **Bit depth**: 16-bit signed PCM
- **Channels**: Mono
- **Dependencies**: None — `wave`, `math`, `struct` (all stdlib)
- **Python**: 3.8+

## One Tool, Many Domains

| Domain | Use Case |
|--------|----------|
| **Testing** | Generate test tones for audio pipelines, VoIP QA |
| **Embedded / IoT** | DTMF sequences for radio/telephony control |
| **Ham Radio** | Practice CW (Morse) at any speed |
| **Education** | Demonstrate wave physics, frequency, harmonics |
| **Sound Design** | Quick sine sweeps for impulse responses, IR measurement |
| **Agentic AI** | Programmatic audio generation for multi-modal agents |

## License

MIT — see [LICENSE](LICENSE).
