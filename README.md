# XClient

<div align="center">

![XClient](https://xclient-mit.vercel.app/assets/icon-CJlnSzrw.ico)

**A Modern Application Launcher for Windows**

[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![Tkinter](https://img.shields.io/badge/GUI-Tkinter-orange.svg)](https://docs.python.org/3/library/tkinter.html)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

</div>

---

## 🎯 Overview

**XClient** is a modern, elegant application launcher designed for Windows. It provides a centralized hub to organize and launch all your applications, scripts, URLs, and shortcuts with style. With its sleek dark-themed interface, automatic categorization, activity tracking, and intuitive drag-and-drop functionality, XClient makes application management effortless. Beyond just launching, it helps you manage your digital habits with powerful goal-setting and a built-in JSON manager for advanced configuration.

You can use the creation tool to manage your application at this URL: https://xclient-mit.vercel.app

### Why XClient?

- 🎨 **Beautiful UI**: Modern dark theme with rounded cards and smooth animations
- 🤖 **Smart Categorization**: Automatically detects and categorizes your applications
- 📁 **Organized Groups**: Custom groups and predefined categories (Games, Development, Office, etc.)
- 🔍 **Fast Search**: Quickly find any application with real-time search
- 🎯 **Drag & Drop**: Reorder applications and groups with ease
- 🌐 **Multi-Format Support**: Launch executables, scripts, URLs, and Internet shortcuts
- 📈 **Activity Tracking**: Monitor your application usage with detailed statistics and charts
- 📊 **Productivity Goals**: Set time limits or usage targets for apps and categories
- 🔧 **JSON Manager**: Advanced tool for importing, exporting, and directly modifying configuration files
- ⌨️ **Keyboard Shortcuts**: Streamlined workflows with intuitive keyboard commands

---

## ✨ Features

### Core Features

-   **Application Management**
    -   Add, edit, and delete applications through an intuitive graphical interface.
    -   Support for a wide range of executable types: `.exe`, `.msi`, `.bat`, `.cmd`, `.vbs`, `.ps1`, `.reg`, `.dll`, `.appref-ms`.
    -   Seamless handling of Internet shortcuts (`.url`) and direct HTTP/HTTPS URLs.
    -   Automatic conversion of desktop shortcuts and certain file types into managed shortcuts for better organization.
    -   Custom icons (local files or URLs) to personalize your launcher.
    -   Double-click applications for quick launching.

-   **Smart Categorization**
    -   Automatic category detection for new applications based on their name, executable path, and predefined keywords (Games, Development, Office, Media, Browsers, Communication, Utilities).
    -   Manual categorization override for individual applications to suit your preferences.
    -   Customizable predefined categories with keywords, paths, and executables for fine-tuned organization.
    -   A bulk recategorization tool to re-evaluate and assign categories to all applications.

-   **Groups Management**
    -   Create, rename, and delete unlimited custom groups to organize your applications logically.
    -   Assign custom icons to groups for visual distinction in the sidebar.
    -   Drag-and-drop functionality for reordering groups in the sidebar, allowing you to customize your layout.
    -   Option to move or delete applications within a group when the group itself is removed.

-   **Activity Tracking & Statistics**
    -   Background tracking of application usage, including total time spent, launch counts, and detailed session data.
    -   A comprehensive activity dashboard providing usage statistics for various time periods (today, 7 days, 30 days, all time).
    -   Visual data representation using interactive pie charts (showing app usage distribution) and bar charts (highlighting top used applications).
    -   Category-based usage breakdown to help you understand where your time is spent.

-   **Goals & Productivity**
    -   Set usage goals to manage your digital habits effectively:
        -   **Maximum time limits** (e.g., "max 1 hour for Games per day").
        -   **Minimum usage targets** (e.g., "at least 30 minutes for Development tools per week").
    -   Goals can be set for daily, weekly, or monthly periods.
    -   Real-time progress display for active goals on the main dashboard.
    -   Customizable notifications for approaching limits, exceeding limits, or achieving goals, delivered via Windows native notifications and in-app pop-ups.
    -   A dedicated management interface to easily add, remove, and enable/disable your goals.

-   **Search & Filter**
    -   Real-time application search across all listed applications, making it easy to find what you need quickly.
    -   Filter applications by custom groups using the sidebar.
    -   A dedicated button to clear your search query.

-   **Modern UI**
    -   A professional and customizable dark theme color scheme.
    -   Rounded cards for applications with interactive hover effects and subtle shadows.
    -   Rounded input fields and buttons for a cohesive aesthetic.
    -   Smooth animations and transitions for UI elements enhance the user experience.
    -   A responsive grid layout for applications (4 cards per row).
    -   Discrete custom scrollbars for content areas and the sidebar.
    -   System tray integration for unobtrusive background operation and notifications.
    -   Tooltips provide enhanced user guidance and information on various UI elements.

### Advanced Features

-   **Keyboard Shortcuts**
    -   `Ctrl + G`: Open the Groups Manager.
    -   `Ctrl + A`: Add a new application.
    -   `Ctrl + O`: Open the Goals Manager.
    -   `Ctrl + S`: View the Activity Dashboard (Statistics).
    -   `Ctrl + P`: Open the Settings menu.

-   **JSON Manager**
    -   Accessible from "Settings" -> "Advanced configuration".
    -   **Import/Export**: Easily import existing configurations from JSON files or export your current setup.
    -   **Copy to Clipboard**: Copy your entire configuration to the clipboard for easy sharing or backup.
    -   **Direct Modification**: For advanced users, directly view and modify the `applications.json` and `goals_data.json` files within the app, with built-in validation to help prevent common errors.

---

## 🚀 Installation

### Prerequisites

-   **Python 3.7 or higher**
-   **Windows OS**: XClient is designed specifically for Windows and leverages Windows-specific features for application launching and system tray integration.

### Required Python Packages

To run XClient from source, you need to install the following Python packages:

```bash
pip install Pillow pystray psutil matplotlib pywin32
```

### Installation Steps (from Source)

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/The-Raptor-s-Company/XClient.git
    cd XClient
    ```
2.  **Install the required packages:**
    ```bash
    pip install -r requirements.txt
    ```
    (Ensure `requirements.txt` contains `Pillow`, `pystray`, `psutil`, `matplotlib`, and `pywin32`)
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
    *   Click the `＋ Add app` button on the top right.
    *   Fill in the application's readable name, the full path to its executable (e.g., `C:\Program Files\App\app.exe`), a URL, or an Internet shortcut.
    *   Optionally, provide a custom icon (local file path or URL).
    *   Use the `🔍 Detect` button to automatically suggest a category for the application.
    *   Click `Add application` to save.

3.  **Organizing Applications**:
    *   **Groups**: Use the sidebar on the left to switch between different groups of applications. You can create and manage new groups via the `Groups` manager (accessible through the gear icon in the sidebar or `Ctrl + G`).
    *   **Drag & Drop**:
        *   Drag applications to reorder them within a group.
        *   Drag an application over a group icon in the sidebar to move it to that group.
    *   **Context Menu**: Right-click an application card for options to modify its order, edit its details, or delete it.

4.  **Launching Applications**:
    *   Simply double-click an application card to launch it.
    *   XClient will automatically start tracking its usage in the background.

5.  **Activity Dashboard**:
    *   Click the `Stats` button on the top right, or press `Ctrl + S`, to open the activity dashboard.
    *   View detailed usage statistics, interactive charts (pie chart for usage distribution, bar chart for top apps), and category breakdowns for different time periods (Today, 7 days, 30 days, All).

6.  **Managing Goals**:
    *   From the `Stats` dashboard or the main window's settings menu, click `📋 Goals` (or press `Ctrl + O`) to open the goals manager.
    *   Add new goals to set maximum time limits or minimum usage targets for specific applications or entire categories.
    *   Monitor your goal progress directly on the main dashboard, and receive proactive notifications when you're approaching limits, exceed them, or achieve your goals.

7.  **Advanced Configuration with JSON Manager**:
    *   Go to `Settings` (gear icon in bottom-left) -> `Advanced Configuration` -> `🔧 JSON Manager`.
    *   Here you can:
        *   Import or export your entire configuration (applications, groups, goals) as a JSON file.
        *   Copy your current configuration to the clipboard.
        *   Directly view and edit `applications.json` and `goals_data.json` for fine-grained control, with safety warnings in place.

---

## ⚙️ Configuration

XClient stores its configuration and data in the following JSON files located in the application's root directory:

-   `applications.json`: This is the primary configuration file, storing all registered applications, their paths, custom icons, group assignments, and application-specific settings. It also defines your custom groups and their properties, as well as general XClient settings like `auto_categorize` and `hide_completed_goals`.
-   `activity_data.json`: Contains all application usage statistics gathered by the `ActivityTracker`. This includes total time spent, launch counts, last used timestamps, and detailed session records for each application.
-   `goals_data.json`: Stores all the usage goals you have defined, including the target application/category, goal type (`max_time` or `min_time`), limit value, period (`daily`, `weekly`, `monthly`), and status.

**Auto-Categorization**:
XClient automatically attempts to categorize new applications when they are added. This feature can be enabled or disabled in the `Groups` manager (accessible via `Ctrl + G`). From this manager, you can also manually trigger a recategorization for all your existing applications at once.

---

## 💾 Data Structure

### `applications.json`

This file stores the main application and group configurations, along with global settings.

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
      "name": "Visual Studio Code",
      "exe": "C:\\Users\\User\\AppData\\Local\\Programs\\Microsoft VS Code\\Code.exe",
      "icon": null,
      "group_id": "development",
      "order": 1
    }
  ],
  "groups": {
    "default": {
      "id": "default",
      "name": "All",
      "icon": null,
      "order": 0
    },
    "games": {
      "id": "games",
      "name": "Games",
      "icon": "icon/games.png",
      "order": 1,
      "auto_created": true
    },
    "development": {
      "id": "development",
      "name": "Development",
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

This file stores a dictionary of activity data per application, indexed by application name.

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
        "duration": 1800.0
      },
      {
        "start": "2023-10-27T10:00:00.000000",
        "end": "2023-10-27T10:30:00.000000",
        "duration": 1800.0
      }
    ]
  },
  "Visual Studio Code": {
    "total_time": 98765,
    "launch_count": 30,
    "last_used": "2023-10-26T14:45:00.987654",
    "sessions": [
      {
        "start": "2023-10-26T14:00:00.000000",
        "end": "2023-10-26T14:45:00.000000",
        "duration": 2700.0
      }
    ]
  }
}
```

### `goals_data.json`

This file stores a dictionary of defined goals, with a unique goal ID as the key.

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
    "app_name": "Development",
    "goal_type": "min_time",
    "limit_value": 10800,
    "period": "weekly",
    "enabled": true,
    "created_at": "2023-10-25T12:00:00.000000"
  },
  "My Game_max_time_daily": {
    "app_name": "My Game",
    "goal_type": "max_time",
    "limit_value": 7200,
    "period": "daily",
    "enabled": false,
    "created_at": "2023-10-28T18:30:00.000000"
  }
}
```

---

## 🐛 Troubleshooting

-   **Application not launching**:
    -   Ensure the "Executable path" is correct and points to a valid file.
    -   Check if the application requires administrator privileges (XClient launches with normal user privileges).
    -   Verify that the executable or URL is not corrupted or blocked by your system's firewall or antivirus.
    -   For `.url` files, ensure they are correctly formatted Internet shortcuts.
-   **Icons not displaying**:
    -   Ensure the icon path (local file or URL) is correct and accessible.
    -   For local files, ensure the file exists and XClient has read permissions.
    -   For URL icons, ensure you have an active internet connection and the URL is valid and publicly accessible.
-   **Activity tracking not working**:
    -   Ensure XClient is running in the background (check the system tray).
    -   Verify that the application's executable name or path accurately matches the process being tracked.
    -   If tracking seems erratic, try restarting XClient.
-   **Data corruption (`.json` files)**:
    -   If a `.json` file becomes corrupted (e.g., due to an improper shutdown, system crash, or manual editing errors), XClient might fail to load data.
    -   You can attempt to open the `.json` file with a text editor and check for syntax errors. Online JSON validators can also help identify issues.
    -   As a last resort, deleting a corrupted file (e.g., `applications.json`, `activity_data.json`, `goals_data.json`) will reset that specific data. **Always back up your files before attempting any manual modifications or deletions.**
-   **Window appears off-screen**:
    -   If the main window or a dialog opens off-screen, try one of the following:
        -   Right-click the XClient icon in the Windows taskbar, then select "Move" and use the arrow keys to bring the window back into view.
        -   Press `Alt + Space` (which opens the window menu), then `M` (for Move), and use arrow keys.
        -   Restart the application.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.