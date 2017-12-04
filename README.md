# uam
Universal application manager.

## Development
### Create a docker environment
```
docker run -dt -v `pwd`:/app --workdir /app --entrypoint bash --name uam -v /var/run/docker.sock:/var/run/docker.sock -v `pwd`/uamlib/:/usr/local/uam python:2
docker exec -ti uam bash
```

### Run Locally
1. Run without installation:
   ```
   python -m uam
   ```

2. Install locally and run:
   ```
   pip install --editable .
   uam
   ```
