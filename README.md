Unshadow
========
An experiment in web crawler development
----------------------------------------

A poorly hacked together web crawler and visualization utilities.


# Build/start the container
```
sudo docker build .
sudo docker run -ti <container_id> /bin/bash
```

# Run the crawler
```
./entrypoint.sh
```

# Backup postgresql

In container
```
pg_dump -U unshadow -d unshadow > /backup
```

In host
```
sudo docker cp <container_id>:/backup ./backup
```
