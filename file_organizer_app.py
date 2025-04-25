import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import magic  # pip install python-magic

# Extension mapping
EXTENSION_MAP = {
    'Images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.svg', '.webp'],
    'Documents': ['.pdf', '.doc', '.docx', '.txt', '.odt', '.rtf'],
    'Spreadsheets': ['.xls', '.xlsx', '.csv', '.ods'],
    'Presentations': ['.ppt', '.pptx', '.odp'],
    'Code': ['.py', '.js', '.html', '.css', '.cpp', '.c', '.java', '.ts', '.json', '.xml'],
    'Videos': ['.mp4', '.mov', '.avi', '.mkv', '.flv', '.webm'],
    'Music': ['.mp3', '.wav', '.aac', '.ogg', '.flac'],
    'Archives': ['.zip', '.rar', '.tar', '.gz', '.7z'],
    'Executables': ['.exe', '.msi', '.apk', '.bat', '.sh'],
}

# MIME to extension mapping
MIME_EXTENSION_MAP = {
    'image/jpeg': '.jpg',
    'image/png': '.png',
    'image/gif': '.gif',
    'image/bmp': '.bmp',
    'image/svg+xml': '.svg',
    'image/webp': '.webp',
    'application/pdf': '.pdf',
    'application/msword': '.doc',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
    'application/vnd.ms-excel': '.xls',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': '.xlsx',
    'text/csv': '.csv',
    'text/plain': '.txt',
    'application/vnd.ms-powerpoint': '.ppt',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation': '.pptx',
    'application/vnd.oasis.opendocument.presentation': '.odp',
    'application/vnd.oasis.opendocument.spreadsheet': '.ods',
    'application/vnd.oasis.opendocument.text': '.odt',
    'text/x-python': '.py',
    'application/javascript': '.js',
    'text/html': '.html',
    'text/css': '.css',
    'application/json': '.json',
    'application/xml': '.xml',
    'video/mp4': '.mp4',
    'video/x-msvideo': '.avi',
    'video/x-matroska': '.mkv',
    'audio/mpeg': '.mp3',
    'audio/x-wav': '.wav',
    'application/zip': '.zip',
    'application/x-rar-compressed': '.rar',
    'application/x-7z-compressed': '.7z',
    'application/gzip': '.gz',
    'application/x-msdownload': '.exe',
    'application/vnd.android.package-archive': '.apk',
    'text/x-shellscript': '.sh',
}

undo_stack = []  # Tracks actions for undo


def move_files(source, base_destination, log_output):
    global undo_stack
    undo_stack = []

    for filename in os.listdir(source):
        file_path = os.path.join(source, filename)

        if os.path.isfile(file_path):
            name, ext = os.path.splitext(filename)
            ext = ext.lower()
            moved = False

            # Handle known extensions
            for folder_name, extensions in EXTENSION_MAP.items():
                if ext in extensions:
                    dest_path = os.path.join(base_destination, folder_name, filename)
                    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                    shutil.move(file_path, dest_path)
                    log_output.insert(tk.END, f"Moved: {filename} → {folder_name}\n")
                    undo_stack.append(("move", dest_path, file_path))
                    moved = True
                    break

            # Handle unknown or no extension
            if not moved or ext == '':
                try:
                    mime = magic.from_file(file_path, mime=True)
                    new_ext = MIME_EXTENSION_MAP.get(mime, None)

                    if not new_ext:
                        mime_main = mime.split('/')[0]
                        for m_key, m_val in MIME_EXTENSION_MAP.items():
                            if m_key.startswith(mime_main):
                                new_ext = m_val
                                break

                    if new_ext:
                        new_filename = f"{name}{new_ext}"
                        new_file_path = os.path.join(source, new_filename)
                        os.rename(file_path, new_file_path)
                        undo_stack.append(("rename", new_file_path, file_path))

                        for folder_name, extensions in EXTENSION_MAP.items():
                            if new_ext in extensions:
                                dest_path = os.path.join(base_destination, folder_name, new_filename)
                                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                                shutil.move(new_file_path, dest_path)
                                log_output.insert(tk.END, f"Renamed & moved: {filename} → {new_filename} → {folder_name}\n")
                                undo_stack.append(("move", dest_path, new_file_path))
                                moved = True
                                break
                except Exception as e:
                    log_output.insert(tk.END, f"Error with {filename}: {e}\n")

            if not moved:
                log_output.insert(tk.END, f"Skipped (unknown): {filename}\n")

    messagebox.showinfo("Done", "Files organized successfully!")
    log_output.insert(tk.END, "✔️ Organization Complete!\n\n")
    log_output.see(tk.END)


def undo_last_operation(log_output):
    if not undo_stack:
        messagebox.showinfo("Undo", "Nothing to undo.")
        return

    while undo_stack:
        action, src, dest = undo_stack.pop()
        try:
            if action == "move":
                shutil.move(src, dest)
                log_output.insert(tk.END, f"Undo move: {os.path.basename(src)} → back to {dest}\n")
            elif action == "rename":
                os.rename(src, dest)
                log_output.insert(tk.END, f"Undo rename: {os.path.basename(src)} → {os.path.basename(dest)}\n")
        except Exception as e:
            log_output.insert(tk.END, f"Undo failed for {src}: {e}\n")

    log_output.insert(tk.END, "↩️ Undo complete!\n\n")
    log_output.see(tk.END)


def create_app():
    root = tk.Tk()
    root.title("Smart File Organizer")
    root.geometry("650x550")
    root.resizable(False, False)

    tk.Label(root, text="📁 Source Folder").pack(pady=(10, 0))
    src_entry = tk.Entry(root, width=60)
    src_entry.pack(pady=5)
    tk.Button(root, text="Browse", command=lambda: src_entry.delete(0, tk.END) or src_entry.insert(0, filedialog.askdirectory())).pack()

    tk.Label(root, text="📂 Destination Base Folder").pack(pady=(15, 0))
    dest_entry = tk.Entry(root, width=60)
    dest_entry.pack(pady=5)
    tk.Button(root, text="Browse", command=lambda: dest_entry.delete(0, tk.END) or dest_entry.insert(0, filedialog.askdirectory())).pack()

    log_output = scrolledtext.ScrolledText(root, width=80, height=20)
    log_output.pack(pady=15)

    def on_organize():
        src = src_entry.get()
        dest = dest_entry.get()
        log_output.delete(1.0, tk.END)

        if not os.path.isdir(src) or not os.path.isdir(dest):
            messagebox.showerror("Error", "Please select valid source and destination folders.")
            return
        move_files(src, dest, log_output)

    def on_undo():
        undo_last_operation(log_output)

    tk.Button(root, text="🚀 Organize Files", command=on_organize, bg="green", fg="white", font=("Arial", 12, "bold")).pack(pady=(0, 5))
    tk.Button(root, text="↩️ Undo", command=on_undo, bg="orange", fg="black", font=("Arial", 11)).pack()

    root.mainloop()


if __name__ == "__main__":
    create_app()
