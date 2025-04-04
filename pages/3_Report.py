import streamlit as st 
from Home import face_rec
import pandas as pd

st.set_page_config(page_title='Reporting', layout='wide')
st.subheader('📊 Reporting')

# Function to retrieve logs from Redis list
def load_logs(name, end=-1):
    logs_list = face_rec.r.lrange(name, start=0, end=end)  # Extract all log data
    return [entry.decode() for entry in logs_list] if logs_list else []

# Function to retrieve registered students
def get_registered_students():
    """Fetch registered students from Redis."""
    redis_face_db = face_rec.retrieve_data(name='academy:register')

    if isinstance(redis_face_db, str):
        try:
            redis_face_db = pd.read_json(redis_face_db)
        except ValueError:
            return pd.DataFrame(columns=['Name', 'Role'])
    
    if redis_face_db.empty:
        return pd.DataFrame(columns=['Name', 'Role'])
    
    return redis_face_db[['Name', 'Role']]

# Tabs for switching between views
tab1, tab2 = st.tabs(['🧑‍🎓 Registered Data', '🕒 Logs'])

with tab1:
    if st.button('🔄 Refresh Data'):
        with st.spinner('Retrieving Data from Redis DB...'):    
            registered_students = get_registered_students()
            if registered_students.empty:
                st.warning("No registered students found.")
            else:
                st.dataframe(registered_students)

with tab2:
    if st.button('📥 Refresh Logs'):
        with st.spinner('Fetching Attendance Logs...'):
            logs = load_logs(name='attendance:logs')

            # Optional: Print a sample log for debugging
            if logs:
                st.text(f"Sample log: {logs[0]}")

            # Extract student names from logs
            present_students = {log.split('@')[0].strip().lower() for log in logs} if logs else set()

            # Get all registered students
            registered_students = get_registered_students()

            if registered_students.empty:
                st.warning("No registered students available.")
            else:
                registered_students['Status'] = registered_students['Name'].apply(
                    lambda name: 'P' if name in present_students else 'A'
                )

                st.dataframe(registered_students[['Name', 'Role', 'Status']])
