# Django Rest Framework based backend application for Spaced Repetition Web App project

## Installation
After downloading the repository from GitHub, you can either
* Install dependencies in you local (set up and configured)
virtual environment:
  ```
  pip install -r requirements.txt
  ```
  and additional development requirements:
  ```
  pip install -r requirements_dev.txt
  ```
  * setup PostgreSQL database
  * setup required environment variables (which are listed in the
  docker-compose-dev.yml in the *environment* section - in this case
  you can use them just for reference)
  * update wsra/settings.py with configuration that are proper for you
  installation instance - database host etc.
* OR build docker containers:
   * ```docker-compose -f docker-compose-dev.yml up --build web```
   for development build
   * ```docker-compose -f docker-compose-prod.yml up --build web```
   for production build
   * note though, that you will also have to install
   PostgreSQL container for database and/or remove/update sections
   for database from docker-compose files if you already have
   your DBMS installed locally.

## Usage
Consult frontend app README.md for details on how to use this app and how
to install and configure frontend part of it.
