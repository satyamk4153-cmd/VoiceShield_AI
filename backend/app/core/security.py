import os
import re
import uuid
import tempfile
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from typing import Generator, Set, Optional, Tuple, BinaryIO
import bcrypt
import jwt
from fastapi import HTTPException, UploadFile, status

from app.core.config import settings
from app.core.logging import logger

ALLOWED_EXTENSIONS: Set[str] = {
    ".wav",
    ".mp3",
    ".ogg",
    ".m4a",
    ".flac"
}

ALLOWED_MIME_TYPES: Set[str] = {
    "audio/wav",
    "audio/x-wav",
    "audio/wave",
    "audio/mpeg",
    "audio/mp3",
    "audio/ogg",
    "audio/x-m4a",
    "audio/mp4",
    "audio/flac",
    "audio/x-flac",
    "application/octet-stream"
}

# Magic byte signatures for audio formats
AUDIO_SIGNATURES = {
    "wav": [b"RIFF"],
    "mp3": [b"ID3", b"\xff\xfb", b"\xff\xf3", b"\xff\xf2"],
    "ogg": [b"OggS"],
    "flac": [b"fLaC"],
}


# ==============================================================================
# Authentication & Cryptography
# ==============================================================================

def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against bcrypt hash."""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """Creates a signed JWT access token."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
        "jti": str(uuid.uuid4())
    })
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> dict:
    """Decodes and validates a signed JWT token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has expired.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ==============================================================================
# Upload Security & File Handling
# ==============================================================================

def sanitize_filename(filename: str) -> str:
    """
    Sanitize uploaded filename to strictly prevent directory traversal,
    null-byte injection, or command injection.
    """
    if not filename:
        return f"audio_{uuid.uuid4().hex[:8]}.wav"
    
    # Strip directory components
    basename = os.path.basename(filename)
    # Remove null bytes and non-whitelisted characters
    cleaned = re.sub(r'[^a-zA-Z0-9_\.-]', '_', basename)
    
    name, ext = os.path.splitext(cleaned)
    ext_lower = ext.lower()
    if ext_lower not in ALLOWED_EXTENSIONS:
        return f"{uuid.uuid4().hex[:8]}.wav"
        
    return f"{uuid.uuid4().hex[:8]}_{name[:32]}{ext_lower}"


def verify_audio_magic_bytes(header: bytes) -> Tuple[bool, str]:
    """
    Validates audio file signature / magic bytes directly from file header bytes.
    Does not trust client Content-Type header or extension.
    """
    if len(header) < 4:
        return False, "UNKNOWN"

    # Check WAV (RIFF....WAVE)
    if header.startswith(b"RIFF") and len(header) >= 12 and header[8:12] == b"WAVE":
        return True, "wav"

    # Check MP3
    if header.startswith(b"ID3") or header[:2] in (b"\xff\xfb", b"\xff\xf3", b"\xff\xf2"):
        return True, "mp3"

    # Check OGG
    if header.startswith(b"OggS"):
        return True, "ogg"

    # Check FLAC
    if header.startswith(b"fLaC"):
        return True, "flac"

    # Check M4A / MP4 ftyp
    if len(header) >= 8 and header[4:8] == b"ftyp":
        return True, "m4a"

    return False, "UNKNOWN"


async def save_upload_to_ephemeral_file(upload_file: UploadFile) -> str:
    """
    Securely streams uploaded file to an ephemeral disk location without loading
    the full file into memory at once. Validates magic bytes and maximum size.
    """
    max_bytes = settings.MAX_AUDIO_SIZE_MB * 1024 * 1024
    temp_dir = os.path.join(tempfile.gettempdir(), "sentinelvoice_ephemeral")
    os.makedirs(temp_dir, exist_ok=True)
    
    temp_path = os.path.join(temp_dir, f"ephemeral_{uuid.uuid4().hex}.wav")
    total_bytes = 0
    header_bytes = b""
    is_verified = False
    detected_format = "unknown"

    try:
        with open(temp_path, "wb") as out_file:
            while True:
                chunk = await upload_file.read(64 * 1024)  # 64 KB chunks
                if not chunk:
                    break
                
                total_bytes += len(chunk)
                if total_bytes > max_bytes:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"Audio payload exceeds maximum permissible size of {settings.MAX_AUDIO_SIZE_MB}MB."
                    )

                if not is_verified:
                    header_bytes += chunk[:16]
                    if len(header_bytes) >= 12:
                        valid, detected_format = verify_audio_magic_bytes(header_bytes)
                        if not valid:
                            # Allow WAV header detection or check extension if raw PCM
                            filename = upload_file.filename or ""
                            _, ext = os.path.splitext(filename)
                            if ext.lower() not in ALLOWED_EXTENSIONS:
                                raise HTTPException(
                                    status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                                    detail="Uploaded file signature does not match any authorized audio format (WAV, MP3, OGG, FLAC, M4A)."
                                )
                        is_verified = True

                out_file.write(chunk)

        if total_bytes == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty audio payload provided."
            )

        return temp_path

    except Exception:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass
        raise


@contextmanager
def ephemeral_temp_file(suffix: str = ".wav") -> Generator[str, None, None]:
    """
    Context manager for zero-retention ephemeral file storage.
    Guarantees file deletion upon exit from context.
    """
    temp_dir = os.path.join(tempfile.gettempdir(), "sentinelvoice_ephemeral")
    os.makedirs(temp_dir, exist_ok=True)
    temp_path = os.path.join(temp_dir, f"ephemeral_{uuid.uuid4().hex}{suffix}")
    try:
        yield temp_path
    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception as e:
                logger.warning(f"Could not delete temporary file {temp_path}: {e}")
