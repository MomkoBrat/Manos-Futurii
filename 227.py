import tkinter as tk
import cv2
import numpy as np
from PIL import Image, ImageTk
import time
import os


class ManosFuturi:
    def __init__(self, root):
        self.root = root
        self.root.geometry("800x600")
        self.cap = cv2.VideoCapture(0)

        self.overlay = np.array(
            Image.open(r'Images/OutterFrame.png').convert("RGBA"))
        self.overlay = cv2.resize(self.overlay, (800, 600))

        self.label = tk.Label(root)
        self.label.pack(fill="both", expand=True)

        self.language = "EN"

        self.instructions_label = tk.Label(root, text="Hold a pose for 5 seconds", fg="white", bg="#232c34",
                                           font=("Arial", 16))
        self.instructions_label.place(x=280, y=90)

        #Buttons
        self.start_button = tk.Button(root, text="Start Recording", command=self.start_recording, bg="#789EB1",
                                      fg="white", font=("Arial", 12, "bold"))
        self.start_button.place(x=245, y=535, width=150, height=40)

        self.info_button = tk.Button(root, text="Info", command=self.show_info, bg="#E4A11B", fg="white",
                                     font=("Arial", 12, "bold"))
        self.info_button.place(x=720, y=535, width=50, height=40)

        self.stop_button = tk.Button(root, text="Stop Recording", command=self.stop_recording, bg="#C41919", fg="white",
                                     font=("Arial", 12, "bold"))
        self.stop_button.place(x=405, y=535, width=150, height=40)
        self.stop_button.config(state="disabled")

        self.language_button = tk.Button(root, text="BG", command=self.toggle_language, bg="#4CAF50", fg="white",
                                         font=("Arial", 12, "bold"))
        self.language_button.place(x=660, y=535, width=50, height=40)

        self.close_button = tk.Button(root, text="X", command=self.close, bg="red", fg="white",
                                      font=("Arial", 12, "bold"))
        self.close_button.place(x=745, y=20, width=30, height=30)

        self.is_recording = False
        self.pose_count = 0
        self.start_time = None
        self.pose_duration = 5

        #Screenshots
        self.save_dir = "screenshots"
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)

        self.info_window = None
        self.info_window_open = False
        self.enable_dragging(self.root)
        self.update()

    def update(self):
        ret, frame = self.cap.read()
        if ret:
            frame = cv2.cvtColor(cv2.flip(frame, 1), cv2.COLOR_BGR2RGB)
            frame_resized = cv2.resize(frame, (800, 600))

            overlay_rgb, overlay_alpha = self.overlay[:, :, :3], self.overlay[:, :, 3] / 255.0

            for c in range(3):
                frame_resized[:, :, c] = (
                        overlay_alpha * overlay_rgb[:, :, c] + (1 - overlay_alpha) * frame_resized[:, :, c]
                )

            self.label.imgtk = ImageTk.PhotoImage(image=Image.fromarray(frame_resized))
            self.label.config(image=self.label.imgtk)

            if self.is_recording:
                if self.start_time is None:
                    self.start_time = time.time()

                elapsed_time = time.time() - self.start_time
                if elapsed_time >= self.pose_duration:
                    self.take_screenshot(frame_resized)
                    self.start_time = None
                    self.pose_count += 1
                    self.instructions_label.config(text="Next pose, please." if self.language == "EN" else "Следваща поза, моля.")
                    self.instructions_label.place(x=315, y=90)

                    self.root.after(2000, self.show_next_instruction)

        self.root.after(10, self.update)

    def enable_dragging(self, window):

        def on_press(event):
            window.offset_x, window.offset_y = event.x, event.y

        def on_drag(event):
            window.geometry(
                f"+{window.winfo_x() + (event.x - window.offset_x)}+{window.winfo_y() + (event.y - window.offset_y)}")

        window.bind("<ButtonPress-1>", on_press)
        window.bind("<B1-Motion>", on_drag)

    def start_recording(self):
        self.is_recording = True
        self.pose_count = 0
        self.instructions_label.config(text="Hold a pose for 5 seconds" if self.language == "EN" else "Задръжте позата за 5 секунди")
        self.instructions_label.place(x=280, y=90)
        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")

    def stop_recording(self):
        self.is_recording = False
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.instructions_label.config(text="Recording stopped. Poses complete." if self.language == "EN" else "Записът приключи. Позите за заснети.")
        self.instructions_label.place(x=240, y=90)
        self.pose_count = 0
        self.start_time = None

    def take_screenshot(self, frame):
        ret, raw_frame = self.cap.read()
        if ret:
            raw_frame = cv2.cvtColor(cv2.flip(raw_frame, 1), cv2.COLOR_BGR2RGB)  # Convert color space
            screenshot_path = os.path.join(self.save_dir, f"{self.pose_count + 1}.png")
            image_to_save = Image.fromarray(raw_frame)
            image_to_save.save(screenshot_path)
            print(f"Screenshot saved as {screenshot_path}")

    def show_next_instruction(self):
        if self.is_recording:
            self.instructions_label.config(text="Hold a pose for 5 seconds" if self.language == "EN" else "Задръжте позата за 5 секунди")
            self.instructions_label.place(x=280, y=90)

    def toggle_language(self):
        if self.language == "EN":
            self.language = "BG"
            self.start_button.config(text="Начало")
            self.stop_button.config(text="Край")
            self.info_button.config(text="Инфо")
            self.language_button.config(text="EN")
            self.instructions_label.config(text="Задръжте позата за 5 секунди")
        else:
            self.language = "EN"
            self.start_button.config(text="Start Recording")
            self.stop_button.config(text="Stop Recording")
            self.info_button.config(text="Info")
            self.language_button.config(text="BG")
            self.instructions_label.config(text="Hold a pose for 5 seconds")


        if self.info_window and self.info_window.winfo_exists():
            self.info_window.destroy()
            self.info_window_open = False

    def show_info(self):
        if self.info_window_open:
            return

        self.info_window = tk.Toplevel(self.root)
        self.info_window.geometry("400x300+850+150")
        self.info_window.configure(bg="#41505D")
        self.info_window.overrideredirect(True)

        self.enable_dragging(self.info_window)

        close_button = tk.Button(self.info_window, text="X", command=self.close_info_window, bg="red", fg="white",
                                 font=("Arial", 12, "bold"))
        close_button.place(x=360, y=10, width=30, height=30)

        self.info_window_open = True

        #Instuctions
        if self.language == "EN":
            text_info = (
                " \n"
                "Instructions\n"
                "\n"
                "1. Click 'Start Recording' to begin.\n"
                "2. Hold a clear hand pose on the camera for 5 seconds.\n"
                "3. A screenshot will be taken automatically.\n"
                "4. Repeat for different poses.\n"
                "5. Click 'Stop Recording' to end.\n"
                "\nScreenshots are saved in the 'screenshots' folder.\n"
                " \n"
            )
        elif self.language == "BG":
            text_info = (
                " \n"
                "Инструкции\n\n"
                " \n"
                "1. Натиснете 'Старт', за да започнете.\n"  
                "2. Задръжте ясна поза с ръце за 5 секунди.\n"  
                "3. Снимката ще бъде направена автоматично.\n"  
                "4. Повторете за различни пози.\n"  
                "5. Натиснете 'Стоп', за да приключите.\n"
                "\nСнимките се запазват в папката 'screenshots'."
                " \n"
            )

        label = tk.Label(self.info_window, text=text_info, bg="#1e1e1e", fg="white",
                         font=("Arial", 11), justify="left", wraplength=500)
        label.pack(pady=45, padx=15)

    def close_info_window(self):
        self.info_window.destroy()
        self.info_window_open = False

    def close(self):
        self.cap.release()
        self.root.destroy()


root = tk.Tk()
root.overrideredirect(True)
root.configure(bg="black")
ManosFuturi(root)
root.mainloop()
