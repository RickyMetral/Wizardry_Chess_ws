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


class BoardState(Node):
    board = chess.Board()
    engine = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH)

    def __init__(self, use_ros = True):
        if use_ros:
            super().__init__("board_state_node")
            self.move_sub = self.create_subscription(String, "player_move", self.update_board_state, 10)
            self.check_move_valid_srv = self.create_service(CheckMoveValid, "check_move_valid", self._check_move_valid_callback)
            self.get_piece_square_srv = self.create_service(GetSquarePiece, "get_square_piece", self._get_square_piece_callback)
            self.reset_board_srv = self.create_service(Trigger, "reset_board", self.reset_board)
            self.get_logger().info("Started Board State Service")
        self.using_ros = use_ros

    #TODO Create callback that returns the location of a specified piece

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
        move = chess.Move.from_uci(player_move)
        return self.board.is_legal(move)

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