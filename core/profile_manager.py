import json
import os
import sys
from typing import List, Optional

def get_app_data_dir() -> str:
    """Returns the persistent user application data directory (%APPDATA%\\IronLog or ~/.ironlog)."""
    if sys.platform == "win32":
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
        app_dir = os.path.join(base, "IronLog")
    else:
        app_dir = os.path.join(os.path.expanduser("~"), ".ironlog")
    os.makedirs(app_dir, exist_ok=True)
    return app_dir


_app_data_dir = get_app_data_dir()
PROFILES_FILE = os.path.join(_app_data_dir, "profiles.json")
LEGACY_CONFIG = os.path.join(_app_data_dir, "config.json")
ROOT_PROFILES_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "profiles.json"))


class Profile:
    """
    User configuration profile data.

    :param name: Athlete display name.
    :param sessions_dir: Directory path containing sessions.py.
    :param output_dir: Directory path where generated Excel logs are saved.
    :param age: Optional athlete age in years.
    :param sex: Biological sex ("male" or "female") for strength standards.
    :param mass: Athlete bodyweight in kilograms (0.0 if resolved from session logs).
    :param show_pr: Whether personal record milestones are displayed.
    :param show_standards: Whether strength standards tiers are displayed.
    :param show_milestones: Whether progression milestones are highlighted.
    """

    def __init__(
        self,
        name: str,
        sessions_dir: str,
        output_dir: str,
        age: int = 0,
        sex: str = "male",
        mass: float = 0.0,
        show_pr: bool = True,
        show_standards: bool = True,
        show_milestones: bool = True,
    ) -> None:
        self.name: str = name
        self.sessions_dir: str = sessions_dir
        self.output_dir: str = output_dir
        self.age: int = age
        self.sex: str = sex
        self.mass: float = mass
        self.show_pr: bool = show_pr
        self.show_standards: bool = show_standards
        self.show_milestones: bool = show_milestones

    def to_dict(self) -> dict:
        """
        Convert profile attributes to JSON-serializable dictionary.

        :return: Dictionary representation of the profile.
        """
        return {
            "name": self.name,
            "sessions_dir": self.sessions_dir,
            "output_dir": self.output_dir,
            "age": self.age,
            "sex": self.sex,
            "mass": self.mass,
            "show_pr": self.show_pr,
            "show_standards": self.show_standards,
            "show_milestones": self.show_milestones,
        }


class ProfileManager:
    """
    Manager for loading, saving, and switching athlete user profiles.
    """

    def __init__(self) -> None:
        self.profiles: List[Profile] = []
        self.active_profile_index: int = -1
        self.remember_last_user: bool = True
        self.auto_check_updates: bool = True
        self.load_profiles()

    def load_profiles(self) -> None:
        """
        Load stored profiles from disk, migrating legacy configs if necessary.

        :return: None
        """
        if not os.path.exists(PROFILES_FILE) and os.path.exists(ROOT_PROFILES_FILE):
            try:
                import shutil
                shutil.copy2(ROOT_PROFILES_FILE, PROFILES_FILE)
            except Exception as e:
                print(f"Migration from root profiles.json failed: {e}")

        if not os.path.exists(PROFILES_FILE):
            if os.path.exists(LEGACY_CONFIG):
                try:
                    with open(LEGACY_CONFIG, "r") as f:
                        config = json.load(f)
                        default_profile = Profile(
                            name="Default User",
                            sessions_dir=config.get("sessions_dir", ""),
                            output_dir=config.get("output_dir", ""),
                            sex="male",
                        )
                        self.profiles.append(default_profile)
                        self.active_profile_index = 0
                        self.remember_last_user = True
                        self.save_profiles()
                except Exception as e:
                    print(f"Migration error: {e}")
            return

        try:
            with open(PROFILES_FILE, "r") as f:
                data = json.load(f)
                self.profiles = [Profile(**p) for p in data.get("profiles", [])]
                self.active_profile_index = data.get("active_profile_index", -1)
                self.remember_last_user = data.get("remember_last_user", True)
                self.auto_check_updates = data.get("auto_check_updates", True)
        except Exception as e:
            print(f"Error loading profiles: {e}")
            self.profiles = []
            self.active_profile_index = -1

        if not self.profiles:
            self.active_profile_index = -1
        elif self.active_profile_index < 0 or self.active_profile_index >= len(self.profiles):
            self.active_profile_index = 0

    def save_profiles(self) -> None:
        """
        Persist all registered profiles and active settings to JSON storage.

        :return: None
        """
        data = {
            "active_profile_index": self.active_profile_index,
            "remember_last_user": self.remember_last_user,
            "auto_check_updates": self.auto_check_updates,
            "profiles": [p.to_dict() for p in self.profiles],
        }
        with open(PROFILES_FILE, "w") as f:
            json.dump(data, f, indent=4)

    def get_active_profile(self) -> Optional[Profile]:
        """
        Retrieve currently active user profile.

        :return: Active Profile object or None if no profiles exist.
        """
        if 0 <= self.active_profile_index < len(self.profiles):
            return self.profiles[self.active_profile_index]
        return None

    def add_profile(self, profile: Profile) -> None:
        """
        Add a new profile to the registry and save.

        :param profile: Profile instance to register.
        :return: None
        """
        self.profiles.append(profile)
        if self.active_profile_index == -1:
            self.active_profile_index = 0
        self.save_profiles()

    def set_active(self, index: int) -> None:
        """
        Switch active profile by index.

        :param index: 0-based profile index.
        :return: None
        """
        if 0 <= index < len(self.profiles):
            self.active_profile_index = index
            self.save_profiles()

    def delete_profile(self, index: int) -> None:
        """
        Delete a profile by index and update active profile pointer.

        :param index: 0-based profile index to delete.
        :return: None
        """
        if 0 <= index < len(self.profiles):
            self.profiles.pop(index)
            if not self.profiles:
                self.active_profile_index = -1
            elif self.active_profile_index >= len(self.profiles):
                self.active_profile_index = len(self.profiles) - 1
            self.save_profiles()

    def update_profile(self, index: int, profile: Profile) -> None:
        """
        Update profile data at specified index and save.

        :param index: 0-based profile index to overwrite.
        :param profile: Updated Profile instance.
        :return: None
        """
        if 0 <= index < len(self.profiles):
            self.profiles[index] = profile
            self.save_profiles()
