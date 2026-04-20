    # functions/common.py


from firebase_admin import initialize_app, firestore, get_app
from settings import *
import stripe

# Lazy-initialization wrapper
class LazyFirestoreClient:
    def __init__(self):
        self._app = None
        self._fdb = None

    def __getattr__(self, item):
        if self._fdb is None:
            try:
                self._app = get_app()
            except ValueError:
                self._app = initialize_app()
            self._fdb = firestore.client()
        return getattr(self._fdb, item)

# Single instance
fdb = LazyFirestoreClient()



from firebase_functions import options

common_cors = options.CorsOptions(
    cors_origins="*",
    cors_methods=["get", "post", "options"],
)


from functools import wraps

def cors(fn):
    @wraps(fn)
    def wrapper(req: https_fn.Request) -> https_fn.Response:
        # Handle preflight OPTIONS request
        if req.method == 'OPTIONS':
            return https_fn.Response(
                '',
                status=204,
                headers={
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type',
                }
            )

        # Call your actual function
        response = fn(req)

        # Add CORS headers to the response
        if isinstance(response, https_fn.Response):
            # Copy existing headers or create a new dict
            headers = dict(response.headers or {})
            headers['Access-Control-Allow-Origin'] = '*'
            headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
            headers['Access-Control-Allow-Headers'] = 'Content-Type'

            # Return a new Response with updated headers but same content and status
            return https_fn.Response(
                response.body,
                status=response.status,
                headers=headers
            )

        # If your function returned something else, just return as is
        return response

    return wrapper



stripe.api_key = STRIPE_SECRET_KEY