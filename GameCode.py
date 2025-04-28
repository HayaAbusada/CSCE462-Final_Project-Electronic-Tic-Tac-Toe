# Import necessary modules
import time                 # Time module to add delays
import board                # Board module to access standard Pi I2C/SPI pin names
import digitalio            # DigitalIO module for using GPIOs in CircuitPython style
import RPi.GPIO as GPIO      # Standard Raspberry Pi GPIO library
from adafruit_ssd1306 import SSD1306_I2C  # Library for controlling OLED screen over I2C
from PIL import Image, ImageDraw, ImageFont  # Libraries for creating images and drawing text/lines

# Setup GPIO mode
GPIO.setmode(GPIO.BCM)  # Use Broadcom pin numbering, not physical pin numbers

# Map Tic-Tac-Toe grid positions to GPIO pins for the FSR sensors
sensor_pins = {
    (0, 0): 21,  # Top left
    (1, 0): 26,  # Middle left
    (2, 0): 19,  # Bottom left
    (0, 1): 20,  # Top middle
    (1, 1): 12,  # Middle middle
    (2, 1): 16,  # Bottom middle
    (0, 2): 23,  # Top right
    (1, 2): 25,  # Middle right
    (2, 2): 24,  # Bottom right
}

# Configure each sensor pin as an input with an internal pull-down resistor
for pin in sensor_pins.values():
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

# Define pushbutton pin and configure it as input with pull-down resistor
BUTTON_PIN = 6
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

# OLED display setup
oled_reset = digitalio.DigitalInOut(board.D4)  # Reset pin for OLED
WIDTH, HEIGHT = 128, 32                        # OLED screen dimensions
i2c = board.I2C()                               # Initialize I2C bus
oled = SSD1306_I2C(WIDTH, HEIGHT, i2c, addr=0x3D, reset=oled_reset)  # Create OLED object

# ---- Functions ----

# Generate an empty 3x3 board with spaces
def generate_empty_board():
    return [[' ' for _ in range(3)] for _ in range(3)]

# Display the current board state (and optional message) on the OLED
def display_board(board_state, message=""):
    image = Image.new('1', (oled.width, oled.height))  # Create a blank image
    draw = ImageDraw.Draw(image)  # Create a drawing object
    for row in range(1, 3):  # Draw horizontal grid lines
        draw.line((0, row * 10, WIDTH, row * 10), fill=255)
    for col in range(1, 3):  # Draw vertical grid lines
        draw.line((col * 42, 0, col * 42, HEIGHT), fill=255)
    font = ImageFont.load_default()  # Load the default font
    for row in range(3):
        for col in range(3):
            piece = board_state[row][col]  # Get the piece at (row, col)
            if piece != ' ':  # Only draw if it's an 'X' or 'O'
                text_width, text_height = draw.textbbox((0, 0), piece, font=font)[2:]
                x_pos = col * 42 + (42 - text_width) // 2  # Center horizontally
                y_pos = row * 10 + (10 - text_height) // 2  # Center vertically
                draw.text((x_pos, y_pos), piece, fill=255, font=font)  # Draw the piece
    if message:  # Draw message if provided
        draw.text((0, HEIGHT - 10), message, fill=255, font=font)
    oled.image(image)  # Push the image to OLED memory
    oled.show()        # Display the image on screen

# Display winner message and updated scores
def display_winner_message(winner, x_wins, o_wins):
    image = Image.new('1', (oled.width, oled.height))  # Create new blank image
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    line1 = f"{winner}"  # Display who won (e.g., 'X wins!')
    line2 = f"X = {x_wins}    |    O = {o_wins}"  # Current score
    text_width1, _ = draw.textbbox((0, 0), line1, font=font)[2:]
    text_width2, _ = draw.textbbox((0, 0), line2, font=font)[2:]
    draw.text(((WIDTH - text_width1) // 2, 5), line1, fill=255, font=font)  # Center winner message
    draw.text(((WIDTH - text_width2) // 2, 18), line2, fill=255, font=font)  # Center score
    oled.image(image)
    oled.show()

# Display draw message and updated scores
def display_draw_message(x_wins, o_wins):
    image = Image.new('1', (oled.width, oled.height))
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    line1 = "Draw!"  # Display 'Draw!' message
    line2 = f"X = {x_wins}    |    O = {o_wins}"  # Show scores
    text_width1, _ = draw.textbbox((0, 0), line1, font=font)[2:]
    text_width2, _ = draw.textbbox((0, 0), line2, font=font)[2:]
    draw.text(((WIDTH - text_width1) // 2, 5), line1, fill=255, font=font)
    draw.text(((WIDTH - text_width2) // 2, 18), line2, fill=255, font=font)
    oled.image(image)
    oled.show()

# Display 'NEW GAME' message on the OLED
def display_new_game():
    image = Image.new('1', (oled.width, oled.height))
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    message = "NEW GAME"
    text_width, _ = draw.textbbox((0, 0), message, font=font)[2:]
    draw.text(((WIDTH - text_width) // 2, (HEIGHT - 8) // 2), message, fill=255, font=font)
    oled.image(image)
    oled.show()

# Wait until the button is pressed and released
def wait_for_button():
    while GPIO.input(BUTTON_PIN) == GPIO.LOW:  # Wait until button pressed
        time.sleep(0.1)  # Small delay to avoid CPU overuse
    while GPIO.input(BUTTON_PIN):  # Wait until button released
        time.sleep(0.1)

# Prompt the user via terminal to select match mode (1, 3, or 5 rounds)
def get_game_mode():
    display_new_game()  # Show NEW GAME screen
    while True:
        try:
            mode = int(input("Play best of (1, 3, 5): "))  # Ask user input
            if mode in [1, 3, 5]:  # Validate input
                return mode
        except ValueError:
            continue  # If invalid input, ask again

# Check if there's a winner on the board
def check_winner(board):
    for i in range(3):
        # Check horizontal wins
        if board[i][0] == board[i][1] == board[i][2] != ' ':
            return board[i][0]
        # Check vertical wins
        if board[0][i] == board[1][i] == board[2][i] != ' ':
            return board[0][i]
    # Check diagonal wins
    if board[0][0] == board[1][1] == board[2][2] != ' ':
        return board[0][0]
    if board[0][2] == board[1][1] == board[2][0] != ' ':
        return board[0][2]
    return None  # No winner found

# Main game loop
try:
    while True:  # Run the entire game indefinitely until user interrupts
        total_rounds = get_game_mode()  # Ask user how many rounds (1, 3, or 5)
        max_rounds = total_rounds  # Set maximum number of rounds allowed
        x_wins, o_wins, draws = 0, 0, 0  # Initialize score counters
        round_count = 0  # Initialize round counter
        wait_for_button()  # Wait for player to press button to start

        game_ended = False  # Flag to check if full game should end
        while not game_ended and round_count < max_rounds:  # Play until game ends or all rounds are played
            board_state = generate_empty_board()  # Reset the board to empty
            display_board(board_state)  # Display the empty board on OLED
            current_player = 'X'  # 'X' always goes first
            moves = 0  # Reset number of moves made
            winner = None  # No winner yet

            while moves < 9:  # Keep playing until board is full or a player wins
                if GPIO.input(BUTTON_PIN):  # Check if reset button was pressed
                    time.sleep(0.3)  # Debounce delay
                    if moves == 0:  # If no moves made yet, full game reset
                        game_ended = True
                        break
                    else:  # Otherwise just reset the board for the round
                        board_state = generate_empty_board()
                        display_board(board_state)
                        current_player = 'X'  # Reset to X's turn
                        moves = 0
                        winner = None
                        continue  # Restart round

                move_made = False  # Track if a move was made this loop
                for pos, pin in sensor_pins.items():  # Check each sensor (FSR) for activation
                    if GPIO.input(pin) == GPIO.HIGH and board_state[pos[0]][pos[1]] == ' ':
                        board_state[pos[0]][pos[1]] = current_player  # Place X or O on the board
                        display_board(board_state)  # Update OLED
                        winner = check_winner(board_state)  # Check if the move caused a win
                        if winner:  # If someone won:
                            if winner == 'X':
                                x_wins += 1  # Increment X's win counter
                            else:
                                o_wins += 1  # Increment O's win counter
                            display_winner_message(f"{winner} wins!", x_wins, o_wins)  # Show win screen
                            wait_for_button()  # Wait for button press before next round
                            break
                        current_player = 'O' if current_player == 'X' else 'X'  # Switch player
                        moves += 1  # Increase move count
                        move_made = True  # Mark that a move was made
                        break  # Break from sensor check loop

                if winner or moves == 9:  # End round if winner or board full
                    break
                time.sleep(0.1)  # Small delay to avoid CPU overuse

            if game_ended:
                break  # Exit full match loop if full reset triggered

            if not winner and moves == 9:  # If no winner and board full → it's a draw
                draws += 1
                display_draw_message(x_wins, o_wins)  # Show draw screen
                wait_for_button()  # Wait for button press before next round

            round_count += 1  # Increment round count
            if x_wins > total_rounds // 2 or o_wins > total_rounds // 2:  # If a player already won majority
                break

        if game_ended:
            continue  # Restart full game setup if reset triggered

        # After all rounds, determine final match winner
        if x_wins > o_wins:
            final_result = "X wins the match!"
        elif o_wins > x_wins:
            final_result = "O wins the match!"
        else:
            final_result = "Match is a draw!"

        display_winner_message(final_result, x_wins, o_wins)  # Show final match result
        time.sleep(2)  # Pause before resetting for new match
        wait_for_button()  # Wait for button press to start new match

except KeyboardInterrupt:  # Allow user to exit safely with Ctrl+C
    print("Interrupted by user.")

finally:
    GPIO.cleanup()  # Release GPIO pins before program exit


