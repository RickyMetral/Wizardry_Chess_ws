from gantry import ChessGantry
import sys
import os
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../chess_common_py/chess_common_py'))
from config import * 

def main():
    gantry = ChessGantry()

    try:
        # gantry.raise_z()
        # time.sleep(1)
        print("Testing X motor...")
        step_size = gantry.mm_to_step(SQUARE_SIZE_MM)
        for _ in range(0, 8):
            gantry.move_x(step_size, direction=False,  delay=GANTRY_SPEED)
            time.sleep(5)

        for _ in range(0, 8):
            print("Testing Y motor...")
            gantry.move_y(step_size, direction=False, delay=GANTRY_SPEED)
            time.sleep(5)
        # gantry.lower_z()
        # time.sleep(1)

    finally:
        gantry.close()
        print("Done")


if __name__ == '__main__':
    main()