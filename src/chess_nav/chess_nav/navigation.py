import math
import time
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from chess_common_py.config import SQUARE_SIZE, BOARD_Z
 
from std_msgs.msg import String, Bool
from sensor_msgs.msg import JointState
from nav_msgs.msg import Odometry
from geometry_msgs.msg import PoseStamped, Quaternion, Twist
 
from action_msgs.msg import GoalStatus
from chess_interfaces.srv import GetSquarePiece
from chess_nav.board_coords import BoardCoords 

import chess


class ChessNavNode(Node):
    def __init__(self):

        super().__init__("chess_nav_node")

        self.get_logger().info("Waiting for Nav2 navigate_to_pose action server…")
        self.get_logger().info("Nav2 connected")

        self.get_piece_cli = self.create_client(GetSquarePiece, "get_square_piece")
        if not self.get_piece_cli.wait_for_service(timeout_sec=5.0):
            self.get_logger().error("get_square_piece not available")
            raise SystemExit
        
        self.move_sub = self.create_subscription(
            String, "player_move", self.on_player_move, 10
        )

        self._gx = 0
        self._gy = 0
        self._gz = BOARD_Z
        self._EM_ON = False

        self.white_gv_col = 9
        self.white_gv_row = 1
        self.black_gv_col = -1
        self.black_gv_row = 1


    def on_player_move(self, msg):
        uci = msg.data.strip()

        if uci == "end" or uci == "error":
            return
        if uci == "reset":
            #TODO: Adda way to reset the board
            pass
        
        try:
            move = chess.Move.from_uci(uci)
        except ValueError:
            self.get_logger().warn(f"Bad UCI received: {uci}")

        from_x, from_y = BoardCoords.sqaure_to_coords(move.from_square)
        to_x, to_y = BoardCoords.sqaure_to_coords(move.to_square)

        captured_piece = self._is_capture(move)
        if captured_piece is not None:
            self.handle_captured_piece(captured_piece, move)
        
        self._move_piece(from_x, from_y, to_x, to_y)

    def _move_piece(self, from_x: float, from_y: float, to_x, to_y) -> bool:
        #TODO Use move to xy, then turn EM on and use navigate to xy, then turn EM off to move a piece
        pass

    def _navigate_to_xy(self, x: float, y: float) -> bool:
        #TODO Implement navigating to a coordinate
        pass
    
    #Moves to coords directly, does not plan path
    def _move_to_xy(self, x: float, y: float) -> bool:
        #TODO Implement navigating to a coordinate
        pass

    def _is_capture(self, move: chess.Move):
        """Returns the chess.Piecetype of the piece on the square requested. Returns 255 if not occupied"""
        req = GetSquarePiece.Request()
        req.chess_square = move
        future = self.get_piece_cli.call_async(req)
        rclpy.spin_until_future_complete(self, future, timeout_sec=3.0)
        return future.piece_type

    #Color is the color of the piece being captured
    def _handle_captured_piece(self, captured_piece, color) -> str:
        if color == "white" or color == "w":
            x, y = BoardCoords.square_to_coords()
        elif color == "black" or color == "b":
            x, y = BoardCoords.square_to_coords()
        else:
            self.get_logger().error("Invalid color for captured piece. Cannot move to graveyard")

        return [x, y]
    
    def _reset_board(self):
        return None
    
    def _nav_feedback_cb(self):
        return None