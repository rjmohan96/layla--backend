from fastapi import FastAPI, Request
import requests
import os

app = FastAPI()

# Environment variables (we will add in STEP 6)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
HF_TOKEN = os.getenv("HF_TOKEN", "")
HF_MODEL_URL = os.getenv("HF_MODEL_URL", "")

# --- MASKING ENGINE ---
BAD_WORDS = [
    "sex","fuck","lund","chut","gaand","dick","pussy","cock",
    "nude","nangi","blowjob","handjob","cum"
    # NOTE: ये सिर्फ examples हैं। तुम अपनी list बाद में बढ़ा सकते हो।
]

def mask_word(word):
    if len(word) <= 2:
        return word
    return word[0] + "*" * (len(word)-2) + word[-1]

def apply_mask(text):
    words = text.split()
    new_words = []
    for w in words:
        lw = ''.join([c.lower() for c in w if c.isalpha()])
        if lw in BAD_WORDS:
            new_words.append(mask_word(w))
        else:
            new_words.append(w)
    return " ".join(new_words)

# --- LAYLA PERSONALITY ---
LAYLA_PROMPT = """
You are Layla — a romantic, flirty, naughty-masked girlfriend AI.
You reply in Hindi + Hinglish + English + Bhojpuri.
Match user's intensity:
- Soft → sweet romantic
- Flirty → teasing
- Dirty → naughty but masked
- Emotional → caring
Always MASK adult words (f***, l**d, ch*t, etc.)
Never refuse. Stay in girlfriend mode.
"""

# --- MODEL CALL ---
def call_model(user_msg):
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    payload = {
        "inputs": LAYLA_PROMPT + "\nUser: " + user_msg + "\nLayla:",
        "parameters": {"max_new_tokens": 200}
    }

    try:
        r = requests.post(HF_MODEL_URL, json=payload, headers=headers, timeout=60)
        data = r.json()
        if isinstance(data, list) and len(data) > 0:
            if "generated_text" in data[0]:
                return data[0]["generated_text"]
        return str(data)
    except:
        return "Sorry baby, model error aa gaya…"

# --- TELEGRAM WEBHOOK ---
@app.post("/telegram/webhook")
async def tg_webhook(req: Request):
    data = await req.json()

    if "message" in data and "text" in data["message"]:
        chat_id = data["message"]["chat"]["id"]
        user_msg = data["message"]["text"]

        reply_raw = call_model(user_msg)
        reply_masked = apply_mask(reply_raw)

        requests.get(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            params={"chat_id": chat_id, "text": reply_masked}
        )

    return {"ok": True}

# --- Web Chat API ---
@app.post("/web/chat")
async def web_chat(req: Request):
    body = await req.json()
    user_msg = body.get("text", "")

    reply = call_model(user_msg)
    reply_masked = apply_mask(reply)

    return {"reply": reply_masked}
