# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import io
import os
import struct
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import install_linux


APP_INI = (
    b"[App]\n"
    b"Vendor=Volcan\n"
    b"Name=LibreZen\n"
    b"Version=1.0.0\n"
    b"\n[Gecko]\n"
    b"Profile=librezen\n"
)
PNG_128 = b"\x89PNG\r\n\x1a\n" + b"\x00\x00\x00\rIHDR" + struct.pack(">II", 128, 128)


def add_file(archive: tarfile.TarFile, name: str, data: bytes, mode: int = 0o644) -> None:
    info = tarfile.TarInfo(name)
    info.size = len(data)
    info.mode = mode
    archive.addfile(info, io.BytesIO(data))


def valid_archive(path: Path, vendor: str = "Volcan", symlink_target: str | None = None) -> None:
    app_ini = APP_INI.replace(b"Vendor=Volcan", f"Vendor={vendor}".encode())
    with tarfile.open(path, "w:xz") as archive:
        root = tarfile.TarInfo("zen/")
        root.type = tarfile.DIRTYPE
        root.mode = 0o755
        archive.addfile(root)
        add_file(archive, "zen/application.ini", app_ini)
        add_file(archive, "zen/zen", b"#!/bin/sh\nexit 0\n", 0o755)
        add_file(archive, "zen/browser/chrome/icons/default/default128.png", PNG_128)
        if symlink_target is not None:
            link = tarfile.TarInfo("zen/browser/linked-library.so")
            link.type = tarfile.SYMTYPE
            link.linkname = symlink_target
            archive.addfile(link)


class InstallerTests(unittest.TestCase):
    def test_validates_and_extracts_expected_bundle(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive_path = root / "valid.tar.xz"
            valid_archive(archive_path, symlink_target="chrome/icons/default/default128.png")

            plan = install_linux.inspect_archive(archive_path)
            self.assertEqual(plan.version, "1.0.0")
            self.assertEqual(plan.icon_size, (128, 128))

            extracted = root / "extracted"
            install_linux.safe_extract(archive_path, extracted)
            self.assertEqual(
                (extracted / "application.ini").read_bytes(),
                APP_INI,
            )
            self.assertTrue((extracted / "zen").stat().st_mode & 0o111)
            self.assertTrue((extracted / "browser/linked-library.so").is_symlink())

    def test_rejects_wrong_vendor_before_install(self):
        with tempfile.TemporaryDirectory() as temporary:
            archive_path = Path(temporary) / "wrong-vendor.tar.xz"
            valid_archive(archive_path, vendor="Mozilla")
            with self.assertRaises(install_linux.InstallError):
                install_linux.inspect_archive(archive_path)

    def test_rejects_path_traversal(self):
        root = tarfile.TarInfo("zen/")
        root.type = tarfile.DIRTYPE
        info = tarfile.TarInfo("zen/../../outside")
        info.size = 0
        with self.assertRaises(install_linux.InstallError):
            install_linux.validate_members([root, info])

    def test_rejects_symlink_that_escapes_bundle(self):
        root = tarfile.TarInfo("zen/")
        root.type = tarfile.DIRTYPE
        info = tarfile.TarInfo("zen/browser/escape")
        info.type = tarfile.SYMTYPE
        info.linkname = "../../../../outside"
        with self.assertRaises(install_linux.InstallError):
            install_linux.validate_members([root, info])

    def test_install_and_uninstall_preserve_profile_data(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            home = root / "home"
            home.mkdir()
            data_home = root / "xdg-data"
            archive_path = root / "valid.tar.xz"
            valid_archive(archive_path)

            profile_data = home / ".config/librezen/test-profile/keep.txt"
            profile_data.parent.mkdir(parents=True)
            profile_data.write_text("profile data must survive", encoding="utf-8")

            with patch.object(Path, "home", return_value=home), patch.dict(
                os.environ, {"HOME": str(home), "XDG_DATA_HOME": str(data_home)}
            ):
                install_linux.install_archive(archive_path, "user")
                self.assertTrue((home / ".local/opt/librezen/zen").is_file())
                self.assertTrue((home / ".local/bin/librezen").is_file())
                desktop = data_home / "applications/librezen.desktop"
                desktop_text = desktop.read_text(encoding="utf-8")
                self.assertIn(f'Exec="{home}/.local/bin/librezen" %U', desktop_text)
                self.assertIn(
                    f'Exec="{home}/.local/bin/librezen" --private-window %u',
                    desktop_text,
                )
                self.assertIn(
                    f'Exec="{home}/.local/bin/librezen" --ProfileManager %u',
                    desktop_text,
                )
                self.assertTrue((data_home / "icons/hicolor/128x128/apps/librezen.png").is_file())

                install_linux.uninstall("user")

            self.assertFalse((home / ".local/opt/librezen").exists())
            self.assertFalse((home / ".local/bin/librezen").exists())
            self.assertFalse((data_home / "applications/librezen.desktop").exists())
            self.assertFalse((data_home / "icons/hicolor/128x128/apps/librezen.png").exists())
            self.assertEqual(profile_data.read_text(encoding="utf-8"), "profile data must survive")

    def test_render_desktop_rewrites_all_launcher_commands(self):
        launcher = Path("/tmp/LibreZen Test/bin/librezen")
        rendered = install_linux.render_desktop(launcher).decode("utf-8")
        command = install_linux.desktop_quote(str(launcher))

        self.assertIn("Name=LibreZen\n", rendered)
        self.assertIn("Comment=Browse the World Wide Web with tranquility!\n", rendered)
        self.assertIn("Actions=new-private-window;new-window;profilemanager;", rendered)
        self.assertIn(f"Exec={command} %U", rendered)
        self.assertIn(
            f"[Desktop Action new-private-window]\nName=Open a New Private Window\n"
            f"Exec={command} --private-window %u",
            rendered,
        )
        self.assertIn(
            f"[Desktop Action new-window]\nName=Open a New Window\nExec={command} %u",
            rendered,
        )
        self.assertIn(
            f"[Desktop Action profilemanager]\nName=Open the Profile Manager\n"
            f"Exec={command} --ProfileManager %u",
            rendered,
        )
        self.assertIn(f"TryExec={command}", rendered)

    def test_refuses_to_overwrite_existing_launcher(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            home = root / "home"
            home.mkdir()
            data_home = root / "xdg-data"
            archive_path = root / "valid.tar.xz"
            valid_archive(archive_path)
            launcher = home / ".local/bin/librezen"
            launcher.parent.mkdir(parents=True)
            launcher.write_text("owned by the user", encoding="utf-8")

            with patch.object(Path, "home", return_value=home), patch.dict(
                os.environ, {"HOME": str(home), "XDG_DATA_HOME": str(data_home)}
            ):
                with self.assertRaises(install_linux.InstallError):
                    install_linux.install_archive(archive_path, "user")
            self.assertEqual(launcher.read_text(encoding="utf-8"), "owned by the user")


if __name__ == "__main__":
    unittest.main()
