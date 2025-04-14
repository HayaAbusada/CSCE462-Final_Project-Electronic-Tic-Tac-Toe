**GAME INSTRUCTIONS**

Connect Bread Board to Raspberry Pi and ssh Group1@pi.local - enter password

**Run the Game:**
   ```
   python3 GameCode.py
   ```

**Choose match length:**
   - When prompted, enter `1`, `3`, or `5` (for best of 1/3/5 rounds).

**Start match:**
   - Press the button once when you see “NEW GAME” on the display.

**Gameplay:**
   - Player X goes first.
   - Press down on a grid cell (FSR) by placing game piece to place an X or O.
   - Turns alternate automatically.
   - After every valid move, the OLED display updates.
   - At the end of every round clear pieces and press button to start next round

**Winning:**
   - A player wins a round by getting 3 in a row.
   - Score is shown after every round.

**Resets:**
   - **Press button once mid-round** → Board resets (clears pieces, round restarts).
   - **Press button twice with empty board** → Game fully resets and prompts for new match setup.

**Match end:**
   - Match ends when one player wins majority OR max rounds reached.
   - If X and O have same wins after all rounds, it’s a draw.
   - Final result is displayed.
   - Press button once to start a new match.
