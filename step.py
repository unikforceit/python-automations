import time
import tkinter as tk
from tkinter import scrolledtext
from appium import webdriver
from appium.webdriver.common.appiumby import AppiumBy
from appium.options.android import UiAutomator2Options
from selenium.common.exceptions import NoSuchElementException  # Import NoSuchElementException
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

# Function to open the link in Firefox
def open_link(log_box, link):
    try:
        driver = start_driver()
        update_log(log_box, "Status: Opening link")
        driver.execute_script('mobile: shell', {
            'command': 'am', 
            'args': [
                'start',
                '--user', '10',  # Specify the work profile user ID
                '-a', 'android.intent.action.VIEW',  # Intent action for viewing a link
                '-d', link,  # The link to open
                '-n', 'com.android.chrome/com.google.android.apps.chrome.Main'  # Chrome package and activity
            ]
        })
        update_log(log_box, "Status: Link opened")
        driver.quit()
    except Exception as e:
        update_log(log_box, "Status: Failed to open link")

# Function to install the game and handle the download button
def install_game(log_box):
    try:
        driver = start_driver()
        update_log(log_box, "Status: Installing game")
        install_button = driver.find_element(AppiumBy.XPATH, '//android.widget.TextView[@content-desc="Install"]')
        install_button.click()
        time.sleep(10)  # Wait for the download button to appear

        download_button = driver.find_element(AppiumBy.XPATH, '//android.widget.TextView[@content-desc="Download"]')
        download_button.click()
        time.sleep(60)  # Wait for download and installation to complete

        update_log(log_box, "Status: Game installed")
        driver.quit()
    except NoSuchElementException:
        update_log(log_box, "Status: Install/Download button not found")
    except Exception as e:
        update_log(log_box, "Status: Failed to install game")

# Function to play the game
def play_game(log_box):
    try:
        driver = start_driver()
        update_log(log_box, "Status: Playing game")
        play_button = driver.find_element(AppiumBy.XPATH, '//android.widget.TextView[@content-desc="Play"]')
        play_button.click()
        time.sleep(30)  # Play the game for 30 seconds
        update_log(log_box, "Status: Game played")
        driver.quit()
    except NoSuchElementException:
        update_log(log_box, "Status: Play button not found")
    except Exception as e:
        update_log(log_box, "Status: Failed to play game")

# Function to close and uninstall the game from the given user profile using ADB
def close_uninstall_game(log_box, package_name):
    try:
        driver = start_driver()
        update_log(log_box, "Status: Closing and uninstalling game")
        # Uninstall the app specifically from the work profile (user 10)
        driver.execute_script('mobile: shell', {
            'command': 'pm', 
            'args': [
                'uninstall', '--user', '10', package_name
            ]
        })
        update_log(log_box, "Status: Game uninstalled")
        driver.quit()
    except Exception as e:
        update_log(log_box, "Status: Failed to uninstall game")

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

# Function to reset Google Ads ID in the given work profile using ADB
def reset_ads_id(log_box):
    try:
        driver = start_driver()
        update_log(log_box, "Status: Resetting Ads ID")
        
        # Reset Ads ID by clearing the Google Play Services data for the work profile
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
        update_log(log_box, "Status: Failed to reset Ads ID")

# GUI setup with separate buttons for each action
def create_gui():
    root = tk.Tk()
    root.title("App Automation")

    tk.Label(root, text="Enter Tracking Link:").grid(row=0, column=0, padx=10, pady=10)
    link_entry = tk.Entry(root, width=50)
    link_entry.grid(row=0, column=1, padx=10, pady=10)

    log_box = scrolledtext.ScrolledText(root, width=60, height=20)
    log_box.grid(row=1, column=0, columnspan=4, padx=10, pady=10)
    log_box.tag_config('log', foreground="white", font=("Helvetica", 10))

    def open_link_action():
        link = link_entry.get()
        open_link(log_box, link)

    def install_game_action():
        install_game(log_box)

    def play_game_action():
        play_game(log_box)

    def close_uninstall_action():
        package_name = link_entry.get().split('/')[3].split('?')[0]
        close_uninstall_game(log_box, package_name)

    def reset_ads_id_action():
        reset_ads_id(log_box)

    tk.Button(root, text="Open Link", bg="black", fg="white", width=15, height=2, command=open_link_action).grid(row=2, column=0, padx=10, pady=10)
    tk.Button(root, text="Install Game", bg="black", fg="white", width=15, height=2, command=install_game_action).grid(row=2, column=1, padx=10, pady=10)
    tk.Button(root, text="Play Game", bg="white", fg="black", width=15, height=2, command=play_game_action).grid(row=2, column=2, padx=10, pady=10)
    tk.Button(root, text="Close & Uninstall", bg="black", fg="white", width=15, height=2, command=close_uninstall_action).grid(row=3, column=0, padx=10, pady=10)
    tk.Button(root, text="Reset Ads ID", bg="black", fg="white", width=15, height=2, command=reset_ads_id_action).grid(row=3, column=1, padx=10, pady=10)
    tk.Button(root, text="Clear Log", bg="black", fg="white", width=15, height=2, command=lambda: clear_log(log_box)).grid(row=3, column=2, padx=10, pady=10)

    root.mainloop()

if __name__ == '__main__':
    create_gui()
