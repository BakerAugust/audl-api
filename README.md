# [ultidata](https://ultidata-dfj8c.ondigitalocean.app/)
A sandbox app for playing with Fast-API, HTMX, MySQL, and app deployment.

## About the data

The data are loaded through a manually-triggered script `etl.batch_load.py`. The script looks at url endpoints from [AUDL-Advanced-Stats](https://github.com/JohnLithio/AUDL-Advanced-Stats/blob/main/audl_advanced_stats/constants.py) identified by a script from [AUDLStats](https://github.cm/JWylie43/AUDLStats) to get a json blob for each game in 2021 that has not already been loaded. The resulting json blobs are parsed and normalized into relational models then loaded into the database.


## Useful References 
- https://htmx.org/examples/click-to-edit/
- https://medium.com/swlh/python-with-docker-compose-fastapi-part-2-88e164d6ef86   
- https://github.com/vlcinsky/fastapi-sse-htmx/blob/master/app.py
- https://fastapi.tiangolo.com/deployment/docker/
- https://towardsdatascience.com/fastapi-cloud-database-loading-with-python-1f531f1d438a
