#!/usr/bin/env python3
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Install or uninstall a validated LibreZen Linux archive without touching profiles."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shlex
import shutil
import struct
import subprocess
import sys
import tarfile
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

APP_ID = "systems.volcan.librezen"
APP_NAME = "LibreZen"
VENDOR = "Volcan"
PROFILE = "librezen"
ARCHIVE_ROOT = "zen"
MARKER_NAME = ".librezen-install.json"
MAX_MEMBERS = 100_000
MAX_UNPACKED_BYTES = 4 * 1024 * 1024 * 1024
ICON_CANDIDATES = (
    ("browser", "chrome", "icons", "default", "default128.png"),
    ("browser", "chrome", "icons", "default", "default64.png"),
    ("browser", "chrome", "icons", "default", "default48.png"),
    ("browser", "chrome", "icons", "default", "default32.png"),
    ("browser", "chrome", "icons", "default", "default16.png"),
)
DESKTOP_TEMPLATE = (
    Path(__file__).resolve().parents[1] / "packaging" / "linux" / "librezen.desktop"
)


class InstallError(RuntimeError):
    """An expected installer or archive validation error."""


@dataclass(frozen=True)
class ArchivePlan:
    members: dict[tuple[str, ...], tarfile.TarInfo]
    version: str
    icon_data: bytes
    icon_size: tuple[int, int]


@dataclass(frozen=True)
class InstallPaths:
    scope: str
    app_dir: Path
    launcher: Path
    data_home: Path
    desktop: Path
    icon: Path


def absolute(path: Path) -> Path:
    return Path(os.path.abspath(os.fspath(path)))


def user_data_home() -> Path:
    value = os.environ.get("XDG_DATA_HOME", "")
    if value and os.path.isabs(value):
        return absolute(Path(value))
    return absolute(Path.home() / ".local" / "share")


def paths_for(scope: str, icon_size: tuple[int, int], data_home: Path | None = None) -> InstallPaths:
    if scope == "user":
        home = absolute(Path.home())
        data_home = absolute(data_home or user_data_home())
        app_dir = home / ".local" / "opt" / "librezen"
        launcher = home / ".local" / "bin" / "librezen"
    elif scope == "system":
        data_home = Path("/usr/local/share")
        app_dir = Path("/opt/librezen")
        launcher = Path("/usr/local/bin/librezen")
    else:
        raise InstallError(f"Unknown installation scope: {scope}")

    width, height = icon_size
    return InstallPaths(
        scope=scope,
        app_dir=absolute(app_dir),
        launcher=absolute(launcher),
        data_home=absolute(data_home),
        desktop=absolute(data_home / "applications" / "librezen.desktop"),
        icon=absolute(
            data_home / "icons" / "hicolor" / f"{width}x{height}" / "apps" / "librezen.png"
        ),
    )


def _archive_key(name: str, is_directory: bool) -> tuple[str, ...]:
    if not name or "\x00" in name or chr(92) in name or name.startswith("/"):
        raise InstallError(f"Unsafe path in browser archive: {name!r}")

    parts = name.split("/")
    if parts and parts[-1] == "" and is_directory:
        parts.pop()
    if not parts or any(part in ("", ".", "..") for part in parts):
        raise InstallError(f"Unsafe path in browser archive: {name!r}")
    if parts[0] != ARCHIVE_ROOT:
        raise InstallError(
            f"Unexpected archive root {parts[0]!r}; expected only {ARCHIVE_ROOT}/"
        )
    key = tuple(parts[1:])
    if not key and not is_directory:
        raise InstallError("The archive root must be a directory")
    return key


def _symlink_target_key(parent: tuple[str, ...], target: str) -> tuple[str, ...]:
    if not target or "\x00" in target or chr(92) in target or target.startswith("/"):
        raise InstallError(f"Unsafe symbolic-link target: {target!r}")
    result = list(parent)
    for part in target.split("/"):
        if part in ("", "."):
            if part == "":
                raise InstallError(f"Unsafe symbolic-link target: {target!r}")
            continue
        if part == "..":
            if not result:
                raise InstallError(f"Symbolic link escapes the browser directory: {target!r}")
            result.pop()
        else:
            result.append(part)
    return tuple(result)


def _hardlink_target_key(target: str) -> tuple[str, ...]:
    return _archive_key(target, is_directory=False)


def validate_members(infos: list[tarfile.TarInfo]) -> dict[tuple[str, ...], tarfile.TarInfo]:
    if not infos:
        raise InstallError("The archive is empty")
    if len(infos) > MAX_MEMBERS:
        raise InstallError(f"Archive contains too many entries ({len(infos):,})")

    members: dict[tuple[str, ...], tarfile.TarInfo] = {}
    total_size = 0
    for info in infos:
        if not (info.isdir() or info.isreg() or info.issym() or info.islnk()):
            raise InstallError(f"Unsupported special file in archive: {info.name!r}")
        key = _archive_key(info.name, info.isdir())
        if key in members:
            if info.isdir() and members[key].isdir():
                continue
            raise InstallError(f"Duplicate path in archive: {info.name!r}")
        members[key] = info
        if info.isreg():
            if info.size < 0:
                raise InstallError(f"Invalid file size: {info.name!r}")
            total_size += info.size
            if total_size > MAX_UNPACKED_BYTES:
                raise InstallError("Unpacked browser archive exceeds the 4 GiB safety limit")

    if () not in members or not members[()].isdir():
        raise InstallError(f"Archive must contain a top-level {ARCHIVE_ROOT}/ directory")

    # No archive entry may be located beneath a non-directory entry.
    for key in members:
        for length in range(1, len(key)):
            parent = key[:length]
            if parent in members and not members[parent].isdir():
                raise InstallError(f"Archive path is nested beneath a non-directory: {key!r}")

    if (MARKER_NAME,) in members:
        raise InstallError(f"Archive contains reserved installer metadata path: {MARKER_NAME}")

    for key, info in members.items():
        if info.issym():
            _symlink_target_key(key[:-1], info.linkname)
        elif info.islnk():
            target = _hardlink_target_key(info.linkname)
            if target not in members:
                raise InstallError(f"Hard link target is missing: {info.linkname!r}")
            if not (members[target].isreg() or members[target].islnk()):
                raise InstallError(f"Hard link target is not a regular file: {info.linkname!r}")

    for required in (("application.ini",), ("zen",)):
        info = members.get(required)
        if info is None or not info.isreg():
            readable = "/".join((ARCHIVE_ROOT, *required))
            raise InstallError(f"Archive is missing required regular file: {readable}")

    binary_info = members[("zen",)]
    if binary_info.mode & 0o111 == 0:
        raise InstallError("The browser binary in the archive is not marked executable")

    return members


def _member_bytes(archive: tarfile.TarFile, info: tarfile.TarInfo, limit: int) -> bytes:
    if info.size > limit:
        raise InstallError(f"Unexpectedly large metadata/icon file: {info.name!r}")
    stream = archive.extractfile(info)
    if stream is None:
        raise InstallError(f"Could not read archive member: {info.name!r}")
    with stream:
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise InstallError(f"Unexpectedly large metadata/icon file: {info.name!r}")
    return data


def inspect_archive(archive_path: Path) -> ArchivePlan:
    try:
        with tarfile.open(archive_path, mode="r:*") as archive:
            members = validate_members(archive.getmembers())
            app_ini = _member_bytes(archive, members[("application.ini",)], 1024 * 1024).decode(
                "utf-8", errors="replace"
            )

            def field(name: str) -> str | None:
                matches = re.findall(rf"(?m)^{re.escape(name)}=(.*?)\r?$", app_ini)
                return matches[-1].strip() if matches else None

            expected = {"Name": APP_NAME, "Vendor": VENDOR, "Profile": PROFILE}
            wrong = [
                f"{key}={field(key)!r} (expected {value!r})"
                for key, value in expected.items()
                if field(key) != value
            ]
            version = field("Version")
            if wrong:
                raise InstallError(
                    "This archive does not identify as a LibreZen build: " + "; ".join(wrong)
                )
            if not version:
                raise InstallError("The archive application.ini has no Version field")

            icon_info = None
            for candidate in ICON_CANDIDATES:
                info = members.get(candidate)
                if info is not None and info.isreg():
                    icon_info = info
                    break
            if icon_info is None:
                raise InstallError(
                    "The archive has no supported Linux browser icon "
                    "(expected browser/chrome/icons/default/default128.png or a smaller variant)"
                )
            icon_data = _member_bytes(archive, icon_info, 8 * 1024 * 1024)
            if len(icon_data) < 24 or icon_data[:8] != b"\x89PNG\r\n\x1a\n":
                raise InstallError(f"The packaged application icon is not a PNG: {icon_info.name}")
            width, height = struct.unpack(">II", icon_data[16:24])
            if not (1 <= width <= 1024 and 1 <= height <= 1024):
                raise InstallError(f"Invalid PNG dimensions for the application icon: {width}x{height}")

            return ArchivePlan(members, version, icon_data, (width, height))
    except (OSError, tarfile.TarError) as exc:
        raise InstallError(f"Could not read browser archive {archive_path}: {exc}") from exc


def _safe_file_mode(mode: int) -> int:
    result = mode & 0o755  # preserve executability, but never group/world write or setuid
    return result or 0o644


def safe_extract(archive_path: Path, destination: Path) -> None:
    """Extract only validated ordinary files and safe in-root links."""
    destination.mkdir(parents=True, exist_ok=True)
    try:
        with tarfile.open(archive_path, mode="r:*") as archive:
            members = validate_members(archive.getmembers())

            directories: set[tuple[str, ...]] = {()}
            for key, info in members.items():
                if info.isdir():
                    directories.add(key)
                for length in range(1, len(key)):
                    directories.add(key[:length])

            for key in sorted(directories, key=lambda item: (len(item), item)):
                if not key:
                    continue
                path = destination.joinpath(*key)
                path.mkdir(mode=0o755, parents=False, exist_ok=True)
                if path.is_symlink() or not path.is_dir():
                    raise InstallError(f"Unexpected directory conflict while extracting: {path}")

            for key, info in members.items():
                if not info.isreg():
                    continue
                target = destination.joinpath(*key)
                source = archive.extractfile(info)
                if source is None:
                    raise InstallError(f"Could not extract archive member: {info.name!r}")
                with source, target.open("xb") as output:
                    shutil.copyfileobj(source, output, length=1024 * 1024)
                target.chmod(_safe_file_mode(info.mode))

            pending_hardlinks = [(key, info) for key, info in members.items() if info.islnk()]
            while pending_hardlinks:
                remaining = []
                progress = False
                for key, info in pending_hardlinks:
                    target_key = _hardlink_target_key(info.linkname)
                    target = destination.joinpath(*target_key)
                    if target.exists() and target.is_file() and not target.is_symlink():
                        os.link(target, destination.joinpath(*key))
                        progress = True
                    else:
                        remaining.append((key, info))
                if not progress:
                    raise InstallError("Could not safely resolve hard links in the browser archive")
                pending_hardlinks = remaining

            for key, info in members.items():
                if not info.issym():
                    continue
                _symlink_target_key(key[:-1], info.linkname)
                destination.joinpath(*key).symlink_to(info.linkname)

            for key in sorted(directories, key=lambda item: (-len(item), item)):
                if key:
                    destination.joinpath(*key).chmod(0o755)
    except (OSError, tarfile.TarError) as exc:
        raise InstallError(f"Could not safely extract browser archive: {exc}") from exc


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def desktop_quote(argument: str) -> str:
    # Desktop Entry Exec quoting is not shell quoting; escape reserved characters per spec.
    escaped = argument.replace("%", "%%")
    for character in (chr(92), '"', '$', chr(96)):
        escaped = escaped.replace(character, chr(92) + character)
    return '"' + escaped + '"'


def render_launcher(binary_path: Path) -> bytes:
    command = shlex.quote(str(binary_path))
    return f"#!/bin/sh\nexec {command} \"$@\"\n".encode("utf-8")


def render_desktop(launcher: Path) -> bytes:
    if not DESKTOP_TEMPLATE.is_file():
        raise InstallError(f"Desktop-entry template is missing: {DESKTOP_TEMPLATE}")
    lines = DESKTOP_TEMPLATE.read_text(encoding="utf-8").splitlines()
    exec_lines = [i for i, line in enumerate(lines) if line.startswith("Exec=")]
    tryexec_lines = [i for i, line in enumerate(lines) if line.startswith("TryExec=")]
    if len(exec_lines) != 1:
        raise InstallError("Desktop-entry template must contain exactly one Exec= line")
    lines[exec_lines[0]] = f"Exec={desktop_quote(str(launcher))} %U"
    if len(tryexec_lines) > 1:
        raise InstallError("Desktop-entry template contains more than one TryExec= line")
    if tryexec_lines:
        lines[tryexec_lines[0]] = f"TryExec={desktop_quote(str(launcher))}"
    else:
        lines.insert(exec_lines[0] + 1, f"TryExec={desktop_quote(str(launcher))}")
    return ("\n".join(lines) + "\n").encode("utf-8")


def exclusive_write(path: Path, data: bytes, mode: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.librezen-tmp-", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "wb") as output:
            output.write(data)
            output.flush()
            os.fsync(output.fileno())
        temporary.chmod(mode)
        # A hard link creates the destination only if no file appeared there meanwhile.
        os.link(temporary, path)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def _read_marker(app_dir: Path, scope: str) -> dict[str, Any]:
    marker_path = app_dir / MARKER_NAME
    if app_dir.is_symlink() or not app_dir.is_dir():
        raise InstallError(f"Not a LibreZen installation directory: {app_dir}")
    try:
        marker = json.loads(marker_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise InstallError(
            f"{app_dir} has no valid LibreZen installer marker; it was left untouched"
        ) from exc

    if not isinstance(marker, dict) or marker.get("schema_version") != 1:
        raise InstallError(f"{app_dir} has an unsupported or invalid LibreZen install marker")
    if marker.get("app_id") != APP_ID or marker.get("scope") != scope:
        raise InstallError(f"{app_dir} is not a recognized {scope}-wide LibreZen installation")
    if marker.get("app_dir") != str(app_dir):
        raise InstallError("Install marker path does not match the installation directory")
    return marker


def _validate_marker_paths(marker: dict[str, Any], paths: InstallPaths) -> dict[str, tuple[Path, str]]:
    files = marker.get("files")
    if not isinstance(files, dict):
        raise InstallError("Install marker has no managed-file manifest")
    result: dict[str, tuple[Path, str]] = {}
    for name in ("launcher", "desktop", "icon"):
        item = files.get(name)
        if not isinstance(item, dict) or not isinstance(item.get("path"), str):
            raise InstallError(f"Install marker is missing the {name} path")
        checksum = item.get("sha256")
        if not isinstance(checksum, str) or not re.fullmatch(r"[0-9a-f]{64}", checksum):
            raise InstallError(f"Install marker has an invalid {name} checksum")
        result[name] = (Path(item["path"]), checksum)

    launcher = result["launcher"][0]
    desktop = result["desktop"][0]
    icon = result["icon"][0]
    if launcher != paths.launcher or desktop.name != "librezen.desktop":
        raise InstallError("Install marker points outside the expected LibreZen launcher locations")
    data_home = desktop.parent.parent
    if not data_home.is_absolute() or desktop != data_home / "applications" / "librezen.desktop":
        raise InstallError("Install marker has an invalid desktop-entry location")
    if paths.scope == "system" and data_home != Path("/usr/local/share"):
        raise InstallError("System install marker points outside /usr/local/share")
    icon_size = marker.get("icon_size")
    if not isinstance(icon_size, dict):
        raise InstallError("Install marker has invalid icon dimensions")
    width = icon_size.get("width")
    height = icon_size.get("height")
    if not isinstance(width, int) or not isinstance(height, int) or not (1 <= width <= 1024 and 1 <= height <= 1024):
        raise InstallError("Install marker has invalid icon dimensions")
    expected_icon = data_home / "icons" / "hicolor" / f"{width}x{height}" / "apps" / "librezen.png"
    if icon != expected_icon:
        raise InstallError("Install marker points outside the expected LibreZen icon location")
    return result


def refresh_desktop_database(desktop_dir: Path) -> None:
    updater = shutil.which("update-desktop-database")
    if updater and desktop_dir.is_dir():
        subprocess.run(
            [updater, str(desktop_dir)],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )


def install_archive(archive_path: Path, scope: str) -> None:
    archive_path = archive_path.expanduser()
    if not archive_path.is_file():
        raise InstallError(f"Browser archive does not exist: {archive_path}")
    plan = inspect_archive(archive_path)
    paths = paths_for(scope, plan.icon_size)
    targets = (paths.app_dir, paths.launcher, paths.desktop, paths.icon)
    conflicts = [path for path in targets if path.exists() or path.is_symlink()]
    if conflicts:
        lines = "\n".join(f"  - {path}" for path in conflicts)
        raise InstallError(
            "Refusing to overwrite existing paths:\n"
            f"{lines}\nUninstall the existing LibreZen installation first. "
            "Unrecognized files are never overwritten automatically."
        )

    paths.app_dir.parent.mkdir(parents=True, exist_ok=True)
    launcher_data = render_launcher(paths.app_dir / "zen")
    desktop_data = render_desktop(paths.launcher)
    icon_data = plan.icon_data
    marker = {
        "schema_version": 1,
        "app_id": APP_ID,
        "product": APP_NAME,
        "vendor": VENDOR,
        "version": plan.version,
        "scope": scope,
        "app_dir": str(paths.app_dir),
        "icon_size": {"width": plan.icon_size[0], "height": plan.icon_size[1]},
        "files": {
            "launcher": {"path": str(paths.launcher), "sha256": digest(launcher_data)},
            "desktop": {"path": str(paths.desktop), "sha256": digest(desktop_data)},
            "icon": {"path": str(paths.icon), "sha256": digest(icon_data)},
        },
    }

    stage_root = Path(tempfile.mkdtemp(prefix=".librezen-stage-", dir=paths.app_dir.parent))
    staged_app = stage_root / "app"
    installed_app = False
    installed_files: list[tuple[Path, str]] = []
    try:
        safe_extract(archive_path, staged_app)
        ini_text = (staged_app / "application.ini").read_text(encoding="utf-8", errors="replace")
        for key, value in (("Name", APP_NAME), ("Vendor", VENDOR), ("Profile", PROFILE)):
            if not re.search(rf"(?m)^{key}={re.escape(value)}\r?$", ini_text):
                raise InstallError(f"Extracted application.ini failed validation for {key}")
        marker_path = staged_app / MARKER_NAME
        marker_path.write_text(json.dumps(marker, indent=2) + "\n", encoding="utf-8")
        marker_path.chmod(0o644)

        os.rename(staged_app, paths.app_dir)
        installed_app = True
        for destination, data, mode in (
            (paths.launcher, launcher_data, 0o755),
            (paths.desktop, desktop_data, 0o644),
            (paths.icon, icon_data, 0o644),
        ):
            exclusive_write(destination, data, mode)
            installed_files.append((destination, digest(data)))

        print(f"Installed LibreZen {plan.version} ({scope}-wide).")
        print(f"  Browser: {paths.app_dir}")
        print(f"  Command: {paths.launcher}")
        print(f"  Desktop: {paths.desktop}")
        print(f"  Icon:    {paths.icon}")
        print("Browser profiles are kept outside the application directory and were not changed.")
        refresh_desktop_database(paths.desktop.parent)
    except Exception:
        for path, expected_hash in reversed(installed_files):
            try:
                if path.is_file() and not path.is_symlink() and digest(path.read_bytes()) == expected_hash:
                    path.unlink()
            except OSError:
                pass
        if installed_app:
            try:
                marker_check = _read_marker(paths.app_dir, scope)
                if marker_check.get("app_id") == APP_ID:
                    shutil.rmtree(paths.app_dir)
            except (OSError, InstallError):
                pass
        raise
    finally:
        shutil.rmtree(stage_root, ignore_errors=True)


def uninstall(scope: str) -> None:
    home = absolute(Path.home())
    app_dir = absolute(home / ".local" / "opt" / "librezen") if scope == "user" else Path("/opt/librezen")
    if not app_dir.exists() and not app_dir.is_symlink():
        print(f"No {scope}-wide LibreZen application directory found at {app_dir}.")
        return

    marker = _read_marker(app_dir, scope)
    version = marker.get("version", "unknown")
    icon_size = marker.get("icon_size")
    if not isinstance(icon_size, dict):
        raise InstallError("Install marker has invalid icon dimensions")
    width = icon_size.get("width")
    height = icon_size.get("height")
    if not isinstance(width, int) or not isinstance(height, int) or not (1 <= width <= 1024 and 1 <= height <= 1024):
        raise InstallError("Install marker has invalid icon dimensions")
    base_paths = paths_for(scope, (width, height))
    files = _validate_marker_paths(marker, base_paths)

    for name in ("launcher", "desktop", "icon"):
        path, expected_hash = files[name]
        if path.is_symlink():
            print(f"Preserving modified/symlinked {name}: {path}")
            continue
        if not path.exists():
            continue
        if not path.is_file() or digest(path.read_bytes()) != expected_hash:
            print(f"Preserving modified {name}: {path}")
            continue
        path.unlink()
        print(f"Removed {name}: {path}")

    shutil.rmtree(app_dir)
    print(f"Removed LibreZen {version} application files ({scope}-wide).")
    print("Profile/configuration/cache data was not touched.")
    refresh_desktop_database(base_paths.desktop.parent)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Install a validated LibreZen Linux archive without touching browser profiles."
    )
    scope = parser.add_mutually_exclusive_group()
    scope.add_argument("--user", action="store_true", help="install under your home directory (default)")
    scope.add_argument("--system", action="store_true", help="install to /opt and /usr/local; requires root")
    parser.add_argument("--uninstall", action="store_true", help="remove a matching installation; profiles are preserved")
    parser.add_argument("archive", nargs="?", type=Path, help="Mozilla mach package .tar.xz archive")
    args = parser.parse_args()
    if args.uninstall and args.archive is not None:
        parser.error("--uninstall does not take an archive path")
    if not args.uninstall and args.archive is None:
        parser.error("provide a browser archive, or use --uninstall")
    return args


def main() -> int:
    args = parse_args()
    scope = "system" if args.system else "user"
    if scope == "system" and os.geteuid() != 0:
        raise InstallError("System installation requires root; rerun with sudo and --system.")
    if scope == "user" and os.geteuid() == 0:
        raise InstallError("User installation must run as the desktop user, without sudo.")

    if args.uninstall:
        uninstall(scope)
    else:
        install_archive(args.archive, scope)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (InstallError, OSError) as exc:
        print(f"LibreZen installer: {exc}", file=sys.stderr)
        raise SystemExit(1)
