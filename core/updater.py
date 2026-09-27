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
    Queries GitHub Releases for the latest release metadata.
    Returns a dictionary containing:
      - has_update: bool
      - current_version: str
      - latest_version: Optional[str]
      - download_url: Optional[str]
      - release_notes: Optional[str]
      - asset_size: int
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
            # Prefer setup installer exe (e.g. IronLog_Setup_v2.0.2.exe)
            selected_asset = None
            for asset in assets:
                name = asset.get("name", "").lower()
                if name.endswith(".exe") and "setup" in name:
                    selected_asset = asset
                    break

            # Fallback to any .exe asset if no setup-named exe is found
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
        # Silently fail on network error, timeouts, etc.
        return result


def check_for_updates(
    current_version: str,
) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Checks GitHub for a newer release.
    Returns: (update_available, new_version_string, download_url)
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
    Downloads the update and launches a batch script to install it silently.
    The batch script will wait for IronLog to exit, run the installer silently,
    restart the updated application, and then delete the setup file and itself.
    Returns: (success: bool, error_message: Optional[str])
    """
    temp_dir = tempfile.gettempdir()
    exe_path = os.path.join(temp_dir, "IronLog_Update.exe")
    bat_path = os.path.join(temp_dir, "ironlog_install_update.bat")

    try:
        # 1. Download the file in chunks
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

        # 2. Create the batch script
        # Note: We use `ping 127.0.0.1 -n 3 > nul` instead of `timeout /t 2`
        # because Windows `timeout` fails with "Input redirection is not supported"
        # when running without an attached console window.
        bat_content = f"""@echo off
echo Installing IronLog Update...
ping 127.0.0.1 -n 3 > nul
start /wait "" "{exe_path}" /SILENT /SUPPRESSMSGBOXES /CLOSEAPPLICATIONS /RESTARTAPPLICATIONS
ping 127.0.0.1 -n 2 > nul
del /f /q "{exe_path}"
del /f /q "%~f0"
"""
        with open(bat_path, "w", encoding="utf-8") as f:
            f.write(bat_content)

        # 3. Launch the batch script detached, without a console window
        # Strip PyInstaller environment variables so the restarted app
        # doesn't try to load DLLs from the old, deleted temp directory.
        env = os.environ.copy()
        keys_to_remove = [
            k
            for k in env
            if k.upper().startswith("_PYI_") or k.upper().startswith("_MEI")
        ]
        for k in keys_to_remove:
            env.pop(k)

        # CREATE_NO_WINDOW = 0x08000000, DETACHED_PROCESS = 0x00000008
        subprocess.Popen(
            ["cmd.exe", "/c", bat_path],
            creationflags=0x08000000 | 0x00000008,
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
        print(f"Error downloading or installing update: {e}")
        return False, str(e)

