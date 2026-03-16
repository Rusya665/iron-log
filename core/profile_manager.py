import json
import os
from typing import List, Optional

PROFILES_FILE = os.path.join(os.path.dirname(__file__), "..", "profiles.json")
LEGACY_CONFIG = os.path.join(os.path.dirname(__file__), "..", "config.json")


class Profile:
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
    ):
        self.name = name
        self.sessions_dir = sessions_dir
        self.output_dir = output_dir
        self.age = age
        self.sex = sex
        self.mass = mass
        self.show_pr = show_pr
        self.show_standards = show_standards
        self.show_milestones = show_milestones

    def to_dict(self):
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
    def __init__(self):
        self.profiles: List[Profile] = []
        self.active_profile_index: int = -1
        self.remember_last_user: bool = True
        self.load_profiles()

    def load_profiles(self):
        if not os.path.exists(PROFILES_FILE):
            # Attempt to migrate from legacy config
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
        except Exception as e:
            print(f"Error loading profiles: {e}")

    def save_profiles(self):
        data = {
            "active_profile_index": self.active_profile_index,
            "remember_last_user": self.remember_last_user,
            "profiles": [p.to_dict() for p in self.profiles],
        }
        with open(PROFILES_FILE, "w") as f:
            json.dump(data, f, indent=4)

    def get_active_profile(self) -> Optional[Profile]:
        if 0 <= self.active_profile_index < len(self.profiles):
            return self.profiles[self.active_profile_index]
        return None

    def add_profile(self, profile: Profile):
        self.profiles.append(profile)
        if self.active_profile_index == -1:
            self.active_profile_index = 0
        self.save_profiles()

    def set_active(self, index: int):
        if 0 <= index < len(self.profiles):
            self.active_profile_index = index
            self.save_profiles()

    def delete_profile(self, index: int):
        if 0 <= index < len(self.profiles):
            self.profiles.pop(index)
            # Adjust active index
            if not self.profiles:
                self.active_profile_index = -1
            elif self.active_profile_index >= len(self.profiles):
                self.active_profile_index = len(self.profiles) - 1
            self.save_profiles()

    def update_profile(self, index: int, profile: Profile):
        if 0 <= index < len(self.profiles):
            self.profiles[index] = profile
            self.save_profiles()
