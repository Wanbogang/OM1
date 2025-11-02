# agents/perception_agent/populate_historical_data.py

import os
import json
import cv2  # <-- TAMBAHKAN IMPORT INI
from prisma import Prisma
from opencv_perception_agent import OpenCVPerceptionAgent

# Inisialisasi Prisma Client
prisma = Prisma()

# Folder yang berisi gambar-gambar historis untuk diproses
HISTORICAL_IMAGES_DIR = "agents/perception_agent/assets/test_images"

# Koordinat dummy untuk simulasi
DEFAULT_LAT = -6.200000
DEFAULT_LNG = 106.816666

async def main():
    await prisma.connect()
    print("✅ Connected to database.")

    # Buat folder jika belum ada
    if not os.path.exists(HISTORICAL_IMAGES_DIR):
        print(f"❌ Directory '{HISTORICAL_IMAGES_DIR}' not found.")
        print(f"👉 Please create it and add some plant images (jpg, png) to populate the database.")
        await prisma.disconnect()
        return

    image_files = [f for f in os.listdir(HISTORICAL_IMAGES_DIR) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    
    if not image_files:
        print(f"❌ No images found in '{HISTORICAL_IMAGES_DIR}'. Please add some images.")
        await prisma.disconnect()
        return

    print(f"📁 Found {len(image_files)} images to process.")

    for image_name in image_files:
        image_path = os.path.join(HISTORICAL_IMAGES_DIR, image_name)
        print(f"\n🔍 Processing {image_name}...")

        # --- PERUBAHAN KRUSIAL DI SINI ---
        # 1. Buka gambar dari path menggunakan OpenCV
        image_data = cv2.imread(image_path)

        # 2. Cek apakah gambar berhasil dibuka
        if image_data is None:
            print(f"⚠️ Could not read image {image_name}. Skipping.")
            continue

        # 3. Buat instance agent dan proses data gambar (bukan path)
        agent = OpenCVPerceptionAgent()
        detection_result = agent.process_image(image_data)

        if detection_result and detection_result.get("detections"):
            best_detection = max(detection_result["detections"], key=lambda x: x['confidence'])
            
            await prisma.detectionrecord.create({
                'image_path': image_path,
                'disease_type': best_detection['disease_type'],
                'confidence': best_detection['confidence'],
                'coordinates': json.dumps(best_detection['bounding_box']), 
                'severity': best_detection['severity'],
                'latitude': DEFAULT_LAT + (len(image_files) * 0.001),
                'longitude': DEFAULT_LNG + (len(image_files) * 0.001),
            })
            print(f"✅ Saved detection for {image_name} ({best_detection['disease_type']})")
        else:
            print(f"⚠️ No disease detected in {image_name}")

    await prisma.disconnect()
    print("\n🎉 Historical data population complete!")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
