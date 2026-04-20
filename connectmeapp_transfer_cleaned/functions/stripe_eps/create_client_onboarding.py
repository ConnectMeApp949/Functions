import os
import stripe
from google.cloud import firestore
from flask import Flask, request, jsonify
from settings import *
from auth.auth_user_wrapper import uauth
from common import *
import traceback

@uauth
def createClientCustomer_fn(request):
    try:
        data = request.json
        client_user_id = data.get("userId")
        email = data.get("email")

        lg.t("createClientCustomer_fn called")
        if not client_user_id or not email:
            return jsonify({"error": "Missing userId or email"}), 400

        lg.t("create stripe customer")
        customer = stripe.Customer.create(
            email=email,
            metadata={"client_user_id": client_user_id}
        )

        lg.t("save stripe customer w id ~ " + str(customer.id))

        fdb.collection(stripe_clients_collection).document(client_user_id).set({
            "stripe_customer_id": customer.id,
            "email": email
        }, merge=True)

        return jsonify({"stripe_customer_id": customer.id}), 200

    except Exception as e:
        lg.e("Exp ~ " + str(e) + " trace ~ " + str(traceback.format_exc()))
        if debug_responses:
            return jsonify({'success': False,           
            'error': str(e),
            }), 500   
        else:
            return std_exception_response()


@uauth
def createClientCheckoutSetupSession_fn(request):
    try:
        data = request.json
        user_id = data.get("userId")
        customer_id = data.get("customer_id")
        success_url = data.get("success_url")
        cancel_url = data.get("cancel_url")

        if not customer_id:
            return jsonify({"error": "Missing customer_id"}), 400


        fdb.collection(stripe_clients_collection).document(user_id).get()

        session = stripe.checkout.Session.create(
            customer=customer_id,
            mode="setup",
            payment_method_types=["card"],
            success_url=success_url,
            cancel_url=cancel_url,
        )

        return jsonify({"url": session.url}), 200

    except Exception as e:
        lg.e("Exp ~ " + str(e) + " trace ~ " + str(traceback.format_exc()))
        if debug_responses:
            return jsonify({'success': False,           
            'error': str(e),
            }), 500   
        else:
            return std_exception_response()


# @uauth
# def createSetupIntent_fn(request):
#     data = request.json
#     client_user_id = data.get("client_user_id")

#     if not client_user_id:
#         return jsonify({"error": "Missing client_user_id"}), 400

#     doc = fdb.collection(stripe_clients_collection).document(client_user_id).get()
#     if not doc.exists:
#         return jsonify({"error": "Client not found"}), 404

#     customer_id = doc.get("stripe_customer_id")

#     setup_intent = stripe.SetupIntent.create(
#         customer=customer_id,
#         payment_method_types=["card"]
#     )

#     fdb.collection(stripe_clients_collection).document(client_user_id).set({
#         "stripe_client_secret": setup_intent.client_secret
#     }, merge=True)

#     return jsonify({"client_secret": setup_intent.client_secret}), 200


@uauth
def getClientStatus_fn(request):

    try:
        lg.t("getClientStatus_fn called")
        request_json = request.get_json()
        client_user_id = request_json.get("userId")

        client_ref = fdb.collection(stripe_clients_collection).document(client_user_id)
        client_doc = client_ref.get()
        if not client_doc.exists:
            return {
                "error": "Client not found",
                "accountStatus": "not_created"
                }, 404

        stripe_customer_id = client_doc.get("stripe_customer_id")

        lg.t("stripe customer id ~ " + str(stripe_customer_id))

        payment_methods = stripe.PaymentMethod.list(
        customer=stripe_customer_id,
        type="card",
        limit=1 # get the most latest card only
        )

        ret_pay_methods = []

        latest_pm = None
        for pm in payment_methods.auto_paging_iter():
            ret_pay_methods.append(pm)
            latest_pm = pm

        latest_payment_method_id = "no payment method"
        try:
            latest_payment_method_id = latest_pm.id
        except:
            lg.t("no latest paymment method")
            
        fdb.collection(stripe_clients_collection).document(client_user_id).set({
                "payment_method_id": latest_payment_method_id,
                "payment_methods_all": ret_pay_methods
            }, merge=True)
        
        lg.t("set user with ~ ")

        if latest_pm != None:
            pm_meta = f"id:{latest_payment_method_id}, card brand:{latest_pm.card["brand"]}, last4:{latest_pm.card["last4"]}"
            lg.t("pm_meta ~ " + str(pm_meta))
            
            fdb.collection(user_collection).document(client_user_id).set({
                    "payment_meta": pm_meta
                }, merge=True)
            

        return {
            "pay_methods": ret_pay_methods,
            "stripe_customer_id": stripe_customer_id
        }, 200
    
    except Exception as e:
        lg.e("Exp ~ " + str(e) + " trace ~ " + str(traceback.format_exc()))
        if debug_responses:
            return jsonify({'success': False,           
            'error': str(e),
            }), 500   
        else:
            return std_exception_response()