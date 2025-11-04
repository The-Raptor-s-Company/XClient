# XClient

<div align="center">

![XClient Logo](https://xclient-mit.vercel.app/assets/icon-CJlnSzrw.ico)

**A Modern Application Launcher for Windows**

[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![Tkinter](https://img.shields.io/badge/GUI-Tkinter-orange.svg)](https://docs.python.org/3/library/tkinter.html)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

</div>

---

## 🎯 Overview 

**XClient** is a modern, elegant application launcher designed for Windows. It provides a centralized hub to organize and launch all your applications, scripts, URLs, and shortcuts with style. With its sleek dark-themed interface, automatic categorization, and intuitive drag-and-drop functionality, XClient makes application management effortless.

### Why XClient?

- 🎨 **Beautiful UI**: Modern dark theme with rounded cards and smooth animations
- 🤖 **Smart Categorization**: Automatically detects and categorizes your applications
- 📁 **Organized Groups**: Custom groups and predefined categories (Games, Development, Office, etc.)
- 🔍 **Fast Search**: Quickly find any application with real-time search
- 🎯 **Drag & Drop**: Reorder applications and groups with ease
- 🌐 **Multi-Format Support**: Launch executables, scripts, URLs, and Internet shortcuts

---

## ✨ Features

### Core Features

- **Application Management**
  - Add, edit, and delete applications
  - Support for executables (.exe, .msi, .bat, .cmd, .vbs, .ps1, .reg, .dll, .appref-ms, .url)
  - Support for Internet shortcuts (.url) and direct HTTP/HTTPS URLs
  - Custom icons (local files or URLs)
  - Double-click to launch applications

- **Smart Categorization**
  - Automatic category detection based on application name and path (Games, Development, Office, Media, Browsers, Communication, Utilities)
  - Manual categorization override for individual applications
  - Customizable predefined categories with keywords, paths, and executables
  - Bulk recategorization tool to re-evaluate all applications

- **Groups Management**
  - Create, rename, and delete unlimited custom groups
  - Assign custom icons to groups for visual distinction
  - Drag-and-drop group reordering in the sidebar
  - Move applications between groups using drag-and-drop
  - Option to move or delete applications within a group when the group is removed

- **Activity Tracking & Statistics**
  - Background tracking of application usage (time spent, launch count)
  - Comprehensive activity dashboard with usage statistics (daily, weekly, monthly, all time)
  - Visual data representation using pie charts (app usage distribution) and bar charts (top used apps)
  - Category-based usage breakdown to understand time spent in different areas

- **Goals & Productivity**
  - Set usage goals: maximum time limits (e.g., "max 1h for Games") or minimum usage targets (e.g., "min 30m for Development tools")
  - Daily, weekly, or monthly goal periods
  - Real-time progress display for active goals on the main dashboard
  - Customizable notifications for approaching limits, exceeding limits, or achieving goals (Windows native notifications)
  - Management interface to add, remove, enable/disable goals

- **Search & Filter**
  - Real-time application search across all listed applications
  - Filter applications by custom groups
  - Clear search with a dedicated button

- **Modern UI**
  - Dark theme with a professional and customizable color scheme
  - Rounded cards for applications with hover effects and subtle shadows
  - Rounded input fields and buttons
  - Smooth animations and transitions for UI elements
  - Responsive grid layout for applications (4 cards per row)
  - Discrete custom scrollbars for content and sidebar
  - System tray integration for background operation and notifications
  - Tooltips for enhanced user guidance

- **Drag & Drop**
  - Reorder applications within their respective groups
  - Move applications between different groups
  - Reorder groups in the sidebar to customize layout

---

## 🚀 Installation

### Prerequisites

-   **Python 3.7 or higher**
-   **Windows OS**: XClient is designed specifically for Windows and leverages Windows-specific features for application launching and system tray integration.

### Required Python Packages

To run XClient from source, you need to install the following Python packages:

```bash
pip install Pillow pystray psutil matplotlib
```

### Installation Steps (from Source)

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/XClient.git
    cd XClient
    ```
2.  **Install the required packages:**
    ```bash
    pip install -r requirements.txt
    ```
3.  **Run the application:**
    ```bash
    python index.py
    ```

### Installation Steps (from Executable)

An `.exe` file is provided for easy installation on Windows systems.

1.  **Download the latest `XClient_Installer.exe`** from the [releases page](https://github.com/RaptorFugueu/XClient/releases).
2.  **Run the installer:** Double-click the downloaded `.exe` file.
3.  **Follow the on-screen instructions** to install XClient.
4.  Once installed, you can launch XClient from your Start Menu or desktop shortcut.

---

## 📝 Usage

1.  **Launching XClient**:
    *   If running from source, execute `python index.py`.
    *   If installed via the `.exe`, launch it from your Start Menu or desktop shortcut.
    *   XClient will start and its icon will appear in the system tray.

2.  **Adding Applications**:
    *   Click the `+ Ajouter une app` (Add an app) button.
    *   Fill in the application's name, path to its executable/URL, and optionally a custom icon.
    *   Use the `🔍 Détecter` (Detect) button to automatically suggest a category.

3.  **Organizing Applications**:
    *   **Groups**: Use the sidebar to switch between groups. You can create new groups via the `Groupes` (Groups) manager.
    *   **Drag & Drop**: Drag applications to reorder them within a group or to move them to a different group (by dragging over a group in the sidebar).

4.  **Launching Applications**:
    *   Double-click an application card to launch it.
    *   XClient will track its usage automatically.

5.  **Activity Dashboard**:
    *   Click the `Stats` button to open the activity dashboard.
    *   View detailed usage statistics, charts, and category breakdowns for different time periods.

6.  **Managing Goals**:
    *   From the `Stats` dashboard or the main window, click `📋 Objectifs` (Goals) to open the goals manager.
    *   Add new goals to set time limits or minimum usage targets for applications/categories.
    *   Monitor goal progress on the main dashboard and receive notifications.

7.  **System Tray**:
    *   XClient runs in the background. Right-click the system tray icon to access quick options like `Quitter` (Quit). Notifications will also appear from here.

---

## ⚙️ Configuration

XClient stores its data in JSON files in the application directory:

-   `applications.json`: Stores all registered applications, their paths, icons, and group assignments.
    *   You can manually edit this file, but ensure proper JSON format to avoid corruption.
-   `activity_data.json`: Contains all application usage statistics, including total time, launch counts, and session details.
-   `goals_data.json`: Stores all defined usage goals, their types, limits, and periods.

**Auto-Categorization**:
XClient automatically attempts to categorize new applications. You can enable/disable this feature and manually trigger recategorization for all apps from the `Groupes` (Groups) manager.

---

## 💾 Data Structure

### `applications.json`

This file stores an array of application objects and a dictionary of group objects.

```json
{
  "applications": [
    {
      "name": "Google Chrome",
      "exe": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
      "icon": "icon/browsers.png",
      "group_id": "browsers",
      "order": 0
    },
    {
      "name": "My Custom Script",
      "exe": "C:\\Users\\User\\Scripts\\myscript.bat",
      "icon": null,
      "group_id": "development",
      "order": 1
    }
  ],
  "groups": {
    "default": {
      "id": "default",
      "name": "Tous",
      "icon": null,
      "order": 0
    },
    "games": {
      "id": "games",
      "name": "Jeux",
      "icon": "icon/games.png",
      "order": 1,
      "auto_created": true
    },
    "development": {
      "id": "development",
      "name": "Développement",
      "icon": "icon/development.png",
      "order": 2,
      "auto_created": true
    }
  },
  "settings": {
    "auto_categorize": true,
    "hide_completed_goals": false
  }
}
```

### `activity_data.json`

This file stores a dictionary of activity data per application.

```json
{
  "Google Chrome": {
    "total_time": 123456,
    "launch_count": 50,
    "last_used": "2023-10-27T10:30:00.123456",
    "sessions": [
      {
        "start": "2023-10-27T09:00:00.000000",
        "end": "2023-10-27T09:30:00.000000",
        "duration": 1800
      }
    ]
  },
  "VS Code": {
    "total_time": 98765,
    "launch_count": 30,
    "last_used": "2023-10-26T14:45:00.987654",
    "sessions": []
  }
}
```

### `goals_data.json`

This file stores a dictionary of defined goals.

```json
{
  "Google Chrome_max_time_daily": {
    "app_name": "Google Chrome",
    "goal_type": "max_time",
    "limit_value": 3600,
    "period": "daily",
    "enabled": true,
    "created_at": "2023-10-20T08:00:00.000000"
  },
  "Development_min_time_weekly": {
    "app_name": "Développement",
    "goal_type": "min_time",
    "limit_value": 10800,
    "period": "weekly",
    "enabled": true,
    "created_at": "2023-10-25T12:00:00.000000"
  }
}
```

---

## 🐛 Troubleshooting

-   **Application not launching**:
    -   Ensure the "Chemin de l'exécutable" (Executable path) is correct and points to a valid file.
    -   Check if the application requires administrator privileges (XClient launches with normal user privileges).
    -   Verify that the executable or URL is not corrupted or blocked by your system.
-   **Icons not displaying**:
    -   Ensure the icon path (local file or URL) is correct and accessible.
    -   For local files, ensure the file exists and is readable.
    -   For URL icons, ensure you have an active internet connection and the URL is valid.
-   **Activity tracking not working**:
    -   Ensure XClient is running in the background (check the system tray).
    -   Verify that the application's executable name or path matches the tracked process.
    -   Restart XClient if you encounter issues.
-   **Data corruption (`.json` files)**:
    -   If a `.json` file becomes corrupted (e.g., due to improper shutdown or manual editing errors), XClient might fail to load data.
    -   You can try to open the `.json` file with a text editor and check for syntax errors. As a last resort, deleting the corrupted file will reset that specific data (e.g., deleting `applications.json` will reset all your added apps, `activity_data.json` will reset stats). **Always back up files before deleting.**
-   **Window appears off-screen**:
    -   If the main window or a dialog opens off-screen, you can try to:
        -   Right-click the XClient icon in the taskbar, then select "Move" and use arrow keys to bring it back.
        -   Press `Alt + Space` and then `M` (for Move), then use arrow keys.
        -   Restart the application.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
