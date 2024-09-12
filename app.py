import time
import tkinter as tk
from tkinter import scrolledtext
from appium import webdriver
from appium.webdriver.common.appiumby import AppiumBy
from appium.options.android import UiAutomator2Options
from selenium.common.exceptions import NoSuchElementException
import threading

# Function to update status log in GUI
def update_log(log_box, message):
    log_box.insert(tk.END, f"{message}\n", "log")
    log_box.yview(tk.END)

# Function to clear the log
def clear_log(log_box):
    log_box.delete('1.0', tk.END)

# Function to initialize the driver
def start_driver():
    capabilities = dict(
        platformName='Android',
        automationName='uiautomator2',
        deviceName='emulator-5554',
        udid='emulator-5554',
        noReset=True,
        userProfile=10  # Work profile user ID 10
    )
    appium_server_url = 'http://localhost:4723'
    capabilities_options = UiAutomator2Options().load_capabilities(capabilities)
    driver = webdriver.Remote(command_executor=appium_server_url, options=capabilities_options)
    return driver

# Function to perform the entire process (open link, install, play, uninstall, reset ads ID)
def start_process(log_box, link, stop_event):
    try:
        driver = start_driver()

        # Open the link directly in Chrome in the work profile
        update_log(log_box, "Status: Opening link in Chrome")
        driver.execute_script('mobile: shell', {
            'command': 'am',
            'args': [
                'start',
                '--user', '10',  # Specify the work profile user ID
                '-a', 'android.intent.action.VIEW',
                '-d', link,
                '-n', 'com.android.chrome/com.google.android.apps.chrome.Main'
            ]
        })
        time.sleep(10)  # Wait for Chrome to load the link
        update_log(log_box, "Status: Link opened in Chrome")

        if stop_event.is_set():
            update_log(log_box, "Process stopped")
            driver.quit()
            return

        # Install the game
        update_log(log_box, "Status: Installing game")
        install_button = driver.find_element(AppiumBy.XPATH, '//android.widget.TextView[@content-desc="Install"]')
        install_button.click()
        time.sleep(10)  # Wait for the download button to appear

        download_button = driver.find_element(AppiumBy.XPATH, '//android.widget.TextView[@content-desc="Download"]')
        download_button.click()
        time.sleep(60)  # Wait for download and installation to complete
        update_log(log_box, "Status: Game installed")

        if stop_event.is_set():
            update_log(log_box, "Process stopped")
            driver.quit()
            return

        # Play the game
        update_log(log_box, "Status: Playing game")
        play_button = driver.find_element(AppiumBy.XPATH, '//android.widget.TextView[@content-desc="Play"]')
        play_button.click()
        time.sleep(30)  # Play the game for 30 seconds
        update_log(log_box, "Status: Game played")

        if stop_event.is_set():
            update_log(log_box, "Process stopped")
            driver.quit()
            return

        # Uninstall the game
        package_name = link.split('/')[3].split('?')[0]
        update_log(log_box, "Status: Uninstalling game")
        driver.execute_script('mobile: shell', {
            'command': 'pm',
            'args': [
                'uninstall', '--user', '10', package_name
            ]
        })
        update_log(log_box, "Status: Game uninstalled")

        if stop_event.is_set():
            update_log(log_box, "Process stopped")
            driver.quit()
            return

        # Close Chrome and Play Store
        update_log(log_box, "Status: Closing Chrome and Play Store")
        driver.execute_script('mobile: shell', {
            'command': 'am',
            'args': [
                'force-stop', '--user', '10', 'com.android.chrome'
            ]
        })
        driver.execute_script('mobile: shell', {
            'command': 'am',
            'args': [
                'force-stop', '--user', '10', 'com.android.vending'
            ]
        })
        update_log(log_box, "Status: Chrome and Play Store closed")

        # Reset Ads ID
        update_log(log_box, "Status: Resetting Ads ID")
        driver.execute_script('mobile: shell', {
            'command': 'pm',
            'args': [
                'clear',
                '--user', '10',
                'com.google.android.gms'
            ]
        })
        update_log(log_box, "Status: Ads ID reset")

        driver.quit()
    except Exception as e:
        update_log(log_box, f"Status: Failed during process - {str(e)}")

# Function to start the process in a separate thread
def start_process_thread(log_box, link, stop_event):
    stop_event.clear()
    process_thread = threading.Thread(target=start_process, args=(log_box, link, stop_event))
    process_thread.start()

# GUI setup with Start, Clear Log, and Stop buttons
def create_gui():
    root = tk.Tk()
    root.title("App Automation")

    tk.Label(root, text="Enter Tracking Link:").grid(row=0, column=0, padx=10, pady=10)
    link_entry = tk.Entry(root, width=50)
    link_entry.grid(row=0, column=1, padx=10, pady=10)

    log_box = scrolledtext.ScrolledText(root, width=60, height=20, bg="black", fg="white")
    log_box.grid(row=1, column=0, columnspan=4, padx=10, pady=10)
    log_box.tag_config('log', foreground="white", font=("Helvetica", 10))

    stop_event = threading.Event()

    start_button = tk.Button(root, text="Start Now", bg="black", fg="white", width=15, height=2, 
                             command=lambda: start_process_thread(log_box, link_entry.get(), stop_event))
    start_button.grid(row=2, column=0, padx=10, pady=10)

    stop_button = tk.Button(root, text="Stop", bg="black", fg="white", width=15, height=2, 
                            command=stop_event.set)
    stop_button.grid(row=2, column=1, padx=10, pady=10)

    clear_button = tk.Button(root, text="Clear Log", bg="black", fg="white", width=15, height=2, 
                             command=lambda: clear_log(log_box))
    clear_button.grid(row=2, column=2, padx=10, pady=10)

    root.mainloop()

if __name__ == '__main__':
    create_gui()
