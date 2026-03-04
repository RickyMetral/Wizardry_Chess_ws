"""
The central node from which everything is orchestrated. Handles the turns of the players.
Receives player moves from player_input_node, publishes those moves to player_move topic.
Also manages the player loyalty and overwrites input moves when necessary.
"""
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from std_srvs.srv import Trigger
from chess_interfaces.srv import PlayerInput
from chess_interfaces.srv import CheckMoveValid, GetPieceSquare
from chess_common_py.lichess_api import LichessApi

#TODO Add the rest of the client calls for check move and get piece

class ChessPlanner(Node):
    black_loyalty = 100
    white_loyalty = 100
    black_turn = False
    white_turn = True
    player_color = None
    move_count = 0

    def __init__(self):
        super().__init__("chess_planner_node")
        self.move_pub = self.create_publisher(String, "player_move", 10)#TODO Create a message that also includes player color in the message
        self.player_input_cli = self.create_client(PlayerInput, "player_input")
        self.check_move_valid_cli = self.create_client(CheckMoveValid, "check_valid_move")
        self.get_piece_square_cli = self.create_client(GetPieceSquare, "get_piece_square")
        self.reset_board_trigger = self.create_client(Trigger, "reset_board")

        if not self.player_input_cli.wait_for_service(timeout_sec=2.0):
            self.get_logger().error("Could not find Player input service. Shutting down...")
            raise SystemExit
        if not self.check_move_valid_cli.wait_for_service(timeout_sec=2.0):
            self.get_logger().error("Could not find check move service. Shutting down...")
            raise SystemExit
        if not self.get_piece_square_cli.wait_for_service(timeout_sec=2.0):
            self.get_logger().error("Could not find get piece square service. Shutting down...")
            raise SystemExit
        if not self.reset_board_trigger.wait_for_service(timeout_sec=2.0):
            self.get_logger().error("Could not find reset board trigger. Shutting down...")
            raise SystemExit

    #Request a move from specified player color
    def request_player_input(self, player_color: str, game_id: str, move_count: int):
        future = self.send_input_request(player_color, game_id, move_count)
        rclpy.spin_until_future_complete(self, future)
        return future.result()

    #Send either 'w' or 'b' for white or black
    def send_input_request(self, player_color: str, game_id: str, move_count: int):
        req = PlayerInput.Request()
        req.player_color = player_color
        req.game_id = game_id
        req.move_count = move_count
        return self.player_input_cli.call_async(req)
    
    def reset_board(self):
        req = Trigger.Request()
        future = self.reset_board_trigger.call_async(req)
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
    
    def handle_white_turn(self, lichess: LichessApi):
        player_move = self.request_player_input("w", lichess._game_id, self.move_count)
        if player_move.move == "end" or player_move == "error":
            return False
        # TODO Rate move
        # TODO Update Loyalty
        # TODO If loyalty too low, make a different move
        self.get_logger().debug(f"Received move from White: {player_move.move}")
        lichess.make_move(player_move.move)
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
        # TODO Rate move
        # TODO Update Loyalty
        # TODO If loyalty too low, make a different move
        self.get_logger().debug(f"Received move from Black: {player_move.move}")
        lichess.make_move(player_move.move)
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
                planner.get_logger().debug("Requesting white move")
                if not planner.handle_white_turn(lichess):
                    planner.get_logger().info("Game is over")
                    break

            elif planner.black_turn:
                planner.get_logger().debug("Requesting black move")
                if not planner.handle_black_turn(lichess):
                    planner.get_logger().info("Game is over")
                    break

        
        planner.reset_board()
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