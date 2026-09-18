from copy import deepcopy

MODES = {
    "practice": {"label": "Practice Lab", "topic": "Arrays", "reward": 35},
    "dsa": {"label": "DSA Duel", "topic": "Algorithms", "reward": 70},
    "cp": {"label": "CP Sprint", "topic": "Competitive Programming", "reward": 95},
    "technical": {"label": "Technical Round", "topic": "Interview Engineering", "reward": 120},
}

BASE_CHALLENGE = {
    "title": "Signal Pair Scanner",
    "difficulty": "easy",
    "story_narrative": "A relay tower is receiving scrambled signals. Find the two values whose sum matches the target before the rival bot takes the sector.",
    "constraints": ["Return the indexes of the two matching values.", "Exactly one valid answer exists.", "Aim for O(n) time with a hash map."],
    "starter_templates": {
        "python": "def two_sum(nums, target):\n    # Return the two indexes\n    pass\n",
        "cpp": "#include <vector>\nusing namespace std;\nvector<int> twoSum(vector<int>& nums, int target) {\n    // Return the two indexes\n}\n",
        "javascript": "function twoSum(nums, target) {\n  // Return the two indexes\n}\n",
    },
    "test_cases": [
        {"input": "[2,7,11,15] 9", "expected_output": "[0,1]", "is_hidden": False},
        {"input": "[3,2,4] 6", "expected_output": "[1,2]", "is_hidden": False},
        {"input": "[3,3] 6", "expected_output": "[0,1]", "is_hidden": True},
    ],
    "lesson": "Use a hash map from number to index. For each value x, look for target - x before storing x.",
}

BOT_NAMES = ["Byte Rookie", "Cache Phantom", "Graph Raider", "Kernel Knight", "Quantum Queue"]

def level_from_xp(xp: int) -> int:
    return max(1, int((xp / 120) ** 0.5) + 1)

def challenge_for(mode: str, level: int) -> dict:
    if mode not in MODES:
        mode = "practice"
    challenge = deepcopy(BASE_CHALLENGE)
    tier = min(5, max(1, level))
    challenge["difficulty"] = ["easy", "easy", "medium", "hard", "elite"][tier - 1]
    challenge["mode"] = mode
    challenge["mode_label"] = MODES[mode]["label"]
    challenge["xp_reward"] = MODES[mode]["reward"] + (tier - 1) * 15
    challenge["bot"] = {"name": BOT_NAMES[tier - 1], "level": tier, "eta_seconds": 150 - tier * 12}
    return challenge

def public_challenge(challenge: dict) -> dict:
    clean = deepcopy(challenge)
    clean["test_cases"] = [case for case in clean["test_cases"] if not case.get("is_hidden")]
    return clean
