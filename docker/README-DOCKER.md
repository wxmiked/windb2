Before you begin
================
This Docker build uses the [official PostgreSQL image](https://hub.docker.com/_/postgres/). It uses Docker environment variables to make custom configurations easy. You can read more about all of the options at [this page](https://hub.docker.com/_/postgres/).

As this is currently set up, you can only install official WinDB2 releases from GitHub, configured with the WINDB2_environment variable. You could easily modify the script to simply copy over the WinDB2 Git repository files to the Docker image if you want to have a developmental version of WinDB2 in your Docker image.

Building
========

```shell
% docker build -t postgres-windb2 --build-arg WINDB2_VERSION=2.0.1 .
```

Running
=======

The command starts the WinDB2, opens port 7000 to it, and links a volume outside of the container to store the main database files.

```shell
% docker run --name mywindb2 -p 7000:5342 -v /data/docker-windb2:/var/lib/postgresql/data -e  POSTGRES_PASSWORD=mysecretpassword -d postgres-windb2
```
Note if you want this image to always restart (e.g. in a production environment), add the `--restart=always` arg.

Connect to the instance
=======================

```shell
% docker run -it --rm --link mywindb2:postgres postgres psql -h postgres -U postgres
```
