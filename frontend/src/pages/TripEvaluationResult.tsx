import { useEffect, useState } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";
import { motion } from "framer-motion";
import { CheckCircle2, ChevronLeft, Sparkles, AlertTriangle, Lightbulb, BarChart3, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import axios from "axios";
import { useAuth } from "@/context/AuthContext";

type EvaluationState = {
  tripTitle: string;
  analysis: {
    sentiment: string;
    score: number;
    summary: string;
    issues_detected: string[];
    user_suggestions: string[];
    system_suggestions: string[];
  };
  feedback: {
    overall_satisfaction: number;
    crowded_level: string;
    schedule_reasonable: string;
    transportation_convenience: string;
    review: string;
  };
};

const TripEvaluationResult = () => {
  const navigate = useNavigate();
  const { tripId } = useParams<{ tripId: string }>();
  const location = useLocation();
  const { user } = useAuth();
  const state = location.state as EvaluationState | null;
  const [evaluation, setEvaluation] = useState<EvaluationState | null>(state);
  const [loading, setLoading] = useState(!state);

  useEffect(() => {
    if (state) {
      setEvaluation(state);
      setLoading(false);
      return;
    }
    if (!tripId || !user) {
      setLoading(false);
      return;
    }

    const fetchEvaluation = async () => {
      try {
        const response = await axios.get(
          `http://localhost:3204/api/trip/evaluate/${tripId}?user_id=${user.id}`,
        );
        const data = response.data;
        setEvaluation({
          tripTitle: data.trip_title || `Trip ${tripId}`,
          analysis: data.analysis,
          feedback: data.feedback,
        });
      } catch (_error) {
        setEvaluation(null);
      } finally {
        setLoading(false);
      }
    };

    void fetchEvaluation();
  }, [state, tripId, user]);

  if (loading) {
    return (
      <div className="container max-w-4xl mx-auto px-6 py-14">
        <div className="flex items-center justify-center">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
        </div>
      </div>
    );
  }

  if (!evaluation) {
    return (
      <div className="container max-w-4xl mx-auto px-6 py-10">
        <Card>
          <CardHeader>
            <CardTitle>No evaluation data found</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-muted-foreground mb-4">
              Please complete a trip review first.
            </p>
            <Button onClick={() => navigate("/trips")}>Back to My Trips</Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const { tripTitle, analysis, feedback } = evaluation;
  const scorePercent = Math.round((analysis.score || 0) * 100);

  const sentimentTone =
    analysis.sentiment === "positive"
      ? "bg-green-100 text-green-700 border-green-200"
      : analysis.sentiment === "negative"
        ? "bg-red-100 text-red-700 border-red-200"
        : "bg-amber-100 text-amber-700 border-amber-200";

  return (
    <div className="container max-w-5xl mx-auto px-6 py-8">
      <div className="flex items-center gap-3 mb-6">
        <Button variant="ghost" size="icon" onClick={() => navigate("/trips")}>
          <ChevronLeft className="w-5 h-5" />
        </Button>
        <div>
          <h1 className="text-2xl font-display font-semibold">Trip Evaluation Agent</h1>
          <p className="text-sm text-muted-foreground">{tripTitle}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="lg:col-span-2 space-y-5">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-primary" />
                AI Analysis Summary
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center gap-3">
                <Badge className={`border ${sentimentTone}`}>{analysis.sentiment}</Badge>
                <span className="text-sm text-muted-foreground">Satisfaction score: {scorePercent}%</span>
              </div>
              <p className="text-sm leading-6">{analysis.summary}</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-amber-500" />
                Detected Issues
              </CardTitle>
            </CardHeader>
            <CardContent>
              {analysis.issues_detected?.length ? (
                <ul className="space-y-2 text-sm">
                  {analysis.issues_detected.map((issue, idx) => (
                    <li key={idx} className="rounded-lg bg-muted/50 px-3 py-2">{issue}</li>
                  ))}
                </ul>
              ) : (
                <p className="text-sm text-muted-foreground">No major issues detected.</p>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2">
                <Lightbulb className="w-5 h-5 text-primary" />
                Suggestions
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <p className="text-sm font-medium mb-2">For Traveler</p>
                <ul className="space-y-2 text-sm">
                  {(analysis.user_suggestions?.length ? analysis.user_suggestions : ["Keep current travel strategy and continue exploring."]).map((tip, idx) => (
                    <li key={idx} className="rounded-lg bg-muted/40 px-3 py-2">{tip}</li>
                  ))}
                </ul>
              </div>
              <div>
                <p className="text-sm font-medium mb-2">For System Optimization</p>
                <ul className="space-y-2 text-sm">
                  {(analysis.system_suggestions?.length ? analysis.system_suggestions : ["No optimization suggestions."]).map((tip, idx) => (
                    <li key={idx} className="rounded-lg bg-muted/40 px-3 py-2">{tip}</li>
                  ))}
                </ul>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.05 }}>
          <Card className="sticky top-24">
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="w-5 h-5 text-primary" />
                Submitted Feedback
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Overall Satisfaction</span>
                <span>{feedback.overall_satisfaction}/5</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Crowded Level</span>
                <span>{feedback.crowded_level}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Schedule Reasonable</span>
                <span>{feedback.schedule_reasonable}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Transportation</span>
                <span>{feedback.transportation_convenience}</span>
              </div>
              <div className="pt-2 border-t border-border/50">
                <p className="text-muted-foreground mb-1">Review</p>
                <p>{feedback.review}</p>
              </div>
              <Button className="w-full mt-2" onClick={() => navigate("/trips")}>
                <CheckCircle2 className="w-4 h-4 mr-1.5" />
                Back to My Trips
              </Button>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </div>
  );
};

export default TripEvaluationResult;

