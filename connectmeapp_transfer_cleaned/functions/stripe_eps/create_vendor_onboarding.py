import stripe
import os
from settings import *
from common import *
from auth.auth_user_wrapper import uauth
import traceback


@uauth
def create_vendor_onboarding(request):

    try:
        request_json = request.get_json()
        vendor_user_id = request_json.get("userId")

        refresh_url = request_json.get("refresh_url")
        redirect_url = request_json.get("redirect_url")

        if not vendor_user_id:
            return {"error": "userId required"}, 400

        # 1️⃣ Create Connect account
        account = stripe.Account.create(
            type="express",
            capabilities={
                "card_payments": {"requested": True},
                "transfers": {"requested": True},
            },
            metadata={"vendor_user_id": vendor_user_id}
        )

        # 💾 Save account.id to your DB associated with vendor_user_id
        save_vendor_stripe_account_id(vendor_user_id, account.id)

        # 2️⃣ Create account onboarding link
        account_link = stripe.AccountLink.create(
            account=account.id,
            refresh_url= f"{refresh_url}?vendor_stripe_id={account.id}", # something went wrong
            return_url= f"{redirect_url}?vendor_stripe_id={account.id}",  # success
            type="account_onboarding"
        )

        return {"url": account_link.url}, 200

    except Exception as e:
        lg.e("Exp ~ " + str(e) + " trace ~ " + str(traceback.format_exc()))
        if debug_responses:
            return jsonify({'success': False,           
            'error': str(e),
            }), 500   
        else:
            return std_exception_response()


def save_vendor_stripe_account_id(vendor_user_id: str, stripe_account_id: str):
    vendor_ref = fdb.collection(stripe_vendors_collection).document(vendor_user_id)

    # Set or update the vendor document
    vendor_ref.set({
        "stripe_account_id": stripe_account_id,
        "charges_enabled": False,
        "payouts_enabled": False,
        "onboarding_complete": False,
    }, merge=True)

    print(f"✅ Saved Stripe account {stripe_account_id} for vendor {vendor_user_id}")


@uauth
def get_vendor_status(request):
    try:
        lg.t("get_vendor_status called")
        request_json = request.get_json()
        vendor_user_id = request_json.get("userId")

        lg.t("get doc for vendor id ~ " + str(vendor_user_id))
        vendor_ref = fdb.collection(stripe_vendors_collection).document(vendor_user_id)
        vendor_doc = vendor_ref.get()
        if not vendor_doc.exists:
            return {
                "error": "Vendor not found",
                "accountStatus": "not_created"
                }, 404

        stripe_account_id = vendor_doc.get("stripe_account_id")

        lg.t("retirieve stripe account")
        account = stripe.Account.retrieve(stripe_account_id)

        lg.t("get charges statuses")
        charges_enabled = account.get("charges_enabled", False)
        payouts_enabled = account.get("payouts_enabled", False)

        onboarding_complete = charges_enabled and payouts_enabled
        
        vr_set_doc = {
            "stripe_account_id": stripe_account_id,
            "charges_enabled": charges_enabled,
            "payouts_enabled": payouts_enabled,
            "onboarding_complete": onboarding_complete,
        }
        lg.t("Vr set doc ~ " + str(vr_set_doc))
        vendor_ref.set(vr_set_doc, merge=True)

        return {
            "charges_enabled": account['charges_enabled'],
            "payouts_enabled": account['payouts_enabled'],
            "stripe_account_id": stripe_account_id
        }, 200

    except Exception as e:
        lg.e("Exp ~ " + str(e) + " trace ~ " + str(traceback.format_exc()))
        if debug_responses:
            return jsonify({'success': False,           
            'error': str(e),
            }), 500   
        else:
            return std_exception_response()


@uauth
def get_vendor_dashboard_url(request):
    try:
        lg.t("get_vendor_dashboard_url called")
        request_json = request.get_json()
        user_id = request_json.get("userId")

        # Look up vendor's own Stripe account instead of trusting client-supplied ID
        vendor_doc = fdb.collection(stripe_vendors_collection).document(user_id).get()
        if not vendor_doc.exists:
            return {"error": "Vendor Stripe account not found"}, 404
        vendor_stripe_account_id = vendor_doc.to_dict().get("stripe_account_id")
        login_link = stripe.Account.create_login_link(vendor_stripe_account_id)

        return {
            "dashboard_url": login_link.url,
        }, 200

    except Exception as e:
        lg.e("Exp ~ " + str(e) + " trace ~ " + str(traceback.format_exc()))
        if debug_responses:
            return jsonify({'success': False,           
            'error': str(e),
            }), 500   
        else:
            return std_exception_response()

# def stripe_webhook(request):
#     payload = request.data
#     sig_header = request.headers.get('Stripe-Signature')
#     event = None

#     try:
#         event = stripe.Webhook.construct_event(
#             payload, sig_header, os.getenv("STRIPE_WEBHOOK_SECRET")
#         )
#     except ValueError:
#         return "Invalid payload", 400
#     except stripe.error.SignatureVerificationError:
#         return "Invalid signature", 400

#     if event['type'] == 'account.updated':
#         account = event['data']['object']
#         vendor_user_id = account['metadata']['vendor_user_id']
#         charges_enabled = account['charges_enabled']
#         payouts_enabled = account['payouts_enabled']

#         # Update vendor status in DB
#         update_vendor_status(vendor_user_id, charges_enabled, payouts_enabled)

#     return '', 200


# def update_vendor_status(
#     vendor_user_id: str,
#     charges_enabled: bool,
#     payouts_enabled: bool
# ):
#     vendor_ref = db.collections(stripe_vendors_collection).document(vendor_user_id)

#     onboarding_complete = charges_enabled and payouts_enabled

#     vendor_ref.update({
#         "charges_enabled": charges_enabled,
#         "payouts_enabled": payouts_enabled,
#         "onboarding_complete": onboarding_complete,
#     })

#     print(f"✅ Updated vendor {vendor_user_id}: "
#           f"charges_enabled={charges_enabled}, payouts_enabled={payouts_enabled}")