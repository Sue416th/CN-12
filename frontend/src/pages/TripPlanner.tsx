import { useState } from "react";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { ChevronLeft, MapPin, Calendar, Users, Footprints, DollarSign, Sparkles, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import axios from "axios";

const INTERESTS = [
  { id: "culture", label: "Culture & History", icon: "🏛️", tags: ["museum", "art", "history", "heritage"] },
  { id: "food", label: "Food & Cuisine", icon: "🍜", tags: ["local cuisine", "street food", "foodie"] },
  { id: "nature", label: "Nature & Scenery", icon: "🏞️", tags: ["park", "mountain", "lake", "hiking"] },
  { id: "religion", label: "Religion & Temples", icon: "⛩️", tags: ["temple", "shrine", "meditation"] },
  { id: "entertainment", label: "Entertainment", icon: "🎭", tags: ["show", "theme park", "nightlife"] },
  { id: "shopping", label: "Shopping", icon: "🛍️", tags: ["market", "mall", "souvenirs"] },
  { id: "photography", label: "Photography", icon: "📷", tags: ["photo", "sunset", "landscape"] },
  { id: "sports", label: "Sports & Adventure", icon: "🏃", tags: ["hiking", "cycling", "adventure"] },
  { id: "wellness", label: "Wellness & Relaxation", icon: "🧘", tags: ["spa", "hot spring", "yoga"] },
];

const CITIES = [
  { id: "hangzhou", label: "Hangzhou", desc: "West Lake & Tea Culture" },
  { id: "dali", label: "Dali", desc: "Erhai Lake & Ancient Town" },
  { id: "beijing", label: "Beijing", desc: "Imperial Capital & Great Wall" },
  { id: "xian", label: "Xi'an", desc: "Terracotta Warriors" },
  { id: "suzhou", label: "Suzhou", desc: "Classical Gardens" },
  { id: "chengdu", label: "Chengdu", desc: "Pandas & Spicy Food" },
];

const TripPlanner = () => {
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);

  // Get today's date in YYYY-MM-DD format
  const getTodayDate = () => {
    const today = new Date();
    return today.toISOString().split('T')[0];
  };

  const [formData, setFormData] = useState({
    city: "hangzhou",
    days: 3,
    startDate: getTodayDate(), // Default to today
    interests: [] as string[],
    budgetLevel: "medium",
    travelStyle: "balanced",
    groupType: "solo",
    fitnessLevel: "medium",
    ageGroup: "adult",
    hasChildren: false,
    priceSensitivity: 0.5,
  });
  const [generatedTrip, setGeneratedTrip] = useState<any>(null);

  const handleInterestToggle = (interestId: string) => {
    setFormData(prev => ({
      ...prev,
      interests: prev.interests.includes(interestId)
        ? prev.interests.filter(i => i !== interestId)
        : [...prev.interests, interestId]
    }));
  };

  const handleSubmit = async () => {
    setLoading(true);
    try {
      const response = await axios.post("http://localhost:3002/api/trip/create", {
        user_id: 1,
        city: formData.city,
        start_date: formData.startDate,
        days: formData.days,
        profile: {
          interests: formData.interests,
          budget_level: formData.budgetLevel,
          travel_style: formData.travelStyle,
          group_type: formData.groupType,
          fitness_level: formData.fitnessLevel,
          age_group: formData.ageGroup,
          has_children: formData.hasChildren,
          price_sensitivity: formData.priceSensitivity,
        }
      });

      if (response.data.success) {
        setGeneratedTrip(response.data.trip);
        setStep(3);
      }
    } catch (error) {
      console.error("Failed to create trip:", error);
      alert("Failed to create trip. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleBack = () => {
    if (step > 1) {
      setStep(step - 1);
    } else {
      navigate("/");
    }
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="border-b bg-card/50 backdrop-blur-sm sticky top-0 z-10">
        <div className="container max-w-4xl mx-auto px-6 py-4">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="icon" onClick={handleBack}>
              <ChevronLeft className="w-5 h-5" />
            </Button>
            <div>
              <h1 className="text-xl font-display font-semibold">Trip Planner</h1>
              <p className="text-sm text-muted-foreground">Create your personalized itinerary</p>
            </div>
          </div>
        </div>
      </div>

      <div className="container max-w-4xl mx-auto px-6 py-8">
        {/* Progress Steps */}
        <div className="flex items-center justify-center gap-4 mb-8">
          {[1, 2, 3].map((s) => (
            <div key={s} className="flex items-center">
              <div className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-medium transition-colors ${
                step >= s ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"
              }`}>
                {step > s ? "✓" : s}
              </div>
              {s < 3 && (
                <div className={`w-16 h-0.5 mx-2 ${step > s ? "bg-primary" : "bg-muted"}`} />
              )}
            </div>
          ))}
        </div>

        {/* Step 1: Basic Info */}
        {step === 1 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
          >
            <Card>
              <CardHeader>
                <CardTitle>Where do you want to go?</CardTitle>
                <CardDescription>Select your destination</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                  {CITIES.map((city) => (
                    <button
                      key={city.id}
                      onClick={() => setFormData(prev => ({ ...prev, city: city.id }))}
                      className={`p-4 rounded-lg border-2 text-left transition-all ${
                        formData.city === city.id
                          ? "border-primary bg-primary/5"
                          : "border-border hover:border-primary/50"
                      }`}
                    >
                      <div className="font-medium">{city.label}</div>
                      <div className="text-xs text-muted-foreground">{city.desc}</div>
                    </button>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>When and how long?</CardTitle>
                <CardDescription>Plan your travel dates</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium mb-2 block">Start Date</label>
                    <input
                      type="date"
                      value={formData.startDate}
                      onChange={(e) => setFormData(prev => ({ ...prev, startDate: e.target.value }))}
                      className="w-full p-2.5 rounded-lg border border-border bg-background"
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium mb-2 block">Duration (days)</label>
                    <select
                      value={formData.days}
                      onChange={(e) => setFormData(prev => ({ ...prev, days: Number(e.target.value) }))}
                      className="w-full p-2.5 rounded-lg border border-border bg-background"
                    >
                      {[1, 2, 3, 4, 5, 6, 7].map(d => (
                        <option key={d} value={d}>{d} day{d > 1 ? "s" : ""}</option>
                      ))}
                    </select>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Button
              size="lg"
              onClick={() => setStep(2)}
              disabled={!formData.city || !formData.startDate}
              className="w-full"
            >
              Continue to Preferences
            </Button>
          </motion.div>
        )}

        {/* Step 2: User Profile */}
        {step === 2 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
          >
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-primary" />
                  What are your interests?
                </CardTitle>
                <CardDescription>Select all that apply to you</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                  {INTERESTS.map((interest) => (
                    <button
                      key={interest.id}
                      onClick={() => handleInterestToggle(interest.id)}
                      className={`p-3 rounded-lg border-2 text-left transition-all ${
                        formData.interests.includes(interest.id)
                          ? "border-primary bg-primary/5"
                          : "border-border hover:border-primary/50"
                      }`}
                    >
                      <span className="text-xl">{interest.icon}</span>
                      <span className="ml-2 font-medium">{interest.label}</span>
                    </button>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <DollarSign className="w-5 h-5 text-primary" />
                  Budget Level
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-3 gap-3">
                  {[
                    { id: "low", label: "Budget", desc: "Hostels, street food" },
                    { id: "medium", label: "Comfort", desc: "Hotels, local restaurants" },
                    { id: "high", label: "Luxury", desc: "5-star hotels, fine dining" }
                  ].map((level) => (
                    <button
                      key={level.id}
                      onClick={() => setFormData(prev => ({ ...prev, budgetLevel: level.id }))}
                      className={`p-4 rounded-lg border-2 text-center transition-all ${
                        formData.budgetLevel === level.id
                          ? "border-primary bg-primary/5"
                          : "border-border hover:border-primary/50"
                      }`}
                    >
                      <div className="font-medium">{level.label}</div>
                      <div className="text-xs text-muted-foreground">{level.desc}</div>
                    </button>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Users className="w-5 h-5 text-primary" />
                  Travel Style
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div>
                    <label className="text-sm font-medium mb-2 block">Group Type</label>
                    <select
                      value={formData.groupType}
                      onChange={(e) => setFormData(prev => ({ ...prev, groupType: e.target.value }))}
                      className="w-full p-2.5 rounded-lg border border-border bg-background"
                    >
                      <option value="solo">Solo</option>
                      <option value="couple">Couple</option>
                      <option value="family">Family</option>
                      <option value="friends">Friends</option>
                      <option value="business">Business</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-sm font-medium mb-2 block">Travel Style</label>
                    <select
                      value={formData.travelStyle}
                      onChange={(e) => setFormData(prev => ({ ...prev, travelStyle: e.target.value }))}
                      className="w-full p-2.5 rounded-lg border border-border bg-background"
                    >
                      <option value="relaxed">Relaxed</option>
                      <option value="balanced">Balanced</option>
                      <option value="intensive">Intensive</option>
                    </select>
                  </div>
                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">Fitness Level</label>
                  <div className="grid grid-cols-3 gap-3">
                    {[
                      { id: "low", label: "Light", desc: "Prefers easy activities" },
                      { id: "medium", label: "Moderate", desc: "Can walk for hours" },
                      { id: "high", label: "Active", desc: "Loves adventure" }
                    ].map((level) => (
                      <button
                        key={level.id}
                        onClick={() => setFormData(prev => ({ ...prev, fitnessLevel: level.id }))}
                        className={`p-3 rounded-lg border-2 text-center transition-all ${
                          formData.fitnessLevel === level.id
                            ? "border-primary bg-primary/5"
                            : "border-border hover:border-primary/50"
                        }`}
                      >
                        <div className="font-medium">{level.label}</div>
                        <div className="text-xs text-muted-foreground">{level.desc}</div>
                      </button>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>

            <div className="flex gap-4">
              <Button variant="outline" size="lg" onClick={() => setStep(1)} className="flex-1">
                Back
              </Button>
              <Button size="lg" onClick={handleSubmit} disabled={loading} className="flex-1">
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Generating...
                  </>
                ) : (
                  "Generate My Trip"
                )}
              </Button>
            </div>
          </motion.div>
        )}

        {/* Step 3: Result */}
        {step === 3 && generatedTrip && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
          >
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-2xl">{generatedTrip.title}</CardTitle>
                    <CardDescription className="mt-1">
                      {generatedTrip.city.charAt(0).toUpperCase() + generatedTrip.city.slice(1)} - {generatedTrip.days} days
                    </CardDescription>
                  </div>
                  <Badge variant="outline" className="text-lg py-1 px-3">
                    {generatedTrip.status}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-6">
                  {generatedTrip.itinerary?.days?.map((day: any, index: number) => (
                    <div key={index} className="border rounded-lg overflow-hidden">
                      <div className="bg-muted/50 px-4 py-2 flex items-center justify-between">
                        <span className="font-medium">Day {day.day}</span>
                        <span className="text-sm text-muted-foreground">{day.date}</span>
                      </div>
                      <div className="p-4 space-y-3">
                        {day.activities.map((activity: any, actIndex: number) => (
                          <div key={actIndex} className="flex gap-3">
                            <div className="w-2 h-2 rounded-full bg-primary mt-2 flex-shrink-0" />
                            <div>
                              <div className="font-medium">{activity.name}</div>
                              <div className="text-sm text-muted-foreground">
                                {activity.time_needed}h • {activity.tips}
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <div className="flex gap-4">
              <Button variant="outline" size="lg" onClick={() => setStep(2)} className="flex-1">
                Modify Preferences
              </Button>
              <Button size="lg" onClick={() => navigate("/trips")} className="flex-1">
                View All My Trips
              </Button>
            </div>
          </motion.div>
        )}
      </div>
    </div>
  );
};

export default TripPlanner;
