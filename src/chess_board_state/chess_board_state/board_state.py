"""
ROS2 Node that holds all the information regarding the chess board's state. Subscribes to the player_move topic to update the board state. 
Can be used to determine validiity of moves, potential moves, if the board is in check/mate, etc. 
"""
import rclpy
from rclpy.node import Node
from rclpy.executors import MultiThreadedExecutor
from std_msgs.msg import String
from std_srvs.srv import Trigger
from chess_interfaces.srv import CheckMoveValid, GetPieceSquare
import chess 


class BoardState(Node):
    def __init__(self):
        super().__init__("board_state_node")
        self.move_sub = self.create_subscription(String, "player_move", self.update_board_state,10)
        self.check_move_valid_srv = self.create_service(CheckMoveValid, "check_valid_move", self.check_move_valid_callback)
        self.get_piece_square_srv = self.create_service(GetPieceSquare, "get_piece_square", self.get_piece_square_callback)
        self.reset_board_srv = self.create_service(Trigger, "reset_board", self.reset_board)
        self.get_logger().info("Started Board State Service")

        self.board = chess.Board()
    
    #TODO Create callback that returns the location of a specified piece

    def update_board_state(self, player_move):
        self.get_logger().info("Received Request to update board state callback")
        #TODO If piece is captured, keep track of it so we can have a callback asking for its location
        self.board.push_uci(player_move.data)


    def check_move_valid_callback(self, request, response):
        self.get_logger().info("Received Request to check valid move callback")
        move = chess.Move.from_uci(request.player_move)
        response.is_valid_move = self.board.is_legal(move)

        if response.is_valid_move:
            self.board.push(move)
        
        response.is_check = self.board.is_check()
        response.is_mate = self.board.is_checkmate()

        self.board.pop()

        return response
    
    def get_piece_square_callback(self, request, response):
        self.get_logger().info("Received Request to get piece square callback")
        piece = self.board.piece_at(request.chess_square)

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
        self.get_logger().info("Reset Board")

def main(args=None):
    rclpy.init()
    node  = BoardState()
    executor = MultiThreadedExecutor(num_threads=2)
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