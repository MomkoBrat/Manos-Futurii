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

        self.overlay = Image.open(r'D:\Documents\НОИТ\OutterFrame.png').convert("RGBA").copy()
        self.overlay = np.array(self.overlay, dtype=np.uint8)

        if len(self.overlay.shape) == 2:
            self.overlay = cv2.cvtColor(self.overlay, cv2.COLOR_GRAY2RGBA)

        self.overlay = cv2.resize(self.overlay, (800, 600))
        self.overlay = self.overlay.astype(np.uint8)

        self.label = tk.Label(root)
        self.label.pack(fill="both", expand=True)

        self.instructions_label = tk.Label(root, text="Hold a pose for 5 seconds", fg="white", bg="#232c34",
                                           font=("Arial", 16))
        self.instructions_label.place(x=280, y=90)

        self.start_button = tk.Button(root, text="Start Recording", command=self.start_recording, bg="#789EB1",
                                      fg="white", font=("Arial", 12, "bold"))
        self.start_button.place(x=200, y=535, width=150, height=40)

        self.stop_button = tk.Button(root, text="Stop Recording", command=self.stop_recording, bg="#C41919", fg="white",
                                     font=("Arial", 12, "bold"))
        self.stop_button.place(x=450, y=535, width=150, height=40)
        self.stop_button.config(state="disabled")

        self.close_button = tk.Button(root, text="X", command=self.close, bg="red", fg="white",
                                      font=("Arial", 12, "bold"))
        self.close_button.place(x=745, y=20, width=30, height=30)

        self.is_recording = False
        self.pose_count = 0
        self.start_time = None
        self.pose_duration = 5

        self.save_dir = "screenshots"
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)

        self.enable_dragging()
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
                    self.instructions_label.config(text="Next pose, please.")
                    self.instructions_label.place(x=315, y=90)

                    self.root.after(2000, self.show_next_instruction)

        self.root.after(10, self.update)

    def enable_dragging(self):
        def on_press(event):
            self.offset_x, self.offset_y = event.x, event.y

        def on_drag(event):
            self.offset_x, self.offset_y = event.x, event.y
            self.root.geometry(
                f"+{self.root.winfo_x() + (event.x - self.offset_x)}+{self.root.winfo_y() + (event.y - self.offset_y)}"
            )

        self.root.bind("<ButtonPress-1>", on_press)
        self.root.bind("<B1-Motion>", on_drag)

    def start_recording(self):
        self.is_recording = True
        self.pose_count = 0
        self.instructions_label.config(text="Hold a pose for 5 seconds")
        self.instructions_label.place(x=280, y=90)
        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")

    def stop_recording(self):
        self.is_recording = False
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.instructions_label.config(text="Recording stopped. Poses complete.")
        self.instructions_label.place(x=240, y=90)
        self.pose_count = 0
        self.start_time = None

    def take_screenshot(self, frame):
        screenshot_path = os.path.join(self.save_dir, f"{self.pose_count + 1}.png")
        image_to_save = Image.fromarray(frame)
        image_to_save.save(screenshot_path)
        print(f"Screenshot saved as {screenshot_path}")

    def show_next_instruction(self):
        if self.is_recording:
            self.instructions_label.config(text="Hold a pose for 5 seconds")
            self.instructions_label.place(x=280, y=90)

    def close(self):
        self.cap.release()
        self.root.destroy()


root = tk.Tk()
root.overrideredirect(True)
root.configure(bg="black")
ManosFuturi(root)
root.mainloop()
