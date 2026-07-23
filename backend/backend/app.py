import pickle
import numpy as np
import bcrypt
import time
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    get_jwt_identity
)
from pymongo import MongoClient
from tensorflow.keras.models import load_model
from datetime import datetime
import joblib
import os

# ===============================
# FLASK SETUP
# ===============================
app = Flask(__name__)
CORS(app)

app.config["JWT_SECRET_KEY"] = "tourmate-secret-key"
jwt = JWTManager(app)

# ===============================
# MONGODB CONNECTION
# ===============================
client = MongoClient("mongodb://localhost:27017/")
db = client["meta"]

# ===============================
# LOAD MODELS
# ===============================
# Load Hybrid Models
svd_model = joblib.load("models/collaborative_model.pkl")
tfidf = joblib.load("models/tfidf_vectorizer.pkl")
cosine_sim = np.load("models/cosine_similarity.npy")

ALPHA = 0.8   # content weight
BETA  = 0.2   # collaborative weight
GAMMA = 0.5   # demand penalty weight
WINDOW = 12

print("Models loaded successfully")
# ===============================
# DISTRICT CACHE CONFIG
# ===============================
district_cache = {
    "data": None,
    "last_updated": 0
}

CACHE_TTL = 600  # 10 minutes
############################################################
def calculate_average_rating(dest_id):
    ratings = list(db.user_interaction.find(
        {"dest_id": dest_id, "interaction_type": "rating"},
        {"_id": 0, "rating": 1}
    ))
    if not ratings:
        return 0
    total = 0
    count = 0
    for r in ratings:
        try:
            total += int(r["rating"])
            count += 1
        except:
            continue
    if count == 0:
        return 0
    avg = total / count
    return round(avg, 2)
############################################################
def build_district_cache():

    print("Rebuilding district cache...")

    dest_df = list(db.destination.find({}, {"_id": 0}))
    unique_districts = list(set(
        dest["district"] for dest in dest_df
    ))

    district_metrics = {}

    for district in unique_districts:

        inflow_data = list(db.tn_inflow.find(
            {"district": district},
            {"_id": 0}
        ).sort([("year", 1)]))

        if not inflow_data:
            district_metrics[district] = {
                "crowd_index": 0.5,
                "future_demand_norm": 0.5
            }
            continue

        values = np.array(
            [i["tourist_inflow"] for i in inflow_data]
        ).reshape(-1, 1)

        # Crowd index (latest month normalized)
        scaled = (values - values.min()) / (values.max() - values.min() + 1e-9)
        crowd_index = float(scaled[-1][0])

        # Future demand prediction
        future_demand = predict_future_demand(values)

        max_val = values.max()
        future_demand_norm = float(future_demand / (max_val + 1e-9))

        district_metrics[district] = {
            "crowd_index": crowd_index,
            "future_demand_norm": future_demand_norm
        }

    return district_metrics
# ===============================
# SIGNUP (Start from U501)
# ===============================
@app.route("/signup", methods=["POST"])
def signup():
    data = request.json

    # 🔒 Validate input safely
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")
    if not username or not email or not password:
        return jsonify({"message": "All fields are required"}), 400

    email = email.lower().strip()
    # 🔒 Check duplicate email
    if db.users.find_one({"email": email}):
        return jsonify({"message": "Email already exists"}), 409

    # 🔢 Generate user_id
    last_user = db.users.find_one(sort=[("user_id", -1)])

    if last_user and "user_id" in last_user:
        last_number = int(last_user["user_id"][1:])
        new_user_id = f"U{last_number + 1}"
    else:
        new_user_id = "U501"

    # 🔐 Hash password
    hashed_pw = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

    user = {
        "user_id": new_user_id,
        "username": username.strip(),
        "email": email,
        "password": hashed_pw.decode("utf-8")
    }

    db.users.insert_one(user)

    return jsonify({
        "message": "User registered successfully",
        "user_id": new_user_id
    }), 201


# ===============================
# LOGIN
# ===============================
@app.route("/login", methods=["POST"])
def login():
    data = request.json

    email = data["email"]
    password = data["password"]

    user = db.users.find_one({"email": email})

    if user:
        stored_password = user["password"].encode("utf-8")

        if bcrypt.checkpw(password.encode("utf-8"), stored_password):
            access_token = create_access_token(identity=user["user_id"])
            return jsonify({
                "access_token": access_token,
                "user_id": user["user_id"]
            })

    return jsonify({"message": "Invalid credentials"}), 401


# ===============================
# RATE DESTINATION
# ===============================
@app.route("/rate", methods=["POST"])
@jwt_required()
def rate_destination():

    current_user_id = get_jwt_identity()
    data = request.json

    dest_id = data.get("dest_id")
    rating = int(data.get("rating"))

    # 🔒 Validate input
    if not dest_id or rating is None:
        return jsonify({"error": "dest_id and rating required"}), 400

    if not isinstance(rating, int) or rating < 1 or rating > 5:
        return jsonify({"error": "Rating must be integer between 1 and 5"}), 400

    # 🔄 Update if exists, else insert
    result = db.user_interaction.update_one(
        {
            "user_id": current_user_id,
            "dest_id": dest_id,
            "interaction_type": "rating"
        },
        {
            "$set": {
                "rating": rating,
                "interaction_type": "rating"
            }
        },
        upsert=True
    )

    if result.matched_count > 0:
        message = "Rating updated successfully"
    else:
        message = "Rating added successfully"

    return jsonify({"message": message})


# ===============================
# HYBRID RECOMMENDATION
# ===============================
# =====================================
# PATH CONFIG
# =====================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "district_models")
SCALER_DIR = os.path.join(BASE_DIR, "district_scalers")
WINDOW = 12
GAMMA = 0.2

# =====================================
# GLOBAL DICTIONARIES (IMPORTANT)
# =====================================
district_models = {}
district_scalers = {}

# =====================================
# PRELOAD DISTRICT MODELS
# =====================================
for filename in os.listdir(MODEL_DIR):
    if filename.endswith(".keras"):
        district = filename.replace(".keras", "")
        district_models[district] = load_model(
            os.path.join(MODEL_DIR, filename),
            compile=False
        )

for filename in os.listdir(SCALER_DIR):
    if filename.endswith("_scaler.pkl"):
        district = filename.replace("_scaler.pkl", "")
        district_scalers[district] = joblib.load(
            os.path.join(SCALER_DIR, filename)
        )
@app.route("/recommend", methods=["GET"])
@jwt_required()
def recommend():

    current_user_id = get_jwt_identity()

    user_ratings = list(
        db.user_interaction.find(
            {
                "user_id": current_user_id,
                "interaction_type": "rating"
            }
        )
    )

    rating_count = len(user_ratings)

    # =====================================
    # 1️⃣ COLD START
    # =====================================
    if rating_count == 0:

        pipeline = [
            {"$match": {"interaction_type": "rating"}},
            {"$group": {
                "_id": "$dest_id",
                "avg_rating": {"$avg": "$rating"},
                "count": {"$sum": 1}
            }},
            {"$sort": {"avg_rating": -1, "count": -1}},
            {"$limit": 5}
        ]

        top_rated = list(db.user_interaction.aggregate(pipeline))
        results = []

        for item in top_rated:
            dest = db.destination.find_one(
                {"dest_id": item["_id"]},
                {"_id": 0}
            )

            if dest:
                results.append({
                    "dest_id": dest["dest_id"],
                    "name": dest["name"],
                    "district": dest["district"],
                    "category": dest.get("category", ""),
                    "image_url": dest.get("image_url", ""),
                    "average_rating": round(item["avg_rating"], 2),
                    "score": None
                })

        return jsonify(results)

    # =====================================
    # 2️⃣ ADAPTIVE WEIGHTS
    # =====================================
    if rating_count < 3:
        ALPHA = 1.0
        BETA = 0.0
    elif rating_count < 7:
        ALPHA = 0.7
        BETA = 0.3
    else:
        ALPHA = 0.5
        BETA = 0.5

    # =====================================
    # 3️⃣ PREPARE DATA
    # =====================================
    destinations = list(db.destination.find({}, {"_id": 0}))
    results = []

    # Map dest_id to index (VERY IMPORTANT)
    dest_id_to_index = {
        dest["dest_id"]: i
        for i, dest in enumerate(destinations)
    }

    # Get liked destinations (rating >= 4)
    liked_dest_ids = []

    for item in user_ratings:
        try:
            rating_value = float(item.get("rating", 0))
            if rating_value >= 4:
                liked_dest_ids.append(item["dest_id"])
        except:
            continue

    # =====================================
    # 4️⃣ SCORING LOOP
    # =====================================
    for idx, dest in enumerate(destinations):

        # -------- FIXED CONTENT SCORE --------
        content_score = 0

        if liked_dest_ids:

            similarities = []

            for liked_id in liked_dest_ids:

                liked_idx = dest_id_to_index.get(liked_id)

                if liked_idx is not None:
                    similarities.append(
                        cosine_sim[idx][liked_idx]
                    )

            if similarities:
                content_score = float(np.mean(similarities))

        # -------- COLLABORATIVE SCORE --------
        try:
            collab_score = (
                collaborative_model
                .predict(current_user_id, dest["dest_id"])
                .est / 5.0
            )
        except:
            collab_score = 0

        hybrid_score = (ALPHA * content_score) + (BETA * collab_score)

        # -------- DEMAND PENALTY --------
        district = dest["district"]
        future_demand_norm = 0.5

        model = district_models.get(district)
        scaler = district_scalers.get(district)

        if model and scaler:

            inflow_data = list(
                db.tn_inflow.find(
                    {"district": district},
                    {"_id": 0}
                ).sort([("year", 1)])
            )

            if len(inflow_data) >= WINDOW:

                values = np.array(
                    [item["tourist_inflow"] for item in inflow_data]
                ).reshape(-1, 1)

                seq = scaler.transform(values[-WINDOW:])
                seq = seq.reshape(1, WINDOW, 1)

                pred_scaled = model.predict(seq, verbose=0)
                predicted_value = scaler.inverse_transform(pred_scaled)[0][0]

                max_val = values.max()
                future_demand_norm = float(
                    predicted_value / (max_val + 1e-9)
                )

        # -------- FINAL SCORE --------
        final_score = hybrid_score - (GAMMA * future_demand_norm)

        results.append({
            "dest_id": dest["dest_id"],
            "name": dest["name"],
            "district": dest["district"],
            "category": dest.get("category", ""),
            "image_url": dest.get("image_url", ""),
            "average_rating": round(
                calculate_average_rating(dest["dest_id"]), 2
            ),
            "score": round(final_score, 3)
        })

    # =====================================
    # 5️⃣ SORT & RETURN
    # =====================================
    results = sorted(results, key=lambda x: x["score"], reverse=True)

    return jsonify(results[:10])
# ===============================
# DEMAND PREDICTION (LSTM)
# ===============================

MODEL_DIR = "district_models"
SCALER_DIR = "district_scalers"
WINDOW = 12


# @app.route("/demand/<district>", methods=["GET"])
# def demand(district):

#     model_path = os.path.join(MODEL_DIR, f"{district}.keras")
#     scaler_path = os.path.join(SCALER_DIR, f"{district}_scaler.pkl")

#     if not os.path.exists(model_path):
#         return jsonify({"error": f"LSTM model not found for {district}"}), 404

#     if not os.path.exists(scaler_path):
#         return jsonify({"error": f"Scaler not found for {district}"}), 404

#     model = load_model(model_path, compile=False)
#     scaler = joblib.load(scaler_path)

#     inflow_data = list(
#         db.tn_inflow.find(
#             {"district": district},
#             {"_id": 0}
#         ).sort([("year", 1)])
#     )

#     if len(inflow_data) < WINDOW:
#         return jsonify({"error": "Not enough historical data"}), 400

#     values = np.array(
#         [item["tourist_inflow"] for item in inflow_data]
#     ).reshape(-1, 1)

#     # last 12 months input
#     seq = scaler.transform(values[-WINDOW:])
#     seq = seq.reshape(1, WINDOW, 1)

#     predictions = []

#     for _ in range(12):
#         next_scaled = model.predict(seq, verbose=0)
#         next_value = scaler.inverse_transform(next_scaled)[0][0]

#         predictions.append(round(float(next_value), 2))

#         seq = np.concatenate(
#             [seq[:, 1:, :], next_scaled.reshape(1, 1, 1)],
#             axis=1
#         )

#     # Month labels (Jan–Dec)
#     months = [
#         "Jan","Feb","Mar","Apr","May","Jun",
#         "Jul","Aug","Sep","Oct","Nov","Dec"
#     ]

#     return jsonify({
#             "district": district,
#             "months": months,
#             "historical_inflow": values.flatten().tolist(),
#             "forecast_inflow": predictions   # <-- IMPORTANT rename
#     })
###############
from statsmodels.tsa.statespace.sarimax import SARIMAX

@app.route("/demand/<district>", methods=["GET","option"])
def demand(district):

    inflow_data = list(
        db.tn_inflow.find(
            {"district": district},
            {"_id": 0}
        ).sort([("year", 1), ("month", 1)])   # ✅ FIXED SORT
    )

    if len(inflow_data) < 24:
        return jsonify({"error": "Not enough data"}), 400

    values = np.array(
        [item["tourist_inflow"] for item in inflow_data]
    )

    # ✅ SARIMA MODEL
    model = SARIMAX(
        values,
        order=(1, 1, 1),
        seasonal_order=(1, 1, 1, 12)  # monthly seasonality
    )

    results = model.fit(disp=False)

    forecast = results.forecast(steps=12)

    months = [
        "Jan","Feb","Mar","Apr","May","Jun",
        "Jul","Aug","Sep","Oct","Nov","Dec"
    ]

    return jsonify({
        "district": district,
        "months": months,
        "historical_inflow": values.tolist(),
        "forecast_inflow": forecast.tolist()
    })
########################################################################
@app.route("/destinations", methods=["GET"])
def get_all_destinations():
    destinations = list(db.destination.find({}, {"_id": 0}))

    for dest in destinations:
        dest["average_rating"] = calculate_average_rating(dest.get("dest_id"))
        dest["image_url"] = dest.get("image_url", "")
        dest["category"] = dest.get("category", "")
        dest["description"] = dest.get("description", "")

    return jsonify(destinations), 200

@app.route("/destination/<dest_id>", methods=["GET"])
def get_destination_detail(dest_id):

    dest = db.destination.find_one(
        {"dest_id": dest_id},
        {"_id": 0}
    )

    if not dest:
        return jsonify({"error": "Destination not found"}), 404

    dest["average_rating"] = calculate_average_rating(dest_id)
    dest["image_url"] = dest.get("image_url", "")
    dest["category"] = dest.get("category", "")
    dest["description"] = dest.get("description", "")

    return jsonify(dest), 200

@app.route("/destinations/filter", methods=["GET"])
def filter_destinations():

    category = request.args.get("category")
    district = request.args.get("district")

    query = {}

    if category:
        query["category"] = {"$regex": category, "$options": "i"}

    if district:
        query["district"] = {"$regex": district, "$options": "i"}

    results = list(db.destination.find(query, {"_id": 0}))

    for dest in results:
        dest["average_rating"] = calculate_average_rating(dest.get("dest_id"))
        dest["image_url"] = dest.get("image_url", "")
        dest["category"] = dest.get("category", "")
        dest["description"] = dest.get("description", "")

    return jsonify(results), 200


@app.route("/similar/<dest_id>", methods=["GET"])
def similar_destinations(dest_id):

    dest_list = list(db.destination.find({}, {"_id": 0}))

    index_map = {d["dest_id"]: i for i, d in enumerate(dest_list)}

    if dest_id not in index_map:
        return jsonify({"error": "Destination not found"}), 404

    idx = index_map[dest_id]

    similarity_scores = list(enumerate(cosine_sim[idx]))
    similarity_scores = sorted(similarity_scores, key=lambda x: x[1], reverse=True)[1:6]

    results = []
    for i, score in similarity_scores:
        dest = dest_list[i]
        results.append({
            "dest_id": dest["dest_id"],
            "name": dest["name"],
            "district": dest["district"],
            "category": dest.get("category", ""),
            "image_url": dest.get("image_url", ""),
            "average_rating": calculate_average_rating(dest["dest_id"]),
            "similarity_score": round(float(score), 3)
        })

    return jsonify(results)

@app.route("/favorites", methods=["GET"])
@jwt_required()
def get_favorites():

    current_user_id = get_jwt_identity()

    favorite_records = list(db.favorites.find(
        {"user_id": current_user_id},
        {"_id": 0}
    ))

    results = []

    for fav in favorite_records:
        dest = db.destination.find_one(
            {"dest_id": fav["dest_id"]},
            {"_id": 0}
        )

        if dest:
            dest["average_rating"] = calculate_average_rating(dest["dest_id"])
            dest["image_url"] = dest.get("image_url", "")
            results.append(dest)

    return jsonify(results)

@app.route("/favorite", methods=["POST"])
@jwt_required()
def add_favorite():

    current_user_id = get_jwt_identity()
    data = request.json

    record = {
        "user_id": current_user_id,
        "dest_id": data["dest_id"]
    }

    db.favorites.update_one(
    {"user_id": current_user_id, "dest_id": data["dest_id"]},
    {"$set": record},
    upsert=True
)

    return jsonify({"message": "Added to favorites"})

@app.route("/favorite/<dest_id>", methods=["DELETE"])
@jwt_required()
def remove_favorite(dest_id):

    current_user_id = get_jwt_identity()

    db.favorites.delete_one({
        "user_id": current_user_id,
        "dest_id": dest_id
    })

    return jsonify({"message": "Removed from favorites"})

@app.route("/crowd-index/<district>", methods=["GET"])
def crowd_index(district):

    inflow = list(db.tn_inflow.find(
        {"district": district},
        {"_id": 0}
    ))

    if not inflow:
        return jsonify({"error": "District not found"}), 404

    values = np.array([item["tourist_inflow"] for item in inflow]).reshape(-1, 1)

    scaled = (values - values.min()) / (values.max() - values.min() + 1e-9)

    return jsonify({
        "district": district,
        "crowd_index": float(scaled[-1][0])
    })

@app.route("/analytics/top-districts", methods=["GET"])
def top_districts():

    pipeline = [
        {"$group": {"_id": "$district", "total": {"$sum": "$tourist_inflow"}}},
        {"$sort": {"total": -1}},
        {"$limit": 5}
    ]

    results = list(db.tn_inflow.aggregate(pipeline))

    formatted = [
        {"district": r["_id"], "total_inflow": r["total"]}
        for r in results
    ]

    return jsonify(formatted)
@app.route("/profile/delete", methods=["DELETE"])
@jwt_required()
def delete_user():
    current_user_id = get_jwt_identity()

    db.users.delete_one({"user_id": current_user_id})
    db.user_interaction.delete_many({"user_id": current_user_id})
    db.favorites.delete_many({"user_id": current_user_id})

    return jsonify({"message": "User deleted"})
@app.route("/profile/update", methods=["PUT"])
@jwt_required()
def update_profile():
    current_user_id = get_jwt_identity()
    data = request.json

    db.users.update_one(
        {"user_id": current_user_id},
        {"$set": {
            "username": data.get("username"),
            "email": data.get("email"),
            "user_id":data.get("user_id")
        }}
    )
    return jsonify({"message": "Profile updated"})
@app.route("/profile", methods=["GET"])
@jwt_required()
def get_profile():
    current_user_id = get_jwt_identity()

    user = db.users.find_one(
        {"user_id": current_user_id},
        {"_id": 0, "password": 0}
    )

    return jsonify(user)
@app.route("/history", methods=["GET"])
@jwt_required()
def history():

    current_user_id = get_jwt_identity()

    interactions = list(db.user_interaction.find(
        {"user_id": current_user_id},
        {"_id": 0}
    ))

    results = []

    for item in interactions:

        dest = db.destination.find_one(
            {"dest_id": item["dest_id"]},
            {"_id": 0}
        )

        if dest:
            results.append({
                "dest_id": dest["dest_id"],
                "name": dest["name"],
                "district": dest["district"],
                "category": dest.get("category", ""),
                "image_url": dest.get("image_url", ""),
                "average_rating": calculate_average_rating(dest["dest_id"]),
                "user_rating": item.get("rating"),
                "interaction_type": item.get("interaction_type")
            })

    return jsonify(results)

# ===============================
# SEARCH DESTINATIONS
# ===============================
@app.route("/search", methods=["GET"])
def search_destinations():

    query = request.args.get("q", "").strip()

    if not query:
        return jsonify([])

    search_filter = {
        "$or": [
            {"name": {"$regex": query, "$options": "i"}},
            {"district": {"$regex": query, "$options": "i"}},
            {"category": {"$regex": query, "$options": "i"}},
            {"description": {"$regex": query, "$options": "i"}}
        ]
    }

    results = list(db.destination.find(search_filter, {"_id": 0}))

    for dest in results:
        dest["average_rating"] = calculate_average_rating(dest["dest_id"])
        dest["image_url"] = dest.get("image_url", "")

    return jsonify(results)

@app.route("/")
def home():
    return jsonify({"message": "TourMate Backend Running"})

@app.route("/admin/model-status", methods=["GET"])
@jwt_required()
def model_status():

    try:
        # Basic model checks
        collaborative_loaded = collaborative_model is not None
        lstm_loaded = lstm_model is not None

        # DB stats
        destination_count = db.destination.count_documents({})
        interaction_count = db.user_interaction.count_documents({})
        inflow_count = db.tn_inflow.count_documents({})

        # Cache info
        if district_cache["data"] is not None:
            cache_size = len(district_cache["data"])
            cache_last_updated = datetime.fromtimestamp(
                district_cache["last_updated"]
            ).strftime("%Y-%m-%d %H:%M:%S")

            cache_age = int(time.time() - district_cache["last_updated"])
        else:
            cache_size = 0
            cache_last_updated = None
            cache_age = None

        return jsonify({
            "collaborative_model_loaded": collaborative_loaded,
            "lstm_model_loaded": lstm_loaded,
            "destination_count": destination_count,
            "interaction_count": interaction_count,
            "inflow_records": inflow_count,
            "district_cached": cache_size,
            "cache_last_updated": cache_last_updated,
            "cache_age_seconds": cache_age
        })

    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500

if __name__ == "__main__":
    app.run(debug=True)