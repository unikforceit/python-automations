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

# Function to retrieve the current Ads ID of the selected profile
def get_ads_id(device_id, user_id):
    try:
        result = subprocess.run(['adb', '-s', device_id, 'shell', 'am', 'broadcast',
                                 '--user', str(user_id), '-a', 'com.google.android.gms.ads.identifier.service.GET_AD_ID'],
                                capture_output=True, text=True)
        for line in result.stdout.splitlines():
            if "advertisingId" in line:
                ads_id = line.split('=')[-1].strip()
                return ads_id
        return "Could not retrieve Ads ID"
    except Exception as e:
        return f"Failed to get Ads ID: {e}"

# Function to reset the Ads ID of the selected profile
def reset_ads_id(driver, device_id, user_id, status_log):
    try:
        # Clear Google Play Services data to reset the Ads ID
        driver.execute_script('mobile: shell', {
            'command': 'pm',
            'args': ['clear', '--user', user_id, 'com.google.android.gms']
        })
        update_log(status_log, "Google Play Services data cleared (Ads ID reset)")

        # Retrieve the new Ads ID after the reset
        time.sleep(5)  # Give it some time to reset
        new_ads_id = get_ads_id(device_id, user_id)
        update_log(status_log, f"New Ads ID: {new_ads_id}")

        return new_ads_id
    except Exception as e:
        return f"Failed to reset Ads ID: {e}"

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
            return "Link opened in Firefox and redirected to Play Store"
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
        time.sleep(10)
        install_button = driver.find_element(AppiumBy.XPATH, '//android.widget.TextView[@content-desc="Install"]')
        install_button.click()
        update_log(status_log, "Install button clicked")

        time.sleep(10)  # Wait for the download button to appear

        # Click on the Download button
        download_button = driver.find_element(AppiumBy.XPATH, '//android.widget.TextView[@content-desc="Download"]')
        download_button.click()
        update_log(status_log, "Download button clicked, game installation started")

        return f"Game installation started for {package_name}"
    except NoSuchElementException:
        return "Install or Download button not found"
    except Exception as e:
        return f"Failed to install game: {str(e)}"

# Function to play the game
def play_game(driver, status_log):
    try:
        play_button = driver.find_element(AppiumBy.XPATH, '//android.widget.TextView[@content-desc="Play"]')
        play_button.click()
        time.sleep(30)  # Play for 30 seconds
        return "Game played for 30 seconds"
    except NoSuchElementException:
        return "Play button not found"
    except Exception as e:
        return f"Failed to play game: {e}"

# Function to close and uninstall the game
def close_uninstall_game(driver, package_name, status_log):
    try:
        driver.execute_script('mobile: shell', {
            'command': 'pm',
            'args': ['uninstall', '--user', driver.capabilities['userProfile'], package_name]
        })
        update_log(status_log, f"Game {package_name} uninstalled")
        return f"Game {package_name} uninstalled"
    except Exception as e:
        return f"Failed to uninstall game {package_name}: {e}"

# Streamlit UI
def main():
    st.title("App Automation with Streamlit")

    # Appium Localhost Input
    appium_url = st.text_input("Enter Appium Server URL", value="http://localhost:4723")

    # Game link input
    link = st.text_input("Enter Tracking Link")

    # Status log box at the top to ensure it's initialized
    status_log = st.empty()

    # Detect devices and profiles
    devices = get_connected_devices()
    if devices:
        selected_device = st.selectbox("Select Android Device", devices)

        user_profiles = get_user_profiles(selected_device)
        selected_user_id = st.selectbox("Select User Profile", user_profiles)

        # Show the current Ads ID
        ads_id = get_ads_id(selected_device, selected_user_id)
        st.write(f"Current Ads ID: {ads_id}")

        if st.button("Open Link"):
            update_log(status_log, "Opening Firefox and navigating to link...")
            driver = start_driver(selected_device, selected_user_id, appium_url)
            message = open_link_in_firefox(driver, link, status_log)
            update_log(status_log, message)
            driver.quit()

        if st.button("Install Game"):
            update_log(status_log, "Installing game from Play Store...")
            driver = start_driver(selected_device, selected_user_id, appium_url)
            message = install_game(driver, link, status_log)
            update_log(status_log, message)
            driver.quit()

        if st.button("Play Game"):
            update_log(status_log, "Playing game...")
            driver = start_driver(selected_device, selected_user_id, appium_url)
            message = play_game(driver, status_log)
            update_log(status_log, message)
            driver.quit()

        if st.button("Close & Uninstall Game"):
            package_name = link.split('/')[3].split('?')[0]
            update_log(status_log, f"Closing and uninstalling {package_name}...")
            driver = start_driver(selected_device, selected_user_id, appium_url)
            message = close_uninstall_game(driver, package_name, status_log)
            update_log(status_log, message)
            driver.quit()

        if st.button("Reset Ads ID"):
            update_log(status_log, "Resetting Ads ID...")
            driver = start_driver(selected_device, selected_user_id, appium_url)
            new_ads_id = reset_ads_id(driver, selected_device, selected_user_id, status_log)
            update_log(status_log, f"New Ads ID: {new_ads_id}")
            driver.quit()

    else:
        st.write("No connected Android devices found.")

if __name__ == '__main__':
    main()
