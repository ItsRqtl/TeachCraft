__all__ = ("validate_turnstile",)


async def validate_turnstile(state, response: str) -> bool:
    if not response:
        return False
    async with state.http.post(
        "https://challenges.cloudflare.com/turnstile/v0/siteverify",
        data={"secret": state.app_conf["turnstile.secret_key"], "response": response},
    ) as resp:
        if resp.status != 200:
            return False
        data = await resp.json()
        return data.get("success", False)
