import os
import uuid
from datetime import datetime
from flask import Flask, request
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler

# Initializes your app with your bot token and signing secret
app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET"),
)

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

# Use the application default credentials
cred = credentials.ApplicationDefault()
firebase_admin.initialize_app(cred, {
  'projectId': os.environ.get("PROJECT_ID"),
})

db = firestore.client()

topics = db.collection(u'topics')

def get_topic(id):
    for topic in get_topics():
        if topic["id"] == id:
            return topic

def add_topic(topic):
    doc_ref = topics.document(topic["id"])
    doc_ref.set(topic)

def delete_topic(topic):
    topics.document(topic["id"]).delete()

def get_topics():
    docs = topics.stream()
    dicts = [d.to_dict() for d in docs]
    dicts.sort(reverse=True, key=lambda topic: len(topic["votes"]))
    return dicts

def update_topic(topic):
    doc_ref = topics.document(topic["id"])
    doc_ref.set(topic)

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
    topics = get_topics()
    if len(topics) > 0:
        blocks.append(
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "backlog", "emoji": True},
            }
        )
        i = 0
        for topic in topics:
            for block in block_for(topic, user):
                blocks.append(block)
            i += 1
            if i > 20:
                break
    # import json
    # print(f"blocks: {json.dumps(blocks)}")
    client.views_publish(
        user_id=user,
        view={"type": "home", "callback_id": "home_view", "blocks": blocks},
    )

@app.action("add_topic-action")
def add_topic_action(ack, body, logger):
    ack()
    print(f"body: {body}")
    user = body["user"]["id"]
    topic = {
        "votes": [user],
        "text": body["actions"][0]["value"],
        "id": str(uuid.uuid4()),
        "created": datetime.now(),
        "created_by": user
    }
    add_topic(topic)
    update_home_tab(app.client, user)

@app.action("delete_topic")
def delete_topic_action(ack, body, logger):
    ack()
    # print(f"body: {body}")
    user = body["user"]["id"]
    id = body["actions"][0]["value"]
    topic = get_topic(id)
    if can_delete(topic, user):
        delete_topic(topic)
        update_home_tab(app.client, user)

@app.action("toggle_vote")
def handle_some_action(ack, body, logger):
    ack()
    # print(f"body: {body}")
    user = body["user"]["id"]
    topic_id = body["actions"][0]["value"]
    for topic in get_topics():
        if topic["id"] == topic_id:
            if user in topic["votes"]:
                topic["votes"].remove(user)
            else:
                topic["votes"].append(user)
            update_topic(topic)
            update_home_tab(app.client, user)
            return

@app.event("message")
def message_received(client, event, logger):
    print(f"got message: \n{client} \n{event} \n{logger}")

def can_delete(topic, user):
    if topic["created_by"] != user:
        return False 
    if len(topic["votes"]) > 1:
        return False
    if len(topic["votes"]) == 1 and topic["votes"][0] != user:
        return False
    return True

def block_for(topic, user):
    votes = len(topic["votes"])
    section = {
        "type": "section",
        "text": {
            "type": "mrkdwn", 
            "text": f"*Topic:* {topic['text']} \n *Votes:* {votes}"
        }
    }
    vote_button = {
        "type": "button",
        "text": {
            "type": "plain_text",
            "text": "Vote"
        },
        "action_id": "toggle_vote",
        "value": topic["id"]
    }
    if user in topic["votes"]:
        vote_button["style"] = "primary"
        vote_button["text"]["text"] = "unVote"
    actions = {
        "type": "actions",
        "elements": [vote_button]
    }
    if can_delete(topic, user):
        actions["elements"].append({
            "type": "button",
            "text": {
                "type": "plain_text",
                "text": "Delete"
            },
            "action_id": "delete_topic",
            "style": "danger",
            "value": topic["id"]
        })
    
    return [{"type":"divider"},section, actions]

@app.event("app_home_opened")
def home_opened(client, event, logger):
    # print(f"app home: \n{client} \n{event} \n{logger}")
    update_home_tab(client, event["user"])

flask_app = Flask(__name__)
handler = SlackRequestHandler(app)

@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    return handler.handle(request)

def post_to_channels(topic):
    resp = app.client.users_conversations(exclude_archived=True)
    # print(f"got: {resp}")
    for channel in resp["channels"]:
        post_to_channel(topic, channel["id"])

def post_to_channel(topic, channel):
    app.client.chat_postMessage(
        channel=channel,
        text=f"Todays topic of choice is: \n```\n{topic['text']}\n```\n\nPlease use a thread to discuss!"
    )

@flask_app.route("/pop")
def pop_topic():
    topics = get_topics()
    if len(topics) > 0:
        topic = topics[0]
        post_to_channels(topic)
        delete_topic(topic)
    return "", 200

# Start your app
if __name__ == "__main__":
    flask_app.run(port=int(os.environ.get("PORT", 8080)))
