import time
import streamlit as st
import subprocess
from appium import webdriver
from appium.webdriver.common.appiumby import AppiumBy
from appium.options.android import UiAutomator2Options
from selenium.common.exceptions import NoSuchElementException

# Function to get connected Android devices
def get_connected_devices():
    result = subprocess.run(['adb', 'devices'], capture_output=True, text=True)
    devices = result.stdout.splitlines()
    device_list = [line.split('\t')[0] for line in devices if '\tdevice' in line]
    return device_list

# Function to get user profiles on a device
def get_user_profiles(device_id):
    result = subprocess.run(['adb', '-s', device_id, 'shell', 'pm', 'list', 'users'], capture_output=True, text=True)
    profiles = result.stdout.splitlines()
    user_ids = []
    for line in profiles:
        if 'UserInfo' in line:
            try:
                profile_id = line.split('{')[1].split('}')[0].split(":")[0]
                user_ids.append(int(profile_id))
            except ValueError:
                continue
    return user_ids

# Function to log real-time updates
def update_log(status_log, message):
    status_log.write(f"**Status**: {message}\n")

# Function to start the Appium driver
def start_driver(device_id, user_id, appium_url):
    capabilities = {
        'platformName': 'Android',
        'automationName': 'uiautomator2',
        'deviceName': device_id,
        'udid': device_id,
        'noReset': True,
        'userProfile': user_id
    }

    capabilities_options = UiAutomator2Options().load_capabilities(capabilities)
    driver = webdriver.Remote(command_executor=appium_url, options=capabilities_options)
    return driver

# Function to open the link in Firefox by manually interacting with the address bar
def open_link_in_firefox(driver, link, status_log):
    try:
        # Launch Firefox from Appium using the work profile
        driver.execute_script('mobile: shell', {
            'command': 'am', 
            'args': [
                'start',
                '--user', driver.capabilities['userProfile'], 
                '-n', 'org.mozilla.firefox/org.mozilla.gecko.BrowserApp'
            ]
        })
        update_log(status_log, "Firefox opened successfully in the selected profile")

        time.sleep(5)  # Wait for Firefox to launch

        # Find the Firefox address bar and input the full link
        search_box = driver.find_element(AppiumBy.XPATH, "//android.widget.LinearLayout[@content-desc='Search or enter address']")
        search_box.click()  # Click the search box
        search_input = driver.find_element(AppiumBy.XPATH, "//android.widget.EditText")
        search_input.send_keys(link)
        update_log(status_log, "Entered URL in the Firefox address bar")

        # Send the Enter key to navigate to the link
        driver.press_keycode(66)  # Keycode 66 is the Enter key in Android
        update_log(status_log, "Submitted the URL")

        time.sleep(10)  # Wait for redirection and page load

        # Check if the Play Store page has been opened by looking for the Install button
        install_button = driver.find_element(AppiumBy.XPATH, '//android.widget.TextView[@content-desc="Install"]')
        if install_button.is_displayed():
            update_log(status_log, "Install button found, Play Store opened successfully")
            return "done"
        else:
            return "Failed to open Play Store after redirection"
    except NoSuchElementException:
        return "Install button not found, Play Store may not have opened"
    except Exception as e:
        return f"Failed to open link: {str(e)}"

# Function to install a game from Google Play after redirection
def install_game(driver, link, status_log):
    try:
        # Extract package name from the link
        package_name = link.split('/')[3].split('?')[0]

        # Wait for the Play Store Install button to appear
        time.sleep(2)
        install_button = driver.find_element(AppiumBy.XPATH, '//android.widget.TextView[@content-desc="Install"]')
        install_button.click()
        update_log(status_log, "Install button clicked")

        # Wait for the Play button to appear instead of forcing the download button
        for _ in range(2):  # Check every 5 seconds up to 50 seconds
            try:
                play_button = driver.find_element(AppiumBy.XPATH, '//android.widget.TextView[@content-desc="Play"]')
                if play_button.is_displayed():
                    update_log(status_log, "Play button appeared, installation complete")
                    return "done"
            except NoSuchElementException:
                time.sleep(2)

        update_log(status_log, "Play button not found after install, assuming installation is complete")

        return "done"
    except NoSuchElementException:
        return "Install button not found"
    except Exception as e:
        return f"Failed to install game: {str(e)}"

# Function to play the game
def play_game(driver, status_log, play_duration):
    try:
        play_button = driver.find_element(AppiumBy.XPATH, '//android.widget.TextView[@content-desc="Play"]')
        play_button.click()
        time.sleep(play_duration)  # Play for the specified number of seconds
        return "done"
    except NoSuchElementException:
        return "Play button not found"
    except Exception as e:
        return f"Failed to play game: {e}"

# Function to close all tabs in Firefox and then force stop
def close_uninstall_game(driver, package_name, status_log):
    try:
          # Uninstall the game from the selected work profile
        driver.execute_script('mobile: shell', {
            'command': 'pm',
            'args': ['uninstall', '--user', driver.capabilities['userProfile'], package_name]
        })
        update_log(status_log, f"Game {package_name} uninstalled")
        
        time.sleep(2)

        driver.execute_script('mobile: shell', {
            'command': 'am',
            'args': ['force-stop', '--user', driver.capabilities['userProfile'], 'com.android.vending']
        })
        update_log(status_log, "Status: Play Store closed")
        time.sleep(2)
        
        # Force stop Firefox
        driver.execute_script('mobile: shell', {
            'command': 'am',
            'args': ['force-stop', '--user', driver.capabilities['userProfile'], 'org.mozilla.firefox']
        })
        update_log(status_log, "Force-stopped Firefox")
        
        return "done"
    except Exception as e:
        return f"Failed to uninstall game {package_name}: {e}"

# Function to reset the Ads ID of the selected profile
def reset_ads_id(driver, device_id, user_id, status_log):
    try:
        # Clear Google Play Services data to reset the Ads ID
        driver.execute_script('mobile: shell', {
            'command': 'pm',
            'args': ['clear', '--user', user_id, 'com.google.android.gms']
        })
        update_log(status_log, "Google Play Services data cleared (Ads ID reset)")
        return "done"
    except Exception as e:
        return f"Failed to reset Ads ID: {e}"

# Function to quit Firefox and force stop
def quit_and_clear_firefox(driver, status_log):
    try:
        # Launch Firefox from Appium using the work profile
        driver.execute_script('mobile: shell', {
            'command': 'am', 
            'args': [
                'start',
                '--user', driver.capabilities['userProfile'], 
                '-n', 'org.mozilla.firefox/org.mozilla.gecko.BrowserApp'
            ]
        })
        update_log(status_log, "Firefox opened successfully in the selected profile")

        time.sleep(5)  # Wait for Firefox to launch

        # Click on the 3-dot menu (3 dots in top-right corner)
        three_dots = driver.find_element(AppiumBy.XPATH, "//android.widget.ImageView[@content-desc='Highlighted']")
        three_dots.click()
        update_log(status_log, "Clicked the 3-dot menu")

        time.sleep(2)

        # Click on Quit
        quit_button = driver.find_element(AppiumBy.XPATH, "//android.widget.LinearLayout[@content-desc='Quit']")
        quit_button.click()
        update_log(status_log, "Clicked 'Quit' in Firefox")

        time.sleep(2)

        # Force stop Firefox
        driver.execute_script('mobile: shell', {
            'command': 'am',
            'args': ['force-stop', '--user', driver.capabilities['userProfile'], 'org.mozilla.firefox']
        })
        update_log(status_log, "Force-stopped Firefox after quitting")

        return "done"
    except NoSuchElementException:
        return "Failed to quit Firefox, element not found"
    except Exception as e:
        return f"Failed to quit Firefox: {e}"

# Streamlit UI
def main():
    st.title("AppsFlayer Automation By Rakib")

    # Appium Localhost Input
    appium_url = st.text_input("Enter Appium Server URL", value="http://localhost:4723")

    # Game link input
    link = st.text_input("Enter Tracking Link")

    # Auto-detect game from the link
    package_name = link.split('/')[3].split('?')[0] if link else None
    game_package_list = {
        "Ant Legion": "com.global.antgame",
        "Puzzle and Chaos": "com.global.pnck",
        "Puzzle and Survival": "com.global.ztmslg",
        "Merge Garden": "com.futureplay.mergematch",
        "Fairy Escaps": "com.games.fairyadventure"
    }
    selected_game = next((game for game, pkg in game_package_list.items() if pkg == package_name), None)
    selected_game = st.selectbox("Detected Game", list(game_package_list.keys()), index=list(game_package_list.keys()).index(selected_game) if selected_game else 0)

    # Time adjustments
    sleep_before_link = st.number_input("Time before opening link (seconds)", min_value=1, max_value=60, value=5)
    sleep_before_install = st.number_input("Time before installing game (seconds)", min_value=1, max_value=60, value=10)
    sleep_before_play = st.number_input("Time before playing game (seconds)", min_value=1, max_value=60, value=5)
    sleep_before_uninstall = st.number_input("Time before closing/uninstalling (seconds)", min_value=1, max_value=60, value=5)
    play_duration = st.number_input("Game Play Duration (seconds)", min_value=10, max_value=300, value=30)

    # Status log box at the top to ensure it's initialized
    status_log = st.empty()

    # Detect devices and profiles
    devices = get_connected_devices()
    if devices:
        selected_device = st.selectbox("Select Android Device", devices)

        user_profiles = get_user_profiles(selected_device)
        selected_user_id = st.selectbox("Select User Profile", user_profiles)

        # Full-width buttons for UI
        st.markdown("<style>button{width:100% !important}</style>", unsafe_allow_html=True)

        # Run individual steps
        if st.button("Open Link"):
            update_log(status_log, "Opening Firefox and navigating to link...")
            driver = start_driver(selected_device, selected_user_id, appium_url)
            time.sleep(sleep_before_link)  # Adjust time before opening link
            message = open_link_in_firefox(driver, link, status_log)
            update_log(status_log, message)
            driver.quit()

        if st.button("Install Game"):
            update_log(status_log, "Installing game from Play Store...")
            driver = start_driver(selected_device, selected_user_id, appium_url)
            time.sleep(sleep_before_install)  # Adjust time before installing
            message = install_game(driver, link, status_log)
            update_log(status_log, message)
            driver.quit()

        if st.button("Play Game"):
            update_log(status_log, "Playing game...")
            driver = start_driver(selected_device, selected_user_id, appium_url)
            time.sleep(sleep_before_play)  # Adjust time before playing
            message = play_game(driver, status_log, play_duration)  # Pass play_duration
            update_log(status_log, message)
            driver.quit()

        if st.button("Close & Uninstall Game"):
            update_log(status_log, f"Closing and uninstalling {package_name}...")
            driver = start_driver(selected_device, selected_user_id, appium_url)
            time.sleep(sleep_before_uninstall)  # Adjust time before uninstalling
            message = close_uninstall_game(driver, package_name, status_log)
            update_log(status_log, message)
            driver.quit()

        # Reset Ads ID
        if st.button("Reset Ads ID"):
            update_log(status_log, "Resetting Ads ID...")
            driver = start_driver(selected_device, selected_user_id, appium_url)
            message = reset_ads_id(driver, selected_device, selected_user_id, status_log)
            update_log(status_log, message)
            driver.quit()

        # New button: Quit Firefox & Force Stop (works independently)
        if st.button("Quit Firefox & Force Stop"):
            update_log(status_log, "Quitting Firefox and force-stopping it...")
            driver = start_driver(selected_device, selected_user_id, appium_url)
            message = quit_and_clear_firefox(driver, status_log)
            update_log(status_log, message)
            driver.quit()

        # Run all steps in sequence with time adjustments
        if st.button("Run Automation"):
            driver = start_driver(selected_device, selected_user_id, appium_url)

            # Step 1: Open link
            update_log(status_log, "Starting full automation: Opening link...")
            time.sleep(sleep_before_link)
            message = open_link_in_firefox(driver, link, status_log)
            if message == "done":
                update_log(status_log, "Link opened successfully.")

                # Step 2: Install game
                update_log(status_log, "Next: Installing game...")
                time.sleep(sleep_before_install)
                message = install_game(driver, link, status_log)
                if message == "done":
                    update_log(status_log, "Game installed successfully.")

                    # Step 3: Play game
                    update_log(status_log, "Next: Playing game...")
                    time.sleep(sleep_before_play)
                    message = play_game(driver, status_log, play_duration)  # Pass play_duration
                    if message == "done":
                        update_log(status_log, "Game played successfully.")

                        # Step 4: Close & Uninstall
                        update_log(status_log, f"Final Step: Closing and uninstalling {package_name}...")
                        time.sleep(sleep_before_uninstall)
                        message = close_uninstall_game(driver, package_name, status_log)
                        if message == "done":
                            update_log(status_log, "Final Step: Resetting Ads ID...")
                            message = reset_ads_id(driver, selected_device, selected_user_id, status_log)
                            update_log(status_log, message)
                            update_log(status_log, "Automation completed successfully.")
                        else:
                            update_log(status_log, message)
                    else:
                        update_log(status_log, message)
                else:
                    update_log(status_log, message)
            else:
                update_log(status_log, message)

            driver.quit()

    else:
        st.write("No connected Android devices found.")

if __name__ == '__main__':
    main()
