"""
LTO Vehicle Lookup Module (Simulated)
Queries the mock LTO database for vehicle owner information
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from utils.logger import get_logger
from modules.database import get_database

logger = get_logger('lto_lookup')

class LTOLookup:
    """Simulated LTO database lookup"""
    
    def __init__(self):
        self.db = get_database()
        logger.info("LTO Lookup module initialized")
    
    def lookup_by_plate(self, plate_number):
        """
        Look up vehicle owner by plate number
        
        Args:
            plate_number (str): License plate number
            
        Returns:
            dict: Owner information or None if not found
        """
        if not plate_number:
            return None
        
        # Clean plate number (remove spaces, convert to uppercase)
        plate_clean = plate_number.strip().upper()
        
        query = """
        SELECT 
            plate_number,
            vehicle_type,
            vehicle_make,
            vehicle_model,
            vehicle_color,
            vehicle_year,
            owner_name,
            owner_address,
            owner_contact,
            registration_status,
            registration_expiry,
            CASE 
                WHEN registration_status = 'active' AND registration_expiry > CURDATE() THEN 'Valid'
                WHEN registration_status = 'active' AND registration_expiry <= CURDATE() THEN 'Expired'
                WHEN registration_status = 'suspended' THEN 'Suspended'
                ELSE 'Invalid'
            END as validity_status
        FROM lto_vehicles
        WHERE plate_number = %s
        """
        
        try:
            result = self.db.execute_query(query, (plate_clean,))
            
            if result and len(result) > 0:
                vehicle = result[0]
                logger.info(f"LTO lookup successful: {plate_clean} -> {vehicle['owner_name']}")
                return vehicle
            else:
                logger.warning(f"LTO lookup failed: Plate {plate_clean} not found")
                return None
        except Exception as e:
            logger.error(f"LTO lookup error: {e}")
            return None
    
    def get_all_vehicles(self, limit=100):
        """Get all registered vehicles (for testing/demo)"""
        query = """
        SELECT plate_number, owner_name, vehicle_make, vehicle_model, 
               registration_status, registration_expiry
        FROM lto_vehicles
        ORDER BY created_at DESC
        LIMIT %s
        """
        
        try:
            results = self.db.execute_query(query, (limit,))
            return results if results else []
        except Exception as e:
            logger.error(f"Error fetching vehicles: {e}")
            return []
    
    def search_by_owner(self, owner_name):
        """Search vehicles by owner name"""
        query = """
        SELECT plate_number, owner_name, owner_contact, vehicle_make, vehicle_model
        FROM lto_vehicles
        WHERE owner_name LIKE %s
        """
        
        try:
            search_term = f"%{owner_name}%"
            results = self.db.execute_query(query, (search_term,))
            return results if results else []
        except Exception as e:
            logger.error(f"Error searching by owner: {e}")
            return []
    
    def get_statistics(self):
        """Get LTO database statistics"""
        query = """
        SELECT 
            COUNT(*) as total_vehicles,
            SUM(CASE WHEN registration_status = 'active' THEN 1 ELSE 0 END) as active_count,
            SUM(CASE WHEN registration_status = 'expired' THEN 1 ELSE 0 END) as expired_count,
            SUM(CASE WHEN registration_status = 'suspended' THEN 1 ELSE 0 END) as suspended_count
        FROM lto_vehicles
        """
        
        try:
            result = self.db.execute_query(query)
            return result[0] if result else {}
        except Exception as e:
            logger.error(f"Error getting LTO stats: {e}")
            return {}


# Singleton instance
_lto_lookup_instance = None

def get_lto_lookup():
    """Get singleton LTO lookup instance"""
    global _lto_lookup_instance
    if _lto_lookup_instance is None:
        _lto_lookup_instance = LTOLookup()
    return _lto_lookup_instance


# Test function
if __name__ == "__main__":
    print("Testing LTO Lookup Module\n")
    
    lto = get_lto_lookup()
    
    # Test 1: Lookup specific plate
    print("Test 1: Looking up ABC-1234")
    vehicle = lto.lookup_by_plate("ABC-1234")
    if vehicle:
        print(f"  Owner: {vehicle['owner_name']}")
        print(f"  Vehicle: {vehicle['vehicle_color']} {vehicle['vehicle_make']} {vehicle['vehicle_model']}")
        print(f"  Contact: {vehicle['owner_contact']}")
        print(f"  Status: {vehicle['validity_status']}\n")
    else:
        print("  Not found\n")
    
    # Test 2: Lookup non-existent plate
    print("Test 2: Looking up XXX-9999 (should not exist)")
    vehicle = lto.lookup_by_plate("XXX-9999")
    if vehicle:
        print(f"  Found: {vehicle['owner_name']}\n")
    else:
        print("  Not found (correct)\n")
    
    # Test 3: Search by owner
    print("Test 3: Searching for owners with 'Juan'")
    results = lto.search_by_owner("Juan")
    for v in results:
        print(f"  {v['plate_number']}: {v['owner_name']}")
    print()
    
    # Test 4: Statistics
    print("Test 4: LTO Database Statistics")
    stats = lto.get_statistics()
    print(f"  Total vehicles: {stats.get('total_vehicles', 0)}")
    print(f"  Active: {stats.get('active_count', 0)}")
    print(f"  Expired: {stats.get('expired_count', 0)}")
    print(f"  Suspended: {stats.get('suspended_count', 0)}")
