from typing import Any, Dict, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.poi import POI


class POIService:
    """POI data management service"""

    def __init__(self, db: Session):
        self.db = db

    def _ensure_sample_pois(self, force: bool = False) -> List[POI]:
        """Initialize sample POI data"""
        pois = self.db.query(POI).all()
        if pois and not force:
            return pois

        if force:
            self.db.query(POI).delete()
            self.db.commit()

        samples = [
            # Hangzhou POIs - English
            POI(
                name="West Lake",
                city="Hangzhou",
                district="Xihu District",
                category="culture",
                sub_category="Lake",
                description="West Lake is a famous scenic area in Hangzhou, known for its natural beauty and cultural heritage. Listed as a World Heritage Site.",
                address="West Lake Scenic Area, Xihu District, Hangzhou, Zhejiang",
                latitude=30.2465,
                longitude=120.1480,
                rating=4.8,
                review_count=50000,
                price_level=0,
                estimated_duration=240,
                opening_hours={"Mon": "Open 24h", "Tue": "Open 24h", "Wed": "Open 24h", "Thu": "Open 24h", "Fri": "Open 24h", "Sat": "Open 24h", "Sun": "Open 24h"},
                ticket_info="Free (some attractions require ticket)",
                booking_required=False,
                tags=["5A", "World Heritage", "Lake", "Garden"],
                highlight="Enjoy the 'Ten Scenes of West Lake' including Spring Dawn at Su Causeway and Melting Snow on Broken Bridge",
                best_season="Spring, Autumn",
                recommended_visit_duration=240,
                is_accessible=True,
                parking_available=True,
            ),
            POI(
                name="Lingyin Temple",
                city="Hangzhou",
                district="Xihu District",
                category="religion",
                sub_category="Temple",
                description="Lingyin Temple is the oldest and largest Buddhist temple in Hangzhou with over 1,700 years of history.",
                address="1 Fayun Lane, Lingyin Road, Xihu District, Hangzhou, Zhejiang",
                latitude=30.2365,
                longitude=120.1230,
                rating=4.7,
                review_count=25000,
                price_level=2,
                estimated_duration=180,
                opening_hours={"Mon": "07:00-18:00", "Tue": "07:00-18:00", "Wed": "07:00-18:00", "Thu": "07:00-18:00", "Fri": "07:00-18:00", "Sat": "07:00-18:00", "Sun": "07:00-18:00"},
                ticket_info="30 RMB (includes Flying Peak)",
                booking_required=False,
                tags=["Buddhism", "Ancient Temple", "Historical Site"],
                highlight="View the Flying Peak stone carvings and make wishes",
                best_season="All seasons",
                recommended_visit_duration=180,
                is_accessible=True,
                parking_available=True,
            ),
            POI(
                name="China Tea Museum",
                city="Hangzhou",
                district="Xihu District",
                category="culture",
                sub_category="Museum",
                description="China's only national-level tea museum, showcasing the history and development of Chinese tea culture.",
                address="Longjing Road, Shuangfeng Village, Xihu District, Hangzhou, Zhejiang",
                latitude=30.2510,
                longitude=120.1090,
                rating=4.5,
                review_count=8000,
                price_level=1,
                estimated_duration=120,
                opening_hours={"Mon": "09:00-17:00", "Tue": "09:00-17:00", "Wed": "09:00-17:00", "Thu": "09:00-17:00", "Fri": "09:00-17:00", "Sat": "09:00-17:00", "Sun": "09:00-17:00"},
                ticket_info="Free admission",
                booking_required=False,
                tags=["Museum", "Tea Culture", "Intangible Heritage"],
                highlight="Learn about Longjing tea culture and taste West Lake Longjing tea",
                best_season="Spring (tea picking season)",
                recommended_visit_duration=120,
                is_accessible=True,
                parking_available=True,
            ),
            POI(
                name="Hefang Street",
                city="Hangzhou",
                district="Shangcheng District",
                category="food",
                sub_category="Food Street",
                description="The most representative historical and cultural block in Hangzhou, preserving the style of late Qing and early Republic era.",
                address="Hefang Street, Shangcheng District, Hangzhou, Zhejiang",
                latitude=30.2490,
                longitude=120.1650,
                rating=4.4,
                review_count=30000,
                price_level=1,
                estimated_duration=120,
                opening_hours={"Mon": "Open 24h", "Tue": "Open 24h", "Wed": "Open 24h", "Thu": "Open 24h", "Fri": "Open 24h", "Sat": "Open 24h", "Sun": "Open 24h"},
                ticket_info="Free street",
                booking_required=False,
                tags=["Ancient Street", "Food", "Shopping", "Night View"],
                highlight="Taste Hangzhou special snacks and buy souvenirs",
                best_season="All seasons",
                recommended_visit_duration=120,
                is_accessible=True,
                parking_available=False,
            ),
            POI(
                name="Grand Canal Museum",
                city="Hangzhou",
                district="Gongshu District",
                category="culture",
                sub_category="Museum",
                description="China's first themed museum featuring the Grand Canal culture.",
                address="1 Canal Cultural Square, Gongshu District, Hangzhou, Zhejiang",
                latitude=30.3450,
                longitude=120.1520,
                rating=4.3,
                review_count=5000,
                price_level=0,
                estimated_duration=90,
                opening_hours={"Mon": "Closed", "Tue": "09:00-16:30", "Wed": "09:00-16:30", "Thu": "09:00-16:30", "Fri": "09:00-16:30", "Sat": "09:00-16:30", "Sun": "09:00-16:30"},
                ticket_info="Free admission",
                booking_required=False,
                tags=["Museum", "Canal", "History"],
                highlight="Learn about the thousand-year history of the Beijing-Hangzhou Grand Canal",
                best_season="All seasons",
                recommended_visit_duration=90,
                is_accessible=True,
                parking_available=True,
            ),
            POI(
                name="Longjing Village",
                city="Hangzhou",
                district="Xihu District",
                category="nature",
                sub_category="Tea Garden",
                description="The birthplace of Longjing tea, featuring beautiful tea garden scenery and unique tea culture experience.",
                address="Longjing Village, Xihu District, Hangzhou, Zhejiang",
                latitude=30.2580,
                longitude=120.1050,
                rating=4.6,
                review_count=15000,
                price_level=0,
                estimated_duration=180,
                opening_hours={"Mon": "Open 24h", "Tue": "Open 24h", "Wed": "Open 24h", "Thu": "Open 24h", "Fri": "Open 24h", "Sat": "Open 24h", "Sun": "Open 24h"},
                ticket_info="Free admission (tea tasting fees apply)",
                booking_required=False,
                tags=["Tea Garden", "Farm Stay", "Nature"],
                highlight="Experience tea picking and processing, taste authentic Longjing tea",
                best_season="Spring (March-April tea picking season)",
                recommended_visit_duration=180,
                is_accessible=True,
                parking_available=True,
            ),
            POI(
                name="Songcheng",
                city="Hangzhou",
                district="Xihu District",
                category="entertainment",
                sub_category="Theme Park",
                description="A large theme park based on Song dynasty culture, recreating the prosperity of the Song dynasty capital.",
                address="148 Zhijiang Road, Xihu District, Hangzhou, Zhejiang",
                latitude=30.1980,
                longitude=120.1450,
                rating=4.5,
                review_count=20000,
                price_level=3,
                estimated_duration=360,
                opening_hours={"Mon": "10:00-21:00", "Tue": "10:00-21:00", "Wed": "10:00-21:00", "Thu": "10:00-21:00", "Fri": "10:00-21:00", "Sat": "09:30-21:30", "Sun": "09:30-21:30"},
                ticket_info="Standard Seat 300 RMB, VIP Seat 320 RMB",
                booking_required=True,
                tags=["Theme Park", "Show", "Song Culture"],
                highlight="Watch the large-scale show 'Songcheng Eternal Love'",
                best_season="All seasons",
                recommended_visit_duration=360,
                is_accessible=True,
                parking_available=True,
            ),
            POI(
                name="Leifeng Pagoda",
                city="Hangzhou",
                district="Xihu District",
                category="culture",
                sub_category="Ancient Pagoda",
                description="China's first colorful bronze carved pagoda, famous for the Legend of White Snake.",
                address="15 Nanshan Road, Xihu District, Hangzhou, Zhejiang",
                latitude=30.2430,
                longitude=120.1580,
                rating=4.4,
                review_count=18000,
                price_level=2,
                estimated_duration=90,
                opening_hours={"Mon": "08:00-17:30", "Tue": "08:00-17:30", "Wed": "08:00-17:30", "Thu": "08:00-17:30", "Fri": "08:00-17:30", "Sat": "08:00-17:30", "Sun": "08:00-17:30"},
                ticket_info="40 RMB",
                booking_required=False,
                tags=["Ancient Pagoda", "Legend", "Panoramic View"],
                highlight="Climb the pagoda for panoramic view of West Lake",
                best_season="Spring, Autumn",
                recommended_visit_duration=90,
                is_accessible=True,
                parking_available=True,
            ),
            POI(
                name="Xixi Wetland",
                city="Hangzhou",
                district="Xihu District",
                category="nature",
                sub_category="Wetland Park",
                description="China's first national wetland park integrating urban wetland, agricultural wetland, and cultural wetland.",
                address="518 Tianmushan Road, Xihu District, Hangzhou, Zhejiang",
                latitude=30.2720,
                longitude=120.0580,
                rating=4.7,
                review_count=22000,
                price_level=2,
                estimated_duration=240,
                opening_hours={"Mon": "08:00-17:30", "Tue": "08:00-17:30", "Wed": "08:00-17:30", "Thu": "08:00-17:30", "Fri": "08:00-17:30", "Sat": "07:30-18:00", "Sun": "07:30-18:00"},
                ticket_info="80 RMB (ticket + boat ride)",
                booking_required=False,
                tags=["Wetland", "Ecology", "Nature Reserve"],
                highlight="Take a boat tour to enjoy wetland scenery, bird watching and flower viewing",
                best_season="Spring, Autumn",
                recommended_visit_duration=240,
                is_accessible=True,
                parking_available=True,
            ),
            POI(
                name="Yue Fei Temple",
                city="Hangzhou",
                district="Xihu District",
                category="culture",
                sub_category="Historical Site",
                description="A famous historical site commemorating Southern Song national hero Yue Fei.",
                address="80 Beishan Road, Xihu District, Hangzhou, Zhejiang",
                latitude=30.2540,
                longitude=120.1550,
                rating=4.5,
                review_count=12000,
                price_level=1,
                estimated_duration=60,
                opening_hours={"Mon": "07:30-17:30", "Tue": "07:30-17:30", "Wed": "07:30-17:30", "Thu": "07:30-17:30", "Fri": "07:30-17:30", "Sat": "07:30-17:30", "Sun": "07:30-17:30"},
                ticket_info="25 RMB",
                booking_required=False,
                tags=["History", "Hero", "Culture"],
                highlight="Pay respects to Yue Fei's statue, read 'Full River Red'",
                best_season="All seasons",
                recommended_visit_duration=60,
                is_accessible=True,
                parking_available=False,
            ),
        ]

        self.db.add_all(samples)
        self.db.commit()
        for p in samples:
            self.db.refresh(p)
        return samples

    def get_by_city(self, city: str) -> List[POI]:
        """Get POIs for specified city"""
        return self.db.query(POI).filter(POI.city == city).all()

    def get_by_category(self, category: str) -> List[POI]:
        """Get POIs for specified category"""
        return self.db.query(POI).filter(POI.category == category).all()

    def search(self, keyword: str, city: Optional[str] = None, category: Optional[str] = None) -> List[POI]:
        """Keyword search POI"""
        query = self.db.query(POI)
        if city:
            query = query.filter(POI.city == city)
        if category:
            query = query.filter(POI.category == category)
        query = query.filter(
            (POI.name.contains(keyword)) |
            (POI.description.contains(keyword)) |
            (POI.tags.contains(keyword))
        )
        return query.all()

    def get_by_id(self, poi_id: int) -> Optional[POI]:
        """Get single POI"""
        return self.db.query(POI).filter(POI.id == poi_id).first()
