# Users CRUD test API

A simple example of a CRUD API for a `users` collection using 
[FastAPI](https://fastapi.tiangolo.com/) 
and [Tortoise-ORM](https://tortoise-orm.readthedocs.io/en/latest/index.html)
with a PostgresSQL database.

### Setting up
Have docker installed and run
```shell
make docker-serve-build
# or
docker-compose up -d --build
```

### Running Integration Tests
```shell
make docker-run-tests
# or
docker-compose exec api pytest -c ./pyproject.toml --disable-pytest-warnings
```


### API Documentation
Head to http://localhost:8080/docs or http://localhost:8080/redoc


## Future Work
+ Add pagination, sorting, field exclusion and filtering to users list endpoint
+ User profile image to get saved in a cloud bucket and served through CDN, 
instead of being saved in the server's file system
