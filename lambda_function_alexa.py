# -*- coding: utf-8 -*-
import logging
import ask_sdk_core.utils as ask_utils
import requests
import json
from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler, AbstractExceptionHandler
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model import Response

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


# === HANDLER PRINCIPAL ===
class LaunchRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        speak_output = (
            "Hello! I’m Astro MatIAS, your space friend. "
            "I can tell you real curiosities from NASA’s research.  "
          
        )
        return (
            handler_input.response_builder
            .speak(speak_output)
            .ask("What space topic would you like to learn about today?")
            .response
        )


# === HANDLER DEL INTENTO PERSONALIZADO ===
class CustomEspacialIntentHandler(AbstractRequestHandler):
    
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("CustomEspacialIntent")(handler_input)

    def handle(self, handler_input):
        response_builder = handler_input.response_builder

        # Obtener el valor del slot "pregunta"
        slots = handler_input.request_envelope.request.intent.slots
        pregunta = slots.get("pregunta").value if "pregunta" in slots and slots["pregunta"].value else None

        if not pregunta:
            return response_builder.speak(
                "No entendí bien tu pregunta. ¿Podrías repetir sobre qué tema espacial quieres saber?"
            ).ask("¿Qué tema espacial te interesa?").response

        # Enviar la pregunta al webhook
        url = "https://uprit-senati.app.n8n.cloud/webhook/matias_cientifico"
        headers = {"Content-Type": "application/json"}
        payload = {"mensaje": pregunta}

        try:
            logger.info(f"Intentando conectar con {url}")
            logger.info(f"Payload enviado: {json.dumps(payload)}")

            # 🔹 Ya no se habla antes de hacer la petición (comportamiento anterior)
            # Alexa esperará a tener la respuesta para hablar

            # Petición HTTP
            r = requests.post(url, headers=headers, json=payload, timeout=10)
            logger.info(f"Respuesta HTTP {r.status_code}")
            logger.info(f"Contenido parcial: {r.text[:300]}")

            if r.status_code == 200:
                try:
                    data = r.json()
                    respuesta = data.get("respuesta", "No encontré información en los registros de la NASA.")
                    final_output = f"Thank you for waiting. {respuesta}"
                except json.JSONDecodeError:
                    logger.error("Error al decodificar la respuesta JSON")
                    final_output = "El servidor respondió, pero el formato no era válido. Intenta más tarde."
            else:
                logger.error(f"Error HTTP recibido: {r.status_code}")
                final_output = f"El servidor respondió con un error {r.status_code}."

        except requests.exceptions.ConnectTimeout:
            logger.exception("Tiempo de espera agotado (timeout).")
            final_output = "El servidor tardó demasiado en responder. Intenta más tarde."

        except requests.exceptions.SSLError:
            logger.exception("Error SSL (certificado).")
            final_output = "Hubo un error de seguridad con el servidor. Verifica el certificado SSL."

        except requests.exceptions.ConnectionError as e:
            logger.exception("Error de conexión.")
            short_err = str(e)[:100].replace("\n", " ").replace("'", "")
            final_output = f"No se pudo conectar con el servidor. Error: {short_err}"

        except Exception as e:
            logger.exception("Error general en CustomEspacialIntentHandler")
            short_err = str(e)[:100].replace("\n", " ").replace("'", "")
            final_output = f"Hubo un error al procesar la solicitud. Detalle: {short_err}"

        # 🔹 Ahora sí Alexa habla cuando ya se obtuvo la respuesta final
        #return response_builder.speak(final_output).response
        return response_builder.speak(final_output).ask("¿Quieres preguntarme otra cosa del espacio?").response

# === HANDLERS ADICIONALES ===
class HelpIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        speak_output = "Puedes decirme: Quiero saber de los ratones en el espacio. ¿Qué deseas saber?"
        return handler_input.response_builder.speak(speak_output).ask(speak_output).response


class CancelOrStopIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return (
            ask_utils.is_intent_name("AMAZON.CancelIntent")(handler_input)
            or ask_utils.is_intent_name("AMAZON.StopIntent")(handler_input)
        )

    def handle(self, handler_input):
        return handler_input.response_builder.speak("Adiós, hasta la próxima misión.").response


class FallbackIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("AMAZON.FallbackIntent")(handler_input)

    def handle(self, handler_input):
        speech = "No estoy seguro de eso. Puedes preguntar sobre investigaciones de la NASA."
        return handler_input.response_builder.speak(speech).ask(speech).response


class SessionEndedRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        return handler_input.response_builder.response


class CatchAllExceptionHandler(AbstractExceptionHandler):
    def can_handle(self, handler_input, exception):
        return True

    def handle(self, handler_input, exception):
        logger.error(exception, exc_info=True)
        err_msg = str(exception)[:100].replace("\n", " ").replace("'", "")
        speak_output = f"Lo siento, hubo un error inesperado. Detalle: {err_msg}"
        return handler_input.response_builder.speak(speak_output).ask("¿Deseas intentar otra pregunta?").response


# === BUILDER ===
sb = SkillBuilder()
sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(CustomEspacialIntentHandler())  # <-- reemplazado aquí
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(FallbackIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
sb.add_exception_handler(CatchAllExceptionHandler())

lambda_handler = sb.lambda_handler()
