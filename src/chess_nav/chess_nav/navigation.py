import rclpy
import chess
from rclpy.node import Node

from collections import deque
 
from std_msgs.msg import String
 
from chess_interfaces.srv import GetSquarePiece
from chess_motor_schema.gantry import ChessGantry
from chess_board_state.board_state import BoardState
from chess_common_py.config import SQUARE_SIZE_MM as SQUARE_SIZE
from chess_common_py.config import MIN_COL, MAX_COL, MIN_ROW, MAX_ROW
 

class ChessNavNode(Node):
    board = BoardState(use_ros = False)

    def __init__(self):
        super().__init__("chess_nav_node")
        self.gantry = ChessGantry()
        self.gantry.home_all()
        self.move_sub = self.create_subscription(
            String, "player_move", self.on_player_move, 10
        )

        self.white_gv_col = MIN_COL
        self.white_gv_row = MIN_ROW 
        self.black_gv_col = MAX_COL - 1
        self.black_gv_row = MIN_ROW


    def on_player_move(self, msg):
        self.get_logger().info("Received player move, beginning navigation")
        uci = msg.data.strip()

        if uci == "end" or uci == "error":
            return
        if uci == "reset":
            self._reset_board()
            return
        try:
            move = chess.Move.from_uci(uci)
        except ValueError:
            self.get_logger().warn(f"Bad UCI received: {uci}")
        
        from_square = chess.square_name(move.from_square)
        to_square = chess.square_name(move.to_square)

        from_x, from_y = self.board.square_to_coords(from_square)
        to_x, to_y = self.board.square_to_coords(to_square)


        if self.is_occupied_square(to_square):
            captured_color = self._get_captured_piece_color(move)
            self.get_logger().info("Handling Captured Piece")
            self._handle_captured_piece(self._get_captured_piece_type(move), captured_color)

        self.get_logger().info(f"Moving piece from coordinates {from_x}, {from_y}")
        self.get_logger().info(f"Moving piece to coordinates {to_x}, {to_y}")
        self.get_logger().info(f"Moving piece from square {from_square}")
        self.get_logger().info(f"Moving piece to square {to_square}")
        self.board.update_board_state(msg)
        self._move_piece(from_x, from_y, to_x, to_y)

    def _move_piece(self, from_x: float, from_y: float, to_x, to_y) -> bool:
        #Use move to xy, then turn EM on and use navigate to xy, then turn EM off to move a piece
        if not self._move_to_xy(from_x, from_y):
            self.get_logger().info(f"Hit boundary moving to ({from_x}, {from_y})")
            return False

        self.gantry.magnet_on()
        self._navigate_to_xy(to_x, to_y)
        self.gantry.magnet_off()

        return True

    def _navigate_to_xy(self, x: float, y: float) -> bool:
        start_square = self.board.coords_to_square(self.gantry._gx, self.gantry._gy)
        end_square = self.board.coords_to_square(x, y)
        waypoints = self._bfs_path(start_square, end_square)

        if waypoints == None:
            self.get_logger().warn(f"Could not find path to square: {end_square}")
            return False

        for (dx, dy) in waypoints:
            self._move_to_xy(dx, dy)

        self.get_logger().info(f"Finished navigating to square: {end_square}")
        return True

    def _bfs_path(self, from_square: str, to_square: str):
        """ BFS on the 12x8 grid. Returns list of (col, row) waypoints excluding start.
        Treats occupied squares as obstacles (except the destination).
        """

        from_x, from_y = self.board.square_to_coords(from_square)
        to_x, to_y =    self.board.square_to_coords(to_square) 
        half = SQUARE_SIZE/2
        from_x, from_y = self.board.square_to_coords(from_square)

        if from_square == to_square:
            return []

        occupied = self._get_occupied_squares()
        start = (from_x, from_y)

        #Checks if a corner is in bounds
        def in_bounds(cx, cy):
            return (MIN_COL - half) <= cx <= (MAX_COL* SQUARE_SIZE + half) and \
                (MIN_COL - half) <= cy <= (MAX_ROW * SQUARE_SIZE + half)

        start_corners = [
            (from_x - half, from_y - half),
            (from_x + half, from_y - half),
            (from_x - half, from_y + half),
            (from_x + half, from_y + half),
        ]
        self.get_logger().info(f"Searching for path from {from_square} to {to_square}")
        for start_corner in start_corners:
            if not in_bounds(*start_corner):
                continue

            queue = deque()
            queue.append((start, [start]))
            visited = {from_square}
            while queue:
                (col, row), path = queue.popleft()

                for dc, dr in [(SQUARE_SIZE,0),(-SQUARE_SIZE,0),(0,SQUARE_SIZE),(0,-SQUARE_SIZE)]:
                    nc, nr = col + dc, row + dr
                    cur_sq = self.board.coords_to_square(nc, nr)

                    if not (MIN_COL <= nc <= MAX_COL and MIN_ROW <= nr <= MAX_ROW):
                        continue
                    if cur_sq in visited:
                        continue

                    # Don't allow passing through occupied squares or the destination
                    if cur_sq in occupied and cur_sq != to_square:
                        continue

                    new_path = path + [(nc, nr)]
                    if abs(to_x - nc) < SQUARE_SIZE and abs(to_y - nr) < SQUARE_SIZE:
                        return [start_corner] + new_path[1:] + [(to_x, to_y)]

                    visited.add(cur_sq)
                    queue.append(((nc, nr), new_path))

            return None  

    #Moves to coords directly, does not plan path
    def _move_to_xy(self, x: float, y: float) -> bool:
        dist_x = self.gantry._gx - x
        dist_y = self.gantry._gy - y
        steps_x = self.gantry.mm_to_step(abs(dist_x))
        steps_y = self.gantry.mm_to_step(abs(dist_y))

        if steps_x != self.gantry.move_x(steps_x, True if dist_x < 0 else False):
            self.get_logger().info("Hit boundary in x")
            return False

        if steps_y != self.gantry.move_y(steps_y, False if dist_y < 0 else True):
            self.get_logger().info("Hit boundary in y")
            return False

        return True

    def _get_captured_piece_color(self, move: chess.Move):
        """Returns the chess.Piecetype of the piece on the square requested. Returns 255 if not occupied"""
        piece = self.board.get_square_piece(move.to_square)

        if not piece:
            return False
        if piece.color == chess.WHITE:
            return "white"
        else:
            return "black"

    def _get_captured_piece_type(self, move: chess.Move):
        """Returns the chess.Piecetype of the piece on the square requested. Returns 255 if not occupied"""
        piece = self.board.get_square_piece(move.to_square)

        if piece:
         return piece.piece_type
        else:
            return 255

    def is_occupied_square(self, square: chess.SQUARES):
        return self.board.get_square_piece(square) is not None

    #Color is the color of the piece being captured
    def _handle_captured_piece(self, captured_piece, color) -> str:
        if color == "white" or color == "w":
            x, y = self.board.square_to_coords()
        elif color == "black" or color == "b":
            x, y = self.board.square_to_coords()
        else:
            self.get_logger().error("Invalid color for captured piece. Cannot move to graveyard")
            return False

        return [x, y]
    

    def _get_occupied_squares(self):
        occupied = set()

        for square in chess.SQUARES:
            if self.is_occupied_square(square):
                occupied.add(chess.square_name(square))
        return occupied
            

    def _reset_board(self):
        return None
    
    def destroy_node(self):
        self.gantry.close()
        super().destroy_node()
        
def main(args=None):
    rclpy.init(args=args)
    node = ChessNavNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()