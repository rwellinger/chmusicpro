"""
MIME Type Configuration for S3 Proxy Service

This module provides explicit MIME type mappings for file extensions.
Priority: Custom mappings first, then fallback to Python's mimetypes library.

Categories:
- Images (Album Covers, Artwork)
- Audio (Lossless, Compressed, Stems)
- Video (Music Videos, Behind-the-Scenes)
- Documents (Lyrics, PDFs, JSON)
- DAW Projects (Cubase, Nuendo, Studio One)
- Audio Tools (Melodyne, SpectraLayers)
- Design Tools (Affinity Suite)
- Archives (ZIP, GZIP, TAR, 7Z, RAR)

Usage:
    from adapters.s3.mime_types_config import MIME_TYPE_MAPPING
"""

MIME_TYPE_MAPPING = {
    # ===== IMAGES (Album Covers, Artwork) =====
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "webp": "image/webp",
    "gif": "image/gif",
    "svg": "image/svg+xml",
    "bmp": "image/bmp",
    "tiff": "image/tiff",
    "tif": "image/tiff",
    "ico": "image/x-icon",
    "heic": "image/heic",
    "heif": "image/heif",
    # ===== AUDIO (Music Production) =====
    # Lossless / Uncompressed (Studio Standard)
    "flac": "audio/flac",  # Free Lossless Audio Codec
    "wav": "audio/wav",  # Waveform Audio
    "aiff": "audio/aiff",  # Audio Interchange File Format
    "aif": "audio/aiff",
    "alac": "audio/alac",  # Apple Lossless
    "ape": "audio/ape",  # Monkey's Audio
    # Compressed (Distribution)
    "mp3": "audio/mpeg",  # MPEG Audio Layer 3
    "aac": "audio/aac",  # Advanced Audio Coding
    "m4a": "audio/mp4",  # MPEG-4 Audio
    "ogg": "audio/ogg",  # Ogg Vorbis
    "opus": "audio/opus",  # Opus Codec
    "wma": "audio/x-ms-wma",  # Windows Media Audio
    "mka": "audio/x-matroska",  # Matroska Audio
    # ===== VIDEO (Music Videos, Behind-the-Scenes) =====
    "mp4": "video/mp4",
    "webm": "video/webm",
    "mov": "video/quicktime",
    "avi": "video/x-msvideo",
    "mkv": "video/x-matroska",
    "flv": "video/x-flv",
    "wmv": "video/x-ms-wmv",
    "m4v": "video/x-m4v",
    # ===== DOCUMENTS (Lyrics, Metadata) =====
    "pdf": "application/pdf",
    "txt": "text/plain",
    "json": "application/json",
    "xml": "application/xml",
    "md": "text/markdown",
    "doc": "application/msword",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "rtf": "application/rtf",
    # ===== DAW PROJECTS =====
    # Steinberg (Cubase, Nuendo, WaveLab)
    "cpr": "application/x-cubase-project",  # Cubase Project
    "npr": "application/x-nuendo-project",  # Nuendo Project
    "npl": "application/x-cubase-notepad",  # Cubase Note Pad Layout
    "csh": "application/x-cubase-preset",  # Cubase Preset
    # PreSonus Studio One
    "song": "application/x-studio-one-song",  # Studio One Song
    "musicloop": "application/x-studio-one-loop",  # Studio One Music Loop
    # Avid Pro Tools
    "ptx": "application/x-protools-session",  # Pro Tools Session
    "ptf": "application/x-protools-session",  # Pro Tools File
    # Apple Logic Pro
    "logic": "application/x-logic-project",  # Logic Project
    "logicx": "application/x-logic-project",  # Logic Pro X Project
    # Ableton Live
    "als": "application/x-ableton-live-set",  # Ableton Live Set
    "alp": "application/x-ableton-live-pack",  # Ableton Live Pack
    # FL Studio
    "flp": "application/x-flstudio-project",  # FL Studio Project
    # Reaper
    "rpp": "application/x-reaper-project",  # Reaper Project
    # ===== AUDIO TOOLS =====
    # Celemony Melodyne
    "mdd": "application/x-melodyne-document",  # Melodyne Document
    # Steinberg SpectraLayers
    "sxp": "application/x-spectralayers-project",  # SpectraLayers Project
    # iZotope RX
    "rxdoc": "application/x-izotope-rx-document",  # iZotope RX Document
    # ===== BAND-IN-A-BOX =====
    "sgu": "application/x-band-in-a-box-style",  # Band-in-a-Box Style
    "mgu": "application/x-band-in-a-box-midi",  # Band-in-a-Box MIDI
    "sg2": "application/x-band-in-a-box-style",  # Band-in-a-Box Style v2
    # ===== AFFINITY SUITE =====
    "afphoto": "application/x-affinity-photo",  # Affinity Photo
    "afdesign": "application/x-affinity-designer",  # Affinity Designer
    "afpub": "application/x-affinity-publisher",  # Affinity Publisher
    # ===== ARCHIVES (Project Backups, Stems) =====
    "zip": "application/zip",
    "gz": "application/gzip",
    "gzip": "application/gzip",
    "tar": "application/x-tar",
    "7z": "application/x-7z-compressed",
    "rar": "application/vnd.rar",
    "bz2": "application/x-bzip2",
    "xz": "application/x-xz",
    # ===== MIDI & NOTATION =====
    "mid": "audio/midi",
    "midi": "audio/midi",
    "musicxml": "application/vnd.recordare.musicxml+xml",
    "mxl": "application/vnd.recordare.musicxml",
}
