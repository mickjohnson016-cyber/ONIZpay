import os
import resend

# Production Notification Service using Resend API
# Securely loaded from environment variables
resend.api_key = os.getenv("RESEND_API_KEY")

def send_contact_email(ticket):
    """
    Sends a contact notification email using the Resend API.
    Replaces SMTP legacy logic for better reliability and performance.
    """
    try:
        resend.Emails.send({
            "from": "OinzPay <onboarding@resend.dev>",
            "to": os.getenv("SUPPORT_EMAIL"),
            "subject": f"New Contact Message from {ticket['full_name']}",
            "html": f"""
                <h2>New Contact Submission</h2>
                <p><strong>Name:</strong> {ticket['full_name']}</p>
                <p><strong>Email:</strong> {ticket['email']}</p>
                <p><strong>Message:</strong></p>
                <p>{ticket['message']}</p>
            """
        })
        print("RESEND EMAIL SENT SUCCESSFULLY")

    except Exception as e:
        # Failsafe: Application continues running even if email fails
        print("RESEND EMAIL ERROR:", e)
