import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class ProblemClusteringEngine:
    """
    Deterministic Problem Clustering Engine (MVP v1).
    Maps unstructured human friction (queries, titles) to canonical Problem nodes.
    Uses strict keyword mapping and aliases rather than AI embeddings.
    """
    
    # MVP Canonical Problem Mapping
    KNOWN_PROBLEMS = {
        "PHONE_OVERHEATING": [
            "iphone hot", "iphone overheating", "telefon fierbinte", 
            "telefon se incinge", "battery hot", "android overheating", "cald"
        ],
        "BATTERY_DRAIN": [
            "battery drain", "baterie scade", "baterie iphone", 
            "se descarca repede", "battery health", "bateria scade"
        ],
        "WHATSAPP_SPAM": [
            "whatsapp spam", "whatsapp hack", "whatsapp fraud", "mesaj necunoscut"
        ],
        "WIFI_ISSUES": [
            "wi-fi", "wifi disconnect", "nu se conecteaza la wifi", "parola wifi"
        ],
        "QR_PHISHING": [
            "qr scam", "qr phishing", "dnsc qr", "dnsc phishing"
        ]
    }

    @classmethod
    def determine_problem(cls, text: str) -> Optional[str]:
        """
        Takes raw text (e.g. from Google Autocomplete or Apple Support)
        and attempts to map it to a canonical Problem node.
        """
        text_lower = text.lower()
        
        for canonical_name, aliases in cls.KNOWN_PROBLEMS.items():
            for alias in aliases:
                if alias in text_lower:
                    return canonical_name
                    
        return None

    @classmethod
    async def attach_signal(cls, db_session, signal: dict) -> None:
        """
        Full implementation will lookup the Problem in the DB, create it if it doesn't exist 
        (or if mapped), and link the Signal to the Problem.id.
        """
        text_to_analyze = signal.get("title", "") + " " + signal.get("summary", "")
        problem_name = cls.determine_problem(text_to_analyze)
        
        if problem_name:
            logger.info(f"[CLUSTERING] Mapped signal to {problem_name}")
        else:
            logger.debug(f"[CLUSTERING] Unmapped signal: {text_to_analyze[:30]}...")
