import tkinter as tk
from ui.dashboard import run_dashboard

def start_system(root):
    root.destroy()
    run_dashboard()

def start_menu():

    root = tk.Tk()

    root.title("AI MULTI-CAMERA MONITORING PLATFORM")

    root.state("zoomed")

    root.configure(bg="#111111")

    title = tk.Label(
        root,
        text="AI MULTI-CAMERA MONITORING PLATFORM",
        font=("Arial", 42, "bold"),
        fg="white",
        bg="#111111"
    )

    title.pack(pady=120)

    subtitle = tk.Label(
        root,
        text="RTSP • HLS • YOLO • Real-Time AI Detection",
        font=("Arial", 18),
        fg="#AAAAAA",
        bg="#111111"
    )

    subtitle.pack()

    start_button = tk.Button(
        root,
        text="START SYSTEM",
        font=("Arial", 20, "bold"),
        bg="#00AA00",
        fg="white",
        padx=40,
        pady=20,
        borderwidth=0,
        command=lambda: start_system(root)
    )

    start_button.pack(pady=80)

    exit_button = tk.Button(
        root,
        text="EXIT",
        font=("Arial", 14),
        bg="#AA0000",
        fg="white",
        padx=20,
        pady=10,
        borderwidth=0,
        command=root.destroy
    )

    exit_button.pack()

    root.mainloop()