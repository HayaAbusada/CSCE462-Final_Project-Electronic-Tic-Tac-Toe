import time
import board
import digitalio
import RPi.GPIO as GPIO
from adafruit_ssd1306 import SSD1306_I2C
from PIL import Image, ImageDraw, ImageFont

# Setup GPIO using BCM numbering
GPIO.setmode(GPIO.BCM)

# Pin map for the 3x3 grid
sensor_pins = {
    (0, 0): 23,  # Top Left
    (1, 0): 20,  # Middle Left
    (2, 0): 21,  # Bottom Left
    (0, 1): 25,  # Top Middle
    (1, 1): 12,  # Center
    (2, 1): 26,  # Bottom Middle
    (0, 2): 24,  # Top Right
    (1, 2): 16,  # Middle Right
    (2, 2): 19,  # Bottom Right
}

# Setup all sensor pins as inputs with pull-down resistors
for pin in sensor_pins.values():
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

# Button pin to start and interrupt game
BUTTON_PIN = 6
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

# OLED display setup
oled_reset = digitalio.DigitalInOut(board.D4)
WIDTH, HEIGHT = 128, 32
i2c = board.I2C()
oled = SSD1306_I2C(WIDTH, HEIGHT, i2c, addr=0x3D, reset=oled_reset)

# Helper function to generate empty 3x3 board
def generate_empty_board():
    return [[' ' for _ in range(3)] for _ in range(3)]

# Display the current board state on OLED
def display_board(board_state):
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
                text_width, text_height = draw.textsize(piece, font=font)
                x_pos = col * 42 + (42 - text_width) // 2
                y_pos = row * 10 + (10 - text_height) // 2
                draw.text((x_pos, y_pos), piece, fill=255, font=font)

    oled.image(image)
    oled.show()

# Check if any player has won
def check_winner(board):
#need to complete

# Wait for button press
def wait_for_button():
    while GPIO.input(BUTTON_PIN) == GPIO.LOW:
        time.sleep(0.1)

# Wait for any sensor press and return the corresponding position
def wait_for_sensor(board):
    while True:
        if GPIO.input(BUTTON_PIN) == GPIO.HIGH:
            return 'RESET', None
        for pos, pin in sensor_pins.items():
            if GPIO.input(pin) == GPIO.HIGH and board[pos[0]][pos[1]] == ' ':
                time.sleep(0.2)  # debounce
                return 'OK', pos
        time.sleep(0.1)

# Ask user for best of 1, 3, or 5
def get_game_mode():
    while True:
        try:
            mode = int(input("Play best of (1, 3, 5): "))
            if mode in [1, 3, 5]:
                return mode
        except ValueError:
            continue

# Main game loop
try:


except KeyboardInterrupt:
    print("Interrupted by user.")

finally:
    GPIO.cleanup()
