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

@uauth
def cancelBooking_fn(request):

    pdata = request.get_json()
    lg.t("[cancelBooking_fn] with pdata ~ " + str(pdata))   

    user_id = pdata.get("userId")
    cancel_request_user = pdata.get("userType")


    try:                
        # lg.t("[createBooking_fne_fn] build booking item")
        # make_uuid = createUUIDMixedCase(16)

        # vendor_details = fdb.collection(stripe_vendors_collection).document(pdata.get("vendorUserId")).get().to_dict()
        # client_details = fdb.collection(stripe_clients_collection).document(pdata.get("userId")).get().to_dict()

        booking_id = pdata.get("bookingId")

        lg.t("find booking item")
        bi = fdb.collection(booking_collection).document(booking_id).get().to_dict()

        bid = bi["bookingId"]
        sid = bi["serviceId"]
        client_user_id = bi["clientUserId"]
        vendor_user_id = bi["vendorUserId"]

        # use a lot of try catch for this bad girl
        try:
            lg.t("look for ratings")
            # need to delete ratings because users will book and rate and cancel to game system
            rids = fdb.collection(rating_collection) \
            .where("bookingId", "==", bid).get()

            ri = None
            for doc in rids:
                lg.t("found rating doc to delete")
                ri = doc.to_dict()
                lg.t("deleting rating doc ~ " + str(ri))
                doc.reference.delete()

            lg.t("deleted ratings")

            lg.t("decrement rating count")
            # need to also decrement rating count if rating is completed
            if ri:
                if ri["ratingStatus"] == "completed":
                    lg.t("found completed rating run decrement")
                    try:
                        si = fdb.collection(service_collection).document(sid).get().to_dict()
                        old_rating = si.get("rating")
                        old_rating_count = si.get("ratingCount")
                        lg.t("old rating and count ~  " + str(old_rating) + " ," + str(old_rating_count))
                        if old_rating_count == 1:
                            new_average = 0
                            new_rating_count = 0
                        else:
                            new_rating_count = old_rating_count - 1
                            new_average = ((old_rating * old_rating_count) - old_rating) / (new_rating_count)
                        lg.t("new rating and count ~  " + str(new_average) + " ," + str(new_rating_count))
                        
                        si["rating"] = new_average
                        si["ratingCount"] = new_rating_count
                            
                        fdb.collection(service_collection).document(sid).set(si)
                    except Exception as e:
                        lg.e("Exception caught updating rating ~ ", str(e))
                        lg.e("Exception st ~ ", traceback.format_exc())
        except Exception as e:
            lg.e("Exception caught deleting ratings ~ ", str(e))
            lg.e("Exception st ~ ", traceback.format_exc())



        lg.t("check confirmed booking")

        # need to do refund if booking is confirmed
        if bi["status"] == "confirmed":
            lg.t("found confirmed booking start stripe refund")
            lg.t("get reciepts with bookingId ~ " + str(bid))
            spr = fdb.collection(stripe_receipts_collection) \
                    .where("booking_id", "==", bid).get()
            lg.t("made stripe receipt query")
            if spr:
                lg.t("found stripe receipt")
                pdoc = spr[0].to_dict()
                piid = pdoc.get("payment_intent_id")
            else:
                return jsonify({'success': False,
                'error': "missing stripe receipt",}), 401

            lg.t("found payment_intent_id ~ " + str(piid))
            payment_amount_original_cents = pdoc.get("payment_amount_cents")
            taxed_amount = payment_amount_original_cents

            do_refund_application_fee = True    
            lg.t("calc taxed_amount ~ " + str(taxed_amount))
            if cancel_request_user == "client":
                taxed_amount = round(payment_amount_original_cents * stripe_refund_percent)
                do_refund_application_fee = False
    
            lg.t("calc taxed_amount ~ " + str(taxed_amount))

            rfi = stripe.Refund.create(
            payment_intent=piid,
            # or: charge="ch_3Rndl2EJGpZQS0Pw0TitSkKS",
            amount=taxed_amount,                # optional, if not set the entire amount will be refunded
            refund_application_fee=do_refund_application_fee,       # optional, if you want to refund your $1.00 fee too
            reverse_transfer=True               # optional, if you want to reclaim the vendor’s payout You could manually call: stripe.Transfer.create_reversal(transfer=…, amount=…)
                                                #But Stripe does that for you if you pass reverse_transfer=True on the refund.
                                                #The transfer ID is already linked internally to the charge — you don’t need to look it up explicitly in this case.
            )

            lg.t("stripe refund created rfi ~ " + str(rfi))

            # we really want an entry here or else we'll never find it probably
            try:
                rfi_id = rfi.id
            except Exception as e:
                lg.e("Exception caught getting rfi id ~ ", str(e))
                make_uuid = createUUIDMixedCase(8)
                rfi_id = "Def_RFI_ID" + make_uuid
            try:
                rfi_pi = rfi.payment_intent
            except Exception as e:
                lg.e("Exception caught getting rfi pi ~ ", str(e))
                make_uuid = createUUIDMixedCase(8)
                rfi_pi = "Def_RFI_PI" + make_uuid
            try:
                rfi_ch = rfi.charge
            except Exception as e:
                lg.e("Exception caught getting rfi ch ~ ", str(e))
                make_uuid = createUUIDMixedCase(8)
                rfi_ch = "Def_RFI_CH" + make_uuid
            try:
                rfi_trr = rfi.transfer_reversal
            except Exception as e:
                lg.e("Exception caught getting rfi trr ~ ", str(e))
                make_uuid = createUUIDMixedCase(8)
                rfi_trr = "Def_RFI_TRR" + make_uuid


            fdb.collection(stripe_receipts_collection).document(rfi_id).set({ 
                "booking_id": booking_id,
                "client_user_id": client_user_id,
                "createTime": datetime.now(timezone.utc),
                "payment_amount_original_cents": payment_amount_original_cents,
                "payment_intent_id": rfi_pi,
                "refund_amount_cents": taxed_amount,
                "refund_charge_id": rfi_ch, # not used so far
                "refund_id": rfi_id,
                "refund_initiator": cancel_request_user,
                "service_id": bi.get("serviceId"),
                "service_name": bi.get("serviceName"),
                "transfer_reversal": rfi_trr,
                "vendor_business_name": bi.get("vendorBusinessName"),
                "vendor_user_id": vendor_user_id,
        
            })

            # do last because we don't want them thinking they cancelled and refunded if it didn't work
            lg.t("set booking item status cancelled")

            fdb.collection(booking_collection).document(booking_id).set({
                "status": "cancelled"},
                 merge=True
                )

        elif bi["status"] == "pending":
            lg.t("found pending for deletion do set status cancelled") 
            fdb.collection(booking_collection).document(booking_id).set({
                "status": "cancelled"},
                 merge=True
                )


        return jsonify({'success': True })

    except Exception as e:
        lg.e("Exp ~ " + str(e) + " trace ~ " + str(traceback.format_exc()))
        return jsonify({'success': False,
        'error': str(e),
        'trace': traceback.format_exc()
        }), 500
    

# >  stripe refund created rfi ~ {
# >    "amount": 736,
# >    "balance_transaction": "txn_3Rnqj8EJGpZQS0Pw0YYVCAsl",
# >    "charge": "ch_3Rnqj8EJGpZQS0Pw0HR2JL2x",
# >    "created": 1753234670,
# >    "currency": "usd",
# >    "destination_details": {
# >      "card": {
# >        "reference_status": "pending",
# >        "reference_type": "acquirer_reference_number",
# >        "type": "refund"
# >      },
# >      "type": "card"
# >    },
# >    "id": "re_3Rnqj8EJGpZQS0Pw0BaRHExC",
# >    "metadata": {},
# >    "object": "refund",
# >    "payment_intent": "pi_3Rnqj8EJGpZQS0Pw06AiKcjE",
# >    "reason": null,
# >    "receipt_number": null,
# >    "source_transfer_reversal": null,
# >    "status": "succeeded",
# >    "transfer_reversal": "trr_1RnrcxEJGpZQS0Pw18C9yiWc"
# >  }
