import pytest
from io import BytesIO

"""
=========================================================
SOFTWARE ENGINEERING MILESTONE: AI FEATURE API TESTING
=========================================================
This test suite covers the AI Rate Updater APIs.

REQUIREMENT SATISFACTION:
1. "Proper test cases to test an API" -> Implemented below using Pytest.
2. "Include input, expected output, actual output" -> Documented in docstrings.
3. "Showcase an API where actual and expected outputs differ" -> See `test_confirm_approval_silently_ignores_invalid_skus`.

=========================================================
"""

def test_get_vendors(client, auth_headers):
    """
    Test Case 1: Fetching allowed vendors for the AI Feature.
    
    INPUT: 
        - GET Request to "/api/ai-feature/vendors"
        - Headers: Valid Bearer Token
        
    EXPECTED OUTPUT: 
        - Status Code: 200 OK
        - JSON Body: A list of vendor dictionaries (e.g., [{'vid': 'V1', 'vendor_name': 'Test'}])
        
    ACTUAL OUTPUT: 
        - Matches Expected exactly. Returns 200 OK and properly serialized vendor lists.
    """
    response = client.get('/api/ai-feature/vendors', headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)


def test_upload_missing_file_or_vendor(client, auth_headers):
    """
    Test Case 2: Uploading without providing a required PDF file.
    
    INPUT: 
        - POST Request to "/api/ai-feature/upload"
        - FormData: vendor_id="1" (Missing 'pdf' file parameter)
        
    EXPECTED OUTPUT: 
        - Status Code: 400 Bad Request
        - JSON Body: {"error": "Missing vendor_id or pdf file"}
        
    ACTUAL OUTPUT: 
        - Matches Expected exactly. Returns 400 with the error string.
    """
    data = {
        'vendor_id': '1'
        # Intentionally omitting the 'pdf' file
    }
    response = client.post(
        '/api/ai-feature/upload', 
        headers=auth_headers, 
        data=data,
        content_type='multipart/form-data'
    )
    assert response.status_code == 400
    assert "error" in response.get_json()


def test_check_job_status_invalid_id(client, auth_headers):
    """
    Test Case 3: Checking status of a non-existent Celery Job.
    
    INPUT: 
        - GET Request to "/api/ai-feature/status/invalid-job-id-12345"
        
    EXPECTED OUTPUT: 
        - Status Code: 200 OK (Celery returns PENDING for unknown IDs)
        - JSON Body: {"state": "PENDING", ...}
        
    ACTUAL OUTPUT: 
        - Matches Expected. Celery defaults to PENDING state if an ID isn't in Redis.
    """
    response = client.get('/api/ai-feature/status/invalid-job-id-12345', headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data['state'] == 'PENDING'


@pytest.mark.xfail(reason="Demonstrating Expected vs Actual Discrepancy")
def test_confirm_approval_silently_ignores_invalid_skus(client, auth_headers):
    """
    Test Case 4: (SHOWCASING DIFFERENCE) Submitting invalid SKU IDs during approval.
    
    SCENARIO: 
        The frontend accidentally attempts to approve a price update for a SKU that 
        does not exist in the database (e.g., deleted recently).
        
    INPUT:
        - POST Request to "/api/ai-feature/confirm"
        - JSON Body: 
            {
              "approved_matches": [
                 {"sku_id": "9999999", "price": 500}
              ]
            }
            
    EXPECTED OUTPUT: 
        - Status Code: 400 Bad Request or 404 Not Found.
        - The API should alert the client that they tried to update a missing SKU!
        
    ACTUAL OUTPUT (What the code currently does): 
        - Status Code: 200 OK.
        - BUG EXPLANATION: The loop in `api.py` queries `sku = SKU.query.get(sku_id)`. 
          If `sku` is None, it just safely ignores it and moves to the next element. 
          It commits the transaction and successfully returns {"message": "Prices updated"}.
          
    HOW TESTING HELPS:
        This test officially captures a silent failure discrepancy. 
        It proves to the development team that the API needs an update to return 
        validation warnings or a 207 Multi-Status instead of blindly returning 200 OK!
    """
    payload = {
        "approved_matches": [
            {"sku_id": "NON_EXISTENT_GHOST_SKU", "price": 500}
        ]
    }
    
    response = client.post(
        '/api/ai-feature/confirm', 
        headers=auth_headers, 
        json=payload
    )
    
    # We EXPECT the API to protect against this and return a 400 Bad Request error.
    # However, because of the silent-ignore bug in our implementation, 
    # it actually returns 200 OK! Therefore, this assertion fails,
    # showcasing the difference between Expected and Actual behavior.
    assert response.status_code == 400, f"Expected 400 Bad Request, but got {response.status_code} OK (silent ignore)"
