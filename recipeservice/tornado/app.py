import json
import traceback
from typing import Any, Awaitable, Dict, Optional, Tuple
from recipeservice.service import RecipeService
import tornado.web

RECIPE_REGEX = r'/v1/recipes'
RECIPE_ENTRY_REGEX = r'/v1/recipes/(?P<id>[a-zA-Z0-9-]+)/?'
RECIPE_ENTRY_URI_FORMAT_STR = r'/v1/recipes/{id}'

class BaseRequestHandler(tornado.web.RequestHandler):
  def initialize(
        self,
        service: RecipeService,
        config: Dict
    ) -> None:
        self.service = service
        self.config = config
  
  def prepare(self) -> Optional[Awaitable[None]]:
    msg = 'REQUEST: {method} {uri} ({ip})'.format(
      method=self.request.method,
      uri=self.request.uri,
      ip=self.request.remote_ip
    )
    print(msg)

    return super().prepare()

  def on_finish(self) -> None:
    super().on_finish()
  
  def write_error(self, status_code: int, **kwargs: Any) -> None:
    body = {
      'method': self.request.method,
      'uri': self.request.path,
      'code': status_code,
      'message': self._reason
    }

    if self.settings.get("serve_traceback") and "exc_info" in kwargs:
      trace = '\n'.join(traceback.format_exception(*kwargs['exc_info']))
      body['trace'] = trace
    
    self.finish(body)

# This Handler deals with Recipe entities
class RecipeRequestHandler(BaseRequestHandler):
  async def get(self):
    all_recipes = await self.service.get_all_recipes()
    self.set_status(200)
    self.finish(all_recipes)

  async def post(self):
    try:
      recipe = json.loads(self.request.body.decode('utf-8'))
      id = await self.service.create_recipe(recipe)
      recipe_uri = RECIPE_ENTRY_URI_FORMAT_STR.format(
        id=id
      )
      self.set_status(201)
      self.set_header('Location', recipe_uri)
      self.finish()
    except (json.decoder.JSONDecodeError, TypeError):
      raise tornado.web.HTTPError(
        400, reason="Invalid JSON body"
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
  def initialize(self, status_code, message):
    self.set_status(status_code, reason=message)

  def prepare(self) -> Optional[Awaitable[None]]:
    raise tornado.web.HTTPError(
      self._status_code, reason=self._reason
    )

def log_function(handler: tornado.web.RequestHandler) -> None:
  status = handler.get_status()
  request_time = 1000.0 * handler.request.request_time()

  msg = 'RESPOSE: {status} {method} {uri} ({ip}) {time}ms'.format(
      status=status,
      method=handler.request.method,
      uri=handler.request.uri,
      ip=handler.request.remote_ip,
      time=request_time,
  )

  print(msg)


def make_recipeservice_app(
  config: Dict,
  debug: bool
) -> Tuple[RecipeService, tornado.web.Application]:
  service = RecipeService(config)
  app = tornado.web.Application(
    [
      (RECIPE_REGEX, RecipeRequestHandler, dict(service=service, config=config)),
      (RECIPE_ENTRY_REGEX, RecipeEntryRequestHandler, dict(service=service, config=config))
    ],
    compress_response=True,
    serve_traceback=debug,
    default_handler_class=DefaultRequestHandler,
    default_handler_args={
      'status_code': 404,
      'message': 'Unknown Endpoint'
    }
  )

  return service, app