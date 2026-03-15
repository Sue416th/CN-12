import { motion } from "framer-motion";
import { BarChart3, Database, Landmark, Users, ArrowRight } from "lucide-react";

const cards = [
  {
    icon: Landmark,
    title: "Cultural Destination Assets",
    desc: "Manage scenic spots, museums, and destination profiles.",
    value: "126",
  },
  {
    icon: Users,
    title: "User Insights",
    desc: "Track user behavior, visit trends, and engagement.",
    value: "18.4k",
  },
  {
    icon: Database,
    title: "Data Pipelines",
    desc: "Monitor ETL sync status for culture and tourism datasets.",
    value: "12",
  },
  {
    icon: BarChart3,
    title: "Visualization Reports",
    desc: "View key indicators and real-time operational metrics.",
    value: "24",
  },
];

const AdminDashboard = () => {
  return (
    <div className="container max-w-6xl mx-auto px-6 py-8">
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="rounded-2xl bg-primary text-primary-foreground p-7"
      >
        <h1 className="text-2xl font-display font-bold">Admin Console</h1>
        <p className="mt-2 text-sm text-primary-foreground/80">
          Welcome to the culture and tourism management backend. Use this panel to manage data and drive visualization-based decisions.
        </p>
      </motion.div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-5 mt-6">
        {cards.map((card, index) => (
          <motion.div
            key={card.title}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.08 }}
            className="rounded-xl border border-border/50 bg-card p-5 shadow-sm"
          >
            <div className="flex items-start justify-between">
              <div className="w-10 h-10 rounded-lg bg-primary/10 text-primary flex items-center justify-center">
                <card.icon className="w-5 h-5" />
              </div>
              <p className="text-xl font-semibold font-display">{card.value}</p>
            </div>
            <h2 className="mt-4 font-display font-semibold">{card.title}</h2>
            <p className="mt-1.5 text-sm text-muted-foreground">{card.desc}</p>
            <button className="mt-4 inline-flex items-center gap-1.5 text-sm text-primary hover:underline">
              Open Module <ArrowRight className="w-4 h-4" />
            </button>
          </motion.div>
        ))}
      </div>
    </div>
  );
};

export default AdminDashboard;
