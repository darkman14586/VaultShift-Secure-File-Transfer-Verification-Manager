"""Path Safety Engine — protects against destructive operations."""
import os
import shutil
from pathlib import Path
from typing import List, Tuple


# Paths that must NEVER be used as a destination for destructive ops
_DANGEROUS_PREFIXES = (
    "/",
    "/mnt",
    "/etc",
    "/var",
    "/usr",
    "/boot",
    "/bin",
    "/sbin",
)

# /mnt/user is allowed only if explicitly specified as a subdirectory
_DANGEROUS_EXACT = {"/", "/mnt"}

# Maximum symlink resolution depth to prevent loops
_MAX_SYMLINK_DEPTH = 10


class PathSafetyError(Exception):
    """Raised when path validation fails."""


class PathSafetyEngine:
    """Central safety component for all file operations.

    Every transfer job must pass paths through this engine before proceeding.
    The engine blocks operations that could result in data loss.
    """

    @staticmethod
    def resolve_symlink_safe(path: str, depth: int = _MAX_SYMLINK_DEPTH) -> str:
        """Resolve symlinks with depth limit to avoid loops."""
        try:
            p = Path(path)
            for _ in range(depth):
                if not p.is_symlink():
                    return str(p.resolve(strict=False))
                target = os.readlink(str(p))
                p = Path(target) if not Path(target).is_absolute() else Path(target)
            return str(Path(path).resolve(strict=False))
        except (OSError, ValueError):
            return str(Path(path).resolve(strict=False))

    @classmethod
    def validate_path(cls, path: str) -> Tuple[bool, str]:
        """Validate a single path for safety.

        Returns (is_safe, reason).
        """
        if not path or not path.strip():
            return False, "Empty path"

        p = Path(path)

        # Must be absolute
        if not p.is_absolute():
            return False, f"Path must be absolute: {path}"

        # No traversal sequences
        clean = str(p.resolve())
        if ".." in path.split("/"):
            return False, "Path traversal detected"

        # Dangerous exact matches
        resolved_str = str(p.resolve())
        if resolved_str in _DANGEROUS_EXACT:
            return False, f"Dangerous path blocked: {resolved_str}"

        return True, "OK"

    @classmethod
    def validate_source_dest(
        cls, source: str, dest: str, mode: str = "copy"
    ) -> Tuple[bool, List[str]]:
        """Validate source and destination paths together.

        Returns (is_safe, list_of_errors).
        """
        errors: List[str] = []

        # Validate individual paths
        src_ok, src_msg = cls.validate_path(source)
        if not src_ok:
            errors.append(f"Source: {src_msg}")

        dst_ok, dst_msg = cls.validate_path(dest)
        if not dst_ok:
            errors.append(f"Destination: {dst_msg}")

        if errors:
            return False, errors

        source_resolved = str(Path(source).resolve())
        dest_resolved = str(Path(dest).resolve())

        # Source must exist
        if not os.path.exists(source_resolved):
            errors.append(f"Source does not exist: {source}")

        # Source must be a directory
        if os.path.exists(source_resolved) and not os.path.isdir(source_resolved):
            errors.append(f"Source is not a directory: {source}")

        # Destination parent must exist (dest itself may not yet)
        dest_parent = str(Path(dest_resolved).parent if not os.path.exists(dest_resolved) else Path(dest_resolved))
        if not os.path.exists(dest_parent):
            errors.append(f"Destination parent does not exist: {dest}")

        # Same source/destination check
        if source_resolved == dest_resolved:
            errors.append("Source and destination are identical")

        # Destination inside source (dangerous for MOVE)
        if mode in ("move", "MOVE"):
            if dest_resolved.startswith(source_resolved + "/"):
                errors.append(
                    f"Destination is inside source — this would cause data loss during MOVE"
                )

        # Destination must be writable
        if os.path.exists(dest_parent):
            if not os.access(dest_parent, os.W_OK):
                errors.append(f"Destination is not writable: {dest_parent}")

        return len(errors) == 0, errors

    @classmethod
    def mount_point_valid(cls, path: str) -> Tuple[bool, str]:
        """Check if a mount point / storage location is accessible.

        Returns (is_valid, reason).
        """
        p = Path(path)

        if not p.exists():
            return False, f"Path does not exist: {path}"

        if not p.is_dir():
            return False, f"Not a directory: {path}"

        # Check writability via actual test (not permission bits)
        try:
            test_file = p / ".vaultshift_write_test"
            fd = os.open(str(test_file), os.O_CREAT | os.O_WRONLY, 0o600)
            os.close(fd)
            os.unlink(str(test_file))
        except OSError as e:
            return False, f"Not writable: {e}"

        # Check that statvfs works (filesystem is mounted and responsive)
        try:
            st = os.statvfs(str(p))
            if st.f_blocks == 0 and st.f_bavail == 0:
                return False, "Filesystem appears unmounted or empty"
        except OSError as e:
            return False, f"statvfs failed (unmounted?): {e}"

        # Detect empty mount point (only . and .. exist) — warning, not block
        try:
            contents = list(p.iterdir())
            if len(contents) == 0:
                # Empty is OK — it could be a fresh target
                return True, "Empty but valid"
        except PermissionError:
            pass

        return True, "Valid"

    @classmethod
    def check_free_space(cls, path: str, needed_bytes: int) -> Tuple[bool, int]:
        """Check if enough disk space is available.

        Returns (has_enough, free_bytes).
        """
        try:
            usage = shutil.disk_usage(path)
            return usage.free >= needed_bytes, usage.free
        except OSError:
            return False, 0
