import logging

import requests
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.utils import is_intent_name
from ask_sdk_model import Response
from ask_sdk_model.ui import SimpleCard

logger = logging.getLogger(__name__)


class OrderIntentHandler(AbstractRequestHandler):
    """Handler for Order Intent"""

    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("OrderIntent")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        slots = handler_input.request_envelope.request.intent.slots
        emojis = slots.get("emojis", {}).get("value", "")
        customer = slots.get("customer", {}).get("value", "Customer")

        # Call OM1 API
        try:
            response = requests.post(
                "http://localhost:8000/api/voice-command",
                json={
                    "command": f"order {emojis} for {customer}",
                    "customer_name": customer,
                },
                timeout=10,
            )

            if response.status_code == 200:
                order_data = response.json()
                speech_text = f"Order {order_data['order_id']} created for {customer}. Total is ${order_data['total_price']}. Payment link sent to your device."
            else:
                speech_text = "Sorry, I couldn't create your order. Please try again."

        except Exception:
            speech_text = "Sorry, there's an error with the ordering system. Please try again later."

        return (
            handler_input.response_builder.speak(speech_text)
            .set_card(SimpleCard("OM1 Order", speech_text))
            .response
        )


class StatusIntentHandler(AbstractRequestHandler):
    """Handler for Order Status Intent"""

    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("StatusIntent")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        slots = handler_input.request_envelope.request.intent.slots
        order_id = slots.get("order_id", {}).get("value", "")

        if not order_id:
            speech_text = (
                "I need an order ID to check the status. Please provide your order ID."
            )
        else:
            try:
                response = requests.get(f"http://localhost:8000/api/order/{order_id}")

                if response.status_code == 200:
                    order_data = response.json()
                    status = order_data.get("status", "unknown")
                    speech_text = (
                        f"Order {order_id} is currently {status.replace('_', ' ')}."
                    )
                else:
                    speech_text = (
                        f"I couldn't find order {order_id}. Please check your order ID."
                    )

            except Exception:
                speech_text = "Sorry, I can't check the order status right now. Please try again later."

        return (
            handler_input.response_builder.speak(speech_text)
            .set_card(SimpleCard("Order Status", speech_text))
            .response
        )


class HelpIntentHandler(AbstractRequestHandler):
    """Handler for Help Intent"""

    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        speech_text = """
        You can order food using emojis! Just say:
        - Order coffee pizza for John
        - Check status of order 12345
        - What's on the menu?

        Available emojis: coffee ☕, pizza 🍕, burger 🍔, salad 🥗, and more!
        """

        return (
            handler_input.response_builder.speak(speech_text).ask(speech_text).response
        )


class CancelAndStopIntentHandler(AbstractRequestHandler):
    """Handler for Cancel and Stop Intent"""

    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("AMAZON.CancelIntent")(handler_input) or is_intent_name(
            "AMAZON.StopIntent"
        )(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        speech_text = "Goodbye! Enjoy your food!"
        return handler_input.response_builder.speak(speech_text).response


class SessionEndedRequestHandler(AbstractRequestHandler):
    """Handler for Session End"""

    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("SessionEndedRequest")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        return handler_input.response_builder.response


# Skill Builder
sb = SkillBuilder()

# Register handlers
sb.add_request_handler(OrderIntentHandler())
sb.add_request_handler(StatusIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelAndStopIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())

# Lambda handler
lambda_handler = sb.lambda_handler()
