import os
import stripe
from google.cloud import firestore
from flask import Flask, request, jsonify
from settings import *
from auth.auth_user_wrapper import uauth
from common import *
from datetime import datetime, timezone
import traceback

@uauth
def getTransactionStripeAccountDetails_fn(request):
    try:
        data = request.json
        client_user_id = data.get("client_user_id")
        vendor_user_id = data.get("vendor_user_id")

        vendor_details = fdb.collection(stripe_vendors_collection).document(vendor_user_id).get().to_dict()
        client_details = fdb.collection(stripe_clients_collection).document(client_user_id).get().to_dict()

        parties_ready = True
        if not vendor_details["charges_enabled"] or not vendor_details["payouts_enabled"]:
            parties_ready = False
        if not client_details["stripe_customer_id"]:
            parties_ready = False

        return jsonify({

            "parties_ready": parties_ready,
            "client_stripe_customer_id": client_details["stripe_customer_id"],
            "client_stripe_payment_method_id": client_details["payment_method_id"],
            "vendor_stripe_account_id": vendor_details["stripe_account_id"],
        }), 200

    except Exception as e:
        lg.e("Exp ~ " + str(e) + " trace ~ " + str(traceback.format_exc()))
        if debug_responses:
            return jsonify({'success': False,           
            'error': str(e),
            }), 500   
        else:
            return std_exception_response()

@uauth
def makeClientPayment_fn(request):
    try:
        data = request.json
        client_user_id = data.get("userId")  # Use authenticated userId
        vendor_user_id = data.get("vendor_user_id")
        service_id = data.get("service_id")
        booking_id = data.get("booking_id")

        if not client_user_id or not vendor_user_id or not service_id:
            return jsonify({"error": "Missing data"}), 400

        # Look up Stripe details server-side instead of trusting client
        client_details = fdb.collection(stripe_clients_collection).document(client_user_id).get().to_dict()
        vendor_details = fdb.collection(stripe_vendors_collection).document(vendor_user_id).get().to_dict()

        client_stripe_customer_id = client_details.get("stripe_customer_id")
        client_payment_method_id = client_details.get("payment_method_id")
        vendor_stripe_account_id = vendor_details.get("stripe_account_id")

        # Look up service price server-side
        service_doc = fdb.collection(service_collection).document(service_id).get()
        if not service_doc.exists:
            return jsonify({"error": "Service not found"}), 404
        payment_amount_cents = service_doc.to_dict().get("priceCents")

        if not client_stripe_customer_id or not client_payment_method_id or not vendor_stripe_account_id:
            return jsonify({"error": "Missing payment setup"}), 400


        stripe_fee_base = ( payment_amount_cents * .029 ) + 30
        four_percent_fee_plus_base = ( payment_amount_cents * .039 ) + 30
        platform_profit = four_percent_fee_plus_base - stripe_fee_base

        intent = stripe.PaymentIntent.create(
            amount= four_percent_fee_plus_base,
            currency="usd",
            customer=client_stripe_customer_id,
            payment_method=client_payment_method_id,
            confirm=True,  # charges immediately
            off_session=True,  # since you already have the saved method
            on_behalf_of=vendor_stripe_account_id,
            transfer_data={
                "destination": vendor_stripe_account_id,
            },
            application_fee_amount= platform_profit,  # e.g., $1.00 fee to your platform
        )

        lg.t("Created intent ~ " + str(intent))
        lg.t("intent dict ~ " + str(dict(intent)))



        if intent.status == "succeeded":
            lg.t("PaymentIntent succeeded:", intent.id)
            fdb.collection(stripe_receipts_collection).document(intent.id).set({ 
                "createTime": datetime.now(timezone.utc),
                "client_stripe_customer_id": client_stripe_customer_id,
                "client_payment_method_id": client_payment_method_id,
                "client_user_id": client_user_id,
                "vendor_stripe_account_id": vendor_stripe_account_id,
                "vendor_user_id": vendor_user_id,
                "payment_amount_cents": payment_amount_cents,
                "payment_intent_id": intent.id,
                "service_id": service_id,
                "booking_id": data.get("booking_id"),
                "service_name": data.get("service_name"),
                "vendor_business_name": data.get("vendor_business_name"),
            
            })
        if intent.status == "requires_payment_method":
            lg.t("PaymentIntent requires_payment_method:", intent.id)
        elif intent.status == "requires_action":
            lg.t("PaymentIntent requires_action:", intent.id)
        else:
            lg.t("PaymentIntent id:", intent.id,", status:", intent.status)

        # intent.status may also be:
        # requires_action → rare in off‑session, but you’d need to notify customer to complete 3DS or other action
        # requires_payment_method → card declined, pick another

        return jsonify({"payment_status": intent.status}), 200
    
    except Exception as e:
        lg.e("Exp ~ " + str(e) + " trace ~ " + str(traceback.format_exc()))
        if debug_responses:
            return jsonify({'success': False,           
            'error': str(e),
            }), 500   
        else:
            return std_exception_response()