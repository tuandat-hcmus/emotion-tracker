from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.core.config import get_settings

ALLOWED_AUDIO_MIME_TYPES = {
    "audio/wav",
    "audio/x-wav",
    "audio/mpeg",
    "audio/mp3",
    "audio/mp4",
    "audio/x-m4a",
    "audio/ogg",
    "audio/webm",
    "video/webm",
}


def validate_upload_file(file: UploadFile) -> None:
    settings = get_settings()
    extension = Path(file.filename or "").suffix.lower()
    allowed_extensions = {
        item.strip().lower()
        for item in settings.allowed_audio_extensions.split(",")
        if item.strip()
    }

    if not file.filename:
        raise ValueError("Uploaded file must have a name")
    if extension not in allowed_extensions:
        raise ValueError(f"Unsupported audio file extension: {extension or 'unknown'}")
    if file.content_type and file.content_type not in ALLOWED_AUDIO_MIME_TYPES:
        raise ValueError(f"Unsupported audio MIME type: {file.content_type}")

    current_position = file.file.tell()
    file.file.seek(0, 2)
    file_size_bytes = file.file.tell()
    file.file.seek(current_position)

    max_size_bytes = settings.max_upload_mb * 1024 * 1024
    if file_size_bytes > max_size_bytes:
        raise ValueError(f"Uploaded file exceeds max size of {settings.max_upload_mb} MB")


def save_upload_file(file: UploadFile, uploads_dir: str) -> str:
    directory = Path(uploads_dir)
    directory.mkdir(parents=True, exist_ok=True)

    extension = Path(file.filename or "").suffix
    filename = f"{uuid4()}{extension}"
    destination = directory / filename

    with destination.open("wb") as output_file:
        while chunk := file.file.read(1024 * 1024):
            output_file.write(chunk)

    return str(destination)
