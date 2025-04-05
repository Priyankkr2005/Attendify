import pandas as pd
import streamlit as st
from Home import face_rec
import datetime

st.subheader('Reporting')

logs_key = 'attendance:logs'
register_key = 'academy:register'

def load_logs(name, end=-1):
    logs_list = face_rec.r.lrange(name, start=0, end=end)
    return logs_list

tab1, tab2, tab3 = st.tabs(['Registered Data', 'Logs', 'Attendance Report'])

with tab1:
    if st.button('Refresh Data'):
        with st.spinner('Retrieving Data from Redis DB ...'):
            redis_face_db = face_rec.retrive_data(name=register_key)
            st.dataframe(redis_face_db[['Name', 'Role']])

with tab2:
    if st.button('Refresh Logs'):
        st.write(load_logs(name=logs_key))

with tab3:
    st.subheader('Attendance Report')

    # Step 1: Load logs
    logs_list = load_logs(name=logs_key)
    logs_list_string = list(map(lambda x: x.decode('utf-8'), logs_list))
    logs_nested_list = list(map(lambda x: x.split('@'), logs_list_string))

    if logs_nested_list:
        logs_df = pd.DataFrame(logs_nested_list, columns=['Name', 'Role', 'Timestamp'])
        logs_df['Timestamp'] = logs_df['Timestamp'].apply(lambda x: x.split('.')[0])
        logs_df['Timestamp'] = pd.to_datetime(logs_df['Timestamp'])
        logs_df['Date'] = logs_df['Timestamp'].dt.date
    else:
        logs_df = pd.DataFrame(columns=['Name', 'Role', 'Timestamp', 'Date'])

    # Step 2: Generate report from logs
    report_df = logs_df.groupby(by=['Date', 'Name', 'Role']).agg(
        In_time=pd.NamedAgg('Timestamp', 'min'),
        Out_time=pd.NamedAgg('Timestamp', 'max')
    ).reset_index()

    report_df['In_time'] = pd.to_datetime(report_df['In_time'], errors='coerce')
    report_df['Out_time'] = pd.to_datetime(report_df['Out_time'], errors='coerce')
    report_df['Duration'] = report_df['Out_time'] - report_df['In_time']

    # Step 3: Fetch registered people
    registered_df = face_rec.retrive_data(name=register_key)[['Name', 'Role']].drop_duplicates()

    # Step 4: Build attendance matrix
    today = datetime.datetime.now().date()
    all_dates = pd.date_range(end=today, periods=1).date  # You can change to more days

    date_name_role_zip = []
    for dt in all_dates:
        for _, row in registered_df.iterrows():
            date_name_role_zip.append([dt, row['Name'], row['Role']])

    base_df = pd.DataFrame(date_name_role_zip, columns=['Date', 'Name', 'Role'])

    # Step 5: Merge with report
    full_df = pd.merge(base_df, report_df, how='left', on=['Date', 'Name', 'Role'])

    # Step 6: Mark Present or Absent
    def status_marker(row):
        return 'Absent' if pd.isnull(row['In_time']) else 'Present'

    full_df['Status'] = full_df.apply(status_marker, axis=1)

    t1, t2 = st.tabs(['Complete Report', 'Filter Report'])

    with t1:
        st.subheader('Complete Report')
        st.dataframe(full_df)

    with t2:
        st.subheader('Search Records')

        date_in = str(st.date_input('Filter Date', datetime.datetime.now().date()))
        name_list = full_df['Name'].unique().tolist()
        name_in = st.selectbox('Select Name', ['ALL'] + name_list)

        role_list = full_df['Role'].unique().tolist()
        role_in = st.selectbox('Select Role', ['ALL'] + role_list)

        status_list = full_df['Status'].unique().tolist()
        status_in = st.multiselect('Select the Status', ['ALL'] + status_list)

        if st.button('Submit'):
            full_df['Date'] = full_df['Date'].astype(str)
            filter_df = full_df.query(f'Date == "{date_in}"')

            if name_in != 'ALL':
                filter_df = filter_df.query(f'Name == "{name_in}"')
            if role_in != 'ALL':
                filter_df = filter_df.query(f'Role == "{role_in}"')

            if 'ALL' in status_in:
                pass
            elif len(status_in) > 0:
                filter_df = filter_df[filter_df['Status'].isin(status_in)]

            st.dataframe(filter_df)
