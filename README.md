# Recipe Microservices

## Setup Source Code

```
$ git clone git@github.com:msriv/recipe-microservice.git
$ cd recipe-microservice
$ python3 -m venv .venv
$ source ./.venv/bin/activate
$ pip install --upgrade pip
$ pip3 install -r ./requirements.txt
```

## Type check

```
$ mypy ./recipeservice ./tests
$ ./run.py typecheck
```

## Lint check

```
$ flake8 ./addrservice ./tests
$ ./run.py lint
```

## Running the microservice

```
$ python3 recipeservice/tornado/server.py --port 8080 --config ./configs/recipe-local.yaml --debug
```

## Testing

- Run All Tests

```
$ python -m unittest discover tests -p '*_test.py'
$ ./run.py test
```

- Unit Tests

```
$ ./run.py test --suite unit
```

- Integration Tests

```
$ ./run.py test --suite integration
```
