const http = require('http');

const data = JSON.stringify({
  user_id: 4,
  city: "Hangzhou",
  start_date: "2026-03-20",
  days: 3,
  profile: {
    interests: ["culture", "food", "nature"],
    budget_level: "medium",
    travel_style: "balanced",
    group_type: "solo",
    fitness_level: "medium"
  }
});

const options = {
  hostname: '127.0.0.1',
  port: 3204,
  path: '/api/trip/create',
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Content-Length': data.length
  }
};

const req = http.request(options, (res) => {
  let body = '';
  res.on('data', (chunk) => { body += chunk; });
  res.on('end', () => {
    const result = JSON.parse(body);
    if (result.success) {
      const itinerary = result.trip.itinerary;
      console.log("=== Trip for user with interests:", result.trip.profile.interests);
      console.log("=== Preferred categories:", result.trip.profile.preferred_categories);
      console.log("=== Budget:", result.trip.profile.budget_level);
      console.log("=== Fitness:", result.trip.profile.fitness_level);
      console.log("");
      
      itinerary.days.forEach(day => {
        console.log(`Day ${day.day}:`);
        day.activities.forEach(act => {
          console.log(`  - ${act.name} (${act.category})`);
        });
        console.log("");
      });
    } else {
      console.log("Error:", result);
    }
  });
});

req.on('error', (error) => { console.error('Error:', error.message); });
req.write(data);
req.end();
