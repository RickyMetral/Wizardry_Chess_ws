import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from std_srvs.srv import Trigger
from chess_common_py.config import LICHESS_TOKEN

class ChessPlanner(Node):
    black_loyalty = 100
    white_loyalty = 100
    black_turn = False
    white_turn = True

    def __init__(self):
        super().__init__("chess_planner_node")
        self.move_pub = self.create_publisher(String, "player_move", 10)#TODO Create a message that also includes player color in the message
        self.player_input_cli = self.create_client(Trigger, "player_input")

        if not self.player_input_cli.wait_for_service(timeout_sec=2.0):
            self.get_logger().error("Could not find Player input service. Shutting down...")
            raise SystemExit

    def request_player_input(self):
        future = self.send_request()
        rclpy.spin_until_future_complete(self, future)
        return future.result()

    def send_request(self):
        req = Trigger.Request()
        return self.player_input_cli.call_async(req)

def main():
    rclpy.init()
    try:
        planner = ChessPlanner()
        #TODO Add logic for game here
        planner.destroy_node()
        rclpy.shutdown()
    except SystemExit:
        rclpy.shutdown()



if __name__ == '__main__':
    main()