import os

#------Which Color is player?-------
PLAYER_COLOR = "w"

#-------Which bot to play against for Lichess--------
BOT_NAME = "maia5"

#------TOKENS---------
STOCKFISH_PATH = os.getenv("STOCKFISH_PATH")
LICHESS_TOKEN = os.getenv("LICHESS_TOKEN")

#------MOTOR MEASUREMENTS---------
GANTRY_SPEED = 0.01
BOARD_Z = 0
SIMULATE = False
SQUARE_SIZE_MM = 50       
MICROSTEP = 8
REV_STEPS = 200 * MICROSTEP
BELT_PITCH_MM = 2
PULLEY_TEETH = 20
MM_PER_REV = PULLEY_TEETH * BELT_PITCH_MM
MM_PER_STEP = MM_PER_REV / REV_STEPS

#------RPI PINS--------
X_STEP_PIN = 12
X_DIR_PIN = 16
X_EN_PIN = 22

Y_STEP_PIN = 6
Y_DIR_PIN = 26
Y_EN_PIN = 5

EM_PIN = 13

# Limit switch pins
X_MIN_PIN  = 17    # X axis minimum (home position)
X_MAX_PIN  = 18    # X axis maximum
Y_MIN_PIN  = 23    # Y axis minimum (home position)
Y_MAX_PIN  = 24    # Y axis maximum