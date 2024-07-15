from flask import Blueprint, render_template, flash, redirect, url_for

from compute.modules.ASNNotFoundError import ASNNotFoundError
Error = Blueprint('errors', __name__, static_folder="static", template_folder="template")

@Error.app_errorhandler(ASNNotFoundError)
def asn_not_found(e):
    flash(e.message)
    return redirect(url_for("custom.custom", _method="GET"))

@Error.app_errorhandler(Exception)
def page_not_found(e):
    print(e)
    e = str(e).split(":")
    print(e)
    error_code = e[0][:3]
    error_name = e[0][3:]
    error_message = e[1]
    return render_template(
        "errorPage.html",
        error_code=error_code,
        error_name=error_name,
        error_message=error_message,
        title="Error",
    )
