from firebase_functions import https_fn
from common import common_cors
from etc.save_provider import saveProvider_fn, getSavedProviders_fn
from etc.track_meta import trackMeta_fn

@https_fn.on_request(cors=common_cors)
def saveProvider(req: https_fn.Request) -> https_fn.Response:
    return saveProvider_fn(req)


@https_fn.on_request(cors=common_cors)
def getSavedProviders(req: https_fn.Request) -> https_fn.Response:
    return getSavedProviders_fn(req)

@https_fn.on_request(cors=common_cors)
def trackMeta(req: https_fn.Request) -> https_fn.Response:
    return trackMeta_fn(req)