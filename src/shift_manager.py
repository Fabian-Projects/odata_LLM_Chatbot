"""
Shift Manager - Verwaltung von Schichtinformationen
KORRIGIERT: Unterstützt createdAt (camelCase)
"""

from datetime import datetime, time
from typing import Dict, List, Optional


class ShiftManager:
    """Verwaltet Schichtinformationen und Zuordnungen"""
    
    # Schichtdefinitionen
    SHIFTS = {
        "Frühschicht": {
            "start": time(6, 0),
            "end": time(14, 0),
            "key": "früh"
        },
        "Spätschicht": {
            "start": time(14, 0),
            "end": time(22, 0),
            "key": "spät"
        }
    }
    
    # Alternative Bezeichnungen für Schichten
    SHIFT_ALIASES = {
        "früh": "Frühschicht",
        "frühschicht": "Frühschicht",
        "frueh": "Frühschicht",
        "fruehschicht": "Frühschicht",
        "morgen": "Frühschicht",
        "morgenschicht": "Frühschicht",
        "spät": "Spätschicht",
        "spätschicht": "Spätschicht",
        "spaet": "Spätschicht",
        "spaetschicht": "Spätschicht",
        "abend": "Spätschicht",
        "abendschicht": "Spätschicht"
    }
    
    @classmethod
    def get_current_shift(cls) -> str:
        """
        Ermittelt die aktuelle Schicht basierend auf der Systemzeit
        
        Returns:
            Name der aktuellen Schicht
        """
        current_time = datetime.now().time()
        
        for shift_name, shift_info in cls.SHIFTS.items():
            if cls._is_time_in_shift(current_time, shift_info["start"], shift_info["end"]):
                return shift_name
        
        # Außerhalb der definierten Schichten
        return "Keine Schicht"
    
    @classmethod
    def get_shift_for_datetime(cls, dt: datetime) -> str:
        """
        Ermittelt die Schicht für einen gegebenen Zeitpunkt
        
        Args:
            dt: Zeitpunkt als datetime-Objekt
            
        Returns:
            Name der Schicht
        """
        time_obj = dt.time()
        
        for shift_name, shift_info in cls.SHIFTS.items():
            if cls._is_time_in_shift(time_obj, shift_info["start"], shift_info["end"]):
                return shift_name
        
        return "Keine Schicht"
    
    @classmethod
    def normalize_shift_name(cls, shift_input: str) -> Optional[str]:
        """
        Normalisiert verschiedene Schichtbezeichnungen zum offiziellen Namen
        
        Args:
            shift_input: Benutzereingabe für Schicht
            
        Returns:
            Offizieller Schichtname oder None
        """
        shift_lower = shift_input.lower().strip()
        return cls.SHIFT_ALIASES.get(shift_lower)
    
    @classmethod
    def filter_orders_by_shift(cls, orders: List[Dict], shift_name: str) -> List[Dict]:
        """
        Filtert Fahraufträge nach Schicht basierend auf createdAt
        
        Args:
            orders: Liste von Fahraufträgen
            shift_name: Name der Schicht zum Filtern
            
        Returns:
            Gefilterte Liste von Fahraufträgen
        """
        filtered_orders = []
        
        for order in orders:
            # Unterstütze beide Varianten: createdAt und created_at
            created_at = order.get("createdAt") or order.get("created_at")
            
            if not created_at:
                continue
            
            # Parse createdAt
            try:
                dt = cls._parse_datetime(created_at)
                order_shift = cls.get_shift_for_datetime(dt)
                
                if order_shift == shift_name:
                    # Füge Schichtinformation zum Order hinzu
                    order_copy = order.copy()
                    order_copy["shift"] = order_shift
                    filtered_orders.append(order_copy)
            except Exception:
                # Bei Parse-Fehler überspringen
                continue
        
        return filtered_orders
    
    @classmethod
    def add_shift_info_to_orders(cls, orders: List[Dict]) -> List[Dict]:
        """
        Fügt Schichtinformation zu allen Fahraufträgen hinzu
        
        Args:
            orders: Liste von Fahraufträgen
            
        Returns:
            Liste mit ergänzten Fahraufträgen
        """
        enhanced_orders = []
        
        for order in orders:
            order_copy = order.copy()
            
            # Unterstütze beide Varianten: createdAt und created_at
            created_at = order.get("createdAt") or order.get("created_at")
            
            if created_at:
                try:
                    dt = cls._parse_datetime(created_at)
                    order_copy["shift"] = cls.get_shift_for_datetime(dt)
                except Exception:
                    order_copy["shift"] = "Unbekannt"
            else:
                order_copy["shift"] = "Unbekannt"
            
            enhanced_orders.append(order_copy)
        
        return enhanced_orders
    
    @classmethod
    def get_shift_distribution(cls, orders: List[Dict]) -> Dict[str, int]:
        """
        Berechnet die Verteilung von Fahraufträgen über Schichten
        
        Args:
            orders: Liste von Fahraufträgen
            
        Returns:
            Dictionary mit Schichten und Anzahl Aufträge
        """
        distribution = {
            "Frühschicht": 0,
            "Spätschicht": 0,
            "Keine Schicht": 0
        }
        
        orders_with_shift = cls.add_shift_info_to_orders(orders)
        
        for order in orders_with_shift:
            shift = order.get("shift", "Keine Schicht")
            if shift in distribution:
                distribution[shift] += 1
            else:
                distribution["Keine Schicht"] += 1
        
        return distribution
    
    @staticmethod
    def _is_time_in_shift(check_time: time, start: time, end: time) -> bool:
        """
        Prüft ob eine Uhrzeit in einer Schicht liegt
        
        Args:
            check_time: Zu prüfende Uhrzeit
            start: Schicht-Startzeit
            end: Schicht-Endzeit
            
        Returns:
            True wenn Zeit in Schicht liegt
        """
        return start <= check_time < end
    
    @staticmethod
    def _parse_datetime(dt_string: str) -> datetime:
        """
        Parst verschiedene DateTime-Formate (inkl. Millisekunden)
        
        Args:
            dt_string: DateTime als String
            
        Returns:
            datetime-Objekt
        """
        # Versuche verschiedene Formate (inkl. Millisekunden!)
        formats = [
            "%Y-%m-%dT%H:%M:%S.%fZ",  # Mit Millisekunden: 2026-01-19T08:43:23.787Z
            "%Y-%m-%dT%H:%M:%SZ",     # Ohne Millisekunden: 2026-01-19T08:43:23Z
            "%Y-%m-%dT%H:%M:%S",      # Ohne Z
            "%Y-%m-%d %H:%M:%S",      # Mit Leerzeichen
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(dt_string, fmt)
            except ValueError:
                continue
        
        raise ValueError(f"Konnte DateTime nicht parsen: {dt_string}")


# Beispiel-Nutzung
if __name__ == "__main__":
    # Teste aktuelle Schicht
    current_shift = ShiftManager.get_current_shift()
    print(f"Aktuelle Schicht: {current_shift}")
    
    # Teste Schicht-Zuordnung
    test_time = datetime(2024, 1, 15, 10, 30)  # 10:30 Uhr
    shift = ShiftManager.get_shift_for_datetime(test_time)
    print(f"Schicht um 10:30: {shift}")
    
    # Teste Normalisierung
    print(f"'früh' -> {ShiftManager.normalize_shift_name('früh')}")
    print(f"'Spätschicht' -> {ShiftManager.normalize_shift_name('Spätschicht')}")
    
    # Teste mit echtem Datum (mit Millisekunden)
    test_order = {"createdAt": "2026-01-19T08:43:23.787Z", "ID": "89"}
    orders_with_shift = ShiftManager.add_shift_info_to_orders([test_order])
    print(f"\nTest Order Schicht: {orders_with_shift[0]['shift']}")