from firebase_admin import firestore
from flask import request, jsonify
from common import fdb
from settings import *
from datetime import datetime, timezone
from util.collection import clean
from firebase_admin.firestore import GeoPoint, FieldFilter
import traceback
from util.hash_methods import *                  
from auth.auth_user_wrapper import uauth
from util.datetime_util import conv_dt_to_utc
import stripe


#confirmed by vendor

@uauth
def confirmBookingAndPay_fn(request):

    pdata = request.get_json()
    lg.t("[confirmBookingAndPay_fn] with pdata ~ " + str(pdata))   



    try:                
        lg.t("[confirmBookingAndPay_fn] build booking item")
        booking_id = pdata.get("bookingId")

        # bi = {
        #     "address": pdata.get("address"),
        #     "bookingId": pdata.get("bookingId"),
        #     "bookingTime": testBTime,
        #     "createTime": testCTime,       
        #     "clientUserId": pdata.get("userId"),
        #     "clientUserName": pdata.get("clientUserName"),
        #     "priceCents": pdata.get("priceCents"),  
        #     "serviceId": pdata.get("serviceId"),
        #     "serviceName": pdata.get("serviceName"),
        #     "site": pdata.get("site"),
        #     "status": "pending",
        #     "timeLength": pdata.get("timeLength"),
        #     "vendorBusinessName": pdata.get("vendorBusinessName"),
        #     "vendorUserId": pdata.get("vendorUserId"),
        #     "vendorUserName": pdata.get("vendorUserName"),
        # }
        # lg.t("booking item ~ " + str(bi))       

        bi = fdb.collection(booking_collection).document(pdata.get("bookingId")).get().to_dict()


        client_user_id = bi.get("clientUserId")
        vendor_user_id = bi.get("vendorUserId")

        vendor_details = fdb.collection(stripe_vendors_collection).document(vendor_user_id).get().to_dict()
        client_details = fdb.collection(stripe_clients_collection).document(client_user_id).get().to_dict()

        lg.t("check for parties ready")
        parties_ready = True
        if not vendor_details["charges_enabled"] or not vendor_details["payouts_enabled"]:
            parties_ready = False
        if not client_details["stripe_customer_id"]:
            parties_ready = False

        if not parties_ready:
            return jsonify({
                "parties_ready": False,
            }), 200

        lg.t("get client details")
        # client_user_id = data.get("client_user_id")
        client_stripe_customer_id = client_details.get("stripe_customer_id")
        client_payment_method_id = client_details.get("payment_method_id")

        vendor_stripe_account_id = vendor_details.get("stripe_account_id")
        # vendor_user_id = data.get("vendor_user_id")
        payment_amount_cents = bi.get("priceCents")

        service_id = bi.get("serviceId")

        if not client_user_id or not client_stripe_customer_id or not client_payment_method_id or not vendor_stripe_account_id or not payment_amount_cents or not service_id:
            return jsonify({"error": "Missing data"}), 400

        else:
            lg.t(f"make payment intent {client_stripe_customer_id} {client_payment_method_id} {vendor_stripe_account_id} {payment_amount_cents} {service_id}")

        lg.t("make payment intent")
        intent = stripe.PaymentIntent.create(
            amount=payment_amount_cents,
            currency="usd",
            customer=client_stripe_customer_id,
            payment_method=client_payment_method_id,
            confirm=True,  # charges immediately
            off_session=True,  # since you already have the saved method
            on_behalf_of=vendor_stripe_account_id,
            transfer_data={
                "destination": vendor_stripe_account_id,
            },
            application_fee_amount=stripe_application_fee_amount_cents
        )
        lg.t("made payment intent ~ " + str(intent))

        lg.t("continue check intent")

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
                "transfer_group": intent.transfer_group,
                "service_id": service_id,
                "booking_id": booking_id,
                "service_name": bi.get("serviceName"),
                "vendor_business_name": bi.get("vendorBusinessName"),
                "payment_stauts": intent.status,
            })

            fdb.collection(booking_collection).document(pdata.get("bookingId")).update({
            "status": "confirmed",
            })
            rating_id = createUUIDMixedCase(16)
            ri = {
                "bookingId": pdata.get("bookingId"),
                "clientUserId": bi.get("clientUserId"),
                "clientUserName": bi.get("clientUserName"),
                "createTime": datetime.now(timezone.utc), 
                "ratingId": rating_id,
                "ratingStatus": "unused",
                "serviceId": bi.get("serviceId"),
                "serviceName": bi.get("serviceName"),
                "bookingTime": bi.get("bookingTime"),
                "vendorUserId": pdata.get("userId"),
                "vendorUserName": bi.get("vendorUserName"),
            }

            fdb.collection(rating_collection) \
            .document(rating_id).set(ri)

            return jsonify({'success': True, "bookingId": pdata.get("bookingId")})

        else:
            lg.t("payment intent not succeeded")
            fdb.collection(stripe_receipts_collection).document(intent.id).set({ 
                "createTime": datetime.now(timezone.utc),
                "client_stripe_customer_id": client_stripe_customer_id,
                "client_payment_method_id": client_payment_method_id,
                "client_user_id": client_user_id,
                "vendor_stripe_account_id": vendor_stripe_account_id,
                "vendor_user_id": vendor_user_id,
                "payment_amount_cents": payment_amount_cents,
                "payment_intent_id": intent.id,
                # "transfer_group": intent.transfer_group,
                "service_id": service_id,
                "booking_id": booking_id,
                "service_name": bi.get("serviceName"),
                "vendor_business_name": bi.get("vendorBusinessName"),
                "payment_status": intent.status,
                "last_payment_error": intent.last_payment_error,
                "next_action": intent.next_action, # (if 3DS authentication was required)
            })

        if intent.status == "requires_payment_method":
            lg.t("PaymentIntent requires_payment_method:", intent.id)
            return jsonify({'success': False, "stripe_intent_status": intent.status})
        elif intent.status == "requires_action":
            lg.t("PaymentIntent requires_action:", intent.id)
            return jsonify({'success': False, "stripe_intent_status": intent.status})
        else:
            lg.t("PaymentIntent id:", intent.id,", status:", intent.status)
            return jsonify({'success': False, "stripe_intent_status": intent.status})

    except Exception as e:
        lg.e("Exp ~ " + str(e) + " trace ~ " + str(traceback.format_exc()))
        return jsonify({'success': False,
        'error': str(e),
        'trace': traceback.format_exc()
        }), 500
    


#     made payment intent ~ {
# >    "amount": 6000,
# >    "amount_capturable": 0,
# >    "amount_details": {
# >      "tip": {}
# >    },
# >    "amount_received": 6000,
# >    "application": null,
# >    "application_fee_amount": 100,
# >    "automatic_payment_methods": {
# >      "allow_redirects": "always",
# >      "enabled": true
# >    },
# >    "canceled_at": null,
# >    "cancellation_reason": null,
# >    "capture_method": "automatic_async",
# >    "client_secret": "pi_3Rndl2EJGpZQS0Pw0QobaYzK_secret_HwHqTr5Z8IQeqRpoWGnlFw5Wr",
# >    "confirmation_method": "automatic",
# >    "created": 1753181356,
# >    "currency": "usd",
# >    "customer": "cus_SdIjjAL63Pq4F1",
# >    "description": null,
# >    "id": "pi_3Rndl2EJGpZQS0Pw0QobaYzK",
# >    "last_payment_error": null,
# >    "latest_charge": "ch_3Rndl2EJGpZQS0Pw0TitSkKS",
# >    "livemode": false,
# >    "metadata": {},
# >    "next_action": null,
# >    "object": "payment_intent",
# >    "on_behalf_of": "acct_1RhmtcENFbzTPDth",
# >    "payment_method": "pm_1Ri52sEJGpZQS0PwcEYcw97b",
# >    "payment_method_configuration_details": {
# >      "id": "pmc_1Rhmu8ENFbzTPDth2lN0Ggeu",
# >      "parent": "pmc_1RhhXUEJGpZQS0Pw3wF3LxRy"
# >    },
# >    "payment_method_options": {
# >      "affirm": {},
# >      "card": {
# >        "installments": null,
# >        "mandate_options": null,
# >        "network": null,
# >        "request_three_d_secure": "automatic"
# >      },
# >      "cashapp": {},
# >      "klarna": {
# >        "preferred_locale": null
# >      },
# >      "link": {
# >        "persistent_token": null
# >      }
# >    },
# >    "payment_method_types": [
# >      "card",
# >      "klarna",
# >      "link",
# >      "affirm",
# >      "cashapp"
# >    ],
# >    "processing": null,
# >    "receipt_email": null,
# >    "review": null,
# >    "setup_future_usage": null,
# >    "shipping": null,
# >    "source": null,
# >    "statement_descriptor": null,
# >    "statement_descriptor_suffix": null,
# >    "status": "succeeded",
# >    "transfer_data": {
# >      "destination": "acct_1RhmtcENFbzTPDth"
# >    },
# >    "transfer_group": "group_pi_3Rndl2EJGpZQS0Pw0QobaYzK"
# >  }
