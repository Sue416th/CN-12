from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from app.agents.base_agent import BaseAgent
from app.models.poi import POI

CULTURE_INFO = {
    "West Lake": {
        "dynasty": "Tang & Song",
        "famous_poems": ["Like the West Lake, compare to Xizi, beautiful in light or heavy makeup", "After all, the West Lake in mid-summer has scenery different from all seasons"],
        "highlights": ["Spring Dawn at Su Causeway", "Melting Snow on Broken Bridge", "Autumn Moon over Calm Lake", "Three Pools Mirroring the Moon"],
        "history": "West Lake evolved from a bay. Governor Bai Juyi built the Bai Causeway in the Tang dynasty, and Su Shi built the Su Causeway in the Song dynasty.",
    },
    "Lingyin Temple": {
        "dynasty": "Eastern Jin",
        "famous_poems": ["What does Lingyin Temple have? Only ancient pines and cypresses rustling in the wind"],
        "highlights": ["Flying Peak Rock", "Stone Cave Statues", "Huayan Hall", "500 Arhat Hall"],
        "history": "Founded in 326 AD during the Eastern Jin dynasty, it has over 1,700 years of history and is the oldest Buddhist temple in Hangzhou.",
    },
    "China Tea Museum": {
        "dynasty": "Modern",
        "famous_poems": ["Tea fragrance floats for a thousand years, green scenery fills the mountains and waters"],
        "highlights": ["Tea History Exhibition", "Tea Ceremony Show", "Tea Garden Experience", "Tea Culture Lectures"],
        "history": "China's only national-level tea museum, showcasing the history and development of Chinese tea culture.",
    },
    "Hefang Street": {
        "dynasty": "Song",
        "famous_poems": ["Hefang street lights shine bright at night, Wushan wine flags flutter gently in the wind"],
        "highlights": ["Ming-Qing Ancient Street", "Hu Qingyu Hall", "Fang Huichun Hall", "Special Snacks"],
        "history": "A commercial district formed during the Southern Song dynasty, an important part of Hangzhou's historical and cultural protection area.",
    },
    "Grand Canal Museum": {
        "dynasty": "Modern",
        "famous_poems": ["Canal water comes from heaven, thousand-year sails chase the waves"],
        "highlights": ["Canal History", "Ancient Ship Models", "Transport Culture", "Multimedia Show"],
        "history": "Comprehensively展示京杭大运河历史文化，是中国唯一的运河专题博物馆。",
    },
    "Longjing Village": {
        "dynasty": "Tang",
        "famous_poems": ["Brewing tea with mountain spring water, enjoying spring scenery"],
        "highlights": ["Longjing Tea Gardens", "Qianlong Ancient Trail", "18 Imperial Tea Trees", "Tea Farmer Visit"],
        "history": "Longjing tea began in the Tang dynasty, with over 1,200 years of history. It was a tribute tea production area during the Qing dynasty.",
    },
    "Songcheng": {
        "dynasty": "Song",
        "famous_poems": ["Songcheng eternal love, a play of a thousand years"],
        "highlights": ["Songcheng Square", "Along the River During the Qingming Festival", "Wang Yuanwai's House", "Water Margin Heroes"],
        "history": "Built based on Zhang Zeduan's 'Along the River During the Qingming Festival', a large theme park showcasing Song dynasty city life.",
    },
    "Leifeng Pagoda": {
        "dynasty": "Five Dynasties",
        "famous_poems": ["Misty rain over Jiangnan West Lake scenery, Leifeng evening glow reflects on the waves"],
        "highlights": ["Pagoda Top View", "Underground Palace Relics", "West Lake Panorama", "Legend of White Snake"],
        "history": "Originally built during the Five Dynasties Wu Yue kingdom. The original pagoda collapsed in 1924, and the current one was rebuilt in 2002.",
    },
    "Xixi Wetland": {
        "dynasty": "Song",
        "famous_poems": ["Let Xixi stay, reeds and willows with birds singing"],
        "highlights": ["Wetland Scenery", "Poled Boat", "Dragon Boat Race", "Persimmon Trees"],
        "history": "Xixi Wetland began in the Song dynasty. It is China's first national wetland park, known as 'Hangzhou's Kidney'.",
    },
    "Yue Fei Temple": {
        "dynasty": "Southern Song",
        "famous_poems": ["Loyalty to the country lasts for thousands of years, righteous spirit fills West Lake"],
        "highlights": ["Yue Fei's Tomb", "Loyalty Cypress", "Tablet Corridor", "Dream祈梦"],
        "history": "Built in 1221 during the Southern Song dynasty, a temple dedicated to national hero Yue Fei.",
    },
}


class CultureAgent(BaseAgent):
    """
    Cultural knowledge agent - provides cultural background and historical knowledge for attractions
    """

    def __init__(self):
        super().__init__(name="culture")

    async def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        db = context.get("db")
        itinerary = context.get("itinerary", {})
        items = itinerary.get("items", [])

        enriched_items = []
        for item in items:
            poi_id = item.get("poi_id")
            poi_name = item.get("poi_name", "")

            culture_info = self._get_culture_info(poi_name, poi_id, db)

            enriched_item = {
                **item,
                "culture_info": culture_info,
            }
            enriched_items.append(enriched_item)

        itinerary["items"] = enriched_items
        context["itinerary"] = itinerary

        return context

    def _get_culture_info(
        self, poi_name: str, poi_id: int, db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """Get cultural information for attraction"""
        # Check both Chinese and English names
        if poi_name in CULTURE_INFO:
            return CULTURE_INFO[poi_name]

        # Map common Chinese names to English
        name_map = {
            "西湖风景区": "West Lake",
            "灵隐寺": "Lingyin Temple",
            "中国茶叶博物馆": "China Tea Museum",
            "河坊街": "Hefang Street",
            "京杭大运河博物馆": "Grand Canal Museum",
            "龙井村": "Longjing Village",
            "宋城": "Songcheng",
            "雷峰塔": "Leifeng Pagoda",
            "西溪湿地": "Xixi Wetland",
            "岳王庙": "Yue Fei Temple",
        }
        
        english_name = name_map.get(poi_name)
        if english_name and english_name in CULTURE_INFO:
            return CULTURE_INFO[english_name]

        if db:
            poi = db.query(POI).filter(POI.id == poi_id).first()
            if poi:
                if poi.name in CULTURE_INFO:
                    return CULTURE_INFO[poi.name]
                # Check mapped names
                eng_name = name_map.get(poi.name)
                if eng_name and eng_name in CULTURE_INFO:
                    return CULTURE_INFO[eng_name]

        return {
            "dynasty": "Unknown",
            "famous_poems": [],
            "highlights": [],
            "history": "No detailed cultural information available",
        }

    def get_poi_culture(self, poi_name: str) -> Dict[str, Any]:
        """Get cultural information for a single attraction"""
        return self._get_culture_info(poi_name, None)
