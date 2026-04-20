"""
Phase 186 companion — scheduled daily sweep that captures off-session
charges for every upcoming booking whose `eventDate` is today.

Only touches the `bookings_v2` Firestore collection (the V2 card-on-file
path, introduced with Phase 85). Legacy `bookings` collection is
unaffected — that flow still charges immediately via
`confirmBookingAndPay`.

Deploy: `firebase deploy --only functions:captureBookingsDaily`

Schedule string is Unix cron. `0 8 * * *` = 08:00 daily.

Stripe fee math mirrors `makeClientPayment_fn` in stripe_eps/make_payment.py:
    grossCharge = amount * .039 + 30 cents   (client pays)
    stripeFee   = amount * .029 + 30 cents   (Stripe takes)
    platformFee = grossCharge - stripeFee    (= 1% of amount)
so the vendor receives `amount` intact and the platform pockets 1%.
"""

import os
import stripe
import traceback
from datetime import datetime, timedelta, timezone

from firebase_functions import scheduler_fn
from common import *
from settings import (
    lg,
    STRIPE_SECRET_KEY,
    stripe_vendors_collection,
    stripe_clients_collection,
    stripe_receipts_collection,
)

BOOKINGS_V2 = "bookings_v2"
USERS_V2 = "users_v2"


def _capture_one(doc):
    """Charge a single booking. Writes status back to the doc + a
    receipt. Swallows Stripe errors so one bad booking doesn't stop
    the sweep."""
    booking = doc.to_dict() or {}
    booking_id = doc.id

    client_id = booking.get("clientId")
    vendor_id = booking.get("vendorId")
    pm_id = booking.get("paymentMethodId")
    amount = int(booking.get("priceCents") or 0)

    if not client_id or not vendor_id or not pm_id or amount <= 0:
        lg.w(f"[captureBookingsDaily] {booking_id} missing fields; skipping")
        fdb.collection(BOOKINGS_V2).document(booking_id).update({
            "paymentStatus": "failed",
            "paymentError": "missing fields",
            "captureAttemptedAt": datetime.now(timezone.utc),
        })
        return

    # Resolve Stripe ids from the legacy Stripe collections that
    # `createClientStripeCustomer` and `createVendorStripeAccountOnboarding`
    # already write to.
    client_doc = fdb.collection(stripe_clients_collection).document(client_id).get()
    vendor_doc = fdb.collection(stripe_vendors_collection).document(vendor_id).get()
    if not client_doc.exists or not vendor_doc.exists:
        lg.w(f"[captureBookingsDaily] {booking_id} missing stripe doc")
        fdb.collection(BOOKINGS_V2).document(booking_id).update({
            "paymentStatus": "failed",
            "paymentError": "missing stripe account",
            "captureAttemptedAt": datetime.now(timezone.utc),
        })
        return

    client_stripe_customer_id = (client_doc.to_dict() or {}).get("stripe_customer_id")
    vendor_stripe_account_id = (vendor_doc.to_dict() or {}).get("stripe_account_id")
    if not client_stripe_customer_id or not vendor_stripe_account_id:
        fdb.collection(BOOKINGS_V2).document(booking_id).update({
            "paymentStatus": "failed",
            "paymentError": "missing stripe ids",
            "captureAttemptedAt": datetime.now(timezone.utc),
        })
        return

    # Fee math matches makeClientPayment_fn.
    stripe_fee_base = int(round(amount * 0.029 + 30))
    four_percent_fee_plus_base = int(round(amount * 0.039 + 30))
    platform_profit = four_percent_fee_plus_base - stripe_fee_base

    try:
        intent = stripe.PaymentIntent.create(
            amount=four_percent_fee_plus_base,
            currency="usd",
            customer=client_stripe_customer_id,
            payment_method=pm_id,
            confirm=True,
            off_session=True,
            on_behalf_of=vendor_stripe_account_id,
            transfer_data={"destination": vendor_stripe_account_id},
            application_fee_amount=platform_profit,
            metadata={
                "bookingId": booking_id,
                "clientId": client_id,
                "vendorId": vendor_id,
                "source": "captureBookingsDaily",
            },
            idempotency_key=f"capture-{booking_id}-{datetime.now(timezone.utc):%Y%m%d}",
        )
    except stripe.error.CardError as e:
        # Declined, insufficient funds, etc.
        lg.e(f"[captureBookingsDaily] {booking_id} card error: {e}")
        fdb.collection(BOOKINGS_V2).document(booking_id).update({
            "paymentStatus": "failed",
            "paymentError": str(e.user_message or e),
            "captureAttemptedAt": datetime.now(timezone.utc),
        })
        return
    except Exception as e:
        lg.e(f"[captureBookingsDaily] {booking_id} stripe error: {e}")
        fdb.collection(BOOKINGS_V2).document(booking_id).update({
            "paymentStatus": "failed",
            "paymentError": str(e),
            "captureAttemptedAt": datetime.now(timezone.utc),
        })
        return

    status = intent.status

    if status == "succeeded":
        fdb.collection(BOOKINGS_V2).document(booking_id).update({
            "paymentStatus": "captured",
            "paymentIntentId": intent.id,
            "capturedAt": datetime.now(timezone.utc),
        })
        # Write a receipt row so the payment history page picks it up.
        fdb.collection(stripe_receipts_collection).document(intent.id).set({
            "createTime": datetime.now(timezone.utc),
            "client_stripe_customer_id": client_stripe_customer_id,
            "client_payment_method_id": pm_id,
            "client_user_id": client_id,
            "vendor_stripe_account_id": vendor_stripe_account_id,
            "vendor_user_id": vendor_id,
            "payment_amount_cents": amount,
            "payment_intent_id": intent.id,
            "booking_id": booking_id,
            "service_name": booking.get("serviceName", ""),
            "vendor_business_name": booking.get("vendorBusinessName", ""),
            "source": "captureBookingsDaily",
        })
        lg.t(f"[captureBookingsDaily] {booking_id} captured {intent.id}")
        return

    if status == "requires_action":
        # 3DS prompt — client needs to finish auth through flutter_stripe.
        fdb.collection(BOOKINGS_V2).document(booking_id).update({
            "paymentStatus": "requires_action",
            "paymentIntentId": intent.id,
            "paymentIntentClientSecret": intent.client_secret,
            "captureAttemptedAt": datetime.now(timezone.utc),
        })
        lg.w(f"[captureBookingsDaily] {booking_id} needs 3DS")
        return

    # Any other non-success state (requires_payment_method, canceled, etc.)
    fdb.collection(BOOKINGS_V2).document(booking_id).update({
        "paymentStatus": "failed",
        "paymentIntentId": intent.id,
        "paymentError": f"intent status {status}",
        "captureAttemptedAt": datetime.now(timezone.utc),
    })


@scheduler_fn.on_schedule(
    schedule="0 8 * * *",
    timezone=scheduler_fn.Timezone("America/Los_Angeles"),
    secrets=["STRIPE_SECRET_KEY"],
)
def captureBookingsDaily(event: scheduler_fn.ScheduledEvent) -> None:
    """Run daily at 08:00 America/Los_Angeles. Captures every
    `bookings_v2` doc whose status is 'upcoming', paymentStatus is
    'card_on_file', and eventDate is before tomorrow (today plus any
    carry-over from yesterday's failures)."""
    stripe.api_key = STRIPE_SECRET_KEY or os.environ.get("STRIPE_SECRET_KEY", "")
    if not stripe.api_key:
        lg.e("[captureBookingsDaily] STRIPE_SECRET_KEY missing")
        return

    now = datetime.now(timezone.utc)
    tomorrow = now + timedelta(days=1)

    snap = (
        fdb.collection(BOOKINGS_V2)
        .where("status", "==", "upcoming")
        .where("paymentStatus", "==", "card_on_file")
        .where("eventDate", "<", tomorrow)
        .stream()
    )

    count = 0
    for doc in snap:
        try:
            _capture_one(doc)
            count += 1
        except Exception as e:
            lg.e(f"[captureBookingsDaily] unexpected error on {doc.id}: {e}")
            lg.e(traceback.format_exc())

    lg.t(f"[captureBookingsDaily] processed {count} bookings")
