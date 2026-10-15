
class GameState:
    def __init__(self):
        self.reset()

    def reset(self):
        self.current_scene = "start"

        self.max_health = 100
        self.health = 100

        self.inventory = []
        self.clues = []
        self.completed_puzzles = []

        self.has_princess_token = False
        self.has_poison_protection = False
        self.has_holy_sword = False

        self.dragon_defeated = False
        self.princess_saved = False
        self.ending = None

    def add_item(self, item_name):
        if item_name not in self.inventory:
            self.inventory.append(item_name)

    def has_item(self, item_name):
        return item_name in self.inventory

    def add_clue(self, clue_name):
        if clue_name not in self.clues:
            self.clues.append(clue_name)

    def complete_puzzle(self, puzzle_id):
        if puzzle_id not in self.completed_puzzles:
            self.completed_puzzles.append(puzzle_id)

    def take_damage(self, damage):
        if damage > 0:
            self.health = max(0, self.health - damage)

    def heal(self, amount):
        if amount > 0:
            self.health = min(
                self.max_health,
                self.health + amount
            )
