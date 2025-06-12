import random
import requests
import time
import sys
import os

def read_quotes():
    with open("quotes.txt", "r") as file:
        quotes = file.readlines()
    return quotes

def main():
    quotes = read_quotes()
    token = os.getenv("TOKEN")
    timeout = int(os.getenv("INTERVAL")

    try:
        while True:
            quote = random.choice(quotes)

            res = requests.patch("https://discord.com/api/v10/users/@me/settings", headers={"Authorization": token}, json={"custom_status": {"text": quote}})
            if res.ok:
                print(f'New Quote: {quote}')
            elif res.status_code == 429:
                print(f'Rate Limited: {res.json()}')
            elif res.status_code == 401:
                sys.exit("Invalid Token")
            else:
                print(res.json())
                print(f'Error: {res.status_code}')
            time.sleep(timeout)
    except KeyboardInterrupt:
        print("Exiting...")


if __name__ == "__main__":
    main()
