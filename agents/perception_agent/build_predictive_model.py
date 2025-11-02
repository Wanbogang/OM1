# agents/perception_agent/build_predictive_model.py

import pandas as pd
from prisma import Prisma
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error
import joblib
import json

async def main():
    # 1. Ambil Data dari Database
    prisma = Prisma()
    await prisma.connect()
    print("✅ Connected to database.")

    records = await prisma.detectionrecord.find_many()
    await prisma.disconnect()
    print(f"📊 Found {len(records)} records in the database.")

    if not records:
        print("❌ No data found. Please run the populate script first.")
        return

    # 2. Feature Engineering
    data_list = [record.model_dump() for record in records]
    df = pd.DataFrame(data_list)

    # Ubah disease_type jadi angka dan simpan peta encoding-nya
    df['disease_type_encoded'], unique_diseases = pd.factorize(df['disease_type'])
    
    # Buat peta dari string disease ke angka
    disease_to_encoded_map = {disease: i for i, disease in enumerate(unique_diseases)}
    
    # Pilih fitur (X) dan target (y)
    features = ['disease_type_encoded']
    target = 'confidence'
    X = df[features]
    y = df[target]

    print("\n--- Data Sample ---")
    print(df[['disease_type', 'disease_type_encoded', 'confidence']].head())

    # 3. Split Data (Training & Testing)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # 4. Latih Model
    print("\n🤖 Training the Linear Regression model...")
    model = LinearRegression()
    model.fit(X_train, y_train)
    print("✅ Model training complete.")

    # 5. Evaluasi Model
    y_pred = model.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    print(f"\n📈 Model Evaluation:")
    print(f"Mean Squared Error: {mse:.4f}")

    # --- PERUBAHAN KRUSIAL: SIMPAN MODEL DAN PETA SEKARANG ---
    model_filename = 'disease_confidence_model.joblib'
    map_filename = 'disease_type_map.json'
    
    joblib.dump(model, model_filename)
    print(f"💾 Model saved to {model_filename}")

    with open(map_filename, 'w') as f:
        json.dump(disease_to_encoded_map, f)
    print(f"💾 Disease type mapping saved to {map_filename}")

    # --- PINDAHKAN CONTOH PREDIKSI KE PALING AKHIR ---
    print("\n🔮 Prediction Example (using saved model):")
    
    # Coba prediksi confidence untuk 'leaf_blight'
    if 'leaf_blight' in disease_to_encoded_map:
        encoded_type = disease_to_encoded_map['leaf_blight']
        prediction_df = pd.DataFrame([{'disease_type_encoded': encoded_type}])
        predicted_confidence = model.predict(prediction_df)
        print(f"Predicted confidence for 'leaf_blight': {predicted_confidence[0]:.2f}")
    else:
        print("Could not run prediction example: 'leaf_blight' not found in data.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
