import requests
import sys
import json
from datetime import datetime

class InitialPlacerAPITester:
    def __init__(self, base_url="https://life-explorer-2.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.user_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ PASS - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"   Response: {json.dumps(response_data, indent=2)[:200]}...")
                    return True, response_data
                except:
                    return True, {}
            else:
                print(f"❌ FAIL - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Error: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ FAIL - Exception: {str(e)}")
            return False, {}

    def test_options(self):
        """Test GET /api/placer/options"""
        success, response = self.run_test(
            "Get Placer Options",
            "GET",
            "placer/options",
            200
        )
        if success:
            # Verify required fields exist and are non-empty
            required_fields = ['income_brackets', 'education_levels', 'ethnicity_options']
            for field in required_fields:
                if field not in response or not response[field]:
                    print(f"❌ FAIL - Missing or empty {field}")
                    return False
            print(f"   ✓ All option lists populated")
        return success

    def test_signup(self):
        """Test POST /api/placer/signup"""
        test_data = {
            "first_name": "Test",
            "last_name": "User",
            "email": f"test_{datetime.now().strftime('%H%M%S')}@example.com",
            "interests": ["testing", "automation", "apis"]
        }
        
        success, response = self.run_test(
            "User Signup",
            "POST",
            "placer/signup",
            200,
            data=test_data
        )
        
        if success and 'id' in response:
            self.user_id = response['id']
            print(f"   ✓ User created with ID: {self.user_id}")
            return True
        return False

    def test_suggest_cards(self):
        """Test POST /api/placer/suggest"""
        if not self.user_id:
            print("❌ FAIL - No user_id available for suggest test")
            return False
            
        suggest_data = {
            "user_id": self.user_id,
            "count": 5
        }
        
        success, response = self.run_test(
            "Suggest Experience Cards",
            "POST",
            "placer/suggest",
            200,
            data=suggest_data
        )
        
        if success:
            if isinstance(response, list) and len(response) > 0:
                print(f"   ✓ Generated {len(response)} cards")
                # Check card structure
                card = response[0]
                required_fields = ['id', 'title', 'description']
                for field in required_fields:
                    if field not in card:
                        print(f"❌ FAIL - Card missing {field}")
                        return False
                print(f"   ✓ Cards have required structure")
                return True
            else:
                print(f"❌ FAIL - Expected array of cards, got: {type(response)}")
        return False

    def test_get_cards(self):
        """Test GET /api/placer/cards"""
        if not self.user_id:
            print("❌ FAIL - No user_id available for get cards test")
            return False
            
        success, response = self.run_test(
            "Get User Cards",
            "GET",
            "placer/cards",
            200,
            params={"user_id": self.user_id, "limit": 10}
        )
        
        if success:
            if isinstance(response, list) and len(response) >= 1:
                print(f"   ✓ Retrieved {len(response)} cards")
                return True
            else:
                print(f"❌ FAIL - Expected at least 1 card, got {len(response) if isinstance(response, list) else 0}")
        return False

    def test_swipe(self):
        """Test POST /api/placer/swipe"""
        if not self.user_id:
            print("❌ FAIL - No user_id available for swipe test")
            return False
            
        # First get a card to swipe on
        try:
            cards_response = requests.get(f"{self.base_url}/placer/cards", 
                                        params={"user_id": self.user_id, "limit": 1})
            if cards_response.status_code == 200:
                cards = cards_response.json()
                if cards and len(cards) > 0:
                    card_id = cards[0]['id']
                    
                    swipe_data = {
                        "user_id": self.user_id,
                        "card_id": card_id,
                        "direction": "left"
                    }
                    
                    success, response = self.run_test(
                        "Swipe Card",
                        "POST",
                        "placer/swipe",
                        200,
                        data=swipe_data
                    )
                    
                    if success and 'id' in response:
                        print(f"   ✓ Swipe recorded with ID: {response['id']}")
                        return True
                else:
                    print("❌ FAIL - No cards available to swipe")
            else:
                print("❌ FAIL - Could not fetch cards for swipe test")
        except Exception as e:
            print(f"❌ FAIL - Exception in swipe test: {str(e)}")
        return False

def main():
    print("🚀 Starting Initial Placer API Tests")
    print("=" * 50)
    
    tester = InitialPlacerAPITester()
    
    # Run all tests in sequence
    tests = [
        tester.test_options,
        tester.test_signup,
        tester.test_suggest_cards,
        tester.test_get_cards,
        tester.test_swipe
    ]
    
    for test in tests:
        test()
        print("-" * 30)
    
    # Print final results
    print(f"\n📊 FINAL RESULTS")
    print(f"Tests passed: {tester.tests_passed}/{tester.tests_run}")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 ALL TESTS PASSED!")
        return 0
    else:
        print("❌ SOME TESTS FAILED!")
        return 1

if __name__ == "__main__":
    sys.exit(main())