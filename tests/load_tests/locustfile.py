"""
Synchronized Load Test for QR Ordering System

ONE-TIME BURST TEST:
- Opens all tables once
- All users hit each endpoint simultaneously (one cycle)
- Full synchronization with barriers between phases
- Measures concurrent load performance
- Exits immediately after completion
"""
import random
import json
import time
import threading
import queue
from datetime import datetime
from locust import HttpUser, task, between, events
from tests.load_tests.config import *
from locust.exception import StopUser


# ============================================================================
# Global Shared State
# ============================================================================

shared_session_id = None
setup_lock = threading.Lock()

# Table assignment
table_queue: queue.Queue = queue.Queue()
assignment_lock = threading.Lock()
table_assignments = {}
all_tables_ready = threading.Event()
setup_printed = False

# User tracking
user_id_counter = 0
users_started = 0
users_completed = 0
completion_lock = threading.Lock()

# SYNCHRONIZATION BARRIERS
barrier_get_table: threading.Barrier = None  # type: ignore
barrier_get_guid: threading.Barrier = None  # type: ignore
barrier_add_item: threading.Barrier = None  # type: ignore
barrier_close: threading.Barrier = None  # type: ignore

test_start_time = None
# Add to global state section
table_timings = {
    'get_table': {},
    'get_guid': {},
    'add_item': {},
    'close_check': {}
}
timing_lock = threading.Lock()
shared_menu_items = None
menu_lock = threading.Lock()

# ============================================================================
# Auto-Configuration
# ============================================================================

@events.init.add_listener
def on_locust_init(environment, **kwargs):
    """Auto-configure from config.py"""
    global table_queue

    if environment.parsed_options:
        user_count = get_user_count()

        # Override parsed options
        environment.parsed_options.num_users = user_count
        environment.parsed_options.spawn_rate = SPAWN_RATE
        environment.parsed_options.run_time = TEST_DURATION_SECONDS

        # PRE-POPULATE table queue
        for table_num in range(TABLE_START, TABLE_END + 1):
            table_queue.put(table_num)

        print("\n" + "=" * 80)
        print("⚙️  AUTO-CONFIGURATION")
        print("=" * 80)
        print(f"Tables: {TABLE_START}-{TABLE_END} ({user_count} tables)")
        print(f"Users: {user_count} (1 per table)")
        print(f"Spawn Rate: {SPAWN_RATE} users/second")
        print(f"Max Duration: {TEST_DURATION_SECONDS}s (timeout only)")
        print(f"Test Type: ONE-TIME synchronized burst")
        print("=" * 80 + "\n")


# ============================================================================
# Setup Helper
# ============================================================================
# Add after imports, before global state
def retry_request(func, max_retries=3, retry_delay=1.0):
    """Retry a function up to max_retries times"""
    for attempt in range(max_retries):
        try:
            result = func()
            if result:  # Success
                return result
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
            else:
                raise
    return None

def stop_test_async(environment):
    """Stop test after a short delay (from separate thread)"""
    time.sleep(0.5)  # Small delay to let print statements finish
    environment.runner.stop()
    print("\n🛑 Test stopped by completion signal\n")

def authenticate_shared():
    """Authenticate ONCE and share session"""
    global shared_session_id

    with setup_lock:
        if shared_session_id is not None:
            return shared_session_id

        print("\n" + "="*80)
        print("🔐 AUTHENTICATING")
        print("="*80)

        import requests
        response = requests.post(
            f"{BASE_URL}/v2/catalog/session/begin",
            headers={
                "Content-Type": "application/json",
                "Ocp-Apim-Subscription-Key": API_KEY
            },
            json={
                "ClientID": CLIENT_ID,
                "username": "internal",
                "passkey": "P455w0rd"
            }
        )

        if response.status_code == 200:
            shared_session_id = response.json().get("SessionID")
            print(f"✓ SessionID: {shared_session_id}")
            print("="*80 + "\n")
            return shared_session_id
        else:
            print(f"✗ FAILED: {response.status_code}")
            print("="*80 + "\n")
            return None


# ============================================================================
# Load Test User
# ============================================================================

class SyncLoadTestUser(HttpUser):
    """Synchronized load test user"""

    wait_time = between(0, 0)
    host = BASE_URL



    def on_start(self):
        """Setup phase"""
        global setup_printed, user_id_counter, users_started

        # Assign unique user ID FIRST
        with assignment_lock:
            self.user_id = user_id_counter
            user_id_counter += 1
            users_started += 1

            # Print header once
            if not setup_printed:
                setup_printed = True
                print("\n" + "="*80)
                print(f"📋 OPENING TABLES {TABLE_START}-{TABLE_END}")
                print("="*80)

        # Get unique table from queue
        try:
            self.table_number = table_queue.get_nowait()
        except queue.Empty:
            print(f"[User {self.user_id:02d}] ✗ No tables available!")
            return

        print(f"[User {self.user_id:02d}] Assigned table {self.table_number}")

        # Authenticate (shared)
        self.session_id = authenticate_shared()
        if not self.session_id:
            print(f"[User {self.user_id:02d}] ✗ No session")
            return

        # Open table
        self.open_table()

        # Register this user
        with assignment_lock:
            table_assignments[self.user_id] = {
                'table_number': self.table_number,
                'transaction_guid': self.transaction_guid if hasattr(self, 'transaction_guid') else None,
                'transaction_number': self.transaction_number if hasattr(self, 'transaction_number') else None,
                'success': hasattr(self, 'transaction_guid') and self.transaction_guid is not None
            }

            # Fire event when ALL users have started
            if users_started == get_user_count():
                successful = sum(1 for u in table_assignments.values() if u.get('success'))
                print("="*80)
                print(f"✓ ALL {users_started} USERS STARTED ({successful} tables opened)")
                print("="*80 + "\n")
                all_tables_ready.set()

        # Flag to track if test has run
        self.test_completed = False

    def open_table(self):
        """Open table (CREATE or GET)"""
        self.transaction_guid = None
        self.transaction_number = None

        print(f"[User {self.user_id:02d}]   → CREATE...")

        # Try CREATE (don't count failures)
        with self.client.post(
            "/v2/order/fullcart/opencheck/create",
            headers={
                "Content-Type": "application/json",
                "Ocp-Apim-Subscription-Key": API_KEY
            },
            json={
                "PropertyID": PROPERTY_ID,
                "RevenueCenterID": REVENUE_CENTER_ID,
                "ClientID": CLIENT_ID,
                "SessionID": self.session_id,
                "TableNumber": self.table_number,
                "OrderTypeIdRef": 1,
                "EmployeeNumber": EMPLOYEE_NUMBER,
                "GuestCheckRef": "",
                "cart": {"items": []}
            },
            name="[Setup] Create Check",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get('Status') == 'SUCCESS' and data.get('Order'):
                    self.transaction_guid = data['Order'].get('TransactionGuid')
                    self.transaction_number = data['Order'].get('TransactionNumber')
                    print(f"[User {self.user_id:02d}]   ✓ CREATE OK")
                    response.success()
                    return

            # Mark as success anyway (fallback is OK)
            response.success()

        # CREATE failed - try GET
        print(f"[User {self.user_id:02d}]   → GET (fallback)...")

        response = self.client.post(
            "/v2/order/fullcart/opencheck/get",
            headers={
                "Content-Type": "application/json",
                "Ocp-Apim-Subscription-Key": API_KEY
            },
            json={
                "PropertyID": PROPERTY_ID,
                "RevenueCenterID": REVENUE_CENTER_ID,
                "ClientID": CLIENT_ID,
                "SessionID": self.session_id,
                "TableNumber": self.table_number
            },
            name="[Setup] Get Check"
        )

        if response.status_code == 200:
            data = response.json()
            if data.get('Status') == 'SUCCESS':
                self.transaction_guid = data.get('TransactionGuid')
                self.transaction_number = data.get('TransactionNumber')
                print(f"[User {self.user_id:02d}]   ✓ GET OK (existing)")
                return

        print(f"[User {self.user_id:02d}]   ✗ FAILED to open table")

    def on_stop(self):
        """Cleanup - only needed if test didn't complete properly"""
        # If test completed successfully, check is already closed
        if hasattr(self, 'test_completed') and self.test_completed:
            # Silently skip cleanup (already closed in test)
            return

        # Emergency cleanup (only if test was interrupted or failed)
        if not hasattr(self, 'transaction_guid') or not self.transaction_guid:
            return

        # Don't print if no GUID (table never opened)
        print(f"[User {self.user_id:02d}] ⚠️  Test incomplete - forcing table closure...")

        try:
            response = self.client.post(
                "/v2/order/fullcart/opencheck/close",
                headers={
                    "Content-Type": "application/json",
                    "Ocp-Apim-Subscription-Key": API_KEY
                },
                json={
                    "PropertyID": PROPERTY_ID,
                    "RevenueCenterID": REVENUE_CENTER_ID,
                    "ClientID": CLIENT_ID,
                    "SessionID": self.session_id,
                    "TableNumber": self.table_number,
                    "TransactionGuid": self.transaction_guid,
                    "Tip": 0,
                    "Payment": {
                        "Amount": 10000.00,
                        "CardNumber": "33333",
                        "TenderType": "2001001",
                        "AuthCode": "67890",
                        "PaymentToken": f"emergency_{self.table_number}"
                    }
                },
                name="[Cleanup] Emergency Close"
            )

            if response.status_code == 200:
                print(f"[User {self.user_id:02d}] ✓ Table {self.table_number} force closed")

        except Exception as e:
            print(f"[User {self.user_id:02d}] ✗ Cleanup error: {e}")

    @task
    def run_synchronized_test(self):
        """
        Main test - FULLY synchronized, runs ONLY ONCE per user
        All users wait at each phase before proceeding
        """
        # Check if already completed
        if self.test_completed:
            raise StopUser()  # Stop this user

        # Skip if no GUID
        if not hasattr(self, 'transaction_guid') or not self.transaction_guid:
            print(f"[User {self.user_id:02d}] ✗ No GUID, skipping test")
            all_tables_ready.wait(timeout=60)
            self.test_completed = True
            raise StopUser()

        # Wait for ALL users to start
        print(f"[User {self.user_id:02d}] Waiting for all users to start...")
        all_tables_ready.wait(timeout=60)

        if not all_tables_ready.is_set():
            print(f"[User {self.user_id:02d}] ✗ Timeout waiting")
            self.test_completed = True
            raise StopUser()

        # First user announces
        if self.user_id == 0:
            print("\n" + "=" * 80)
            print("🔥 STARTING SYNCHRONIZED TEST")
            print("=" * 80 + "\n")

        time.sleep(1)

        print(f"[User {self.user_id:02d}] 🚀 Testing...")

        # PHASE 1: GET by Table
        if self.user_id == 0:
            print("\n[Phase 1] All users → GET by Table...")
        self.do_get_by_table()
        barrier_get_table.wait()
        if self.user_id == 0:
            print("[Phase 1] ✓ All users completed GET by Table\n")
        time.sleep(0.5)

        # PHASE 2: GET by GUID
        if self.user_id == 0:
            print("[Phase 2] All users → GET by GUID...")
        self.do_get_by_guid()
        barrier_get_guid.wait()
        if self.user_id == 0:
            print("[Phase 2] ✓ All users completed GET by GUID\n")
        time.sleep(0.5)

        # PHASE 3: Add Items
        if self.user_id == 0:
            print("[Phase 3] All users → Get Menu + Add Items...")
        menu_items = self.do_get_menu()
        total = 0
        if menu_items:
            items = random.sample(menu_items, min(1, len(menu_items)))
            for item in items:
                self.do_add_item(item)
                total += item.get('Price', 0)
        barrier_add_item.wait()
        if self.user_id == 0:
            print("[Phase 3] ✓ All users completed Add Items\n")
        time.sleep(0.5)

        # PHASE 4: Close Check
        if self.user_id == 0:
            print("[Phase 4] All users → Close Check...")
        if total == 0:
            total = 1.00
        self.do_close_check(total)
        barrier_close.wait()
        if self.user_id == 0:
            print("[Phase 4] ✓ All users completed Close Check\n")

        print(f"[User {self.user_id:02d}] ✓ Test complete")

        # Mark as completed
        self.test_completed = True

        # Check if ALL users completed
        global users_completed
        with completion_lock:
            users_completed += 1

            if users_completed == get_user_count():
                # Last user - stop entire test
                print("\n" + "=" * 80)
                print(f"✓ ALL {users_completed} USERS COMPLETED - STOPPING TEST")
                print("=" * 80 + "\n")

                # Stop the runner
                self.environment.runner.quit()

        # Stop this user's greenlet
        raise StopUser()

                # ========================================================================
    # Test Methods (MEASURED)
    # ========================================================================

    def do_get_by_table(self):
        """GET by table number - MEASURED with retry"""

        def _request():
            response = self.client.post(
                "/v2/order/fullcart/opencheck/get",
                headers={
                    "Content-Type": "application/json",
                    "Ocp-Apim-Subscription-Key": API_KEY
                },
                json={
                    "PropertyID": PROPERTY_ID,
                    "RevenueCenterID": REVENUE_CENTER_ID,
                    "ClientID": CLIENT_ID,
                    "SessionID": self.session_id,
                    "TableNumber": self.table_number
                },
                name="1. GET (by Table)"
            )
            if response.status_code == 200:
                ms = response.elapsed.total_seconds() * 1000
                print(f"[User {self.user_id:02d}]   GET by Table: {ms / 1000:.2f}s")

                # Track timing
                with timing_lock:
                    table_timings['get_table'][self.table_number] = ms / 1000
                return True
            return False

        # Retry up to 3 times
        for attempt in range(3):
            if _request():
                return
            print(f"[User {self.user_id:02d}]   ⚠ GET by Table failed, retry {attempt + 1}/3...")
            time.sleep(1)

        print(f"[User {self.user_id:02d}]   ✗ GET by Table FAILED after 3 retries")

    def do_get_by_guid(self):
        """GET by GUID - MEASURED with retry"""

        def _request():
            response = self.client.post(
                "/v2/order/fullcart/opencheck/get",
                headers={
                    "Content-Type": "application/json",
                    "Ocp-Apim-Subscription-Key": API_KEY
                },
                json={
                    "PropertyID": PROPERTY_ID,
                    "RevenueCenterID": REVENUE_CENTER_ID,
                    "ClientID": CLIENT_ID,
                    "SessionID": self.session_id,
                    "TransactionGuid": self.transaction_guid
                },
                name="2. GET (by GUID)"
            )
            if response.status_code == 200:
                ms = response.elapsed.total_seconds() * 1000
                print(f"[User {self.user_id:02d}]   GET by GUID: {ms / 1000:.2f}s")

                # Track timing
                with timing_lock:
                    table_timings['get_guid'][self.table_number] = ms / 1000
                return True
            return False

        for attempt in range(3):
            if _request():
                return
            print(f"[User {self.user_id:02d}]   ⚠ GET by GUID failed, retry {attempt + 1}/3...")
            time.sleep(1)

        print(f"[User {self.user_id:02d}]   ✗ GET by GUID FAILED after 3 retries")

    def do_get_menu(self):
        """Get menu - NOT MEASURED - fetched once and shared"""
        global shared_menu_items

        # Check if menu already fetched
        with menu_lock:
            if shared_menu_items is not None:
                return shared_menu_items

        # Only User 0 fetches the menu
        if self.user_id == 0:
            print(f"[Phase 3] Fetching menu...")

            response = self.client.post(
                "/v2/catalog/menuitems/modifiergroups/byrevenuecenter",
                headers={
                    "Content-Type": "application/json",
                    "Ocp-Apim-Subscription-Key": API_KEY
                },
                json={
                    "PropertyID": PROPERTY_ID,
                    "RevenueCenterID": REVENUE_CENTER_ID,
                    "ClientID": CLIENT_ID,
                    "SessionID": self.session_id
                },
                name="[Setup] Get Menu"
            )

            if response.status_code == 200:
                data = response.json()
                items = [i for i in data.get('Items', []) if i.get('Active')]

                # Cache the menu
                with menu_lock:
                    shared_menu_items = items
                    print(f"[Phase 3] ✓ Menu loaded: {len(items)} items")

                return items

            return []
        else:
            # Other users wait for User 0 to fetch
            print(f"[User {self.user_id:02d}]   Waiting for menu...")

            # Poll until menu is available (max 10 seconds)
            for _ in range(100):
                with menu_lock:
                    if shared_menu_items is not None:
                        print(f"[User {self.user_id:02d}]   ✓ Menu ready ({len(shared_menu_items)} items)")
                        return shared_menu_items
                time.sleep(0.1)

            print(f"[User {self.user_id:02d}]   ✗ Menu timeout")
            return []

    def do_add_item(self, item_data):
        """Add item - MEASURED with retry"""

        def _request():
            response = self.client.post(
                "/v2/order/fullcart/opencheck/add",
                headers={
                    "Content-Type": "application/json",
                    "Ocp-Apim-Subscription-Key": API_KEY
                },
                json={
                    "PropertyID": PROPERTY_ID,
                    "RevenueCenterID": REVENUE_CENTER_ID,
                    "ClientID": CLIENT_ID,
                    "SessionID": self.session_id,
                    "TableNumber": self.table_number,
                    "TransactionGuid": self.transaction_guid,
                    "cart": {
                        "items": [{
                            "ID": item_data.get('ID'),
                            "Name": item_data.get('Name'),
                            "Price": item_data.get('Price', 0),
                            "Quantity": 1,
                            "FreeText": None,
                            "Modifiers": []
                        }]
                    }
                },
                name="4. Add Item"
            )
            if response.status_code == 200:
                ms = response.elapsed.total_seconds() * 1000
                print(
                    f"[User {self.user_id:02d}]   Add: {item_data.get('Name')} (${item_data.get('Price', 0):.2f}, {ms / 1000:.2f}s)")

                # Track timing (accumulate for multiple adds)
                with timing_lock:
                    if self.table_number not in table_timings['add_item']:
                        table_timings['add_item'][self.table_number] = 0
                    table_timings['add_item'][self.table_number] += ms / 1000
                return True
            return False

        for attempt in range(3):
            if _request():
                return
            print(f"[User {self.user_id:02d}]   ⚠ Add Item failed, retry {attempt + 1}/3...")
            time.sleep(1)

        print(f"[User {self.user_id:02d}]   ✗ Add Item FAILED after 3 retries")

    def do_close_check(self, amount):
        """Close check - MEASURED with retry"""

        def _request():
            response = self.client.post(
                "/v2/order/fullcart/opencheck/close",
                headers={
                    "Content-Type": "application/json",
                    "Ocp-Apim-Subscription-Key": API_KEY
                },
                json={
                    "PropertyID": PROPERTY_ID,
                    "RevenueCenterID": REVENUE_CENTER_ID,
                    "ClientID": CLIENT_ID,
                    "SessionID": self.session_id,
                    "TableNumber": self.table_number,
                    "TransactionGuid": self.transaction_guid,
                    "Tip": 0,
                    "Payment": {
                        "Amount": 10000.00,
                        "CardNumber": "33333",
                        "TenderType": "2001001",
                        "AuthCode": "67890",
                        "PaymentToken": f"test_{self.table_number}_{int(time.time())}"
                    }
                },
                name="5. Close Check"
            )
            if response.status_code == 200:
                ms = response.elapsed.total_seconds() * 1000
                print(f"[User {self.user_id:02d}]   Close: Paid $10,000 (estimated ${amount:.2f}), {ms / 1000:.2f}s")

                # Track timing
                with timing_lock:
                    table_timings['close_check'][self.table_number] = ms / 1000
                return True
            return False

        for attempt in range(3):
            if _request():
                return
            print(f"[User {self.user_id:02d}]   ⚠ Close Check failed, retry {attempt + 1}/3...")
            time.sleep(2)  # Longer delay for close

        print(f"[User {self.user_id:02d}]   ✗ Close Check FAILED after 3 retries")


# ============================================================================
# Event Listeners
# ============================================================================

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Test start - initialize barriers"""
    global test_start_time, barrier_get_table, barrier_get_guid, barrier_add_item, barrier_close
    test_start_time = time.time()

    user_count = get_user_count()

    # Initialize barriers (all users must reach before proceeding)
    barrier_get_table = threading.Barrier(user_count)
    barrier_get_guid = threading.Barrier(user_count)
    barrier_add_item = threading.Barrier(user_count)
    barrier_close = threading.Barrier(user_count)

    print("\n" + "=" * 90)
    print("🚀 SYNCHRONIZED LOAD TEST".center(90))
    print("=" * 90)
    print(f"\n📋 CONFIGURATION:")
    print(f"  Target: {environment.host}")
    print(f"  Tables: {TABLE_START}-{TABLE_END} ({user_count} tables)")
    print(f"  Mode: FULLY SYNCHRONIZED (barriers between phases)")
    print(f"\n📝 TEST PHASES:")
    print(f"  Phase 1: GET by Table (all users wait)")
    print(f"  Phase 2: GET by GUID (all users wait)")
    print(f"  Phase 3: Add Items (all users wait)")
    print(f"  Phase 4: Close Check (all users wait)")
    print("=" * 90)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Test complete"""
    duration = time.time() - test_start_time if test_start_time else 0
    stats = environment.stats

    print("\n" + "=" * 90)
    print("✅ TEST COMPLETED".center(90))
    print("=" * 90)

    print(f"\n📊 SUMMARY:")
    print(f"  Duration: {duration:.1f}s")
    print(f"  Total Requests: {stats.total.num_requests:,}")
    print(f"  Failed Requests: {stats.total.num_failures:,}")

    if stats.total.num_requests > 0:
        success_rate = ((stats.total.num_requests - stats.total.num_failures) / stats.total.num_requests * 100)
        print(f"  Success Rate: {success_rate:.1f}%")

    print(f"\n⏱️  OVERALL RESPONSE TIMES:")
    print(f"  Average: {stats.total.avg_response_time / 1000:.2f}s")
    print(f"  Min: {stats.total.min_response_time / 1000:.2f}s")
    print(f"  Max: {stats.total.max_response_time / 1000:.2f}s")
    print(f"  Median (p50): {stats.total.get_response_time_percentile(0.5) / 1000:.2f}s")
    print(f"  p95: {stats.total.get_response_time_percentile(0.95) / 1000:.2f}s")
    print(f"  p99: {stats.total.get_response_time_percentile(0.99) / 1000:.2f}s")

    # Per-endpoint table with fastest/slowest tables
    print(f"\n📋 MEASURED ENDPOINTS (Under Concurrent Load):")
    print(f"┌{'─' * 45}┬{'─' * 10}┬{'─' * 10}┬{'─' * 12}┬{'─' * 17}┬{'─' * 17}┐")
    print(
        f"│ {'Endpoint':<43} │ {'Count':>8} │ {'Fails':>8} │ {'Avg (s)':>10} │ {'Fastest Table':>15} │ {'Slowest Table':>15} │")
    print(f"├{'─' * 45}┼{'─' * 10}┼{'─' * 10}┼{'─' * 12}┼{'─' * 17}┼{'─' * 17}┤")

    # Only show measured endpoints (not Setup/Cleanup)
    measured = sorted(
        [s for s in stats.entries.values() if not s.name.startswith('[') and s.num_requests > 0],
        key=lambda x: x.name
    )

    # Map endpoint names to timing keys
    timing_map = {
        '1. GET (by Table)': 'get_table',
        '2. GET (by GUID)': 'get_guid',
        '4. Add Item': 'add_item',
        '5. Close Check': 'close_check'
    }

    for stat in measured:
        name = stat.name[:43]
        count = f"{stat.num_requests:,}"
        fails = f"{stat.num_failures:,}"
        avg = f"{stat.avg_response_time / 1000:.2f}"

        # Get fastest/slowest tables
        timing_key = timing_map.get(stat.name)
        if timing_key and table_timings[timing_key]:
            timings = table_timings[timing_key]
            fastest_table = min(timings, key=timings.get)
            slowest_table = max(timings, key=timings.get)
            fastest = f"T{fastest_table} {timings[fastest_table]:.2f}s"
            slowest = f"T{slowest_table} {timings[slowest_table]:.2f}s"
        else:
            fastest = "N/A"
            slowest = "N/A"

        print(f"│ {name:<43} │ {count:>8} │ {fails:>8} │ {avg:>10} │ {fastest:>15} │ {slowest:>15} │")

    print(f"└{'─' * 45}┴{'─' * 10}┴{'─' * 10}┴{'─' * 12}┴{'─' * 17}┴{'─' * 17}┘")

    # GET comparison
    print(f"\n🔍 GET METHOD COMPARISON:")
    get_table = next((s for s in stats.entries.values() if 'by Table' in s.name), None)
    get_guid = next((s for s in stats.entries.values() if 'by GUID' in s.name), None)

    if get_table and get_guid and get_guid.avg_response_time > 0:
        speedup = get_table.avg_response_time / get_guid.avg_response_time
        improvement = ((get_table.avg_response_time - get_guid.avg_response_time) / get_table.avg_response_time) * 100

        print(f"  GET by Table: {get_table.avg_response_time / 1000:.2f}s avg")
        print(f"  GET by GUID:  {get_guid.avg_response_time / 1000:.2f}s avg")
        print(f"  Speedup:      {speedup:.2f}x faster with GUID")
        print(f"  Improvement:  {improvement:.1f}% faster")

    # Check if Add Item is slow
    add_item = next((s for s in stats.entries.values() if 'Add Item' in s.name), None)
    if add_item and add_item.avg_response_time > 10000:
        print(f"\n⚠️  WARNING: Add Item endpoint is VERY SLOW!")
        print(f"  Average: {add_item.avg_response_time / 1000:.2f}s")
        print(f"  This is a CRITICAL PERFORMANCE ISSUE!")

    # Check if Close Check completed
    close_check = next((s for s in stats.entries.values() if 'Close Check' in s.name), None)
    if not close_check or close_check.num_requests < get_user_count():
        actual = close_check.num_requests if close_check else 0
        expected = get_user_count()
        print(f"\n⚠️  WARNING: Not all users completed Close Check")
        print(f"  Expected: {expected}")
        print(f"  Actual: {actual}")

    # Show table performance summary
    if table_timings['get_table'] or table_timings['add_item'] or table_timings['close_check']:
        print(f"\n📊 TABLE PERFORMANCE SUMMARY:")

        # Find overall slowest table
        all_timings = {}
        for table_num in range(TABLE_START, TABLE_END + 1):
            total = 0
            count = 0
            for timing_type in ['get_table', 'get_guid', 'add_item', 'close_check']:
                if table_num in table_timings[timing_type]:
                    total += table_timings[timing_type][table_num]
                    count += 1
            if count > 0:
                all_timings[table_num] = total / count

        if all_timings:
            slowest_overall = max(all_timings, key=all_timings.get)
            fastest_overall = min(all_timings, key=all_timings.get)
            print(f"  Fastest Overall: Table {fastest_overall} (avg {all_timings[fastest_overall]:.2f}s)")
            print(f"  Slowest Overall: Table {slowest_overall} (avg {all_timings[slowest_overall]:.2f}s)")

    print("\n" + "=" * 90)
    print("✓ Test completed successfully")
    print("=" * 90)

    # Export
    try:
        results = {
            "test_info": {
                "start_time": datetime.fromtimestamp(test_start_time).isoformat() if test_start_time else None,
                "duration_seconds": duration,
                "table_range": f"{TABLE_START}-{TABLE_END}",
                "user_count": get_user_count(),
                "test_type": "ONE-TIME Synchronized Burst Test",
                **TEST_METADATA
            },
            "summary": {
                "total_requests": stats.total.num_requests,
                "failed_requests": stats.total.num_failures,
                "success_rate": ((
                                             stats.total.num_requests - stats.total.num_failures) / stats.total.num_requests * 100) if stats.total.num_requests > 0 else 0,
                "avg_response_time_seconds": stats.total.avg_response_time / 1000,
                "min_response_time_seconds": stats.total.min_response_time / 1000,
                "max_response_time_seconds": stats.total.max_response_time / 1000,
                "p50_seconds": stats.total.get_response_time_percentile(0.5) / 1000,
                "p95_seconds": stats.total.get_response_time_percentile(0.95) / 1000,
                "p99_seconds": stats.total.get_response_time_percentile(0.99) / 1000,
            },
            "endpoints": [],
            "table_timings": table_timings  # Add table timings to export
        }

        # Export all endpoints (including setup for reference)
        for stat in stats.entries.values():
            if stat.num_requests > 0:
                results["endpoints"].append({
                    "name": stat.name,
                    "num_requests": stat.num_requests,
                    "num_failures": stat.num_failures,
                    "avg_response_time_seconds": stat.avg_response_time / 1000,
                    "min_response_time_seconds": stat.min_response_time / 1000,
                    "max_response_time_seconds": stat.max_response_time / 1000,
                    "p50_seconds": stat.get_response_time_percentile(0.5) / 1000,
                    "p95_seconds": stat.get_response_time_percentile(0.95) / 1000,
                    "p99_seconds": stat.get_response_time_percentile(0.99) / 1000,
                })

        with open(LOCUST_RESULTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)  # type: ignore[arg-type]

        print(f"\n✓ Results exported to: {LOCUST_RESULTS_FILE}")

    except Exception as e:
        print(f"\n⚠️  Failed to export results: {e}")