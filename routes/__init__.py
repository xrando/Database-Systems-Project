from flask import Blueprint

routes = Blueprint('routes', __name__)

from .Movie import *
from .Actor import *
from .Director import *
from .Search import *
from .Review import *
from .Genre import *
from .Forum import *
from .Admin import *
from .Authentication import *
from .Profile import *


@routes.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404
