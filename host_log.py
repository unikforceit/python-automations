import pyshark
import threading
from tkinter import Tk, Text, Scrollbar, END, VERTICAL

class HTTPRequestCaptureApp:
    def __init__(self):
        # Create the GUI window
        self.root = Tk()
        self.root.title("HTTP Request Capture")
        self.root.geometry("800x600")

        # Create a Text widget to display captured requests
        self.text_area = Text(self.root, wrap="word", font=("Arial", 12))
        self.scrollbar = Scrollbar(self.root, orient=VERTICAL, command=self.text_area.yview)
        self.text_area.configure(yscrollcommand=self.scrollbar.set)

        # Pack the widgets into the window
        self.text_area.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Start capturing network traffic in a separate thread
        self.start_capture()

    def start_capture(self):
        """ Start capturing traffic on a separate thread """
        capture_thread = threading.Thread(target=self.capture_http_requests)
        capture_thread.daemon = True  # Run as a background thread
        capture_thread.start()

    def capture_http_requests(self):
        """ Capture HTTP and HTTPS requests using pyshark """
        # Use your network interface (e.g., 'Ethernet', 'Wi-Fi', etc.)
        # To find the correct interface name, you can run pyshark.LiveCapture().interfaces in Python
        capture = pyshark.LiveCapture(interface='Wi-Fi', display_filter='http || tls')
        
        for packet in capture.sniff_continuously():
            try:
                # Handle HTTP packets
                if 'HTTP' in packet:
                    url = packet.http.host + packet.http.request_uri
                    self.log_url(url)
                # Handle TLS (HTTPS) packets
                elif 'TLS' in packet:
                    sni = packet.tls.handshake_extensions_server_name
                    self.log_url(f"HTTPS request to: {sni}")
            except AttributeError:
                # Skip packets that don't contain the expected attributes
                pass

    def log_url(self, url):
        """ Log the captured URL to the text area in the GUI """
        self.text_area.insert(END, f"{url}\n")
        self.text_area.see(END)

    def run(self):
        """ Run the Tkinter main loop """
        self.root.mainloop()

if __name__ == "__main__":
    app = HTTPRequestCaptureApp()
    app.run()