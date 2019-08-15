# Building WinDB2 Docker Server and Client Images

## Before you begin
This Docker build uses the [official PostgreSQL image](https://hub.docker.com/_/postgres/). It uses Docker environment variables to make custom configurations easy. You can read more about all of the options at [this page](https://hub.docker.com/_/postgres/).

As this is currently set up, you can only install official WinDB2 releases from GitHub, configured with the WINDB2_HOME environment variable. You could easily modify the script to simply copy over the WinDB2 Git repository files to the Docker image if you want to have a developmental version of WinDB2 in your Docker image.

## Building
In the same directory as this README-DOCKER.md run the following command.  Make sure you look at the [releases](https://github.com/sailorsenergy/windb2/releases) page to get the current version of WinDB2. You may need to prepend the `sudo` command if you haven't set Docker up to run as a user:

```shell
% docker build -t windb2-server -f Dockerfile-server .
% docker build -t windb2-client -f Dockerfile-client .
```

## Running
The command starts the WinDB2, opens port 7000 to it, and links a volume outside of the container to store the main database files. You should create a local data directory like the one named `/data/docker-windb2` in the command below.

```shell
docker run --name mywindb2-server -v /data/docker-windb2:/var/lib/postgresql/data -e POSTGRES_PASSWORD=mysecretpassword -d windb2-server
```
Note if you want this image to always restart (e.g. in a production environment), add the `--restart=always` arg.

## Connect to the instance
If you want to connect to the WinDB2 instance and don't want to install the Postgres client, use the following command to use Postgres client in the Docker instance to connect.

```shell
docker run -it --rm --link mywindb2-server:postgres postgres psql -h postgres -U postgres windb2
```

You will have to enter the password that you set as `POSTGRES_PASSWORD` above, the default of which is "mysecretpassword". Alternatively you can use a `$HOME/.pgpass` for authentication.

You can use the `windb2-client` Docker image to insert WRF, GFS, etc... data as shown in the README.md in the root directory.
