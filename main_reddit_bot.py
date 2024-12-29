import praw
import time
import logging
import config
import os
import unicodedata

# File to store replied comment IDs
REPLIED_COMMENTS_FILE = "replied_comments.txt"

# Set up logging
logging.basicConfig(
    filename='bot.log',
    level=logging.DEBUG,  # Set to DEBUG for detailed output
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def bot_login():
    """Authenticate with Reddit."""
    try:
        r = praw.Reddit(
            username=config.username,
            password=config.password,
            client_id=config.client_id,
            client_secret=config.client_secret,
            user_agent="brandon test bot"
        )
        logging.info(f"Logged in as {r.user.me()}")
        return r
    except Exception as e:
        logging.error(f"Login error: {e}")
        raise

def load_replied_comments():
    """Load replied comment IDs from file, normalizing line endings and handling encoding/control characters."""
    try:
        if os.path.exists(REPLIED_COMMENTS_FILE):
            with open(REPLIED_COMMENTS_FILE, "r", encoding="utf-8") as f:
                replied = set()
                for line_number, line in enumerate(f):
                    # Normalize line endings:
                    cleaned_line = line.replace('\r\n', '\n').replace('\r', '\n').strip()
                    original_length = len(cleaned_line)
                    cleaned_line = "".join(ch for ch in cleaned_line if unicodedata.category(ch)[0] != "C")
                    if original_length != len(cleaned_line):
                        logging.debug(f"Line {line_number + 1}: Removed control characters. Original: '{line.strip()}', Cleaned: '{cleaned_line}'")
                    if cleaned_line:
                        replied.add(cleaned_line)
                    else:
                        logging.debug(f"Line {line_number + 1}: Line is empty or contains only control characters after cleaning.")
                logging.debug(f"Loaded {len(replied)} replied comment IDs.")
                return replied
        else:
            logging.debug("Replied comments file does not exist. Starting with empty set.")
            return set()
    except Exception as e:
        logging.error(f"Error loading replied comments: {e}")
        return set()

def save_replied_comment(comment_id):
    """Save a replied comment ID to file, using UTF-8 encoding."""
    try:
        with open(REPLIED_COMMENTS_FILE, "a", encoding="utf-8") as f:
            f.write(comment_id + "\n")
    except Exception as e:
        logging.error(f"Error saving replied comment: {e}")
# IMPORTANT here is where you will need to edit the sub reddit you are tyring to use this put in and what you want the bot to say
def run_bot(r, replied_comments):
    """Run the bot, checking for new comments and handling rate limits."""
    try:
        for comment in r.subreddit("test").comments(limit=25):
            if "dog" in comment.body.lower():
                logging.debug(f"Found 'dog' in comment: {comment.id}, Body: {comment.body}")
                if comment.id not in replied_comments:
                    logging.debug(f"Comment {comment.id} not in replied_comments. Replying...")
                    try:
                        comment.reply("Did someone say dog? 🐶")
                        logging.info(f"Replied to: {comment.id}")
                        replied_comments.add(comment.id)
                        save_replied_comment(comment.id)
                    except praw.exceptions.APIException as e:
                        if e.error_type == "RATELIMIT":
                            logging.warning("Rate limited. Sleeping...")
                            time.sleep(60)
                            continue  # Skip to the next comment
                        else:
                            logging.error(f"API Error replying: {e}")
                    except Exception as e:
                        logging.error(f"Error replying: {e}")
                else:
                    logging.debug(f"Already replied to comment: {comment.id}. Skipping.")
                    # Detailed comparison and logging
                    logging.debug(f"Replied Comments Set: {replied_comments}")
                    for id_in_file in replied_comments:
                        logging.debug(f"Comparing: Reddit ID '{comment.id}' vs. File ID '{id_in_file}', Match: {comment.id == id_in_file}")
    except Exception as e:
        logging.error(f"Error in main bot loop: {e}")

def main():
    """Main function to start the bot."""
    r = bot_login()
    replied_comments = load_replied_comments()

    while True:
        run_bot(r, replied_comments)
        time.sleep(10)

if __name__ == "__main__":
    main()
