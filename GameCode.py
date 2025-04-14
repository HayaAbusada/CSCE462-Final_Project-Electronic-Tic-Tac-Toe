import time
import board
import digitalio
import RPi.GPIO as GPIO
from adafruit_ssd1306 import SSD1306_I2C
from PIL import Image, ImageDraw, ImageFont

# Setup GPIO using BCM numbering
GPIO.setmode(GPIO.BCM)

# Pin map for the 3x3 grid (row, col) mapped to GPIO pins
sensor_pins = {
    (0, 0): 23,
    (1, 0): 20,
    (2, 0): 21,
    (0, 1): 25,
    (1, 1): 12,
    (2, 1): 26,
    (0, 2): 24,
    (1, 2): 16,
    (2, 2): 19,
}

# Configure all sensor pins as inputs with pull-down resistors
for pin in sensor_pins.values():
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

# Setup pushbutton pin
BUTTON_PIN = 6
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

# OLED display setup
oled_reset = digitalio.DigitalInOut(board.D4)
WIDTH, HEIGHT = 128, 32
i2c = board.I2C()
oled = SSD1306_I2C(WIDTH, HEIGHT, i2c, addr=0x3D, reset=oled_reset)

# Returns an empty 3x3 board
def generate_empty_board():
    return [[' ' for _ in range(3)] for _ in range(3)]

# Displays the current board state (and optional message) on the OLED
def display_board(board_state, message=""):
    image = Image.new('1', (oled.width, oled.height))
    draw = ImageDraw.Draw(image)
    for row in range(1, 3):
        draw.line((0, row * 10, WIDTH, row * 10), fill=255)
    for col in range(1, 3):
        draw.line((col * 42, 0, col * 42, HEIGHT), fill=255)
    font = ImageFont.load_default()
    for row in range(3):
        for col in range(3):
            piece = board_state[row][col]
            if piece != ' ':
                text_width, text_height = draw.textbbox((0, 0), piece, font=font)[2:]
                x_pos = col * 42 + (42 - text_width) // 2
                y_pos = row * 10 + (10 - text_height) // 2
                draw.text((x_pos, y_pos), piece, fill=255, font=font)
    if message:
        draw.text((0, HEIGHT - 10), message, fill=255, font=font)
    oled.image(image)
    oled.show()

# Displays winner message and current score
def display_winner_message(winner, x_wins, o_wins):
    image = Image.new('1', (oled.width, oled.height))
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    line1 = f"{winner}"
    line2 = f"X = {x_wins}    |    O = {o_wins}"
    text_width1, _ = draw.textbbox((0, 0), line1, font=font)[2:]
    text_width2, _ = draw.textbbox((0, 0), line2, font=font)[2:]
    draw.text(((WIDTH - text_width1) // 2, 5), line1, fill=255, font=font)
    draw.text(((WIDTH - text_width2) // 2, 18), line2, fill=255, font=font)
    oled.image(image)
    oled.show()

# Displays draw message with score
def display_draw_message(x_wins, o_wins):
    image = Image.new('1', (oled.width, oled.height))
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    line1 = "Draw!"
    line2 = f"X = {x_wins}    |    O = {o_wins}"
    text_width1, _ = draw.textbbox((0, 0), line1, font=font)[2:]
    text_width2, _ = draw.textbbox((0, 0), line2, font=font)[2:]
    draw.text(((WIDTH - text_width1) // 2, 5), line1, fill=255, font=font)
    draw.text(((WIDTH - text_width2) // 2, 18), line2, fill=255, font=font)
    oled.image(image)
    oled.show()

# Displays "NEW GAME" message
def display_new_game():
    image = Image.new('1', (oled.width, oled.height))
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    message = "NEW GAME"
    text_width, _ = draw.textbbox((0, 0), message, font=font)[2:]
    draw.text(((WIDTH - text_width) // 2, (HEIGHT - 8) // 2), message, fill=255, font=font)
    oled.image(image)
    oled.show()

# Waits for button press
def wait_for_button():
    while GPIO.input(BUTTON_PIN) == GPIO.LOW:
        time.sleep(0.1)
    while GPIO.input(BUTTON_PIN):
        time.sleep(0.1)

# Prompts user for best of 1, 3, or 5 rounds
def get_game_mode():
    display_new_game()
    while True:
        try:
            mode = int(input("Play best of (1, 3, 5): "))
            if mode in [1, 3, 5]:
                return mode
        except ValueError:
            continue

# Checks if a player has won the round
def check_winner(board):
    for i in range(3):
        if board[i][0] == board[i][1] == board[i][2] != ' ':
            return board[i][0]
        if board[0][i] == board[1][i] == board[2][i] != ' ':
            return board[0][i]
    if board[0][0] == board[1][1] == board[2][2] != ' ':
        return board[0][0]
    if board[0][2] == board[1][1] == board[2][0] != ' ':
        return board[0][2]
    return None

# Main game loop
try:
    while True:
        total_rounds = get_game_mode()
        max_rounds = total_rounds
        x_wins, o_wins, draws = 0, 0, 0
        round_count = 0
        wait_for_button()

        game_ended = False
        while not game_ended and round_count < max_rounds:
            board_state = generate_empty_board()
            display_board(board_state)
            current_player = 'X'
            moves = 0
            winner = None

            while moves < 9:
                if GPIO.input(BUTTON_PIN):
                    time.sleep(0.3)
                    if moves == 0:
                        game_ended = True
                        break
                    else:
                        board_state = generate_empty_board()
                        display_board(board_state)
                        current_player = 'X'
                        moves = 0
                        winner = None
                        continue

                move_made = False
                for pos, pin in sensor_pins.items():
                    if GPIO.input(pin) == GPIO.HIGH and board_state[pos[0]][pos[1]] == ' ':
                        board_state[pos[0]][pos[1]] = current_player
                        display_board(board_state)
                        winner = check_winner(board_state)
                        if winner:
                            if winner == 'X':
                                x_wins += 1
                            else:
                                o_wins += 1
                            display_winner_message(f"{winner} wins!", x_wins, o_wins)
                            wait_for_button()
                            break
                        current_player = 'O' if current_player == 'X' else 'X'
                        moves += 1
                        move_made = True
                        break

                if winner or moves == 9:
                    break
                time.sleep(0.1)

            if game_ended:
                break

            if not winner and moves == 9:
                draws += 1
                display_draw_message(x_wins, o_wins)
                wait_for_button()

            round_count += 1
            if x_wins > total_rounds // 2 or o_wins > total_rounds // 2:
                break

        if game_ended:
            continue

        if x_wins > o_wins:
            final_result = "X wins the match!"
        elif o_wins > x_wins:
            final_result = "O wins the match!"
        else:
            final_result = "Match is a draw!"

        display_winner_message(final_result, x_wins, o_wins)
        time.sleep(2)
        wait_for_button()

except KeyboardInterrupt:
    print("Interrupted by user.")

finally:
    GPIO.cleanup()

