from flask import Flask

from novatrade.adapters.flask.order_api.routes import create_order_blueprint
from novatrade.application.commands.place_order_handler import (
    PlaceOrderCommandHandler,
)


def create_app(
    place_order_handler: PlaceOrderCommandHandler,
) -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)

    app.register_blueprint(
        create_order_blueprint(place_order_handler),
    )

    return app
