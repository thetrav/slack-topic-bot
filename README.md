# python
```
python -m venv .venv
.venv\scripts\Activate.ps1

source .venv/bin/activate

python main.py
```

# docker
```
docker build -t ilg/qandavoting .

docker run -it --rm -p 8080:8080 --env-file env ilg/qandavoting
```

# local auth:
```
gcloud iam service-accounts keys create .service_account.json --iam-account=<accountid>
```

# env:

```
SLACK_BOT_TOKEN=
SLACK_SIGNING_SECRET=
PROJECT_ID=
GOOGLE_APPLICATION_CREDENTIALS=.service_account.json
```