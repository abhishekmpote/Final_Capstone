"""Upload extension and payload validation."""

from pathlib import Path

from fastapi import UploadFile

DOCUMENT_EXTENSIONS = {".pdf", ".docx", ".txt"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}


def validate_extension(filename: str, allowed: set[str]) -> str:
    """Return the normalized extension or raise for unsupported files."""
    extension = Path(filename).suffix.lower()
    if extension not in allowed:
        supported = ", ".join(sorted(allowed))
        raise ValueError(f"Unsupported file type. Supported extensions: {supported}.")
    return extension


async def read_upload(upload: UploadFile, max_bytes: int) -> bytes:
    """Read an upload while enforcing a strict maximum byte count."""
    content = await upload.read(max_bytes + 1)
    if len(content) > max_bytes:
        raise ValueError(f"File exceeds the {max_bytes // (1024 * 1024)} MB upload limit.")
    if not content:
        raise ValueError("Empty files cannot be uploaded.")
    return content


def validate_image_payload(content: bytes, extension: str) -> None:
    """Reject image uploads that Pillow cannot decode."""
    from io import BytesIO

    from PIL import Image, UnidentifiedImageError

    try:
        with Image.open(BytesIO(content)) as image:
            actual_format = image.format
            image.verify()
    except (UnidentifiedImageError, OSError) as exc:
        raise ValueError("The uploaded file is not a valid JPG or PNG image.") from exc
    expected_format = "PNG" if extension.lower() == ".png" else "JPEG"
    if actual_format != expected_format:
        raise ValueError("The image content does not match its filename extension.")
