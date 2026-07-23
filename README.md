# Smart Tourism Recommendation System with LSTM-Based Tourist Inflow Prediction

## Overview

The Smart Tourism Recommendation System is an AI-powered web application that recommends tourist destinations based on user preferences and predicts future tourist inflow using a Long Short-Term Memory (LSTM) deep learning model.

The system combines content-based filtering, collaborative filtering, and LSTM time-series forecasting to provide personalized recommendations while helping tourism authorities understand future visitor trends.

---

## Objectives

- Recommend tourist destinations based on user interests.
- Predict future tourist inflow using LSTM.
- Improve travel planning with data-driven recommendations.
- Support tourism management through demand forecasting.

---

## Features

- User registration and login
- Personalized tourist place recommendations
- Content-Based Recommendation
- Collaborative Filtering Recommendation
- Hybrid Recommendation Model
- LSTM Tourist Inflow Prediction
- Tourist destination search
- District-wise tourist information
- Dashboard with analytics
- MongoDB database integration
- Responsive web interface

---

## Tech Stack

### Frontend
- HTML
- CSS
- JavaScript
- Bootstrap

### Backend
- Python
- Flask

### Machine Learning
- TensorFlow
- Keras
- Scikit-learn
- Pandas
- NumPy

### Database
- MongoDB

---

## Machine Learning Models

### Recommendation System
- Content-Based Filtering (TF-IDF)
- Collaborative Filtering
- Hybrid Recommendation

### Prediction Model
- Long Short-Term Memory (LSTM)

---

## Dataset

The dataset contains:

- Tourist Place Name
- District
- Category
- Description
- Ratings
- Monthly Tourist Inflow
- Seasonal Information
- Popularity Score

---

## System Architecture

```
User
   │
   ▼
Web Application
   │
   ▼
Recommendation Engine
(Content + Collaborative)
   │
   ▼
Hybrid Recommendation
   │
   ▼
LSTM Prediction Model
   │
   ▼
MongoDB Database
```

---

## Installation

### Clone Repository

```bash
git clone (https://github.com/Tamilselvan2026/LSTM_Project.git)
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Start MongoDB

```bash
mongod
```

### Run the Flask Application

```bash
python app.py
```

---

## Project Structure

```
Smart-Tourism-System/
│
├── app.py
├── requirements.txt
├── dataset/
├── models/
│   ├── recommendation.py
│   ├── lstm_model.py
│
├── static/
├── templates/
├── uploads/
├── README.md
└── trained_model/
```

---

## LSTM Model

- Framework: TensorFlow/Keras
- Model Type: Sequential
- Layers:
  - LSTM
  - Dropout
  - Dense
- Optimizer: Adam
- Loss Function: Mean Squared Error (MSE)
- Prediction: Monthly Tourist Inflow

---

## Evaluation Metrics

- Mean Absolute Error (MAE)
- Root Mean Square Error (RMSE)
- Model Accuracy

---

## Future Enhancements

- Weather-based recommendations
- Hotel recommendation
- Route optimization
- Real-time tourist prediction
- Mobile application
- Multi-language support
- Cloud deployment

---

## Authors

**Tamilselvan R**

B.E. Computer Science and Engineering

IFET College of Engineering

---

## License

This project is developed for academic and research purposes.

---

## Acknowledgements

- TensorFlow
- Keras
- Scikit-learn
- Flask
- MongoDB
- IFET College of Engineering
