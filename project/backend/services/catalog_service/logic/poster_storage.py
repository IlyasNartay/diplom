import io
import string
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile
from PIL import Image, ImageOps

from services.catalog_service.config import settings

MAX_POSTER_BYTES = 5 * 1024 * 1024
ALLOWED_INPUT_TYPES = frozenset(
    {
        "image/jpeg",
        "image/png",
        "image/webp",
    }
)


def _poster_dir() -> Path:
    return Path(settings.MEDIA_ROOT) / "posters"


def ensure_media_dirs() -> None:
    _poster_dir().mkdir(parents=True, exist_ok=True)


def _cover_resize_to_canvas(img: Image.Image, width: int, height: int) -> Image.Image:
    """Масштаб с заполнением кадра и центральная обрезка (как object-fit: cover)."""
    src_w, src_h = img.size
    if src_w < 1 or src_h < 1:
        raise ValueError("Invalid image dimensions")

    scale = max(width / src_w, height / src_h)
    new_w = max(1, int(round(src_w * scale)))
    new_h = max(1, int(round(src_h * scale)))
    resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

    left = (new_w - width) // 2
    top = (new_h - height) // 2
    return resized.crop((left, top, left + width, top + height))


def _normalize_poster_to_jpeg(raw: bytes) -> bytes:
    try:
        img = Image.open(io.BytesIO(raw))
        img.load()
    except (OSError, ValueError) as e:
        raise HTTPException(status_code=400, detail="Invalid image file") from e

    img = ImageOps.exif_transpose(img)
    if img.mode in ("RGBA", "P"):
        background = Image.new("RGB", img.size, (255, 255, 255))
        if img.mode == "P":
            img = img.convert("RGBA")
        background.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
        img = background
    elif img.mode != "RGB":
        img = img.convert("RGB")

    w = settings.POSTER_CANVAS_WIDTH
    h = settings.POSTER_CANVAS_HEIGHT
    if w < 32 or h < 32:
        raise HTTPException(status_code=500, detail="POSTER_CANVAS_* misconfigured")

    img = _cover_resize_to_canvas(img, w, h)
    buf = io.BytesIO()
    img.save(
        buf,
        format="JPEG",
        quality=settings.POSTER_JPEG_QUALITY,
        optimize=True,
    )
    out = buf.getvalue()
    if len(out) > MAX_POSTER_BYTES:
        raise HTTPException(status_code=400, detail="Processed poster still too large; try a smaller source")
    return out


async def save_event_poster(file: UploadFile) -> str:
    if not file.content_type:
        raise HTTPException(status_code=400, detail="Missing file content type")

    ctype = file.content_type.split(";", 1)[0].strip().lower()
    if ctype not in ALLOWED_INPUT_TYPES:
        raise HTTPException(status_code=400, detail="Allowed types: JPEG, PNG, WebP")

    raw = await file.read(MAX_POSTER_BYTES + 1)
    if len(raw) > MAX_POSTER_BYTES:
        raise HTTPException(status_code=400, detail="Poster too large (max 5 MB)")

    jpeg_bytes = _normalize_poster_to_jpeg(raw)

    ensure_media_dirs()
    name = f"{uuid.uuid4().hex}.jpg"
    path = _poster_dir() / name
    path.write_bytes(jpeg_bytes)

    rel = f"/media/posters/{name}"
    base = (settings.PUBLIC_MEDIA_BASE_URL or "").rstrip("/")
    if base:
        return f"{base}{rel}"
    return rel


def delete_owned_poster_file(poster_url: str | None) -> None:
    """Удаляет файл с диска, если URL указывает на наш каталог posters (имя = 32 hex + .jpg)."""
    if not poster_url or not poster_url.strip():
        return
    marker = "/media/posters/"
    idx = poster_url.find(marker)
    if idx < 0:
        return
    name = poster_url[idx + len(marker) :].strip()
    if not name or "/" in name or "\\" in name or ".." in name:
        return
    if not name.endswith(".jpg"):
        return
    stem = name[:-4]
    if len(stem) != 32 or any(c not in string.hexdigits for c in stem):
        return
    path = _poster_dir() / name
    try:
        if path.is_file():
            path.unlink()
    except OSError:
        pass
