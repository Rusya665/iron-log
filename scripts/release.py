import os
import re
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import messagebox as mb, ttk
from typing import List, Optional

import requests
from packaging import version
from packaging.version import InvalidVersion

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERSION_FILE = os.path.join(ROOT_DIR, "core", "version.py")
ISS_FILE = os.path.join(ROOT_DIR, "installer", "iron_log_setup.iss")
GITHUB_REPO = "Rusya665/iron-log"
RELEASES_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"

if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)


class ReleaseManager(tk.Tk):
    """
    GUI Application for automating Git versioning, tagging, and deployment.
    """

    def __init__(self) -> None:
        super().__init__()

        self.title("Iron Log - Release Manager")
        self.geometry("820x760")
        self.configure(bg="#121212")

        self.latest_github_version: str = "Loading..."
        self._build_ui()

        threading.Thread(target=self._fetch_latest_version, daemon=True).start()

    def _get_sorted_branches(self) -> List[str]:
        try:
            output = self._run_git(
                [
                    "git",
                    "for-each-ref",
                    "--sort=-committerdate",
                    "refs/heads/",
                    "--format=%(refname:short)",
                ]
            )
            return [b for b in output.splitlines() if b.strip()]
        except Exception:
            return ["main"]

    def _get_current_branch(self) -> str:
        try:
            return self._run_git(["git", "branch", "--show-current"]).strip()
        except Exception:
            return "main"

    def _build_ui(self) -> None:
        hdr = tk.Frame(self, bg="#1a1a1a")
        hdr.pack(fill="x")
        tk.Label(hdr, text="Release Manager", font=("Helvetica", 20, "bold"), fg="#ffffff", bg="#1a1a1a").pack(
            pady=(16, 4)
        )
        tk.Label(
            hdr,
            text="Automated versioning, tagging, and deployment",
            font=("Helvetica", 11),
            fg="#888888",
            bg="#1a1a1a",
        ).pack(pady=(0, 16))

        container = tk.Frame(self, bg="#121212")
        container.pack(fill="both", expand=True, padx=20, pady=10)

        # Branch row
        branch_frame = tk.Frame(container, bg="#1c1c1c", padx=10, pady=10)
        branch_frame.pack(fill="x", pady=6)

        tk.Label(
            branch_frame, text="Active Branch:", font=("Helvetica", 11, "bold"), fg="#ffffff", bg="#1c1c1c"
        ).pack(side="left", padx=(10, 10))

        self.branch_var = tk.StringVar(value=self._get_current_branch())
        self.branch_combo = ttk.Combobox(
            branch_frame,
            values=self._get_sorted_branches(),
            textvariable=self.branch_var,
            width=24,
            state="readonly",
        )
        self.branch_combo.bind("<<ComboboxSelected>>", lambda e: self._switch_branch(self.branch_var.get()))
        self.branch_combo.pack(side="left", padx=5)

        # Version row
        v_frame = tk.Frame(container, bg="#1c1c1c", padx=10, pady=10)
        v_frame.pack(fill="x", pady=6)

        self.v_github_label = tk.Label(
            v_frame,
            text=f"Latest on GitHub: {self.latest_github_version}",
            font=("Helvetica", 11),
            fg="#cccccc",
            bg="#1c1c1c",
        )
        self.v_github_label.pack(side="left", padx=(10, 20))

        tk.Label(v_frame, text="New Version:", font=("Helvetica", 11, "bold"), fg="#ffffff", bg="#1c1c1c").pack(
            side="left", padx=(20, 5)
        )
        self.new_v_entry = tk.Entry(
            v_frame, width=12, font=("Helvetica", 11), bg="#2a2a2a", fg="#ffffff", insertbackground="white"
        )
        self.new_v_entry.pack(side="left", padx=5)

        # Commit message
        tk.Label(
            container,
            text="Commit Message (displayed in Git history):",
            font=("Helvetica", 11, "bold"),
            fg="#ffffff",
            bg="#121212",
        ).pack(anchor="w", padx=4, pady=(12, 4))
        self.commit_msg_box = tk.Text(
            container, height=6, font=("Consolas", 10), bg="#1e1e1e", fg="#ffffff", insertbackground="white"
        )
        self.commit_msg_box.pack(fill="x", padx=4)
        self.commit_msg_box.insert("1.0", "feat: \n- \n\nfix: \n- ")

        # Release notes
        tk.Label(
            container,
            text="Release Notes (displayed on GitHub Release page):",
            font=("Helvetica", 11, "bold"),
            fg="#ffffff",
            bg="#121212",
        ).pack(anchor="w", padx=4, pady=(12, 2))
        tk.Label(
            container,
            text="(Leave empty to use the Commit Message instead)",
            font=("Helvetica", 9),
            fg="#666666",
            bg="#121212",
        ).pack(anchor="w", padx=4, pady=(0, 4))
        self.release_msg_box = tk.Text(
            container, height=6, font=("Consolas", 10), bg="#1e1e1e", fg="#ffffff", insertbackground="white"
        )
        self.release_msg_box.pack(fill="x", padx=4)

        # Status & Action
        self.status_label = tk.Label(
            self, text="Ready", font=("Helvetica", 10), fg="#888888", bg="#121212"
        )
        self.status_label.pack(pady=4)

        btn_frame = tk.Frame(self, bg="#111111", padx=20, pady=12)
        btn_frame.pack(fill="x", side="bottom")

        self.push_btn = tk.Button(
            btn_frame,
            text="PUSH RELEASE",
            height=2,
            font=("Helvetica", 13, "bold"),
            bg="#1B5E20",
            fg="#ffffff",
            activebackground="#2E7D32",
            activeforeground="#ffffff",
            relief="flat",
            command=self._on_push_pressed,
        )
        self.push_btn.pack(fill="x")

    def _switch_branch(self, branch_name: str) -> None:
        try:
            self._run_git(["git", "checkout", branch_name])
            self._log(f"Switched to branch: {branch_name}", "#4caf50")
            self.branch_var.set(self._get_current_branch())
        except subprocess.CalledProcessError as e:
            err_msg = e.output.strip() if e.output else str(e)
            mb.showerror(
                "Git Checkout Error",
                f"Could not switch to {branch_name}.\nEnsure working tree is clean.\n\n{err_msg}",
            )
            self.branch_var.set(self._get_current_branch())

    def _fetch_latest_version(self) -> None:
        try:
            response = requests.get(RELEASES_URL, timeout=5)
            response.raise_for_status()
            data = response.json()
            latest = data.get("tag_name", "").lstrip("v")
            if latest:
                self.latest_github_version = latest
                self.after(
                    0,
                    lambda: self.v_github_label.config(
                        text=f"Latest on GitHub: v{latest}"
                    ),
                )
        except Exception:
            self.after(
                0,
                lambda: self.v_github_label.config(
                    text="GitHub Status: Offline / Error", fg="red"
                ),
            )

    def _log(self, text: str, color: str = "#888888") -> None:
        self.after(0, lambda: self.status_label.config(text=text, fg=color))

    def _on_push_pressed(self) -> None:
        new_v = self.new_v_entry.get().strip()
        commit_msg = self.commit_msg_box.get("1.0", "end-1c").strip()
        release_msg = self.release_msg_box.get("1.0", "end-1c").strip()

        if not release_msg:
            release_msg = commit_msg

        try:
            parsed_new_v = version.parse(new_v)
        except InvalidVersion:
            mb.showerror(
                "Validation Error",
                "Invalid version format. Use standard semantic versioning (e.g. 1.2.3, 1.2.3-beta).",
            )
            return

        if self.latest_github_version != "Loading...":
            try:
                parsed_latest_v = version.parse(self.latest_github_version)
                if parsed_new_v <= parsed_latest_v:
                    mb.showerror(
                        "Validation Error",
                        f"New version (v{new_v}) must be greater than current version (v{self.latest_github_version}).",
                    )
                    return
            except InvalidVersion:
                pass

        if not commit_msg:
            mb.showerror("Validation Error", "Commit message cannot be empty.")
            return

        current_branch = self.branch_var.get()
        msg = f"Deploy Version: v{new_v}\nTarget Branch: {current_branch}\nCommit: '{commit_msg.splitlines()[0]}...'\n\nCONTINUE?"
        if not mb.askyesno("Final Confirmation", msg):
            return

        self.push_btn.config(state="disabled", text="PROCESSING...")
        threading.Thread(
            target=lambda: self._execute_sequence(
                new_v, commit_msg, release_msg, current_branch
            ),
            daemon=True,
        ).start()

    def _execute_sequence(
        self, new_v: str, commit_msg: str, release_msg: str, target_branch: str
    ) -> None:
        tag_name = f"v{new_v}"
        initial_hash = None

        try:
            try:
                initial_hash = self._run_git(["git", "rev-parse", "HEAD"]).strip()
            except RuntimeError:
                pass

            self._log("Updating version files...")
            self._update_file(
                VERSION_FILE,
                r'^__version__\s*=\s*".*"[ \t\r]*$',
                f'__version__ = "{new_v}"',
            )
            self._update_file(
                ISS_FILE,
                r'^#define MyAppVersion\s+".*"[ \t\r]*$',
                f'#define MyAppVersion "{new_v}"',
            )

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
            self.after(
                0,
                lambda: mb.showinfo(
                    "Success",
                    f"Version {new_v} has been deployed on branch {target_branch}.",
                ),
            )

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
            self.after(
                0, lambda: self.push_btn.config(state="normal", text="PUSH RELEASE")
            )

    def _handle_failure(self, initial_hash: Optional[str], error_message: str) -> None:
        if initial_hash:
            try:
                self._run_git(["git", "reset", "--hard", initial_hash])
            except Exception:
                pass
        self.after(
            0,
            lambda: mb.showerror(
                "Process Error",
                f"Deployment failed. Local state reset.\n\nDetails:\n{error_message}",
            ),
        )

    def _update_file(self, path: str, pattern: str, replacement: str) -> None:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        new_content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_content)

    def _run_git(self, cmd: List[str]) -> str:
        result = subprocess.run(
            cmd, check=True, text=True, capture_output=True, cwd=ROOT_DIR, timeout=60
        )
        return result.stdout


if __name__ == "__main__":
    app = ReleaseManager()
    app.mainloop()
