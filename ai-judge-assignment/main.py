"""
Minimal glue code for Rock-Paper-Scissors Plus AI Judge.
Uses Google Gemini; game logic and decisions are driven by prompts.
"""
import os
import random
import re

# Try to load .env from this folder (optional convenience)
env_path = os.path.join(os.path.dirname(__file__), ".env")
try:
    from dotenv import load_dotenv

    load_dotenv(env_path)
except ImportError:
    pass


MOVES = ["rock", "paper", "scissors", "bomb"]

game_state = {
    "round": 1,
    "user_score": 0,
    "bot_score": 0,
    "user_bomb_used": False,
    "bot_bomb_used": False,
}


def load_prompts():
    """Load system prompt and instruction template from prompts.txt."""
    path = os.path.join(os.path.dirname(__file__), "prompts.txt")
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    # Split by INSTRUCTION PROMPT TEMPLATE section
    parts = re.split(r"INSTRUCTION PROMPT TEMPLATE", text, maxsplit=1)
    system_raw = parts[0].replace("SYSTEM PROMPT", "").replace("=" * 80, "").strip()
    template_raw = parts[1].replace("=" * 80, "").strip() if len(parts) > 1 else ""
    return system_raw, template_raw


def get_bot_move():
    """Bot picks a move; cannot pick bomb if already used."""
    if game_state["bot_bomb_used"]:
        return random.choice(["rock", "paper", "scissors"])
    return random.choice(MOVES)


def update_state_from_response(response_text: str, bot_move: str):
    """
    Minimal parsing: update round, scores, and bomb usage from AI response.
    No game logic here—we trust the judge's Round Result and Updated Score.
    """
    global game_state
    lines = response_text.strip().split("\n")

    # Round result
    for line in lines:
        if "Round Result:" in line:
            if "User wins" in line:
                game_state["user_score"] += 1
            elif "Bot wins" in line:
                game_state["bot_score"] += 1
            break

    # Bomb usage: if user move was bomb and valid, mark used
    move_status = ""
    user_move_interpreted = ""
    for line in lines:
        if "Move Status:" in line:
            move_status = line.split(":")[-1].strip().upper()
        if "User Move:" in line:
            user_move_interpreted = line.split(":")[-1].strip().lower()
    if move_status == "VALID" and user_move_interpreted == "bomb":
        game_state["user_bomb_used"] = True
    if bot_move == "bomb":
        game_state["bot_bomb_used"] = True

    # Optional: sync scores from "Updated Score" if present (AI is source of truth)
    for i, line in enumerate(lines):
        if "Updated Score:" in line and i + 2 < len(lines):
            # Next lines often "User: X" and "Bot: Y"
            rest = "\n".join(lines[i:])
            u = re.search(r"User:\s*(\d+)", rest)
            b = re.search(r"Bot:\s*(\d+)", rest)
            if u and b:
                game_state["user_score"] = int(u.group(1))
                game_state["bot_score"] = int(b.group(1))
            break

    game_state["round"] += 1


def run_round(user_input: str) -> str:
    """Build prompts, call Gemini, update state, return response text."""
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        return (
            "Error: Install the Gemini SDK: pip install google-genai\n"
            "Set GEMINI_API_KEY in your environment (get key from https://aistudio.google.com/apikey)."
        )

    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return "Error: Set GEMINI_API_KEY in your environment (get key from https://aistudio.google.com/apikey)."

    system_prompt, instruction_template = load_prompts()
    bot_move = get_bot_move()

    instruction = instruction_template.format(
        round_number=game_state["round"],
        user_bomb=game_state["user_bomb_used"],
        bot_bomb=game_state["bot_bomb_used"],
        user_score=game_state["user_score"],
        bot_score=game_state["bot_score"],
        bot_move=bot_move,
        user_input=user_input,
    )

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=instruction,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
        ),
    )
    response_text = response.text if response.text else "(No text in response)"

    update_state_from_response(response_text, bot_move)
    return response_text


def main():
    print("Rock-Paper-Scissors Plus — AI Judge")
    print("Valid moves: rock, paper, scissors, bomb (bomb once per player).")
    print("Type your move and press Enter. Empty input to quit.\n")

    while True:
        try:
            user_input = input("Your move: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            break
        if not user_input:
            print("Bye.")
            break

        print()
        result = run_round(user_input)
        print(result)
        print()


if __name__ == "__main__":
    main()
