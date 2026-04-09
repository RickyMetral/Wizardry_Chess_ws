from chess_common_py.config import SQUARE_SIZE
"""
CHESS BOARD COORDINATE MAP (Gantry View)
----------------------------------------
   [Y-AXIS / COLUMNS]
   -2   -1        a   b   c   d   e   f   g   h          9   10
  +---+---+      +---+---+---+---+---+---+---+---+     +---+---+ 
8 |   |   |      |   |   |   |   |   |   |   |   |     |   |   |  8
  +---+---+      +---+---+---+---+---+---+---+---+     +---+---+ 
7 |   |   |      |   |   |   |   |   |   |   |   |     |   |   |  7
  +---+---+      +---+---+---+---+---+---+---+---+     +---+---+ 
6 |   |   |      |   |   |   |   |   |   |   |   |     |   |   |  6
  +---+---+      +---+---+---+---+---+---+---+---+     +---+---+ 
5 |   |   |      |   |   |   |   |   |   |   |   |     |   |   |  5  [X-AXIS / ROWS]
  +---+---+      +---+---+---+---+---+---+---+---+     +---+---+ 
4 |   |   |      |   |   |   |   |   |   |   |   |     |   |   |  4
  +---+---+      +---+---+---+---+---+---+---+---+     +---+---+ 
3 |   |   |      |   |   |   |   |   |   |   |   |     |   |   |  3
  +---+---+      +---+---+---+---+---+---+---+---+     +---+---+ 
2 |   |   |      |   |   |   |   |   |   |   |   |     |   |   |  2
  +---+---+      +---+---+---+---+---+---+---+---+     +---+---+ 
1 |   |   |      |   |   |   |   |   |   |   |   |     |   |   |  1
  +---+---+      +---+---+---+---+---+---+---+---+     +---+---+ 
   -2   -1         a   b   c   d   e   f   g   h         9   10
    (0,0) Origin at a1

White graveyard are the i and j columns and the black graveyard are the z and y columns
"""
 
#A graveyard square on the board is represented as "x,y". Ex: "9,2"
class BoardCoords:
  def __init__(self):
    self.black_graveyard = {}
    self.white_graveyard = {}
    #Pieces to be inserted will use chess.(PieceType). Ex: chess.ROOK, chess.PAWN
    for col in [-2, -1]:
        for row in range(1, 9):
          square = f"{col},{row}"
          self.black_graveyard[square] = None

    for col in [9, 10]:
        for row in range(1, 9):
          square = f"{col},{row}"
          self.white_graveyard[square] = None

  def square_to_coords(self, sq: str) -> list[int]:
    coords = []
    sq = sq.split(",")

    if sq[0].isalpha():
        coords.append(ord(sq[0]) - ord('a') * SQUARE_SIZE)  
        coords.append(int(sq[1]) * SQUARE_SIZE)              
    else:
        coords.append(int(sq[0]) * SQUARE_SIZE)
        coords.append(int(sq[1]) * SQUARE_SIZE)

    return coords

  def coords_to_square(self, x: int, y: int) -> str:
    square = ""
    if x >= 9 or x <= -1:
        square = f"{x/SQUARE_SIZE},{y/SQUARE_SIZE}"          
    else:
        square = chr(x + ord('a')) + "," + str(y/SQUARE_SIZE)  #TODO Might have to round cuz of float accuracy loss
    return square