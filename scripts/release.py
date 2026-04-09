import os
import re
import sys
import subprocess
import threading
import tkinter.messagebox as mb
from typing import List, Optional

import requests
import customtkinter as ctk
from packaging import version
from packaging.version import InvalidVersion

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERSION_FILE = os.path.join(ROOT_DIR, "core", "version.py")
ISS_FILE = os.path.join(ROOT_DIR, "installer", "iron_log_setup.iss")
GITHUB_REPO = "Rusya665/iron-log"
RELEASES_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"

if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

class ReleaseManager(ctk.CTk):
    """
    GUI Application for automating Git versioning, tagging, and deployment.
    """

    def __init__(self) -> None:
        """
        Initializes the ReleaseManager application, configures the UI,
        and starts background workers.
        """
        super().__init__()

        self.title("Iron Log - Release Manager")
        self.geometry("900x800")
        
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        self.latest_github_version: str = "Loading..."
        self._build_ui()
        
        threading.Thread(target=self._fetch_latest_version, daemon=True).start()

    def _get_sorted_branches(self) -> List[str]:
        """
        Retrieves a list of local Git branches sorted by commit date (newest first).

        :return: A list of branch names as strings.
        """
        try:
            output = self._run_git([
                "git", "for-each-ref", "--sort=-committerdate", 
                "refs/heads/", "--format=%(refname:short)"
            ])
            return [b for b in output.splitlines() if b.strip()]
        except Exception:
            return ["main"]

    def _get_current_branch(self) -> str:
        """
        Retrieves the name of the currently active Git branch.

        :return: The name of the current branch.
        """
        try:
            return self._run_git(["git", "branch", "--show-current"]).strip()
        except Exception:
            return "main"

    def _build_ui(self) -> None:
        """
        Constructs the graphical user interface components.
        """
        hdr = ctk.CTkFrame(self, fg_color="#1a1a1a", corner_radius=0)
        hdr.pack(fill="x")
        ctk.CTkLabel(hdr, text="Release Manager", font=("Roboto", 24, "bold")).pack(pady=(20, 5))
        ctk.CTkLabel(hdr, text="Automated versioning, tagging, and deployment", font=("Roboto", 13), text_color="#888").pack(pady=(0, 20))

        container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=10)

        branch_frame = ctk.CTkFrame(container)
        branch_frame.pack(fill="x", pady=10, padx=10)

        ctk.CTkLabel(branch_frame, text="Active Branch:", font=("Roboto", 13, "bold")).pack(side="left", padx=20, pady=15)
        
        self.branch_combo = ctk.CTkComboBox(
            branch_frame, 
            values=self._get_sorted_branches(),
            command=self._switch_branch,
            width=200
        )
        self.branch_combo.set(self._get_current_branch())
        self.branch_combo.pack(side="left", padx=5)

        self.btn_new_branch = ctk.CTkButton(
            branch_frame, 
            text="Start New Branch", 
            command=self._create_new_branch,
            width=120
        )
        self.btn_new_branch.pack(side="left", padx=20)

        v_frame = ctk.CTkFrame(container)
        v_frame.pack(fill="x", pady=10, padx=10)

        self.v_github_label = ctk.CTkLabel(v_frame, text=f"Latest on GitHub: {self.latest_github_version}", font=("Roboto", 13))
        self.v_github_label.pack(side="left", padx=20, pady=15)

        ctk.CTkLabel(v_frame, text="New Version:", font=("Roboto", 13, "bold")).pack(side="left", padx=(40, 5))
        self.new_v_entry = ctk.CTkEntry(v_frame, width=120, placeholder_text="e.g. 1.2.0")
        self.new_v_entry.pack(side="left", padx=5)

        ctk.CTkLabel(container, text="Commit Message (displayed in Git history):", font=("Roboto", 13, "bold")).pack(anchor="w", padx=10, pady=(20, 5))
        self.commit_msg_box = ctk.CTkTextbox(container, height=140, font=("Consolas", 12))
        self.commit_msg_box.pack(fill="x", padx=10)
        self.commit_msg_box.insert("1.0", "feat: \n- \n\nfix: \n- ")

        ctk.CTkLabel(container, text="Release Notes (displayed on GitHub Release page):", font=("Roboto", 13, "bold")).pack(anchor="w", padx=10, pady=(20, 5))
        ctk.CTkLabel(container, text="(Leave empty to use the Commit Message instead)", font=("Roboto", 11), text_color="#666").pack(anchor="w", padx=10)
        self.release_msg_box = ctk.CTkTextbox(container, height=140, font=("Consolas", 12))
        self.release_msg_box.pack(fill="x", padx=10)

        self.status_label = ctk.CTkLabel(self, text="Ready", font=("Roboto", 12), text_color="#666")
        self.status_label.pack(pady=5)

        btn_frame = ctk.CTkFrame(self, fg_color="#111", corner_radius=0)
        btn_frame.pack(fill="x", side="bottom")

        self.push_btn = ctk.CTkButton(
            btn_frame, 
            text="PUSH RELEASE", 
            height=50, 
            font=("Roboto", 16, "bold"),
            fg_color="#1B5E20",
            hover_color="#2E7D32",
            command=self._on_push_pressed
        )
        self.push_btn.pack(fill="x", padx=20, pady=15)

    def _switch_branch(self, branch_name: str) -> None:
        """
        Checks out the specified Git branch.

        :param branch_name: The name of the target branch.
        """
        try:
            self._run_git(["git", "checkout", branch_name])
            self._log(f"Switched to branch: {branch_name}", "#4caf50")
            self.branch_combo.set(self._get_current_branch())
        except subprocess.CalledProcessError as e:
            err_msg = e.output.strip() if e.output else str(e)
            mb.showerror("Git Checkout Error", f"Could not switch to {branch_name}.\nEnsure working tree is clean.\n\n{err_msg}")
            self.branch_combo.set(self._get_current_branch())

    def _create_new_branch(self) -> None:
        """
        Prompts the user for a new branch name and creates it.
        """
        dialog = ctk.CTkInputDialog(text="Enter new branch name:", title="New Branch")
        new_branch = dialog.get_input()
        
        if new_branch:
            new_branch = new_branch.strip()
            try:
                self._run_git(["git", "checkout", "-b", new_branch])
                self._log(f"Created and switched to new branch: {new_branch}", "#4caf50")
                self.branch_combo.configure(values=self._get_sorted_branches())
                self.branch_combo.set(new_branch)
            except subprocess.CalledProcessError as e:
                err_msg = e.output.strip() if e.output else str(e)
                mb.showerror("Git Branch Error", f"Could not create branch '{new_branch}'.\n\n{err_msg}")

    def _fetch_latest_version(self) -> None:
        """
        Fetches the latest release version tag from the GitHub API.
        """
        try:
            response = requests.get(RELEASES_URL, timeout=5)
            response.raise_for_status()
            data = response.json()
            latest = data.get("tag_name", "").lstrip("v")
            if latest:
                self.latest_github_version = latest
                self.after(0, lambda: self.v_github_label.configure(text=f"Latest on GitHub: v{latest}"))
        except Exception:
            self.after(0, lambda: self.v_github_label.configure(text="GitHub Status: Offline / Error", text_color="red"))

    def _log(self, text: str, color: str = "#666") -> None:
        """
        Updates the status label in the GUI.

        :param text: The message to display.
        :param color: The hex color code for the text.
        """
        self.after(0, lambda: self.status_label.configure(text=text, text_color=color))

    def _on_push_pressed(self) -> None:
        """
        Validates inputs and initiates the deployment sequence in a background thread.
        """
        new_v = self.new_v_entry.get().strip()
        commit_msg = self.commit_msg_box.get("1.0", "end-1c").strip()
        release_msg = self.release_msg_box.get("1.0", "end-1c").strip()
        
        if not release_msg:
            release_msg = commit_msg

        try:
            parsed_new_v = version.parse(new_v)
        except InvalidVersion:
            mb.showerror("Validation Error", "Invalid version format. Use standard semantic versioning (e.g. 1.2.3, 1.2.3-beta).")
            return

        if self.latest_github_version != "Loading...":
            try:
                parsed_latest_v = version.parse(self.latest_github_version)
                if parsed_new_v <= parsed_latest_v:
                    mb.showerror("Validation Error", f"New version (v{new_v}) must be greater than current version (v{self.latest_github_version}).")
                    return
            except InvalidVersion:
                pass

        if not commit_msg:
            mb.showerror("Validation Error", "Commit message cannot be empty.")
            return

        current_branch = self.branch_combo.get()
        msg = f"Deploy Version: v{new_v}\nTarget Branch: {current_branch}\nCommit: '{commit_msg.splitlines()[0]}...'\n\nCONTINUE?"
        if not mb.askyesno("Final Confirmation", msg):
            return

        self.push_btn.configure(state="disabled", text="PROCESSING...")
        threading.Thread(target=lambda: self._execute_sequence(new_v, commit_msg, release_msg, current_branch), daemon=True).start()

    def _execute_sequence(self, new_v: str, commit_msg: str, release_msg: str, target_branch: str) -> None:
        """
        Executes the Git commands to tag and release the new version.

        :param new_v: The semantic version string to apply.
        :param commit_msg: The commit message for the version update.
        :param release_msg: The release notes for the Git tag.
        :param target_branch: The branch to push the commit and tag to.
        """
        tag_name = f"v{new_v}"
        initial_hash = None
        
        try:
            try:
                initial_hash = self._run_git(["git", "rev-parse", "HEAD"]).strip()
            except RuntimeError:
                pass

            self._log("Updating version files...")
            self._update_file(VERSION_FILE, r'^__version__\s*=\s*".*"[ \t\r]*$', f'__version__ = "{new_v}"')
            self._update_file(ISS_FILE, r'^#define MyAppVersion\s+".*"[ \t\r]*$', f'#define MyAppVersion "{new_v}"')

            self._log("Staging all changes (git add .)...")
            self._run_git(["git", "add", "."])

            self._log("Committing changes...")
            self._run_git(["git", "commit", "-m", commit_msg])

            self._log(f"Pushing to {target_branch} branch...")
            self._run_git(["git", "push", "origin", target_branch])

            self._log(f"Creating tag {tag_name}...")
            temp_msg_file = os.path.join(ROOT_DIR, "temp_release_msg.txt")
            with open(temp_msg_file, "w", encoding="utf-8") as f:
                f.write(release_msg)
            
            self._run_git(["git", "tag", "-a", tag_name, "-F", temp_msg_file])
            os.remove(temp_msg_file)

            self._log(f"Pushing tag {tag_name} to GitHub...")
            self._run_git(["git", "push", "origin", tag_name])

            self._log("SUCCESS! Release pushed.", "#4caf50")
            self.after(0, lambda: mb.showinfo("Success", f"Version {new_v} has been deployed on branch {target_branch}."))
            
        except subprocess.CalledProcessError as e:
            err_msg = e.output.strip() if e.output else str(e)
            self._log("GIT ERROR", "red")
            self._handle_failure(initial_hash, err_msg)
        except subprocess.TimeoutExpired:
            self._log("TIMEOUT ERROR", "red")
            self._handle_failure(initial_hash, "Process timed out after 60 seconds.")
        except Exception as e:
            self._log("ERROR", "red")
            self._handle_failure(initial_hash, str(e))
        finally:
            self.after(0, lambda: self.push_btn.configure(state="normal", text="PUSH RELEASE"))

    def _handle_failure(self, initial_hash: Optional[str], error_message: str) -> None:
        """
        Reverts the repository to the initial hash in case of deployment failure.

        :param initial_hash: The Git commit hash recorded prior to execution.
        :param error_message: The text detailing the cause of the failure.
        """
        if initial_hash:
            try:
                self._run_git(["git", "reset", "--hard", initial_hash])
            except Exception:
                pass
        self.after(0, lambda: mb.showerror("Process Error", f"Deployment failed. Local state reset.\n\nDetails:\n{error_message}"))

    def _update_file(self, path: str, pattern: str, replacement: str) -> None:
        """
        Reads a file, applies a regex replacement, and overwrites the file.

        :param path: The absolute file path to read and write.
        :param pattern: The regular expression pattern to identify target text.
        :param replacement: The string to replace the targeted text.
        """
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        new_content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_content)

    def _run_git(self, cmd: List[str]) -> str:
        """
        Executes a Git subprocess command.

        :param cmd: A list of string arguments comprising the shell command.
        :return: Standard output string from the executed command.
        """
        result = subprocess.run(
            cmd, 
            check=True, 
            text=True, 
            capture_output=True, 
            cwd=ROOT_DIR,
            timeout=60
        )
        return result.stdout

if __name__ == "__main__":
    app = ReleaseManager()
    app.mainloop()