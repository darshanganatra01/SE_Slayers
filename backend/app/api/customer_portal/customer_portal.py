from flask_restx import Namespace, Resource

# We'll call the variable 'customer_ns' to match your teammate's naming style
customer_ns = Namespace('customer', description='Customer Portal operations')

@customer_ns.route('/test')
class CustomerTest(Resource):
    def get(self):
        return {"status": "Customer Portal is active"}