# dc-status-updater 🌀

A simple Python script that updates your Discord custom status with a random quote from a `.txt` file at a set interval.

## ✨ Features

* Picks a random line from `quotes.txt`
* Updates your Discord status using the Discord API
* Controlled via environment variables (`TOKEN` & `INTERVAL`)
* Lightweight and easy to run

## ⚙️ Configuration

### Required Environment Variables

* `TOKEN`: Your Discord user token *(⚠️ see note below)*
* `INTERVAL`: Time in seconds between status updates (e.g., `300` for 5 min)

You can set them in your shell or use a `.env` file:

```
TOKEN=your_discord_user_token
INTERVAL=300
```

## 📦 Setup & Usage

### Using Docker

1. **Run the container:**

```bash
docker run -d \
  --name dc-status-updater \
  -e TOKEN="your_discord_token" \
  -e INTERVAL=3600 \
  -v $(pwd)/quotes.txt:/app/quotes.txt \
  ghcr.io/thegameprofi/dc-status-updater
```

> 💡 `quotes.txt` is mounted as a volume so you can edit it on your host.

### Using Python

1. **Clone the repo**

   ```bash
   git clone https://github.com/your-username/dc-status-updater.git
   cd dc-status-updater
   ```

2. **Install dependencies**

   ```bash
   pip install requests
   ```

3. **Add your quotes**

   * Create or edit `quotes.txt`
   * Add one quote per line

4. **Run the script**

   ```bash
   python main.py
   ```

## 📄 Example quotes.txt

```
Hello there 👋
Coding like a boss 😎
UwU what's this?
Time for tea ☕
```

## ⚠️ Warning

This script uses a **user token**, which may violate Discord’s Terms of Service. Use responsibly and at your own risk.

## 📜 License

MIT – free to use, modify, and share. Just be cool 😇
