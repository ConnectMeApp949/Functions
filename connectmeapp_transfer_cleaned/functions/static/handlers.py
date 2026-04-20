from firebase_functions import https_fn
from common import common_cors
from static.privacypolicy import privacyPolicy_fn
from static.termsOfService import termsOfService_fn
from static.returns import stripeVendorOnboardRedirectUrl_fn, stripeVendorOnboardRefreshUrl_fn


@https_fn.on_request(cors=common_cors)
def privacyPolicy(req: https_fn.Request) -> https_fn.Response:
    return privacyPolicy_fn(req)

@https_fn.on_request(cors=common_cors)
def termsOfService(req: https_fn.Request) -> https_fn.Response:
    return termsOfService_fn(req)

@https_fn.on_request(cors=common_cors)
def stripeVendorOnboardRedirectUrl(req: https_fn.Request) -> https_fn.Response:
    return stripeVendorOnboardRedirectUrl_fn(req)

@https_fn.on_request(cors=common_cors)
def stripeVendorOnboardRefreshUrl(req: https_fn.Request) -> https_fn.Response:
    return stripeVendorOnboardRefreshUrl_fn(req)
