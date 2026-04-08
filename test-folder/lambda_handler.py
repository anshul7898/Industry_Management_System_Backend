from mangum import Mangum
from main import app

# This is what Lambda will call
handler = Mangum(app)