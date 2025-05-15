import asyncio
import os
import time
from telethon import TelegramClient, errors
from telethon.tl.types import InputMessagesFilterEmpty
from telethon.tl.functions.channels import GetMessagesRequest
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.tl.types import PeerChannel
from tqdm import tqdm

API_ID = 20133674
API_HASH = 'b755fc83ab03eecf8dedd27acaa05f8a'
PHONE = '+917307868421'

SOURCE_CHANNEL_ID = -1002500762976  # Private source channel (forward denied)
TARGET_CHANNEL_USERNAME = 'vksirrs'  # Your public target channel username

SESSION_FILE = 'userbot.session'

# To keep track of processed messages
PROCESSED_FILE = 'processed_ids.txt'

async def main():
    client = TelegramClient(SESSION_FILE, API_ID, API_HASH)
    await client.start(phone=PHONE)

    print(f"Logged in as {await client.get_me().stringify()}")

    # Load processed message IDs
    if os.path.exists(PROCESSED_FILE):
        with open(PROCESSED_FILE, 'r') as f:
            processed = set(map(int, f.read().splitlines()))
    else:
        processed = set()

    print("Fetching messages from source channel...")

    offset_id = 0
    limit = 10  # fetch 10 msgs at once
    total_processed = 0

    while True:
        history = await client(GetHistoryRequest(
            peer=SOURCE_CHANNEL_ID,
            offset_id=offset_id,
            offset_date=None,
            add_offset=0,
            limit=limit,
            max_id=0,
            min_id=0,
            hash=0
        ))

        if not history.messages:
            print("No more messages to process.")
            break

        for msg in reversed(history.messages):  # oldest to newest
            if msg.id in processed:
                # skip duplicates
                continue

            print(f"\nProcessing message ID {msg.id}...")

            # Download media if any
            media_path = None
            if msg.media:
                print("Downloading media...")
                try:
                    media_path = await client.download_media(msg, file="downloads/")
                except Exception as e:
                    print(f"Error downloading media: {e}")
                    continue

            # Build caption with source msg ID
            caption = msg.message or ""
            caption += f"\n\n(Source Msg ID: {msg.id})"

            # Upload to target channel
            try:
                if media_path:
                    print("Uploading media...")
                    await client.send_file(TARGET_CHANNEL_USERNAME, media_path, caption=caption)
                    # delete downloaded file to save space
                    os.remove(media_path)
                else:
                    # text only message
                    await client.send_message(TARGET_CHANNEL_USERNAME, caption)
            except Exception as e:
                print(f"Error uploading: {e}")
                continue

            processed.add(msg.id)
            total_processed += 1

            # Save progress after each message
            with open(PROCESSED_FILE, 'w') as f:
                f.write('\n'.join(str(x) for x in processed))

            print(f"Message {msg.id} processed and uploaded. Total: {total_processed}")

            # Small delay to avoid flooding
            await asyncio.sleep(2)

        offset_id = history.messages[0].id

    print("All messages processed.")

if __name__ == '__main__':
    asyncio.run(main())
