# Slack Topic Bot
A bot for enabling a group to discretely suggest topics, vote on what they want to talk about, and then have discussion promted in channel.

You will need to handle setup and deployment yourself, but what I did was:

+ Setup an app and bot in slack
+ Create the firestore
+ Put the relevant secrets in google secret manager
+ Deploy the app using google cloud run
+ Create a google cloud scheduler instance to hit the "pop" url on a schedule (9am weekdays for us)
+ Install the app to your workspace and invite it to your channel

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
docker tag ilg/qandavoting gcr.io/initiative-leads-guild/ilg/qandavoting
docker push gcr.io/initiative-leads-guild/ilg/qandavoting 

docker run -it --rm -p 8080:8080 --env-file env -v ${PWD}:/secrets ilg/qandavoting
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