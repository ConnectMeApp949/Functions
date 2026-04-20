"""
Phase 191 — client-initiated retry of a failed booking capture.

The Phase 188 scheduled sweep `captureBookingsDaily` sets
`bookings_v2/{id}.paymentStatus = 'failed'` with a `paymentError`
when off-session capture fails (declined card, missing Stripe
account, etc.). This endpoint lets the client press a "Retry
payment" button on that booking to force a fresh capture attempt
without waiting for the next daily sweep.

Safety:
- `@uauth` decorator ensures the caller's userId + authToken match
  a real user doc.
- We additionally require the caller to be the booking's `clientId`
  — only the card holder can re-run a charge against their card.
- Only bookings currently in `paymentStatus == 'failed'` are eligible;
  `captured` / `requires_action` / `card_on_file` are rejected so the
  client can't accidentally double-charge.
- A monotonically-increasing `paymentRetryCount` on the booking doc
  drives the Stripe idempotency key so each retry gets a fresh key
  (Stripe's idempotency window is 24h — same key = cached prior
  response).
"""

import os
import stripe
import traceback
from datetime import datetime, timezone

from firebase_admin import firestore
from flask import jsonify
from common import fdb
from settings import lg, STRIPE_SECRET_KEY
from auth.auth_user_wrapper import uauth
from booking.capture_bookings_daily import capture_booking, BOOKINGS_V2


@uauth
def retryBookingCapture_fn(request):
    pdata = request.get_json() or {}
    user_id = pdata.get("userId")
    booking_id = pdata.get("bookingId")

    lg.t(f"[retryBookingCapture] user={user_id} booking={booking_id}")

    if not booking_id:
        return jsonify({"success": False, "error": "missing bookingId"}), 400

    stripe.api_key = STRIPE_SECRET_KEY or os.environ.get("STRIPE_SECRET_KEY", "")
    if not stripe.api_key:
        lg.e("[retryBookingCapture] STRIPE_SECRET_KEY missing")
        return jsonify({"success": False, "error": "server misconfigured"}), 500

    booking_ref = fdb.collection(BOOKINGS_V2).document(booking_id)
    doc = booking_ref.get()
    if not doc.exists:
        return jsonify({"success": False, "error": "booking not found"}), 404

    booking = doc.to_dict() or {}

    # Only the booking's client can retry its payment.
    if booking.get("clientId") != user_id:
        lg.w(f"[retryBookingCapture] {booking_id} caller {user_id} "
             f"!= clientId {booking.get('clientId')}")
        return jsonify({"success": False, "error": "not authorized"}), 403

    # Guard against double-charging a healthy booking.
    current_status = booking.get("paymentStatus")
    if current_status != "failed":
        return jsonify({
            "success": False,
            "error": f"booking paymentStatus is '{current_status}', "
                     "retry only valid from 'failed'",
        }), 409

    # Bump retry count atomically so concurrent presses don't collide
    # on the Stripe idempotency key.
    booking_ref.update({
        "paymentRetryCount": firestore.Increment(1),
        "paymentRetryAt": datetime.now(timezone.utc),
    })
    # Re-read to pick up the incremented counter for the idempotency key.
    doc = booking_ref.get()
    retry_count = (doc.to_dict() or {}).get("paymentRetryCount", 1)

    try:
        result = capture_booking(
            doc,
            attempt_suffix=f"retry-{retry_count}",
            source="retryBookingCapture",
        )
    except Exception as e:
        lg.e(f"[retryBookingCapture] {booking_id} unexpected: {e}")
        lg.e(traceback.format_exc())
        return jsonify({"success": False, "error": str(e)}), 500

    result = result or {}
    ok = result.get("status") in ("captured", "requires_action")
    return jsonify({
        "success": ok,
        "status": result.get("status"),
        "paymentIntentId": result.get("paymentIntentId"),
        "clientSecret": result.get("clientSecret"),
        "reason": result.get("reason"),
    })
