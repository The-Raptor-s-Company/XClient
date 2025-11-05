```markdown
# XClient Installer

## 🎯 Overview
This project provides an installer application for XClient, designed to simplify the setup process for users. Written in Python with a graphical user interface (GUI) built using `tkinter`, this installer downloads the main XClient application executable and its essential assets (icons, images) from a remote server. It creates a dedicated `.XClient` directory within the user's `APPDATA` folder, organizes downloaded files, and automatically generates a desktop shortcut for easy access to the installed XClient application. The installer also offers a choice between English and French for the XClient application download.

## 🚀 Technologies Used

The XClient Installer is built using the following technologies:

*   **Python**: The core programming language for the application logic.
*   **tkinter**: Python's standard GUI toolkit, used to create the interactive user interface.
*   **requests**: A powerful and user-friendly HTTP library for making web requests to download files from remote servers.
*   **Pillow (PIL)**: Used for image manipulation, specifically for handling the application's icon loaded from a URL.
*   **winshell**: A Python library that provides convenient access to the Windows Shell, primarily used here for creating desktop shortcuts.
*   **pywin32 (win32com.client)**: Python extensions for Microsoft Windows, leveraged in conjunction with `winshell` for robust shortcut creation capabilities.
*   **os**: Python's standard library for interacting with the operating system, used for file path manipulation and directory creation.
*   **urllib.parse**: For parsing and constructing URLs safely.

## ⚙️ Prerequisites

To run this installer, you need:

*   **Python 3.x**: Download and install from [python.org](https://www.python.org/).
*   **Required Python Packages**:
    You can install them using pip:
    ```bash
    pip install requests Pillow winshell pypiwin32
    ```
    *Note*: `winshell` and `pypiwin32` are specific to Windows operating systems, making this installer primarily a Windows application.

## 💻 Installation (of the Installer)

1.  **Save the Script**: Save the provided Python code as a `.py` file (e.g., `xclient_installer.py`).
2.  **Install Dependencies**: Open a command prompt or terminal and navigate to the directory where you saved the file. Then, run the following command to install the necessary libraries:
    ```bash
    pip install requests Pillow winshell pypiwin32
    ```

## 🚀 Usage

1.  **Run the Installer**: Execute the Python script from your terminal:
    ```bash
    python xclient_installer.py
    ```
2.  **Select Language**: Choose your preferred language (English or Français) for the XClient application using the "Select Language" dropdown.
3.  **Choose Icon Download Option**:
    *   **None**: Do not download any additional application icons.
    *   **All**: Download all available application icons (if populated in the future).
    *   **Select**: Open a popup window to manually choose which application icons to download. (Note: In the current version, the selection list for app icons might be empty, indicating potential future expansion.)
4.  **Start Download**: Click the "Start Download" button.
5.  **Monitor Progress**: The "Downloaded Files" listbox will populate with the names of files as they are successfully downloaded.
6.  **Completion**: A success message box will appear once all files are downloaded and the desktop shortcut is created.
7.  **Launch XClient**: A new "XClient" shortcut will be available on your desktop, ready to launch the application.

## 📂 Project Structure (Code Overview)

The installer's functionality is organized into several key functions:

*   `create_xclient_folder()`: Manages the creation of the `.XClient` directory and its essential subfolders in `APPDATA`.
*   `download_file(url, save_path)`: A utility function to download a single file from a given URL to a specified path, including basic error handling.
*   `download_files(xclient_path, update_folder, language, image_choice, selected_images)`: Orchestrates the main download process, fetching core executables, icons, and selected images based on user preferences.
*   `create_shortcut(exe_path)`: Creates a desktop shortcut for the XClient executable.
*   `open_image_selection_popup(callback)`: (Currently with an empty list of images) Designed to open a `Toplevel` window for users to select specific application icons for download.
*   `on_start_download()`: The primary callback function for the "Start Download" button, integrating all installation steps.
*   `set_icon_from_url(url)`: Sets the installer's application window icon from a remote URL.
*   **GUI Initialization**: The main `tkinter` window (`root`), frames, labels, comboboxes, buttons, and the listbox are set up to provide the user interface.

## 📄 License

This project is open-source and available under the MIT License. See the LICENSE file for more details.
```