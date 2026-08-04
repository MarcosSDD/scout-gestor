import re
import warnings
from pathlib import Path

from PIL import Image, UnidentifiedImageError
from pypdf import PdfReader
from pypdf.errors import PdfReadError

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator


RUT_REGEX = re.compile(r"^(\d{7,8})-([\dkK])$")
LOGO_PATH_REGEX = re.compile(r"^[A-Za-z0-9_./\\-]+$")
PERSONA_FOTO_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
PERSONA_FOTO_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
PERSONA_FOTO_MAX_SIZE_BYTES = 2 * 1024 * 1024
PERSONA_FOTO_MAX_PIXELS = 20_000_000
PERSONA_FOTO_MAX_DIMENSION = 8_000
CERTIFICADO_EXTENSIONS = {".pdf"}
CERTIFICADO_CONTENT_TYPES = {"application/pdf"}
CERTIFICADO_MAX_SIZE_BYTES = 5 * 1024 * 1024


def normalizar_rut(value: str) -> str:
    raw = value.replace(".", "").replace(" ", "").upper()
    if "-" not in raw and len(raw) > 1:
        raw = f"{raw[:-1]}-{raw[-1]}"
    return raw


def validar_rut(value: str) -> None:
    rut = normalizar_rut(value)
    match = RUT_REGEX.match(rut)
    if not match:
        raise ValidationError("RUT invalido. Formato esperado: 12345678-5")

    numero, digito = match.groups()
    reversed_digits = map(int, reversed(numero))
    factors = [2, 3, 4, 5, 6, 7]
    total = 0
    for index, digit in enumerate(reversed_digits):
        total += digit * factors[index % len(factors)]

    remainder = 11 - (total % 11)
    expected = "0" if remainder == 11 else "K" if remainder == 10 else str(remainder)
    if digito.upper() != expected:
        raise ValidationError("RUT invalido. Digito verificador no coincide")


def validar_url_o_ruta_logo(value: str) -> None:
    if not value:
        return

    raw_value = value.strip()
    if raw_value != value:
        raise ValidationError("La ruta o URL del logo no debe tener espacios al inicio o final")

    if raw_value.startswith(("http://", "https://")):
        validator = URLValidator(schemes=["http", "https"])
        validator(raw_value)
        return

    if "://" in raw_value:
        raise ValidationError("El logo debe ser una URL http/https o una ruta valida del servidor")

    if not LOGO_PATH_REGEX.fullmatch(raw_value):
        raise ValidationError("La ruta del logo contiene caracteres no permitidos")


def validar_foto_persona(value) -> None:
    if not value:
        return

    extension = Path(value.name).suffix.lower()
    if extension not in PERSONA_FOTO_EXTENSIONS:
        raise ValidationError("La foto debe ser un archivo JPG, PNG o WebP")

    content_type = getattr(value, "content_type", None)
    if content_type and content_type not in PERSONA_FOTO_CONTENT_TYPES:
        raise ValidationError("El tipo de archivo de la foto no esta permitido")

    size = getattr(value, "size", None)
    if size is not None and size > PERSONA_FOTO_MAX_SIZE_BYTES:
        raise ValidationError("La foto no puede superar 2 MB")

    try:
        value.seek(0)
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(value) as image:
                image.verify()
        value.seek(0)
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(value) as image:
                width, height = image.size
        value.seek(0)
    except (Image.DecompressionBombError, Image.DecompressionBombWarning, UnidentifiedImageError, OSError, ValueError) as exc:
        raise ValidationError("La foto no contiene una imagen valida") from exc

    if width > PERSONA_FOTO_MAX_DIMENSION or height > PERSONA_FOTO_MAX_DIMENSION or width * height > PERSONA_FOTO_MAX_PIXELS:
        raise ValidationError("Las dimensiones de la foto exceden el limite permitido")


def validar_certificado_inhabilidades(value) -> None:
    if not value:
        return

    # Existing records are represented by a FieldFile whose backing storage is
    # intentionally not opened during model validation. New uploads always
    # provide an in-memory/temporary file and are validated below.
    if getattr(value, "_file", value) is None:
        return

    if Path(value.name).suffix.lower() not in CERTIFICADO_EXTENSIONS:
        raise ValidationError("El certificado debe ser un archivo PDF")
    content_type = getattr(value, "content_type", None)
    if content_type and content_type not in CERTIFICADO_CONTENT_TYPES:
        raise ValidationError("El certificado debe tener tipo PDF")
    size = getattr(value, "size", None)
    if size is not None and size > CERTIFICADO_MAX_SIZE_BYTES:
        raise ValidationError("El certificado no puede superar 5 MB")
    try:
        value.seek(0)
        signature = value.read(5)
        value.seek(0)
    except (AttributeError, OSError, ValueError) as exc:
        raise ValidationError("No fue posible validar el certificado") from exc
    if signature != b"%PDF-":
        raise ValidationError("El certificado no contiene un PDF valido")

    try:
        value.seek(0)
        reader = PdfReader(value)
        if len(reader.pages) < 1:
            raise ValueError("El PDF no contiene paginas")
    except (AttributeError, EOFError, OSError, PdfReadError, ValueError) as exc:
        raise ValidationError("El certificado no contiene un PDF valido") from exc
    finally:
        try:
            value.seek(0)
        except (AttributeError, OSError, ValueError):
            pass
