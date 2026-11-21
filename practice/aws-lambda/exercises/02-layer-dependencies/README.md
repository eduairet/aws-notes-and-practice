# Layer Dependencies

Practice for the [Layer Dependencies](../../../../notes/aws-lambda/notes/aws-lambda/layer-dependencies.md) note: a function that keeps its dependencies in a layer instead of its own package.

- [`greeting-app/template.yaml`](greeting-app/template.yaml) defines:
  - `GreetingLayer` (`AWS::Serverless::LayerVersion`): a shared module, [`greeting.py`](greeting-app/layers/greeting/greeting.py), plus a third-party package (`humanize`, from the layer's [`requirements.txt`](greeting-app/layers/greeting/requirements.txt)).
  - `GreetingFunction`: imports both from the layer. Its own folder holds only `app.py`.
- `Metadata: BuildMethod: python3.13` makes `sam build` package the layer the way Lambda expects. The code and the pip-installed packages go under `python/`, and Lambda adds that folder to the import path (`/opt/python`).
- The function's deployment package stays tiny. Updating `humanize` only means publishing a new layer version.

## Run It

```bash
cd greeting-app
sam build
sam deploy --guided            # real AWS
sam remote invoke GreetingFunction --event-file events/event.json
```

Or run it against the local emulator, with the other practice projects: `docker compose run --rm practice-tests` from the repo root.

## Tests

- `tests/unit`: the layer module and the handler. `tests/conftest.py` puts the layer folder on the import path, the same thing Lambda does with `/opt/python`.
- `tests/integration`: invokes the deployed function and checks that the layer is attached and its code ran.
