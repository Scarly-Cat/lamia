#TODO: Remove this pylint statment when this file isn't super WIP
# pylint: skip-file
from starlette.responses import JSONResponse
from starlette.responses import HTMLResponse
from lamia.database import db
from lamia.templating import jinja
from lamia.config import SITE_NAME


async def introduction(request):
    template = jinja.get_template('index.html')
    content = template.render(request=request, site_name=f'{SITE_NAME}')
    return HTMLResponse(content)


# How to get a connection
#async with db.acquire(lazy=True) as connection:
