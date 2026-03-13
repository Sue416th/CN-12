import requests
import json

response = requests.post('http://127.0.0.1:3204/api/trip/create', json={
    "user_id": 1,
    "city": "Hangzhou",
    "start_date": "2026-03-20",
    "days": 3,
    "profile": {
        "interests": ["culture", "food", "nature"],
        "budget_level": "medium",
        "travel_style": "balanced",
        "group_type": "solo",
        "fitness_level": "medium"
    }
})

data = response.json()
if data.get('success'):
    trip = data.get('trip', {})
    print("Trip:", trip.get('title'))
    print("City:", trip.get('city'))
    print("Days:", trip.get('days'))
    print()
    
    itinerary = trip.get('itinerary', {})
    days = itinerary.get('days', [])
    
    all_names = []
    for day in days:
        print(f"=== Day {day.get('day')} - {day.get('date')} ===")
        activities = day.get('activities', [])
        for activity in activities:
            name = activity.get('name')
            category = activity.get('category')
            time_needed = activity.get('time_needed')
            has_image = bool(activity.get('image'))
            print(f"  - {name} ({category}) - {time_needed}h - Image: {has_image}")
            all_names.append(name)
        print()
    
    # Check for duplicates
    print("Checking for duplicates...")
    unique_names = set(all_names)
    if len(all_names) != len(unique_names):
        print("WARNING: Duplicate activities found!")
    else:
        print("SUCCESS: No duplicate activities!")
else:
    print("Error:", data)
