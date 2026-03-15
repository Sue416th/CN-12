import beijingImage from "@/assets/cities/beijing.png";
import chengduImage from "@/assets/cities/chengdu.png";
import daliImage from "@/assets/cities/dali.png";
import hangzhouImage from "@/assets/cities/hangzhou.png";
import jiuzhaigouImage from "@/assets/cities/jiuzhaigou.png";
import shanghaiImage from "@/assets/cities/shanghai.png";

export type DestinationAttraction = {
  name: string;
  category: string;
  description: string;
  best_time: string;
  duration: string;
  price: number;
  crowd_level: string;
};

export type Destination = {
  id: string;
  name: string;
  location: string;
  country: string;
  shortDescription: string;
  description: string;
  image: string;
  highlights: string[];
  best_season: string;
  recommended_days: string;
  tags: string[];
  attractions: DestinationAttraction[];
};

export const DESTINATIONS: Destination[] = [
  {
    id: "dali",
    name: "Dali",
    location: "Yunnan",
    country: "China",
    shortDescription: "Ancient town charm, Erhai Lake cycling, and Bai culture.",
    description:
      "Dali blends old-town architecture, mountain scenery, and local ethnic culture. It is ideal for slow travel, lakeside experiences, and heritage exploration.",
    image: daliImage,
    highlights: ["Dali Old Town", "Erhai Lake", "Three Pagodas", "Cangshan Mountain"],
    best_season: "Mar-May, Sep-Nov",
    recommended_days: "3-5 days",
    tags: ["Culture", "Lake", "Slow Travel"],
    attractions: [
      {
        name: "Erhai Lake",
        category: "Nature",
        description: "Scenic lake loop with villages and sunset viewpoints.",
        best_time: "Morning / Sunset",
        duration: "2-3 hours",
        price: 0,
        crowd_level: "Medium",
      },
      {
        name: "Dali Old Town",
        category: "Culture",
        description: "Historic district with local food streets and craft shops.",
        best_time: "Evening",
        duration: "2-4 hours",
        price: 0,
        crowd_level: "High",
      },
      {
        name: "Three Pagodas",
        category: "History",
        description: "Iconic Tang-era pagodas and Buddhist architecture.",
        best_time: "Morning",
        duration: "1-2 hours",
        price: 75,
        crowd_level: "Medium",
      },
    ],
  },
  {
    id: "beijing",
    name: "Beijing",
    location: "Beijing",
    country: "China",
    shortDescription: "Imperial heritage, the Great Wall, and classic landmarks.",
    description:
      "Beijing offers a rich timeline of Chinese history through palaces, city gates, and world-famous monuments, combined with modern urban life.",
    image: beijingImage,
    highlights: ["Great Wall", "Forbidden City", "Temple of Heaven", "Summer Palace"],
    best_season: "Apr-May, Sep-Oct",
    recommended_days: "4-7 days",
    tags: ["History", "Architecture", "Capital City"],
    attractions: [
      {
        name: "Great Wall",
        category: "History",
        description: "One of the world most iconic fortifications.",
        best_time: "Morning",
        duration: "3-5 hours",
        price: 65,
        crowd_level: "High",
      },
      {
        name: "Forbidden City",
        category: "History",
        description: "Imperial palace complex of Ming and Qing dynasties.",
        best_time: "Morning",
        duration: "2-4 hours",
        price: 60,
        crowd_level: "High",
      },
      {
        name: "Summer Palace",
        category: "Culture",
        description: "Lakeside imperial garden with pavilions and corridors.",
        best_time: "Afternoon",
        duration: "2-3 hours",
        price: 60,
        crowd_level: "Medium",
      },
    ],
  },
  {
    id: "jiuzhaigou",
    name: "Jiuzhaigou Valley",
    location: "Sichuan",
    country: "China",
    shortDescription: "UNESCO natural wonder with multicolor alpine lakes.",
    description:
      "Jiuzhaigou is known for turquoise lakes, waterfalls, and mountain forests. It is among the most photogenic nature reserves in China.",
    image: jiuzhaigouImage,
    highlights: ["Five Flower Lake", "Nuorilang Waterfall", "Long Lake", "Rize Valley"],
    best_season: "Sep-Nov",
    recommended_days: "2-4 days",
    tags: ["Nature", "Photography", "UNESCO"],
    attractions: [
      {
        name: "Five Flower Lake",
        category: "Nature",
        description: "Clear layered colors and exceptional reflections.",
        best_time: "Morning",
        duration: "1-2 hours",
        price: 170,
        crowd_level: "High",
      },
      {
        name: "Nuorilang Waterfall",
        category: "Nature",
        description: "Wide multi-tier waterfall and signature photo spot.",
        best_time: "Morning / Afternoon",
        duration: "1-2 hours",
        price: 0,
        crowd_level: "High",
      },
    ],
  },
  {
    id: "hangzhou",
    name: "Hangzhou",
    location: "Zhejiang",
    country: "China",
    shortDescription: "West Lake poetry, tea culture, and elegant city views.",
    description:
      "Hangzhou is famous for serene lake landscapes, tea plantations, and long-standing Jiangnan aesthetics.",
    image: hangzhouImage,
    highlights: ["West Lake", "Lingyin Temple", "Longjing Tea Village", "Leifeng Pagoda"],
    best_season: "Mar-May, Sep-Nov",
    recommended_days: "2-4 days",
    tags: ["Lake", "Culture", "Tea"],
    attractions: [
      {
        name: "West Lake",
        category: "Nature",
        description: "Historic lake with causeways, boats, and gardens.",
        best_time: "Morning / Sunset",
        duration: "2-4 hours",
        price: 0,
        crowd_level: "Medium",
      },
      {
        name: "Lingyin Temple",
        category: "Culture",
        description: "Ancient Buddhist temple complex with stone carvings.",
        best_time: "Morning",
        duration: "1-2 hours",
        price: 45,
        crowd_level: "Medium",
      },
    ],
  },
  {
    id: "shanghai",
    name: "Shanghai",
    location: "Shanghai",
    country: "China",
    shortDescription: "Modern skyline, riverfront walks, and food streets.",
    description:
      "Shanghai combines international urban architecture with traditional lanes, vibrant nightlife, and rich culinary options.",
    image: shanghaiImage,
    highlights: ["The Bund", "Yu Garden", "Nanjing Road", "Shanghai Museum"],
    best_season: "Mar-May, Oct-Nov",
    recommended_days: "3-5 days",
    tags: ["City", "Food", "Night View"],
    attractions: [
      {
        name: "The Bund",
        category: "Culture",
        description: "Historic waterfront promenade and skyline viewpoint.",
        best_time: "Evening",
        duration: "1-2 hours",
        price: 0,
        crowd_level: "High",
      },
      {
        name: "Shanghai Museum",
        category: "History",
        description: "Top collections of Chinese art and artifacts.",
        best_time: "Morning",
        duration: "2-3 hours",
        price: 0,
        crowd_level: "Medium",
      },
    ],
  },
  {
    id: "chengdu",
    name: "Chengdu",
    location: "Sichuan",
    country: "China",
    shortDescription: "Pandas, tea houses, and relaxed local lifestyle.",
    description:
      "Chengdu is known for giant pandas, spicy cuisine, and a laid-back pace that blends history with modern neighborhoods.",
    image: chengduImage,
    highlights: ["Panda Base", "Jinli Street", "Wenshu Monastery", "Kuanzhai Alleys"],
    best_season: "Mar-Jun, Sep-Nov",
    recommended_days: "3-5 days",
    tags: ["Food", "Panda", "Culture"],
    attractions: [
      {
        name: "Chengdu Panda Base",
        category: "Nature",
        description: "Flagship giant panda conservation and observation center.",
        best_time: "Morning",
        duration: "2-3 hours",
        price: 55,
        crowd_level: "High",
      },
      {
        name: "Jinli Street",
        category: "Culture",
        description: "Traditional commercial street with local snacks.",
        best_time: "Evening",
        duration: "1-2 hours",
        price: 0,
        crowd_level: "High",
      },
    ],
  },
];

export const DESTINATIONS_MAP: Record<string, Destination> = DESTINATIONS.reduce(
  (acc, item) => {
    acc[item.id] = item;
    return acc;
  },
  {} as Record<string, Destination>,
);

export const getDestinationById = (destinationId?: string) => {
  if (!destinationId) return null;
  return DESTINATIONS_MAP[destinationId] || null;
};

