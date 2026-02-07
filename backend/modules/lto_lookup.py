"""
LTO Vehicle Lookup Module - Mock API Gateway for Demonstration

═══════════════════════════════════════════════════════════════════════════════
IMPORTANT NOTICE FOR DEFENSE PANELISTS:
═══════════════════════════════════════════════════════════════════════════════

This module serves as a SIMULATED/MOCK API GATEWAY to the Philippine Land 
Transportation Office (LTO) database for DEMONSTRATION PURPOSES ONLY.

PURPOSE:
    This is NOT a real connection to the actual LTO government database.
    It queries a LOCAL MySQL database containing FICTIONAL test data to 
    demonstrate the system's capability to retrieve vehicle owner information.

DATA PRIVACY COMPLIANCE:
    - All data used is SYNTHETIC/FICTIONAL (generated for testing)
    - No real personal information from actual vehicle owners is stored
    - This design protects citizen privacy while showcasing functionality
    
REAL-WORLD DEPLOYMENT:
    In a production environment, this module would:
    1. Connect to the official LTO API (requires government authorization)
    2. Implement OAuth2/API key authentication
    3. Comply with Data Privacy Act of 2012 (RA 10173)
    4. Use encrypted connections (HTTPS/TLS)
    5. Log all access for audit trails
    
TECHNICAL IMPLEMENTATION:
    Current: Local MySQL database with mock records
    Future: RESTful API client to official LTO web services

For questions during defense, refer to:
    - Data Privacy Act of 2012 (RA 10173)
    - LTO Memorandum Circular on data sharing protocols
    
═══════════════════════════════════════════════════════════════════════════════
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from utils.logger import get_logger
from modules.database import get_database

logger = get_logger('lto_lookup')

class LTOLookup:
    """
    Mock LTO Database API Gateway (Demonstration Only)
    
    DEFENSE NOTE: This class simulates an API client that would connect to the
    official Philippine LTO database system. In production, this would use
    secure government-authorized API endpoints.
    
    Data Privacy Safeguards (Production-Ready):
        - All queries would be logged with timestamps and user IDs
        - Access restricted to authorized law enforcement personnel only
        - Encryption in transit (TLS 1.3) and at rest (AES-256)
        - Automatic data retention policies (auto-delete after 90 days)
        - Compliance with RA 10173 (Data Privacy Act)
    
    Current Implementation:
        - Queries local MySQL database with fictional test data
        - No real personal information is stored or accessed
        - Safe for academic demonstration and system testing
    """
    
    def __init__(self):
        """
        Initialize LTO Lookup module
        
        DEFENSE NOTE: In production, this would initialize:
            - API authentication tokens
            - SSL certificate validation
            - Rate limiting configuration
            - Audit logging system
        """
        self.db = get_database()
        logger.info("LTO Lookup module initialized (MOCK MODE - Demo Data Only)")
    
    def lookup_by_plate(self, plate_number):
        """
        Look up vehicle owner information by license plate number
        
        PRIVACY NOTICE: This queries FICTIONAL data from a local test database.
        Real deployment would require:
            - Government-issued API credentials
            - Written authorization from LTO
            - Compliance with Data Privacy Act
            - Secure audit trail of all queries
        
        Args:
            plate_number (str): License plate number (e.g., "ABC-1234")
            
        Returns:
            dict: Owner information (MOCK DATA) or None if not found
            
        Example Response:
            {
                'plate_number': 'ABC-1234',
                'owner_name': 'Juan Dela Cruz',  # FICTIONAL
                'vehicle_make': 'Honda',
                'vehicle_model': 'Wave 110',
                'registration_status': 'active',
                ...
            }
        """
        if not plate_number:
            return None
        
        # Clean plate number (remove spaces, convert to uppercase)
        plate_clean = plate_number.strip().upper()
        
        # Defense Note: In production, this would be a REST API call like:
        # response = requests.post(
        #     'https://api.lto.gov.ph/v1/vehicles/lookup',
        #     headers={'Authorization': f'Bearer {LTO_API_TOKEN}'},
        #     json={'plate_number': plate_clean},
        #     timeout=10
        # )
        
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
                logger.info(f"LTO lookup successful (MOCK): {plate_clean} -> {vehicle['owner_name']}")
                
                # Defense Note: Log access for audit trail (production requirement)
                # In real system, this would log: user_id, timestamp, plate_queried, purpose
                
                return vehicle
            else:
                logger.warning(f"LTO lookup failed: Plate {plate_clean} not found in mock database")
                return None
        except Exception as e:
            logger.error(f"LTO lookup error: {e}")
            return None
    
    def get_all_vehicles(self, limit=100):
        """
        Get all registered vehicles (for testing/demo purposes)
        
        DEFENSE NOTE: This method would NOT exist in production for privacy reasons.
        Real LTO API would only allow targeted lookups, never bulk data access.
        
        Args:
            limit (int): Maximum number of records to return
            
        Returns:
            list: List of vehicle records (MOCK DATA only)
        """
        query = """
        SELECT plate_number, owner_name, vehicle_make, vehicle_model, 
               registration_status, registration_expiry
        FROM lto_vehicles
        ORDER BY created_at DESC
        LIMIT %s
        """
        
        try:
            results = self.db.execute_query(query, (limit,))
            logger.info(f"Retrieved {len(results)} mock vehicle records for demo")
            return results if results else []
        except Exception as e:
            logger.error(f"Error fetching vehicles: {e}")
            return []
    
    def search_by_owner(self, owner_name):
        """
        Search vehicles by owner name (DEMO FEATURE - Not available in real LTO API)
        
        PRIVACY WARNING: This type of reverse lookup would be RESTRICTED in production
        to prevent unauthorized personal data access. Only authorized law enforcement
        with proper warrants would have this capability.
        
        Args:
            owner_name (str): Owner name to search (partial match allowed)
            
        Returns:
            list: Matching vehicle records (FICTIONAL DATA)
        """
        query = """
        SELECT plate_number, owner_name, owner_contact, vehicle_make, vehicle_model
        FROM lto_vehicles
        WHERE owner_name LIKE %s
        """
        
        try:
            search_term = f"%{owner_name}%"
            results = self.db.execute_query(query, (search_term,))
            logger.info(f"Owner search (MOCK): '{owner_name}' -> {len(results)} results")
            return results if results else []
        except Exception as e:
            logger.error(f"Error searching by owner: {e}")
            return []
    
    def get_statistics(self):
        """
        Get LTO database statistics (for demo dashboard)
        
        DEFENSE NOTE: Demonstrates system capability to aggregate data.
        Production version would show real-time stats from actual LTO database.
        
        Returns:
            dict: Statistics about registered vehicles (MOCK DATA)
        """
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


# Singleton instance (best practice for database connections)
_lto_lookup_instance = None

def get_lto_lookup():
    """
    Get singleton LTO lookup instance
    
    DEFENSE NOTE: Singleton pattern ensures only one database connection pool
    is used, improving performance and resource management.
    
    Returns:
        LTOLookup: Singleton instance of LTO lookup module
    """
    global _lto_lookup_instance
    if _lto_lookup_instance is None:
        _lto_lookup_instance = LTOLookup()
    return _lto_lookup_instance


# ═══════════════════════════════════════════════════════════════════════════
# Test Functions (for defense demonstration)
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 70)
    print("iCapture LTO Lookup Module - MOCK API GATEWAY TEST")
    print("=" * 70)
    print("NOTICE: This uses FICTIONAL data for demonstration purposes only.")
    print("No real personal information is accessed or stored.\n")
    
    lto = get_lto_lookup()
    
    # Test 1: Lookup specific plate
    print("Test 1: Looking up ABC-1234")
    print("-" * 70)
    vehicle = lto.lookup_by_plate("ABC-1234")
    if vehicle:
        print(f"  ✓ Plate Number: {vehicle['plate_number']}")
        print(f"  ✓ Owner: {vehicle['owner_name']} (FICTIONAL)")
        print(f"  ✓ Vehicle: {vehicle['vehicle_color']} {vehicle['vehicle_make']} {vehicle['vehicle_model']}")
        print(f"  ✓ Contact: {vehicle['owner_contact']}")
        print(f"  ✓ Registration: {vehicle['validity_status']}\n")
    else:
        print("  ✗ Not found in mock database\n")
    
    # Test 2: Lookup non-existent plate
    print("Test 2: Looking up XXX-9999 (should not exist)")
    print("-" * 70)
    vehicle = lto.lookup_by_plate("XXX-9999")
    if vehicle:
        print(f"  Found: {vehicle['owner_name']}\n")
    else:
        print("  ✓ Not found (expected behavior)\n")
    
    # Test 3: Search by owner
    print("Test 3: Searching for owners with 'Juan' (MOCK DATA)")
    print("-" * 70)
    results = lto.search_by_owner("Juan")
    if results:
        for v in results:
            print(f"  {v['plate_number']}: {v['owner_name']} (FICTIONAL)")
    else:
        print("  No results found")
    print()
    
    # Test 4: Statistics
    print("Test 4: LTO Database Statistics (DEMONSTRATION)")
    print("-" * 70)
    stats = lto.get_statistics()
    print(f"  Total vehicles in mock database: {stats.get('total_vehicles', 0)}")
    print(f"  Active registrations: {stats.get('active_count', 0)}")
    print(f"  Expired registrations: {stats.get('expired_count', 0)}")
    print(f"  Suspended registrations: {stats.get('suspended_count', 0)}")
    print("\n" + "=" * 70)
    print("TEST COMPLETE - All data shown above is FICTIONAL for demo only")
    print("=" * 70)
