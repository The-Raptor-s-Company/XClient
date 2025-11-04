import os
import requests
import tkinter as tk
from tkinter import ttk, messagebox, Toplevel, Checkbutton, IntVar
from PIL import Image, ImageTk
from io import BytesIO
import winshell
from win32com.client import Dispatch
from urllib.parse import urljoin


def create_xclient_folder():
    app_data = os.getenv('APPDATA')
    xclient_path = os.path.join(app_data, '.XClient')
    os.makedirs(xclient_path, exist_ok=True)


    update_folder = os.path.join(xclient_path, "update")
    os.makedirs(update_folder, exist_ok=True)

    return xclient_path, update_folder


def download_file(url, save_path):
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(save_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        return os.path.basename(save_path)
    except requests.exceptions.RequestException as e:
        messagebox.showerror("Error", f"Failed to download {url}:\n{e}")
        return None


def download_files(xclient_path, update_folder, language, image_choice, selected_images):
    icon_url = "https://xclient-downloads.vercel.app/media/"
    image_url = "https://xclient-downloads.vercel.app/media/images/"
    install_url = f"https://xclient-downloads.vercel.app/{language}/XClient.exe"
    install_update_url = f"https://xclient-downloads.vercel.app/{language}/XClient_installation.exe"

    icon_folder = os.path.join(xclient_path, 'icon')
    images_folder = os.path.join(xclient_path, 'images')
    os.makedirs(icon_folder, exist_ok=True)
    os.makedirs(images_folder, exist_ok=True)

    icon_files = [
        'icon.ico', 'browsers.png', 'communication.png', 'delete.png',
        'development.png', 'eye.png', 'eye-off.png', 'games.png',
        'media.png', 'modif.png', 'office.png', 'settings.png', 'utilities.png'
    ]

    image_files = []

    downloaded_files = []


    for icon in icon_files:
        file_url = urljoin(icon_url, icon)
        save_path = os.path.join(icon_folder, icon)
        result = download_file(file_url, save_path)
        if result:
            downloaded_files.append(f"Icon: {result}")


    if image_choice != "none":
        if image_choice == "all":
            to_download = image_files
        else:
            to_download = selected_images

        for image in to_download:
            file_url = urljoin(image_url, image)
            save_path = os.path.join(images_folder, image)
            result = download_file(file_url, save_path)
            if result:
                downloaded_files.append(f"Image: {result}")


    installer_path = os.path.join(xclient_path, "XClient.exe")
    result = download_file(install_url, installer_path)
    if result:
        downloaded_files.append("XClient.exe")


    update_installer_path = os.path.join(update_folder, "XClient_installation.exe")
    result = download_file(install_update_url, update_installer_path)
    if result:
        downloaded_files.append("update/XClient_installation.exe")

    return downloaded_files, installer_path


def create_shortcut(exe_path):
    desktop = winshell.desktop()
    shortcut_path = os.path.join(desktop, "XClient.lnk")
    shell = Dispatch('WScript.Shell')
    shortcut = shell.CreateShortCut(shortcut_path)
    shortcut.TargetPath = exe_path
    shortcut.WorkingDirectory = os.path.dirname(exe_path)
    shortcut.save()


def open_image_selection_popup(callback):
    popup = Toplevel(root)
    popup.title("Select Images to Download")
    popup.geometry("300x350")

    ttk.Label(popup, text="Select the images you want to download:").pack(pady=10)

    image_files = [
        'chrome.png', 'discord.png', 'spotify.png', 'vlc.png',
        'vscode.png', 'steam.png', 'notepad.png', 'minecraft.png'
    ]

    vars_dict = {}
    for img in image_files:
        var = IntVar()
        Checkbutton(popup, text=img, variable=var).pack(anchor="w", padx=20)
        vars_dict[img] = var

    def confirm_selection():
        selected = [img for img, var in vars_dict.items() if var.get() == 1]
        popup.destroy()
        callback(selected)

    ttk.Button(popup, text="Confirm", command=confirm_selection).pack(pady=15)


def on_start_download():
    language = "en" if language_var.get() == "English" else "fr"
    image_choice = image_choice_var.get()

    def proceed(selected_images=None):
        xclient_path, update_folder = create_xclient_folder()
        downloaded_files, installer_path = download_files(xclient_path, update_folder, language, image_choice, selected_images or [])
        if installer_path:
            create_shortcut(installer_path)
        file_list.delete(0, tk.END)
        for file in downloaded_files:
            file_list.insert(tk.END, file)
        messagebox.showinfo("Success", "Download completed successfully!")

    if image_choice == "select":
        open_image_selection_popup(proceed)
    else:
        proceed()


def set_icon_from_url(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        image_data = BytesIO(response.content)
        image = Image.open(image_data)
        photo = ImageTk.PhotoImage(image)
        root.iconphoto(True, photo)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load icon from URL:\n{e}")


root = tk.Tk()
root.title("XClient Installer")

set_icon_from_url("https://xclient-mit.vercel.app/assets/icon-CJlnSzrw.ico")

frame_options = ttk.Frame(root)
frame_options.pack(pady=10)


language_var = tk.StringVar(value="English")
ttk.Label(frame_options, text="Select Language:").grid(row=0, column=0, padx=10)
ttk.Combobox(frame_options, textvariable=language_var, values=["English", "Français"], state="readonly").grid(row=0, column=1)


image_choice_var = tk.StringVar(value="none")
ttk.Label(frame_options, text="Download Images:").grid(row=1, column=0, padx=10)
ttk.Combobox(
    frame_options,
    textvariable=image_choice_var,
    values=["none", "all", "select"],
    state="readonly"
).grid(row=1, column=1)


ttk.Button(root, text="Start Download", command=on_start_download).pack(pady=10)


ttk.Label(root, text="Downloaded Files:").pack(pady=5)
file_list = tk.Listbox(root, width=60, height=12)
file_list.pack(pady=10)

root.mainloop()
