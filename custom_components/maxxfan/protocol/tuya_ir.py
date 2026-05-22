"""Tuya IR base64 codec.

Vendored from https://github.com/burkminipup/irdb-to-tuya (MIT-licensed),
which in turn vendored the codec from Mildsunrise's Tuya reverse-engineering
notes (https://gist.github.com/mildsunrise/1d576669b63a260d2cff35fda63ec0b5).
Original work by ``@mildsunrise``; ``@burkminipup`` made it Tuya-ZS06 /
TS1201 / UFO-R11 specific and confirmed it on hardware.

Format summary
--------------

The Tuya IR sub-protocol used by their Zigbee IR-blasters (ZS06, ZS08,
TS1201, Moes UFO-R11) carries an LZSS-compressed payload of unsigned 16-bit
little-endian microsecond durations, base64-encoded.  Each timing alternates
mark / space starting with mark, just like ESPHome's ``RemoteTransmitData``
output.  The compression is a tiny custom variant — single-byte block headers
with a 3-bit length / 5-bit distance split.

This file is small and self-contained on purpose — the goal is to be a drop-
in vendored module rather than yet another PyPI dependency.  All compression
internals are private (``_compress``, ``_decompress``, ``_emit_*``); the
public surface is just :func:`encode_ir` / :func:`decode_ir`.
"""

from __future__ import annotations

import base64
import io
from struct import pack, unpack
from typing import Final

# Distance window for back-references in the LZSS encoder, in bytes.  Bigger
# windows let the encoder de-duplicate longer ranges but yield diminishing
# returns on the kind of input we feed it (~70 microsecond timings).
_WINDOW_SIZE: Final = 2**13
# Maximum match length the encoder will emit.
_MAX_MATCH_LEN: Final = 255 + 9


def encode_ir(signal: list[int], compression_level: int = 2) -> str:
    """Encode a list of µs mark/space timings as a Tuya base64 IR code.

    Args:
        signal: Alternating mark/space durations in microseconds, starting
            with a mark.  Values above 65535 are clamped — the Tuya wire
            format stores each entry as a uint16.
        compression_level: ``0`` to emit literal blocks only (largest output,
            most compatible), ``2`` (default) to emit LZSS back-references
            (smallest output, what every TS1201-class device we've tested
            accepts happily).

    Returns:
        A base64 ASCII string that can be POSTed directly into a Z2M-paired
        IR-blaster's ``ir_code_to_send`` attribute.
    """
    clamped = [min(t, 65535) for t in signal]
    payload = b"".join(pack("<H", t) for t in clamped)
    out = io.BytesIO()
    _compress(out, payload, compression_level)
    return base64.encodebytes(out.getvalue()).decode("ascii").replace("\n", "")


def decode_ir(code: str) -> list[int]:
    """Decode a Tuya base64 IR code back into a list of µs timings.

    Inverse of :func:`encode_ir`.  Used by round-trip tests; not called from
    the integration's runtime path.
    """
    payload = base64.decodebytes(code.encode("ascii"))
    payload = _decompress(io.BytesIO(payload))
    out: list[int] = []
    while payload:
        out.append(unpack("<H", payload[:2])[0])
        payload = payload[2:]
    return out


# ── Internals ────────────────────────────────────────────────────────────


def _decompress(inf: io.BytesIO) -> bytes:
    out = bytearray()
    while header := inf.read(1):
        length_hi, distance_lo = header[0] >> 5, header[0] & 0b11111
        # Both branches must build into a `bytearray` because the back-reference
        # branch needs to grow incrementally; the literal branch could use
        # `bytes` but using `bytearray` for both keeps the type stable.
        block = bytearray()
        if not length_hi:
            # Literal block: length encoded in the low 5 bits (+1), data follows.
            literal_len = distance_lo + 1
            literal = inf.read(literal_len)
            assert len(literal) == literal_len
            block.extend(literal)
        else:
            # Back-reference block: length in the high 3 bits (with an
            # optional follow-up byte when saturated), distance is 13 bits
            # split across the header's low 5 bits and the next byte.
            length = length_hi
            if length == 7:
                length += inf.read(1)[0]
            length += 2
            distance = (distance_lo << 8 | inf.read(1)[0]) + 1
            while len(block) < length:
                # Greedy copy — supports overlapping matches (RLE style).
                chunk = out[-distance:][: length - len(block)]
                block.extend(chunk)
        out.extend(block)
    return bytes(out)


def _emit_literal_blocks(out: io.BytesIO, data: bytes) -> None:
    """Emit ``data`` as one or more 32-byte literal blocks."""
    for i in range(0, len(data), 32):
        chunk = data[i : i + 32]
        out.write(bytes([len(chunk) - 1]))
        out.write(chunk)


def _compress(out: io.BytesIO, data: bytes, level: int = 2) -> None:
    """LZSS-style compress ``data`` into ``out``.

    ``level=0`` skips back-reference search entirely (literal blocks only) —
    larger output but guaranteed to decode on any Tuya firmware revision.
    ``level=2`` is what every TS1201 we've tested accepts.
    """
    if level == 0:
        _emit_literal_blocks(out, data)
        return

    def _find_match(pos: int) -> tuple[int, int] | None:
        """Return ``(length, distance)`` of the longest back-reference at ``pos``."""
        best: tuple[int, int] | None = None
        limit = min(_MAX_MATCH_LEN, len(data) - pos)
        for d in range(1, min(pos, _WINDOW_SIZE) + 1):
            length = 0
            while length < limit and data[pos + length] == data[pos - d + length]:
                length += 1
            if best is None or length > best[0] or (length == best[0] and d < best[1]):
                best = (length, d)
        return best

    pos = 0
    block_start = 0
    while pos < len(data):
        match = _find_match(pos)
        if match and match[0] >= 3:
            # Flush any pending literals before the back-reference.
            _emit_literal_blocks(out, data[block_start:pos])
            length, distance = match
            distance -= 1
            length -= 2
            block = bytearray()
            if length >= 7:
                # Length doesn't fit in 3 bits — emit overflow byte first.
                block.append(length - 7)
                length = 7
            block.insert(0, (length << 5) | (distance >> 8))
            block.append(distance & 0xFF)
            out.write(block)
            pos += match[0]
            block_start = pos
        else:
            pos += 1
    _emit_literal_blocks(out, data[block_start:pos])
