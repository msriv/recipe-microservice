import json
import logging
import traceback
from types import TracebackType
from typing import Any, Awaitable, Dict, Optional, Tuple, Type
import uuid
from recipeservice.service import RecipeService
import tornado.web
from recipeservice.utils import logutils
from recipeservice import LOGGER_NAME

RECIPE_REGEX = r'/v1/recipes/?'
RECIPE_ENTRY_REGEX = r'/v1/recipes/(?P<id>[a-zA-Z0-9-]+)/?'
RECIPE_ENTRY_URI_FORMAT_STR = r'/v1/recipes/{id}'


class BaseRequestHandler(tornado.web.RequestHandler):

    def initialize(
        self,
        service: RecipeService,
        config: Dict,
        logger: logging.Logger
    ) -> None:
        self.service = service
        self.config = config
        self.logger = logger

    def prepare(self) -> Optional[Awaitable[None]]:
        req_id = uuid.uuid4().hex
        logutils.set_log_context(
            req_id=req_id,
            method=self.request.method,
            uri=self.request.uri,
            ip=self.request.remote_ip
        )

        logutils.log(
            self.logger,
            logging.DEBUG,
            include_context=True,
            message='REQUEST'
        )

        return super().prepare()

    def on_finish(self) -> None:
        super().on_finish()

    def write_error(self, status_code: int, **kwargs: Any) -> None:
        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        body = {
            'method': self.request.method,
            'uri': self.request.path,
            'code': status_code,
            'message': self._reason
        }
        logutils.set_log_context(reason=self._reason)
        if 'exc_info' in kwargs:
            exc_info = kwargs['exc_info']
            logutils.set_log_context(exc_info=exc_info)
            if self.settings.get('serve_traceback'):
                # in debug mode, send a traceback
                trace = '\n'.join(
                    traceback.format_exception(*exc_info))
                body['trace'] = trace

        self.finish(body)

    def log_exception(
        self,
        typ: Optional[Type[BaseException]],
        value: Optional[BaseException],
        tb: Optional[TracebackType],
    ) -> None:
        if isinstance(value, tornado.web.HTTPError):
            if value.log_message:
                msg = value.log_message % value.args
                logutils.log(
                    tornado.log.gen_log,
                    logging.WARNING,
                    status=value.status_code,
                    request_summary=self._request_summary(),
                    message=msg
                )
        else:
            logutils.log(
                tornado.log.app_log,
                logging.ERROR,
                message='Uncaught exception',
                request_summary=self._request_summary(),
                request=repr(self.request),
                exc_info=(typ, value, tb)
            )


# This Handler deals with Recipe entities
class RecipeRequestHandler(BaseRequestHandler):
    async def get(self):
        all_recipes = {}
        async for key, recipe in self.service.get_all_recipes():
            all_recipes[key] = recipe

        self.set_status(200)
        self.finish(all_recipes)

    async def post(self):
        try:
            recipe = json.loads(self.request.body.decode('utf-8'))
            id = await self.service.create_recipe(recipe)
            recipe_uri = RECIPE_ENTRY_URI_FORMAT_STR.format(
                id=id
            )
            print("DEBUGG", recipe_uri)
            self.set_status(201)
            self.set_header('Location', recipe_uri)
            self.finish()
        except (json.decoder.JSONDecodeError, TypeError):
            raise tornado.web.HTTPError(
                400, reason='Invalid JSON body'
            ) from None
        except ValueError as e:
            raise tornado.web.HTTPError(400, reason=str(e))


# This Handler deals with Recipy entity
class RecipeEntryRequestHandler(BaseRequestHandler):
    async def get(self, id):
        try:
            recipe = await self.service.get_recipe(id)
            self.set_status(200)
            self.finish(recipe)
        except KeyError as e:
            raise tornado.web.HTTPError(404, reason=str(e))

    async def put(self, id):
        try:
            recipe = json.loads(self.request.body.decode('utf-8'))
            await self.service.update_recipe(id, recipe)
            self.set_status(204)
            self.finish()
        except (json.decoder.JSONDecodeError, TypeError):
            raise tornado.web.HTTPError(
                400, reason='Invalid JSON body'
            )
        except KeyError as e:
            raise tornado.web.HTTPError(404, reason=str(e))
        except ValueError as e:
            raise tornado.web.HTTPError(400, reason=str(e))

    async def delete(self, id):
        try:
            await self.service.delete_recipe(id)
            self.set_status(204)
            self.finish()
        except KeyError as e:
            raise tornado.web.HTTPError(404, reason=str(e))


# Called for all other invalid requests
class DefaultRequestHandler(BaseRequestHandler):

    def initialize(  # type: ignore
        self,
        status_code: int,
        message: str,
        logger: logging.Logger
    ):
        self.logger = logger
        self.set_status(status_code, reason=message)

    def prepare(self) -> Optional[Awaitable[None]]:
        raise tornado.web.HTTPError(
            self._status_code,
            'request uri: %s',
            self.request.uri,
            reason=self._reason
        )


def log_function(handler: tornado.web.RequestHandler) -> None:
    # https://www.tornadoweb.org/en/stable/web.html#tornado.web.Application.settings

    logger = getattr(handler, 'logger', logging.getLogger(LOGGER_NAME))

    if handler.get_status() < 400:
        level = logging.INFO
    elif handler.get_status() < 500:
        level = logging.WARNING
    else:
        level = logging.ERROR

    logutils.log(
        logger,
        level,
        include_context=True,
        message='RESPONSE',
        status=handler.get_status(),
        time_ms=(1000.0 * handler.request.request_time())
    )

    logutils.clear_log_context()


def make_recipeservice_app(
    config: Dict,
    debug: bool,
    logger: logging.Logger
) -> Tuple[RecipeService, tornado.web.Application]:
    service = RecipeService(config, logger)
    app = tornado.web.Application(
            [
                (RECIPE_REGEX, RecipeRequestHandler, dict(service=service, config=config, logger=logger)), # noqa
                (RECIPE_ENTRY_REGEX, RecipeEntryRequestHandler, dict(service=service, config=config, logger=logger)) # noqa
            ],
            compress_response=True,
            log_function=log_function,  # log_request() uses it to log results
            serve_traceback=debug,
            default_handler_class=DefaultRequestHandler,
            default_handler_args={
                'status_code': 404,
                'message': 'Unknown Endpoint',
                'logger': logger
            }
    )

    return service, app
