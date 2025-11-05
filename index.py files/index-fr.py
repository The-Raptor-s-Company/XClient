import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import json
import os
import webbrowser
from PIL import Image, ImageTk, ImageDraw, ImageChops
import shutil
from pystray import Icon, MenuItem, Menu
import threading
from tkinter import simpledialog
import time
from datetime import datetime, timedelta
import psutil
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure


class ActivityTracker:
    def __init__(self, app_manager):
        self.app_manager = app_manager
        self.activity_file = "activity_data.json"
        self.activities = self.load_activities()
        self.running_apps = {}
        self.tracking_thread = None
        self.tracking_active = False
        
    def load_activities(self):
        
        if os.path.exists(self.activity_file):
            try:
                with open(self.activity_file, "r") as f:
                    data = json.load(f)

                    for app_name, app_data in data.items():
                        for session in app_data.get("sessions", []):
                            if "start" in session:
                                session["start"] = datetime.fromisoformat(session["start"])
                            if "end" in session:
                                session["end"] = datetime.fromisoformat(session["end"])
                    return data
            except Exception as e:
                print(f"Erreur de chargement des activités : {e}")
                return {}
        return {}
    
    def save_activities(self):
        
        try:

            data_to_save = {}
            for app_name, app_data in self.activities.items():
                data_to_save[app_name] = {
                    "total_time": app_data.get("total_time", 0),
                    "launch_count": app_data.get("launch_count", 0),
                    "last_used": app_data.get("last_used", ""),
                    "sessions": []
                }
                for session in app_data.get("sessions", []):
                    session_copy = session.copy()
                    if isinstance(session_copy.get("start"), datetime):
                        session_copy["start"] = session_copy["start"].isoformat()
                    if isinstance(session_copy.get("end"), datetime):
                        session_copy["end"] = session_copy["end"].isoformat()
                    data_to_save[app_name]["sessions"].append(session_copy)
            
            with open(self.activity_file, "w") as f:
                json.dump(data_to_save, f, indent=2)
        except Exception as e:
            print(f"Erreur de sauvegarde des activités : {e}")
    
    def start_tracking(self):
        
        if not self.tracking_active:
            self.tracking_active = True
            self.tracking_thread = threading.Thread(target=self._tracking_loop, daemon=True)
            self.tracking_thread.start()
    
    def stop_tracking(self):
        
        self.tracking_active = False

        for app_name in list(self.running_apps.keys()):
            self._record_session_end(app_name)
        self.save_activities()
    
    def _tracking_loop(self):
        
        while self.tracking_active:
            try:

                current_processes = []
                for proc in psutil.process_iter(['name', 'exe', 'pid']):
                    try:
                        proc_info = proc.info
                        if proc_info.get('name'):
                            current_processes.append({
                                'name': proc_info['name'].lower(),
                                'exe': proc_info.get('exe', '').lower() if proc_info.get('exe') else '',
                                'process': proc
                            })
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                

                for app in self.app_manager.applications:
                    app_name = app["name"]
                    exe_path = app["exe"].lower()
                    

                    if exe_path.endswith('.url') or exe_path.startswith(('http://', 'https://')):
                        continue
                    
                    exe_filename = os.path.basename(exe_path)
                    

                    is_running = False
                    matching_process = None
                    
                    for proc_info in current_processes:
                        proc_name = proc_info['name']
                        proc_exe = proc_info['exe']
                        

                        if exe_filename == proc_name:
                            is_running = True
                            matching_process = proc_info['process']
                            break
                        

                        if exe_filename and exe_filename in proc_name:
                            is_running = True
                            matching_process = proc_info['process']
                            break
                        

                        if proc_exe and exe_path in proc_exe:
                            is_running = True
                            matching_process = proc_info['process']
                            break
                        

                        exe_base = os.path.splitext(exe_filename)[0]
                        proc_base = os.path.splitext(proc_name)[0]
                        if exe_base and proc_base and exe_base == proc_base:
                            is_running = True
                            matching_process = proc_info['process']
                            break
                    

                    if is_running:

                        if app_name not in self.running_apps:
                            self._record_session_start(app_name, matching_process)
                            print(f"[Tracker] Démarrage détecté: {app_name}")
                    else:

                        if app_name in self.running_apps:
                            self._record_session_end(app_name)
                            print(f"[Tracker] Arrêt détecté: {app_name}")
                
                time.sleep(3)
            except Exception as e:
                print(f"Erreur dans le tracking loop : {e}")
                import traceback
                traceback.print_exc()
                time.sleep(5)
    
    def _record_session_start(self, app_name, process):
        

        if app_name in self.running_apps:
            return
            
        now = datetime.now()
        self.running_apps[app_name] = {
            "start_time": now,
            "process": process
        }
        

        if app_name not in self.activities:
            self.activities[app_name] = {
                "total_time": 0,
                "launch_count": 0,
                "last_used": "",
                "sessions": []
            }
        
        self.activities[app_name]["launch_count"] += 1
        self.activities[app_name]["last_used"] = now.isoformat()
        
        print(f"[Tracker] Session démarrée pour {app_name} à {now.strftime('%H:%M:%S')}")
    
    def _record_session_end(self, app_name):
        
        if app_name not in self.running_apps:
            return
            
        start_time = self.running_apps[app_name]["start_time"]
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        

        if duration < 5:
            del self.running_apps[app_name]
            return
        

        if app_name in self.activities:
            self.activities[app_name]["total_time"] += duration
            self.activities[app_name]["sessions"].append({
                "start": start_time,
                "end": end_time,
                "duration": duration
            })
        

        hours = int(duration // 3600)
        minutes = int((duration % 3600) // 60)
        seconds = int(duration % 60)
        
        if hours > 0:
            duration_str = f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            duration_str = f"{minutes}m {seconds}s"
        else:
            duration_str = f"{seconds}s"
        
        print(f"[Tracker] Session terminée pour {app_name}: {duration_str}")
        
        del self.running_apps[app_name]
        self.save_activities()
    
    def on_app_launch(self, app_name):
        

        if app_name not in self.activities:
            self.activities[app_name] = {
                "total_time": 0,
                "launch_count": 0,
                "last_used": "",
                "sessions": []
            }
        self.activities[app_name]["launch_count"] += 1
        self.activities[app_name]["last_used"] = datetime.now().isoformat()
        self.save_activities()
    
    def get_statistics(self, period_days=7):
        
        cutoff_date = datetime.now() - timedelta(days=period_days)
        stats = {}
        
        for app_name, app_data in self.activities.items():

            recent_sessions = [
                s for s in app_data.get("sessions", [])
                if isinstance(s.get("start"), datetime) and s["start"] >= cutoff_date
            ]
            
            period_time = sum(s.get("duration", 0) for s in recent_sessions)
            period_launches = len(recent_sessions)
            
            stats[app_name] = {
                "total_time": app_data.get("total_time", 0),
                "period_time": period_time,
                "total_launches": app_data.get("launch_count", 0),
                "period_launches": period_launches,
                "last_used": app_data.get("last_used", ""),
                "avg_session_time": period_time / period_launches if period_launches > 0 else 0
            }
        
        return stats
    
    def get_tracking_status(self):
        
        return {
            "active": self.tracking_active,
            "running_apps": list(self.running_apps.keys()),
            "total_apps_tracked": len(self.activities)
        }
    
    def remove_app_data(self, app_name):
        
        if app_name in self.activities:
            del self.activities[app_name]
            self.save_activities()
            print(f"[Tracker] Données supprimées pour: {app_name}")
            return True
        return False
    
    def print_status(self):
        
        status = self.get_tracking_status()
        print(f"\n[Tracker Status]")
        print(f"  Active: {status['active']}")
        print(f"  Applications en cours: {', '.join(status['running_apps']) if status['running_apps'] else 'Aucune'}")
        print(f"  Total d'apps suivies: {status['total_apps_tracked']}")


class GoalsManager:
    def __init__(self, activity_tracker):
        self.activity_tracker = activity_tracker
        self.goals_file = "goals_data.json"
        self.goals = self.load_goals()
        self.notifications_shown = {}
        
    def load_goals(self):
        
        if os.path.exists(self.goals_file):
            try:
                with open(self.goals_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Erreur de chargement des objectifs : {e}")
                return {}
        return {}
    
    def save_goals(self):
        
        try:
            with open(self.goals_file, "w") as f:
                json.dump(self.goals, f, indent=2)
        except Exception as e:
            print(f"Erreur de sauvegarde des objectifs : {e}")
    
    def add_goal(self, app_name, goal_type, limit_value, period="daily"):
        """
        Ajoute un nouvel objectif
        
        Args:
            app_name: Nom de l'application (ou catégorie)
            goal_type: 'max_time' (limiter le temps) ou 'min_time' (encourager l'utilisation)
            limit_value: Limite en secondes
            period: 'daily', 'weekly', 'monthly'
        """
        goal_id = f"{app_name}_{goal_type}_{period}"
        self.goals[goal_id] = {
            "app_name": app_name,
            "goal_type": goal_type,
            "limit_value": limit_value,
            "period": period,
            "enabled": True,
            "created_at": datetime.now().isoformat()
        }
        self.save_goals()
        return goal_id
    
    def remove_goal(self, goal_id):
        
        if goal_id in self.goals:
            del self.goals[goal_id]
            self.save_goals()
    
    def remove_goals_for_app(self, app_name):
        
        goals_to_remove = []
        for goal_id, goal in self.goals.items():
            if goal["app_name"] == app_name:
                goals_to_remove.append(goal_id)
        
        for goal_id in goals_to_remove:
            del self.goals[goal_id]
            print(f"[Goals] Objectif supprimé: {goal_id}")
        
        if goals_to_remove:
            self.save_goals()
        
        return len(goals_to_remove)
    
    def toggle_goal(self, goal_id):
        
        if goal_id in self.goals:
            self.goals[goal_id]["enabled"] = not self.goals[goal_id].get("enabled", True)
            self.save_goals()
    
    def check_goals(self):
        
        alerts = []
        today = datetime.now().date()
        
        for goal_id, goal in self.goals.items():
            if not goal.get("enabled", True):
                continue
            
            app_name = goal["app_name"]
            goal_type = goal["goal_type"]
            limit_value = goal["limit_value"]
            period = goal["period"]
            

            if period == "daily":
                days = 1
            elif period == "weekly":
                days = 7
            elif period == "monthly":
                days = 30
            else:
                days = 1
            

            stats = self.activity_tracker.get_statistics(period_days=days)
            
            if app_name not in stats:
                continue
            
            current_time = stats[app_name]["period_time"]
            

            alert = None
            notification_key = f"{goal_id}_{today.isoformat()}"
            
            if goal_type == "max_time":

                percentage = (current_time / limit_value) * 100
                
                if current_time >= limit_value:

                    if notification_key not in self.notifications_shown:
                        alert = {
                            "type": "limit_exceeded",
                            "goal_id": goal_id,
                            "app_name": app_name,
                            "current_time": current_time,
                            "limit_value": limit_value,
                            "percentage": percentage,
                            "message": f"⚠️ Limite dépassée pour {app_name}\n"
                                     f"Temps utilisé: {self._format_time(current_time)}\n"
                                     f"Limite: {self._format_time(limit_value)}"
                        }
                        self.notifications_shown[notification_key] = True
                        alerts.append(alert)
                elif percentage >= 80:

                    warning_key = f"{notification_key}_warning"
                    if warning_key not in self.notifications_shown:
                        alert = {
                            "type": "approaching_limit",
                            "goal_id": goal_id,
                            "app_name": app_name,
                            "current_time": current_time,
                            "limit_value": limit_value,
                            "percentage": percentage,
                            "message": f"⚡ Attention: {app_name}\n"
                                     f"Vous avez utilisé {percentage:.0f}% de votre limite quotidienne\n"
                                     f"Temps restant: {self._format_time(limit_value - current_time)}"
                        }
                        self.notifications_shown[warning_key] = True
                        alerts.append(alert)
            
            elif goal_type == "min_time":

                if current_time >= limit_value:
                    if notification_key not in self.notifications_shown:
                        alert = {
                            "type": "goal_achieved",
                            "goal_id": goal_id,
                            "app_name": app_name,
                            "current_time": current_time,
                            "limit_value": limit_value,
                            "message": f"✅ Objectif atteint pour {app_name}!\n"
                                     f"Vous avez utilisé {self._format_time(current_time)}\n"
                                     f"Objectif: {self._format_time(limit_value)}"
                        }
                        self.notifications_shown[notification_key] = True
                        alerts.append(alert)
        
        return alerts
    
    def _format_time(self, seconds):
        
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"
    
    def get_goal_progress(self, goal_id):
        
        if goal_id not in self.goals:
            return None
        
        goal = self.goals[goal_id]
        app_name = goal["app_name"]
        limit_value = goal["limit_value"]
        period = goal["period"]
        
        if period == "daily":
            days = 1
        elif period == "weekly":
            days = 7
        elif period == "monthly":
            days = 30
        else:
            days = 1
        
        stats = self.activity_tracker.get_statistics(period_days=days)
        
        if app_name not in stats:
            return {
                "current": 0,
                "limit": limit_value,
                "percentage": 0,
                "remaining": limit_value
            }
        
        current_time = stats[app_name]["period_time"]
        percentage = (current_time / limit_value) * 100 if limit_value > 0 else 0
        
        return {
            "current": current_time,
            "limit": limit_value,
            "percentage": min(percentage, 100),
            "remaining": max(0, limit_value - current_time)
        }
    
    def get_pinned_goals(self, hide_completed=False):
        """Retourne la liste des objectifs épinglés
        
        Args:
            hide_completed: Si True, masque les objectifs atteints (100% ou plus)
        """
        pinned = []
        for goal_id, goal in self.goals.items():
            if goal.get("pinned", False) and goal.get("enabled", True):
                progress = self.get_goal_progress(goal_id)
                if progress:

                    if hide_completed:


                        if progress["percentage"] >= 100:
                            continue
                    pinned.append((goal_id, goal, progress))
        return pinned    
    def reset_daily_notifications(self):
        
        today = datetime.now().date().isoformat()
        keys_to_remove = [k for k in self.notifications_shown.keys() if not k.endswith(today)]
        for key in keys_to_remove:
            del self.notifications_shown[key]
    
    def get_category_usage(self, period_days=7):
        
        stats = self.activity_tracker.get_statistics(period_days=period_days)
        category_stats = {}
        

        for app_name, app_stats in stats.items():

            category = "Autres"
            for cat_id, cat_data in APP_CATEGORIES.items():

                app_lower = app_name.lower()
                for keyword in cat_data.get("keywords", []):
                    if keyword in app_lower:
                        category = cat_data["name"]
                        break
                if category != "Autres":
                    break
            
            if category not in category_stats:
                category_stats[category] = {
                    "total_time": 0,
                    "launches": 0,
                    "apps": []
                }
            
            category_stats[category]["total_time"] += app_stats["period_time"]
            category_stats[category]["launches"] += app_stats["period_launches"]
            category_stats[category]["apps"].append({
                "name": app_name,
                "time": app_stats["period_time"]
            })
        
        return category_stats

def apply_hover_to_button(btn, base_bg="#2e3440", hover_delta=-15, active_delta=-25):

    def adjust(color, amount):
        try:
            rgb = tuple(int(color[i:i+2], 16) for i in (1, 3, 5))
            rgb = tuple(max(0, min(255, x + amount)) for x in rgb)
            return f'#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}'
        except:
            return color
    hover_bg = adjust(base_bg, hover_delta)
    active_bg = adjust(base_bg, active_delta)
    btn.configure(relief="flat", bd=0, activebackground=hover_bg, highlightthickness=0, cursor="hand2")
    btn.bind("<Enter>", lambda e: btn.configure(bg=hover_bg))
    btn.bind("<Leave>", lambda e: btn.configure(bg=base_bg))
    btn.bind("<ButtonPress-1>", lambda e: btn.configure(bg=active_bg))
    btn.bind("<ButtonRelease-1>", lambda e: btn.configure(bg=hover_bg))


class ToolTip:
    def __init__(self, widget, text, delay=500):
        self.widget = widget
        self.text = text
        self.delay = delay
        self.tipwindow = None
        self.id = None
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)

    def enter(self, event=None):
        self.schedule()

    def leave(self, event=None):
        self.unschedule()
        self.hidetip()

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(self.delay, self.showtip)

    def unschedule(self):
        if self.id:
            self.widget.after_cancel(self.id)
            self.id = None

    def showtip(self, event=None):
        if self.tipwindow or not self.text:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.configure(bg="#000000")
        frame = tk.Frame(tw, bg="#000000", bd=0, highlightthickness=0)
        frame.pack()
        label = tk.Label(frame, text=self.text, justify="left",
                         bg="#000000", fg="#ffffff",
                         relief="flat", borderwidth=0,
                         font=("Arial", 9))
        label.pack(ipadx=6, ipady=3)
        tw.wm_geometry(f"+{x}+{y}")

    def hidetip(self):
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()

def add_placeholder(entry, placeholder):

    def set_placeholder():
        entry.delete(0, tk.END)
        entry.insert(0, placeholder)
        entry._placeholder = placeholder
        entry._has_placeholder = True
        entry.configure(fg="#9aa0a6")

    def clear_placeholder():
        if getattr(entry, "_has_placeholder", False):
            entry.delete(0, tk.END)
            entry._has_placeholder = False
            entry.configure(fg="white")


    entry.set_placeholder = set_placeholder
    entry.clear_placeholder = clear_placeholder


    set_placeholder()

    def on_focus_in(e):
        clear_placeholder()

    def on_focus_out(e):
        if entry.get().strip() == "":
            set_placeholder()

    entry.bind("<FocusIn>", on_focus_in)
    entry.bind("<FocusOut>", on_focus_out)

DEFAULT_GROUP_ID = "default"


APP_CATEGORIES = {
    "games": {
        "name": "Jeux",
        "icon": "icon/games.png",
        "keywords": ["game", "gaming", "steam", "epic", "uplay", "origin", "gog", "minecraft", "fortnite", "league", "valorant", "overwatch", "wow", "battle.net"],
        "paths": ["steam", "games", "epic games", "riot games", "rockstar games"],
        "extensions": [".exe"],
        "executables": ["steam.exe", "epicgameslauncher.exe", "riotclientservices.exe"]
    },
    "development": {
        "name": "Développement",
        "icon": "icon/development.png",
        "keywords": ["visual studio", "vscode", "pycharm", "intellij", "eclipse", "netbeans", "atom", "sublime", "notepad++", "git", "github", "docker", "node", "python", "java", "compiler"],
        "paths": ["microsoft visual studio", "jetbrains", "python", "nodejs", "git"],
        "extensions": [".exe", ".bat", ".ps1"],
        "executables": ["code.exe", "devenv.exe", "pycharm64.exe", "idea64.exe"]
    },
    "office": {
        "name": "Bureautique",
        "icon": "icon/office.png",
        "keywords": ["office", "word", "excel", "powerpoint", "outlook", "onenote", "access", "publisher", "libreoffice", "openoffice", "writer", "calc", "impress"],
        "paths": ["microsoft office", "libreoffice", "openoffice"],
        "extensions": [".exe"],
        "executables": ["winword.exe", "excel.exe", "powerpnt.exe", "outlook.exe"]
    },
    "media": {
        "name": "Multimédia",
        "icon": "icon/media.png",
        "keywords": ["vlc", "media player", "spotify", "itunes", "adobe", "photoshop", "premiere", "audacity", "obs", "gimp", "inkscape", "blender"],
        "paths": ["videolan", "spotify", "adobe", "obs-studio"],
        "extensions": [".exe"],
        "executables": ["vlc.exe", "spotify.exe", "photoshop.exe", "obs64.exe"]
    },
    "browsers": {
        "name": "Navigateurs",
        "icon": "icon/browsers.png",
        "keywords": ["chrome", "firefox", "edge", "opera", "brave", "safari", "browser"],
        "paths": ["google\\chrome", "mozilla firefox", "microsoft\\edge", "opera", "brave"],
        "extensions": [".exe"],
        "executables": ["chrome.exe", "firefox.exe", "msedge.exe", "opera.exe", "brave.exe"]
    },
    "communication": {
        "name": "Communication",
        "icon": "icon/communication.png",
        "keywords": ["discord", "slack", "teams", "zoom", "skype", "telegram", "whatsapp", "signal", "messenger"],
        "paths": ["discord", "slack", "microsoft\\teams", "zoom"],
        "extensions": [".exe"],
        "executables": ["discord.exe", "slack.exe", "teams.exe", "zoom.exe"]
    },
    "utilities": {
        "name": "Utilitaires",
        "icon": "icon/utilities.png",
        "keywords": ["7-zip", "winrar", "ccleaner", "malwarebytes", "antivirus", "utility", "tool", "cleaner"],
        "paths": ["7-zip", "winrar", "ccleaner"],
        "extensions": [".exe", ".msi"],
        "executables": ["7zfm.exe", "winrar.exe", "ccleaner64.exe"]
    }
}

def ensure_data_schema(data):

    if isinstance(data, list):
        applications = data
        groups = {
            DEFAULT_GROUP_ID: {
                "id": DEFAULT_GROUP_ID,
                "name": "Tous",
                "icon": None,
                "order": 0
            }
        }

        for i, app in enumerate(applications):
            if "group_id" not in app:
                app["group_id"] = DEFAULT_GROUP_ID
            app.setdefault("order", i)
        return {"applications": applications, "groups": groups}
    elif isinstance(data, dict):

        data.setdefault("applications", [])
        data.setdefault("groups", {})
        if DEFAULT_GROUP_ID not in data["groups"]:
            data["groups"][DEFAULT_GROUP_ID] = {
                "id": DEFAULT_GROUP_ID,
                "name": "Tous",
                "icon": None,
                "order": 0
            }

        for i, app in enumerate(data["applications"]):
            app.setdefault("group_id", DEFAULT_GROUP_ID)
            app.setdefault("order", i)


        ordered_groups = sorted(data["groups"].values(), key=lambda g: (0 if g["id"] == DEFAULT_GROUP_ID else 1, g.get("name","").lower()))
        for idx, g in enumerate(ordered_groups):
            data["groups"][g["id"]].setdefault("order", idx)

        for gid, g in list(data["groups"].items()):
            if "color" in g:
                g.pop("color", None)
        return data
    else:
        return ensure_data_schema([])

def color_or_default(c, fallback="#1e2124"):
    return c if c else fallback

def sort_groups_for_sidebar(groups_dict):

    return sorted(groups_dict.values(), key=lambda g: (1 if g["id"] != DEFAULT_GROUP_ID else 0, g.get("order", 0), g.get("name","").lower()))

def sort_apps_for_group(apps_list, group_id):

    filtered = [a for a in apps_list if a.get("group_id", DEFAULT_GROUP_ID) == group_id]
    return sorted(filtered, key=lambda a: a.get("order", 0))

def color_or_default(c, fallback="#1e2124"):
    return c if c else fallback

class RoundedCard(tk.Canvas):
    def __init__(self, parent, width, height, bg="#2e3440"):
        super().__init__(parent, width=width, height=height,
                         borderwidth=0, relief="flat", highlightthickness=0,
                         bg=parent.cget('bg'))
        self.width = width
        self.height = height
        self.bg = bg
        self.hover_bg = self._adjust_color(bg, 20)
        

        self.radius = 12
        

        self.shadow = self.create_rounded_rect(2, 2, width+2, height+2, self.radius, 
                                             fill='#1a1c1e', outline='#1a1c1e', state='hidden')
        

        self.card = self.create_rounded_rect(0, 0, width, height, self.radius, 
                                           fill=bg, outline=bg)
        

        self.inner_frame = tk.Frame(self, bg=bg, highlightthickness=0)
        self.create_window(width/2, height/2, window=self.inner_frame, width=width-20, height=height-20)
        

        self.bind('<Enter>', self._on_enter)
        self.bind('<Leave>', self._on_leave)
        self.inner_frame.bind('<Enter>', self._on_enter)
        self.inner_frame.bind('<Leave>', self._on_leave)

    def _adjust_color(self, color, amount):
        try:

            rgb = tuple(int(color[i:i+2], 16) for i in (1, 3, 5))

            rgb = tuple(min(255, max(0, x + amount)) for x in rgb)

            return f'#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}'
        except:
            return color

    def _update_widget_colors(self, widget, new_bg):
        
        widget.configure(bg=new_bg)
        

        if hasattr(widget, 'bg'):
            widget.bg = new_bg
            

        for child in widget.winfo_children():
            if isinstance(child, (tk.Frame, tk.Label, tk.Button)):
                self._update_widget_colors(child, new_bg)

    def _on_enter(self, event):

        self.itemconfigure(self.shadow, state='normal')
        self.itemconfigure(self.card, fill=self.hover_bg, outline=self.hover_bg)
        

        self._update_widget_colors(self.inner_frame, self.hover_bg)
        self.configure(cursor='hand2')


        if hasattr(self, 'button_frame'):
            self.button_frame.place(relx=1.0, rely=0, anchor="ne", x=-5, y=5)

    def _on_leave(self, event):

        self.itemconfigure(self.shadow, state='hidden')
        self.itemconfigure(self.card, fill=self.bg, outline=self.bg)
        

        self._update_widget_colors(self.inner_frame, self.bg)
        self.configure(cursor='')


        if hasattr(self, 'button_frame'):
            self.button_frame.place_forget()

    def create_rounded_rect(self, x1, y1, x2, y2, radius, **kwargs):

        if 'fill' in kwargs and 'outline' not in kwargs:
            kwargs['outline'] = kwargs['fill']
        

        points = [
            x1+radius, y1,
            x2-radius, y1,
            x2, y1,
            x2, y1+radius,
            x2, y2-radius,
            x2, y2,
            x2-radius, y2,
            x1+radius, y2,
            x1, y2,
            x1, y2-radius,
            x1, y1+radius,
            x1, y1
        ]

        return self.create_polygon(points, smooth=True, **kwargs)

    def create_rounded_rect(self, x1, y1, x2, y2, radius, **kwargs):

        if 'fill' in kwargs and 'outline' not in kwargs:
            kwargs['outline'] = kwargs['fill']
            

        self.create_arc(x1, y1, x1+2*radius, y1+2*radius, start=90, extent=90, **kwargs)
        self.create_arc(x2-2*radius, y1, x2, y1+2*radius, start=0, extent=90, **kwargs)
        self.create_arc(x1, y2-2*radius, x1+2*radius, y2, start=180, extent=90, **kwargs)
        self.create_arc(x2-2*radius, y2-2*radius, x2, y2, start=270, extent=90, **kwargs)
        self.create_rectangle(x1+radius, y1, x2-radius, y2, **kwargs)
        self.create_rectangle(x1, y1+radius, x2, y2-radius, **kwargs)

class RoundedEntry(tk.Frame):
    def __init__(self, parent, width=None, placeholder="", **kwargs):
        tk.Frame.__init__(self, parent, bg="#2e3440", highlightthickness=0)
        

        self.container = tk.Canvas(self, bg=parent.cget('bg'), highlightthickness=0, 
                                   height=40, borderwidth=0, relief="flat")
        self.container.pack(fill="both", expand=True)
        

        self.bg_color = "#2e3440"
        self.focus_color = "#3a4250"
        self.radius = 8
        

        self.bg_rect = self._create_rounded_rect(2, 2, 398, 38, self.radius, fill=self.bg_color, outline=self.bg_color)
        

        self.entry = tk.Entry(self.container, bg=self.bg_color, fg="white", 
                             relief="flat", insertbackground="white",
                             font=("Arial", 10), borderwidth=0,
                             highlightthickness=0, **kwargs)
        self.entry_window = self.container.create_window(10, 20, window=self.entry, anchor="w", width=380)
        

        if placeholder:
            add_placeholder(self.entry, placeholder)
        

        self.entry.bind("<FocusIn>", self._on_focus_in)
        self.entry.bind("<FocusOut>", self._on_focus_out)
        

        self.get = self.entry.get
        self.delete = self.entry.delete
        self.insert = self.entry.insert
        self.bind = self.entry.bind
        self.configure = self.entry.configure
    
    def _create_rounded_rect(self, x1, y1, x2, y2, radius, **kwargs):
        points = [
            x1+radius, y1,
            x2-radius, y1,
            x2, y1,
            x2, y1+radius,
            x2, y2-radius,
            x2, y2,
            x2-radius, y2,
            x1+radius, y2,
            x1, y2,
            x1, y2-radius,
            x1, y1+radius,
            x1, y1
        ]
        return self.container.create_polygon(points, smooth=True, **kwargs)
    
    def _on_focus_in(self, event):
        self.container.itemconfig(self.bg_rect, fill=self.focus_color, outline=self.focus_color)
        self.entry.configure(bg=self.focus_color)
    
    def _on_focus_out(self, event):
        self.container.itemconfig(self.bg_rect, fill=self.bg_color, outline=self.bg_color)
        self.entry.configure(bg=self.bg_color)

class RoundedButton(tk.Canvas):
    def __init__(self, parent, width, height, cornerradius, bg, fg, command, text, padding=8):
        tk.Canvas.__init__(self, parent, borderwidth=0, 
                         relief="flat", highlightthickness=0)
        self.command = command
        self.bg = bg
        self.active_bg = self._adjust_color(bg, -20)
        
        total_height = height + padding * 2
        

        self.configure(width=width, height=total_height, bg=parent.cget('bg'))
        self.create_oval(0, 0, cornerradius * 2, cornerradius * 2, fill=bg, outline="")
        self.create_oval(width - cornerradius * 2, 0, width, cornerradius * 2, fill=bg, outline="")
        self.create_oval(0, total_height - cornerradius * 2, cornerradius * 2, total_height, fill=bg, outline="")
        self.create_oval(width - cornerradius * 2, total_height - cornerradius * 2, width, total_height, fill=bg, outline="")
        

        self.rect_1 = self.create_rectangle(cornerradius, 0, width - cornerradius, total_height, fill=bg, outline="")
        self.rect_2 = self.create_rectangle(0, cornerradius, width, total_height - cornerradius, fill=bg, outline="")
        

        self.text_item = self.create_text(width/2, total_height/2, text=text, fill=fg, 
                                        font=("Arial", 11, "bold"))
        

        self.bind('<Enter>', self._on_enter)
        self.bind('<Leave>', self._on_leave)
        self.bind('<Button-1>', self._on_click)

    def _adjust_color(self, color, amount):

        try:
            rgb = tuple(int(color[i:i+2], 16) for i in (1, 3, 5))
            rgb = tuple(max(0, min(255, x + amount)) for x in rgb)
            return f'#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}'
        except:
            return color

    def _on_enter(self, event):
        self.config(cursor='hand2')

        self.itemconfig(self.rect_1, fill=self.active_bg)
        self.itemconfig(self.rect_2, fill=self.active_bg)
        for i in range(4):
            self.itemconfig(i+1, fill=self.active_bg)

    def _on_leave(self, event):

        self.itemconfig(self.rect_1, fill=self.bg)
        self.itemconfig(self.rect_2, fill=self.bg)
        for i in range(4):
            self.itemconfig(i+1, fill=self.bg)
        
    def _on_click(self, event):
        if self.command is not None:
            self.command()

def center_window(window):
    window.update_idletasks()
    width = window.winfo_width()
    height = window.winfo_height()
    x = (window.winfo_screenwidth() // 2) - (width // 2)
    y = (window.winfo_screenheight() // 2) - (height // 2)
    window.geometry(f"{width}x{height}+{x}+{y}")

class XClientApp:
    def __init__(self, root):
        self.root = root
        self.root.title("XClient")
        self.root.geometry("1200x900")
        self.root.configure(bg="#1e2124")  
        self.root.resizable(False, False)
        


        project_root = os.path.dirname(os.path.abspath(__file__))
        self.links_path = os.path.join(project_root, 'link')
        os.makedirs(self.links_path, exist_ok=True)


        try:
            appdata_root = os.getenv('APPDATA')
            if appdata_root:
                appdata_link_folder = os.path.join(appdata_root, '.XClient', 'link')
                if os.path.exists(appdata_link_folder):
                    for f in os.listdir(appdata_link_folder):
                        src = os.path.join(appdata_link_folder, f)
                        dst = os.path.join(self.links_path, f)
                        if os.path.isfile(src) and not os.path.exists(dst):
                            shutil.copy2(src, dst)

                    try:
                        shutil.rmtree(appdata_link_folder)
                    except Exception:
                        pass

                old_xclient = os.path.join(appdata_root, '.XClient')
                if os.path.exists(old_xclient) and not os.listdir(old_xclient):
                    try:
                        os.rmdir(old_xclient)
                    except Exception:
                        pass
        except Exception as e:
            print(f"Erreur lors de la migration depuis AppData vers le dossier projet: {e}")
        

        self.root.bind("<Control-g>", lambda e: self.open_groups_manager())
        self.root.bind("<Control-a>", lambda e: self.add_application())
        self.root.bind("<Control-o>", lambda e: self.open_goals_manager())
        self.root.bind("<Control-s>", lambda e: self.open_activity_dashboard())
        self.root.bind("<Control-p>", lambda e: self.open_settings_menu())

        self.icon_cache = {}


        self._drag_app_index = None
        self._drag_group_id = None
        self._sidebar_group_widgets = []


        loaded = self.load_raw_data()
        data = ensure_data_schema(loaded)
        self.applications = data["applications"]
        self.groups = data["groups"]
        self.active_group_filter = DEFAULT_GROUP_ID
        self.search_query = ""
        

        self.activity_tracker = ActivityTracker(self)
        self.activity_tracker.start_tracking()
        

        self.goals_manager = GoalsManager(self.activity_tracker)
        

        self.auto_categorize = data.get("settings", {}).get("auto_categorize", True)
        

        self.hide_completed_goals = data.get("settings", {}).get("hide_completed_goals", False)
        

        self._initialize_default_categories()


        style = ttk.Style()
        try:
            style.theme_create("XClientPlus", parent="clam", settings={
                "TCombobox": {
                    "configure": {
                        "fieldbackground": "#2e3440",
                        "background": "#2e3440",
                        "foreground": "white",
                        "arrowcolor": "#ffffff",
                        "selectforeground": "white",
                        "selectbackground": "#4a90e2",
                        "borderwidth": 1,
                        "bordercolor": "#3a4250",
                        "lightcolor": "#3a4250",
                        "darkcolor": "#3a4250",
                        "relief": "flat",
                        "padding": 8
                    },
                    "map": {
                        "fieldbackground": [("readonly", "#2e3440"), ("focus", "#3a4250")],
                        "selectbackground": [("readonly", "#4a90e2")],
                        "bordercolor": [("focus", "#4a90e2")]
                    }
                },
                "TEntry": {
                    "configure": {
                        "fieldbackground": "#2e3440",
                        "foreground": "white",
                        "insertcolor": "#ffffff",
                        "borderwidth": 1,
                        "bordercolor": "#3a4250",
                        "relief": "flat",
                        "padding": 8
                    },
                    "map": {
                        "fieldbackground": [("focus", "#3a4250")],
                        "bordercolor": [("focus", "#4a90e2")]
                    }
                },
                "TSpinbox": {
                    "configure": {
                        "fieldbackground": "#2e3440",
                        "background": "#2e3440",
                        "foreground": "white",
                        "arrowcolor": "#ffffff",
                        "borderwidth": 1,
                        "bordercolor": "#3a4250",
                        "relief": "flat",
                        "padding": 6
                    },
                    "map": {
                        "fieldbackground": [("focus", "#3a4250")],
                        "bordercolor": [("focus", "#4a90e2")]
                    }
                },

                "Apps.Vertical.TScrollbar": {"configure": {
                    "background": "#2a2f38",
                    "troughcolor": "#161a1e",
                    "width": 8,
                    "arrowcolor": "#2a2f38",
                    "bordercolor": "#161a1e",
                    "lightcolor": "#161a1e",
                    "darkcolor": "#161a1e",
                    "relief": "flat"
                }},

                "Groups.Vertical.TScrollbar": {"configure": {
                    "background": "#242a32",
                    "troughcolor": "#0f1215",
                    "width": 6,
                    "arrowcolor": "#242a32",
                    "bordercolor": "#0f1215",
                    "lightcolor": "#0f1215",
                    "darkcolor": "#0f1215",
                    "relief": "flat"
                }}
            })
            style.theme_use("XClientPlus")
        except Exception:
            style.theme_use(style.theme_use())


        style.map("Apps.Vertical.TScrollbar",
            background=[
                ("!disabled", "#2a2f38"),
                ("active", "#323844"),
                ("pressed", "#394150")
            ],
            arrowcolor=[
                ("!disabled", "#2a2f38"),
                ("active", "#323844"),
                ("pressed", "#394150")
            ])
        style.map("Groups.Vertical.TScrollbar",
            background=[
                ("!disabled", "#242a32"),
                ("active", "#2b323c"),
                ("pressed", "#313a45")
            ],
            arrowcolor=[
                ("!disabled", "#242a32"),
                ("active", "#2b323c"),
                ("pressed", "#313a45")
            ])

        self.set_window_icon()


        header_frame = tk.Frame(self.root, bg="#1e2124")
        header_frame.pack(fill="x", padx=20, pady=(20, 0))
        

        left_title = tk.Frame(header_frame, bg="#1e2124")
        left_title.pack(side="left")
        x_label = tk.Label(left_title, text="X", font=("Arial", 24, "bold"), fg="#f84444", bg="#1e2124")
        x_label.pack(side="left")
        client_label = tk.Label(left_title, text="Client", font=("Arial", 24, "bold"), fg="white", bg="#1e2124")
        client_label.pack(side="left")


        right_tools = tk.Frame(header_frame, bg="#1e2124")
        right_tools.pack(side="right")


        search_frame = tk.Frame(right_tools, bg="#1e2124")
        search_frame.pack(side="right", padx=(10,0))


        self.search_container = tk.Canvas(search_frame, width=280, height=36, bg="#1e2124",
                                          highlightthickness=0, bd=0, relief="flat")
        self.search_container.pack()
        self._search_radius = 16

        self._search_bg = "#2b313b"
        self._search_bg_hover = "#303744"
        self._search_bg_focus = "#364054"
        self._search_border_inner = "#4a90e2"
        self._search_border_neutral = "#2d333d"
        self._search_shadow = "#0e1013"
        self._search_grad_top = "#2f3642"
        self._search_grad_bottom = "#2a303a"


        def _rounded_rect(c, x1, y1, x2, y2, r, color):
            c.create_arc(x1, y1, x1+2*r, y1+2*r, start=90, extent=90, fill=color, outline=color)
            c.create_arc(x2-2*r, y1, x2, y1+2*r, start=0, extent=90, fill=color, outline=color)
            c.create_arc(x1, y2-2*r, x1+2*r, y2, start=180, extent=90, fill=color, outline=color)
            c.create_arc(x2-2*r, y2-2*r, x2, y2, start=270, extent=90, fill=color, outline=color)
            c.create_rectangle(x1+r, y1, x2-r, y2, fill=color, outline=color)
            c.create_rectangle(x1, y1+r, x2, y2-r, fill=color, outline=color)


        def draw_search_bg(color, focused=False, hovered=False):
            c = self.search_container
            c.delete("all")
            r = self._search_radius
            w = int(c.cget("width"))
            h = int(c.cget("height"))


            _rounded_rect(c, 2, 2, w-2, h-2, r, self._search_shadow)


            _rounded_rect(c, 0, 0, w, h, r, self._search_grad_top)
            _rounded_rect(c, 0, h//2-2, w, h, r, self._search_grad_bottom)


            _rounded_rect(c, 0, 0, w, h, r, color)


            border_color = self._search_border_inner if focused else self._search_border_neutral
            _rounded_rect(c, 1, 1, w-1, h-1, r, border_color)
            _rounded_rect(c, 2, 2, w-2, h-2, r, color)


            try:
                self.search_entry.configure(bg=color, fg="black", insertbackground="black")
            except Exception:
                pass

        draw_search_bg(self._search_bg, focused=False)


        self.search_entry = tk.Entry(search_frame, width=24, font=("Arial", 10),
                                     bg=self._search_bg, fg="black", relief="flat",
                                     insertbackground="black", highlightthickness=0, borderwidth=0)
        entry_item = self.search_container.create_window(20, 18, window=self.search_entry, anchor="w")
        add_placeholder(self.search_entry, "Rechercher...")


        self.clear_btn = tk.Label(search_frame, text="✕", bg="#1e2124", fg="#7f8791", cursor="hand2")
        clear_item = self.search_container.create_window(264, 18, window=self.clear_btn, anchor="e")

        def update_clear_visibility():
            txt = self.search_entry.get()
            if getattr(self.search_entry, "_has_placeholder", False) or txt.strip() == "":
                self.search_container.itemconfigure(clear_item, state="hidden")
            else:
                self.search_container.itemconfigure(clear_item, state="normal")


        def _clear_hover_in(e):
            self.clear_btn.configure(fg="#c6ccd6")
        def _clear_hover_out(e):
            self.clear_btn.configure(fg="#7f8791")
        def clear_search(e=None):
            self.search_entry.delete(0, tk.END)
            if hasattr(self.search_entry, "set_placeholder"):
                self.search_entry.set_placeholder()
            self.search_query = ""
            self._on_search_changed()
            update_clear_visibility()
        self.clear_btn.bind("<Enter>", _clear_hover_in)
        self.clear_btn.bind("<Leave>", _clear_hover_out)
        self.clear_btn.bind("<Button-1>", clear_search)
        ToolTip(self.clear_btn, "Effacer")

        def on_focus_in(e):
            if getattr(self.search_entry, "_has_placeholder", False):
                self.search_entry.clear_placeholder()

        def on_focus_out(e):
            if self.search_entry.get().strip() == "":
                self.search_entry.set_placeholder()

        self.search_entry.bind("<KeyRelease>", lambda e: (self._on_search_changed(), update_clear_visibility()))
        self.search_entry.bind("<FocusIn>", on_focus_in)
        self.search_entry.bind("<FocusOut>", on_focus_out)


        update_clear_visibility()


        self.stats_button = RoundedButton(right_tools, width=140, height=30, cornerradius=8,
                                  bg="#2e3440", fg="white", text="Stats",
                                  command=self.open_activity_dashboard)
        self.stats_button.pack(side="right", pady=10, padx=(10,0))
        ToolTip(self.stats_button, "Voir les statistiques d'utilisation")
        

        self.goals_progress_frame = tk.Frame(self.root, bg="#1e2124")
        self.goals_progress_frame.pack(fill="x", padx=20, pady=(10, 0))
        

        self.root.after(5000, self._periodic_status_check)
        

        self._update_goals_progress_display()
        

        self.root.after(30000, self._periodic_progress_update)
        

        self.root.after(120000, self._periodic_goals_check)





        self.add_button = RoundedButton(right_tools, width=160, height=30, cornerradius=8,
                                  bg="#f84444", fg="white", text="＋ Ajouter une app",
                                  command=self.add_application)
        self.add_button.pack(side="right", pady=10, padx=(10,0))
        ToolTip(self.add_button, "Ajouter une application")


        sep = tk.Frame(self.root, bg="#15181b", height=1)
        sep.pack(fill="x", padx=20, pady=(10,0))

        header_frame.update()


        main_frame = tk.Frame(self.root, bg="#1e2124")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)


        self.sidebar = tk.Frame(main_frame, bg="#161a1e", width=80)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)


        content_area = tk.Frame(main_frame, bg="#1e2124")
        content_area.pack(side="left", fill="both", expand=True)

        self.canvas = tk.Canvas(content_area, bg="#1e2124", highlightthickness=0)
        app_scrollbar = ttk.Scrollbar(content_area, orient="vertical", command=self.canvas.yview, style="Apps.Vertical.TScrollbar")
        

        self.grid_frame = tk.Frame(self.canvas, bg="#1e2124")
        

        def scroll_callback(first, last):

            if float(first) < 0:
                self.canvas.yview_moveto(0)
            app_scrollbar.set(max(0, float(first)), last)

        self.canvas.configure(yscrollcommand=scroll_callback)
        

        app_scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        

        self.canvas_frame = self.canvas.create_window((0, 0), window=self.grid_frame, anchor="nw")
        

        settings_frame = tk.Frame(content_area, bg="#1e2124")
        settings_frame.pack(side="left", anchor="sw", padx=(0, 5), pady=10)

        settings_img = self.load_icon("settings.png", (24, 24))
        if settings_img:
            self.settings_button = tk.Button(settings_frame, image=settings_img, 
                                          bg="#2e3440", activebackground="#3a4250",
                                          bd=0, relief="flat", command=self.open_settings_menu)
            self.settings_button.image = settings_img
            self.settings_button.pack(side="bottom")
            apply_hover_to_button(self.settings_button, "#2e3440")
            ToolTip(self.settings_button, "Paramètres")

        self.grid_frame.bind("<Configure>", self.on_frame_configure)
        self.canvas.bind("<Configure>", self.on_canvas_configure)
        

        def _bind_app_mousewheel(e=None):
            self.canvas.bind_all("<MouseWheel>", self.on_mousewheel)
        def _unbind_app_mousewheel(e=None):
            self.canvas.unbind_all("<MouseWheel>")

        self.canvas.bind("<Enter>", _bind_app_mousewheel)
        self.canvas.bind("<Leave>", _unbind_app_mousewheel)
        self.grid_frame.bind("<Enter>", _bind_app_mousewheel)
        self.grid_frame.bind("<Leave>", _unbind_app_mousewheel)


        self._build_sidebar()
        self.update_app_grid()

        self.system_tray_icon = None
        self.create_system_tray_icon()


        self.center_window(self.root)

    def set_window_icon(self):
        try:
            img = Image.open('icon/icon.ico')
            img = img.resize((16, 16))
            img.save('icon/icon_resized.ico')

            self.root.iconbitmap('icon/icon_resized.ico')
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la définition de l'icône de la fenêtre: {e}")
    
    def open_settings_menu(self):
        settings_window = tk.Toplevel(self.root)
        settings_window.transient(self.root)
        settings_window.grab_set()
        self.setup_window(settings_window, "Paramètres")
        settings_window.geometry("400x600")
        settings_window.resizable(False, False)
        try:
            settings_window.iconbitmap('icon/icon_resized.ico')
        except:
            pass
        
        settings_window.focus_set()
        self.center_window(settings_window)

        header = tk.Label(settings_window, text="Paramètres", 
                         font=("Arial", 16, "bold"), fg="white", bg="#1e2124")
        header.pack(pady=20)


        buttons_frame = tk.Frame(settings_window, bg="#1e2124")
        buttons_frame.pack(pady=20)

        def show_shortcuts():
            shortcuts_window = tk.Toplevel(settings_window)
            shortcuts_window.transient(settings_window)
            shortcuts_window.grab_set()
            self.setup_window(shortcuts_window, "Raccourcis clavier")
            shortcuts_window.geometry("400x300")
            shortcuts_window.resizable(False, False)
            shortcuts_window.focus_set()


            tk.Label(shortcuts_window, text="Raccourcis clavier", 
                    font=("Arial", 14, "bold"), fg="white", bg="#1e2124").pack(pady=20)


            shortcuts_frame = tk.Frame(shortcuts_window, bg="#2e3440")
            shortcuts_frame.pack(fill="x", padx=20, pady=10)

            shortcuts = [
                ("Ctrl + G", "Ouvrir l'interface des groupes"),
                ("Ctrl + A", "Ajouter une application"),
                ("Ctrl + O", "Gérer les objectifs"),
                ("Ctrl + S", "Voir les statistiques"),
                ("Ctrl + P", "Ouvrir les paramètres")
            ]

            for shortcut, description in shortcuts:
                shortcut_row = tk.Frame(shortcuts_frame, bg="#2e3440")
                shortcut_row.pack(fill="x", padx=15, pady=8)
                
                tk.Label(shortcut_row, text=shortcut, 
                        font=("Arial", 10, "bold"), fg="#4a90e2", bg="#2e3440",
                        width=10, anchor="w").pack(side="left")
                
                tk.Label(shortcut_row, text=description, 
                        font=("Arial", 10), fg="white", bg="#2e3440",
                        anchor="w").pack(side="left", padx=(10, 0))


        buttons_frame = tk.Frame(settings_window, bg="#1e2124")
        buttons_frame.pack(pady=20)


        def create_menu_button(text, command):
            button = tk.Button(buttons_frame, text=text, font=("Arial", 11),
                             bg="#2e3440", fg="white", bd=0, relief="flat",
                             activebackground="#3a4250", activeforeground="white",
                             command=command)
            button.pack(fill="x", pady=5, padx=20, ipady=10)
            apply_hover_to_button(button, "#2e3440")
            return button


        create_menu_button("⌨️ Voir les raccourcis clavier", show_shortcuts)


        separator = tk.Frame(buttons_frame, height=1, bg="#3a4250")
        separator.pack(fill="x", pady=10, padx=20)


        create_menu_button("🔄 Mettre à jour XClient", 
                         lambda: os.startfile(os.path.join("update", "XClient_installation")))


        create_menu_button("🔗 Voir sur GitHub",
                         lambda: webbrowser.open("https://github.com/RaptorFugueu/XClient"))


        create_menu_button("🎮 Voir sur itch.io",
                         lambda: webbrowser.open("https://raptorfugueu.itch.io/xclient"))

        separator = tk.Frame(buttons_frame, height=1, bg="#3a4250")
        separator.pack(fill="x", pady=10, padx=20)

        create_menu_button("⚙️ Configuration avancée",
                         lambda: self.open_advanced_settings(settings_window))

    def open_advanced_settings(self, parent_window):
        advanced_window = tk.Toplevel(parent_window)
        advanced_window.transient(parent_window)
        advanced_window.grab_set()
        advanced_window.title("Configuration avancée")
        advanced_window.configure(bg="#1e2124")
        advanced_window.geometry("400x300")
        advanced_window.resizable(False, False)
        try:
            advanced_window.iconbitmap('icon/icon_resized.ico')
        except:
            pass

        advanced_window.focus_set()
        self.center_window(advanced_window)
        
        header = tk.Label(advanced_window, text="Configuration avancée",
                         font=("Arial", 14, "bold"), fg="white", bg="#1e2124")
        header.pack(pady=20)

        desc = tk.Label(advanced_window, 
                       text="Configuration avancée pour les utilisateurs expérimentés.\nUtilisez cette section avec précaution.",
                       font=("Arial", 10), fg="#8b9099", bg="#1e2124",
                       justify="center")
        desc.pack(pady=(0, 20))

        json_btn = tk.Button(advanced_window, text="🔧 Gestionnaire JSON",
                           font=("Arial", 11), bg="#2e3440", fg="white",
                           bd=0, relief="flat", activebackground="#3a4250",
                           activeforeground="white", width=25, height=2,
                           command=lambda: self.open_json_manager(advanced_window))
        json_btn.pack(pady=10)
        apply_hover_to_button(json_btn, "#2e3440")

        close_btn = tk.Button(advanced_window, text="Fermer",
                             font=("Arial", 11), bg="#4c566a", fg="white",
                             bd=0, relief="flat", activebackground="#556075",
                             activeforeground="white", width=15,
                             command=advanced_window.destroy)
        close_btn.pack(pady=20)
        apply_hover_to_button(close_btn, "#4c566a")

    def open_json_manager(self, parent_window):
        json_window = tk.Toplevel(parent_window)
        json_window.transient(parent_window)
        json_window.grab_set()
        json_window.title("Gestionnaire JSON")
        json_window.configure(bg="#1e2124")
        json_window.geometry("800x700")
        json_window.resizable(False, False)
        try:
            json_window.iconbitmap('icon/icon_resized.ico')
        except:
            pass

        json_window.focus_set()
        self.center_window(json_window)


        header_frame = tk.Frame(json_window, bg="#1e2124")
        header_frame.pack(fill="x", padx=20, pady=10)
        
        header = tk.Label(header_frame, text="Gestionnaire de configuration JSON",
                         font=("Arial", 14, "bold"), fg="white", bg="#1e2124")
        header.pack(pady=5)
        

        notebook = ttk.Notebook(json_window)
        notebook.pack(fill="both", expand=True, padx=20, pady=10)


        style = ttk.Style()
        style.configure("Custom.TNotebook", background="#1e2124", borderwidth=0)
        style.configure("Custom.TNotebook.Tab", background="#2e3440", foreground="white",
                       padding=[10, 5], font=("Arial", 10))
        style.map("Custom.TNotebook.Tab",
                 background=[("selected", "#3b4252")],
                 foreground=[("selected", "white")])
        notebook.configure(style="Custom.TNotebook")


        import_export_frame = tk.Frame(notebook, bg="#1e2124")
        import_export_frame.pack(fill="both", expand=True)
        notebook.add(import_export_frame, text="Import / Export")


        import_frame = tk.Frame(import_export_frame, bg="#1e2124", padx=20)
        import_frame.pack(fill="x", pady=10)

        import_label = tk.Label(import_frame, text="Importer une configuration",
                              font=("Arial", 12, "bold"), fg="white", bg="#1e2124")
        import_label.pack(anchor="w", pady=(0, 10))

        def import_json_file():
            try:
                file_path = filedialog.askopenfilename(
                    title="Sélectionner un fichier JSON",
                    filetypes=[("Fichiers JSON", "*.json"), ("Tous les fichiers", "*.*")]
                )
                if not file_path:
                    return
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                self._apply_json_config(config)
                messagebox.showinfo("Succès", "Configuration importée avec succès !")
                
            except json.JSONDecodeError:
                messagebox.showerror("Erreur", "Le fichier n'est pas un JSON valide.")
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de l'importation : {str(e)}")

        import_file_btn = tk.Button(import_frame, text="📂 Importer depuis un fichier",
                                  font=("Arial", 11), bg="#2e3440", fg="white",
                                  bd=0, relief="flat", activebackground="#3a4250",
                                  activeforeground="white", width=25,
                                  command=import_json_file)
        import_file_btn.pack(pady=5)
        apply_hover_to_button(import_file_btn, "#2e3440")


        text_frame = tk.Frame(json_window, bg="#1e2124", padx=20)
        text_frame.pack(fill="both", expand=True, pady=10)

        text_label = tk.Label(text_frame, text="Ou collez votre JSON ici :",
                            font=("Arial", 10), fg="white", bg="#1e2124")
        text_label.pack(anchor="w", pady=(0, 5))

        json_text = tk.Text(text_frame, height=10, width=50, bg="#2e3440", fg="white",
                          font=("Consolas", 10), bd=0)
        json_text.pack(pady=(0, 10))

        def import_json_text():
            try:
                json_str = json_text.get("1.0", "end-1c").strip()
                if not json_str:
                    messagebox.showerror("Erreur", "Veuillez entrer du texte JSON valide.")
                    return
                
                config = json.loads(json_str)
                self._apply_json_config(config)
                messagebox.showinfo("Succès", "Configuration importée avec succès !")
                
            except json.JSONDecodeError:
                messagebox.showerror("Erreur", "Le texte n'est pas un JSON valide.")
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de l'importation : {str(e)}")

        import_text_btn = tk.Button(text_frame, text="📝 Importer depuis le texte",
                                  font=("Arial", 11), bg="#2e3440", fg="white",
                                  bd=0, relief="flat", activebackground="#3a4250",
                                  activeforeground="white", width=25,
                                  command=import_json_text)
        import_text_btn.pack()
        apply_hover_to_button(import_text_btn, "#2e3440")


        export_frame = tk.Frame(json_window, bg="#1e2124", padx=20)
        export_frame.pack(fill="x", pady=20)

        export_label = tk.Label(export_frame, text="Exporter la configuration",
                              font=("Arial", 12, "bold"), fg="white", bg="#1e2124")
        export_label.pack(anchor="w", pady=(0, 10))

        def export_json_file():
            try:
                config = self._get_current_config()
                
                file_path = filedialog.asksaveasfilename(
                    title="Enregistrer la configuration",
                    defaultextension=".json",
                    filetypes=[("Fichiers JSON", "*.json"), ("Tous les fichiers", "*.*")]
                )
                if not file_path:
                    return
                    
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)
                    
                messagebox.showinfo("Succès", "Configuration exportée avec succès !")
                
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de l'exportation : {str(e)}")

        def export_json_clipboard():
            try:
                config = self._get_current_config()
                json_str = json.dumps(config, indent=2, ensure_ascii=False)
                
                self.root.clipboard_clear()
                self.root.clipboard_append(json_str)
                
                messagebox.showinfo("Succès", "Configuration copiée dans le presse-papiers !")
                
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de la copie : {str(e)}")

        export_file_btn = tk.Button(export_frame, text="💾 Exporter vers un fichier",
                                  font=("Arial", 11), bg="#2e3440", fg="white",
                                  bd=0, relief="flat", activebackground="#3a4250",
                                  activeforeground="white", width=25,
                                  command=export_json_file)
        export_file_btn.pack(pady=5)
        apply_hover_to_button(export_file_btn, "#2e3440")

        export_clip_btn = tk.Button(export_frame, text="📋 Copier dans le presse-papiers",
                                  font=("Arial", 11), bg="#2e3440", fg="white",
                                  bd=0, relief="flat", activebackground="#3a4250",
                                  activeforeground="white", width=25,
                                  command=export_json_clipboard)
        export_clip_btn.pack(pady=5)
        apply_hover_to_button(export_clip_btn, "#2e3440")


        edit_frame = tk.Frame(notebook, bg="#1e2124")
        edit_frame.pack(fill="both", expand=True)
        notebook.add(edit_frame, text="Modification Directe")


        warning_frame = tk.Frame(edit_frame, bg="#2e3440", padx=20, pady=15)
        warning_frame.pack(fill="x", padx=20, pady=(10, 20))

        warning_icon = tk.Label(warning_frame, text="⚠️", 
                              font=("Arial", 20), bg="#2e3440", fg="yellow")
        warning_icon.pack(pady=(0, 5))

        warning_text = tk.Label(warning_frame, text="ZONE DANGEREUSE",
                              font=("Arial", 12, "bold"), fg="yellow", bg="#2e3440")
        warning_text.pack()

        warning_desc = tk.Label(warning_frame, 
                              text="La modification directe des fichiers JSON peut rendre\n"
                                   "l'application instable ou inutilisable si mal configurée.\n"
                                   "Assurez-vous de faire une sauvegarde avant toute modification.",
                              font=("Arial", 10), fg="white", bg="#2e3440", justify="center")
        warning_desc.pack(pady=(5, 0))


        select_frame = tk.Frame(edit_frame, bg="#1e2124", padx=20)
        select_frame.pack(fill="x", pady=10)

        select_label = tk.Label(select_frame, text="Sélectionner le fichier à modifier :",
                              font=("Arial", 11, "bold"), fg="white", bg="#1e2124")
        select_label.pack(anchor="w", pady=(0, 10))

        def load_json_file(file_name):
            try:
                with open(file_name, 'r', encoding='utf-8') as f:
                    content = json.load(f)
                    edit_text.delete('1.0', tk.END)
                    edit_text.insert('1.0', json.dumps(content, indent=2, ensure_ascii=False))
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de la lecture du fichier : {str(e)}")

        def save_json_file(file_name):
            try:
                content = edit_text.get('1.0', tk.END).strip()

                json_content = json.loads(content)
                

                if file_name == "applications.json":
                    used_orders = set()
                    next_order = 1
                    for app in json_content:
                        if "order" in app:
                            while app["order"] in used_orders:
                                app["order"] = next_order
                                next_order += 1
                            used_orders.add(app["order"])
                        else:
                            while next_order in used_orders:
                                next_order += 1
                            app["order"] = next_order
                            used_orders.add(next_order)
                            next_order += 1
                    content = json.dumps(json_content, indent=2, ensure_ascii=False)
                
                with open(file_name, 'w', encoding='utf-8') as f:
                    f.write(content)
                messagebox.showinfo("Succès", "Fichier sauvegardé avec succès !")
                

                if file_name == "goals_data.json":
                    self.goals = json_content
                
            except json.JSONDecodeError:
                messagebox.showerror("Erreur", "Le JSON n'est pas valide.")
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de la sauvegarde : {str(e)}")

        button_frame = tk.Frame(select_frame, bg="#1e2124")
        button_frame.pack(fill="x")

        json_files = [
            ("📱 Applications", "applications.json"),
            ("🎯 Objectifs", "goals_data.json")
        ]

        for label, filename in json_files:
            btn = tk.Button(button_frame, text=label,
                          font=("Arial", 11), bg="#2e3440", fg="white",
                          bd=0, relief="flat", activebackground="#3a4250",
                          activeforeground="white", width=20,
                          command=lambda f=filename: load_json_file(f))
            btn.pack(side="left", padx=5, pady=5)
            apply_hover_to_button(btn, "#2e3440")


        edit_label = tk.Label(edit_frame, text="Contenu du fichier :",
                            font=("Arial", 11, "bold"), fg="white", bg="#1e2124")
        edit_label.pack(anchor="w", padx=20, pady=(10, 5))

        edit_text = tk.Text(edit_frame, height=15, bg="#2e3440", fg="white",
                          font=("Consolas", 11), bd=0)
        edit_text.pack(fill="both", expand=True, padx=20, pady=(0, 10))


        save_frame = tk.Frame(edit_frame, bg="#1e2124")
        save_frame.pack(fill="x", padx=20, pady=(0, 10))

        for label, filename in json_files:
            save_btn = tk.Button(save_frame, text=f"💾 Sauvegarder {label}",
                               font=("Arial", 11), bg="#2e3440", fg="white",
                               bd=0, relief="flat", activebackground="#3a4250",
                               activeforeground="white", width=25,
                               command=lambda f=filename: save_json_file(f))
            save_btn.pack(side="left", padx=5)
            apply_hover_to_button(save_btn, "#2e3440")


        close_frame = tk.Frame(json_window, bg="#1e2124")
        close_frame.pack(fill="x", pady=20)

        close_btn = tk.Button(close_frame, text="Fermer",
                            font=("Arial", 11), bg="#4c566a", fg="white",
                            bd=0, relief="flat", activebackground="#556075",
                            activeforeground="white", width=15,
                            command=json_window.destroy)
        close_btn.pack()
        apply_hover_to_button(close_btn, "#4c566a")

    def _get_current_config(self):
        config = {
            "applications": self._load_applications(),
            "goals": self.goals
        }
        

        try:
            with open(self.activity_file, 'r') as f:
                config["activity_data"] = json.load(f)
        except:
            config["activity_data"] = {}
            
        return config

    def _apply_json_config(self, config):
        data = ensure_data_schema(config)
        

        if isinstance(data, dict) and "applications" in data and "groups" in data:

            self.groups = data["groups"]
            

            apps = data["applications"]
            used_orders = set()
            next_order = 1
            
            for app in apps:
                if "order" in app:
                    while app["order"] in used_orders:
                        app["order"] = next_order
                        next_order += 1
                    used_orders.add(app["order"])
                else:
                    while next_order in used_orders:
                        next_order += 1
                    app["order"] = next_order
                    used_orders.add(next_order)
                    next_order += 1
            
            self.applications = apps
            self.save_all()
            

            self._build_sidebar()
            self.update_app_grid()
        
        if "goals" in config:
            self.goals = config["goals"]
            self._save_goals()
        
        if "activity_data" in config:
            with open(self.activity_file, "w") as f:
                json.dump(config["activity_data"], f, indent=2)
    
    def load_icon(self, icon_name, size=(20, 20)):
        
        cache_key = f"{icon_name}_{size[0]}x{size[1]}"
        
        if cache_key in self.icon_cache:
            return self.icon_cache[cache_key]
        
        try:
            icon_path = f"icon/{icon_name}"
            if os.path.exists(icon_path):
                img = Image.open(icon_path)
                if img.mode == "RGBA":

                    img = img.resize(size, Image.Resampling.LANCZOS)
                else:

                    img = img.convert("RGBA")
                    img = img.resize(size, Image.Resampling.LANCZOS)
                
                photo = ImageTk.PhotoImage(img)
                self.icon_cache[cache_key] = photo
                return photo
        except Exception as e:
            print(f"Erreur de chargement de l'icône {icon_name}: {e}")
        
        return None

    def open_activity_dashboard(self):
        
        win = tk.Toplevel(self.root)
        win.geometry("1400x900")
        self.setup_window(win, "Tableau de bord d'activité")
        

        header = tk.Frame(win, bg="#1e2124")
        header.pack(fill="x", padx=20, pady=(20, 10))
        
        tk.Label(header, text="Statistiques d'utilisation des applications", 
                font=("Arial", 16, "bold"), fg="white", bg="#1e2124").pack(side="left")
        

        header_buttons = tk.Frame(header, bg="#1e2124")
        header_buttons.pack(side="right")
        
        goals_btn = RoundedButton(header_buttons, width=140, height=30, cornerradius=6,
                                 bg="#4a90e2", fg="white", text="📋 Objectifs",
                                 command=lambda: self.open_goals_manager(win))
        goals_btn.pack(side="left", padx=5)
        ToolTip(goals_btn, "Gérer les objectifs")
        

        period_frame = tk.Frame(header, bg="#1e2124")
        period_frame.pack(side="right")
        
        tk.Label(period_frame, text="Période:", bg="#1e2124", fg="white",
                font=("Arial", 10)).pack(side="left", padx=(0, 5))
        
        period_var = tk.StringVar(value="7 jours")
        period_combo = ttk.Combobox(period_frame, textvariable=period_var, state="readonly",
                                    values=["Aujourd'hui", "7 jours", "30 jours", "Tout"], width=12)
        period_combo.pack(side="left")
        

        main_container = tk.Frame(win, bg="#1e2124")
        main_container.pack(fill="both", expand=True, padx=20, pady=10)
        

        canvas_scroll = tk.Canvas(main_container, bg="#1e2124", highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_container, orient="vertical", command=canvas_scroll.yview, 
                                 style="Apps.Vertical.TScrollbar")
        scrollbar_frame = tk.Frame(canvas_scroll, bg="#1e2124")
        
        canvas_scroll.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas_scroll.pack(side="left", fill="both", expand=True)
        
        canvas_window = canvas_scroll.create_window((0, 0), window=scrollbar_frame, anchor="nw")
        
        def on_frame_config(event):
            canvas_scroll.configure(scrollregion=canvas_scroll.bbox("all"))
        def on_canvas_config(event):
            canvas_scroll.itemconfig(canvas_window, width=event.width)
        
        scrollbar_frame.bind("<Configure>", on_frame_config)
        canvas_scroll.bind("<Configure>", on_canvas_config)
        

        def update_stats(period_str=None):
            if period_str is None:
                period_str = period_var.get()
            

            if period_str == "Aujourd'hui":
                days = 1
            elif period_str == "7 jours":
                days = 7
            elif period_str == "30 jours":
                days = 30
            else:
                days = 36500
            

            for widget in scrollbar_frame.winfo_children():
                widget.destroy()
            

            stats = self.activity_tracker.get_statistics(period_days=days)
            
            if not stats:
                tk.Label(scrollbar_frame, text="Aucune donnée d'activité disponible", 
                        fg="#9aa0a6", bg="#1e2124", font=("Arial", 12)).pack(pady=50)
                return
            

            sorted_apps = sorted(stats.items(), key=lambda x: x[1]["period_time"], reverse=True)
            

            graphs_frame = tk.Frame(scrollbar_frame, bg="#1e2124")
            graphs_frame.pack(fill="x", pady=(0, 20))
            

            left_graph = tk.Frame(graphs_frame, bg="#2e3440")
            left_graph.pack(side="left", fill="both", expand=True, padx=(0, 10))
            
            tk.Label(left_graph, text="Répartition du temps d'utilisation", 
                    bg="#2e3440", fg="white", font=("Arial", 12, "bold")).pack(pady=10)
            

            fig_pie = Figure(figsize=(6, 5), facecolor='#2e3440')
            ax_pie = fig_pie.add_subplot(111)
            

            top_apps = sorted_apps[:8]
            others_time = sum(x[1]["period_time"] for x in sorted_apps[8:])
            
            labels = [x[0] for x in top_apps]
            sizes = [x[1]["period_time"] / 3600 for x in top_apps]
            
            if others_time > 0:
                labels.append("Autres")
                sizes.append(others_time / 3600)
            
            if sum(sizes) > 0:
                colors = plt.cm.Set3(range(len(labels)))
                ax_pie.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=colors)
                ax_pie.axis('equal')
                fig_pie.patch.set_facecolor('#2e3440')
                ax_pie.set_facecolor('#2e3440')
                for text in ax_pie.texts:
                    text.set_color('white')
            
            canvas_pie = FigureCanvasTkAgg(fig_pie, left_graph)
            canvas_pie.draw()
            canvas_pie.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
            

            right_graph = tk.Frame(graphs_frame, bg="#2e3440")
            right_graph.pack(side="left", fill="both", expand=True, padx=(10, 0))
            
            tk.Label(right_graph, text="Top 10 - Temps d'utilisation (heures)", 
                    bg="#2e3440", fg="white", font=("Arial", 12, "bold")).pack(pady=10)
            
            fig_bar = Figure(figsize=(6, 5), facecolor='#2e3440')
            ax_bar = fig_bar.add_subplot(111)
            
            top_10 = sorted_apps[:10]
            app_names = [x[0][:15] + "..." if len(x[0]) > 15 else x[0] for x in top_10]
            times_hours = [x[1]["period_time"] / 3600 for x in top_10]
            
            if times_hours:
                bars = ax_bar.barh(app_names, times_hours, color='#4a90e2')
                ax_bar.set_xlabel('Heures', color='white')
                ax_bar.invert_yaxis()
                ax_bar.set_facecolor('#2e3440')
                ax_bar.tick_params(colors='white')
                ax_bar.spines['bottom'].set_color('white')
                ax_bar.spines['left'].set_color('white')
                ax_bar.spines['top'].set_visible(False)
                ax_bar.spines['right'].set_visible(False)
                fig_bar.patch.set_facecolor('#2e3440')
            
            canvas_bar = FigureCanvasTkAgg(fig_bar, right_graph)
            canvas_bar.draw()
            canvas_bar.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
            

            category_frame = tk.Frame(scrollbar_frame, bg="#2e3440")
            category_frame.pack(fill="x", pady=(20, 10))
            
            tk.Label(category_frame, text="Répartition par catégories", 
                    bg="#2e3440", fg="white", font=("Arial", 12, "bold")).pack(pady=10)
            
            category_stats = self.goals_manager.get_category_usage(period_days=days)
            
            if category_stats:

                cat_chart_frame = tk.Frame(category_frame, bg="#2e3440")
                cat_chart_frame.pack(fill="x", padx=10, pady=10)
                
                categories = sorted(category_stats.items(), key=lambda x: x[1]["total_time"], reverse=True)
                
                for i, (cat_name, cat_data) in enumerate(categories[:8]):
                    cat_row = tk.Frame(cat_chart_frame, bg="#2a2f38" if i % 2 == 0 else "#242933")
                    cat_row.pack(fill="x", pady=2)
                    

                    tk.Label(cat_row, text=cat_name, width=18, anchor="w",
                            bg=cat_row.cget("bg"), fg="white", font=("Arial", 10)).pack(side="left", padx=10, pady=8)
                    

                    total_time = sum(c[1]["total_time"] for c in categories)
                    percentage = (cat_data["total_time"] / total_time * 100) if total_time > 0 else 0
                    
                    bar_container = tk.Frame(cat_row, bg="#1a1e22", height=20, width=300)
                    bar_container.pack(side="left", padx=10)
                    bar_container.pack_propagate(False)
                    
                    bar_width = int(300 * percentage / 100)
                    bar = tk.Frame(bar_container, bg="#4a90e2", height=20, width=bar_width)
                    bar.pack(side="left")
                    

                    hours = int(cat_data["total_time"] // 3600)
                    minutes = int((cat_data["total_time"] % 3600) // 60)
                    time_str = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
                    
                    tk.Label(cat_row, text=f"{time_str} ({percentage:.1f}%)", width=15, anchor="e",
                            bg=cat_row.cget("bg"), fg="white", font=("Arial", 9)).pack(side="left", padx=10)
                    

                    tk.Label(cat_row, text=f"{len(cat_data['apps'])} apps", width=10, anchor="e",
                            bg=cat_row.cget("bg"), fg="#9aa0a6", font=("Arial", 8)).pack(side="left", padx=5)
            

            table_frame = tk.Frame(scrollbar_frame, bg="#2e3440")
            table_frame.pack(fill="x", pady=(10, 0))
            
            tk.Label(table_frame, text="Détails des applications", 
                    bg="#2e3440", fg="white", font=("Arial", 12, "bold")).pack(pady=10)
            

            headers_frame = tk.Frame(table_frame, bg="#1e2124")
            headers_frame.pack(fill="x", padx=10, pady=(0, 5))
            
            tk.Label(headers_frame, text="Application", width=25, anchor="w",
                    bg="#1e2124", fg="white", font=("Arial", 9, "bold")).pack(side="left", padx=5)
            tk.Label(headers_frame, text="Temps total", width=12, anchor="center",
                    bg="#1e2124", fg="white", font=("Arial", 9, "bold")).pack(side="left", padx=5)
            tk.Label(headers_frame, text="Lancements", width=12, anchor="center",
                    bg="#1e2124", fg="white", font=("Arial", 9, "bold")).pack(side="left", padx=5)
            tk.Label(headers_frame, text="Temps moyen", width=12, anchor="center",
                    bg="#1e2124", fg="white", font=("Arial", 9, "bold")).pack(side="left", padx=5)
            tk.Label(headers_frame, text="Dernière utilisation", width=18, anchor="center",
                    bg="#1e2124", fg="white", font=("Arial", 9, "bold")).pack(side="left", padx=5)
            

            for i, (app_name, app_stats) in enumerate(sorted_apps):
                row_bg = "#2a2f38" if i % 2 == 0 else "#242933"
                row = tk.Frame(table_frame, bg=row_bg)
                row.pack(fill="x", padx=10, pady=2)
                

                tk.Label(row, text=app_name[:25], width=25, anchor="w",
                        bg=row_bg, fg="white", font=("Arial", 9)).pack(side="left", padx=5)
                

                total_hours = int(app_stats["period_time"] // 3600)
                total_minutes = int((app_stats["period_time"] % 3600) // 60)
                time_str = f"{total_hours}h {total_minutes}m"
                tk.Label(row, text=time_str, width=12, anchor="center",
                        bg=row_bg, fg="white", font=("Arial", 9)).pack(side="left", padx=5)
                

                tk.Label(row, text=str(app_stats["period_launches"]), width=12, anchor="center",
                        bg=row_bg, fg="white", font=("Arial", 9)).pack(side="left", padx=5)
                

                avg_minutes = int(app_stats["avg_session_time"] // 60)
                avg_str = f"{avg_minutes}m"
                tk.Label(row, text=avg_str, width=12, anchor="center",
                        bg=row_bg, fg="white", font=("Arial", 9)).pack(side="left", padx=5)
                

                if app_stats["last_used"]:
                    try:
                        last_used = datetime.fromisoformat(app_stats["last_used"])
                        last_str = last_used.strftime("%d/%m/%Y %H:%M")
                    except:
                        last_str = "N/A"
                else:
                    last_str = "N/A"
                tk.Label(row, text=last_str, width=18, anchor="center",
                        bg=row_bg, fg="white", font=("Arial", 9)).pack(side="left", padx=5)
            

            scrollbar_frame.update_idletasks()
        

        period_combo.bind("<<ComboboxSelected>>", lambda e: update_stats())
        

        update_stats()
        

        def _on_mousewheel(event):
            canvas_scroll.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas_scroll.bind("<Enter>", lambda e: canvas_scroll.bind_all("<MouseWheel>", _on_mousewheel))
        canvas_scroll.bind("<Leave>", lambda e: canvas_scroll.unbind_all("<MouseWheel>"))
    
    def open_goals_manager(self, parent_window=None):
        
        win = tk.Toplevel(parent_window or self.root)
        win.geometry("1000x700")
        self.setup_window(win, "Gestion des objectifs")
        

        header = tk.Frame(win, bg="#1e2124")
        header.pack(fill="x", padx=20, pady=(20, 10))
        
        tk.Label(header, text="Gérer vos objectifs d'utilisation", 
                font=("Arial", 14, "bold"), fg="white", bg="#1e2124").pack(side="left")
        

        add_goal_btn = RoundedButton(header, width=160, height=30, cornerradius=6,
                                    bg="#4a90e2", fg="white", text="+ Nouvel objectif",
                                    command=lambda: self.open_add_goal_dialog(win))
        add_goal_btn.pack(side="right")
        

        main_container = tk.Frame(win, bg="#1e2124")
        main_container.pack(fill="both", expand=True, padx=20, pady=10)
        
        canvas = tk.Canvas(main_container, bg="#1e2124", highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_container, orient="vertical", command=canvas.yview,
                                 style="Apps.Vertical.TScrollbar")
        goals_frame = tk.Frame(canvas, bg="#1e2124")
        
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        
        canvas_window = canvas.create_window((0, 0), window=goals_frame, anchor="nw")
        
        def on_frame_config(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        def on_canvas_config(event):
            canvas.itemconfig(canvas_window, width=event.width)
        
        goals_frame.bind("<Configure>", on_frame_config)
        canvas.bind("<Configure>", on_canvas_config)
        

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))
        

        if not self.goals_manager.goals:
            tk.Label(goals_frame, text="Aucun objectif défini\nCliquez sur 'Nouvel objectif' pour commencer",
                    fg="#9aa0a6", bg="#1e2124", font=("Arial", 11), justify="center").pack(pady=50)
        else:
            for goal_id, goal in self.goals_manager.goals.items():
                goal_card = tk.Frame(goals_frame, bg="#2e3440")
                goal_card.pack(fill="x", padx=10, pady=8)
                

                header_row = tk.Frame(goal_card, bg="#2e3440")
                header_row.pack(fill="x", padx=15, pady=(15, 5))
                

                icon = "⏱️" if goal["goal_type"] == "max_time" else "🎯"
                tk.Label(header_row, text=icon, bg="#2e3440", fg="white",
                        font=("Arial", 16)).pack(side="left", padx=(0, 10))
                
                tk.Label(header_row, text=goal["app_name"], bg="#2e3440", fg="white",
                        font=("Arial", 12, "bold")).pack(side="left")
                

                actions = tk.Frame(header_row, bg="#2e3440")
                actions.pack(side="right")
                

                toggle_text = "✓ Activé" if goal.get("enabled", True) else "✗ Désactivé"
                toggle_bg = "#4caf50" if goal.get("enabled", True) else "#9aa0a6"
                toggle_btn = tk.Button(actions, text=toggle_text, bg=toggle_bg, fg="white",
                                      relief="flat", cursor="hand2",
                                      command=lambda gid=goal_id: [
                                          self.goals_manager.toggle_goal(gid),
                                          win.destroy(),
                                          self.open_goals_manager(parent_window)
                                      ])
                toggle_btn.pack(side="left", padx=5)
                apply_hover_to_button(toggle_btn, base_bg=toggle_bg)
                

                delete_btn = tk.Button(actions, text="🗑️", bg="#ff4444", fg="white",
                                      relief="flat", cursor="hand2",
                                      command=lambda gid=goal_id: [
                                          self.goals_manager.remove_goal(gid),
                                          win.destroy(),
                                          self.open_goals_manager(parent_window)
                                      ])
                delete_btn.pack(side="left", padx=5)
                apply_hover_to_button(delete_btn, base_bg="#ff4444")
                

                desc_row = tk.Frame(goal_card, bg="#2e3440")
                desc_row.pack(fill="x", padx=15, pady=5)
                
                goal_type_text = "Limite maximale" if goal["goal_type"] == "max_time" else "Objectif minimum"
                period_text = {"daily": "par jour", "weekly": "par semaine", "monthly": "par mois"}.get(goal["period"], "par jour")
                
                hours = int(goal["limit_value"] // 3600)
                minutes = int((goal["limit_value"] % 3600) // 60)
                limit_text = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
                
                tk.Label(desc_row, text=f"{goal_type_text}: {limit_text} {period_text}",
                        bg="#2e3440", fg="#9aa0a6", font=("Arial", 9)).pack(side="left")
                

                if goal.get("enabled", True):
                    progress = self.goals_manager.get_goal_progress(goal_id)
                    if progress:
                        progress_row = tk.Frame(goal_card, bg="#2e3440")
                        progress_row.pack(fill="x", padx=15, pady=(5, 15))
                        

                        bar_container = tk.Frame(progress_row, bg="#1a1e22", height=24)
                        bar_container.pack(fill="x", side="left", expand=True)
                        

                        percentage = progress["percentage"]
                        if goal["goal_type"] == "max_time":

                            if percentage >= 100:
                                bar_color = "#ff4444"
                            elif percentage >= 80:
                                bar_color = "#ff9800"
                            else:
                                bar_color = "#4caf50"
                        else:

                            bar_color = "#4caf50" if percentage >= 100 else "#4a90e2"
                        
                        bar = tk.Frame(bar_container, bg=bar_color, height=24)
                        bar.place(relwidth=min(percentage / 100, 1.0), relheight=1.0)
                        

                        current_hours = int(progress["current"] // 3600)
                        current_minutes = int((progress["current"] % 3600) // 60)
                        current_text = f"{current_hours}h {current_minutes}m" if current_hours > 0 else f"{current_minutes}m"
                        
                        label_text = f"{current_text} / {limit_text} ({percentage:.0f}%)"
                        tk.Label(bar_container, text=label_text, bg="#1a1e22", fg="white",
                                font=("Arial", 9)).place(relx=0.5, rely=0.5, anchor="center")
    
    def open_add_goal_dialog(self, parent_window):
        
        dialog = tk.Toplevel(parent_window)
        dialog.geometry("600x500")
        self.setup_window(dialog, "Nouvel objectif")
        

        tk.Label(dialog, text="Créer un nouvel objectif", bg="#1e2124", fg="white",
                font=("Arial", 14, "bold")).pack(pady=20)
        

        form = tk.Frame(dialog, bg="#1e2124")
        form.pack(fill="both", expand=True, padx=30)
        

        tk.Label(form, text="Application ou Catégorie", bg="#1e2124", fg="white",
                font=("Arial", 10, "bold")).pack(anchor="w", pady=(0, 5))
        
        app_var = tk.StringVar()

        app_names = [app["name"] for app in self.applications]
        category_names = [cat_data["name"] for cat_data in APP_CATEGORIES.values()]
        all_choices = sorted(set(app_names + category_names))
        
        app_combo = ttk.Combobox(form, textvariable=app_var, values=all_choices, state="readonly")
        app_combo.pack(fill="x", pady=(0, 15))
        

        tk.Label(form, text="Type d'objectif", bg="#1e2124", fg="white",
                font=("Arial", 10, "bold")).pack(anchor="w", pady=(0, 5))
        
        goal_type_var = tk.StringVar(value="max_time")
        
        type_frame = tk.Frame(form, bg="#1e2124")
        type_frame.pack(fill="x", pady=(0, 15))
        
        tk.Radiobutton(type_frame, text="⏱️ Limiter le temps d'utilisation", variable=goal_type_var,
                      value="max_time", bg="#1e2124", fg="white", selectcolor="#2e3440",
                      activebackground="#1e2124", activeforeground="white",
                      font=("Arial", 10)).pack(anchor="w", pady=2)
        
        tk.Radiobutton(type_frame, text="🎯 Encourager l'utilisation (minimum)", variable=goal_type_var,
                      value="min_time", bg="#1e2124", fg="white", selectcolor="#2e3440",
                      activebackground="#1e2124", activeforeground="white",
                      font=("Arial", 10)).pack(anchor="w", pady=2)
        

        tk.Label(form, text="Durée (heures et minutes)", bg="#1e2124", fg="white",
                font=("Arial", 10, "bold")).pack(anchor="w", pady=(0, 5))
        
        time_frame = tk.Frame(form, bg="#1e2124")
        time_frame.pack(fill="x", pady=(0, 15))
        
        tk.Label(time_frame, text="Heures:", bg="#1e2124", fg="white").pack(side="left", padx=(0, 5))
        hours_var = tk.StringVar(value="1")
        hours_spin = tk.Spinbox(time_frame, from_=0, to=23, textvariable=hours_var, width=5,
                               bg="#2e3440", fg="white", relief="flat", insertbackground="white")
        hours_spin.pack(side="left", padx=(0, 20))
        
        tk.Label(time_frame, text="Minutes:", bg="#1e2124", fg="white").pack(side="left", padx=(0, 5))
        minutes_var = tk.StringVar(value="0")
        minutes_spin = tk.Spinbox(time_frame, from_=0, to=59, textvariable=minutes_var, width=5,
                                 bg="#2e3440", fg="white", relief="flat", insertbackground="white")
        minutes_spin.pack(side="left")
        

        tk.Label(form, text="Période", bg="#1e2124", fg="white",
                font=("Arial", 10, "bold")).pack(anchor="w", pady=(0, 5))
        
        period_var = tk.StringVar(value="daily")
        period_combo = ttk.Combobox(form, textvariable=period_var, state="readonly",
                                   values=["daily", "weekly", "monthly"])
        period_combo.pack(fill="x", pady=(0, 20))
        

        buttons = tk.Frame(dialog, bg="#1e2124")
        buttons.pack(fill="x", padx=30, pady=20)
        
        def save_goal():
            app_name = app_var.get()
            if not app_name:
                messagebox.showwarning("Erreur", "Veuillez sélectionner une application ou catégorie")
                return
            
            try:
                hours = int(hours_var.get())
                minutes = int(minutes_var.get())
                limit_seconds = hours * 3600 + minutes * 60
                
                if limit_seconds <= 0:
                    messagebox.showwarning("Erreur", "La durée doit être supérieure à 0")
                    return
                
                goal_type = goal_type_var.get()
                period = period_var.get()
                
                self.goals_manager.add_goal(app_name, goal_type, limit_seconds, period)
                dialog.destroy()
                parent_window.destroy()
                self.open_goals_manager()
                
            except ValueError:
                messagebox.showerror("Erreur", "Valeurs de temps invalides")
        
        cancel_btn = RoundedButton(buttons, width=140, height=32, cornerradius=6,
                                  bg="#2e3440", fg="white", text="Annuler",
                                  command=dialog.destroy)
        cancel_btn.pack(side="left", padx=5)
        
        save_btn = RoundedButton(buttons, width=160, height=32, cornerradius=6,
                                bg="#4a90e2", fg="white", text="Créer l'objectif",
                                command=save_goal)
        save_btn.pack(side="right", padx=5)
    
    def open_icon_picker(self, icon_entry):
        
        picker_win = tk.Toplevel(self.root)
        picker_win.geometry("700x600")
        self.setup_window(picker_win, "Sélectionner une icône")
        

        header = tk.Frame(picker_win, bg="#1e2124")
        header.pack(fill="x", padx=20, pady=(20, 10))
        
        tk.Label(header, text="Choisissez une icône XClient", 
                font=("Arial", 14, "bold"), fg="white", bg="#1e2124").pack(side="left")
        

        search_frame = tk.Frame(header, bg="#1e2124")
        search_frame.pack(side="right")
        
        search_var = tk.StringVar()
        search_entry = tk.Entry(search_frame, textvariable=search_var, width=20,
                               bg="#2e3440", fg="white", relief="flat", insertbackground="white")
        search_entry.pack(side="left", padx=5)
        add_placeholder(search_entry, "Rechercher...")
        

        main_container = tk.Frame(picker_win, bg="#1e2124")
        main_container.pack(fill="both", expand=True, padx=20, pady=10)
        
        canvas = tk.Canvas(main_container, bg="#1e2124", highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_container, orient="vertical", command=canvas.yview,
                                 style="Apps.Vertical.TScrollbar")
        icons_frame = tk.Frame(canvas, bg="#1e2124")
        
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        
        canvas_window = canvas.create_window((0, 0), window=icons_frame, anchor="nw")
        
        def on_frame_config(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        def on_canvas_config(event):
            canvas.itemconfig(canvas_window, width=event.width)
        
        icons_frame.bind("<Configure>", on_frame_config)
        canvas.bind("<Configure>", on_canvas_config)
        

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))
        

        icon_folder = "images"
        icon_files = []
        
        if os.path.exists(icon_folder):
            for file in os.listdir(icon_folder):
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.ico', '.gif')):
                    icon_files.append(os.path.join(icon_folder, file))
        

        for cat_id, cat_data in APP_CATEGORIES.items():
            if cat_data.get("icon") and os.path.exists(cat_data["icon"]):
                if cat_data["icon"] not in icon_files:
                    icon_files.append(cat_data["icon"])
        

        print(f"[Icon Picker] {len(icon_files)} icônes trouvées dans '{icon_folder}/'")
        
        if not icon_files:
            tk.Label(icons_frame, text="Aucune icône trouvée dans le dossier icon/",
                    fg="#9aa0a6", bg="#1e2124", font=("Arial", 11)).pack(pady=50)
        else:

            selected_icon = [None]
            selected_widget = [None]
            
            def select_icon(icon_path, widget):

                if selected_widget[0]:
                    selected_widget[0].configure(bg="#2e3440", highlightthickness=0)
                

                selected_icon[0] = icon_path
                selected_widget[0] = widget
                widget.configure(bg="#4a90e2", highlightthickness=2, highlightbackground="#4a90e2")
            
            def apply_selection():
                if selected_icon[0]:
                    icon_entry.delete(0, tk.END)
                    icon_entry.insert(0, selected_icon[0])

                    if hasattr(icon_entry, '_has_placeholder'):
                        icon_entry._has_placeholder = False
                        icon_entry.configure(fg="white")
                    picker_win.destroy()
            

            def filter_icons(*args):
                query = search_var.get().lower()
                for widget in icons_frame.winfo_children():
                    widget.destroy()
                
                row = 0
                col = 0
                displayed = 0
                
                for icon_path in icon_files:
                    icon_name = os.path.basename(icon_path).lower()
                    

                    if hasattr(search_entry, '_has_placeholder') and search_entry._has_placeholder:
                        query = ""
                    
                    if query and query not in icon_name:
                        continue
                    
                    displayed += 1
                    

                    card = tk.Frame(icons_frame, bg="#2e3440", cursor="hand2")
                    card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
                    
                    try:

                        img = Image.open(icon_path)
                        img = img.resize((80, 80), Image.Resampling.LANCZOS)
                        photo = ImageTk.PhotoImage(img)
                        

                        icon_label = tk.Label(card, image=photo, bg="#2e3440")
                        icon_label.image = photo
                        icon_label.pack(pady=10)
                        

                        name = os.path.splitext(os.path.basename(icon_path))[0]
                        short_name = name if len(name) <= 12 else name[:11] + "…"
                        name_label = tk.Label(card, text=short_name, bg="#2e3440",
                                            fg="white", font=("Arial", 9))
                        name_label.pack(pady=(0, 10))
                        

                        ToolTip(card, name)
                        

                        for widget in [card, icon_label, name_label]:
                            widget.bind("<Button-1>", lambda e, p=icon_path, c=card: select_icon(p, c))
                            widget.bind("<Double-Button-1>", lambda e, p=icon_path, c=card: (select_icon(p, c), apply_selection()))
                        

                        def on_enter(e, c=card):
                            if c != selected_widget[0]:
                                c.configure(bg="#3a4250")
                                for child in c.winfo_children():
                                    if isinstance(child, tk.Label):
                                        child.configure(bg="#3a4250")
                        
                        def on_leave(e, c=card):
                            if c != selected_widget[0]:
                                c.configure(bg="#2e3440")
                                for child in c.winfo_children():
                                    if isinstance(child, tk.Label):
                                        child.configure(bg="#2e3440")
                        
                        card.bind("<Enter>", on_enter)
                        card.bind("<Leave>", on_leave)
                        
                    except Exception as e:
                        print(f"Erreur de chargement de l'icône {icon_path}: {e}")
                        continue
                    
                    col += 1
                    if col >= 5:
                        col = 0
                        row += 1
                
                if displayed == 0:
                    tk.Label(icons_frame, text="Aucune icône ne correspond à votre recherche",
                            fg="#9aa0a6", bg="#1e2124", font=("Arial", 11)).pack(pady=50)
                
                icons_frame.update_idletasks()
            

            search_var.trace('w', filter_icons)
            search_entry.bind("<KeyRelease>", filter_icons)
            

            filter_icons()
        

        buttons_frame = tk.Frame(picker_win, bg="#1e2124")
        buttons_frame.pack(fill="x", padx=20, pady=20)
        
        cancel_btn = RoundedButton(buttons_frame, width=140, height=32, cornerradius=8,
                                   bg="#2e3440", fg="white", text="Annuler",
                                   command=picker_win.destroy)
        cancel_btn.pack(side="left", padx=10)
        
        apply_btn = RoundedButton(buttons_frame, width=180, height=32, cornerradius=8,
                                 bg="#f84444", fg="white", text="Utiliser cette icône",
                                 command=apply_selection)
        apply_btn.pack(side="right", padx=10)
    
    def open_groups_manager(self):
        win = tk.Toplevel(self.root)
        win.geometry("1100x500")
        self.setup_window(win, "Gestion des groupes")


        header = tk.Frame(win, bg="#1e2124")
        header.pack(fill="x", padx=20, pady=(20, 10))
        
        tk.Label(header, text="Gestion des groupes et catégories", 
                font=("Arial", 14, "bold"), fg="white", bg="#1e2124").pack(side="left")
        

        options_frame = tk.Frame(header, bg="#1e2124")
        options_frame.pack(side="right")
        
        auto_cat_var = tk.BooleanVar(value=self.auto_categorize)
        def toggle_auto_categorize():
            self.auto_categorize = auto_cat_var.get()
            self.save_all()
        
        auto_cat_check = tk.Checkbutton(options_frame, text="Catégorisation automatique",
                                       variable=auto_cat_var, command=toggle_auto_categorize,
                                       bg="#1e2124", fg="white", selectcolor="#2e3440",
                                       activebackground="#1e2124", activeforeground="white")
        auto_cat_check.pack(side="left", padx=5)
        
        recategorize_btn = RoundedButton(options_frame, width=180, height=28, cornerradius=6,
                                        bg="#f84444", fg="white", text="Recatégoriser tout",
                                        command=self.recategorize_all_apps)
        recategorize_btn.pack(side="left", padx=5)
        ToolTip(recategorize_btn, "Recatégoriser automatiquement toutes les applications")
        
        cleanup_btn = RoundedButton(options_frame, width=180, height=28, cornerradius=6,
                                    bg="#ff9800", fg="white", text="Nettoyer stats",
                                    command=self.cleanup_orphaned_stats)
        cleanup_btn.pack(side="left", padx=5)
        ToolTip(cleanup_btn, "Supprimer les statistiques des applications supprimées")

        body = tk.Frame(win, bg="#1e2124")
        body.pack(fill="both", expand=True, padx=20, pady=20)


        list_frame = tk.Frame(body, bg="#1e2124")
        list_frame.pack(side="left", fill="y")
        tk.Label(list_frame, text="Groupes", bg="#1e2124", fg="white", font=("Arial", 11, "bold")).pack(anchor="w", pady=(0,8))
        self.groups_listbox = tk.Listbox(list_frame, width=28, height=18, bg="#2e3440", fg="white", highlightthickness=0, selectbackground="#3b4252")
        self.groups_listbox.pack(fill="y")
        self._refresh_groups_listbox()


        detail = tk.Frame(body, bg="#1e2124")
        detail.pack(side="left", fill="both", expand=True, padx=(20,0))

        tk.Label(detail, text="Nom du groupe", bg="#1e2124", fg="white", 
                font=("Arial", 10, "bold")).pack(anchor="w", pady=(0, 8))
        
        name_entry_frame = tk.Frame(detail, bg="#1e2124", height=42)
        name_entry_frame.pack(fill="x", pady=(0, 15))
        name_entry_frame.pack_propagate(False)
        
        name_entry = tk.Entry(name_entry_frame, font=("Arial", 11), 
                            bg="#2e3440", fg="white", relief="flat",
                            insertbackground="white", borderwidth=0,
                            highlightthickness=1, highlightbackground="#3a4250",
                            highlightcolor="#4a90e2")
        name_entry.pack(fill="both", expand=True, padx=2, pady=2, ipady=8)

        tk.Label(detail, text="Icône (optionnel)", bg="#1e2124", fg="white", 
                font=("Arial", 10, "bold")).pack(anchor="w", pady=(0, 8))
        
        icon_entry_frame = tk.Frame(detail, bg="#1e2124", height=42)
        icon_entry_frame.pack(fill="x", pady=(0, 10))
        icon_entry_frame.pack_propagate(False)
        
        icon_entry = tk.Entry(icon_entry_frame, font=("Arial", 11),
                            bg="#2e3440", fg="white", relief="flat",
                            insertbackground="white", borderwidth=0,
                            highlightthickness=1, highlightbackground="#3a4250",
                            highlightcolor="#4a90e2")
        icon_entry.pack(fill="both", expand=True, padx=2, pady=2, ipady=8)
        

        group_icon_buttons_frame = tk.Frame(detail, bg="#1e2124")
        group_icon_buttons_frame.pack(anchor="w", pady=(0, 10))
        
        group_browse_icon_btn = RoundedButton(group_icon_buttons_frame, width=150, height=32, cornerradius=8,
                                              bg="#2e3440", fg="white", text="📁 Parcourir",
                                              command=lambda: icon_entry.delete(0, tk.END) or icon_entry.insert(0, filedialog.askopenfilename(
                                                  filetypes=[("Images", "*.png *.jpg *.jpeg *.gif *.ico")])))
        group_browse_icon_btn.pack(side="left", padx=(0, 10))
        ToolTip(group_browse_icon_btn, "Sélectionner un fichier image local")
        
        group_xclient_icon_btn = RoundedButton(group_icon_buttons_frame, width=180, height=32, cornerradius=8,
                                               bg="#4a90e2", fg="white", text="🎨 Icônes XClient",
                                               command=lambda: self.open_icon_picker(icon_entry))
        group_xclient_icon_btn.pack(side="left")
        ToolTip(group_xclient_icon_btn, "Choisir parmi les icônes XClient")


        btns = tk.Frame(detail, bg="#1e2124")
        btns.pack(fill="x", pady=10)
        create_btn = RoundedButton(btns, width=120, height=30, cornerradius=6, bg="#f84444", fg="white",
                                   text="Créer", command=lambda: self._create_group(name_entry.get(), icon_entry.get() or None))
        create_btn.pack(side="left", padx=6)
        ToolTip(create_btn, "Créer un nouveau groupe")
        rename_btn = RoundedButton(btns, width=140, height=30, cornerradius=6, bg="#2e3440", fg="white",
                                   text="Renommer", command=lambda: self._rename_selected_group(name_entry))
        rename_btn.pack(side="left", padx=6)
        update_btn = RoundedButton(btns, width=160, height=30, cornerradius=6, bg="#2e3440", fg="white",
                                   text="Maj icône", command=lambda: self._update_selected_group(icon_entry.get() or None))
        update_btn.pack(side="left", padx=6)
        delete_btn = RoundedButton(btns, width=120, height=30, cornerradius=6, bg="#ff4444", fg="white",
                                   text="Supprimer", command=self._delete_selected_group)
        delete_btn.pack(side="left", padx=6)


        def on_select(evt=None):
            sel = self.groups_listbox.curselection()
            if not sel:
                return
            gid = self._group_id_from_listbox_index(sel[0])
            g = self.groups[gid]
            name_entry.delete(0, tk.END); name_entry.insert(0, g["name"])
            icon_entry.delete(0, tk.END); icon_entry.insert(0, g.get("icon") or "")
        self.groups_listbox.bind("<<ListboxSelect>>", on_select)
        on_select()

    def add_application(self):
        def save_app():
            name = name_entry.get()
            exe_path = exe_entry.get()
            icon_path = icon_entry.get() if icon_entry.get() else None
            group_name = group_var.get()
            group_id = self._group_id_by_name(group_name) or DEFAULT_GROUP_ID

            if not name or not exe_path:
                messagebox.showwarning("Erreur", "Le nom et le chemin de l'exécutable sont obligatoires.")
                return



            link_folder = self.links_path


            desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
            is_from_desktop = exe_path.lower().startswith(desktop_path.lower())
            

            if exe_path.lower().endswith('.url'):
                try:

                    with open(exe_path, 'r', encoding='utf-8-sig') as f:
                        content = f.read()
                    

                    new_path = os.path.join(link_folder, os.path.basename(exe_path))
                    with open(new_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    

                    if is_from_desktop:
                        try:
                            os.remove(exe_path)
                        except:
                            pass
                    

                    exe_path = new_path
                except Exception as e:
                    messagebox.showerror("Erreur", f"Erreur lors de la copie du fichier .url : {str(e)}")
                    return
                    

            elif is_from_desktop and os.path.isfile(exe_path) and not exe_path.lower().endswith('.exe'):
                try:

                    new_path = os.path.join(link_folder, os.path.basename(exe_path))
                    shutil.copy2(exe_path, new_path)
                    

                    try:
                        os.remove(exe_path)
                    except:
                        pass
                    

                    exe_path = new_path
                except Exception as e:
                    messagebox.showerror("Erreur", f"Erreur lors de la copie du fichier : {str(e)}")
                    return


            elif not exe_path.lower().endswith('.exe'):
                try:
                    import win32com.client
                    shell = win32com.client.Dispatch("WScript.Shell")
                    shortcut_path = os.path.join(link_folder, f"{name}.lnk")
                    shortcut = shell.CreateShortCut(shortcut_path)
                    shortcut.Targetpath = exe_path
                    shortcut.WorkingDirectory = os.path.dirname(exe_path)
                    shortcut.save()

                    exe_path = shortcut_path
                except Exception as e:
                    messagebox.showerror("Erreur", f"Erreur lors de la création du raccourci : {str(e)}")
                    return


            group_apps = sort_apps_for_group(self.applications, group_id)
            next_order = (group_apps[-1]["order"] + 1) if group_apps else 0
            self.applications.append({"name": name, "exe": exe_path, "icon": icon_path, "group_id": group_id, "order": next_order})
            self.save_all()
            self._refresh_group_filter_combo()
            self.update_app_grid()
            add_app_window.destroy()
        
        def detect_and_update_category():
            
            exe_path = exe_entry.get()
            name = name_entry.get()
            if exe_path and self.auto_categorize:
                detected_category = self.detect_app_category(exe_path, name)
                if detected_category != DEFAULT_GROUP_ID and detected_category in self.groups:
                    group_var.set(self.groups[detected_category]["name"])

                    category_label.config(text=f"✓ Catégorie détectée: {self.groups[detected_category]['name']}", 
                                        fg="#4caf50")
                else:
                    category_label.config(text="", fg="white")


        add_app_window = tk.Toplevel(self.root)
        add_app_window.geometry("900x700")
        self.setup_window(add_app_window, "Ajouter une application")
        

        title_frame = tk.Frame(add_app_window, bg="#1e2124")
        title_frame.pack(fill="x", padx=20, pady=20)
        
        title_label = tk.Label(title_frame, text="Ajouter une nouvelle application",
                             font=("Arial", 16, "bold"), fg="white", bg="#1e2124")
        title_label.pack()


        form_frame = tk.Frame(add_app_window, bg="#1e2124")
        form_frame.pack(fill="both", expand=True, padx=20)


        tk.Label(form_frame, text="Nom de l'application", bg="#1e2124", fg="white",
                font=("Arial", 10, "bold")).pack(anchor="w", pady=(0, 8))
        
        name_entry_frame = tk.Frame(form_frame, bg="#1e2124", height=42)
        name_entry_frame.pack(fill="x", pady=(0, 15))
        name_entry_frame.pack_propagate(False)
        
        name_entry = tk.Entry(name_entry_frame, font=("Arial", 11),
                            bg="#2e3440", fg="white", relief="flat", 
                            insertbackground="white", borderwidth=0,
                            highlightthickness=1, highlightbackground="#3a4250",
                            highlightcolor="#4a90e2")
        name_entry.pack(fill="both", expand=True, padx=2, pady=2, ipady=8)
        add_placeholder(name_entry, "Nom lisible (ex: Google Chrome)")


        tk.Label(form_frame, text="Chemin de l'exécutable", bg="#1e2124", fg="white",
                font=("Arial", 10, "bold")).pack(anchor="w", pady=(0, 8))
        
        exe_entry_frame = tk.Frame(form_frame, bg="#1e2124", height=42)
        exe_entry_frame.pack(fill="x", pady=(0, 10))
        exe_entry_frame.pack_propagate(False)
        
        exe_entry = tk.Entry(exe_entry_frame, font=("Arial", 11),
                           bg="#2e3440", fg="white", relief="flat",
                           insertbackground="white", borderwidth=0,
                           highlightthickness=1, highlightbackground="#3a4250",
                           highlightcolor="#4a90e2")
        exe_entry.pack(fill="both", expand=True, padx=2, pady=2, ipady=8)
        add_placeholder(exe_entry, "Chemin vers l'exécutable ou .url")
        
        exe_btn = RoundedButton(form_frame, width=150, height=32, cornerradius=8,
                               bg="#2e3440", fg="white", text="📁 Parcourir",
                               command=lambda: exe_entry.delete(0, tk.END) or exe_entry.insert(0, filedialog.askopenfilename(
                                   filetypes=[
                                       ("Fichiers exécutables", "*.exe;*.msi;*.bat;*.cmd;*.vbs;*.ps1;*.reg;*.dll;*.appref-ms;*.url"),
                                       ("Tout les fichiers", "*.*"),
                                       ("Raccourci Internet", "*.url"),
                                       ("Exécutable Windows", "*.exe"),
                                       ("Package d'installation", "*.msi"),
                                       ("Script batch", "*.bat"),
                                       ("Script command", "*.cmd"),
                                       ("Script VBScript", "*.vbs"),
                                       ("Script PowerShell", "*.ps1"),
                                       ("Fichier registre", "*.reg"),
                                       ("Bibliothèque DLL", "*.dll"),
                                       ("Application ClickOnce", "*.appref-ms"),
                                       ("Raccourci Internet", "*.url")
                                   ])))
        exe_btn.pack(anchor="w", pady=(0, 15))
        ToolTip(exe_btn, "Sélectionner un fichier exécutable")


        tk.Label(form_frame, text="Icône (URL ou fichier, Optionnel)", bg="#1e2124", fg="white",
                font=("Arial", 10, "bold")).pack(anchor="w", pady=(0, 8))
        
        icon_entry_frame = tk.Frame(form_frame, bg="#1e2124", height=42)
        icon_entry_frame.pack(fill="x", pady=(0, 10))
        icon_entry_frame.pack_propagate(False)
        
        icon_entry = tk.Entry(icon_entry_frame, font=("Arial", 11),
                            bg="#2e3440", fg="white", relief="flat",
                            insertbackground="white", borderwidth=0,
                            highlightthickness=1, highlightbackground="#3a4250",
                            highlightcolor="#4a90e2")
        icon_entry.pack(fill="both", expand=True, padx=2, pady=2, ipady=8)
        add_placeholder(icon_entry, "Fichier image ou URL (optionnel)")
        

        icon_buttons_frame = tk.Frame(form_frame, bg="#1e2124")
        icon_buttons_frame.pack(anchor="w", pady=(0, 15))
        
        browse_icon_btn = RoundedButton(icon_buttons_frame, width=150, height=32, cornerradius=8,
                                       bg="#2e3440", fg="white", text="📁 Parcourir",
                                       command=lambda: icon_entry.delete(0, tk.END) or icon_entry.insert(0, filedialog.askopenfilename(
                                           filetypes=[("Images", "*.png *.jpg *.jpeg *.gif *.ico")])))
        browse_icon_btn.pack(side="left", padx=(0, 10))
        ToolTip(browse_icon_btn, "Sélectionner un fichier image local")
        
        xclient_icon_btn = RoundedButton(icon_buttons_frame, width=180, height=32, cornerradius=8,
                                        bg="#4a90e2", fg="white", text="🎨 Icônes XClient",
                                        command=lambda: self.open_icon_picker(icon_entry))
        xclient_icon_btn.pack(side="left")
        ToolTip(xclient_icon_btn, "Choisir parmi les icônes XClient")


        tk.Label(form_frame, text="Groupe", bg="#1e2124", fg="white",
                font=("Arial", 10, "bold")).pack(anchor="w", pady=(0, 8))
        
        group_selection_frame = tk.Frame(form_frame, bg="#1e2124")
        group_selection_frame.pack(fill="x", pady=(0, 5))
        
        group_var = tk.StringVar(value=self.groups[DEFAULT_GROUP_ID]["name"])
        group_combo = ttk.Combobox(group_selection_frame, textvariable=group_var, state="readonly",
                                   values=self._group_names_for_combo(), font=("Arial", 11),
                                   height=10)
        group_combo.pack(side="left", fill="x", expand=True, ipady=8)
        

        detect_btn = RoundedButton(group_selection_frame, width=140, height=32, cornerradius=8,
                                  bg="#4caf50", fg="white", text="🔍 Détecter",
                                  command=detect_and_update_category)
        detect_btn.pack(side="left", padx=(10, 0))
        ToolTip(detect_btn, "Détecter automatiquement la catégorie")
        

        category_label = tk.Label(form_frame, text="", bg="#1e2124", fg="white",
                                font=("Arial", 9, "italic"))
        category_label.pack(anchor="w", pady=(5, 15))        

        def on_exe_change(*args):
            if self.auto_categorize:
                detect_and_update_category()
        
        exe_entry.bind("<FocusOut>", on_exe_change)


        buttons_frame = tk.Frame(add_app_window, bg="#1e2124")
        buttons_frame.pack(fill="x", padx=20, pady=20)


        cancel_btn = RoundedButton(buttons_frame, width=160, height=28, cornerradius=8,
                                 bg="#2e3440", fg="white", text="Annuler",
                                 command=add_app_window.destroy)
        cancel_btn.pack(side="left", padx=10)

        add_btn = RoundedButton(buttons_frame, width=200, height=28, cornerradius=8,
                              bg="#f84444", fg="white", text="Ajouter l'application",
                              command=save_app)
        add_btn.pack(side="right", padx=10)
        

        buttons_frame.update()

    def modify_app_order(self, index):
        app = self.applications[index]
        group_id = app.get("group_id", DEFAULT_GROUP_ID)
        
        dialog = tk.Toplevel(self.root)
        dialog.geometry("400x250")
        self.setup_window(dialog, "Modifier l'ordre")
        
        main_frame = tk.Frame(dialog, bg="#1e2124")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        tk.Label(main_frame, text=f"Modifier l'ordre de", 
                font=("Arial", 12, "bold"), fg="white", bg="#1e2124").pack(pady=5)
        tk.Label(main_frame, text=app["name"],
                font=("Arial", 10), fg="#4a90e2", bg="#1e2124").pack()
        
        # Liste des applications dans le même groupe
        apps_in_group = sort_apps_for_group(self.applications, group_id)
        current_order = app.get("order", 0)
        
        # Création du spinbox pour sélectionner l'ordre
        order_frame = tk.Frame(main_frame, bg="#1e2124")
        order_frame.pack(pady=20)
        
        tk.Label(order_frame, text="Position :", fg="white", bg="#1e2124").pack(side="left", padx=(0, 10))
        order_var = tk.StringVar(value=str(current_order + 1))
        order_spin = tk.Spinbox(order_frame, from_=1, to=len(apps_in_group), 
                               textvariable=order_var, width=5,
                               bg="#2e3440", fg="white", buttonbackground="#2e3440",
                               relief="flat", highlightthickness=1,
                               highlightbackground="#3a4250", insertbackground="white")
        order_spin.pack(side="left")
        
        buttons_frame = tk.Frame(main_frame, bg="#1e2124")
        buttons_frame.pack(side="bottom", pady=20)
        
        def apply_order():
            try:
                new_pos = int(order_var.get()) - 1
                if 0 <= new_pos < len(apps_in_group):
                    # Réorganise les ordres des applications du groupe
                    old_pos = apps_in_group.index(app)
                    apps_in_group.insert(new_pos, apps_in_group.pop(old_pos))
                    
                    # Met à jour les ordres
                    for i, a in enumerate(apps_in_group):
                        idx = self.applications.index(a)
                        self.applications[idx]["order"] = i
                    
                    self.save_all()
                    self.update_app_grid()
                dialog.destroy()
            except ValueError:
                messagebox.showerror("Erreur", "Veuillez entrer un nombre valide")
        
        cancel_btn = RoundedButton(buttons_frame, width=140, height=32, cornerradius=8,
                                 bg="#2e3440", fg="white", text="Annuler",
                                 command=dialog.destroy)
        cancel_btn.pack(side="left", padx=10)
        
        apply_btn = RoundedButton(buttons_frame, width=140, height=32, cornerradius=8,
                                bg="#4a90e2", fg="white", text="Appliquer",
                                command=apply_order)
        apply_btn.pack(side="left", padx=10)

    def modify_application(self, index):
        app = self.applications[index]

        def save_modifications():
            new_name = new_name_entry.get()
            new_exe = new_exe_entry.get()
            new_icon = new_icon_entry.get() if new_icon_entry.get() else None
            new_group_name = group_var.get()
            new_group_id = self._group_id_by_name(new_group_name) or DEFAULT_GROUP_ID


            prev = self.applications[index]
            order = prev.get("order", 0)
            self.applications[index] = {"name": new_name, "exe": new_exe, "icon": new_icon, "group_id": new_group_id, "order": order}
            self.save_all()
            self._refresh_group_filter_combo()
            self.update_app_grid()
            modify_window.destroy()


        modify_window = tk.Toplevel(self.root)
        modify_window.geometry("900x650")
        self.setup_window(modify_window, "Modifier l'application")
        

        title_frame = tk.Frame(modify_window, bg="#1e2124")
        title_frame.pack(fill="x", padx=20, pady=20)
        
        title_label = tk.Label(title_frame, text="Modifier l'application",
                             font=("Arial", 16, "bold"), fg="white", bg="#1e2124")
        title_label.pack()


        form_frame = tk.Frame(modify_window, bg="#1e2124")
        form_frame.pack(fill="both", expand=True, padx=20)


        tk.Label(form_frame, text="Nom de l'application", bg="#1e2124", fg="white",
                font=("Arial", 10, "bold")).pack(anchor="w", pady=(0, 8))
        
        new_name_entry_frame = tk.Frame(form_frame, bg="#1e2124", height=42)
        new_name_entry_frame.pack(fill="x", pady=(0, 15))
        new_name_entry_frame.pack_propagate(False)
        
        new_name_entry = tk.Entry(new_name_entry_frame, font=("Arial", 11),
                            bg="#2e3440", fg="white", relief="flat",
                            insertbackground="white", borderwidth=0,
                            highlightthickness=1, highlightbackground="#3a4250",
                            highlightcolor="#4a90e2")
        new_name_entry.pack(fill="both", expand=True, padx=2, pady=2, ipady=8)
        new_name_entry.insert(0, app["name"])


        tk.Label(form_frame, text="Chemin de l'exécutable", bg="#1e2124", fg="white",
                font=("Arial", 10, "bold")).pack(anchor="w", pady=(0, 8))
        
        new_exe_entry_frame = tk.Frame(form_frame, bg="#1e2124", height=42)
        new_exe_entry_frame.pack(fill="x", pady=(0, 10))
        new_exe_entry_frame.pack_propagate(False)
        
        new_exe_entry = tk.Entry(new_exe_entry_frame, font=("Arial", 11),
                           bg="#2e3440", fg="white", relief="flat",
                           insertbackground="white", borderwidth=0,
                           highlightthickness=1, highlightbackground="#3a4250",
                           highlightcolor="#4a90e2")
        new_exe_entry.pack(fill="both", expand=True, padx=2, pady=2, ipady=8)
        new_exe_entry.insert(0, app["exe"])
        
        new_exe_btn = RoundedButton(form_frame, width=150, height=32, cornerradius=8,
                                    bg="#2e3440", fg="white", text="📁 Parcourir",
                                    command=lambda: new_exe_entry.delete(0, tk.END) or new_exe_entry.insert(0, filedialog.askopenfilename(
                                        filetypes=[
                                            ("Fichiers exécutables", "*.exe;*.msi;*.bat;*.cmd;*.vbs;*.ps1;*.reg;*.dll;*.appref-ms;*.url"),
                                            ("Tout les fichiers", "*.*"),
                                            ("Raccourci Internet", "*.url"),
                                            ("Exécutable Windows", "*.exe"),
                                            ("Package d'installation", "*.msi"),
                                            ("Script batch", "*.bat"),
                                            ("Script command", "*.cmd"),
                                            ("Script VBScript", "*.vbs"),
                                            ("Script PowerShell", "*.ps1"),
                                            ("Fichier registre", "*.reg"),
                                            ("Bibliothèque DLL", "*.dll"),
                                            ("Application ClickOnce", "*.appref-ms"),
                                            ("Raccourci Internet", "*.url")
                                        ])))
        new_exe_btn.pack(anchor="w", pady=(0, 15))
        ToolTip(new_exe_btn, "Sélectionner un fichier exécutable")


        tk.Label(form_frame, text="Icône (URL ou fichier, Optionnel)", bg="#1e2124", fg="white",
                font=("Arial", 10, "bold")).pack(anchor="w", pady=(0, 8))
        
        new_icon_entry_frame = tk.Frame(form_frame, bg="#1e2124", height=42)
        new_icon_entry_frame.pack(fill="x", pady=(0, 10))
        new_icon_entry_frame.pack_propagate(False)
        
        new_icon_entry = tk.Entry(new_icon_entry_frame, font=("Arial", 11),
                            bg="#2e3440", fg="white", relief="flat",
                            insertbackground="white", borderwidth=0,
                            highlightthickness=1, highlightbackground="#3a4250",
                            highlightcolor="#4a90e2")
        new_icon_entry.pack(fill="both", expand=True, padx=2, pady=2, ipady=8)
        new_icon_entry.insert(0, app["icon"] if app["icon"] else "")
        

        new_icon_buttons_frame = tk.Frame(form_frame, bg="#1e2124")
        new_icon_buttons_frame.pack(anchor="w", pady=(0, 15))
        
        new_browse_icon_btn = RoundedButton(new_icon_buttons_frame, width=150, height=32, cornerradius=8,
                                            bg="#2e3440", fg="white", text="📁 Parcourir",
                                            command=lambda: new_icon_entry.delete(0, tk.END) or new_icon_entry.insert(0, filedialog.askopenfilename(
                                                filetypes=[("Images", "*.png *.jpg *.jpeg *.gif *.ico")])))
        new_browse_icon_btn.pack(side="left", padx=(0, 10))
        ToolTip(new_browse_icon_btn, "Sélectionner un fichier image local")
        
        new_xclient_icon_btn = RoundedButton(new_icon_buttons_frame, width=180, height=32, cornerradius=8,
                                             bg="#4a90e2", fg="white", text="🎨 Icônes XClient",
                                             command=lambda: self.open_icon_picker(new_icon_entry))
        new_xclient_icon_btn.pack(side="left")
        ToolTip(new_xclient_icon_btn, "Choisir parmi les icônes XClient")


        tk.Label(form_frame, text="Groupe", bg="#1e2124", fg="white",
                font=("Arial", 10, "bold")).pack(anchor="w", pady=(0, 8))
        group_var = tk.StringVar(value=self.groups.get(app.get("group_id", DEFAULT_GROUP_ID), self.groups[DEFAULT_GROUP_ID])["name"])
        group_combo = ttk.Combobox(form_frame, textvariable=group_var, state="readonly",
                                   values=self._group_names_for_combo(), font=("Arial", 11),
                                   height=10)
        group_combo.pack(fill="x", pady=(0, 15), ipady=8)


        buttons_frame = tk.Frame(modify_window, bg="#1e2124")
        buttons_frame.pack(fill="x", padx=20, pady=20)


        cancel_btn = RoundedButton(buttons_frame, width=160, height=28, cornerradius=8,
                                 bg="#2e3440", fg="white", text="Annuler",
                                 command=modify_window.destroy)
        cancel_btn.pack(side="left", padx=10)

        save_btn = RoundedButton(buttons_frame, width=200, height=28, cornerradius=8,
                               bg="#f84444", fg="white", text="Enregistrer les modifications",
                               command=save_modifications)
        save_btn.pack(side="right", padx=10)
        

        buttons_frame.update()

    def delete_application(self, index):
        if index < 0 or index >= len(self.applications):
            return
            
        app = self.applications[index]
        

        dialog = tk.Toplevel(self.root)
        dialog.geometry("600x500")
        self.setup_window(dialog, "Confirmer la suppression")
        

        dialog.focus_set()
        dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)
        

        message_frame = tk.Frame(dialog, bg="#1e2124")
        message_frame.pack(expand=True, fill="both", padx=20, pady=20)
        
        warning_label = tk.Label(message_frame, text="⚠", font=("Arial", 24),
                               fg="#ff4444", bg="#1e2124")
        warning_label.pack(pady=(0, 10))
        
        message_label = tk.Label(message_frame, 
                               text=f'Êtes-vous sûr de vouloir supprimer l\'application\n"{app["name"]}" ?',
                               fg="white", bg="#1e2124", font=("Arial", 11, "bold"))
        message_label.pack(pady=10)
        

        options_frame = tk.Frame(message_frame, bg="#2e3440")
        options_frame.pack(fill="x", pady=20, padx=20)
        
        tk.Label(options_frame, text="Que faire avec les statistiques d'utilisation ?",
                fg="white", bg="#2e3440", font=("Arial", 10, "bold")).pack(anchor="w", pady=(10, 10))
        

        delete_stats_var = tk.BooleanVar(value=False)
        

        stats_check = tk.Checkbutton(options_frame, 
                                     text="Supprimer également toutes les statistiques et objectifs liés à cette application",
                                     variable=delete_stats_var,
                                     bg="#2e3440", fg="white", selectcolor="#1e2124",
                                     activebackground="#2e3440", activeforeground="white",
                                     font=("Arial", 9), wraplength=500, justify="left")
        stats_check.pack(anchor="w", padx=10, pady=5)
        

        info_label = tk.Label(options_frame, 
                             text="⚠ Si vous conservez les statistiques, elles resteront visibles\ndans le tableau de bord même après la suppression.",
                             fg="#9aa0a6", bg="#2e3440", font=("Arial", 8, "italic"),
                             justify="left")
        info_label.pack(anchor="w", padx=10, pady=(5, 10))
        

        button_frame = tk.Frame(dialog, bg="#1e2124")
        button_frame.pack(fill="x", padx=20, pady=20)
        

        cancel_btn = RoundedButton(button_frame, width=220, height=35, cornerradius=6,
                                 bg="#2e3440", fg="white", text="Annuler",
                                 command=dialog.destroy)
        cancel_btn.pack(side="left", padx=15)
        
        delete_btn = RoundedButton(button_frame, width=220, height=35, cornerradius=6,
                                 bg="#ff4444", fg="white", text="Supprimer",
                                 command=lambda: self.confirm_delete(index, dialog, delete_stats_var.get()))
        delete_btn.pack(side="right", padx=15)
        

        button_frame.update()


        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")

    def confirm_delete(self, index, dialog, delete_stats=False):
        try:
            if 0 <= index < len(self.applications):
                app_name = self.applications[index]["name"]
                

                del self.applications[index]
                self.save_all()
                

                if delete_stats:

                    removed_activity = self.activity_tracker.remove_app_data(app_name)
                    

                    removed_goals = self.goals_manager.remove_goals_for_app(app_name)
                    

                    stats_msg = []
                    if removed_activity:
                        stats_msg.append("statistiques d'utilisation")
                    if removed_goals > 0:
                        stats_msg.append(f"{removed_goals} objectif(s)")
                    
                    if stats_msg:
                        messagebox.showinfo("Suppression réussie", 
                                          f'Application "{app_name}" supprimée.\n\n'
                                          f'Également supprimé : {", ".join(stats_msg)}.')
                    

                    if hasattr(self, 'goals_progress_frame'):
                        self._update_goals_progress_display()
                
                self.update_app_grid()
            dialog.destroy()
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la suppression : {str(e)}")
            dialog.destroy()

    def launch_application(self):
        try:
            selected_item = getattr(self, "selected_button", None)
            if selected_item is None:
                raise IndexError()
            selected_app = self.applications[selected_item]
            self._open_path_or_command(selected_app["exe"])
        except IndexError:
            messagebox.showwarning("Erreur", "Aucune application sélectionnée.")
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de lancer l'élément : {str(e)}")

    def update_app_grid(self):

        for widget in self.grid_frame.winfo_children():
            widget.destroy()


        self.canvas.yview_moveto(0)

        group = self.groups.get(self.active_group_filter, self.groups[DEFAULT_GROUP_ID])


        group_frame = tk.Frame(self.grid_frame, bg="#1e2124")
        group_frame.pack(fill="x", expand=True, pady=(0, 20))


        header = tk.Frame(group_frame, bg="#1e2124")
        header.pack(fill="x", padx=5, pady=(10, 5))
        icon_img = None
        if group.get("icon"):
            try:
                icon_img = Image.open(group["icon"])
                icon_img = icon_img.resize((20, 20))
                icon_img = ImageTk.PhotoImage(icon_img)
            except Exception:
                icon_img = None
        if icon_img:
            lbl_icon = tk.Label(header, image=icon_img, bg=header.cget("bg"))
            lbl_icon.image = icon_img
            lbl_icon.pack(side="left", padx=(5, 8))
        tk.Label(header, text=group["name"], font=("Arial", 14, "bold"), fg="white", bg=header.cget("bg")).pack(side="left")


        drop_zone = tk.Frame(group_frame, bg="#1e2124")
        drop_zone.pack(fill="x")
        drop_zone.group_id = group["id"]
        drop_zone.bind("<Enter>", lambda e, z=drop_zone: self._on_group_drop_enter(z))
        drop_zone.bind("<Leave>", lambda e, z=drop_zone: self._on_group_drop_leave(z))
        drop_zone.bind("<ButtonRelease-1>", lambda e, z=drop_zone: self._on_group_drop(z))


        apps_container = tk.Frame(group_frame, bg="#1e2124")
        apps_container.pack(fill="x", padx=10, pady=10)

        col = 0
        row = 0
        

        if self.active_group_filter == DEFAULT_GROUP_ID:

            apps = sorted(self.applications, key=lambda a: a.get("order", 0))
        else:

            apps = sort_apps_for_group(self.applications, group["id"])
        

        if self.search_query:
            q = self.search_query.lower()
            apps = [a for a in apps if q in a.get("name", "").lower()]
        
        if not apps:
            msg = "Aucune application" if not self.search_query else "Aucune application ne correspond à votre recherche"
            tk.Label(apps_container, text=msg, fg="#9aa0a6", bg=apps_container.cget("bg")).grid(row=0, column=0, sticky="w", padx=5, pady=5)
        
        for app in apps:
            index = self.applications.index(app)

            card = RoundedCard(apps_container, width=200, height=250)
            card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            

            app_frame = card.inner_frame


            def trigger_parent_hover(event, enter=True, this_card=card):
                if enter:
                    this_card._on_enter(event)
                else:
                    this_card._on_leave(event)
            

            button_frame = tk.Frame(app_frame, bg="#2e3440")
            button_frame.place(relx=1.0, rely=0, anchor="ne", x=-5, y=5)
            button_frame.place_forget()
            button_frame.bind('<Enter>', lambda e, f=trigger_parent_hover: f(e, True))
            button_frame.bind('<Leave>', lambda e, f=trigger_parent_hover: f(e, False))


            try:
                edit_icon = Image.open('icon/modif.png')
                edit_icon = edit_icon.resize((16, 16))
                edit_photo = ImageTk.PhotoImage(edit_icon)
                
                delete_icon = Image.open('icon/delete.png')
                delete_icon = delete_icon.resize((16, 16))
                delete_photo = ImageTk.PhotoImage(delete_icon)
            except Exception as e:
                print(f"Erreur de chargement des icônes d'action : {e}")
                edit_photo = None
                delete_photo = None


            edit_btn = tk.Button(button_frame, image=edit_photo if edit_photo else "✎",
                                command=lambda i=index: self.modify_application(i),
                                bg="#2e3440", fg="white", relief="flat", bd=0,
                                cursor="hand2", width=20 if not edit_photo else None,
                                height=20 if not edit_photo else None,
                                highlightthickness=0,
                                activebackground="#2e3440",
                                borderwidth=0)
            edit_btn.image = edit_photo
            edit_btn.pack(side="left", padx=2)


            delete_btn = tk.Button(button_frame, image=delete_photo if delete_photo else "×",
                                command=lambda i=index: self.delete_application(i),
                                bg="#2e3440", fg="#ff4444", relief="flat", bd=0,
                                cursor="hand2", width=20 if not edit_photo else None,
                                height=20 if not edit_photo else None,
                                highlightthickness=0,
                                activebackground="#2e3440",
                                borderwidth=0)
            delete_btn.image = delete_photo
            delete_btn.pack(side="left", padx=2)
            delete_btn.bind("<Button-1>", lambda e, i=index: [self.delete_application(i), "break"])


            card.button_frame = button_frame


            icon_photo = None
            try:
                if app.get("icon"):

                    if app["icon"].startswith(("http://", "https://")):
                        import urllib.request
                        import tempfile
                        
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
                            urllib.request.urlretrieve(app["icon"], tmp_file.name)
                            icon_image = Image.open(tmp_file.name)
                            os.unlink(tmp_file.name)
                    else:
                        icon_image = Image.open(app["icon"])
                    

                    if icon_image.mode != "RGBA":
                        icon_image = icon_image.convert("RGBA")
                    

                    icon_image = icon_image.resize((150, 150), Image.Resampling.LANCZOS)
                    

                    mask = Image.new('L', (150, 150), 0)
                    mask_draw = ImageDraw.Draw(mask)
                    mask_draw.rounded_rectangle([(0, 0), (150, 150)], radius=15, fill=255)
                    

                    output = Image.new('RGBA', (150, 150), (0, 0, 0, 0))
                    

                    r, g, b, a = icon_image.split()
                    a = ImageChops.multiply(a, mask)
                    icon_image.putalpha(a)
                    

                    output.paste(icon_image, (0, 0), icon_image)
                    
                    icon_photo = ImageTk.PhotoImage(output)
            except Exception as e:
                print(f"Erreur de chargement de l'icône : {e}")


            content_frame = tk.Frame(app_frame, bg="#2e3440")
            content_frame.place(relx=0.5, rely=0.5, anchor="center")

            if icon_photo:
                icon_label = tk.Label(content_frame, image=icon_photo, bg="#2e3440")
                icon_label.image = icon_photo
                icon_label.pack(pady=(0, 10))
                icon_label.bind('<Enter>', lambda e, f=trigger_parent_hover: f(e, True))
                icon_label.bind('<Leave>', lambda e, f=trigger_parent_hover: f(e, False))


            full_name = app["name"]
            short_name = full_name if len(full_name) <= 22 else full_name[:21] + "…"
            name_label = tk.Label(content_frame, text=short_name, 
                                fg="white", bg="#2e3440",
                                font=("Arial", 12))
            name_label.pack()
            ToolTip(name_label, full_name)
            name_label.bind('<Enter>', lambda e, f=trigger_parent_hover: f(e, True))
            name_label.bind('<Leave>', lambda e, f=trigger_parent_hover: f(e, False))

            if isinstance(button_frame, tk.Frame):
                for child in button_frame.winfo_children():
                    try:
                        child.configure(activebackground="#2e3440")
                    except Exception:
                        pass

            content_frame.bind('<Enter>', lambda e, f=trigger_parent_hover: f(e, True))
            content_frame.bind('<Leave>', lambda e, f=trigger_parent_hover: f(e, False))


            app_frame.bind("<Double-Button-1>", lambda e, i=index: self.launch_app(i))
            content_frame.bind("<Double-Button-1>", lambda e, i=index: self.launch_app(i))
            if icon_photo:
                icon_label.bind("<Double-Button-1>", lambda e, i=index: self.launch_app(i))
            name_label.bind("<Double-Button-1>", lambda e, i=index: self.launch_app(i))

            # Menu contextuel pour l'application
            app_menu = tk.Menu(self.root, tearoff=0, bg="#2e3440", fg="white", activebackground="#3a4250", activeforeground="white")
            app_menu.add_command(label="Modifier l'ordre", command=lambda i=index: self.modify_app_order(i))
            app_menu.add_command(label="Modifier l'application", command=lambda i=index: self.modify_application(i))
            app_menu.add_separator()
            app_menu.add_command(label="Supprimer", command=lambda i=index: self.delete_application(i), foreground="#ff4444")

            def show_app_menu(e, i=index):
                self.select_application(i)
                app_menu.tk_popup(e.x_root, e.y_root)

            app_frame.bind("<Button-1>", lambda e, i=index: self.select_application(i))
            content_frame.bind("<Button-1>", lambda e, i=index: self.select_application(i))
            app_frame.bind("<Button-3>", show_app_menu)
            content_frame.bind("<Button-3>", show_app_menu)
            if icon_photo:
                icon_label.bind("<Button-1>", lambda e, i=index: self.select_application(i))
                icon_label.bind("<Button-3>", show_app_menu)
            name_label.bind("<Button-1>", lambda e, i=index: self.select_application(i))
            name_label.bind("<Button-3>", show_app_menu)


            app_frame.bind("<ButtonPress-1>", lambda e, i=index: self._on_drag_start(i))
            app_frame.bind("<B1-Motion>", lambda e, i=index, container=apps_container: self._on_drag_motion_app(e, container, group["id"]))
            app_frame.bind("<ButtonRelease-1>", lambda e, i=index, container=apps_container, grp_id=group["id"]: self._on_drag_end_app(e, container, grp_id))

            col += 1
            if col >= 4:
                col = 0
                row += 1

    def select_application(self, index):

        if 0 <= index < len(self.applications):
            self.selected_button = index


    def launch_app(self, index):
        try:
            if 0 <= index < len(self.applications):
                app = self.applications[index]
                self._open_path_or_command(app["exe"])

                self.activity_tracker.on_app_launch(app["name"])
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de lancer l'application : {str(e)}")

    def save_all(self):
        data = {
            "applications": self.applications, 
            "groups": self.groups,
            "settings": {
                "auto_categorize": self.auto_categorize,
                "hide_completed_goals": self.hide_completed_goals
            }
        }
        with open("applications.json", "w") as f:
            json.dump(data, f, indent=2)
    
    def _initialize_default_categories(self):
        
        categories_created = False
        for cat_id, cat_data in APP_CATEGORIES.items():
            if cat_id not in self.groups:

                order = len(self.groups)
                icon_path = cat_data.get("icon")

                if icon_path and not os.path.exists(icon_path):
                    icon_path = None
                self.groups[cat_id] = {
                    "id": cat_id,
                    "name": cat_data["name"],
                    "icon": icon_path,
                    "order": order,
                    "auto_created": True
                }
                categories_created = True
        
        if categories_created:
            self.save_all()
    
    def detect_app_category(self, exe_path, app_name=""):
        """
        Détecte automatiquement la catégorie d'une application
        
        Args:
            exe_path: Chemin vers l'exécutable
            app_name: Nom de l'application (optionnel)
        
        Returns:
            str: ID du groupe détecté ou DEFAULT_GROUP_ID
        """
        if not exe_path:
            return DEFAULT_GROUP_ID
        
        exe_path_lower = exe_path.lower()
        app_name_lower = app_name.lower()
        

        scores = {}
        
        for cat_id, cat_data in APP_CATEGORIES.items():
            score = 0
            

            for keyword in cat_data.get("keywords", []):
                if keyword in exe_path_lower:
                    score += 3
                if keyword in app_name_lower:
                    score += 2
            

            for path_part in cat_data.get("paths", []):
                if path_part.lower() in exe_path_lower:
                    score += 5
            

            exe_name = os.path.basename(exe_path_lower)
            for known_exe in cat_data.get("executables", []):
                if known_exe.lower() == exe_name:
                    score += 10
            

            for ext in cat_data.get("extensions", []):
                if exe_path_lower.endswith(ext):
                    score += 1
            
            if score > 0:
                scores[cat_id] = score
        

        if scores:
            best_category = max(scores.items(), key=lambda x: x[1])
            if best_category[1] >= 3:
                return best_category[0]
        
        return DEFAULT_GROUP_ID
    
    def recategorize_all_apps(self):
        
        recategorized_count = 0
        for app in self.applications:
            old_group = app.get("group_id", DEFAULT_GROUP_ID)

            if old_group == DEFAULT_GROUP_ID:
                detected_category = self.detect_app_category(app["exe"], app["name"])
                if detected_category != DEFAULT_GROUP_ID:
                    app["group_id"] = detected_category
                    recategorized_count += 1
        
        if recategorized_count > 0:
            self.save_all()
            self.update_app_grid()
            messagebox.showinfo("Catégorisation", 
                              f"{recategorized_count} application(s) ont été recatégorisées automatiquement.")
        else:
            messagebox.showinfo("Catégorisation", 
                              "Aucune application à recatégoriser.")
    
    def cleanup_orphaned_stats(self):
        
        app_names = {app["name"] for app in self.applications}
        tracked_apps = set(self.activity_tracker.activities.keys())
        goal_apps = {goal["app_name"] for goal in self.goals_manager.goals.values()}
        

        orphaned_stats = tracked_apps - app_names
        orphaned_goals = goal_apps - app_names
        
        if not orphaned_stats and not orphaned_goals:
            messagebox.showinfo("Nettoyage", "Aucune statistique orpheline trouvée.")
            return
        

        message = "Applications avec statistiques mais non configurées:\n\n"
        if orphaned_stats:
            message += f"Statistiques: {len(orphaned_stats)} app(s)\n"
            message += "   - " + "\n   - ".join(list(orphaned_stats)[:5])
            if len(orphaned_stats) > 5:
                message += f"\n   ... et {len(orphaned_stats) - 5} autres\n"
        if orphaned_goals:
            message += f"\n🎯 Objectifs: {len(orphaned_goals)} app(s)\n"
        
        message += "\n\nVoulez-vous supprimer ces données ?"
        
        if messagebox.askyesno("Nettoyage des statistiques", message):
            removed_count = 0
            for app_name in orphaned_stats:
                if self.activity_tracker.remove_app_data(app_name):
                    removed_count += 1
            
            for app_name in orphaned_goals:
                removed_count += self.goals_manager.remove_goals_for_app(app_name)
            
            if hasattr(self, 'goals_progress_frame'):
                self._update_goals_progress_display()
            
            messagebox.showinfo("Nettoyage terminé", 
                              f"{removed_count} élément(s) supprimé(s).")

    def load_raw_data(self):
        if os.path.exists("applications.json"):
            with open("applications.json", "r") as f:
                try:
                    return json.load(f)
                except Exception:
                    return []
        return []

    def setup_window(self, window, title):
        
        window.title(f"XClient - {title}")
        window.configure(bg="#1e2124")
        window.resizable(False, False)
        try:
            window.iconbitmap('icon/icon_resized.ico')
        except Exception as e:
            print(f"Erreur lors de la définition de l'icône : {e}")
        window.transient(self.root)
        window.grab_set()
        

        window.update_idletasks()

        geom = window.geometry()
        size_part = geom.split("+")[0]
        try:
            width, height = map(int, size_part.split("x"))
        except Exception:
            width = window.winfo_width()
            height = window.winfo_height()
        x = (window.winfo_screenwidth() // 2) - (width // 2)
        y = (window.winfo_screenheight() // 2) - (height // 2)
        window.geometry(f"{width}x{height}+{x}+{y}")


    def _group_names_for_combo(self):

        ordered = sort_groups_for_sidebar(self.groups)
        return [g["name"] for g in ordered]

    def _group_id_by_name(self, name):
        for gid, g in self.groups.items():
            if g["name"] == name:
                return gid
        return None

    def _refresh_group_filter_combo(self):
        try:
            self.group_combo["values"] = self._group_names_for_combo()

            if self.active_group_filter not in self.groups:
                self.active_group_filter = DEFAULT_GROUP_ID

            current_name = self.groups[self.active_group_filter]["name"]
            self.group_var.set(current_name)
        except Exception:
            pass

    def _on_group_filter_changed(self):
        name = self.group_var.get()
        gid = self._group_id_by_name(name)
        if gid:
            self.active_group_filter = gid
            self.update_app_grid()

    def _on_search_changed(self):

        txt = self.search_entry.get()
        if getattr(self.search_entry, "_has_placeholder", False):
            txt = ""
        self.search_query = txt.strip()
        self.update_app_grid()


    def _build_sidebar(self):
        for w in self.sidebar.winfo_children():
            w.destroy()


        settings_icon = self.load_icon("settings.png", size=(20, 20))
        if settings_icon:
            mg = tk.Label(self.sidebar, image=settings_icon, bg="#161a1e", cursor="hand2")
            mg.image = settings_icon
            mg.pack(pady=(10, 6))
            mg.bind("<Button-1>", lambda e: self.open_groups_manager())
            

            def settings_hover_in(e):
                mg.configure(bg="#1f252b")
            def settings_hover_out(e):
                mg.configure(bg="#161a1e")
            mg.bind("<Enter>", settings_hover_in)
            mg.bind("<Leave>", settings_hover_out)
            
            ToolTip(mg, "Ouvrir le gestionnaire de groupes")
        
        title_grp = tk.Label(self.sidebar, text="Groupes", bg="#161a1e", fg="#9aa0a6", font=("Arial", 10, "bold"))
        title_grp.pack(pady=(0,8))


        scroll_container = tk.Frame(self.sidebar, bg="#161a1e")
        scroll_container.pack(fill="both", expand=True)

        groups_canvas = tk.Canvas(scroll_container, bg="#161a1e", highlightthickness=0)
        groups_scrollbar = ttk.Scrollbar(scroll_container, orient="vertical", command=groups_canvas.yview, style="Groups.Vertical.TScrollbar")
        groups_canvas.configure(yscrollcommand=groups_scrollbar.set)

        groups_scrollbar.pack(side="right", fill="y")
        groups_canvas.pack(side="left", fill="both", expand=True)

        groups_inner = tk.Frame(groups_canvas, bg="#161a1e")
        inner_window = groups_canvas.create_window((0, 0), window=groups_inner, anchor="nw")

        def _update_scrollregion(event=None):
            groups_canvas.configure(scrollregion=groups_canvas.bbox("all"))
        def _resize_inner(event):
            groups_canvas.itemconfig(inner_window, width=event.width)

        groups_inner.bind("<Configure>", _update_scrollregion)
        groups_canvas.bind("<Configure>", _resize_inner)


        def _on_mousewheel_groups(e):
            groups_canvas.yview_scroll(int(-1*(e.delta/120)), "units")
        def _bind_groups_wheel(e=None):
            groups_canvas.bind_all("<MouseWheel>", _on_mousewheel_groups)
        def _unbind_groups_wheel(e=None):
            groups_canvas.unbind_all("<MouseWheel>")
        groups_canvas.bind("<Enter>", _bind_groups_wheel)
        groups_canvas.bind("<Leave>", _unbind_groups_wheel)

        self._sidebar_group_widgets = []
        ordered = sort_groups_for_sidebar(self.groups)
        for g in ordered:
            item = tk.Frame(groups_inner, bg="#161a1e")
            item.pack(pady=6, fill="x")
            item.group_id = g["id"]
            self._sidebar_group_widgets.append((item, g["id"]))

            item.bind("<ButtonPress-1>", lambda e, gid=g["id"]: self._on_group_drag_start(gid))
            item.bind("<B1-Motion>", lambda e, gid=g["id"]: self._on_group_drag_motion(e))
            item.bind("<ButtonRelease-1>", lambda e, gid=g["id"]: self._on_group_drag_end(e))


            icon_img = None
            if g.get("icon"):
                try:
                    im = Image.open(g["icon"]).resize((28, 28))
                    icon_img = ImageTk.PhotoImage(im)
                except Exception:
                    icon_img = None

            def on_click(evt=None, gid=g["id"]):
                self.active_group_filter = gid
                self.update_app_grid()
                self._highlight_active_group()

            if icon_img:
                icon_lbl = tk.Label(item, image=icon_img, bg="#161a1e", cursor="hand2")
                icon_lbl.image = icon_img
                icon_lbl.pack()
                icon_lbl.bind("<Button-1>", on_click)
            else:

                c = tk.Canvas(item, width=32, height=32, bg="#161a1e", highlightthickness=0, cursor="hand2")
                c.pack()
                oval_id = c.create_oval(2, 2, 30, 30, fill="#2e3440", outline="#2e3440")
                c.bind("<Button-1>", on_click)


            name_short = g["name"] if len(g["name"]) <= 6 else g["name"][:6] + "…"
            name_lbl = tk.Label(item, text=name_short, bg="#161a1e", fg="white", font=("Arial", 8))
            name_lbl.pack()
            ToolTip(name_lbl, g["name"])

            def _hover_in(e, w=item):
                w.configure(bg="#1a1e22")
                for ch in w.winfo_children():
                    if isinstance(ch, tk.Label) or isinstance(ch, tk.Canvas):
                        ch.configure(bg="#1a1e22")
            def _hover_out(e, w=item):
                if getattr(w, "group_id", None) != self.active_group_filter:
                    w.configure(bg="#161a1e")
                    for ch in w.winfo_children():
                        if isinstance(ch, tk.Label) or isinstance(ch, tk.Canvas):
                            ch.configure(bg="#161a1e")
            item.bind("<Enter>", _hover_in)
            item.bind("<Leave>", _hover_out)

            # Menu contextuel pour le groupe
            group_menu = tk.Menu(self.root, tearoff=0, bg="#2e3440", fg="white", activebackground="#3a4250", activeforeground="white")
            if g["id"] != DEFAULT_GROUP_ID:  # Ne pas montrer les options pour le groupe par défaut
                group_menu.add_command(label="Supprimer", command=lambda gid=g["id"]: self._delete_group(gid), foreground="#ff4444")
            
            def show_group_menu(e, gid=g["id"]):
                if gid != DEFAULT_GROUP_ID:  # N'affiche le menu que pour les groupes non-défaut
                    # Sélectionne le groupe et met à jour l'affichage
                    self.active_group_filter = gid
                    self.update_app_grid()
                    self._highlight_active_group()
                    # Affiche le menu contextuel
                    group_menu.tk_popup(e.x_root, e.y_root)
                    
            item.bind("<Button-3>", show_group_menu)
            if icon_img:
                icon_lbl.bind("<Button-3>", show_group_menu)
            # Ajouter le binding au label du nom
            name_lbl.bind("<Button-3>", show_group_menu)


            item.group_id = g["id"]

        self._highlight_active_group()

    def _highlight_active_group(self):
        for item in self.sidebar.winfo_children():

            if isinstance(item, tk.Frame) and hasattr(item, "group_id"):
                if item.group_id == self.active_group_filter:
                    item.configure(bg="#20262c")
                    for ch in item.winfo_children():
                        if isinstance(ch, tk.Label):
                            ch.configure(bg="#20262c")
                        if isinstance(ch, tk.Canvas):
                            ch.configure(bg="#20262c")
                else:
                    item.configure(bg="#161a1e")
                    for ch in item.winfo_children():
                        if isinstance(ch, tk.Label):
                            ch.configure(bg="#161a1e")
                        if isinstance(ch, tk.Canvas):
                            ch.configure(bg="#161a1e")


    def _on_group_drag_start(self, gid):
        if gid == DEFAULT_GROUP_ID:
            self._drag_group_id = None
            return
        self._drag_group_id = gid

    def _group_widget_at_y(self, y_root):

        for widget, gid in self._sidebar_group_widgets:
            try:
                y1 = widget.winfo_rooty()
                y2 = y1 + widget.winfo_height()
                if y1 <= y_root <= y2:
                    return widget, gid
            except Exception:
                continue
        return None, None

    def _on_group_drag_motion(self, e):
        if not self._drag_group_id:
            return

        e.widget.configure(cursor="fleur")

    def _on_group_drag_end(self, e):
        if not self._drag_group_id:
            return
        target_widget, target_gid = self._group_widget_at_y(e.y_root)
        if target_gid and target_gid != self._drag_group_id:

            ordered = sort_groups_for_sidebar(self.groups)
            ids = [g["id"] for g in ordered if g["id"] != DEFAULT_GROUP_ID]
            try:
                from_idx = ids.index(self._drag_group_id)
                to_idx = ids.index(target_gid)
            except ValueError:
                self._drag_group_id = None
                return
            gid_list = ids
            item = gid_list.pop(from_idx)
            gid_list.insert(to_idx, item)

            self.groups[DEFAULT_GROUP_ID]["order"] = 0
            for i, gid in enumerate(gid_list, start=1):
                self.groups[gid]["order"] = i
            self.save_all()
            self._build_sidebar()
        self._drag_group_id = None
        try:
            e.widget.configure(cursor="")
        except Exception:
            pass

    def _refresh_groups_listbox(self):
        self.groups_listbox.delete(0, tk.END)
        for g in sort_groups_for_sidebar(self.groups):

            prefix = "📁 " if g.get("auto_created", False) else ""
            self.groups_listbox.insert(tk.END, f'{prefix}{g["name"]}')

    def _group_id_from_listbox_index(self, idx):
        ordered = sort_groups_for_sidebar(self.groups)
        if 0 <= idx < len(ordered):
            return ordered[idx]["id"]
        return DEFAULT_GROUP_ID

    def _create_group(self, name, icon=None):
        if not name:
            messagebox.showwarning("Erreur", "Le nom du groupe est obligatoire.")
            return

        base_id = name.lower().strip().replace(" ", "_")
        gid = base_id
        i = 1
        while gid in self.groups:
            i += 1
            gid = f"{base_id}_{i}"

        existing = [g for g in self.groups.values() if g["id"] != DEFAULT_GROUP_ID]
        next_order = (max([g.get("order", 0) for g in existing]) + 1) if existing else 1
        self.groups[gid] = {"id": gid, "name": name, "icon": icon or None, "order": next_order}
        self.save_all()
        self._refresh_groups_listbox()
        try:
            self._build_sidebar()
        except Exception:
            pass
        self.update_app_grid()

    def _rename_selected_group(self, name_entry):
        sel = self.groups_listbox.curselection()
        if not sel:
            return
        gid = self._group_id_from_listbox_index(sel[0])
        if gid == DEFAULT_GROUP_ID:
            messagebox.showinfo("Info", "Le groupe par défaut ne peut pas être renommé.")
            return
        new_name = name_entry.get().strip()
        if not new_name:
            return
        self.groups[gid]["name"] = new_name
        self.save_all()
        self._refresh_groups_listbox()
        try:
            self._build_sidebar()
        except Exception:
            pass
        self.update_app_grid()

    def _update_selected_group(self, icon):
        sel = self.groups_listbox.curselection()
        if not sel:
            return
        gid = self._group_id_from_listbox_index(sel[0])
        if icon is not None:
            self.groups[gid]["icon"] = icon or None
        self.save_all()
        self._refresh_groups_listbox()
        try:
            self._build_sidebar()
        except Exception:
            pass
        self.update_app_grid()

    def modify_group_order(self, group_id):
        if group_id == DEFAULT_GROUP_ID:
            return
            
        dialog = tk.Toplevel(self.root)
        dialog.geometry("400x250")
        self.setup_window(dialog, "Modifier l'ordre")
        
        main_frame = tk.Frame(dialog, bg="#1e2124")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        tk.Label(main_frame, text=f"Modifier l'ordre de", 
                font=("Arial", 12, "bold"), fg="white", bg="#1e2124").pack(pady=5)
        tk.Label(main_frame, text=self.groups[group_id]["name"],
                font=("Arial", 10), fg="#4a90e2", bg="#1e2124").pack()
        
        # Obtenir la liste des groupes triés (sauf le groupe par défaut)
        ordered_groups = sort_groups_for_sidebar(self.groups)
        groups_list = [g for g in ordered_groups if g["id"] != DEFAULT_GROUP_ID]
        current_pos = next(i for i, g in enumerate(groups_list) if g["id"] == group_id)
        
        # Frame pour le spinbox
        order_frame = tk.Frame(main_frame, bg="#1e2124")
        order_frame.pack(pady=20)
        
        tk.Label(order_frame, text="Position :", fg="white", bg="#1e2124").pack(side="left", padx=(0, 10))
        order_var = tk.StringVar(value=str(current_pos + 1))
        order_spin = tk.Spinbox(order_frame, from_=1, to=len(groups_list), 
                               textvariable=order_var, width=5,
                               bg="#2e3440", fg="white", buttonbackground="#2e3440",
                               relief="flat", highlightthickness=1,
                               highlightbackground="#3a4250", insertbackground="white")
        order_spin.pack(side="left")
        
        buttons_frame = tk.Frame(main_frame, bg="#1e2124")
        buttons_frame.pack(side="bottom", pady=20)
        
        def apply_order():
            try:
                new_pos = int(order_var.get()) - 1
                if 0 <= new_pos < len(groups_list):
                    # Déplacer le groupe à la nouvelle position
                    groups_list.insert(new_pos, groups_list.pop(current_pos))
                    
                    # Mettre à jour les ordres
                    self.groups[DEFAULT_GROUP_ID]["order"] = 0
                    for i, g in enumerate(groups_list, start=1):
                        self.groups[g["id"]]["order"] = i
                    
                    self.save_all()
                    self._build_sidebar()
                dialog.destroy()
            except ValueError:
                messagebox.showerror("Erreur", "Veuillez entrer un nombre valide")
        
        cancel_btn = RoundedButton(buttons_frame, width=140, height=32, cornerradius=8,
                                 bg="#2e3440", fg="white", text="Annuler",
                                 command=dialog.destroy)
        cancel_btn.pack(side="left", padx=10)
        
        apply_btn = RoundedButton(buttons_frame, width=140, height=32, cornerradius=8,
                                bg="#4a90e2", fg="white", text="Appliquer",
                                command=apply_order)
        apply_btn.pack(side="left", padx=10)

    def _update_group_contextual(self, group_id):
        if group_id == DEFAULT_GROUP_ID:
            return
            
        dialog = tk.Toplevel(self.root)
        dialog.geometry("600x300")
        self.setup_window(dialog, "Modifier le groupe")
        
        main_frame = tk.Frame(dialog, bg="#1e2124")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        tk.Label(main_frame, text="Modifier le groupe", 
                font=("Arial", 12, "bold"), fg="white", bg="#1e2124").pack(pady=5)
                
        # Frame pour le nom
        name_frame = tk.Frame(main_frame, bg="#1e2124")
        name_frame.pack(fill="x", pady=10)
        
        tk.Label(name_frame, text="Nom du groupe", bg="#1e2124", fg="white", 
                font=("Arial", 10, "bold")).pack(anchor="w", pady=(0, 8))
        
        name_entry = tk.Entry(name_frame, font=("Arial", 11),
                            bg="#2e3440", fg="white", relief="flat",
                            insertbackground="white", width=30,
                            highlightthickness=1, highlightbackground="#3a4250")
        name_entry.insert(0, self.groups[group_id]["name"])
        name_entry.pack(ipady=5)
        
        # Frame pour l'icône
        icon_frame = tk.Frame(main_frame, bg="#1e2124")
        icon_frame.pack(fill="x", pady=10)
        
        tk.Label(icon_frame, text="Icône (optionnel)", bg="#1e2124", fg="white",
                font=("Arial", 10, "bold")).pack(anchor="w", pady=(0, 8))
        
        icon_entry = tk.Entry(icon_frame, font=("Arial", 11),
                            bg="#2e3440", fg="white", relief="flat",
                            insertbackground="white",
                            highlightthickness=1, highlightbackground="#3a4250")
        icon_entry.insert(0, self.groups[group_id].get("icon", ""))
        icon_entry.pack(fill="x", ipady=5)
        
        # Boutons pour l'icône
        icon_buttons = tk.Frame(icon_frame, bg="#1e2124")
        icon_buttons.pack(anchor="w", pady=(10, 0))
        
        browse_icon_btn = RoundedButton(icon_buttons, width=150, height=32, cornerradius=8,
                                      bg="#2e3440", fg="white", text="📁 Parcourir",
                                      command=lambda: icon_entry.delete(0, tk.END) or icon_entry.insert(0, filedialog.askopenfilename(
                                          filetypes=[("Images", "*.png *.jpg *.jpeg *.gif *.ico")])))
        browse_icon_btn.pack(side="left", padx=(0, 10))
        
        xclient_icon_btn = RoundedButton(icon_buttons, width=180, height=32, cornerradius=8,
                                       bg="#4a90e2", fg="white", text="🎨 Icônes XClient",
                                       command=lambda: self.open_icon_picker(icon_entry))
        xclient_icon_btn.pack(side="left")
        
        # Boutons d'action
        buttons_frame = tk.Frame(main_frame, bg="#1e2124")
        buttons_frame.pack(side="bottom", pady=20)
        
        def apply_changes():
            new_name = name_entry.get().strip()
            new_icon = icon_entry.get().strip()
            
            if not new_name:
                messagebox.showwarning("Erreur", "Le nom du groupe ne peut pas être vide")
                return
                
            self.groups[group_id]["name"] = new_name
            self.groups[group_id]["icon"] = new_icon if new_icon else None
            
            self.save_all()
            self._build_sidebar()
            dialog.destroy()
        
        cancel_btn = RoundedButton(buttons_frame, width=140, height=32, cornerradius=8,
                                 bg="#2e3440", fg="white", text="Annuler",
                                 command=dialog.destroy)
        cancel_btn.pack(side="left", padx=10)
        
        apply_btn = RoundedButton(buttons_frame, width=140, height=32, cornerradius=8,
                                bg="#4a90e2", fg="white", text="Appliquer",
                                command=apply_changes)
        apply_btn.pack(side="left", padx=10)

    def _delete_group(self, group_id):
        """Version du menu contextuel de la suppression de groupe"""
        if group_id == DEFAULT_GROUP_ID:
            messagebox.showinfo("Info", "Le groupe par défaut ne peut pas être supprimé.")
            return
        
        apps_count = len([a for a in self.applications if a.get("group_id", DEFAULT_GROUP_ID) == group_id])
        
        dialog = tk.Toplevel(self.root)
        dialog.geometry("550x380")
        self.setup_window(dialog, "Supprimer le groupe")
        
        result = {"confirmed": False, "dest_id": DEFAULT_GROUP_ID}
        
        header_frame = tk.Frame(dialog, bg="#1e2124")
        header_frame.pack(fill="x", padx=30, pady=(25, 15))
        
        icon_label = tk.Label(header_frame, text="🗑️", font=("Arial", 32),
                             bg="#1e2124", fg="#ff4444")
        icon_label.pack(side="left", padx=(0, 15))
        
        title_label = tk.Label(header_frame, 
                              text=f"Supprimer le groupe\n\"{self.groups[group_id]['name']}\"",
                              bg="#1e2124", fg="white", font=("Arial", 13, "bold"),
                              justify="left")
        title_label.pack(side="left", anchor="w")
        
        info_frame = tk.Frame(dialog, bg="#2e3440")
        info_frame.pack(fill="x", padx=30, pady=(0, 20))
        
        if apps_count > 0:
            info_text = f"Ce groupe contient {apps_count} application(s).\nVeuillez choisir où les déplacer avant de supprimer le groupe."
            info_icon = "📦"
        else:
            info_text = "Ce groupe est vide.\nVous pouvez le supprimer sans déplacer d'applications."
            info_icon = "✓"
        
        info_header = tk.Frame(info_frame, bg="#2e3440")
        info_header.pack(fill="x", padx=15, pady=(12, 8))
        
        tk.Label(info_header, text=info_icon, bg="#2e3440", fg="white",
                font=("Arial", 16)).pack(side="left", padx=(0, 10))
        
        tk.Label(info_header, text=info_text, bg="#2e3440", fg="white",
                font=("Arial", 10), justify="left").pack(side="left", anchor="w")

        if apps_count > 0:
            dest_frame = tk.Frame(dialog, bg="#1e2124")
            dest_frame.pack(fill="x", padx=30, pady=(10, 20))
            
            tk.Label(dest_frame, text="Groupe de destination", bg="#1e2124", fg="white",
                    font=("Arial", 10, "bold")).pack(anchor="w", pady=(0, 8))
            
            available_groups = [g["name"] for g in self.groups.values() if g["id"] != group_id]
            
            dest_var = tk.StringVar(value=self.groups[DEFAULT_GROUP_ID]["name"])
            dest_combo = ttk.Combobox(dest_frame, textvariable=dest_var, state="readonly",
                                     values=available_groups, font=("Arial", 11), height=10)
            dest_combo.pack(fill="x", ipady=8)
            
            def update_dest(*args):
                dest_name = dest_var.get()
                result["dest_id"] = self._group_id_by_name(dest_name) or DEFAULT_GROUP_ID
            
            dest_var.trace('w', update_dest)
            update_dest()
        
        buttons_frame = tk.Frame(dialog, bg="#1e2124")
        buttons_frame.pack(fill="x", padx=30, pady=(10, 25))
        
        def on_cancel():
            result["confirmed"] = False
            dialog.destroy()
        
        def on_confirm():
            result["confirmed"] = True
            dialog.destroy()
        
        cancel_btn = RoundedButton(buttons_frame, width=200, height=38, cornerradius=8,
                                   bg="#2e3440", fg="white", text="Annuler",
                                   command=on_cancel)
        cancel_btn.pack(side="left", padx=(0, 10))
        
        confirm_btn = RoundedButton(buttons_frame, width=200, height=38, cornerradius=8,
                                    bg="#ff4444", fg="white", text="Supprimer le groupe",
                                    command=on_confirm)
        confirm_btn.pack(side="right")
        
        dialog.wait_window()
        
        if result["confirmed"]:
            dest_id = result["dest_id"]
            
            # Déplacer les applications du groupe supprimé
            for app in self.applications:
                if app.get("group_id", DEFAULT_GROUP_ID) == group_id:
                    app["group_id"] = dest_id
            
            # Supprimer le groupe
            del self.groups[group_id]
            if self.active_group_filter == group_id:
                self.active_group_filter = DEFAULT_GROUP_ID
            
            self.save_all()
            self._refresh_groups_listbox()
            self._build_sidebar()
            self.update_app_grid()

    def _delete_selected_group(self):
        sel = self.groups_listbox.curselection()
        if not sel:
            return
        gid = self._group_id_from_listbox_index(sel[0])
        if gid == DEFAULT_GROUP_ID:
            messagebox.showinfo("Info", "Le groupe par défaut ne peut pas être supprimé.")
            return
        

        dialog = tk.Toplevel(self.root)
        dialog.geometry("550x380")
        self.setup_window(dialog, "Supprimer le groupe")
        

        result = {"confirmed": False, "dest_id": DEFAULT_GROUP_ID}
        

        header_frame = tk.Frame(dialog, bg="#1e2124")
        header_frame.pack(fill="x", padx=30, pady=(25, 15))
        
        icon_label = tk.Label(header_frame, text="🗑️", font=("Arial", 32),
                             bg="#1e2124", fg="#ff4444")
        icon_label.pack(side="left", padx=(0, 15))
        
        title_label = tk.Label(header_frame, 
                              text=f"Supprimer le groupe\n\"{self.groups[gid]['name']}\"",
                              bg="#1e2124", fg="white", font=("Arial", 13, "bold"),
                              justify="left")
        title_label.pack(side="left", anchor="w")
        

        info_frame = tk.Frame(dialog, bg="#2e3440")
        info_frame.pack(fill="x", padx=30, pady=(0, 20))
        

        apps_count = len([a for a in self.applications if a.get("group_id", DEFAULT_GROUP_ID) == gid])
        
        if apps_count > 0:
            info_text = f"Ce groupe contient {apps_count} application(s).\nVeuillez choisir où les déplacer avant de supprimer le groupe."
            info_icon = "📦"
        else:
            info_text = "Ce groupe est vide.\nVous pouvez le supprimer sans déplacer d'applications."
            info_icon = "✓"
        
        info_header = tk.Frame(info_frame, bg="#2e3440")
        info_header.pack(fill="x", padx=15, pady=(12, 8))
        
        tk.Label(info_header, text=info_icon, bg="#2e3440", fg="white",
                font=("Arial", 16)).pack(side="left", padx=(0, 10))
        
        tk.Label(info_header, text=info_text, bg="#2e3440", fg="white",
                font=("Arial", 10), justify="left").pack(side="left", anchor="w")
        

        if apps_count > 0:
            dest_frame = tk.Frame(dialog, bg="#1e2124")
            dest_frame.pack(fill="x", padx=30, pady=(10, 20))
            
            tk.Label(dest_frame, text="Groupe de destination", bg="#1e2124", fg="white",
                    font=("Arial", 10, "bold")).pack(anchor="w", pady=(0, 8))
            

            available_groups = [g["name"] for g in self.groups.values() if g["id"] != gid]
            
            dest_var = tk.StringVar(value=self.groups[DEFAULT_GROUP_ID]["name"])
            dest_combo = ttk.Combobox(dest_frame, textvariable=dest_var, state="readonly",
                                     values=available_groups, font=("Arial", 11), height=10)
            dest_combo.pack(fill="x", ipady=8)
            

            def update_dest(*args):
                dest_name = dest_var.get()
                result["dest_id"] = self._group_id_by_name(dest_name) or DEFAULT_GROUP_ID
            
            dest_var.trace('w', update_dest)
            update_dest()
        

        buttons_frame = tk.Frame(dialog, bg="#1e2124")
        buttons_frame.pack(fill="x", padx=30, pady=(10, 25))
        
        def on_cancel():
            result["confirmed"] = False
            dialog.destroy()
        
        def on_confirm():
            result["confirmed"] = True
            dialog.destroy()
        
        cancel_btn = RoundedButton(buttons_frame, width=200, height=38, cornerradius=8,
                                   bg="#2e3440", fg="white", text="Annuler",
                                   command=on_cancel)
        cancel_btn.pack(side="left", padx=(0, 10))
        
        confirm_btn = RoundedButton(buttons_frame, width=200, height=38, cornerradius=8,
                                    bg="#ff4444", fg="white", text="Supprimer le groupe",
                                    command=on_confirm)
        confirm_btn.pack(side="right")
        

        dialog.wait_window()
        

        if result["confirmed"]:
            dest_id = result["dest_id"]
            

            for app in self.applications:
                if app.get("group_id", DEFAULT_GROUP_ID) == gid:
                    app["group_id"] = dest_id
            

            del self.groups[gid]
            if self.active_group_filter == gid:
                self.active_group_filter = DEFAULT_GROUP_ID
            
            self.save_all()
            self._refresh_groups_listbox()
            try:
                self._build_sidebar()
            except Exception:
                pass
            self.update_app_grid()


    def _on_drag_start(self, app_index):
        self._drag_app_index = app_index

    def _on_drag_motion(self):
        pass

    def _on_drag_end(self):
        self._drag_app_index = None


    def _card_widget_under_pointer(self, container):

        x, y = self.root.winfo_pointerx(), self.root.winfo_pointery()
        for idx, child in enumerate(container.winfo_children()):
            try:
                y1 = child.winfo_rooty()
                y2 = y1 + child.winfo_height()
                x1 = child.winfo_rootx()
                x2 = x1 + child.winfo_width()
                if x1 <= x <= x2 and y1 <= y <= y2:
                    return idx
            except Exception:
                continue
        return None

    def _recompute_orders_for_group(self, grp_id, container):

        current_apps = sort_apps_for_group(self.applications, grp_id)
        ids_in_group = [self.applications.index(a) for a in current_apps]

        visual_indices = list(range(len(container.winfo_children())))

        app_indices = ids_in_group[:]

        for order_value, global_idx in enumerate(app_indices):
            self.applications[global_idx]["order"] = order_value

    def _on_drag_motion_app(self, e, container, grp_id):
        if self._drag_app_index is None:
            return
        e.widget.configure(cursor="fleur")

    def _on_drag_end_app(self, e, container, grp_id):
        if self._drag_app_index is None:
            return
        target_pos = self._card_widget_under_pointer(container)

        apps = sort_apps_for_group(self.applications, grp_id)
        if target_pos is None or target_pos >= len(apps):
            target_pos = len(apps) - 1 if apps else 0
        dragged_app = self.applications[self._drag_app_index]

        if dragged_app.get("group_id", DEFAULT_GROUP_ID) != grp_id:
            self._drag_app_index = None
            return

        ids = [self.applications.index(a) for a in apps]
        try:
            from_idx = ids.index(self._drag_app_index)
        except ValueError:
            self._drag_app_index = None
            return
        to_idx = target_pos
        item = ids.pop(from_idx)
        ids.insert(to_idx, item)

        for i, global_idx in enumerate(ids):
            self.applications[global_idx]["order"] = i
        self._drag_app_index = None
        self.save_all()
        self.update_app_grid()
        try:
            e.widget.configure(cursor="")
        except Exception:
            pass

    def _on_group_drop_enter(self, zone):
        zone.configure(bg="#1a1e22")

    def _on_group_drop_leave(self, zone):
        zone.configure(bg="#1e2124")

    def _on_group_drop(self, zone):
        if self._drag_app_index is None:
            return
        self.applications[self._drag_app_index]["group_id"] = zone.group_id
        self._drag_app_index = None
        self.save_all()
        self.update_app_grid()

    def create_system_tray_icon(self):
        icon_image = Image.open('icon/icon.ico')
        icon_image = icon_image.resize((32, 32))
        icon_photo = ImageTk.PhotoImage(icon_image)

        menu = Menu(MenuItem("Quitter", self.quit_app))

        self.system_tray_icon = Icon("XClient", icon_photo, menu=menu)

        threading.Thread(target=self.system_tray_icon.run, daemon=True).start()

    def quit_app(self):

        self.activity_tracker.stop_tracking()

        if hasattr(self, 'goals_manager'):
            self.goals_manager.save_goals()
        self.system_tray_icon.stop()
        self.root.quit()

    def on_frame_configure(self, event=None):

        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def on_canvas_configure(self, event):

        width = event.width
        self.canvas.itemconfig(self.canvas_frame, width=width)

    def on_mousewheel(self, event):

        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def _periodic_status_check(self):
        
        if hasattr(self, 'activity_tracker'):
            self.activity_tracker.print_status()

        self.root.after(30000, self._periodic_status_check)
    
    def _periodic_progress_update(self):
        
        if hasattr(self, 'goals_progress_frame'):
            self._update_goals_progress_display()

        self.root.after(30000, self._periodic_progress_update)
    
    def _update_goals_progress_display(self):
        

        for widget in self.goals_progress_frame.winfo_children():
            widget.destroy()
        

        active_goals = {gid: goal for gid, goal in self.goals_manager.goals.items() 
                       if goal.get("enabled", True)}
        
        if not active_goals:
            return
        

        header = tk.Frame(self.goals_progress_frame, bg="#1e2124")
        header.pack(fill="x", pady=(0, 10))
        
        tk.Label(header, text="Objectifs actifs", font=("Arial", 11, "bold"),
                fg="white", bg="#1e2124").pack(side="left")
        

        buttons_frame = tk.Frame(header, bg="#1e2124")
        buttons_frame.pack(side="right")
        
        def toggle_hide_completed():
            self.hide_completed_goals = not self.hide_completed_goals
            self.save_all()
            self._update_goals_progress_display()
        

        hide_icon_name = "eye.png" if self.hide_completed_goals else "eye-off.png"
        hide_icon = self.load_icon(hide_icon_name, size=(16, 16))
        hide_bg = "#2e3440" if self.hide_completed_goals else "#2a2f38"
        hide_tooltip = "Afficher les objectifs atteints" if self.hide_completed_goals else "Masquer les objectifs atteints"
        
        if hide_icon:
            hide_btn = tk.Label(buttons_frame, image=hide_icon, bg=hide_bg, cursor="hand2",
                               width=28, height=28)
            hide_btn.image = hide_icon
            hide_btn.pack(side="left", padx=(0, 6))
            hide_btn.bind("<Button-1>", lambda e: toggle_hide_completed())
            

            def hide_hover_in(e):
                hide_btn.configure(bg=self._adjust_color(hide_bg, 20))
            def hide_hover_out(e):
                hide_btn.configure(bg=hide_bg)
            hide_btn.bind("<Enter>", hide_hover_in)
            hide_btn.bind("<Leave>", hide_hover_out)
            
            ToolTip(hide_btn, hide_tooltip)
        

        manage_icon = self.load_icon("settings.png", size=(16, 16))
        
        if manage_icon:
            manage_btn = tk.Label(buttons_frame, image=manage_icon, bg="#2a2f38", cursor="hand2",
                                 width=28, height=28)
            manage_btn.image = manage_icon
            manage_btn.pack(side="left")
            manage_btn.bind("<Button-1>", lambda e: self.open_goals_manager())
            

            def manage_hover_in(e):
                manage_btn.configure(bg=self._adjust_color("#2a2f38", 20))
            def manage_hover_out(e):
                manage_btn.configure(bg="#2a2f38")
            manage_btn.bind("<Enter>", manage_hover_in)
            manage_btn.bind("<Leave>", manage_hover_out)
            
            ToolTip(manage_btn, "Gérer les objectifs")
    
    def _adjust_color(self, color, amount):
        
        try:
            rgb = tuple(int(color[i:i+2], 16) for i in (1, 3, 5))
            rgb = tuple(min(255, max(0, x + amount)) for x in rgb)
            return f'#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}'
        except:
            return color
        progress_container = tk.Frame(self.goals_progress_frame, bg="#1e2124")
        progress_container.pack(fill="x")
        

        goals_with_progress = []
        for goal_id, goal in active_goals.items():
            progress = self.goals_manager.get_goal_progress(goal_id)
            if progress:
                goals_with_progress.append((goal_id, goal, progress))
        

        goals_with_progress.sort(key=lambda x: x[2]["percentage"], reverse=True)
        

        all_goals = goals_with_progress[:]
        if self.hide_completed_goals:
            goals_with_progress = [g for g in goals_with_progress if g[2]["percentage"] < 100]
        

        if not goals_with_progress and self.hide_completed_goals and all_goals:

            congrats_frame = tk.Frame(progress_container, bg="#2e3440")
            congrats_frame.pack(fill="x", pady=10, padx=5)
            
            tk.Label(congrats_frame, text="🎉", font=("Arial", 24),
                    bg="#2e3440", fg="white").pack(pady=(10, 5))
            tk.Label(congrats_frame, text="Tous vos objectifs sont atteints !",
                    font=("Arial", 11, "bold"), bg="#2e3440", fg="#4caf50").pack()
            tk.Label(congrats_frame, text=f"{len(all_goals)} objectif(s) terminé(s)",
                    font=("Arial", 9, "italic"), bg="#2e3440", fg="#9aa0a6").pack(pady=(2, 10))
        else:
            for goal_id, goal, progress in goals_with_progress[:3]:
                self._create_goal_progress_widget(progress_container, goal, progress)
            

            indicators = []
            

            hidden_count = len(all_goals) - len(goals_with_progress)
            if hidden_count > 0 and self.hide_completed_goals:
                indicators.append(f"✓ {hidden_count} objectif(s) atteint(s) masqué(s)")
            

            if len(goals_with_progress) > 3:
                indicators.append(f"+ {len(goals_with_progress) - 3} autre(s) objectif(s)")
            

            if indicators:
                for indicator in indicators:
                    more_label = tk.Label(progress_container, 
                                         text=indicator,
                                         fg="#9aa0a6", bg="#1e2124", font=("Arial", 8, "italic"))
                    more_label.pack(anchor="e", pady=(5, 0))    
    def _create_goal_progress_widget(self, parent, goal, progress):
        

        goal_frame = tk.Frame(parent, bg="#2e3440")
        goal_frame.pack(fill="x", pady=5, padx=5)
        

        info_frame = tk.Frame(goal_frame, bg="#2e3440")
        info_frame.pack(fill="x", padx=10, pady=(8, 5))
        

        icon = "⏱️" if goal["goal_type"] == "max_time" else "🎯"
        tk.Label(info_frame, text=icon, bg="#2e3440", fg="white",
                font=("Arial", 12)).pack(side="left", padx=(0, 8))
        

        app_name = goal["app_name"]
        short_name = app_name if len(app_name) <= 25 else app_name[:24] + "…"
        tk.Label(info_frame, text=short_name, bg="#2e3440", fg="white",
                font=("Arial", 10, "bold")).pack(side="left")
        

        current_hours = int(progress["current"] // 3600)
        current_minutes = int((progress["current"] % 3600) // 60)
        limit_hours = int(progress["limit"] // 3600)
        limit_minutes = int((progress["limit"] % 3600) // 60)
        
        current_text = f"{current_hours}h{current_minutes:02d}" if current_hours > 0 else f"{current_minutes}m"
        limit_text = f"{limit_hours}h{limit_minutes:02d}" if limit_hours > 0 else f"{limit_minutes}m"
        
        time_label = tk.Label(info_frame, text=f"{current_text} / {limit_text}",
                             bg="#2e3440", fg="#9aa0a6", font=("Arial", 9))
        time_label.pack(side="right")
        

        is_pinned = goal.get("pinned", False)
        pin_icon_name = "pin.png" if is_pinned else "pin-off.png"
        pin_icon = self.load_icon(pin_icon_name, size=(16, 16))
        pin_tooltip = "Désépingler" if is_pinned else "Épingler sur la page d'accueil"
        
        def toggle_pin():
            self.goals_manager.toggle_pin_goal(goal_id)
            self._update_goals_progress_display()
        
        if pin_icon:
            pin_btn = tk.Label(info_frame, image=pin_icon, bg="#2e3440", cursor="hand2")
            pin_btn.image = pin_icon
            pin_btn.pack(side="right", padx=(8, 0))
            pin_btn.bind("<Button-1>", lambda e: toggle_pin())
            ToolTip(pin_btn, pin_tooltip)
            

            def on_pin_hover(e):
                pin_btn.configure(bg="#3a4250")
            def on_pin_leave(e):
                pin_btn.configure(bg="#2e3440")
            pin_btn.bind("<Enter>", on_pin_hover)
            pin_btn.bind("<Leave>", on_pin_leave)        

        bar_frame = tk.Frame(goal_frame, bg="#2e3440")
        bar_frame.pack(fill="x", padx=10, pady=(0, 8))
        
        bar_container = tk.Frame(bar_frame, bg="#1a1e22", height=22)
        bar_container.pack(fill="x")
        bar_container.pack_propagate(False)
        

        percentage = progress["percentage"]
        if goal["goal_type"] == "max_time":
            if percentage >= 100:
                bar_color = "#ff4444"
                status_text = "Dépassé !"
            elif percentage >= 80:
                bar_color = "#ff9800"
                status_text = "Attention"
            else:
                bar_color = "#4caf50"
                status_text = "OK"
        else:
            if percentage >= 100:
                bar_color = "#4caf50"
                status_text = "Atteint !"
            else:
                bar_color = "#4a90e2"
                status_text = "En cours"
        

        progress_bar = tk.Frame(bar_container, bg=bar_color, height=22)
        progress_bar.place(relwidth=min(percentage / 100, 1.0), relheight=1.0)
        

        label_text = f"{percentage:.0f}% - {status_text}"
        tk.Label(bar_container, text=label_text, bg="#1a1e22", fg="white",
                font=("Arial", 9, "bold")).place(relx=0.5, rely=0.5, anchor="center")
    
    def _periodic_goals_check(self):
        
        if hasattr(self, 'goals_manager'):
            alerts = self.goals_manager.check_goals()
            for alert in alerts:

                self._show_goal_popup(alert)

                self._show_windows_notification(alert["message"], alert["type"])
            

            if hasattr(self, 'goals_progress_frame'):
                self._update_goals_progress_display()
        

        self.root.after(300000, self._periodic_goals_check)
    
    def _show_windows_notification(self, message, alert_type="info"):
        
        try:

            if hasattr(self, 'system_tray_icon') and self.system_tray_icon:

                if alert_type == "limit_exceeded":
                    title = "⚠️ XClient - Limite dépassée"
                elif alert_type == "approaching_limit":
                    title = "⚡ XClient - Attention"
                elif alert_type == "goal_achieved":
                    title = "✅ XClient - Objectif atteint"
                else:
                    title = "XClient - Notification"
                

                self.system_tray_icon.notify(title, message)
        except Exception as e:
            print(f"Erreur lors de l'affichage de la notification : {e}")
    
    def _show_goal_popup(self, alert):
        
        popup = tk.Toplevel(self.root)
        popup.overrideredirect(True)
        popup.attributes('-topmost', True)
        

        popup_width = 420
        popup_height = 200
        screen_width = popup.winfo_screenwidth()
        screen_height = popup.winfo_screenheight()
        x = screen_width - popup_width - 20
        y = screen_height - popup_height - 60
        popup.geometry(f"{popup_width}x{popup_height}+{x}+{y}")
        

        if alert["type"] == "limit_exceeded":
            bg_color = "#ff4444"
            icon = "⚠️"
            title_text = "Limite dépassée !"
        elif alert["type"] == "approaching_limit":
            bg_color = "#ff9800"
            icon = "⚡"
            title_text = "Attention !"
        elif alert["type"] == "goal_achieved":
            bg_color = "#4caf50"
            icon = "✅"
            title_text = "Objectif atteint !"
        else:
            bg_color = "#4a90e2"
            icon = "ℹ️"
            title_text = "Notification"
        

        main_frame = tk.Frame(popup, bg=bg_color)
        main_frame.pack(fill="both", expand=True)
        

        header = tk.Frame(main_frame, bg=bg_color)
        header.pack(fill="x", padx=20, pady=(15, 10))
        
        tk.Label(header, text=icon, font=("Arial", 32), bg=bg_color, fg="white").pack(side="left", padx=(0, 15))
        tk.Label(header, text=title_text, font=("Arial", 16, "bold"), bg=bg_color, fg="white").pack(side="left")
        

        message_frame = tk.Frame(main_frame, bg=bg_color)
        message_frame.pack(fill="x", padx=20, pady=10)
        
        tk.Label(message_frame, text=alert["app_name"], 
                font=("Arial", 13, "bold"), bg=bg_color, fg="white").pack(anchor="w")
        

        if alert["type"] in ["limit_exceeded", "approaching_limit"]:
            hours_current = int(alert["current_time"] // 3600)
            minutes_current = int((alert["current_time"] % 3600) // 60)
            hours_limit = int(alert["limit_value"] // 3600)
            minutes_limit = int((alert["limit_value"] % 3600) // 60)
            
            time_current = f"{hours_current}h {minutes_current}m" if hours_current > 0 else f"{minutes_current}m"
            time_limit = f"{hours_limit}h {minutes_limit}m" if hours_limit > 0 else f"{minutes_limit}m"
            
            tk.Label(message_frame, text=f"Temps utilisé: {time_current} / {time_limit}", 
                    font=("Arial", 10), bg=bg_color, fg="white").pack(anchor="w", pady=(5, 5))
            

            progress_container = tk.Frame(message_frame, bg="#ffffff", height=20)
            progress_container.pack(fill="x", pady=(5, 0))
            progress_container.pack_propagate(False)
            
            percentage = min(alert["percentage"], 100)
            progress_bar = tk.Frame(progress_container, bg="#1e2124", height=20)
            progress_bar.place(relwidth=percentage/100, relheight=1.0)
            
            tk.Label(progress_container, text=f"{percentage:.0f}%", 
                    bg="#ffffff", fg="#1e2124", font=("Arial", 9, "bold")).place(relx=0.5, rely=0.5, anchor="center")
        
        elif alert["type"] == "goal_achieved":
            hours = int(alert["current_time"] // 3600)
            minutes = int((alert["current_time"] % 3600) // 60)
            time_str = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
            
            tk.Label(message_frame, text=f"Temps utilisé: {time_str}", 
                    font=("Arial", 11), bg=bg_color, fg="white").pack(anchor="w", pady=(5, 0))
            tk.Label(message_frame, text="Félicitations ! Continuez comme ça ! 🎉", 
                    font=("Arial", 9, "italic"), bg=bg_color, fg="white").pack(anchor="w", pady=(5, 0))
        

        buttons_frame = tk.Frame(main_frame, bg=bg_color)
        buttons_frame.pack(fill="x", padx=20, pady=(10, 15))
        
        close_btn = tk.Button(buttons_frame, text="OK", bg="white", fg=bg_color,
                             font=("Arial", 10, "bold"), relief="flat", cursor="hand2",
                             command=popup.destroy, width=12)
        close_btn.pack(side="right")
        apply_hover_to_button(close_btn, base_bg="white", hover_delta=-20, active_delta=-40)
        
        details_btn = tk.Button(buttons_frame, text="Voir détails", bg="white", fg=bg_color,
                               font=("Arial", 10), relief="flat", cursor="hand2",
                               command=lambda: [popup.destroy(), self.open_goals_manager()], width=12)
        details_btn.pack(side="right", padx=(0, 10))
        apply_hover_to_button(details_btn, base_bg="white", hover_delta=-20, active_delta=-40)
        

        popup.attributes('-alpha', 0.0)
        self._animate_popup_in(popup)
        

        popup.after(10000, lambda: self._animate_popup_out(popup))
    
    def _animate_popup_in(self, popup):
        
        alpha = popup.attributes('-alpha')
        if alpha < 1.0:
            popup.attributes('-alpha', alpha + 0.1)
            popup.after(30, lambda: self._animate_popup_in(popup))
    
    def _animate_popup_out(self, popup):
        
        try:
            alpha = popup.attributes('-alpha')
            if alpha > 0.0:
                popup.attributes('-alpha', alpha - 0.1)
                popup.after(30, lambda: self._animate_popup_out(popup))
            else:
                popup.destroy()
        except:
            pass
    
    def center_window(self, window):

        window.update_idletasks()
        try:
            geom = window.geometry()
            size_part = geom.split("+")[0]
            width, height = map(int, size_part.split("x"))
        except Exception:
            width = window.winfo_width()
            height = window.winfo_height()
        x = (window.winfo_screenwidth() // 2) - (width // 2)
        y = (window.winfo_screenheight() // 2) - (height // 2)
        window.geometry(f"{width}x{height}+{x}+{y}")

    def _open_path_or_command(self, path):

        try:
            if not path:
                raise ValueError("Chemin vide")
            lower = path.lower()


            if lower.startswith(("http://", "https://")):
                try:
                    import webbrowser
                    webbrowser.open(path)
                    return
                except Exception:
                    pass


            if lower.endswith(".url"):
                try:
                    os.startfile(path)
                    return
                except Exception:

                    subprocess.Popen(["cmd", "/c", "start", "", path], shell=False)
                    return


            executable_exts = (".exe", ".msi", ".bat", ".cmd", ".vbs", ".ps1", ".reg", ".dll", ".appref-ms")
            if lower.endswith(executable_exts):
                creationflags = 0
                if hasattr(subprocess, "CREATE_NO_WINDOW"):
                    creationflags = subprocess.CREATE_NO_WINDOW
                subprocess.Popen(path,
                                 stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL,
                                 stdin=subprocess.DEVNULL,
                                 creationflags=creationflags,
                                 shell=False)
                return


            try:
                os.startfile(path)
                return
            except Exception:
                subprocess.Popen(["cmd", "/c", "start", "", path], shell=False)
        except Exception as e:
            raise

if __name__ == "__main__":
    root = tk.Tk()
    app = XClientApp(root)
    root.mainloop()
