"""
Credential retrieval for the Transition Gate shared secret.

Uses the Windows Credential Manager via ctypes to read Generic credentials
stored under the target name 'TransitionGate'. This avoids any dependency
on the `keyring` library.

The secret is stored as a Generic credential (CRED_TYPE_GENERIC = 1) with
CRED_PERSIST_LOCAL_MACHINE persistence. It must be written once via:

    python -c "
    from boundaries.transition_gate.credential import store_secret
    store_secret('your-hex-secret-here')
    "

Or via the cmdkey-compatible store_secret() function in this module.

Security:
    - The secret is held in memory only for the duration of the calling
      function. Callers should avoid persisting the return value.
    - Never log, serialize, or embed the secret in any output.
    - Per NR-S02 / NR-R06: transient use only.
"""

from __future__ import annotations

import ctypes
import ctypes.wintypes
import os
import platform

# ── Windows API constants ──

CRED_TYPE_GENERIC: int = 1
CRED_TYPE_DOMAIN_PASSWORD: int = 2
CRED_PERSIST_LOCAL_MACHINE: int = 2

DEFAULT_TARGET_NAME: str = "TransitionGate"
DEFAULT_USERNAME: str = os.environ.get("USERNAME", os.environ.get("USER", "USER"))


class _CREDENTIAL(ctypes.Structure):
    """Win32 CREDENTIAL structure for CredReadW / CredWriteW."""

    _fields_ = [
        ("Flags", ctypes.wintypes.DWORD),
        ("Type", ctypes.wintypes.DWORD),
        ("TargetName", ctypes.wintypes.LPWSTR),
        ("Comment", ctypes.wintypes.LPWSTR),
        ("LastWritten", ctypes.wintypes.FILETIME),
        ("CredentialBlobSize", ctypes.wintypes.DWORD),
        ("CredentialBlob", ctypes.POINTER(ctypes.c_ubyte)),
        ("Persist", ctypes.wintypes.DWORD),
        ("AttributeCount", ctypes.wintypes.DWORD),
        ("Attributes", ctypes.c_void_p),
        ("TargetAlias", ctypes.wintypes.LPWSTR),
        ("UserName", ctypes.wintypes.LPWSTR),
    ]


class _CREDENTIAL_WRITE(ctypes.Structure):
    """Win32 CREDENTIAL structure with c_void_p blob for CredWriteW."""

    _fields_ = [
        ("Flags", ctypes.wintypes.DWORD),
        ("Type", ctypes.wintypes.DWORD),
        ("TargetName", ctypes.wintypes.LPWSTR),
        ("Comment", ctypes.wintypes.LPWSTR),
        ("LastWritten", ctypes.wintypes.FILETIME),
        ("CredentialBlobSize", ctypes.wintypes.DWORD),
        ("CredentialBlob", ctypes.c_void_p),
        ("Persist", ctypes.wintypes.DWORD),
        ("AttributeCount", ctypes.wintypes.DWORD),
        ("Attributes", ctypes.c_void_p),
        ("TargetAlias", ctypes.wintypes.LPWSTR),
        ("UserName", ctypes.wintypes.LPWSTR),
    ]


_PCREDENTIAL = ctypes.POINTER(_CREDENTIAL)


def _is_windows() -> bool:
    """Check if we're running on Windows."""
    return platform.system() == "Windows"


def _get_advapi32() -> ctypes.WinDLL:
    """Get the advapi32 DLL handle with correct function signatures."""
    if not _is_windows():
        raise OSError("Credential Manager is only available on Windows")

    advapi32 = ctypes.windll.advapi32  # type: ignore[attr-defined]

    advapi32.CredReadW.restype = ctypes.wintypes.BOOL
    advapi32.CredReadW.argtypes = [
        ctypes.wintypes.LPCWSTR,
        ctypes.wintypes.DWORD,
        ctypes.wintypes.DWORD,
        ctypes.POINTER(_PCREDENTIAL),
    ]

    advapi32.CredWriteW.restype = ctypes.wintypes.BOOL
    advapi32.CredWriteW.argtypes = [
        ctypes.POINTER(_CREDENTIAL_WRITE),
        ctypes.wintypes.DWORD,
    ]

    advapi32.CredFree.restype = None
    advapi32.CredFree.argtypes = [ctypes.c_void_p]

    advapi32.CredDeleteW.restype = ctypes.wintypes.BOOL
    advapi32.CredDeleteW.argtypes = [
        ctypes.wintypes.LPCWSTR,
        ctypes.wintypes.DWORD,
        ctypes.wintypes.DWORD,
    ]

    return advapi32


def get_secret(
    target_name: str = DEFAULT_TARGET_NAME,
) -> str | None:
    """
    Retrieve the shared secret from Windows Credential Manager.

    Reads a Generic credential stored under the given target name.
    Returns the secret as a string, or None if the credential is not found
    or the blob is empty.

    Args:
        target_name: The credential target name. Default: 'TransitionGate'.

    Returns:
        The secret string, or None if not found / empty.

    Raises:
        OSError: If not running on Windows.
    """
    advapi32 = _get_advapi32()
    cred_ptr = _PCREDENTIAL()

    # Try Generic first (our preferred storage type)
    found = advapi32.CredReadW(target_name, CRED_TYPE_GENERIC, 0, ctypes.byref(cred_ptr))

    if not found:
        # Fall back to Domain Password (legacy cmdkey /add storage)
        found = advapi32.CredReadW(target_name, CRED_TYPE_DOMAIN_PASSWORD, 0, ctypes.byref(cred_ptr))

    if not found:
        return None

    try:
        blob_size = cred_ptr.contents.CredentialBlobSize
        if blob_size == 0:
            return None

        blob = bytes(cred_ptr.contents.CredentialBlob[i] for i in range(blob_size))
        return blob.decode("utf-16-le")
    finally:
        advapi32.CredFree(cred_ptr)


def store_secret(
    secret: str,
    target_name: str = DEFAULT_TARGET_NAME,
    username: str = DEFAULT_USERNAME,
    comment: str = "Transition Gate shared HMAC secret",
) -> bool:
    """
    Store the shared secret in Windows Credential Manager as a Generic credential.

    This writes the secret so that get_secret() can retrieve it. The credential
    persists across reboots (CRED_PERSIST_LOCAL_MACHINE).

    Args:
        secret: The secret string to store.
        target_name: The credential target name. Default: 'TransitionGate'.
        username: The username to associate. Default: current user.
        comment: Human-readable comment.

    Returns:
        True if the credential was stored successfully.

    Raises:
        OSError: If not running on Windows or the write fails.
        ValueError: If secret is empty.
    """
    if not secret:
        raise ValueError("secret must not be empty")

    advapi32 = _get_advapi32()

    secret_bytes = secret.encode("utf-16-le")
    blob_buffer = ctypes.create_string_buffer(secret_bytes, len(secret_bytes))

    cred = _CREDENTIAL_WRITE()
    cred.Type = CRED_TYPE_GENERIC
    cred.TargetName = target_name
    cred.UserName = username
    cred.CredentialBlobSize = len(secret_bytes)
    cred.CredentialBlob = ctypes.cast(blob_buffer, ctypes.c_void_p)
    cred.Persist = CRED_PERSIST_LOCAL_MACHINE
    cred.Comment = comment

    ok = advapi32.CredWriteW(ctypes.byref(cred), 0)
    if not ok:
        error_code = ctypes.get_last_error()
        raise OSError(
            f"CredWriteW failed with error code {error_code}. "
            f"Run as the target user ({username}) with sufficient privileges."
        )
    return True


def delete_secret(
    target_name: str = DEFAULT_TARGET_NAME,
) -> bool:
    """
    Delete the credential from Windows Credential Manager.

    Use for emergency revocation per secret_rotation_sop.emergency_revocation.

    Args:
        target_name: The credential target name. Default: 'TransitionGate'.

    Returns:
        True if the credential was deleted, False if it didn't exist.

    Raises:
        OSError: If not running on Windows.
    """
    advapi32 = _get_advapi32()

    # Try Generic first
    ok = advapi32.CredDeleteW(target_name, CRED_TYPE_GENERIC, 0)
    if ok:
        return True

    # Try Domain Password (legacy)
    ok = advapi32.CredDeleteW(target_name, CRED_TYPE_DOMAIN_PASSWORD, 0)
    return bool(ok)


def secret_exists(
    target_name: str = DEFAULT_TARGET_NAME,
) -> bool:
    """
    Check whether the credential exists without retrieving the secret.

    Args:
        target_name: The credential target name. Default: 'TransitionGate'.

    Returns:
        True if a credential with the target name exists.
    """
    secret = get_secret(target_name)
    return secret is not None and len(secret) > 0


# ── CLI entry point ──

if __name__ == "__main__":
    import sys

    usage = (
        "Usage:\n"
        "  python -m boundaries.transition_gate.credential check\n"
        "  python -m boundaries.transition_gate.credential store <secret>\n"
        "  python -m boundaries.transition_gate.credential delete\n"
        "  python -m boundaries.transition_gate.credential get\n"
    )

    if len(sys.argv) < 2:
        print(usage)
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "check":
        exists = secret_exists()
        print(f"TransitionGate credential: {'EXISTS' if exists else 'NOT FOUND'}")
        sys.exit(0 if exists else 1)

    elif command == "store":
        if len(sys.argv) < 3:
            print("Error: secret argument required")
            print(usage)
            sys.exit(1)
        store_secret(sys.argv[2])
        print("Credential stored successfully.")

    elif command == "delete":
        deleted = delete_secret()
        if deleted:
            print("Credential deleted.")
        else:
            print("Credential not found (nothing to delete).")

    elif command == "get":
        val = get_secret()
        if val:
            # Only show first/last 4 chars for safety
            masked = val[:4] + "..." + val[-4:] if len(val) > 12 else "****"
            print(f"Retrieved: {masked} ({len(val)} chars)")
        else:
            print("NOT FOUND")
            sys.exit(1)

    else:
        print(f"Unknown command: {command}")
        print(usage)
        sys.exit(1)
