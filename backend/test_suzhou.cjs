const http = require('http');

const data = JSON.stringify({
  user_id: 4,
  city: "Suzhou",  // 只有3个景点
  start_date: "2026-03-20",
  days: 3,
  profile: {
    interests: ["culture"],
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
      console.log("=== City: Suzhou (only 3 POIs) ===");
      console.log("=== Days requested: 3 ===");
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
