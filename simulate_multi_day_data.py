# simulate_multi_day_data.py

import asyncio
from datetime import datetime, timedelta
from prisma import Prisma

async def main():
    prisma = Prisma()
    await prisma.connect()
    print("✅ Connected to database.")

    # Fetch all detection records
    records = await prisma.detectionrecord.find_many()
    print(f"📊 Found {len(records)} records to update.")

    if not records:
        print("❌ No records found.")
        return

    # We will distribute the records over the last 5 days
    today = datetime.now().date()
    num_days = 5

    for i, record in enumerate(records):
        # Calculate a date to assign to this record
        days_ago = i % num_days
        new_date = today - timedelta(days=days_ago)
        
        # Create a new datetime object with the new date
        # We keep the original time component
        original_time = record.timestamp.time()
        new_timestamp = datetime.combine(new_date, original_time)

        # Update the record in the database
        await prisma.detectionrecord.update(
            where={'id': record.id},
            data={'timestamp': new_timestamp}
        )
        
        print(f"Updated record {record.id} to {new_timestamp.strftime('%Y-%m-%d')}")

    await prisma.disconnect()
    print("\n🎉 Simulation complete! Data is now spread across multiple days.")

if __name__ == "__main__":
    asyncio.run(main())
