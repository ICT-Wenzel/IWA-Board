import streamlit as st
import json
import requests
import base64

# --- GitHub Setup ---
GITHUB_REPO = st.secrets["github_repo"]  # z.B. "deinname/IWABoard"
FILE_PATH = "data/tasks.json"
GITHUB_TOKEN = st.secrets["github_token"]

headers = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

# --- Funktionen: Laden & Speichern ---
def load_tasks():
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{FILE_PATH}"
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        content = res.json()
        try:
            file_text = requests.get(content["download_url"]).text
            if not file_text.strip():  # leeres JSON abfangen
                raise ValueError("Empty JSON")
            data = json.loads(file_text)
        except (json.JSONDecodeError, ValueError):
            data = {"Backlog": [], "In Progress": [], "Done": []}
        return data, content.get("sha", None)
    else:
        return {"Backlog": [], "In Progress": [], "Done": []}, None

def save_tasks(tasks, sha):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{FILE_PATH}"
    content_str = json.dumps(tasks, indent=2)
    payload = {
        "message": "Update tasks via IWA Board",
        "content": base64.b64encode(content_str.encode()).decode(),
    }
    if sha:
        payload["sha"] = sha
    res = requests.put(url, headers=headers, json=payload)
    return res.status_code in [200, 201]

# --- Session State Setup ---
def reload_tasks():
    st.session_state.tasks, st.session_state.sha = load_tasks()

reload_tasks()

# --- Streamlit Setup ---
st.set_page_config(page_title="IWA Board", layout="wide")
st.title("🧩 IWA Board")

columns = ["Backlog", "In Progress", "Done"]
colors = ["#74b9ff", "#ffeaa7", "#55efc4"]
cols = st.columns(3)

# --- Neue Aufgabe erstellen ---
with st.sidebar:
    st.subheader("➕ Neue Aufgabe")
    new_title = st.text_input("Titel")
    new_desc = st.text_area("Beschreibung")
    if st.button("Hinzufügen"):
        if new_title.strip():
            st.session_state.tasks["Backlog"].append({"title": new_title, "description": new_desc})
            save_tasks(st.session_state.tasks, st.session_state.sha)
            reload_tasks()
            st.success("Task hinzugefügt!")

# --- Board anzeigen ---
for i, col_name in enumerate(columns):
    with cols[i]:
        st.markdown(f"### <span style='color:{colors[i]}'>{col_name}</span>", unsafe_allow_html=True)
        for idx, task in enumerate(st.session_state.tasks[col_name]):
            # Card Design
            card = f"""
            <div style='
                background-color: {colors[i]};
                padding: 10px;
                margin-bottom: 8px;
                border-radius: 8px;
                box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
            '>
            <b>{task['title']}</b><br>{task['description']}
            </div>
            """
            st.markdown(card, unsafe_allow_html=True)

            # Move Task
            move_to = st.selectbox("Verschieben nach", columns, index=i, key=f"move_{col_name}_{idx}")
            if move_to != col_name:
                moved = st.session_state.tasks[col_name].pop(idx)
                st.session_state.tasks[move_to].append(moved)
                save_tasks(st.session_state.tasks, st.session_state.sha)
                reload_tasks()

            # Delete Task
            if st.button("🗑️ Löschen", key=f"del_{col_name}_{idx}"):
                st.session_state.tasks[col_name].pop(idx)
                save_tasks(st.session_state.tasks, st.session_state.sha)
                reload_tasks()
