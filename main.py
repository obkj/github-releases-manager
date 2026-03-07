import tkinter as tk
from tkinter import ttk, messagebox
import requests
import threading
from ttkbootstrap import Style

class GitHubReleaseManager(tk.Tk):
    """
    A GUI application for managing GitHub releases, featuring repository browsing
    and batch deletion of releases.
    """
    def __init__(self):
        super().__init__()
        self.title("GitHub Release Manager")
        self.geometry("900x600")
        Style(theme='litera') # Apply a modern, clean theme from ttkbootstrap

        self.token = tk.StringVar()
        self.selected_repo = tk.StringVar()
        self.repos = []
        self.releases = []

        self._create_widgets()

    def _create_widgets(self):
        """Create and layout all the GUI widgets."""
        # --- Top Frame for Token and Repo Selection ---
        top_frame = ttk.Frame(self, padding="10")
        top_frame.pack(fill=tk.X, side=tk.TOP, ipady=5)

        ttk.Label(top_frame, text="GitHub Token:").pack(side=tk.LEFT, padx=(0, 5))
        token_entry = ttk.Entry(top_frame, textvariable=self.token, width=40, show="*")
        token_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)

        load_repos_button = ttk.Button(top_frame, text="Load Repositories", command=self.load_repositories)
        load_repos_button.pack(side=tk.LEFT, padx=5)

        self.repo_selector = ttk.Combobox(top_frame, textvariable=self.selected_repo, state="readonly", width=30)
        self.repo_selector.pack(side=tk.LEFT, padx=5)
        self.repo_selector.bind("<<ComboboxSelected>>", self.load_releases)

        # --- Main Frame for Releases ---
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        release_frame = ttk.LabelFrame(main_frame, text="Releases", padding="10")
        release_frame.pack(fill=tk.BOTH, expand=True)

        cols = ("Select", "Tag Name", "Release Name", "Created At")
        self.tree = ttk.Treeview(release_frame, columns=cols, show="headings")
        
        # Define headings and column properties
        self.tree.heading("Select", text="Select")
        self.tree.column("Select", width=60, anchor=tk.CENTER, stretch=False)
        self.tree.heading("Tag Name", text="Tag Name")
        self.tree.column("Tag Name", width=150)
        self.tree.heading("Release Name", text="Release Name")
        self.tree.column("Release Name", width=250)
        self.tree.heading("Created At", text="Created At")
        self.tree.column("Created At", width=150)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(release_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Bind click event to toggle checkbox simulation
        self.tree.bind("<Button-1>", self.on_tree_click)

        # --- Bottom Frame for Actions and Status ---
        bottom_frame = ttk.Frame(self, padding="10")
        bottom_frame.pack(fill=tk.X, side=tk.BOTTOM)

        delete_button = ttk.Button(bottom_frame, text="Delete Selected Releases", command=self.delete_selected_releases, style='danger.TButton')
        delete_button.pack(side=tk.LEFT)

        self.status_label = ttk.Label(bottom_frame, text="Status: Ready")
        self.status_label.pack(side=tk.RIGHT)

    def _execute_in_thread(self, target_func, *args):
        """Executes a function in a separate thread to keep the GUI responsive."""
        thread = threading.Thread(target=target_func, args=args)
        thread.daemon = True
        thread.start()

    def update_status(self, message, is_error=False):
        """Updates the status label on the main GUI thread."""
        color = "red" if is_error else "black"
        self.status_label.config(text=f"Status: {message}", foreground=color)

    def load_repositories(self):
        """Initiates fetching all repositories for the authenticated user."""
        if not self.token.get():
            messagebox.showerror("Error", "Please enter a GitHub Personal Access Token.")
            return
        self.update_status("Loading repositories...")
        self._execute_in_thread(self._fetch_all_repos_task)

    def _fetch_all_repos_task(self):
        """The background task to fetch repositories via GitHub API."""
        self.repos = []
        headers = {"Authorization": f"token {self.token.get()}"}
        url = "https://api.github.com/user/repos"
        page = 1
        try:
            while True:
                response = requests.get(url, headers=headers, params={"per_page": 100, "page": page, "sort": "full_name"})
                response.raise_for_status()
                data = response.json()
                if not data:
                    break
                self.repos.extend([repo['full_name'] for repo in data])
                page += 1
            
            self.after(0, self._update_repo_selector)
            self.after(0, self.update_status, f"Loaded {len(self.repos)} repositories.")
        except requests.RequestException as e:
            error_message = f"Error loading repos: {e}"
            self.after(0, self.update_status, error_message, True)
            self.after(0, lambda: messagebox.showerror("API Error", f"Failed to fetch repositories.\nCheck your token and network connection.\n\n{e}"))

    def _update_repo_selector(self):
        """Updates the repository dropdown on the main GUI thread."""
        self.repo_selector['values'] = self.repos
        if self.repos:
            self.repo_selector.current(0)
            self.selected_repo.set(self.repo_selector['values'][0])
            self.load_releases() # Auto-load releases for the first repo

    def load_releases(self, event=None):
        """Initiates fetching releases for the selected repository."""
        repo_name = self.selected_repo.get()
        if not repo_name:
            return
        self.update_status(f"Loading releases for {repo_name}...")
        self._execute_in_thread(self._fetch_releases_task, repo_name)

    def _fetch_releases_task(self, repo_name):
        """The background task to fetch releases."""
        headers = {"Authorization": f"token {self.token.get()}"}
        url = f"https://api.github.com/repos/{repo_name}/releases"
        try:
            response = requests.get(url, headers=headers, params={"per_page": 100})
            response.raise_for_status()
            self.releases = response.json()
            self.after(0, self._populate_release_tree)
            self.after(0, self.update_status, f"Loaded {len(self.releases)} releases for {repo_name}.")
        except requests.RequestException as e:
            self.after(0, self.update_status, f"Error loading releases: {e}", True)

    def _populate_release_tree(self):
        """Clears and populates the treeview with release data on the main GUI thread."""
        for i in self.tree.get_children():
            self.tree.delete(i)
        
        for release in self.releases:
            # Use Unicode characters to simulate checkboxes for a clean look
            checkbox = "☐"
            self.tree.insert("", "end", iid=release['id'], values=(
                checkbox,
                release.get('tag_name', 'N/A'),
                release.get('name', 'N/A'),
                release.get('created_at', 'N/A').split('T')[0]
            ))

    def on_tree_click(self, event):
        """Handles clicks on the treeview to toggle the checkbox simulation."""
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell":
            return

        column_id = self.tree.identify_column(event.x)
        if column_id == "#1": # Check if the click was on the "Select" column
            row_id = self.tree.identify_row(event.y)
            if not row_id:
                return
            
            current_values = self.tree.item(row_id, "values")
            current_state = current_values[0]
            new_state = "☑" if current_state == "☐" else "☐"
            
            # Update only the checkbox value
            self.tree.item(row_id, values=(new_state,) + current_values[1:])

    def delete_selected_releases(self):
        """Identifies selected releases and asks for user confirmation before deletion."""
        selected_items = [item for item in self.tree.get_children() if self.tree.item(item, "values")[0] == "☑"]

        if not selected_items:
            messagebox.showinfo("Info", "No releases selected for deletion.")
            return

        release_details_to_delete = []
        for item_id in selected_items:
            values = self.tree.item(item_id, "values")
            tag_name = values[1]
            release_name = values[2]
            release_details_to_delete.append(f"{release_name} ({tag_name})")
        
        confirm = messagebox.askyesno(
            "Confirm Deletion",
            f"Are you sure you want to permanently delete these {len(selected_items)} releases?\n\n- " + "\n- ".join(release_details_to_delete)
        )

        if confirm:
            self.update_status("Deleting selected releases...")
            self._execute_in_thread(self._perform_deletion_task, selected_items)

    def _perform_deletion_task(self, release_ids):
        """The background task to delete releases via API calls."""
        headers = {"Authorization": f"token {self.token.get()}"}
        repo_name = self.selected_repo.get()
        success_count = 0
        fail_count = 0

        for release_id in release_ids:
            url = f"https://api.github.com/repos/{repo_name}/releases/{release_id}"
            try:
                response = requests.delete(url, headers=headers)
                response.raise_for_status()
                success_count += 1
            except requests.RequestException:
                fail_count += 1
        
        result_message = f"Deletion complete. Succeeded: {success_count}, Failed: {fail_count}."
        self.after(0, self.update_status, result_message)
        self.after(0, self.load_releases) # Refresh the list after deletion

if __name__ == "__main__":
    app = GitHubReleaseManager()
    app.mainloop()