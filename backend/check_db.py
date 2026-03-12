import asyncio
import aiomysql

async def check_table_structure():
    """Check the structure of the trips table"""
    conn = await aiomysql.connect(
        host='127.0.0.1',
        port=3306,
        user='root',
        password='123456',
        db='trailmark',
        charset='utf8mb4',
        autocommit=True
    )
    
    async with conn.cursor() as cur:
        # Check table structure
        await cur.execute("DESCRIBE trips;")
        rows = await cur.fetchall()
        print("Trips table structure:")
        for row in rows:
            print(row)
        
        # Check if there are any trips
        await cur.execute("SELECT COUNT(*) FROM trips;")
        count = await cur.fetchone()
        print(f"Number of trips: {count[0]}")
        
        # Check a sample trip
        if count[0] > 0:
            await cur.execute("SELECT * FROM trips LIMIT 1;")
            trip = await cur.fetchone()
            print(f"Sample trip: {trip}")
            print(f"Itinerary type: {type(trip[8])}")
            print(f"Itinerary value: {trip[8]}")
    
    conn.close()

if __name__ == "__main__":
    asyncio.run(check_table_structure())