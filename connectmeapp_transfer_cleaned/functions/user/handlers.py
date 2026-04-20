from firebase_functions import https_fn
from user.user_meta import updateUserMeta_fn, getUserMeta_fn, updateUserAccountSub_fn
from user.user_delete_account import userDeleteAccount_fn, requestDataDeletion_fn
from user.user_account_subscription import getUserAccountSubscription_fn
from common import common_cors


@https_fn.on_request(cors=common_cors)
def getUserMeta(req: https_fn.Request) -> https_fn.Response:
    return getUserMeta_fn(req)

@https_fn.on_request(cors=common_cors)
def updateUserMeta(req: https_fn.Request) -> https_fn.Response:
    return updateUserMeta_fn(req)

@https_fn.on_request(cors=common_cors)
def deleteUserAccount(req: https_fn.Request) -> https_fn.Response:
    return userDeleteAccount_fn(req)

@https_fn.on_request(cors=common_cors)
def requestDataDeletion(req: https_fn.Request) -> https_fn.Response:
    return requestDataDeletion_fn(req)


@https_fn.on_request(cors=common_cors)
def getUserAccountSubscription(req: https_fn.Request) -> https_fn.Response:
    return getUserAccountSubscription_fn(req)


@https_fn.on_request(cors=common_cors)
def updateUserAccountSub(req: https_fn.Request) -> https_fn.Response:
    return updateUserAccountSub_fn(req)


