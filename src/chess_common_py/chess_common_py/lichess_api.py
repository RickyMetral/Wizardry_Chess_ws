"""
This file is where all Lichess api wrappers will be written. Check out https://lichess.org/api#description/introduction for docs on the entire api.
Everything will be wrapped under the lichess class and be called as methods of said class. 
 """
import requests
from chess_common_py.config import LICHESS_TOKEN

class LichessApi:
    bot_username = "maia9"
    _game_id = None
    _player_color = None

    #Expects Ros logger object
    def __init__(self, logger, bot_username = ""):
        self.header = {"Authorization": f"Bearer {LICHESS_TOKEN}"}
        self.logger = logger

        if(bot_username != ""):
            LichessApi.bot_username = bot_username

    """clock timer are in seconds. Timers will be invalid if not in specifc intervals. Look in lichess what those intervals are.""" 
    def start_game(self, player_color = "random", clock_limit = 600, clock_increment = 5) -> bool:
        req_body = {
            "rated": False,
            "clock.limit": clock_limit ,     #Each players total time
            "clock.increment": clock_increment,   # Time each player gains when making a move
            "color": player_color,      # "white", "black", or "random"
            "variant": "standard",
        }

        response = requests.post(
            f"https://lichess.org/api/challenge/{self.bot_username}",
            headers=self.header,
            json = req_body        
        )

        data = response.json()

        if data.get("error"):
            self.logger.warn("Something went wrong!")
            self.logger.error(data["error"])
            return False

        LichessApi._game_id = data["id"]
        LichessApi._player_color = data["finalColor"]

        if data.get("status") == "declined":
            self.logger.info("Game was declined")
            self.logger.info(f"View why here: https://lichess.org/{LichessApi._game_id}")
            return False

        self.logger.info(f"Game started! https://lichess.org/{LichessApi._game_id}")
        return True

    def abort_game(self):
        r = requests.post(
            f"https://lichess.org/api/board/game/{LichessApi._game_id}/abort",
            headers=self.header
        )

        return r.json()

    def resign_game(self):
        r = requests.post(
            f"https://lichess.org/api/board/game/{LichessApi._game_id}/resign",
            headers=self.header
        )

        return r.json()

    def make_move(self, move: str):
        headers = {"Authorization": f"Bearer {LICHESS_TOKEN}"}
        r = requests.post(
            f"https://lichess.org/api/board/game/{LichessApi._game_id}/move/{move}",
            headers=headers
        )

        return r.json()

    def show_available_bots(self):
        self.logger.info("maia1")
        self.logger.info("maia5")
        self.logger.info("maia9")
        self.logger.info("Visit: lichess.org/player/bots for community bots!")
    
    #Returns json object of newest board event. Will return 'finished' if game is over
    #Blocks program until at least one response is received
    def wait_for_board_event(self):
        response = requests.get(
            f"https://lichess.org/api/board/game/stream/{LichessApi._game_id}",
            headers=self.header,
            stream=True
        )

        return response

    
    def set_game_id(self, game_id: str):
        LichessApi._game_id = game_id

    
if __name__ == "__main__":
    lichess = LichessApi()
    if lichess.start_game(clock_limit = 600, clock_increment = 5):

        if lichess._player_color == "white":
            lichess.make_move("e2e4")

            black_move = "none"
            while(black_move == "none"):
                moves = lichess.wait_for_board_event()
                black_move = lichess.get_black_move(moves)
            
            lichess.logger.info(f"Bot made move: {black_move}")

        else:
            black_move = "none"
            while(black_move == "none"):
                moves = lichess.wait_for_board_event()
                black_move = lichess.get_black_move(moves)

            lichess.make_move("e4")
            
            lichess.logger.info(f"Bot made move: {black_move}")


        lichess.resign_game()
