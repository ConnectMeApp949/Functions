

from firebase_functions import https_fn, options
from flask import Response
from common import fdb, common_cors
import json
from settings import *
import traceback

@https_fn.on_request(cors=common_cors)
def test_post_req(req: https_fn.Request) -> https_fn.Response:
  
    try:
        if req.method != 'POST':
            return https_fn.Response("Method Not Allowed. This endpoint only accepts POST requests.", status=405)

        if req.method == "OPTIONS":
            # Preflight request
            response = Response(status=204)

        request_data = req.json
        print("[test_post_req] post data ~ ", str(request_data))
    
        response =  Response(
            json.dumps({"response": "request succeeded"}), 
            mimetype="application/json",
        status=200 # OK 
        )

        return response


    except Exception as e:
        lg.e("Exp ~ " + str(e) + " trace ~ " + str(traceback.format_exc()))
        if debug_responses:
            return jsonify({'success': False,           
            'error': str(e),
            }), 500   
        else:
            return std_exception_response()

