import os
import uuid
from datetime import datetime

# Use the package we installed
from slack_bolt import App

# Initializes your app with your bot token and signing secret
app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET"),
)

topics = []

def sort_topics():
    topics.sort(reverse=True, key=lambda topic: len(topic["votes"]))

def update_home_tab(client, user):
    blocks = [{
        "dispatch_action": True,
        "type": "input",
        "element": {
            "type": "plain_text_input",
            "action_id": "add_topic-action",
        },
        "label": {
            "type": "plain_text",
            "text": "Add a Topic / Question",
            "emoji": True,
        },
    }]
    if len(topics) > 0:
        blocks.append(
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "backlog", "emoji": True},
            }
        )
        blocks.append({"type": "divider"})
        i = 0
        for topic in topics:
            blocks.append(block_for(topic, user))
            i += 1
            if i > 20:
                break
    # print(f"blocks: {json.dumps(blocks)}")
    client.views_publish(
        user_id=user,
        view={"type": "home", "callback_id": "home_view", "blocks": blocks},
    )

@app.action("add_topic-action")
def add_topic_action(ack, body, logger):
    ack()
    # print(f"body: {body}")
    user = body["user"]["id"]
    topic = {
        "votes": [user],
        "text": body["actions"][0]["value"],
        "id": str(uuid.uuid4()),
        "created": datetime.now(),
    }
    topics.append(topic)
    sort_topics()
    update_home_tab(app.client, user)

@app.action("toggle_vote")
def handle_some_action(ack, body, logger):
    ack()
    # print(f"body: {body}")
    user = body["user"]["id"]
    topic_id = body["actions"][0]["value"]
    for topic in topics:
        if topic["id"] == topic_id:
            if user in topic["votes"]:
                topic["votes"].remove(user)
            else:
                topic["votes"].append(user)
            sort_topics()
            update_home_tab(app.client, user)
            return

@app.event("message")
def message_received(client, event, logger):
    print(f"got message: \n{client} \n{event} \n{logger}")

def block_for(topic, user):
    votes = len(topic["votes"])
    section = {
        "type": "section",
        "text": {"type": "mrkdwn", "text": f"*{votes}* Votes: {topic['text']}"},
        "accessory": {
            "type": "button",
            "action_id": "toggle_vote",
            "text": {"type": "plain_text", "emoji": True},
            "value": topic["id"],
        },
    }
    if user in topic["votes"]:
        section["accessory"]["style"] = "primary"
        section["accessory"]["text"]["text"] = "unVote"
    else:
        section["accessory"]["text"]["text"] = "Vote"
    return section

@app.event("app_home_opened")
def home_opened(client, event, logger):
    # print(f"app home: \n{client} \n{event} \n{logger}")
    update_home_tab(client, event["user"])

# Start your app
if __name__ == "__main__":
    app.start(port=int(os.environ.get("PORT", 3000)))
