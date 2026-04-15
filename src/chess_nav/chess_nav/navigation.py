import rclpy
import chess
from rclpy.node import Node
from rclpy.action import ActionClient

from collections import deque
 
from std_msgs.msg import String
 
from chess_interfaces.srv import GetSquarePiece
from chess_motor_schema.gantry import ChessGantry
from chess_board_state.board_state import BoardState
 

class ChessNavNode(Node):
    board = BoardState(use_ros = False)

    def __init__(self):
        super().__init__("chess_nav_node")
        self.gantry = ChessGantry()
        self.get_piece_cli = self.create_client(GetSquarePiece, "get_square_piece")
        if not self.get_piece_cli.wait_for_service(timeout_sec=5.0):
            self.get_logger().error("get_square_piece not available")
            raise SystemExit
        self.move_sub = self.create_subscription(
            String, "player_move", self.on_player_move, 10
        )

        self.white_gv_col = 9
        self.white_gv_row = 1
        self.black_gv_col = -1
        self.black_gv_row = 1


    def on_player_move(self, msg):
        self.board.update_board_state(msg)
        uci = msg.data.strip()

        if uci == "end" or uci == "error":
            return
        if uci == "reset":
            self._reset_board()
            pass
        try:
            move = chess.Move.from_uci(uci)
        except ValueError:
            self.get_logger().warn(f"Bad UCI received: {uci}")

        from_x, from_y = self.board.sqaure_to_coords(move.from_square)
        to_x, to_y = self.board.sqaure_to_coords(move.to_square)

        captured_piece = self._is_capture(move)
        if captured_piece is not None:
            self.handle_captured_piece(captured_piece, move)

        self._move_piece(from_x, from_y, to_x, to_y)

    def _move_piece(self, from_x: float, from_y: float, to_x, to_y) -> bool:
        #TODO Use move to xy, then turn EM on and use navigate to xy, then turn EM off to move a piece
        if not self._move_to_xy(from_x, from_y):
            self.get_logger().info(f"Something went wrong moving to ({from_x}, {from_y})")
            return False

        self.gantry.magnet_on()
        self._navigate_to_xy(to_x, to_y)
        self.gantry.magnet_off()

        return True

    def _navigate_to_xy(self, x: float, y: float) -> bool:
        #TODO Implement navigating to a coordinate
        pass

    def _bfs_path(self, from_col, from_row, to_col, to_row):
        """ BFS on the 12x8 grid. Returns list of (col, row) waypoints excluding start.
        Treats occupied squares as obstacles (except the destination).
        """
        start = (from_col, from_row)
        goal = (to_col, to_row)

        if start == goal:
            return []

        occupied = self._get_occupied_squares()

        queue = deque()
        queue.append((start, [start]))
        visited = {start}

        while queue:
            (col, row), path = queue.popleft()

            for dc, dr in [(1,0),(-1,0),(0,1),(0,-1)]:
                nc, nr = col + dc, row + dr

                if not (-2 <= nc <= 9 and -2 <= nr <= 9):
                    continue
                if (nc, nr) in visited:
                    continue
                # Don't allow passing through empty squares or the destination
                if (nc, nr) in occupied and (nc, nr) != goal:
                    continue

                new_path = path + (nc, nr)
                if (nc, nr) == goal:
                    return new_path[1:]  

                visited.add((nc, nr))
                queue.append(((nc, nr), new_path))

        return None  

    #Moves to coords directly, does not plan path
    def _move_to_xy(self, x: float, y: float) -> bool:
        dist_x = self.gantry._gx - x
        dist_y = self.gantry._gy - y
        steps_x = self.gantry.mm_to_step(dist_x)
        steps_y = self.gantry.mm_to_step(dist_y)

        if steps_x != self.gantry.move_x(steps_x, True if dist_x < 0 else False):
            return False

        if steps_y != self.gantry.move_y(steps_y, False if dist_y < 0 else True):
            return False

        return True

    def _is_capture(self, move: chess.Move):
        """Returns the chess.Piecetype of the piece on the square requested. Returns 255 if not occupied"""
        piece = self.board.get_square_piece(move.to_square)

        if piece:
         return piece.piece_type
        else:
            return 255

    def is_occupied_square(self, square: chess.SQUARE):
        return False if self.board.get_piece_square(square) == 255 else True

    #Color is the color of the piece being captured
    def _handle_captured_piece(self, captured_piece, color) -> str:
        if color == "white" or color == "w":
            x, y = self.board.square_to_coords()
        elif color == "black" or color == "b":
            x, y = self.board.square_to_coords()
        else:
            self.get_logger().error("Invalid color for captured piece. Cannot move to graveyard")

        return [x, y]
    

    def _get_occupied_squares(self):
        occupied = set()

        for square in chess.SQUARES:
            if self.is_occupied_square(square):
                col = chess.square_name(square)[1]
                row = chess.square_name(square)[0]
                occupied.add((col,row))
            

    def _reset_board(self):
        return None
    

