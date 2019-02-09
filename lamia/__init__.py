"""Lamia is an ActivityPub federating social network site server that
supports blogs, status updates, and polls.
"""

import logging
import gettext
import os
import jinja2
from starlette.applications import Starlette
from starlette.staticfiles import StaticFiles
from starlette.config import Config
import lamia.utilities.gino as gino
import lamia.utilities.email as email

# TODO : mypy

# Included this code to change gino's logging level. This prevents some double
# logging that was making my lose my mind with uvicorn's defaults.
logging.basicConfig()
logging.getLogger('gino').setLevel(logging.WARN)

# Initialize the app, including the database connection.
# disabling pylint warning, as this is conventional for these packages
# pylint: disable=invalid-name
db = gino.Gino()
mail = email.Email()
config = Config('lamia.config')
app = Starlette(debug=config('DEBUG', cast=bool, default=False))
db.init_app(app, config)
mail.init_app(app, config)
locale = os.path.dirname(__file__) + ('/locales')
gettext.bindtextdomain('lamia', locale)
gettext.textdomain('lamia')
en = gettext.translation('lamia', locale, ['en'])
_ = gettext.gettext
# pylint: enable=invalid-name
# This should be translated to true to show that translation is not failing

# Debug messages only when in debug mode
if config('DEBUG', cast=bool, default=False):
    logging.getLogger().setLevel(logging.DEBUG)

logging.debug(_("Translation is working: False"))
# Some config loading
app.site_name = config('SITE_NAME', cast=str, default=_('A Lamia Community'))


# Jinja2 science starts here
def setup_jinja2(template_dirs, auto_reload):
    """Setup a jinja2 env (https://www.starlette.io/templates/)"""

    @jinja2.contextfunction
    def url_for(context, name, **path_params):
        request = context['request']
        return request.url_for(name, **path_params)

    # first check for template overrides on the same level above the modual.
    # check lamia defaults if nothing is found
    loader = jinja2.ChoiceLoader([
        jinja2.FileSystemLoader(template_dirs),
        jinja2.PackageLoader('lamia')
    ])
    env = jinja2.Environment(
        loader=loader,
        autoescape=True,
        auto_reload=auto_reload,
        extensions=['jinja2.ext.i18n'],
    )
    env.install_gettext_translations(en)  # pylint: disable=no-member
    env.globals['url_for'] = url_for
    return env


TEMPLATES_DIRS = ['templates']

# pylint: disable=invalid-name
# same rational as above
jinja = setup_jinja2(
    TEMPLATES_DIRS,
    config(
        "TEMPLATE_RELOAD",
        cast=bool,
        default=False,
    ),
)
# pylint: enable=invalid-name
# Static content loading
app.mount('/static', StaticFiles(directory='statics'), name='static')

# TODO: Setup redis here

# There's probably a more graceful way to do this (a la blueprints)
# Note: the pylint disable address the fact that these imports are not in the
# pythonic place for them (normally, at the top of a file).
from .views import general  # pylint: disable=C0413
