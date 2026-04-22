import os
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

def get_gmail_service():
    """Authenticates and returns the Gmail API service."""
    creds = None
    
    # Paths to credentials and token files
    # Placing them in the backend root for simplicity (adjustable)
    backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    token_path = os.path.join(backend_root, "token.json")
    creds_path = os.path.join(backend_root, "credentials.json")

    # Load existing token if available
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    
    # If there are no (valid) credentials available, attempt to refresh or start flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(creds_path):
                # Raise an informative error if credentials.json is missing
                raise FileNotFoundError(
                    f"Gmail credentials not found at {creds_path}. "
                    "Please refer to GMAIL_SETUP.md to set up your credentials."
                )
            
            # This will open a browser window for authentication
            # Note: In a headless environment, this may need adjustment
            flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open(token_path, "w") as token:
            token.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def send_vendor_order_email(vendor_email, part_name, quantity, total_amount, order_id, specification=None):
    """
    Constructs and sends an order notification email to a vendor.
    
    Args:
        vendor_email (str): Recipient's email address.
        part_name (str): Name of the part ordered.
        quantity (int): Number of units ordered.
        total_amount (float/Decimal): Total cost of the order.
        order_id (str): Reference ID for the order.
        specification (str, optional): Product specifications.
    """
    if not vendor_email:
        print(f"Skipping email for order {order_id}: No vendor email provided.")
        return False

    try:
        service = get_gmail_service()
        
        subject = f"New Purchase Order: {order_id} - Metro Hardware"
        
        # Format specification line
        spec_line = f"Specification:   {specification}\n" if specification else ""

        # Professional email body
        body = f"""
Dear Vendor,

We have placed a new order for parts. Please find the details below:

--------------------------------------------------
Order Reference: {order_id}
Part Name:       {part_name}
{spec_line}Quantity:        {quantity}
Total Amount:    Rs. {float(total_amount):,.2f}
--------------------------------------------------

Kindly confirm the receipt of this order and reply with an estimated delivery schedule.

Thank you,
Procurement Team
Metro Hardware Store
"""

        message = MIMEText(body)
        message["to"] = vendor_email
        message["subject"] = subject
        
        # Encode the message for the Gmail API
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        
        send_request = {
            "raw": raw_message
        }
        
        service.users().messages().send(userId="me", body=send_request).execute()
        print(f"Email successfully sent to {vendor_email} for order {order_id}")
        return True

    except Exception as e:
        # We log the error but don't crash the main procurement flow if email fails
        print(f"CRITICAL: Failed to send email to {vendor_email}: {e}")
        return False


def send_customer_shipment_email(customer_email, invoice_id, items, grand_total, order_id, invoice_html=None):
    """
    Constructs and sends a shipment notification email to a customer.
    
    Args:
        customer_email (str): Recipient's email address.
        invoice_id (str): Reference ID for the shipment invoice.
        items (list): List of dicts with {name, specs, qty, price, amount}.
        grand_total (float): Total amount of the invoice.
        order_id (str): Reference ID for the customer order.
        invoice_html (str, optional): Rich HTML invoice content from frontend.
    """
    if not customer_email:
        print(f"Skipping customer email for invoice {invoice_id}: No email provided.")
        return False

    try:
        service = get_gmail_service()
        subject = f"Your Order {order_id} has Shipped! - Invoice {invoice_id}"

        # Build items table (Plain Text version)
        table_header = f"{'Product':<30} {'Specs':<20} {'Qty':<5} {'Total (Rs.)':>12}\n"
        table_divider = "-" * 70 + "\n"
        item_rows = ""
        for item in items:
            name = (item['name'][:27] + '...') if len(item['name']) > 30 else item['name']
            specs = (item['specs'][:17] + '...') if len(item['specs']) > 20 else item['specs']
            item_rows += f"{name:<30} {specs:<20} {item['qty']:<5} {float(item['amount']):>12,.2f}\n"

        body_text = f"""
Dear Customer,

Great news! Your order has been shipped. Please find your invoice details below:

----------------------------------------------------------------------
Order Reference: {order_id}
Invoice Number:  {invoice_id}
----------------------------------------------------------------------

{table_header}{table_divider}{item_rows}{table_divider}
Grand Total:                                           Rs. {float(grand_total):,.2f}
----------------------------------------------------------------------

Please confirm receipt once the shipment arrives.

Thank you for shopping with us!
Metro Hardware Store
"""

        message = MIMEMultipart("alternative")
        message["to"] = customer_email
        message["subject"] = subject

        # Attach text version
        part1 = MIMEText(body_text, "plain")
        message.attach(part1)

        # Attach HTML version if available
        if invoice_html:
            # We wrap the frontend invoice HTML with our friendly message
            full_html = f"""
            <html>
                <body style="font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #333; line-height: 1.6;">
                    <div style="max-width: 800px; margin: 0 auto; padding: 20px;">
                        <h2 style="color: #2563eb;">Great news! Your order has been shipped.</h2>
                        <p>Dear Customer,</p>
                        <p>We are pleased to inform you that your order <strong>{order_id}</strong> has been dispatched. Please find your official invoice below.</p>
                        <hr style="border: none; border-top: 1px solid #eee; margin: 25px 0;">
                        
                        <!-- Embedded Frontend Invoice -->
                        {invoice_html}
                        
                        <p style="margin-top: 30px;">Please confirm receipt once the shipment arrives.</p>
                        <p>Thank you for shopping with us!<br><strong>Metro Hardware Store</strong></p>
                    </div>
                </body>
            </html>
            """
            part2 = MIMEText(full_html, "html")
            message.attach(part2)
        else:
            # Fallback to simple HTML if frontend didn't send one (shouldn't happen with new UI)
            simple_html = f"<html><body><pre>{body_text}</pre></body></html>"
            part2 = MIMEText(simple_html, "html")
            message.attach(part2)
        
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        send_request = {"raw": raw_message}
        
        service.users().messages().send(userId="me", body=send_request).execute()
        print(f"Shipment notification sent to {customer_email} for invoice {invoice_id}")
        return True

    except Exception as e:
        print(f"CRITICAL: Failed to send shipment email to {customer_email}: {e}")
        return False
