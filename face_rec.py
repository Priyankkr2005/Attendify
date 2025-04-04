import numpy as np  
import pandas as pd
import cv2
import redis
from insightface.app import FaceAnalysis
from sklearn.metrics import pairwise
from datetime import datetime
import os

# Connect to Redis Client
REDIS_HOST = 'redis-15217.c275.us-east-1-4.ec2.redns.redis-cloud.com'
REDIS_PORT = 15217
REDIS_PASSWORD = 'CCJQsW7tni8VPIOzv0ddEzvgae4feGTg'

r = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD)

# Retrieve Data from Database
def retrieve_data(name):
    retrieved_dict = r.hgetall(name)
    if not retrieved_dict:
        return pd.DataFrame(columns=['Name', 'Role', 'facial_features'])

    valid_entries = {}
    for k, v in retrieved_dict.items():
        try:
            embedding = np.frombuffer(v, dtype=np.float32)
            if embedding.shape[0] == 512:
                valid_entries[k.decode()] = embedding
        except ValueError:
            print(f"Skipping invalid entry: {k.decode()}")

    retrieved_series = pd.Series(valid_entries)
    retrieved_df = retrieved_series.to_frame().reset_index()
    retrieved_df.columns = ['name_role', 'facial_features']
    retrieved_df[['Name', 'Role']] = retrieved_df['name_role'].str.split('@', expand=True)
    return retrieved_df[['Name', 'Role', 'facial_features']]

# Configure Face Analysis
faceapp = FaceAnalysis(name='buffalo_sc', root='insightface_model', providers=['CPUExecutionProvider'])
faceapp.prepare(ctx_id=0, det_size=(640, 640), det_thresh=0.5)

# ML Search Algorithm
def ml_search_algorithm(dataframe, feature_column, test_vector, name_role=['Name', 'Role'], thresh=0.5):
    if dataframe.empty:
        return 'Unknown', 'Unknown'

    X_list = dataframe[feature_column].tolist()
    x = np.asarray(X_list)
    similar = pairwise.cosine_similarity(x, test_vector.reshape(1, -1)).flatten()
    dataframe['cosine'] = similar
    data_filter = dataframe.query(f'cosine >= {thresh}')

    if not data_filter.empty:
        argmax = data_filter['cosine'].idxmax()
        person_name, person_role = data_filter.loc[argmax, name_role]
    else:
        person_name, person_role = 'Unknown', 'Unknown'

    return person_name, person_role

# Real-Time Prediction Class
class RealTimePred:
    def __init__(self):
        self.logs = {'name': [], 'role': [], 'current_time': []}

    def reset_dict(self):
        self.logs = {'name': [], 'role': [], 'current_time': []}

    def save_logs_redis(self):
        dataframe = pd.DataFrame(self.logs).drop_duplicates('name')
        encoded_data = [f"{n}@{r}@{t}" for n, r, t in zip(dataframe['name'], dataframe['role'], dataframe['current_time']) if n != 'Unknown']
        if encoded_data:
            r.lpush('attendance:logs', *encoded_data)
        self.reset_dict()

    def face_prediction(self, test_image, dataframe, feature_column, name_role=['Name', 'Role'], thresh=0.5):
        current_time = str(datetime.now())
        results = faceapp.get(test_image)
        test_copy = test_image.copy()
        
        for res in results:
            x1, y1, x2, y2 = res['bbox'].astype(int)
            embeddings = res['embedding']

            # Logging detected embeddings for debugging
            print("Detected Face Embedding:", embeddings)

            person_name, person_role = ml_search_algorithm(dataframe, feature_column, test_vector=embeddings, name_role=name_role, thresh=thresh)
            
            # Log search results
            print(f"Predicted Name: {person_name}, Role: {person_role}")

            color = (0, 255, 0) if person_name != 'Unknown' else (0, 0, 255)
            cv2.rectangle(test_copy, (x1, y1), (x2, y2), color)
            cv2.putText(test_copy, person_name, (x1, y1), cv2.FONT_HERSHEY_DUPLEX, 0.7, color, 2)
            cv2.putText(test_copy, current_time, (x1, y2 + 10), cv2.FONT_HERSHEY_DUPLEX, 0.7, color, 2)
            self.logs['name'].append(person_name)
            self.logs['role'].append(person_role)
            self.logs['current_time'].append(current_time)
        
        return test_copy

# Registration Form Class
class RegistrationForm:
    def __init__(self):
        self.sample = 0
    
    def reset(self):
        self.sample = 0
    
    def get_embedding(self, frame):
        results = faceapp.get(frame, max_num=1)
        embeddings = None
        for res in results:
            self.sample += 1
            x1, y1, x2, y2 = res['bbox'].astype(int)
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 1)
            cv2.putText(frame, f"samples = {self.sample}", (x1, y1), cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 0), 2)
            embeddings = res['embedding']
        return frame, embeddings
    
    def save_data_in_redis_db(self, name, role):
        if not name or name.strip() == '':
            return 'name_false'
        
        key = f'{name}@{role}'
        if 'face_embedding.txt' not in os.listdir():
            return 'file_false'
        
        x_array = np.loadtxt('face_embedding.txt', dtype=np.float32)
        if x_array.size % 512 != 0:
            return 'file_corrupt'
        
        received_samples = x_array.size // 512
        x_array = x_array.reshape(received_samples, 512)
        x_mean = x_array.mean(axis=0).astype(np.float32).tobytes()
        r.hset(name='academy:register', key=key, value=x_mean)
        os.remove('face_embedding.txt')
        self.reset()
        return True
