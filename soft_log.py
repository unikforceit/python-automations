import tkinter as tk
from tkinter import scrolledtext
import subprocess
import threading

class MitmproxyApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Mitmproxy Capture Logs")
        self.root.geometry("800x500")

        # Create a scrolled text box to display the logs
        self.text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=100, height=30, font=("Arial", 10))
        self.text_area.pack(padx=10, pady=10)

        # Start the mitmproxy in a thread
        self.start_mitmproxy()

    def start_mitmproxy(self):
        def run_mitmproxy():
            process = subprocess.Popen(["mitmproxy", "-T"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

            # Capture stdout from the mitmproxy process and update the text area
            for line in iter(process.stdout.readline, ""):
                self.update_text_area(line)
        
        # Run mitmproxy in a separate thread
        threading.Thread(target=run_mitmproxy, daemon=True).start()

    def update_text_area(self, log_line):
        # Insert the log line into the text area and auto-scroll
        self.text_area.insert(tk.END, log_line)
        self.text_area.see(tk.END)


if __name__ == "__main__":
    root = tk.Tk()
    app = MitmproxyApp(root)
    root.mainloop()
