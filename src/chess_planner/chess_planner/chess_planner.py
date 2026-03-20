"""
The central node from which everything is orchestrated. Handles the turns of the players.
Receives player moves from player_input_node, publishes those moves to player_move topic.
Also manages the player loyalty and overwrites input moves when necessary.
"""
import rclpy
import chess
from rclpy.node import Node
from std_msgs.msg import String
from std_srvs.srv import Trigger
from chess_interfaces.srv import PlayerInput
from chess_interfaces.srv import GetSquarePiece 
from chess_board_state.board_state import BoardState
from chess_common_py.lichess_api import LichessApi
from chess.engine import Cp, Mate, MateGiven

class ChessPlanner(Node):
    black_loyalty = 100
    white_loyalty = 100
    white_cp_score = 0
    black_cp_score = 0
    black_turn = False
    white_turn = True
    player_color = None
    move_count = 0

    def __init__(self):
        super().__init__("chess_planner_node")
        self.move_pub = self.create_publisher(String, "player_move", 10)#TODO Create a message that also includes player color in the message
        self.player_input_cli = self.create_client(PlayerInput, "player_input")
        self.get_piece_square_cli = self.create_client(GetSquarePiece, "get_square_piece")
        self.reset_board_trigger = self.create_client(Trigger, "reset_board")
        self.board = BoardState(use_ros = False)

        if not self.player_input_cli.wait_for_service(timeout_sec=2.0):
            self.get_logger().error("Could not find Player input service. Shutting down...")
            raise SystemExit
        if not self.reset_board_trigger.wait_for_service(timeout_sec=2.0):
            self.get_logger().error("Could not find reset board trigger. Shutting down...")
            raise SystemExit
        if not self.get_piece_square_cli.wait_for_service(timeout_sec=2.0):
            self.get_logger().error("Could not find get piece square service. Shutting down...")
            raise SystemExit

    #Request a move from specified player color
    def request_player_input(self, player_color: str, game_id: str, move_count: int):
        req = PlayerInput.Request()
        req.player_color = player_color
        req.game_id = game_id
        req.move_count = move_count
        future = self.player_input_cli.call_async(req)
        rclpy.spin_until_future_complete(self, future)
        return future.result()

    #Request to reset the board state 
    def reset_board_req(self):
        req = Trigger.Request()
        future = self.reset_board_trigger.call_async(req)
        rclpy.spin_until_future_complete(self, future, timeout_sec=3.0)
        return future.result()
    
    def switch_turns(self):
        #If its currently blacks turn 
        if self.black_turn:
            self.black_turn = False
            self.white_turn = True

        #If its currently whites turn 
        else:
            self.black_turn = True 
            self.white_turn = False 

    def set_player_color(self, player_color):
        ChessPlanner.player_color = player_color
    
    def get_square_piece_req(self, chess_square):
        #If square input is a string, convert it to the enum for chess lib
        if isinstance(chess_square, str):
            try:
                chess_square = chess.parse_square(chess_square)
            except ValueError:
                self.get_logger().info("Could not parse chess square name")
                raise SystemExit
        req = GetSquarePiece.Request()
        req.chess_square = chess_square
        future = self.get_piece_square_cli.call_async(req)
        rclpy.spin_until_future_complete(self, future, timeout_sec=3.0)
        return future.result()

    def get_square_piece(self, chess_square):
        future = self.get_square_piece_req(chess_square)
        if future.is_occupied:
            return future.piece_type
        else:
            return 255 #255 is square is not occupied

    def update_white_loyalty(self, loyalty_multiplier: int):
        score = self.board.analyze_board()
        score_diff = score - self.white_cp_score
        self.white_loyalty += score_diff * loyalty_multiplier
        self.white_loyalty = max(0, min(100, self.white_loyalty))  
        self.white_cp_score = score  

    def update_black_loyalty(self, loyalty_multiplier: int):
        score = self.board.analyze_board()
        score_diff = score - self.black_cp_score
        self.black_loyalty += score_diff * loyalty_multiplier
        self.black_loyalty = max(0, min(100, self.black_loyalty))  
        self.black_cp_score = score  

    def handle_white_turn(self, lichess: LichessApi):
        player_move = self.request_player_input("w", lichess._game_id, self.move_count)
        if not player_move or player_move == "end" or player_move == "error":
            return False
        self.update_white_loyalty(0.5)
        self.get_logger().debug(f"Received move from White: {player_move.move}")
        if self.white_loyalty < 20:
            player_move.move = self.board.gen_random_move()
            self.get_logger().debug(f"Loyalty too Low! Overwrote white move: {player_move.move}")

        # lichess.make_move(player_move.move)
        self.move_count += 1
        msg = String()
        msg.data = player_move.move
        self.move_pub.publish(msg)#Publishes move to player_move topic
        self.switch_turns()
        return True

    def handle_black_turn(self, lichess: LichessApi):
        player_move = self.request_player_input("b", lichess._game_id, self.move_count)
        if player_move.move == "end" or player_move == "error":
            return False
        self.update_black_loyalty(.5)
        self.get_logger().debug(f"Received move from Black: {player_move.move}")
        if self.black_loyalty < 20:
            player_move.move = self.board.gen_random_move()
            self.get_logger().debug(f"Loyalty too Low! Overwrote black move: {player_move.move}")
        # lichess.make_move(player_move.move)
        self.move_count += 1
        msg = String()
        msg.data = player_move.move
        self.move_pub.publish(msg)#Publishes move to player_move topic
        self.switch_turns()
        return True

def main():
    rclpy.init()
    try:
        planner = ChessPlanner()
        lichess = LichessApi(planner.get_logger())
        if not lichess.start_game():
            raise SystemExit
            
        planner.set_player_color(lichess._player_color)

        while True:
            if planner.white_turn:
                planner.get_logger().info(f"White Loyalty: {planner.white_loyalty}")
                planner.get_logger().debug("Requesting white move")
                if not planner.handle_white_turn(lichess):
                    planner.get_logger().info("Game is over")
                    break

            elif planner.black_turn:
                planner.get_logger().info(f"Black Loyalty: {planner.black_loyalty}")
                planner.get_logger().debug("Requesting black move")
                if not planner.handle_black_turn(lichess):
                    planner.get_logger().info("Game is over")
                    break

        
        planner.reset_board_req()
        planner.destroy_node()

    except (SystemExit, KeyboardInterrupt):
        if lichess:
            lichess.resign_game()
        
    finally:
        if planner:
            planner.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()