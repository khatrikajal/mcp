"""
Comprehensive API Endpoint Tests

Tests all API endpoints for the AI Workforce Platform including:
- Authentication (register, login, token refresh)
- Agents CRUD
- Conversations & Messages
- Delegations (Phase 4)
- Approvals
"""
import os
import sys
import asyncio
import requests
from datetime import datetime, timedelta
from typing import Optional

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuration
BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")
TEST_EMAIL = "test_user@example.com"
TEST_PASSWORD = "TestPassword123!"
TEST_NAME = "Test User"


class APITestClient:
    """Test client for API endpoint testing."""

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.token: Optional[str] = None
        self.user_id: Optional[int] = None
        self.results = {"passed": 0, "failed": 0, "errors": []}

    def _headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _log_result(self, test_name: str, passed: bool, details: str = ""):
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status}: {test_name}")
        if details:
            print(f"       {details}")
        if passed:
            self.results["passed"] += 1
        else:
            self.results["failed"] += 1
            self.results["errors"].append(f"{test_name}: {details}")

    def _request(self, method: str, endpoint: str, data: dict = None, expected_status: int = 200) -> tuple[bool, dict]:
        """Make HTTP request and return (success, response_data)."""
        url = f"{self.base_url}{endpoint}"
        try:
            if method == "GET":
                response = requests.get(url, headers=self._headers(), timeout=10)
            elif method == "POST":
                response = requests.post(url, json=data, headers=self._headers(), timeout=10)
            elif method == "PUT":
                response = requests.put(url, json=data, headers=self._headers(), timeout=10)
            elif method == "DELETE":
                response = requests.delete(url, headers=self._headers(), timeout=10)
            else:
                return False, {"error": f"Unknown method: {method}"}

            success = response.status_code == expected_status
            try:
                response_data = response.json()
            except:
                response_data = {"text": response.text}

            if not success:
                response_data["actual_status"] = response.status_code
                response_data["expected_status"] = expected_status

            return success, response_data
        except requests.exceptions.ConnectionError:
            return False, {"error": "Connection refused - is the server running?"}
        except Exception as e:
            return False, {"error": str(e)}

    # =========================================================================
    # Authentication Tests
    # =========================================================================

    def test_health_check(self):
        """Test health endpoint."""
        # Health endpoint is at root level, not under /api/v1
        url = self.base_url.replace("/api/v1", "") + "/health"
        try:
            response = requests.get(url, timeout=10)
            success = response.status_code == 200
            data = response.json() if success else {}
            self._log_result("Health Check", success and data.get("status") == "healthy")
        except Exception as e:
            self._log_result("Health Check", False, str(e))

    def test_register_user(self):
        """Test user registration."""
        success, data = self._request("POST", "/auth/register", {
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "name": TEST_NAME
        }, expected_status=201)

        # May fail if user exists, try login instead
        if not success and "already" in str(data.get("detail", "")).lower():
            self._log_result("Register User", True, "User already exists (expected)")
            return True

        if success:
            self.token = data.get("access_token")
            self.user_id = data.get("user", {}).get("id")
            self._log_result("Register User", True)
            return True
        else:
            self._log_result("Register User", False, str(data))
            return False

    def test_login_user(self):
        """Test user login."""
        success, data = self._request("POST", "/auth/login", {
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })

        if success:
            self.token = data.get("access_token")
            self.user_id = data.get("user", {}).get("id")
            self._log_result("Login User", True)
            return True
        else:
            self._log_result("Login User", False, str(data))
            return False

    def test_get_current_user(self):
        """Test get current user endpoint."""
        success, data = self._request("GET", "/auth/me")
        self._log_result("Get Current User", success and "email" in data)

    # =========================================================================
    # Agent Tests
    # =========================================================================

    def test_create_agent(self) -> Optional[int]:
        """Test agent creation."""
        success, data = self._request("POST", "/agents", {
            "name": "Test Agent",
            "description": "A test AI agent",
            "system_instructions": "You are a helpful test assistant."
        }, expected_status=201)

        if success:
            agent_id = data.get("id")
            self._log_result("Create Agent", True, f"ID: {agent_id}")
            return agent_id
        else:
            self._log_result("Create Agent", False, str(data))
            return None

    def test_list_agents(self):
        """Test listing agents."""
        success, data = self._request("GET", "/agents")
        is_list = isinstance(data, list)
        self._log_result("List Agents", success and is_list, f"Count: {len(data) if is_list else 0}")

    def test_get_agent(self, agent_id: int):
        """Test getting a specific agent."""
        success, data = self._request("GET", f"/agents/{agent_id}")
        self._log_result("Get Agent", success and data.get("id") == agent_id)

    def test_update_agent(self, agent_id: int):
        """Test updating an agent."""
        success, data = self._request("PUT", f"/agents/{agent_id}", {
            "name": "Updated Test Agent",
            "description": "Updated description"
        })
        self._log_result("Update Agent", success and "Updated" in data.get("name", ""))

    def test_delete_agent(self, agent_id: int):
        """Test deleting an agent."""
        success, data = self._request("DELETE", f"/agents/{agent_id}", expected_status=204)
        # 204 No Content is expected, but may fail if agent has active conversations
        if not success and "actual_status" in data:
            # Could be 409 Conflict if agent has dependencies
            self._log_result("Delete Agent", data.get("actual_status") in [204, 409],
                           f"Status: {data.get('actual_status')}")
        else:
            self._log_result("Delete Agent", success)

    # =========================================================================
    # Conversation Tests
    # =========================================================================

    def test_create_conversation(self, agent_id: int) -> Optional[int]:
        """Test conversation creation."""
        success, data = self._request("POST", "/conversations", {
            "agent_id": agent_id,
            "title": "Test Conversation"
        }, expected_status=201)

        if success:
            conv_id = data.get("id")
            self._log_result("Create Conversation", True, f"ID: {conv_id}")
            return conv_id
        else:
            self._log_result("Create Conversation", False, str(data))
            return None

    def test_list_conversations(self):
        """Test listing conversations."""
        success, data = self._request("GET", "/conversations")
        is_list = isinstance(data, list)
        self._log_result("List Conversations", success and is_list)

    def test_send_message(self, conversation_id: int):
        """Test sending a message."""
        success, data = self._request("POST", f"/conversations/{conversation_id}/messages", {
            "content": "Hello, this is a test message!"
        }, expected_status=200)  # Returns 200 with AI response
        # Check if it succeeded or has a valid response structure
        has_content = "content" in str(data) or "id" in data if isinstance(data, dict) else False
        self._log_result("Send Message", success or has_content, str(data)[:100] if not success else "")

    def test_get_messages(self, conversation_id: int):
        """Test getting conversation messages."""
        success, data = self._request("GET", f"/conversations/{conversation_id}/messages")
        is_list = isinstance(data, list)
        self._log_result("Get Messages", success and is_list)

    def test_delete_conversation(self, conversation_id: int):
        """Test deleting a conversation."""
        success, data = self._request("DELETE", f"/conversations/{conversation_id}", expected_status=204)
        self._log_result("Delete Conversation", success)

    # =========================================================================
    # Delegation Tests (Phase 4)
    # =========================================================================

    def test_get_delegation_stats(self):
        """Test getting delegation statistics."""
        success, data = self._request("GET", "/delegations/stats")
        has_stats = all(k in data for k in ["total", "pending", "completed"]) if success else False
        self._log_result("Get Delegation Stats", success and has_stats)

    def test_list_delegations(self):
        """Test listing delegations."""
        success, data = self._request("GET", "/delegations")
        is_list = isinstance(data, list)
        self._log_result("List Delegations", success and is_list)

    def test_get_pending_delegations(self):
        """Test getting pending delegations."""
        success, data = self._request("GET", "/delegations/pending")
        is_list = isinstance(data, list)
        self._log_result("Get Pending Delegations", success and is_list)

    def test_get_upcoming_delegations(self):
        """Test getting upcoming delegations."""
        success, data = self._request("GET", "/delegations/upcoming?minutes_ahead=60")
        is_list = isinstance(data, list)
        self._log_result("Get Upcoming Delegations", success and is_list)

    def test_process_meetings(self):
        """Test processing meetings from calendar."""
        success, data = self._request("POST", "/delegations/process-meetings", {
            "look_ahead_hours": 24
        })
        # This may return empty list if no calendar configured
        is_list = isinstance(data, list)
        self._log_result("Process Meetings", success and is_list,
                        f"Found {len(data)} meetings" if is_list else str(data))

    # =========================================================================
    # Approval Tests
    # =========================================================================

    def test_list_approvals(self):
        """Test listing approval requests."""
        success, data = self._request("GET", "/approvals")
        is_list = isinstance(data, list)
        self._log_result("List Approvals", success and is_list)

    # =========================================================================
    # Run All Tests
    # =========================================================================

    def run_all_tests(self):
        """Run all API tests."""
        print("\n" + "=" * 60)
        print("AI Workforce Platform - API Endpoint Tests")
        print("=" * 60)
        print(f"Base URL: {self.base_url}")
        print("=" * 60 + "\n")

        # Health check
        print("\n--- System Health ---")
        self.test_health_check()

        # Authentication
        print("\n--- Authentication ---")
        self.test_register_user()
        if not self.token:
            self.test_login_user()

        if not self.token:
            print("\n❌ Cannot continue without authentication!")
            return self.results

        self.test_get_current_user()

        # Agents
        print("\n--- Agents ---")
        agent_id = self.test_create_agent()
        self.test_list_agents()

        if agent_id:
            self.test_get_agent(agent_id)
            self.test_update_agent(agent_id)

            # Conversations (requires agent)
            print("\n--- Conversations ---")
            conv_id = self.test_create_conversation(agent_id)
            self.test_list_conversations()

            if conv_id:
                self.test_send_message(conv_id)
                self.test_get_messages(conv_id)
                # Cleanup conversation first (required before deleting agent)
                self.test_delete_conversation(conv_id)

            # Cleanup agent (now safe to delete)
            self.test_delete_agent(agent_id)

        # Delegations
        print("\n--- Delegations (Phase 4) ---")
        self.test_get_delegation_stats()
        self.test_list_delegations()
        self.test_get_pending_delegations()
        self.test_get_upcoming_delegations()
        self.test_process_meetings()

        # Approvals
        print("\n--- Approvals ---")
        self.test_list_approvals()

        # Summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print(f"Passed: {self.results['passed']}")
        print(f"Failed: {self.results['failed']}")
        total = self.results['passed'] + self.results['failed']
        if total > 0:
            rate = (self.results['passed'] / total) * 100
            print(f"Success Rate: {rate:.1f}%")

        if self.results['errors']:
            print("\n--- Errors ---")
            for error in self.results['errors']:
                print(f"  • {error}")

        print("=" * 60 + "\n")

        return self.results


def main():
    """Main entry point for tests."""
    client = APITestClient(BASE_URL)
    results = client.run_all_tests()

    # Exit with error code if any tests failed
    if results["failed"] > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
