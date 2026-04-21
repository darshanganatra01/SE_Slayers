import unittest
from unittest.mock import MagicMock, patch
from app.utils.email_utils import send_vendor_order_email

class TestEmailLogic(unittest.TestCase):

    @patch('app.utils.email_utils.get_gmail_service')
    def test_send_vendor_order_email_success(self, mock_get_service):
        # Mock the Gmail API service
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service
        
        # mock_service.users().messages().send(userId="me", body=send_request).execute()
        mock_send = mock_service.users().messages().send
        mock_execute = mock_send.return_value.execute
        
        # Define test data
        vendor_email = "vendor@example.com"
        part_name = "Steel Bolt"
        specification = "10mm Chrome"
        quantity = 50
        total_amount = 250.75
        order_id = "VO-12345"

        # Execute the function
        result = send_vendor_order_email(vendor_email, part_name, quantity, total_amount, order_id, specification=specification)

        # Assertions
        self.assertTrue(result)
        mock_get_service.assert_called_once()
        
        # Check if send was called with userId="me" and some body
        mock_send.assert_called_once()
        args, kwargs = mock_send.call_args
        self.assertEqual(kwargs['userId'], 'me')
        self.assertIn('raw', kwargs['body'])
        
        # Check if execute was called
        mock_execute.assert_called_once()

    @patch('app.utils.email_utils.get_gmail_service')
    def test_send_vendor_order_email_no_email(self, mock_get_service):
        # Should return False if email is missing
        result = send_vendor_order_email(None, "Steel Bolt", 50, 250.75, "VO-12345")
        self.assertFalse(result)
        mock_get_service.assert_not_called()

if __name__ == '__main__':
    unittest.main()
