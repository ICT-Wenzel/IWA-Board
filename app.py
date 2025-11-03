import streamlit as st
import json
import requests

# --- GitHub Repo Setup ---
GITHUB_REPO = "ICT-Wenzel/IWA-Board"
FILE_PATH = "data/tasks.json"
GITHUB_TOKEN = st.secrets["github_token"]

headers = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

def load_tasks():
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{FILE_PATH}"
    res = requests.get(url, headers=headers)
    
    if res.status_code == 200:
        content = res.json()
        try:
            file_text = requests.get(content["download_url"]).text
            if not file_text.strip():  # falls Datei leer
                raise ValueError("Empty JSON")
            data = json.loads(file_text)
        except (json.JSONDecodeError, ValueError):
            # Leeres Board anlegen, falls JSON ungültig oder leer
            data = {"Backlog": [], "In Progress": [], "Done": []}
        return data, content["sha"]
    else:
        # Datei existiert noch nicht → leeres Board anlegen
        return {"Backlog": [], "In Progress": [], "Done": []}, None

def save_tasks(tasks, sha):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{FILE_PATH}"
    data = {
        "message": "Update tasks via Streamlit Kanban",
        "content": json.dumps(tasks).encode("utf-8").decode("utf-8"),
        "sha": sha,
    }
    res = requests.put(url, headers=headers, json=data)
    return res.status_code == 200

# --- Streamlit UI ---
st.set_page_config(page_title="Kanban Board", layout="wide")

st.title("🧩 Modernes Kanban Board")

tasks, sha = load_tasks()

cols = st.columns(3)
columns = ["Backlog", "In Progress", "Done"]
colors = ["#74b9ff", "#ffeaa7", "#55efc4"]

for i, col_name in enumerate(columns):
    with cols[i]:
        st.markdown(f"### <span style='color:{colors[i]}'>{col_name}</span>", unsafe_allow_html=True)
        for idx, task in enumerate(tasks[col_name]):
            with st.expander(f"🗒️ {task['title']}"):
                st.write(task["description"])
                move_to = st.selectbox("Verschieben nach", columns, index=i, key=f"{col_name}_{idx}")
                if move_to != col_name:
                    moved = tasks[col_name].pop(idx)
                    tasks[move_to].append(moved)
                    save_tasks(tasks, sha)
                    st.experimental_rerun()
                if st.button("🗑️ Löschen", key=f"delete_{col_name}_{idx}"):
                    tasks[col_name].pop(idx)
                    save_tasks(tasks, sha)
                    st.experimental_rerun()

# --- Add New Task ---
st.markdown("---")
st.subheader("➕ Neue Aufgabe hinzufügen")
title = st.text_input("Titel")
desc = st.text_area("Beschreibung")

if st.button("Aufgabe hinzufügen"):
    if title:
        tasks["Backlog"].append({"title": title, "description": desc})
        save_tasks(tasks, sha)
        st.success("Aufgabe hinzugefügt!")
        st.experimental_rerun()
