import werkzeug
from flask import request, g
from .. import sentry

from ..value_objs import User


def is_browser() -> bool:
    # bit of content negotiation magic
    accepts = werkzeug.http.parse_accept_header(request.headers.get("Accept"))
    best = accepts.best_match(["text/html", "text/csv"], default="text/csv")
    return best == "text/html"


def set_current_user(user: User) -> None:
    g.current_user = user

    # This is duplication but very convenient for jinja templates
    g.current_username = user.username

    sentry.set_user(user)