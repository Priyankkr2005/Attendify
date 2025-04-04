import streamlit as st  
from Home import face_rec
from streamlit_webrtc import webrtc_streamer
import av
import time

st.subheader('Real-Time Attendance System')

# Retrieve the data from Redis Database
with st.spinner('Retrieving Data from Redis DB ...'):    
    redis_face_db = face_rec.retrieve_data(name='academy:register')
    st.dataframe(redis_face_db)

st.success("Data successfully retrieved from Redis")

# Time settings
waitTime = 10  # Reduced wait time from 30s to 10s for testing
setTime = time.time()
realtimepred = face_rec.RealTimePred()  # Real-time prediction class

# Streamlit WebRTC: Real-Time Prediction
def video_frame_callback(frame):
    global setTime
    
    img = frame.to_ndarray(format="bgr24")  # Convert frame to numpy array
    pred_img = realtimepred.face_prediction(img, redis_face_db,
                                            'facial_features', ['Name', 'Role'], thresh=0.5)
    
    timenow = time.time()
    difftime = timenow - setTime
    if difftime >= waitTime:
        realtimepred.save_logs_redis()
        setTime = time.time()  # Reset timer        
        print('Logs saved to Redis')

    return av.VideoFrame.from_ndarray(pred_img, format="bgr24")

webrtc_streamer(key="realtimePrediction", video_frame_callback=video_frame_callback,
                rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]})

# 🚀 Debugging: Manually save logs for testing
if st.button("Save Logs Now"):
    realtimepred.save_logs_redis()
    st.success("Logs saved to Redis manually")
