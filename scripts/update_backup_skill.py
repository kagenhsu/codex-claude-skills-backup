#!/usr/bin/env python3
"""Update one skill file inside the tracked skills backup tarball."""
import hashlib
import io
import subprocess
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKUP = ROOT / "codex-skills-backup.tar.gz"
TARGET = "skills/dual-ai-workflow/SKILL.md"
SOURCE = ROOT / TARGET


def main() -> None:
    original = subprocess.check_output(["git", "show", f"HEAD:{BACKUP.name}"])
    source_data = SOURCE.read_bytes()

    old_tar = tarfile.open(fileobj=io.BytesIO(original), mode="r:gz")
    out_buffer = io.BytesIO()
    new_tar = tarfile.open(fileobj=out_buffer, mode="w:gz")

    replaced = False
    entries = 0
    for member in old_tar.getmembers():
        if member.name == TARGET:
            info = tarfile.TarInfo(TARGET)
            info.size = len(source_data)
            info.mode = member.mode
            new_tar.addfile(info, io.BytesIO(source_data))
            replaced = True
        else:
            fileobj = old_tar.extractfile(member) if member.isfile() else None
            new_tar.addfile(member, fileobj)
        entries += 1

    if not replaced:
        info = tarfile.TarInfo(TARGET)
        info.size = len(source_data)
        new_tar.addfile(info, io.BytesIO(source_data))
        entries += 1

    old_tar.close()
    new_tar.close()
    BACKUP.write_bytes(out_buffer.getvalue())

    print(
        f"OK: {BACKUP.name} updated, entries={entries}, "
        f"replaced={replaced}, {TARGET} md5={hashlib.md5(source_data).hexdigest()}"
    )


if __name__ == "__main__":
    main()
