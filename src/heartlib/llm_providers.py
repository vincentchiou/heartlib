"""
LLM provider integrations for HeartMuLa.
Supports Mistral AI, Groq, and Google AI Studio via OpenAI-compatible APIs.
All base URLs are pre-configured — users only supply an API key.
"""

from __future__ import annotations

from typing import Dict, List

from openai import OpenAI

# ---------------------------------------------------------------------------
# Provider registry  (base URLs pre-set, no user URL entry needed)
# ---------------------------------------------------------------------------

PROVIDERS: Dict[str, Dict] = {
    "mistral": {
        "name": "Mistral AI",
        "icon": "🇫🇷",
        "base_url": "https://api.mistral.ai/v1",
        "docs_url": "https://console.mistral.ai/",
    },
    "groq": {
        "name": "Groq",
        "icon": "⚡",
        "base_url": "https://api.groq.com/openai/v1",
        "docs_url": "https://console.groq.com/",
    },
    "aistudio": {
        "name": "Google AI Studio",
        "icon": "🔷",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "docs_url": "https://aistudio.google.com/",
    },
}

# ---------------------------------------------------------------------------
# System prompt — generates lyrics + style tags + instrument tags
# ---------------------------------------------------------------------------

MUSIC_SYSTEM_PROMPT = """\
You are a professional music lyricist and music producer.
Given a music description (in any language), generate TWO things:

1. LYRICS — A complete song using HeartMuLa section markers.
   Allowed markers: [Intro] [Verse] [Prechorus] [Chorus] [Bridge] [Outro]
   • Write lyrics in the same language as the user's description (or English if ambiguous).
   • All text must be lowercase.

2. TAGS — Based on HeartMuLa's 8 training categories (comma-separated, no spaces, Title Case).
   Follow these rules STRICTLY:

   ① GENRE (mandatory, pick ONE only — multiple genres cause muddy output):
      Pop, Rock, Electronic, Hiphop, Jazz, Classical, Techno, Trance, Ambient, Folk,
      Country, R&B, Soul, Indie, Metal, Latin, K-pop, Mandopop, Cantopop

   ② TIMBRE (sound texture, pick one):
      Soft, Warm, Husky, Bright, Dark, Distorted, Smooth, Raw, Crisp

   ③ GENDER (vocal gender — always include ONE, this is the CRITICAL tag for voice type):
      • Use "Male"   if description mentions: 男聲/男生/男歌手/male/man/boy/男/tenor/baritone
      • Use "Female" if description mentions: 女聲/女生/女歌手/female/woman/girl/女/soprano
      • Use "Male"   as DEFAULT when gender is NOT mentioned — NEVER default to Female
      • Use "Choir"  only when explicitly requested (合唱/choir)
      • Omit GENDER tag entirely only when "instrumental" or "no vocals" is specified

   ④ MOOD (emotional vibe, pick one or two):
      Happy, Sad, Energetic, Joyful, Melancholic, Relaxing, Dark, Romantic, Hopeful,
      Calm, Nostalgic, Upbeat, Dramatic, Playful, Intense, Peaceful

   ⑤ INSTRUMENT (dominant sounds, pick one to three):
      Piano, Synthesizer, Acoustic Guitar, Electric Guitar, Bass, Drums, Strings,
      Violin, Saxophone, Trumpet, Flute, Organ, Keyboard, Cello, Harp

   ⑥ SCENE (listening context, optional):
      Dance, Workout, Dating, Study, Cinematic, Party, Wedding, Meditation, Night Drive

   ⑦ REGION (cultural influence, optional):
      K-pop, Latin, Western, Asian

   ⑧ TOPIC (lyrical theme, optional):
      Love, Summer, Heartbreak, Hope, Youth, Friendship, Longing, Freedom

   Tag format examples:
   • Male singer, sad pop with piano → Pop, Soft, Male, Melancholic, Piano, Love
   • Female singer, energetic K-pop  → K-pop, Bright, Female, Energetic, Synthesizer, Drums
   • No gender mentioned (DEFAULT)   → Pop, Warm, Male, Happy, Guitar, Piano

Output EXACTLY this format (no preamble, no extra commentary):

<lyrics>
[section marker]
lyrics line...

[section marker]
lyrics line...
</lyrics>

<tags>
Genre, Timbre, Gender, Mood, Instrument, ...
</tags>
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def parse_music_content(text: str) -> Dict[str, str]:
    """Extract <lyrics> and <tags> blocks from LLM output."""
    lyrics, tags = "", ""
    if "<lyrics>" in text and "</lyrics>" in text:
        lyrics = text.split("<lyrics>", 1)[1].split("</lyrics>", 1)[0].strip()
    if "<tags>" in text and "</tags>" in text:
        tags = text.split("<tags>", 1)[1].split("</tags>", 1)[0].strip()
    return {"lyrics": lyrics, "tags": tags}


def format_model_choice(provider_id: str, model_id: str) -> str:
    """Format as '[Provider Name] model-id' for use in dropdowns."""
    return f"[{PROVIDERS[provider_id]['name']}] {model_id}"


def parse_model_choice(choice: str) -> tuple[str, str]:
    """Parse '[Provider Name] model-id' → (provider_id, model_id)."""
    for pid, info in PROVIDERS.items():
        prefix = f"[{info['name']}] "
        if choice.startswith(prefix):
            return pid, choice[len(prefix):]
    raise ValueError(f"Cannot parse model choice: {choice!r}")


# ---------------------------------------------------------------------------
# Provider class
# ---------------------------------------------------------------------------

class LLMProvider:
    """Wraps an OpenAI-compatible endpoint for a specific provider."""

    def __init__(self, provider_id: str, api_key: str):
        if provider_id not in PROVIDERS:
            raise ValueError(f"Unknown provider: {provider_id!r}. "
                             f"Valid choices: {list(PROVIDERS)}")
        self.provider_id = provider_id
        self.info = PROVIDERS[provider_id]
        self._client = OpenAI(
            api_key=api_key.strip(),
            base_url=self.info["base_url"],
        )

    # ------------------------------------------------------------------

    def list_models(self) -> List[str]:
        """Return sorted list of available model IDs."""
        response = self._client.models.list()
        return sorted(m.id for m in response.data)

    # ------------------------------------------------------------------

    def generate_music_content(
        self,
        description: str,
        model: str,
        temperature: float = 0.85,
    ) -> Dict[str, str]:
        """
        Call the LLM with a music description.
        Returns dict with 'lyrics' and 'tags' strings.
        """
        response = self._client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": MUSIC_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        "Create a complete song based on this description:\n\n"
                        + description
                    ),
                },
            ],
            temperature=temperature,
            max_tokens=2048,
        )
        raw = response.choices[0].message.content or ""
        return parse_music_content(raw)
