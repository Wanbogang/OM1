import asyncio
import random
from datetime import datetime, timedelta
from prisma import Prisma
from opencv_perception_agent import OpenCVPerceptionAgent

async def main():
    """
    Populates the database with FAKE historical detection data for analytics.
    This version bypasses image processing entirely for speed and reliability.
    """
    print("🔌 Using .env.dev for database connection.")
    db = Prisma()
    agent = OpenCVPerceptionAgent()

    try:
        await db.connect()
        print("✅ Connected to database.")

        # --- We don't need images anymore, we'll create data directly ---
        print("🔧 Generating fake historical data...")
        
        # List of possible diseases to detect
        disease_types = ["Leaf Blight", "Powdery Mildew", "Leaf Spot", "Rust", "Healthy"]
        
        # Let's create 20 fake historical records
        num_records_to_create = 20
        for i in range(num_records_to_create):
            print(f"🔍 Creating fake record {i+1}/{num_records_to_create}...")

            # Generate fake data
            disease_type = random.choice(disease_types)
            confidence = round(random.uniform(0.75, 0.98), 2)
            severity = random.choice(['mild', 'moderate', 'severe'])
            
            # Generate fake coordinates
            latitude = round(random.uniform(-6.5, -6.2), 6)
            longitude = round(random.uniform(106.7, 106.9), 6)
            
            # Generate a fake timestamp within the last 30 days
            fake_timestamp = datetime.now() - timedelta(days=random.randint(0, 30))
            
            # Save the fake data to the database
            await db.detectionrecord.create(
                data={
                    'disease_type': disease_type,
                    'confidence': confidence,
                    'latitude': latitude,
                    'longitude': longitude,
                    'image_path': f'fake_image_{i+1}.jpg',
                    'timestamp': fake_timestamp
                }
            )
            print(f"✅ Saved fake record: {disease_type} with confidence {confidence}")

        print("🎉 Fake historical data population complete!")

    except Exception as e:
        print(f"❌ An error occurred: {e}")
    finally:
        await db.disconnect()
        print("🔌 Disconnected from database.")

if __name__ == "__main__":
    asyncio.run(main())
