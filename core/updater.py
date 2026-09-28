import os
import subprocess
import tempfile
from typing import Any, Callable, Dict, Optional, Tuple

import requests
from packaging import version

GITHUB_REPO = "Rusya665/iron-log"
RELEASES_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"


def get_update_details(
    current_version: str,
) -> Dict[str, Any]:
    """
    Query GitHub Releases for the latest release metadata.

    :param current_version: Semantic version string of the running application.
    :return: Dictionary containing release metadata (has_update, latest_version, download_url, release_notes, asset_size).
    """
    result: Dict[str, Any] = {
        "has_update": False,
        "current_version": current_version,
        "latest_version": None,
        "download_url": None,
        "release_notes": None,
        "asset_size": 0,
    }
    try:
        headers = {"User-Agent": f"IronLog-Updater/{current_version}"}
        response = requests.get(RELEASES_URL, headers=headers, timeout=(10, 15))
        response.raise_for_status()
        data = response.json()

        latest_tag = data.get("tag_name", "").lstrip("v")
        if not latest_tag:
            return result

        result["latest_version"] = latest_tag
        result["release_notes"] = data.get("body", "")

        # Compare versions
        if version.parse(latest_tag) > version.parse(current_version.lstrip("v")):
            assets = data.get("assets", [])
            selected_asset = None
            for asset in assets:
                name = asset.get("name", "").lower()
                if name.endswith(".exe") and "setup" in name:
                    selected_asset = asset
                    break

            if not selected_asset:
                for asset in assets:
                    if asset.get("name", "").lower().endswith(".exe"):
                        selected_asset = asset
                        break

            if selected_asset:
                result["has_update"] = True
                result["download_url"] = selected_asset.get("browser_download_url")
                result["asset_size"] = selected_asset.get("size", 0)

        return result
    except Exception:
        return result


def check_for_updates(
    current_version: str,
) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Check GitHub for a newer release tag.

    :param current_version: Semantic version string of the running application.
    :return: Tuple of (update_available, new_version_string, download_url).
    """
    details = get_update_details(current_version)
    if details["has_update"]:
        return True, details["latest_version"], details["download_url"]
    return False, None, None


def download_and_install_update(
    download_url: str,
    progress_callback: Optional[Callable[[int, int, float], None]] = None,
) -> Tuple[bool, Optional[str]]:
    """
    Download update installer and launch interactive setup window with progress and completion controls.

    :param download_url: Direct download URL of the setup executable asset.
    :param progress_callback: Optional callback accepting (downloaded_bytes, total_bytes, percentage).
    :return: Tuple of (success, error_message).
    """
    temp_dir = tempfile.gettempdir()
    exe_path = os.path.join(temp_dir, "IronLog_Update.exe")
    bat_path = os.path.join(temp_dir, "ironlog_install_update.bat")

    try:
        # Download in chunks
        headers = {"User-Agent": "IronLog-Updater"}
        with requests.get(download_url, stream=True, timeout=(15, 60), headers=headers) as r:
            r.raise_for_status()
            total_size = int(r.headers.get("content-length", 0))
            downloaded = 0
            with open(exe_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=65536):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback:
                            percent = (downloaded / total_size * 100) if total_size > 0 else 0.0
                            progress_callback(downloaded, total_size, min(percent, 100.0))

        if not os.path.exists(exe_path) or os.path.getsize(exe_path) == 0:
            return False, "Downloaded update installer was empty or invalid."

        # Batch script: wait for IronLog to exit, launch interactive installer with progress & finish controls, clean up
        bat_content = f"""@echo off
ping 127.0.0.1 -n 3 > nul
start "" /wait "{exe_path}"
del /f /q "{exe_path}"
del /f /q "%~f0"
"""
        with open(bat_path, "w", encoding="utf-8") as f:
            f.write(bat_content)


        # Strip PyInstaller env variables so spawned process starts fresh
        env = os.environ.copy()
        keys_to_remove = [
            k for k in env if k.upper().startswith("_PYI_") or k.upper().startswith("_MEI")
        ]
        for k in keys_to_remove:
            env.pop(k, None)

        # DETACHED_PROCESS = 0x00000008, CREATE_NEW_PROCESS_GROUP = 0x00000200
        subprocess.Popen(
            ["cmd.exe", "/c", bat_path],
            creationflags=0x00000008 | 0x00000200,
            env=env,
            close_fds=True,
        )

        return True, None

    except Exception as e:
        if os.path.exists(exe_path):
            try:
                os.remove(exe_path)
            except Exception:
                pass
        return False, str(e)

