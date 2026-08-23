import os
import logging
from django.conf import settings
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


def send_resend_email(to_email, subject, html_content):
    """
    Core Email Dispatcher using Resend API.
    Handles sandbox mode and logs output if RESEND_API_KEY is not yet configured.
    """
    if not to_email:
        logger.warning("[RESEND WARNING] No recipient email provided.")
        return {"status": "skipped", "reason": "No recipient email"}

    resend_api_key = getattr(settings, 'RESEND_API_KEY', '') or os.environ.get('RESEND_API_KEY', '')
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'TRUST Protocol <onboarding@resend.dev>')

    if not resend_api_key:
        logger.info(f"[RESEND SANDBOX LOG] Simulated email to {to_email} | Subject: '{subject}'")
        return {"status": "simulated", "to": to_email, "subject": subject}

    try:
        import resend
        resend.api_key = resend_api_key
        params = {
            "from": from_email,
            "to": [to_email],
            "subject": subject,
            "html": html_content,
        }
        email_resp = resend.Emails.send(params)
        logger.info(f"[RESEND SUCCESS] Email sent to {to_email}: {email_resp}")
        return email_resp
    except Exception as e:
        logger.error(f"[RESEND ERROR] Dispatch failed to {to_email}: {str(e)}")
        return {"status": "error", "error": str(e)}


def send_tenant_welcome_email(user, site_url="http://127.0.0.1:8000"):
    """Template 1: Tenant Welcome Email"""
    if not user.email:
        return
    subject = "Welcome to TRUST – Your Account is Ready"
    html_content = render_to_string("emails/tenant_welcome.html", {
        "user": user,
        "site_url": site_url,
    })
    return send_resend_email(user.email, subject, html_content)


def send_landlord_welcome_email(user, site_url="http://127.0.0.1:8000"):
    """Template 2: Landlord Application Received Email"""
    if not user.email:
        return
    subject = "Welcome to TRUST – Landlord Application Received"
    html_content = render_to_string("emails/landlord_welcome.html", {
        "user": user,
        "site_url": site_url,
    })
    return send_resend_email(user.email, subject, html_content)


def send_landlord_approved_email(user, site_url="http://127.0.0.1:8000"):
    """Template 3: Landlord Account Approved Email"""
    if not user.email:
        return
    subject = "Account Approved! Welcome to the TRUST Landlord Network"
    html_content = render_to_string("emails/landlord_approved.html", {
        "user": user,
        "site_url": site_url,
    })
    return send_resend_email(user.email, subject, html_content)


def send_property_approved_email(property_obj, site_url="http://127.0.0.1:8000"):
    """Template 4: Property Listing Approved Email (to Landlord)"""
    landlord = getattr(property_obj, 'owner', None)
    if not landlord or not landlord.email:
        return
    subject = f"Property Listing Live – {property_obj.title}"
    html_content = render_to_string("emails/property_approved.html", {
        "property": property_obj,
        "user": landlord,
        "site_url": site_url,
    })
    return send_resend_email(landlord.email, subject, html_content)


def send_property_revision_requested_email(property_obj, revision_notes="", site_url="http://127.0.0.1:8000"):
    """Template 5: Property Revision Required Email (to Landlord)"""
    landlord = getattr(property_obj, 'owner', None)
    if not landlord or not landlord.email:
        return
    subject = f"Action Required: Property Listing Revision – {property_obj.title}"
    html_content = render_to_string("emails/property_revision.html", {
        "property": property_obj,
        "revision_notes": revision_notes,
        "user": landlord,
        "site_url": site_url,
    })
    return send_resend_email(landlord.email, subject, html_content)


def send_tenant_payment_receipt_email(user, property_obj, amount, tracking_id, payment_purpose="Booking Commitment Fee", payment_method="Mobile Money", landlord=None, site_url="http://127.0.0.1:8000"):
    """Template 6: Tenant Payment Receipt Email (Tenant ONLY)"""
    recipient_email = getattr(user, 'email', '')
    if not recipient_email:
        return
    subject = f"Official Receipt – Payment #{tracking_id}"
    html_content = render_to_string("emails/tenant_payment_receipt.html", {
        "user": user,
        "property": property_obj,
        "amount": amount,
        "tracking_id": tracking_id,
        "payment_purpose": payment_purpose,
        "payment_method": payment_method,
        "landlord": landlord or getattr(property_obj, 'owner', None),
        "site_url": site_url,
    })
    return send_resend_email(recipient_email, subject, html_content)


def send_landlord_rent_received_email(landlord, property_obj, tenant_name, amount, tracking_id, rental_term="2 Months Rent", site_url="http://127.0.0.1:8000"):
    """Template 7: Landlord Rent Payment Received Alert (Landlord ONLY - Full Rent Payments Only)"""
    if not landlord or not landlord.email:
        return
    subject = f"Payment Confirmed: Rent Collected for {property_obj.title}"
    html_content = render_to_string("emails/landlord_rent_received.html", {
        "landlord": landlord,
        "property": property_obj,
        "tenant_name": tenant_name,
        "amount": amount,
        "tracking_id": tracking_id,
        "rental_term": rental_term,
        "site_url": site_url,
    })
    return send_resend_email(landlord.email, subject, html_content)
