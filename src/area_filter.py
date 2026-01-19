"""
Area Filter - Filterung nach Lagerbereichen
KORRIGIERT: Unterstützt source/destination als Bereichs-Indikatoren
"""

from typing import Dict, List, Optional


class AreaFilter:
    """Verwaltet Bereichsinformationen und Filterung"""
    
    # Definierte Bereiche
    AREAS = [
        "Lager_Mitte",
        "Wareneingang/-ausgang",
        "Hochregallager",
        "Safelog",
        "Magazino",
        "Agilox",
        "Lagermitte"
    ]
    
    # Alternative Bezeichnungen für Bereiche
    AREA_ALIASES = {
        "lager mitte": "Lager_Mitte",
        "lagermitte": "Lagermitte",
        "mitte": "Lager_Mitte",
        "wareneingang": "Wareneingang/-ausgang",
        "warenausgang": "Wareneingang/-ausgang",
        "waren": "Wareneingang/-ausgang",
        "hochregal": "Hochregallager",
        "hochregallager": "Hochregallager",
        "regal": "Hochregallager",
        "safelog": "Safelog",
        "safe log": "Safelog",
        "magazino": "Magazino",
        "agilox": "Agilox"
    }
    
    # Mapping von source/destination Präfixen zu Bereichen
    # Basierend auf deinen realen Daten (z.B. "0011-P003", "WE-PUFFER-02")
    LOCATION_TO_AREA = {
        "WE-": "Wareneingang/-ausgang",
        "WARENEINGANG": "Wareneingang/-ausgang",
        "HR-": "Hochregallager",
        "0011-": "Lager_Mitte",  # Beispiel, anpassen an deine Daten
    }
    
    @classmethod
    def normalize_area_name(cls, area_input: str) -> Optional[str]:
        """
        Normalisiert verschiedene Bereichsbezeichnungen zum offiziellen Namen
        
        Args:
            area_input: Benutzereingabe für Bereich
            
        Returns:
            Offizieller Bereichsname oder None
        """
        area_lower = area_input.lower().strip()
        
        # Direkte Übereinstimmung
        for area in cls.AREAS:
            if area.lower() == area_lower:
                return area
        
        # Alias-Übereinstimmung
        return cls.AREA_ALIASES.get(area_lower)
    
    @classmethod
    def filter_orders_by_area(cls, orders: List[Dict], area_name: str) -> List[Dict]:
        """
        Filtert Fahraufträge nach Bereich
        
        Args:
            orders: Liste von Fahraufträgen
            area_name: Name des Bereichs zum Filtern
            
        Returns:
            Gefilterte Liste von Fahraufträgen
        """
        filtered_orders = []
        
        for order in orders:
            # Prüfe verschiedene mögliche Felder für Bereichsinformation
            order_area = cls._extract_area_from_order(order)
            
            if order_area and cls._areas_match(order_area, area_name):
                filtered_orders.append(order)
        
        return filtered_orders
    
    @classmethod
    def get_area_distribution(cls, orders: List[Dict]) -> Dict[str, int]:
        """
        Berechnet die Verteilung von Fahraufträgen über Bereiche
        
        Args:
            orders: Liste von Fahraufträgen
            
        Returns:
            Dictionary mit Bereichen und Anzahl Aufträge
        """
        distribution = {area: 0 for area in cls.AREAS}
        distribution["Unbekannt"] = 0
        
        for order in orders:
            area = cls._extract_area_from_order(order)
            
            if area:
                normalized = cls.normalize_area_name(area)
                if normalized and normalized in distribution:
                    distribution[normalized] += 1
                else:
                    distribution["Unbekannt"] += 1
            else:
                distribution["Unbekannt"] += 1
        
        return distribution
    
    @classmethod
    def _extract_area_from_order(cls, order: Dict) -> Optional[str]:
        """
        Extrahiert Bereichsinformation aus einem Fahrauftrag
        
        Args:
            order: Fahrauftrag
            
        Returns:
            Bereichsname oder None
        """
        # 1. Prüfe dedizierte Bereichsfelder
        possible_fields = [
            "area",
            "bereich",
            "location",
            "standort",
            "zone",
            "target_location",
            "ziel_bereich"
        ]
        
        for field in possible_fields:
            if field in order and order[field]:
                return str(order[field])
        
        # 2. Prüfe source und destination Felder (häufigster Fall!)
        source = order.get("source", "")
        destination = order.get("destination", "")
        
        # Versuche Bereich aus source/destination zu extrahieren
        for location in [source, destination]:
            if location:
                area = cls._location_to_area(str(location))
                if area:
                    return area
        
        # 3. Fallback: Versuche aus type_ID zu extrahieren
        type_id = order.get("type_ID", "")
        if type_id:
            type_lower = type_id.lower()
            if "wareneingang" in type_lower or "warenausgang" in type_lower:
                return "Wareneingang/-ausgang"
        
        # 4. Letzter Fallback: Namen oder Beschreibung
        description = order.get("description", "")
        name = order.get("name", "")
        combined_text = f"{description} {name}".lower()
        
        for area in cls.AREAS:
            if area.lower() in combined_text:
                return area
        
        return None
    
    @classmethod
    def _location_to_area(cls, location: str) -> Optional[str]:
        """
        Mappt eine Location (source/destination) zu einem Bereich
        
        Args:
            location: Source oder Destination String
            
        Returns:
            Bereichsname oder None
        """
        location_upper = location.upper()
        
        # Prüfe Präfix-Mappings
        for prefix, area in cls.LOCATION_TO_AREA.items():
            if location_upper.startswith(prefix):
                return area
        
        # Prüfe exakte Matches oder Teilstrings
        location_lower = location.lower()
        for area in cls.AREAS:
            if area.lower() in location_lower:
                return area
        
        return None
    
    @classmethod
    def _areas_match(cls, area1: str, area2: str) -> bool:
        """
        Prüft ob zwei Bereichsbezeichnungen gleich sind
        
        Args:
            area1: Erste Bereichsbezeichnung
            area2: Zweite Bereichsbezeichnung
            
        Returns:
            True wenn Bereiche übereinstimmen
        """
        norm1 = cls.normalize_area_name(area1)
        norm2 = cls.normalize_area_name(area2)
        
        if norm1 and norm2:
            return norm1 == norm2
        
        return area1.lower() == area2.lower()
    
    @classmethod
    def get_available_areas(cls) -> List[str]:
        """
        Gibt Liste aller verfügbaren Bereiche zurück
        
        Returns:
            Liste der Bereichsnamen
        """
        return cls.AREAS.copy()


# Beispiel-Nutzung
if __name__ == "__main__":
    # Teste Normalisierung
    print(f"'wareneingang' -> {AreaFilter.normalize_area_name('wareneingang')}")
    print(f"'Hochregal' -> {AreaFilter.normalize_area_name('Hochregal')}")
    print(f"'mitte' -> {AreaFilter.normalize_area_name('mitte')}")
    
    # Teste mit echten Daten
    test_orders = [
        {
            "ID": "89",
            "source": "WARENEINGANG",
            "destination": "WE-PUFFER-02",
            "type_ID": "WARENEINGANG",
            "state": "RUNNING"
        },
        {
            "ID": "1",
            "source": "0011-P003",
            "destination": "0011-P004",
            "state": "READY"
        },
        {
            "ID": "2",
            "source": "HR-01-08",
            "destination": "HR-02-02",
            "state": "COMPLETED"
        }
    ]
    
    distribution = AreaFilter.get_area_distribution(test_orders)
    print(f"\nBereichsverteilung: {distribution}")
    
    # Teste Filterung
    we_orders = AreaFilter.filter_orders_by_area(test_orders, "Wareneingang/-ausgang")
    print(f"\nWareneingang Aufträge: {len(we_orders)}")
    for order in we_orders:
        print(f"  ID {order['ID']}: {order['source']} -> {order['destination']}")