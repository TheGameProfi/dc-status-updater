import requests


class DiscordClient:
    def __init__(self, token: str) -> None:
        self._token = token
        self._url = "https://discord.com/api/v10/users/@me/settings"

    def update_status(self, text: str) -> None:
        if not self._token:
            raise PermissionError("TOKEN is not configured.")

        response = requests.patch(
            self._url,
            headers={"Authorization": self._token},
            json={"custom_status": {"text": text}},
            timeout=15,
        )

        if response.ok:
            return
        if response.status_code == 401:
            raise PermissionError("Invalid Discord token.")
        if response.status_code == 429:
            raise RuntimeError(f"Discord rate limit: {response.text}")
        raise RuntimeError(f"Discord API error {response.status_code}: {response.text}")
