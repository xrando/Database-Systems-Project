from flask import Blueprint

routes = Blueprint('routes', __name__)

from .Movie import *
from .Actor import *
from .Director import *
from .Search import *
from .Review import *
from .Genre import *

#TODO: User routes
