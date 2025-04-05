import streamlit as st
# from auth import authenticator
st.set_page_config(page_title='Attendance System',layout='wide')



with st.spinner("Initializing face recognition components"):
    import face_rec


st.header('Attendify : Facial Recognition-Based Attendance System')

st.success('Model loaded sucesfully')
st.success('Redis db sucessfully connected')



