import repost_trigger.codexreposter
import azure.functions as func
app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

# Register the functions from codexreposter
repost_trigger.codexreposter.register_functions(app)
