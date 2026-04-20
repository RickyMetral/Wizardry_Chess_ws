"""
ROS2 Node that holds all the information regarding the chess board's state. Subscribes to the player_move topic to update the board state. 
Can be used to determine validiity of moves, potential moves, if the board is in check/mate, etc. 
"""
import rclpy
from rclpy.node import Node
from rclpy.executors import MultiThreadedExecutor
from chess_common_py.config import STOCKFISH_PATH 
from std_msgs.msg import String
from std_srvs.srv import Trigger
from chess_interfaces.srv import CheckMoveValid, GetSquarePiece
import chess 
import random
import chess.engine
from chess_common_py.config import SQUARE_SIZE_MM as SQUARE_SIZE

import chess

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
   -3  -2    -1     a   b   c   d   e   f   g   h   8   9   10
    (0,0) Origin at a1

White graveyard are the -3 and -2 columns and the black graveyard are the 0 and 10 columns
"""


class BoardState(Node):
    board = chess.Board()
    engine = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH)
    black_graveyard = {}
    white_graveyard = {}

    def __init__(self, use_ros = True):
        if use_ros:
            super().__init__("board_state_node")
            self.move_sub = self.create_subscription(String, "player_move", self.update_board_state, 10)
            self.check_move_valid_srv = self.create_service(CheckMoveValid, "check_move_valid", self._check_move_valid_callback)
            self.get_piece_square_srv = self.create_service(GetSquarePiece, "get_square_piece", self._get_square_piece_callback)
            self.reset_board_srv = self.create_service(Trigger, "reset_board", self.reset_board)
            self.get_logger().info("Started Board State Service")
        self.using_ros = use_ros

        #Pieces to be inserted will use chess.(PieceType). Ex: chess.ROOK, chess.PAWN
        for col in [-3, -2]:
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
        if x >= 10 or x <= -2:
            square = f"{x/SQUARE_SIZE},{y/SQUARE_SIZE}"          
        else:
            square = chr(round(x) + ord('a')) + "," + str(round(y/SQUARE_SIZE))  #TODO Might have to round cuz of float accuracy loss
        return square

    def gen_random_move(self)->str:
        return random.choice(list(self.board.legal_moves)).uci()

    #Gives centipawn score from whites perspective
    #To swich to perspectives just negate the returned score(Ex: white: 50, black: -50)
    def analyze_board(self, mate_score = 10000):
        return self.engine.analyse(self.board, chess.engine.Limit(time=0.1))["score"].white().score(mate_score=mate_score)

    def update_board_state(self, player_move):
        if self.using_ros:
            self.get_logger().info("Received Request to update board state callback")
        self.board.push_uci(player_move.data)

    #Takes in move in UCI format and parses to chess lib format
    def check_move_valid(self, player_move):
        try:
            move = chess.Move.from_uci(player_move)
            return self.board.is_legal(move)
        except chess.InvalidMoveError:
            return False

    def _check_move_valid_callback(self, request, response):
        self.get_logger().info("Received Request to check valid move callback")
        response.is_valid_move = self.check_move_valid(request.player_move)
        self.get_logger().info("Found move validity now")

        if not response.is_valid_move:
            response.is_check = False
            response.is_mate = False 
            return response

        move = chess.Move.from_uci(request.player_move)
        self.board.push(move)
        response.is_check = self.board.is_check()
        response.is_mate = self.board.is_checkmate()
        self.board.pop()

        return response

    #Expected to be in chess library enum format(Ex: the value of chess.A3)
    def get_square_piece(self, chess_square):
        return self.board.piece_at(chess_square) 

    def _get_square_piece_callback(self, request, response):
        self.get_logger().info("Received Request to get square piece callback")
        piece = self.get_square_piece(request.chess_square )

        if piece:
            response.is_occupied = True
            response.piece_type = piece.piece_type
        else:
            response.is_occupied = False
            response.piece_type = 255 #Max value to represent no piece

        return response

    def reset_board(self, request, response):
        self.board.reset()
        response.success = True
        response.message = "Board Reset"
        if self.using_ros:
            self.get_logger().info("Reset Board")
        return response

def main(args=None):
    rclpy.init()
    node  = BoardState()
    executor = MultiThreadedExecutor(num_threads=3)
    executor.add_node(node)
    try: 
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()