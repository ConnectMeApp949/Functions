from flask import jsonify
from util.logger import lg_logger



import os

STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")

admin_utils_password = os.environ.get("ADMIN_UTILS_PASSWORD", "")

test_user_password = os.environ.get("TEST_USER_PASSWORD", "")



stripe_application_fee_amount_cents = 100  # e.g., $1.00 fee to your platform
stripe_refund_percent = .92


vendor_account_sub_status_string = "vendor_basic"

# whether to return exceptions when caught or use std_exception_response
debug_responses = False

log_level = 5

lg = lg_logger(log_level)




millisInMinute = 60000
sandboxMonthMillis = millisInMinute * 3
monthMillis = 2629746000
sandboxYearMillis = millisInMinute * 5
yearMillis = 31556952000




# Magic Strings
no_email_hash_seed_placeholder_email = "notfoundemail@placeholder.com" # set from client too used to keep consistent hash of email because uses userID in google_auth.py

# Collection Name Strings
user_collection = "users"
deleted_user_collection = "deleted_users"
booking_collection = "bookings"
service_collection = "services"
deleted_service_collection = "deleted_services"
thread_collection = "threads"
messages_sub_collection = "messages"
saved_provider_collection = "saved_providers"

rating_collection = "ratings"

stripe_vendors_collection = "stripe_vendors"
stripe_clients_collection = "stripe_clients"
stripe_receipts_collection = "stripe_receipts"

availability_collection = "availability"

report_collection = "reports"

def std_exception_response():
    return jsonify({"success": False, "reason": "error"}), 500