import tkinter as tk
from tkinter import messagebox
import subprocess
import os
import signal
import threading
import time
import sys
import psutil

process = None
start_time = None
timer_running = False

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS  # For PyInstaller
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def is_script_running(script_name):
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['cmdline'] and script_name in proc.info['cmdline']:
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return False

def run_script():
    global process, start_time, timer_running
    script_name = "new11.py"

    if is_script_running(script_name):
        messagebox.showinfo("Info", f"{script_name} is already running.")
        return

    if process is None or process.poll() is not None:
        try:
            script_path = resource_path(script_name)

            log_file = os.path.join(os.getcwd(), "gesture_log.txt")
            with open(log_file, "w") as f:
                # Launch the script
                process = subprocess.Popen([sys.executable, script_path], stdout=f, stderr=f)

            status_label.config(text="Gesture Control is running...", fg="#28a745")
            start_button.config(state="disabled")
            stop_button.config(state="normal")
            start_time = time.time()
            timer_running = True
            threading.Thread(target=update_timer, daemon=True).start()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to run script:\n{e}")
    else:
        messagebox.showinfo("Info", "Gesture Control is already running.")

def update_timer():
    while timer_running:
        elapsed = int(time.time() - start_time)
        mins, secs = divmod(elapsed, 60)
        time_label.config(text=f"Running Time: {mins:02d}:{secs:02d}")
        time.sleep(1)

def stop_script():
    global process, timer_running
    if process is not None:
        try:
            process.terminate()
            process.wait(timeout=5)
        except Exception as e:
            messagebox.showerror("Error", f"Error stopping script:\n{e}")
        process = None
        timer_running = False
        status_label.config(text="Gesture Control stopped.", fg="#dc3545")
        time_label.config(text="Running Time: 00:00")
        start_button.config(state="normal")
        stop_button.config(state="disabled")

def on_closing():
    if messagebox.askokcancel("Exit", "Do you really want to exit?"):
        stop_script()
        root.destroy()

# GUI setup
root = tk.Tk()
root.title("Gesture VLC Controller")
root.geometry("500x400")
root.configure(bg="#f5f5f5")
root.protocol("WM_DELETE_WINDOW", on_closing)

label = tk.Label(root, text="Gesture Controlled Media-Player", font=("Helvetica", 16, "bold"), pady=20, bg="#f5f5f5", fg="#333")
label.pack()

start_button = tk.Button(root, text="Start Gesture Control", font=("Helvetica", 14), bg="#4CAF50", fg="white", width=25, height=2, relief="flat", command=run_script)
start_button.pack(pady=15)

stop_button = tk.Button(root, text="STOP", font=("Helvetica", 14), bg="#f44336", fg="white", width=25, height=2, relief="flat", command=stop_script, state="disabled")
stop_button.pack(pady=10)

status_label = tk.Label(root, text="Gesture Control not running.", font=("Helvetica", 12), fg="#dc3545", bg="#f5f5f5")
status_label.pack(pady=5)

time_label = tk.Label(root, text="Running Time: 00:00", font=("Helvetica", 12), fg="#007bff", bg="#f5f5f5")
time_label.pack(pady=10)

footer_label = tk.Label(root, text="Developed by Ankit Gola", font=("Helvetica", 8, "italic"), pady=10, bg="#f5f5f5", fg="#888")
footer_label.place(relx=0.0, rely=1.0, x=10, y=-10, anchor="sw")

root.mainloop()
