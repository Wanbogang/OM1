# agents/perception_agent/predictor.py

import pandas as pd
import joblib
import json
import os

# Global variables untuk menyimpan model dan peta
_model = None
_disease_map = None

def load_model():
    """Memuat model dan peta encoding dari file."""
    global _model, _disease_map
    
    # Cek apakah sudah dimuat
    if _model is not None and _disease_map is not None:
        return True

    # Path ke file model dan peta (RELATIF TERHADAP LOKASI FILE INI)
    # Karena app.py dan predictor.py berada di folder yang sama
    model_path = 'disease_confidence_model.joblib'
    map_path = 'disease_type_map.json'
    
    # Cek apakah file ada
    if not os.path.exists(model_path) or not os.path.exists(map_path):
        print(f"❌ Model or mapping file not found. Looking for '{model_path}' and '{map_path}'. Please run the training script first.")
        return False

    try:
        # Muat model dan peta
        _model = joblib.load(model_path)
        with open(map_path, 'r') as f:
            _disease_map = json.load(f)
        print("✅ Model and mapping loaded successfully.")
        return True
    except Exception as e:
        print(f"❌ Error loading model or mapping: {e}")
        return False

def predict_confidence(disease_type: str):
    """Memprediksi confidence berdasarkan tipe penyakit."""
    
    # Pastikan model sudah dimuat
    if not load_model():
        return None

    # Cek apakah tipe penyakit dikenali
    if disease_type not in _disease_map:
        print(f"⚠️ Unknown disease type: {disease_type}")
        print(f"Available disease types: {list(_disease_map.keys())}") # <-- Tambahkan ini untuk debugging
        return None

    # Ubah string disease jadi angka
    encoded_type = _disease_map[disease_type]
    
    # Buat DataFrame untuk prediksi
    prediction_df = pd.DataFrame([{'disease_type_encoded': encoded_type}])
    
    # Lakukan prediksi
    predicted_confidence = _model.predict(prediction_df)
    
    return predicted_confidence[0]
