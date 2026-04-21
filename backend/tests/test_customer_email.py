import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add the backend directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.utils.email_utils import send_customer_shipment_email

class TestCustomerEmail(unittest.TestCase):

    @patch("app.utils.email_utils.get_gmail_service")
    def test_send_customer_shipment_email_content(self, mock_get_service):
        # Setup mock
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service
        
        # Test data
        customer_email = "test_customer@example.com"
        invoice_id = "INV-TEST123"
        order_id = "CO-TEST456"
        items = [
            {"name": "Hammer", "specs": "16oz Wood Handle", "qty": 2, "amount": 500.0},
            {"name": "Nails", "specs": "2 inch Steel", "qty": 1, "amount": 150.0}
        ]
        grand_total = 650.0

        # Execute
        result = send_customer_shipment_email(customer_email, invoice_id, items, grand_total, order_id)

        # Assertions
        self.assertTrue(result)
        mock_service.users().messages().send.assert_called_once()
        
        # Verify the message content (requires decoding)
        call_args = mock_service.users().messages().send.call_args
        raw_message = call_args[1]['body']['raw']
        
        import base64
        decoded_message = base64.urlsafe_b64decode(raw_message).decode()
        
        # Check for key content
        self.assertIn(f"Order Reference: {order_id}", decoded_message)
        self.assertIn(f"Invoice Number:  {invoice_id}", decoded_message)
        self.assertIn("Hammer", decoded_message)
        self.assertIn("16oz Wood Handle", decoded_message)
        self.assertIn("Grand Total:                                           Rs. 650.00", decoded_message)
        self.assertIn("Please confirm receipt once the shipment arrives.", decoded_message)
        self.assertIn("Metro Hardware Store", decoded_message)

    @patch("app.utils.email_utils.get_gmail_service")
    def test_send_customer_shipment_email_no_email(self, mock_get_service):
        result = send_customer_shipment_email(None, "INV-123", [], 0, "CO-456")
        self.assertFalse(result)
        mock_get_service.assert_not_called()

if __name__ == "__main__":
    unittest.main()
