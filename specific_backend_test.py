#!/usr/bin/env python3

import requests
import sys
import json
import time

class SpecificAPITester:
    def __init__(self, base_url="https://life-explorer-2.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api"
        self.user_id = None
        self.cards = []

    def test_1_signup(self):
        """Test 1: Create user with minimal body {first_name, last_name, email, interests}"""
        print("🔍 Test 1: POST /api/placer/signup with minimal body")
        
        payload = {
            "first_name": "Test",
            "last_name": "User", 
            "email": f"test.{int(time.time())}@example.com",
            "interests": ["technology", "music"]
        }
        
        try:
            response = requests.post(
                f"{self.api_base}/placer/signup",
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                self.user_id = data.get('id')
                print(f"   ✅ PASS - User ID captured: {self.user_id}")
                return True
            else:
                print(f"   ❌ FAIL - HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ FAIL - Exception: {str(e)}")
            return False

    def test_2_suggest(self):
        """Test 2: POST /api/placer/suggest with {user_id: <id>, count: 4}"""
        print(f"🔍 Test 2: POST /api/placer/suggest with user_id={self.user_id}, count=4")
        
        if not self.user_id:
            print("   ❌ FAIL - No user_id available")
            return False
            
        payload = {
            "user_id": self.user_id,
            "count": 4
        }
        
        try:
            response = requests.post(
                f"{self.api_base}/placer/suggest",
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and 1 <= len(data) <= 4:
                    print(f"   ✅ PASS - Generated {len(data)} cards (expected 1-4)")
                    return True
                else:
                    print(f"   ❌ FAIL - Expected 1-4 cards, got {len(data) if isinstance(data, list) else 'non-list'}")
                    print(f"   Response: {response.text}")
                    return False
            else:
                print(f"   ❌ FAIL - HTTP {response.status_code}")
                print(f"   Response body: {response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ FAIL - Exception: {str(e)}")
            return False

    def test_3_get_cards(self):
        """Test 3: GET /api/placer/cards?user_id=<id>&limit=10"""
        print(f"🔍 Test 3: GET /api/placer/cards?user_id={self.user_id}&limit=10")
        
        if not self.user_id:
            print("   ❌ FAIL - No user_id available")
            return False
            
        try:
            response = requests.get(
                f"{self.api_base}/placer/cards",
                params={"user_id": self.user_id, "limit": 10},
                timeout=30
            )
            
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) >= 1:
                    self.cards = data
                    print(f"   ✅ PASS - Retrieved {len(data)} cards (expected >=1)")
                    return True
                else:
                    print(f"   ❌ FAIL - Expected >=1 cards, got {len(data) if isinstance(data, list) else 'non-list'}")
                    return False
            else:
                print(f"   ❌ FAIL - HTTP {response.status_code}")
                print(f"   Response body: {response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ FAIL - Exception: {str(e)}")
            return False

    def test_4_swipe_left(self):
        """Test 4: POST /api/placer/swipe with direction left for first card"""
        print("🔍 Test 4: POST /api/placer/swipe with direction=left for first card")
        
        if not self.user_id:
            print("   ❌ FAIL - No user_id available")
            return False
            
        if not self.cards:
            print("   ❌ FAIL - No cards available")
            return False
            
        first_card = self.cards[0]
        payload = {
            "user_id": self.user_id,
            "card_id": first_card['id'],
            "direction": "left"
        }
        
        try:
            response = requests.post(
                f"{self.api_base}/placer/swipe",
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                print(f"   ✅ PASS - Successfully swiped left on card: {first_card.get('title', 'Unknown')}")
                return True
            else:
                print(f"   ❌ FAIL - HTTP {response.status_code}")
                print(f"   Response body: {response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ FAIL - Exception: {str(e)}")
            return False

    def run_specific_tests(self):
        """Run the specific tests requested in the review"""
        print("🚀 Running Specific Backend API Tests as Requested")
        print("=" * 60)
        
        results = []
        
        # Test 1: Signup
        results.append(self.test_1_signup())
        print()
        
        # Test 2: Suggest (only if signup passed)
        if results[0]:
            results.append(self.test_2_suggest())
        else:
            results.append(False)
        print()
        
        # Test 3: Get cards (only if suggest passed)
        if results[1]:
            results.append(self.test_3_get_cards())
        else:
            results.append(False)
        print()
        
        # Test 4: Swipe left (only if get cards passed)
        if results[2]:
            results.append(self.test_4_swipe_left())
        else:
            results.append(False)
        print()
        
        # Summary
        print("=" * 60)
        print("📊 SPECIFIC TEST RESULTS:")
        test_names = ["Signup", "Suggest", "Get Cards", "Swipe Left"]
        for i, (name, result) in enumerate(zip(test_names, results)):
            status = "PASS" if result else "FAIL"
            print(f"   {i+1}. {name}: {status}")
        
        passed = sum(results)
        total = len(results)
        print(f"\nOverall: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 ALL SPECIFIC BACKEND TESTS PASSED!")
            return 0
        else:
            print("⚠️  SOME SPECIFIC BACKEND TESTS FAILED!")
            return 1

def main():
    tester = SpecificAPITester()
    return tester.run_specific_tests()

if __name__ == "__main__":
    sys.exit(main())