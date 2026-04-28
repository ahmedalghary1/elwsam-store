from pathlib import Path

from django.conf import settings

try:
    from PIL import Image, ImageOps
except ImportError:  # pragma: no cover - production fallback if Pillow is absent.
    Image = None
    ImageOps = None


def get_thumbnail_url(image_field, spec="400x400:cover"):
    """Return a cached WebP thumbnail URL for ImageFieldFile values."""
    if not image_field:
        return ""

    try:
        source_path = Path(image_field.path)
        source_name = Path(image_field.name)
        source_url = image_field.url
    except (AttributeError, ValueError):
        return ""

    if Image is None or not source_path.exists():
        return source_url

    try:
        size_spec, mode = _parse_spec(spec)
    except ValueError:
        return source_url

    width, height = size_spec
    stem = source_name.with_suffix("").as_posix()
    thumb_rel = Path("_thumbs") / f"{stem}-{width}x{height}-{mode}.webp"
    thumb_path = Path(settings.MEDIA_ROOT) / thumb_rel
    thumb_url = f"{settings.MEDIA_URL.rstrip('/')}/{thumb_rel.as_posix()}"

    try:
        if not thumb_path.exists() or thumb_path.stat().st_mtime < source_path.stat().st_mtime:
            thumb_path.parent.mkdir(parents=True, exist_ok=True)
            _create_thumbnail(source_path, thumb_path, (width, height), mode)
    except OSError:
        return source_url

    return thumb_url


def _parse_spec(spec):
    size_part, _, mode_part = str(spec).partition(":")
    width_part, _, height_part = size_part.lower().partition("x")
    width = int(width_part)
    height = int(height_part)
    mode = mode_part or "cover"
    if width <= 0 or height <= 0 or mode not in {"cover", "contain"}:
        raise ValueError("Invalid thumbnail spec")
    return (width, height), mode


def _create_thumbnail(source_path, thumb_path, size, mode):
    resample = Image.Resampling.LANCZOS
    with Image.open(source_path) as image:
        image = ImageOps.exif_transpose(image)

        if mode == "cover":
            image = image.convert("RGB")
            image = ImageOps.fit(image, size, method=resample, centering=(0.5, 0.5))
        else:
            image = image.convert("RGBA")
            image.thumbnail(size, resample)
            canvas = Image.new("RGBA", size, (255, 255, 255, 0))
            left = (size[0] - image.width) // 2
            top = (size[1] - image.height) // 2
            canvas.alpha_composite(image, (left, top))
            image = canvas

        image.save(thumb_path, "WEBP", quality=82, method=6)
