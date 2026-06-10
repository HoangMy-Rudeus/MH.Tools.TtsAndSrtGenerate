# Conversation Script JSON — AI Input Guide
**Version 1.0.0** · TTS & SRT Generator · 2026-06-11 · HADS 1.0.0

---

## AI READING INSTRUCTION

Read `[SPEC]` and `[BUG]` blocks for authoritative facts — they define the exact JSON
structure this tool accepts and the values it supports.
Read `[NOTE]` only if additional context is needed.
`[?]` blocks are unverified.

When generating a script: emit a single JSON object matching Section 2, obey every
constraint in Sections 3–5, use only the speaker IDs in Section 6, and validate against
the rules in Section 7 before returning.

---

## 1. PURPOSE

**[SPEC]**
- This tool converts ONE conversation-script JSON file into audio + subtitles.
- Input: a JSON object describing a multi-speaker conversation (Sections 2–7).
- Output: per input, the files in Section 8 (audio, SRT, subtitles JSON, timeline JSON).
- The input JSON is loaded and validated by `src/services/validator.py`; structure and
  defaults come from `src/models/script.py`.

---

## 2. TOP-LEVEL STRUCTURE

**[SPEC]**
```json
{
  "lesson_id": "string (required)",
  "title": "string (required)",
  "language": "string (optional, default \"en\")",
  "level": "string (optional, default \"B1\")",
  "lines": [ /* required, >= 1 line object — see Section 4 */ ],
  "settings": { /* optional — see Section 5 */ }
}
```

---

## 3. ROOT FIELDS

**[SPEC]**
| Field | Type | Required | Default | Constraints |
|-------|------|----------|---------|-------------|
| `lesson_id` | string | Yes | — | Non-empty. Only letters, digits, `_`, `-`. Used as the output filename stem. |
| `title` | string | Yes | — | Non-empty. Human-readable. |
| `language` | string | No | `"en"` | e.g. `en`, `en-US`, `en-GB`. Not range-checked. |
| `level` | string | No | `"B1"` | CEFR: `A1`,`A2`,`B1`,`B2`,`C1`,`C2`. Not enforced by the validator. |
| `lines` | array | Yes | — | Must contain at least 1 line object. |
| `settings` | object | No | omitted | See Section 5. |

---

## 4. LINE OBJECT FIELDS

**[SPEC]**
Each element of `lines` is an object:
| Field | Type | Required | Default | Constraints (enforced) |
|-------|------|----------|---------|------------------------|
| `id` | integer | Yes | — | Unique within the script. |
| `speaker` | string | Yes | — | Non-empty. A standard speaker ID (Section 6) or a direct engine voice name. |
| `text` | string | Yes | — | Non-empty. Max 5000 characters. |
| `voice` | string | No | null | Direct engine voice override (bypasses speaker→voice mapping). |
| `emotion` | string | No | `"neutral"` | One of: `neutral`, `friendly`, `cheerful`, `serious`, `excited`. |
| `pause_after_ms` | integer | No | `400` | Range 0–10000. Silence inserted after this line. |
| `speech_rate` | float | No | `1.0` | Range 0.5–2.0. Per-line speed multiplier. |

**[NOTE]**
`emotion` is a hint. The current engines (Edge TTS, Kokoro-ONNX) do not strongly vary
delivery by emotion; it is stored and reserved for future engines. `speech_rate` and
`pause_after_ms` DO take effect.

---

## 5. SETTINGS OBJECT FIELDS

**[SPEC]**
| Field | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| `speech_rate` | float | No | `1.0` | Global default speed for lines that do not set their own. Range 0.5–2.0. |
| `initial_silence_ms` | integer | No | `300` | Silence at the very start of the audio. |
| `default_pause_ms` | integer | No | `400` | Pause between lines when a line omits `pause_after_ms`. |

---

## 6. SPEAKER IDS

**[SPEC]**
- A `speaker` is an abstract ID mapped to a real voice per engine in `config/default.yaml`.
- IDs supported by BOTH engines (portable — prefer these):
  `female_us_1`, `female_us_2`, `male_us_1`, `male_us_2`, `female_uk_1`, `male_uk_1`.
- Kokoro engine additionally supports: `female_us_3`, `female_us_4`.
- To bypass mapping, set `voice` to a real engine voice name:
  - Edge: e.g. `en-US-AriaNeural`, `en-US-GuyNeural`, `en-GB-SoniaNeural`.
  - Kokoro: e.g. `af_heart`, `am_adam`, `bf_emma`, `bm_george`.

**[BUG] Unknown speaker causes a validation error**
- Symptom: generation fails with `Line N (id=...): Unknown speaker 'X'. Available: ...`.
- Cause: the `speaker` value is not a key in the active engine's voice map and no valid
  `voice` override / direct voice name was given (`src/services/validator.py`).
- Fix: use a standard speaker ID from this section, OR add `"voice": "<real engine voice>"`
  to that line, OR add the speaker→voice mapping to the config before running.

---

## 7. VALIDATION RULES (ENFORCED)

**[SPEC]**
A script is rejected unless ALL hold:
1. `lesson_id` non-empty and matches `[A-Za-z0-9_-]+`.
2. `title` non-empty.
3. `lines` has ≥ 1 entry.
4. Every line `id` is unique.
5. Every line `speaker` is non-empty (and resolvable — see Section 6 BUG).
6. Every line `text` is non-empty and ≤ 5000 characters.
7. `emotion`, if present, is one of the five valid values.
8. `pause_after_ms` is 0–10000.
9. `speech_rate` is 0.5–2.0.

**[NOTE]**
`language`, `level`, and the `settings` ranges are NOT strictly enforced by the validator;
stick to the documented values anyway for predictable output.

---

## 8. OUTPUT FILES (PER INPUT)

**[SPEC]**
For `lesson_id = "coffee_shop_001"` the tool writes to the output dir:
| File | Description |
|------|-------------|
| `coffee_shop_001.mp3` or `.wav` | Stitched audio (format per config `audio.output_format`). |
| `coffee_shop_001.srt` | SubRip subtitles (`HH:MM:SS,mmm` timestamps). |
| `coffee_shop_001_subtitles.json` | Subtitle array, times in **seconds** — see below. |
| `coffee_shop_001_timeline.json` | Detailed segments with millisecond timing + metadata. |

`*_subtitles.json` shape:
```json
[
  { "startTime": 0.5, "endTime": 7.436, "text": "..." },
  { "startTime": 8.236, "endTime": 14.092, "text": "..." }
]
```

`*_timeline.json` shape (abridged):
```json
{
  "lesson_id": "coffee_shop_001",
  "title": "Ordering Coffee",
  "audio_file": "coffee_shop_001.mp3",
  "srt_file": "coffee_shop_001.srt",
  "duration_ms": 25000,
  "segments": [
    { "id": 1, "speaker": "female_us_1", "text": "...",
      "start_ms": 500, "end_ms": 3500, "audio_duration_ms": 3000 }
  ],
  "metadata": { "engine": "edge", "generated_at": "2026-06-11T10:30:00Z" }
}
```

---

## 9. COMPLETE VALID EXAMPLE

**[SPEC]**
```json
{
  "lesson_id": "coffee_shop_001",
  "title": "Ordering Coffee",
  "language": "en",
  "level": "A2",
  "lines": [
    {
      "id": 1,
      "speaker": "female_us_1",
      "text": "Good morning! Welcome to Coffee House. What can I get for you?",
      "emotion": "cheerful",
      "pause_after_ms": 800
    },
    {
      "id": 2,
      "speaker": "male_us_1",
      "text": "Hi! I'd like a medium cappuccino, please.",
      "emotion": "friendly",
      "pause_after_ms": 600,
      "speech_rate": 1.0
    },
    {
      "id": 3,
      "speaker": "female_us_1",
      "text": "Sure! For here or to go?",
      "emotion": "friendly"
    }
  ],
  "settings": {
    "speech_rate": 1.0,
    "initial_silence_ms": 500,
    "default_pause_ms": 400
  }
}
```

---

## 10. GENERATION CHECKLIST (FOR AI)

**[SPEC]**
Before returning a generated script, confirm:
- [ ] Output is a single JSON object (not wrapped in markdown, not an array).
- [ ] `lesson_id` matches `[A-Za-z0-9_-]+`; `title` non-empty.
- [ ] `lines` non-empty; all `id` values unique and sequential is fine.
- [ ] Every `speaker` is from Section 6 (or has a valid `voice` override).
- [ ] Every `text` ≤ 5000 chars and non-empty.
- [ ] Any `emotion` is one of the five allowed values.
- [ ] Any `pause_after_ms` in 0–10000; any `speech_rate` in 0.5–2.0.

---

## 11. CHANGELOG

**[SPEC]**
- 1.0.0 (2026-06-11): Initial AI input guide. Documents script schema, validation rules,
  speaker IDs, and all four output files including the new `_subtitles.json` (seconds-based).
