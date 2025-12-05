Summary of planning tasks
Build a batch lesson generator that converts scripted English content into synchronized audio and SRT transcripts using Coqui TTS, focused on B2 level and US accent.

Objectives
Primary goal: produce high‑quality, natural US‑accent audio and accurate SRT transcripts for listening practice.

Outputs: one combined audio file and a matching SRT plus a JSON mapping for each lesson.

User experience: easy script creation, reliable preview, and simple export for use in other apps.

Key decisions to make
Batch only versus real‑time generation — choose batch for quality and simplicity.

Voice strategy — select and pin a small set of US‑accent voices and model versions.

Speaker handling — decide single voice or multi‑speaker per lesson.

File formats — choose audio format and subtitle format for compatibility.

Processing scale — determine expected lesson volume and worker scaling.

Core components to plan
Script editor and import for JSON/CSV input with metadata fields.

SRT generator that estimates timing using CPS and supports pause metadata.

TTS worker to synthesize per‑line audio and store artifacts.

Audio stitcher to concatenate, normalize, and produce final audio.

Alignment and QA services for forced alignment, ASR round‑trip, and MOS checks.

Frontend preview and QA dashboard for synchronized playback and reviewer feedback.

Storage and job queue for scalable batch processing and artifact management.

Pipeline and workflow steps
Author or import scripts with speaker, text, voice, emotion, and pause metadata.

Generate initial SRT using CPS estimates and non‑overlapping rules.

Synthesize each subtitle line via Coqui TTS and save per‑line audio.

Concatenate and normalize audio into a single file while preserving segment mapping.

Run forced alignment and ASR checks, adjust timestamps or regenerate flagged lines.

Produce final package containing audio, SRT, and JSON mapping; present job report.

QA, metrics and operational tasks
Automated checks: forced alignment drift thresholds, ASR WER thresholds, MOS proxy thresholds, and overlap detection.

Human review: sample lessons for naturalness, intelligibility, and timing; provide reviewer actions.

Monitoring: track model versioning, voice consistency, job success rates, and storage usage.

Policies: pin model versions, manage licensing, and secure learner data.
