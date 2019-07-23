[![pipeline status](https://gitlab.com/sv1r4/shome.assistant/badges/master/pipeline.svg)](https://gitlab.com/sv1r4/shome.assistant/commits/master)

## build docker

``` shell
docker build -t shome.assistant ./src/shome.assistant/
```

## run docker

``` shell
docker run -e 'GOOGLE_APPLICATION_CREDENTIALS=/app/secrets/key.json' --privileged -it  shome.assistant
````
