import os
import subprocess
import tempfile
from typing import Optional, Tuple

import requests
from packaging import version

GITHUB_REPO = "Rusya665/iron-log"
RELEASES_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"


def check_for_updates(
    current_version: str,
) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Checks GitHub for a newer release.
    Returns: (update_available, new_version_string, download_url)
    """
    try:
        response = requests.get(RELEASES_URL, timeout=5)
        response.raise_for_status()
        data = response.json()

        latest_tag = data.get("tag_name", "").lstrip("v")

        if not latest_tag:
            return False, None, None

        # Compare versions
        if version.parse(latest_tag) > version.parse(current_version.lstrip("v")):
            # Find the .exe asset
            download_url = None
            for asset in data.get("assets", []):
                if asset.get("name", "").endswith(".exe"):
                    download_url = asset.get("browser_download_url")
                    break

            if download_url:
                return True, latest_tag, download_url

        return False, None, None
    except Exception:
        # Silently fail on network error, timeouts, etc.
        return False, None, None


def download_and_install_update(download_url: str):
    """
    Downloads the update and launches a batch script to install it silently.
    The batch script will delete the setup file and itself after installation.
    """
    try:
        # 1. Download the file
        temp_dir = tempfile.gettempdir()
        exe_path = os.path.join(temp_dir, "IronLog_Update.exe")

        # Download in chunks
        with requests.get(download_url, stream=True, timeout=10) as r:
            r.raise_for_status()
            with open(exe_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

        # 2. Create the batch script
        # The batch script waits 2 seconds for Python to exit,
        # runs the installer silently, and then deletes the installer and itself.
        bat_content = f"""@echo off
echo Installing IronLog Update...
timeout /t 2 /nobreak > nul
start /wait "" "{exe_path}" /SILENT /CLOSEAPPLICATIONS /RESTARTAPPLICATIONS
del "{exe_path}"
del "%~f0"
"""
        bat_path = os.path.join(temp_dir, "ironlog_install_update.bat")
        with open(bat_path, "w") as f:
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

        # CREATE_NO_WINDOW = 0x08000000
        subprocess.Popen([bat_path], creationflags=0x08000000, env=env)

    except Exception as e:
        print(f"Error downloading or installing update: {e}")
