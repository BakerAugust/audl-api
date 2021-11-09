# audl-api

## About the data

### `event`

For each game, a record of events is provided by both the home and away team. Across these records major events like scores and turnovers overlap while the personel and passing information is typically only present on the record from the team in possesion.

In some instances these independent records of events don't even agree on the number of points played. 

As such, knitting together these two independent sources presents a challenge in creating a single sequence-aware record of events for each point.

## Running MySQL database locally
Simply run `docker compose up` from the project root.

## Resources 
- https://htmx.org/examples/click-to-edit/
- https://medium.com/swlh/python-with-docker-compose-fastapi-part-2-88e164d6ef86   
- https://github.com/vlcinsky/fastapi-sse-htmx/blob/master/app.py
- https://fastapi.tiangolo.com/deployment/docker/
- https://towardsdatascience.com/fastapi-cloud-database-loading-with-python-1f531f1d438a
