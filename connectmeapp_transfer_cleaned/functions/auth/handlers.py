from firebase_functions import https_fn
from auth.google_auth import loginWithGoogle_fn, createAccountFirebaseToken_fn
# REMOVED: testUserAuth is a security backdoor — do not deploy to production
# from auth.test_user_auth import testUserAuth_fn
from common import common_cors


@https_fn.on_request(cors=common_cors)
def loginWithGoogle(req: https_fn.Request) -> https_fn.Response:
    return loginWithGoogle_fn(req)


@https_fn.on_request(cors=common_cors)
def createAccountFirebaseToken(req: https_fn.Request) -> https_fn.Response:
    return createAccountFirebaseToken_fn(req)
