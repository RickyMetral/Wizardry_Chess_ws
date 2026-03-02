import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from chess_interfaces.srv import PlayerInput
from chess_common_py.lichess_api import LichessApi


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

        if not self.player_input_cli.wait_for_service(timeout_sec=2.0):
            self.get_logger().error("Could not find Player input service. Shutting down...")
            raise SystemExit

    #Request a move from specified player color
    def request_player_input(self, player_color: str, game_id: str, move_count: int):
        future = self.send_request(player_color, game_id, move_count)
        rclpy.spin_until_future_complete(self, future)
        return future.result()

    #Send either 'w' or 'b' for white or black
    def send_request(self, player_color: str, game_id: str, move_count: int):
        req = PlayerInput.Request()
        req.player_color = player_color
        req.game_id = game_id
        req.move_count = move_count
        return self.player_input_cli.call_async(req)
    
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
        # TODO Publish move to nav
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
        
        # TODO Publish move to nav
        self.switch_turns()
        return True

def main():
    rclpy.init()
    try:
        planner = ChessPlanner()
        lichess = LichessApi()
        lichess.start_game()
        planner.set_player_color(lichess._player_color)

        while True:
            if planner.white_turn:
                planner.get_logger().debug("Requesting white move")
                if not planner.handle_white_turn(lichess):
                    print("Game is over")
                    break

            elif planner.black_turn:
                planner.get_logger().debug("Requesting black move")
                if not planner.handle_black_turn(lichess):
                    print("Game is over!")
                    break


        planner.destroy_node()
        rclpy.shutdown()
    except (SystemExit, KeyboardInterrupt):
        lichess.resign_game()
        rclpy.shutdown()



if __name__ == '__main__':
    main()