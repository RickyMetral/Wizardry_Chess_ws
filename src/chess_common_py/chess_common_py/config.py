import os

#------Which Color is player?-------
PLAYER_COLOR = "w"

#-------Which bot to play against for Lichess--------
BOT_NAME = "maia5"

#------TOKENS AND PATHS---------
STOCKFISH_PATH = os.getenv("STOCKFISH_PATH")
LICHESS_TOKEN = os.getenv("LICHESS_TOKEN")
VOSK_PATH = "/home/ws/src/Wizardry_Chess_ws/vosk-model-small-en-us"

#------MOTOR MEASUREMENTS---------
GANTRY_SPEED = 0.00001
BOARD_Z = 0
SIMULATE = False
SQUARE_SIZE_MM = 73.025     
MICROSTEP = 8
REV_STEPS = 200 * MICROSTEP
BELT_PITCH_MM = 2
PULLEY_TEETH = 20
MM_PER_REV = PULLEY_TEETH * BELT_PITCH_MM
MM_PER_STEP = MM_PER_REV / REV_STEPS
MAX_COL = 10
MIN_COL = -3
MIN_ROW = 0
MAX_ROW = 8

#------RPI PINS--------
X_DIR_PIN = 13
X_STEP_PIN = 6 
X_EN_PIN = 5

Y_DIR_PIN = 17
Y_STEP_PIN = 27
Y_EN_PIN = 22

SERVO_PIN = 2
SERVO_DOWN_ANGLE = 45
SERVO_UP_ANGLE = 165


EM_PIN = 24

# Limit switch pins
X_MIN_PIN  = 12    # X axis minimum (home position)
X_MAX_PIN  = 25   # X axis maximum
Y_MIN_PIN  = 16    # Y axis minimum (home position)
Y_MAX_PIN  = 26    # Y axis maximum

VOICE_ACTIVATION_PIN = 23

#--------Config on whether or not to check limit switches--------
CHECK_BOUNDARIES = True