from firebase_functions import https_fn
from stripe_eps.create_vendor_onboarding import create_vendor_onboarding, save_vendor_stripe_account_id, get_vendor_status, get_vendor_dashboard_url
from stripe_eps.create_client_onboarding import createClientCustomer_fn, getClientStatus_fn, createClientCheckoutSetupSession_fn
from stripe_eps.make_payment import makeClientPayment_fn, getTransactionStripeAccountDetails_fn
from common import common_cors


@https_fn.on_request(cors=common_cors)
def createVendorStripeAccountOnboarding(req: https_fn.Request) -> https_fn.Response:
    return create_vendor_onboarding(req)

@https_fn.on_request(cors=common_cors)
def saveVendorStripeAccountId(req: https_fn.Request) -> https_fn.Response:
    return save_vendor_stripe_account_id(req)

@https_fn.on_request(cors=common_cors)
def getVendorStripeAccountStatus(req: https_fn.Request) -> https_fn.Response:
    return get_vendor_status(req)

@https_fn.on_request(cors=common_cors)
def getVendorStripeDashboardUrl(req: https_fn.Request) -> https_fn.Response:
    return get_vendor_dashboard_url(req)



@https_fn.on_request(cors=common_cors)
def createClientStripeCustomer(req: https_fn.Request) -> https_fn.Response:
    return createClientCustomer_fn(req)

# @https_fn.on_request(cors=common_cors)
# def createClientStripeSetupIntent(req: https_fn.Request) -> https_fn.Response:
#     return createSetupIntent_fn(req)

@https_fn.on_request(cors=common_cors)
def createClientStripeCheckoutSetupSession(req: https_fn.Request) -> https_fn.Response:
    return createClientCheckoutSetupSession_fn(req)

@https_fn.on_request(cors=common_cors)
def getClientStripeSetupStatus(req: https_fn.Request) -> https_fn.Response:
    return getClientStatus_fn(req)

# @https_fn.on_request(cors=common_cors)
# def makeClientStripePayment(req: https_fn.Request) -> https_fn.Response:
#     return makeClientPayment_fn(req)

# @https_fn.on_request(cors=common_cors)
# def getTransactionStripeAccountDetails(req: https_fn.Request) -> https_fn.Response:
#     return getTransactionStripeAccountDetails_fn(req)



