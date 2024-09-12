import streamlit as st
import pandas as pd
import os
import csv
from datetime import datetime

csv_file_path = "links_database.csv"

def save_link(account_name, link, profile, config, run_datetime):
    if not os.path.exists(csv_file_path):
        with open(csv_file_path, 'w') as f:
            writer = csv.writer(f)
            writer.writerow(['Account Name', 'Link', 'Profile', 'Configuration', 'Run DateTime'])
    with open(csv_file_path, 'a') as f:
        writer = csv.writer(f)
        writer.writerow([account_name, link, profile, config, run_datetime])

def delete_link(link_id):
    df = pd.read_csv(csv_file_path)
    df = df.drop(index=link_id)
    df.to_csv(csv_file_path, index=False)

def load_links():
    if os.path.exists(csv_file_path):
        return pd.read_csv(csv_file_path).to_dict('records')
    else:
        return []

def display_saved_links():
    saved_links = load_links()
    st.subheader("Saved Links")
    if saved_links:
        table_data = []
        for idx, link_data in enumerate(saved_links):
            short_link = link_data['Link'][:30] + "..." if len(link_data['Link']) > 30 else link_data['Link']
            table_data.append([
                link_data['Account Name'],
                link_data['Profile'],
                short_link,
                link_data['Run DateTime'],
                st.button(f"Run Now {idx+1}"),
                st.button(f"Delete {idx+1}")
            ])
            if st.session_state.get(f"Run Now {idx+1}"):
                st.write(f"Running automation for link: {link_data['Link']}")
            if st.session_state.get(f"Delete {idx+1}"):
                delete_link(idx)
                st.success(f"Link {idx+1} deleted")
        df = pd.DataFrame(table_data, columns=["Account Name", "Profile", "Link", "Time", "Run", "Delete"])
        st.table(df)
    else:
        st.write("No saved links available.")

def schedule_automation():
    links = load_links()
    current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M')
    for link_data in links:
        if link_data['Run DateTime'] == current_datetime:
            st.write(f"Running automation for link: {link_data['Link']}")
            # Call the automation function here...

def main():
    st.title("Link Management & Scheduling")

    st.subheader("Add New Link Configuration")
    account_name = st.text_input("Enter Account Name")
    link = st.text_input("Enter Tracking Link")
    run_date = st.date_input("Select Run Date")
    run_time = st.time_input("Select Run Time")
    run_datetime = datetime.combine(run_date, run_time).strftime('%Y-%m-%d %H:%M')

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

    sleep_before_link = st.number_input("Time before opening link (seconds)", min_value=1, max_value=60, value=5)
    sleep_before_install = st.number_input("Time before installing game (seconds)", min_value=1, max_value=60, value=10)
    sleep_before_play = st.number_input("Time before playing game (seconds)", min_value=1, max_value=60, value=5)
    sleep_before_uninstall = st.number_input("Time before closing/uninstalling (seconds)", min_value=1, max_value=60, value=5)
    play_duration = st.number_input("Game Play Duration (seconds)", min_value=10, max_value=300, value=30)

    config = {
        "sleep_before_link": sleep_before_link,
        "sleep_before_install": sleep_before_install,
        "sleep_before_play": sleep_before_play,
        "sleep_before_uninstall": sleep_before_uninstall,
        "play_duration": play_duration
    }

    if st.button("Save Link Configuration"):
        save_link(account_name, link, selected_game, config, run_datetime)
        st.success("Link saved successfully!")

    display_saved_links()
    schedule_automation()

if __name__ == '__main__':
    main()
