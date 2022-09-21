import asyncio
from typing import Dict
from recipeservice.tornado.app import make_recipeservice_app
from recipeservice.service import RecipeService
import tornado.web
import yaml
import argparse


def parse_args(args=None):
    parser = argparse.ArgumentParser(
        description='Run Recipe Server'
    )

    parser.add_argument(
        '-p',
        '--port',
        type=int,
        default=8080,
        help='port number for %(prog)s server to listen; '
        'default: %(default)s'
    )

    parser.add_argument(
        '-d',
        '--debug',
        action='store_true',
        help='turn on debug logging'
    )

    parser.add_argument(
        '-c',
        '--config',
        required=True,
        type=argparse.FileType('r'),
        help='config file for %(prog)s in yaml'
    )

    args = parser.parse_args(args)
    return args


def run_server(
    app: tornado.web.Application,
    service: RecipeService,
    config: Dict,
    port: int,
    debug: bool
):
    # name = config['service']['name']
    loop = asyncio.get_event_loop()
    service.start()

    http_server_args = {
        'decompress_request': True
    }

    http_server = app.listen(port, '', **http_server_args)
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        loop.stop()
        http_server.stop()
        loop.run_until_complete(
            loop.shutdown_asyncgens()
        )
        service.stop()
        loop.close()


def main(args=parse_args()):
    config = yaml.load(args.config.read(), Loader=yaml.SafeLoader)
    recipe_service, recipe_app = make_recipeservice_app(config, args.debug)
    run_server(
        app=recipe_app,
        service=recipe_service,
        config=config,
        port=args.port,
        debug=args.debug
    )


if __name__ == '__main__':
    main()


# Run server
# python3 recipeservice/tornado/server.py --port 8080 --config ./configs/recipe-local.yaml --debug # noqa