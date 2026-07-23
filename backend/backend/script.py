from sklearn.preprocessing import MinMaxScaler
import pickle
import numpy as np
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["meta"]

all_inflow = list(db.tn_inflow.find({}, {"_id": 0}))

values = np.array(
    [item["tourist_inflow"] for item in all_inflow]
).reshape(-1, 1)

scaler = MinMaxScaler()
scaler.fit(values)

with open("models/lstm_scaler.pkl", "wb") as f:
    pickle.dump(scaler, f)

print("Scaler updated successfully.")