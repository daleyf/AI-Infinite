import os
from datetime import datetime
from config import LOG_DIR, STREAM_LOG_FILE
from utils import ensure_dir_exists


ensure_dir_exists(LOG_DIR)

def log_text(text: str) -> None:
    from datetime import datetime
    now = datetime.now()
    time_str = now.strftime("%I:%M%p").lower()
    day_str = now.strftime("%m-%d")

    time_and_date = f"time: {time_str}\nday: {day_str}\n"

    # Save to file
    with open(STREAM_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(time_and_date + "\n" + text + "\n\n")

    # Print cleanly to terminal
    print(time_and_date)     # ✅ Prints on two lines
    print(text.strip())      # ✅ Prints your log content
    print("=" * 40)
    

