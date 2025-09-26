#!/usr/bin/env python3

import requests
import json
import sys
from datetime import datetime
import time

class BachFlowerRemedyAPITester:
    def __init__(self, base_url="https://bloom-therapy-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        self.user_id = f"test_user_{int(time.time())}"
        self.selection_id = None

    def log_test(self, name, success, details="", response_data=None):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            status = "✅ PASSED"
        else:
            status = "❌ FAILED"
        
        result = {
            "test_name": name,
            "status": status,
            "success": success,
            "details": details,
            "response_data": response_data
        }
        self.test_results.append(result)
        print(f"{status} - {name}: {details}")
        return success

    def make_request(self, method, endpoint, data=None, expected_status=200):
        """Make HTTP request and handle response"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=30)
            else:
                return False, f"Unsupported method: {method}", None

            success = response.status_code == expected_status
            
            if success:
                try:
                    response_data = response.json()
                except:
                    response_data = response.text
            else:
                try:
                    error_data = response.json()
                    response_data = error_data
                except:
                    response_data = response.text

            details = f"Status: {response.status_code}"
            if not success:
                details += f", Expected: {expected_status}, Response: {str(response_data)[:200]}"

            return success, details, response_data

        except requests.exceptions.Timeout:
            return False, "Request timeout (30s)", None
        except requests.exceptions.ConnectionError:
            return False, "Connection error - backend may be down", None
        except Exception as e:
            return False, f"Request error: {str(e)}", None

    def test_basic_symptom_analysis(self):
        """Test basic symptom analysis with comma-separated symptoms"""
        print("\n🔍 Testing Basic Symptom Analysis...")
        
        test_data = {
            "symptoms": "anxiety, worry, fear, restlessness",
            "nlp_mode": False
        }
        
        success, details, response_data = self.make_request('POST', 'recommendations', test_data)
        
        if success and response_data:
            # Verify response structure
            required_fields = ['vector_recommendation', 'knowledge_graph_recommendation', 'symptoms_analyzed']
            missing_fields = [field for field in required_fields if field not in response_data]
            
            if missing_fields:
                success = False
                details += f", Missing fields: {missing_fields}"
            else:
                # Check if recommendations have proper structure
                vector_rec = response_data.get('vector_recommendation')
                graph_rec = response_data.get('knowledge_graph_recommendation')
                
                if vector_rec and 'remedy_name' in vector_rec and 'similarity_score' in vector_rec:
                    details += f", Vector: {vector_rec['remedy_name']} ({vector_rec['similarity_score']:.2f})"
                
                if graph_rec and 'remedy_name' in graph_rec and 'relevance_score' in graph_rec:
                    details += f", Graph: {graph_rec['remedy_name']} ({graph_rec['relevance_score']})"
        
        return self.log_test("Basic Symptom Analysis", success, details, response_data)

    def test_nlp_mode_analysis(self):
        """Test NLP mode with natural language input"""
        print("\n🔍 Testing NLP Mode Analysis...")
        
        test_data = {
            "symptoms": "I've been feeling overwhelmed at work, constantly worried about everything, and having trouble sleeping. I feel anxious and can't relax.",
            "nlp_mode": True
        }
        
        success, details, response_data = self.make_request('POST', 'recommendations', test_data)
        
        if success and response_data:
            # Verify NLP-specific fields
            if 'nlp_analysis' in response_data:
                nlp_data = response_data['nlp_analysis']
                if 'sentiment_polarity' in nlp_data and 'sentiment_subjectivity' in nlp_data:
                    sentiment = nlp_data['sentiment_polarity']
                    details += f", Sentiment: {sentiment:.2f}"
                else:
                    success = False
                    details += ", Missing NLP analysis fields"
            else:
                success = False
                details += ", Missing nlp_analysis in response"
        
        return self.log_test("NLP Mode Analysis", success, details, response_data)

    def test_save_remedy_selection(self):
        """Test saving remedy selection"""
        print("\n🔍 Testing Save Remedy Selection...")
        
        test_data = {
            "user_id": self.user_id,
            "symptoms": "stress, tension, overwhelm",
            "nlp_mode": False
        }
        
        success, details, response_data = self.make_request('POST', 'remedy-selections', test_data, 200)
        
        if success and response_data:
            if 'id' in response_data:
                self.selection_id = response_data['id']
                details += f", Selection ID: {self.selection_id}"
            else:
                success = False
                details += ", Missing selection ID in response"
        
        return self.log_test("Save Remedy Selection", success, details, response_data)

    def test_load_user_selections(self):
        """Test loading user selections"""
        print("\n🔍 Testing Load User Selections...")
        
        success, details, response_data = self.make_request('GET', f'remedy-selections/{self.user_id}')
        
        if success and response_data:
            if isinstance(response_data, list):
                details += f", Found {len(response_data)} selections"
                if len(response_data) > 0:
                    selection = response_data[0]
                    if 'recommendations' in selection and 'symptoms' in selection:
                        details += f", First selection: {selection['symptoms'][:30]}..."
                    else:
                        success = False
                        details += ", Invalid selection structure"
            else:
                success = False
                details += ", Response is not a list"
        
        return self.log_test("Load User Selections", success, details, response_data)

    def test_update_selection(self):
        """Test updating a remedy selection"""
        print("\n🔍 Testing Update Selection...")
        
        if not self.selection_id:
            return self.log_test("Update Selection", False, "No selection ID available (save test may have failed)")
        
        # The API expects updated_symptoms as query parameter, let's test with URL params
        url = f"{self.api_url}/remedy-selections/{self.selection_id}?updated_symptoms=updated symptoms: fatigue, exhaustion, burnout"
        headers = {'Content-Type': 'application/json'}
        
        try:
            response = requests.put(url, headers=headers, timeout=30)
            success = response.status_code == 200
            
            if success:
                try:
                    response_data = response.json()
                except:
                    response_data = response.text
            else:
                try:
                    response_data = response.json()
                except:
                    response_data = response.text
            
            details = f"Status: {response.status_code}"
            if not success:
                details += f", Response: {str(response_data)[:200]}"
                
        except Exception as e:
            success = False
            details = f"Request error: {str(e)}"
            response_data = None
        
        return self.log_test("Update Selection", success, details, response_data)

    def test_get_all_remedies(self):
        """Test getting all Bach flower remedies"""
        print("\n🔍 Testing Get All Remedies...")
        
        success, details, response_data = self.make_request('GET', 'remedies')
        
        if success and response_data:
            if 'remedies' in response_data:
                remedies = response_data['remedies']
                remedy_count = len(remedies)
                details += f", Found {remedy_count} remedies"
                
                # Verify we have all 38 Bach flower remedies
                if remedy_count == 38:
                    details += " (Complete set)"
                else:
                    details += f" (Expected 38)"
                
                # Check a few key remedies
                key_remedies = ['rescue_remedy', 'agrimony', 'aspen', 'beech']
                found_remedies = [r for r in key_remedies if r in remedies]
                details += f", Key remedies found: {len(found_remedies)}/{len(key_remedies)}"
            else:
                success = False
                details += ", Missing 'remedies' field in response"
        
        return self.log_test("Get All Remedies", success, details, response_data)

    def test_get_specific_remedy(self):
        """Test getting details for a specific remedy"""
        print("\n🔍 Testing Get Specific Remedy...")
        
        remedy_id = "rescue_remedy"
        success, details, response_data = self.make_request('GET', f'remedies/{remedy_id}')
        
        if success and response_data:
            if 'remedy' in response_data:
                remedy = response_data['remedy']
                if 'name' in remedy and 'symptoms' in remedy:
                    details += f", Remedy: {remedy['name']}"
                    if 'connected_remedies' in response_data:
                        connected_count = len(response_data['connected_remedies'])
                        details += f", Connected: {connected_count}"
                else:
                    success = False
                    details += ", Missing remedy fields"
            else:
                success = False
                details += ", Missing 'remedy' field in response"
        
        return self.log_test("Get Specific Remedy", success, details, response_data)

    def test_admin_add_knowledge_source(self):
        """Test adding knowledge source (admin functionality)"""
        print("\n🔍 Testing Admin Add Knowledge Source...")
        
        test_data = {
            "source_type": "text",
            "content": "Test knowledge source for Bach flower remedies testing",
            "source_url": "https://example.com/test"
        }
        
        success, details, response_data = self.make_request('POST', 'admin/knowledge-sources', test_data)
        
        if success and response_data:
            if 'id' in response_data and 'source_type' in response_data:
                details += f", Source ID: {response_data['id']}"
            else:
                success = False
                details += ", Missing required fields in response"
        
        return self.log_test("Admin Add Knowledge Source", success, details, response_data)

    def test_admin_get_knowledge_sources(self):
        """Test getting knowledge sources (admin functionality)"""
        print("\n🔍 Testing Admin Get Knowledge Sources...")
        
        success, details, response_data = self.make_request('GET', 'admin/knowledge-sources')
        
        if success and response_data:
            if isinstance(response_data, list):
                details += f", Found {len(response_data)} knowledge sources"
            else:
                success = False
                details += ", Response is not a list"
        
        return self.log_test("Admin Get Knowledge Sources", success, details, response_data)

    def test_admin_rebuild_knowledge_base(self):
        """Test rebuilding knowledge base (admin functionality)"""
        print("\n🔍 Testing Admin Rebuild Knowledge Base...")
        
        success, details, response_data = self.make_request('POST', 'admin/rebuild-knowledge-base', {})
        
        if success and response_data:
            if 'message' in response_data:
                details += f", Message: {response_data['message'][:50]}..."
            else:
                success = False
                details += ", Missing message in response"
        
        return self.log_test("Admin Rebuild Knowledge Base", success, details, response_data)

    def test_error_handling(self):
        """Test error handling with invalid inputs"""
        print("\n🔍 Testing Error Handling...")
        
        # Test invalid remedy ID
        success, details, response_data = self.make_request('GET', 'remedies/invalid_remedy', expected_status=404)
        error_test_1 = self.log_test("Error Handling - Invalid Remedy ID", success, details)
        
        # Test empty symptoms
        test_data = {"symptoms": "", "nlp_mode": False}
        success, details, response_data = self.make_request('POST', 'recommendations', test_data, expected_status=500)
        error_test_2 = self.log_test("Error Handling - Empty Symptoms", success, details)
        
        return error_test_1 and error_test_2

    def run_all_tests(self):
        """Run all backend API tests"""
        print("🚀 Starting Bach Flower Remedy API Tests")
        print(f"🌐 Testing against: {self.base_url}")
        print("=" * 60)
        
        # Core functionality tests
        self.test_basic_symptom_analysis()
        self.test_nlp_mode_analysis()
        self.test_save_remedy_selection()
        self.test_load_user_selections()
        self.test_update_selection()
        
        # Remedy database tests
        self.test_get_all_remedies()
        self.test_get_specific_remedy()
        
        # Admin functionality tests
        self.test_admin_add_knowledge_source()
        self.test_admin_get_knowledge_sources()
        self.test_admin_rebuild_knowledge_base()
        
        # Error handling tests
        self.test_error_handling()
        
        # Print summary
        print("\n" + "=" * 60)
        print(f"📊 Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        print(f"✅ Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed! Backend API is working correctly.")
            return 0
        else:
            print("⚠️  Some tests failed. Check the details above.")
            return 1

    def get_test_summary(self):
        """Get detailed test summary for reporting"""
        return {
            "total_tests": self.tests_run,
            "passed_tests": self.tests_passed,
            "failed_tests": self.tests_run - self.tests_passed,
            "success_rate": (self.tests_passed/self.tests_run)*100 if self.tests_run > 0 else 0,
            "test_results": self.test_results
        }

def main():
    tester = BachFlowerRemedyAPITester()
    exit_code = tester.run_all_tests()
    
    # Save detailed results
    summary = tester.get_test_summary()
    with open('/app/backend_test_results.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    return exit_code

if __name__ == "__main__":
    sys.exit(main())