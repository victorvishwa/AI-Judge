# Rock-Paper-Scissors Plus — AI Judge Assignment

An AI Game Judge that evaluates free-text user moves for "Rock-Paper-Scissors Plus" using **Google Gemini**. The judge classifies moves as **VALID**, **INVALID**, or **UNCLEAR**, explains why, and reports round results. Logic is driven by prompts; code keeps minimal state and glue only.

---

## Setup

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Get a Gemini API key** from [Google AI Studio](https://aistudio.google.com/apikey) (free tier).

3. **Set the API key**
   ```bash
   set GEMINI_API_KEY=your-key-here
   ```
   (Use `export GEMINI_API_KEY=...` on Linux/macOS.)

4. **Run the game**
   ```bash
   python main.py
   ```
   Enter moves as free text (e.g. `rock`, `paper`, `scissors`, `bomb`). Empty input quits.

---

## Deliverables

| File | Description |
|------|-------------|
| **prompts.txt** | System prompt + instruction prompt template for the AI Judge |
| **main.py** | Minimal glue: state, bot move, Gemini call, response parsing, I/O |
| **README.md** | This file — strategy, state, edge cases, improvements |

---

## Prompt Strategy

- **AI as strict judge**  
  The system prompt defines the model as an "AI Game Judge" that *strictly* evaluates the user’s move against the rules and current game state. It must not invent moves or ignore constraints.

- **Avoid guessing**  
  The prompt states: *"If unsure, choose UNCLEAR instead of guessing."* This pushes the model to prefer UNCLEAR for ambiguous or noisy input rather than guessing VALID/INVALID.

- **Handling ambiguity**  
  Rules explicitly say that ambiguous or unclear user input → **UNCLEAR**. The instruction template supplies the exact game state (round, scores, bomb usage) and the user’s raw input so the judge can reason about intent and clarity without hardcoded logic in code.

- **Constraints in the prompt**  
  Bomb-once-per-player, bomb beats everything, bomb vs bomb = draw, and “INVALID or UNCLEAR moves waste the turn” are all stated in the system prompt. The judge is instructed to enforce these via reasoning, not via regex or if/else in Python.

---

## State Management

- **Bomb tracking**  
  `game_state` keeps `user_bomb_used` and `bot_bomb_used`. The bot only chooses from `rock`/`paper`/`scissors` when its bomb is already used. After each round, the code checks the judge’s response: if the user’s interpreted move was `bomb` and status was VALID, it sets `user_bomb_used = True`; if the bot played bomb, it sets `bot_bomb_used = True`.

- **Score tracking**  
  Scores are updated from the judge’s reply: the code looks for "Round Result: User wins / Bot wins / Draw" and, when present, for "Updated Score:" with User/Bot numbers. The judge is the source of truth for who won the round and the resulting scores; the code only parses and applies those values.

- **Round number**  
  The current round is passed into the instruction template and incremented after each round so the next prompt has the correct round number.

---

## Edge Cases Handled

The prompts and minimal parsing are designed so the **AI Judge** handles these in language, not in code:

| Input / situation | Expected classification | How it’s handled |
|-------------------|-------------------------|-------------------|
| `rock` | VALID | Clear single move; judge accepts and applies rules. |
| `rok` | VALID (minor typo) | Prompt allows "Minor spelling errors may be accepted if clearly understandable." |
| `rock and paper` | UNCLEAR | Multiple moves in one input; judge should mark UNCLEAR and explain. |
| `bomb twice` | INVALID | Either invalid (not a single move) or bomb reuse; bomb-once rule in prompt. |
| `something sharp` | UNCLEAR | Vague; no clear mapping to rock/paper/scissors/bomb → UNCLEAR. |
| `💣` (emoji) | VALID if bomb unused | Judge can interpret as "bomb" when bomb not yet used. |
| Bomb already used | INVALID | State includes "User bomb used: True"; judge must reject. |
| Empty or nonsensical text | UNCLEAR / INVALID | "If unsure, choose UNCLEAR"; invalid/unclear wastes the turn per rules. |

The code does **not** implement win/loss or move-validation logic; it only updates bomb flags and scores from the judge’s structured text output.

---

## Future Improvements

- **Structured output (e.g. JSON)**  
  Use Gemini’s JSON/structured output so the judge returns a fixed schema (e.g. `move_status`, `round_result`, `user_score`, `bot_score`). That would make parsing reliable and avoid regex on free text.

- **Stronger intent understanding**  
  Optionally add a short instruction block with examples (e.g. "rok" → rock, "💣" → bomb) or a small set of allowed synonyms to improve consistency for typos and emojis.

- **Multi-game or session memory**  
  For multiple games or long sessions, persist minimal state (e.g. last N rounds, bomb usage, scores) and pass a short summary into the instruction so the judge can handle "rematch" or "new game" without starting from scratch in code.

- **Game-over condition**  
  The prompt asks for "Game Status: Continue / Game Over". The glue code could parse this and stop the loop or show a final result screen when the judge says Game Over.

---

## Summary

- **Prompts** in `prompts.txt` define the judge’s role, rules, and output format; they are the main place where logic and explainability live.  
- **Code** in `main.py` keeps minimal state, picks the bot move, calls Gemini with the system + instruction prompts, and parses the judge’s reply to update round, scores, and bomb usage.  
- No databases, no UI, no external APIs other than Gemini; no heavy game logic in code.
