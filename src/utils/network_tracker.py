"""
Simple Network Tracker - FIXED for actual endpoints
"""
import json
import time
from typing import List, Dict, Any
import allure


class NetworkTracker:
    """Simple API performance tracker"""

    def __init__(self, driver):
        self.driver = driver

        # Storage for captured calls
        self.get_by_table = []      # GET calls with TableNumber
        self.get_by_guid = []       # GET calls with TransactionGuid
        self.add_calls = []         # POST /addtoopencheck calls
        self.close_calls = []       # POST /closecheck calls

    def capture(self):
        """Capture network logs and parse API calls"""
        try:
            logs = self.driver.get_log('performance')
            print(f"\n🔍 DEBUG: Retrieved {len(logs)} performance log entries")
        except Exception as e:
            print(f"⚠️  Could not get performance logs: {e}")
            return

        if not logs:
            print("⚠️  WARNING: No performance logs found!")
            return

        # Track requests and their POST bodies
        pending_requests = {}
        request_bodies = {}  # Store request bodies separately

        for log in logs:
            try:
                message = json.loads(log['message'])
                method = message.get('message', {}).get('method', '')
                params = message.get('message', {}).get('params', {})

                # Capture request body data BEFORE the request is sent
                if method == 'Network.requestWillBeSentExtraInfo':
                    request_id = params.get('requestId')
                    headers = params.get('headers', {})
                    # Store for later use
                    if request_id:
                        request_bodies[request_id] = params

                # Request started
                if method == 'Network.requestWillBeSent':
                    request_id = params.get('requestId')
                    request_data = params.get('request', {})
                    url = request_data.get('url', '')
                    http_method = request_data.get('method', '')

                    # ✅ FIXED: Match actual endpoints
                    if '/getcheck' in url or \
                       '/addtoopencheck' in url or \
                       '/pay' in url:

                        post_data = request_data.get('postData', '')

                        print(f"  ✅ MATCHED: {http_method} {url}")

                        pending_requests[request_id] = {
                            'url': url,
                            'method': http_method,
                            'post_data': post_data,
                            'start_time': params.get('timestamp', 0)
                        }

                # Response received
                elif method == 'Network.responseReceived':
                    request_id = params.get('requestId')
                    if request_id in pending_requests:
                        response_data = params.get('response', {})
                        pending_requests[request_id]['status'] = response_data.get('status', 0)
                        pending_requests[request_id]['end_time'] = params.get('timestamp', 0)

                # Get response body to check TableNumber vs TransactionGuid
                elif method == 'Network.getResponseBody':
                    request_id = params.get('requestId')
                    # This gives us the actual request/response body

                # Request completed
                elif method == 'Network.loadingFinished':
                    request_id = params.get('requestId')
                    if request_id in pending_requests:
                        request_info = pending_requests.pop(request_id)

                        # Calculate duration
                        duration_ms = (request_info['end_time'] - request_info['start_time']) * 1000

                        call_data = {
                            'duration_ms': round(duration_ms, 0),
                            'status': request_info.get('status', 'Unknown'),
                            'timestamp': time.strftime('%H:%M:%S')
                        }

                        url = request_info['url']
                        post_data = request_info.get('post_data', '')

                        # ✅ Categorize by actual endpoints
                        if '/getcheck' in url:
                            # Check if TableNumber or TransactionGuid in POST body
                            if post_data:
                                try:
                                    body = json.loads(post_data)
                                    if 'TableNumber' in body:
                                        self.get_by_table.append(call_data)
                                        print(f"  📊 Captured GET by Table: {duration_ms:.0f}ms")
                                    elif 'TransactionGuid' in body:
                                        self.get_by_guid.append(call_data)
                                        print(f"  🚀 Captured GET by GUID: {duration_ms:.0f}ms")
                                    else:
                                        # Default to GUID if can't determine
                                        self.get_by_guid.append(call_data)
                                        print(f"  🚀 Captured GET (assumed GUID): {duration_ms:.0f}ms")
                                except json.JSONDecodeError:
                                    # Can't parse, check string content
                                    if 'TableNumber' in post_data:
                                        self.get_by_table.append(call_data)
                                        print(f"  📊 Captured GET by Table: {duration_ms:.0f}ms")
                                    else:
                                        self.get_by_guid.append(call_data)
                                        print(f"  🚀 Captured GET by GUID: {duration_ms:.0f}ms")
                            else:
                                # No post data visible, assume GUID (faster calls)
                                self.get_by_guid.append(call_data)
                                print(f"  🚀 Captured GET (no body, assumed GUID): {duration_ms:.0f}ms")

                        elif '/addtoopencheck' in url:
                            self.add_calls.append(call_data)
                            print(f"  ➕ Captured ADD: {duration_ms:.0f}ms")

                        elif '/pay' in url:
                            self.close_calls.append(call_data)
                            print(f"  🔒 Captured CLOSE: {duration_ms:.0f}ms")

            except (json.JSONDecodeError, KeyError) as e:
                continue

        print(f"\n📊 CAPTURE SUMMARY:")
        print(f"  GET by Table: {len(self.get_by_table)}")
        print(f"  GET by GUID: {len(self.get_by_guid)}")
        print(f"  ADD calls: {len(self.add_calls)}")
        print(f"  CLOSE calls: {len(self.close_calls)}")

    def get_summary(self) -> str:
        """Generate simple summary report"""
        total_calls = len(self.get_by_table) + len(self.get_by_guid) + len(self.add_calls) + len(self.close_calls)

        if total_calls == 0:
            return "No API calls captured."

        summary = f"""
╔════════════════════════════════════════════════════════════════════════════════
║                        🌐 API PERFORMANCE SUMMARY
╠════════════════════════════════════════════════════════════════════════════════
║ Total API Calls: {total_calls}
╠════════════════════════════════════════════════════════════════════════════════
"""

        # GET by Table
        if self.get_by_table:
            avg = sum(c['duration_ms'] for c in self.get_by_table) / len(self.get_by_table)
            summary += f"║ 📊 GET (by Table Number):\n"
            summary += f"║    Count: {len(self.get_by_table)}\n"
            summary += f"║    Average: {avg:.0f}ms\n"
            summary += f"║    Durations:\n"
            for i, call in enumerate(self.get_by_table, 1):
                summary += f"║      {i}. {call['duration_ms']:.0f}ms (Status: {call['status']}) at {call['timestamp']}\n"
            summary += "║\n"
        else:
            summary += "║ 📊 GET (by Table Number): None\n║\n"

        # GET by GUID
        if self.get_by_guid:
            avg = sum(c['duration_ms'] for c in self.get_by_guid) / len(self.get_by_guid)
            summary += f"║ 🚀 GET (by TransactionGuid):\n"
            summary += f"║    Count: {len(self.get_by_guid)}\n"
            summary += f"║    Average: {avg:.0f}ms\n"
            summary += f"║    Durations:\n"
            for i, call in enumerate(self.get_by_guid, 1):
                summary += f"║      {i}. {call['duration_ms']:.0f}ms (Status: {call['status']}) at {call['timestamp']}\n"
            summary += "║\n"
        else:
            summary += "║ 🚀 GET (by TransactionGuid): None\n║\n"

        # ADD calls
        if self.add_calls:
            avg = sum(c['duration_ms'] for c in self.add_calls) / len(self.add_calls)
            summary += f"║ ➕ ADD Item (addtoopencheck):\n"
            summary += f"║    Count: {len(self.add_calls)}\n"
            summary += f"║    Average: {avg:.0f}ms\n"
            summary += f"║    Durations:\n"
            for i, call in enumerate(self.add_calls, 1):
                summary += f"║      {i}. {call['duration_ms']:.0f}ms (Status: {call['status']}) at {call['timestamp']}\n"
            summary += "║\n"
        else:
            summary += "║ ➕ ADD Item: None\n║\n"

        # CLOSE calls
        if self.close_calls:
            summary += f"║ 🔒 CLOSE Check:\n"
            summary += f"║    Count: {len(self.close_calls)}\n"
            summary += f"║    Durations:\n"
            for i, call in enumerate(self.close_calls, 1):
                summary += f"║      {i}. {call['duration_ms']:.0f}ms (Status: {call['status']}) at {call['timestamp']}\n"
            summary += "║\n"
        else:
            summary += "║ 🔒 CLOSE Check: None\n║\n"

        # Performance comparison
        if self.get_by_table and self.get_by_guid:
            table_avg = sum(c['duration_ms'] for c in self.get_by_table) / len(self.get_by_table)
            guid_avg = sum(c['duration_ms'] for c in self.get_by_guid) / len(self.get_by_guid)
            speedup = table_avg / guid_avg if guid_avg > 0 else 0

            summary += "╠════════════════════════════════════════════════════════════════════════════════\n"
            summary += "║                        ⚡ PERFORMANCE COMPARISON\n"
            summary += "╠════════════════════════════════════════════════════════════════════════════════\n"
            summary += f"║ GET by Table:  {table_avg:.0f}ms average\n"
            summary += f"║ GET by GUID:   {guid_avg:.0f}ms average\n"
            summary += f"║ 🚀 GUID is {speedup:.1f}x FASTER than Table\n"

        summary += "╚════════════════════════════════════════════════════════════════════════════════\n"

        return summary

    def attach_to_allure(self):
        """Attach summary to Allure report"""
        summary = self.get_summary()

        allure.attach(
            summary,
            name="🌐 API Performance Report",
            attachment_type=allure.attachment_type.TEXT
        )

    def clear(self):
        """Clear all captured data"""
        self.get_by_table.clear()
        self.get_by_guid.clear()
        self.add_calls.clear()
        self.close_calls.clear()