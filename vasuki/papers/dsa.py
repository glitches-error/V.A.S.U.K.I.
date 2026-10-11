"""DSA coding problems for DSA-pattern companies.

Each problem is solved by implementing one Python function. Tests call the
function with `args` and compare the return value to `expected` ("exact"), or
after sorting both sides ("unordered"). Only the tests marked "sample" are
shown to the player. Problems are written in the style each company is known
for; they are original practice problems, not leaked interview questions.
"""

PROBLEMS = [
    # ------------------------------------------------------------------ Optum
    {
        "company": "Optum",
        "title": "Second Largest Distinct",
        "level": "Easy",
        "topics": ["Arrays"],
        "statement": (
            "Given a list of integers nums, return the second largest DISTINCT value.\n"
            "If there is no second distinct value, return -1.\n\n"
            "Example 1: nums = [4, 1, 7, 7, 3] -> 4  (largest is 7, next distinct is 4)\n"
            "Example 2: nums = [5, 5] -> -1\n\n"
            "Return type: int\n"
            "Constraints: 0 <= len(nums) <= 10^5, -10^9 <= nums[i] <= 10^9"
        ),
        "func": "second_largest",
        "starter": "def second_largest(nums):\n    # write your code here\n    pass\n",
        "compare": "exact",
        "tests": [
            {"args": [[4, 1, 7, 7, 3]], "expected": 4, "sample": True},
            {"args": [[5, 5]], "expected": -1, "sample": True},
            {"args": [[]], "expected": -1, "sample": False},
            {"args": [[9]], "expected": -1, "sample": False},
            {"args": [[-3, -1, -2]], "expected": -2, "sample": False},
            {"args": [[1, 2]], "expected": 1, "sample": False},
            {"args": [[10, 10, 9, 9, 8]], "expected": 9, "sample": False},
            {"args": [[0, -5, 0, -5]], "expected": -5, "sample": False},
        ],
        "solution": (
            "def second_largest(nums):\n"
            "    first = second = None\n"
            "    for x in nums:\n"
            "        if first is None or x > first:\n"
            "            if first is not None:\n"
            "                second = first\n"
            "            first = x\n"
            "        elif x != first and (second is None or x > second):\n"
            "            second = x\n"
            "    return -1 if second is None else second\n"
        ),
        "approach": "Single pass tracking the largest and second-largest distinct values: O(n) time, O(1) space.",
    },
    {
        "company": "Optum",
        "title": "Valid Anagram Check",
        "level": "Easy",
        "topics": ["Strings", "Hashing"],
        "statement": (
            "Given two strings s and t, return True if t is an anagram of s, otherwise False.\n"
            "An anagram uses exactly the same characters with the same counts. Comparison is\n"
            "case-sensitive and every character (including spaces) counts.\n\n"
            "Example 1: s = \"listen\", t = \"silent\" -> True\n"
            "Example 2: s = \"rat\", t = \"car\" -> False\n\n"
            "Return type: bool\n"
            "Constraints: 0 <= len(s), len(t) <= 10^5"
        ),
        "func": "is_anagram",
        "starter": "def is_anagram(s, t):\n    # write your code here\n    pass\n",
        "compare": "exact",
        "tests": [
            {"args": ["listen", "silent"], "expected": True, "sample": True},
            {"args": ["rat", "car"], "expected": False, "sample": True},
            {"args": ["", ""], "expected": True, "sample": False},
            {"args": ["a", ""], "expected": False, "sample": False},
            {"args": ["Aa", "aA"], "expected": True, "sample": False},
            {"args": ["Ab", "ab"], "expected": False, "sample": False},
            {"args": ["aabbcc", "abcabc"], "expected": True, "sample": False},
            {"args": ["aab", "abb"], "expected": False, "sample": False},
            {"args": ["a b", "ba "], "expected": True, "sample": False},
        ],
        "solution": (
            "def is_anagram(s, t):\n"
            "    if len(s) != len(t):\n"
            "        return False\n"
            "    counts = {}\n"
            "    for ch in s:\n"
            "        counts[ch] = counts.get(ch, 0) + 1\n"
            "    for ch in t:\n"
            "        if counts.get(ch, 0) == 0:\n"
            "            return False\n"
            "        counts[ch] -= 1\n"
            "    return True\n"
        ),
        "approach": "Count characters of s in a hash map, then decrement with t; any shortfall means not an anagram. O(n) time.",
    },
    {
        "company": "Optum",
        "title": "Longest Run of Ones After One Flip",
        "level": "Medium",
        "topics": ["Arrays", "Sliding Window"],
        "statement": (
            "Given a list bits containing only 0s and 1s, you may flip AT MOST one 0 into a 1.\n"
            "Return the length of the longest contiguous run of 1s you can get.\n\n"
            "Example 1: bits = [1, 0, 1, 1, 0] -> 4  (flip index 1: [1,1,1,1,0])\n"
            "Example 2: bits = [1, 1, 1] -> 3\n\n"
            "Return type: int\n"
            "Constraints: 0 <= len(bits) <= 10^5"
        ),
        "func": "longest_ones",
        "starter": "def longest_ones(bits):\n    # write your code here\n    pass\n",
        "compare": "exact",
        "tests": [
            {"args": [[1, 0, 1, 1, 0]], "expected": 4, "sample": True},
            {"args": [[1, 1, 1]], "expected": 3, "sample": True},
            {"args": [[]], "expected": 0, "sample": False},
            {"args": [[0]], "expected": 1, "sample": False},
            {"args": [[0, 0, 0]], "expected": 1, "sample": False},
            {"args": [[1, 0, 1, 0, 1, 1, 1]], "expected": 5, "sample": False},
            {"args": [[0, 1, 1, 0, 1, 1, 0, 1]], "expected": 5, "sample": False},
            {"args": [[1, 1, 0, 0, 1, 1]], "expected": 3, "sample": False},
        ],
        "solution": (
            "def longest_ones(bits):\n"
            "    best = left = zeros = 0\n"
            "    for right, b in enumerate(bits):\n"
            "        if b == 0:\n"
            "            zeros += 1\n"
            "        while zeros > 1:\n"
            "            if bits[left] == 0:\n"
            "                zeros -= 1\n"
            "            left += 1\n"
            "        best = max(best, right - left + 1)\n"
            "    return best\n"
        ),
        "approach": "Sliding window that holds at most one zero; shrink from the left when a second zero enters. O(n) time, O(1) space.",
    },

    # ------------------------------------------------------------------ Adobe
    {
        "company": "Adobe",
        "title": "Reverse Words in a Sentence",
        "level": "Easy",
        "topics": ["Strings"],
        "statement": (
            "Given a string s, return a string with the words in reverse order.\n"
            "Words are separated by one or more spaces. The result must have words joined by a\n"
            "single space, with no leading or trailing spaces.\n\n"
            "Example 1: s = \"the sky is blue\" -> \"blue is sky the\"\n"
            "Example 2: s = \"  hello   world \" -> \"world hello\"\n\n"
            "Return type: str\n"
            "Constraints: 0 <= len(s) <= 10^4"
        ),
        "func": "reverse_words",
        "starter": "def reverse_words(s):\n    # write your code here\n    pass\n",
        "compare": "exact",
        "tests": [
            {"args": ["the sky is blue"], "expected": "blue is sky the", "sample": True},
            {"args": ["  hello   world "], "expected": "world hello", "sample": True},
            {"args": [""], "expected": "", "sample": False},
            {"args": ["   "], "expected": "", "sample": False},
            {"args": ["single"], "expected": "single", "sample": False},
            {"args": ["a b c d"], "expected": "d c b a", "sample": False},
            {"args": ["Adobe  Creative Cloud"], "expected": "Cloud Creative Adobe", "sample": False},
            {"args": [" x "], "expected": "x", "sample": False},
        ],
        "solution": (
            "def reverse_words(s):\n"
            "    return ' '.join(reversed(s.split()))\n"
        ),
        "approach": "Split on whitespace (which drops empty tokens), reverse the list, join with single spaces. O(n) time.",
    },
    {
        "company": "Adobe",
        "title": "Product of Array Except Self",
        "level": "Medium",
        "topics": ["Arrays", "Prefix Products"],
        "statement": (
            "Given a list of integers nums, return a list out where out[i] is the product of every\n"
            "element of nums except nums[i]. Do not use division.\n\n"
            "Example 1: nums = [1, 2, 3, 4] -> [24, 12, 8, 6]\n"
            "Example 2: nums = [-1, 1, 0, -3, 3] -> [0, 0, 9, 0, 0]\n\n"
            "Return type: list[int] (same length as nums)\n"
            "Constraints: 1 <= len(nums) <= 10^5"
        ),
        "func": "product_except_self",
        "starter": "def product_except_self(nums):\n    # write your code here\n    pass\n",
        "compare": "exact",
        "tests": [
            {"args": [[1, 2, 3, 4]], "expected": [24, 12, 8, 6], "sample": True},
            {"args": [[-1, 1, 0, -3, 3]], "expected": [0, 0, 9, 0, 0], "sample": True},
            {"args": [[5]], "expected": [1], "sample": False},
            {"args": [[2, 3]], "expected": [3, 2], "sample": False},
            {"args": [[0, 0, 2]], "expected": [0, 0, 0], "sample": False},
            {"args": [[0, 4, 5]], "expected": [20, 0, 0], "sample": False},
            {"args": [[-2, -3, 4]], "expected": [-12, -8, 6], "sample": False},
            {"args": [[1, 1, 1, 1, 1]], "expected": [1, 1, 1, 1, 1], "sample": False},
        ],
        "solution": (
            "def product_except_self(nums):\n"
            "    n = len(nums)\n"
            "    out = [1] * n\n"
            "    left = 1\n"
            "    for i in range(n):\n"
            "        out[i] = left\n"
            "        left *= nums[i]\n"
            "    right = 1\n"
            "    for i in range(n - 1, -1, -1):\n"
            "        out[i] *= right\n"
            "        right *= nums[i]\n"
            "    return out\n"
        ),
        "approach": "Fill out[i] with the product of everything to the left, then sweep right-to-left multiplying in the product of everything to the right. O(n) time, O(1) extra space.",
    },
    {
        "company": "Adobe",
        "title": "Longest Palindromic Substring",
        "level": "Medium",
        "topics": ["Strings", "Two Pointers"],
        "statement": (
            "Given a string s, return its longest palindromic substring.\n"
            "If several have the same maximum length, return the one that starts EARLIEST in s.\n\n"
            "Example 1: s = \"babad\" -> \"bab\"  (\"aba\" is also length 3 but starts later)\n"
            "Example 2: s = \"cbbd\" -> \"bb\"\n\n"
            "Return type: str (empty string if s is empty)\n"
            "Constraints: 0 <= len(s) <= 1000"
        ),
        "func": "longest_palindrome",
        "starter": "def longest_palindrome(s):\n    # write your code here\n    pass\n",
        "compare": "exact",
        "tests": [
            {"args": ["babad"], "expected": "bab", "sample": True},
            {"args": ["cbbd"], "expected": "bb", "sample": True},
            {"args": [""], "expected": "", "sample": False},
            {"args": ["a"], "expected": "a", "sample": False},
            {"args": ["abc"], "expected": "a", "sample": False},
            {"args": ["forgeeksskeegfor"], "expected": "geeksskeeg", "sample": False},
            {"args": ["aaaa"], "expected": "aaaa", "sample": False},
            {"args": ["abacdfgdcaba"], "expected": "aba", "sample": False},
            {"args": ["racecarxyz"], "expected": "racecar", "sample": False},
        ],
        "solution": (
            "def longest_palindrome(s):\n"
            "    best_start, best_len = 0, 0\n"
            "    for c in range(len(s)):\n"
            "        for lo, hi in ((c, c), (c, c + 1)):\n"
            "            while lo >= 0 and hi < len(s) and s[lo] == s[hi]:\n"
            "                lo -= 1\n"
            "                hi += 1\n"
            "            length = hi - lo - 1\n"
            "            start = lo + 1\n"
            "            if length > best_len or (length == best_len and start < best_start):\n"
            "                best_start, best_len = start, length\n"
            "    return s[best_start:best_start + best_len]\n"
        ),
        "approach": "Expand around every centre (each character and each gap) and keep the longest, preferring the earliest start on ties. O(n^2) time, O(1) space.",
    },

    # --------------------------------------------------------------- Flipkart
    {
        "company": "Flipkart",
        "title": "Best Day to Buy and Sell",
        "level": "Easy",
        "topics": ["Arrays", "Greedy"],
        "statement": (
            "prices[i] is the price of an item on day i. You may buy once and later sell once.\n"
            "Return the maximum profit you can make. If no profit is possible, return 0.\n\n"
            "Example 1: prices = [7, 1, 5, 3, 6, 4] -> 5  (buy at 1, sell at 6)\n"
            "Example 2: prices = [7, 6, 4, 3, 1] -> 0\n\n"
            "Return type: int\n"
            "Constraints: 0 <= len(prices) <= 10^5, 0 <= prices[i] <= 10^4"
        ),
        "func": "max_profit",
        "starter": "def max_profit(prices):\n    # write your code here\n    pass\n",
        "compare": "exact",
        "tests": [
            {"args": [[7, 1, 5, 3, 6, 4]], "expected": 5, "sample": True},
            {"args": [[7, 6, 4, 3, 1]], "expected": 0, "sample": True},
            {"args": [[]], "expected": 0, "sample": False},
            {"args": [[5]], "expected": 0, "sample": False},
            {"args": [[1, 2]], "expected": 1, "sample": False},
            {"args": [[3, 3, 3]], "expected": 0, "sample": False},
            {"args": [[2, 4, 1, 7]], "expected": 6, "sample": False},
            {"args": [[9, 2, 8, 1, 3]], "expected": 6, "sample": False},
        ],
        "solution": (
            "def max_profit(prices):\n"
            "    best = 0\n"
            "    low = None\n"
            "    for p in prices:\n"
            "        if low is None or p < low:\n"
            "            low = p\n"
            "        best = max(best, p - low)\n"
            "    return best\n"
        ),
        "approach": "Track the lowest price seen so far and the best profit selling today. O(n) time, O(1) space.",
    },
    {
        "company": "Flipkart",
        "title": "Merge Delivery Windows",
        "level": "Medium",
        "topics": ["Intervals", "Sorting"],
        "statement": (
            "Each delivery window is [start, end] with start <= end. Merge all windows that overlap\n"
            "or touch (end of one == start of next) and return the merged list sorted by start.\n\n"
            "Example 1: windows = [[1,3],[2,6],[8,10],[15,18]] -> [[1,6],[8,10],[15,18]]\n"
            "Example 2: windows = [[1,4],[4,5]] -> [[1,5]]\n\n"
            "Return type: list[list[int]]\n"
            "Constraints: 0 <= len(windows) <= 10^4, 0 <= start <= end <= 10^6"
        ),
        "func": "merge_windows",
        "starter": "def merge_windows(windows):\n    # write your code here\n    pass\n",
        "compare": "exact",
        "tests": [
            {"args": [[[1, 3], [2, 6], [8, 10], [15, 18]]], "expected": [[1, 6], [8, 10], [15, 18]], "sample": True},
            {"args": [[[1, 4], [4, 5]]], "expected": [[1, 5]], "sample": True},
            {"args": [[]], "expected": [], "sample": False},
            {"args": [[[5, 7]]], "expected": [[5, 7]], "sample": False},
            {"args": [[[8, 10], [1, 3], [2, 6]]], "expected": [[1, 6], [8, 10]], "sample": False},
            {"args": [[[1, 10], [2, 3], [4, 5]]], "expected": [[1, 10]], "sample": False},
            {"args": [[[1, 2], [3, 4], [5, 6]]], "expected": [[1, 2], [3, 4], [5, 6]], "sample": False},
            {"args": [[[0, 0], [0, 0], [1, 1]]], "expected": [[0, 0], [1, 1]], "sample": False},
        ],
        "solution": (
            "def merge_windows(windows):\n"
            "    out = []\n"
            "    for s, e in sorted(windows):\n"
            "        if out and s <= out[-1][1]:\n"
            "            out[-1][1] = max(out[-1][1], e)\n"
            "        else:\n"
            "            out.append([s, e])\n"
            "    return out\n"
        ),
        "approach": "Sort by start, then sweep: extend the last merged window when the next one starts at or before its end. O(n log n) time.",
    },
    {
        "company": "Flipkart",
        "title": "Coin Change Minimum Coins",
        "level": "Medium",
        "topics": ["Dynamic Programming"],
        "statement": (
            "Given coin denominations coins (unlimited supply of each) and an amount, return the\n"
            "fewest coins needed to make exactly amount. Return -1 if it cannot be made.\n\n"
            "Example 1: coins = [1, 2, 5], amount = 11 -> 3  (5 + 5 + 1)\n"
            "Example 2: coins = [2], amount = 3 -> -1\n\n"
            "Return type: int (0 when amount is 0)\n"
            "Constraints: 1 <= len(coins) <= 12, 1 <= coins[i] <= 10^4, 0 <= amount <= 10^4"
        ),
        "func": "min_coins",
        "starter": "def min_coins(coins, amount):\n    # write your code here\n    pass\n",
        "compare": "exact",
        "tests": [
            {"args": [[1, 2, 5], 11], "expected": 3, "sample": True},
            {"args": [[2], 3], "expected": -1, "sample": True},
            {"args": [[1], 0], "expected": 0, "sample": False},
            {"args": [[7], 7], "expected": 1, "sample": False},
            {"args": [[1, 3, 4], 6], "expected": 2, "sample": False},
            {"args": [[2, 5, 10, 1], 27], "expected": 4, "sample": False},
            {"args": [[186, 419, 83, 408], 6249], "expected": 20, "sample": False},
            {"args": [[5, 10], 3], "expected": -1, "sample": False},
        ],
        "solution": (
            "def min_coins(coins, amount):\n"
            "    INF = float('inf')\n"
            "    dp = [0] + [INF] * amount\n"
            "    for a in range(1, amount + 1):\n"
            "        for c in coins:\n"
            "            if c <= a and dp[a - c] + 1 < dp[a]:\n"
            "                dp[a] = dp[a - c] + 1\n"
            "    return -1 if dp[amount] == INF else dp[amount]\n"
        ),
        "approach": "Bottom-up DP: dp[a] = 1 + min(dp[a - c]) over coins c. Greedy fails (e.g. [1,3,4] for 6). O(amount * len(coins)) time.",
    },

    # ----------------------------------------------------------------- Amazon
    {
        "company": "Amazon",
        "title": "Longest Substring Without Repeats",
        "level": "Medium",
        "topics": ["Strings", "Sliding Window"],
        "statement": (
            "Given a string s, return the length of the longest substring that contains no\n"
            "repeated characters.\n\n"
            "Example 1: s = \"abcabcbb\" -> 3  (\"abc\")\n"
            "Example 2: s = \"bbbbb\" -> 1\n\n"
            "Return type: int\n"
            "Constraints: 0 <= len(s) <= 5 * 10^4"
        ),
        "func": "longest_unique",
        "starter": "def longest_unique(s):\n    # write your code here\n    pass\n",
        "compare": "exact",
        "tests": [
            {"args": ["abcabcbb"], "expected": 3, "sample": True},
            {"args": ["bbbbb"], "expected": 1, "sample": True},
            {"args": [""], "expected": 0, "sample": False},
            {"args": ["pwwkew"], "expected": 3, "sample": False},
            {"args": ["a"], "expected": 1, "sample": False},
            {"args": ["abba"], "expected": 2, "sample": False},
            {"args": ["dvdf"], "expected": 3, "sample": False},
            {"args": ["a b c a"], "expected": 3, "sample": False},
            {"args": ["abcdefghij"], "expected": 10, "sample": False},
        ],
        "solution": (
            "def longest_unique(s):\n"
            "    last = {}\n"
            "    best = left = 0\n"
            "    for i, ch in enumerate(s):\n"
            "        if ch in last and last[ch] >= left:\n"
            "            left = last[ch] + 1\n"
            "        last[ch] = i\n"
            "        best = max(best, i - left + 1)\n"
            "    return best\n"
        ),
        "approach": "Sliding window with a map of each character's last index; jump the left edge past a repeat. O(n) time.",
    },
    {
        "company": "Amazon",
        "title": "K Closest Warehouses",
        "level": "Medium",
        "topics": ["Heaps", "Sorting"],
        "statement": (
            "points is a list of warehouse coordinates [x, y]. Return the k points closest to the\n"
            "origin (0, 0) by Euclidean distance.\n"
            "Order the result by distance ascending; break ties by x ascending, then y ascending.\n\n"
            "Example 1: points = [[1,3],[-2,2]], k = 1 -> [[-2,2]]\n"
            "Example 2: points = [[3,3],[5,-1],[-2,4]], k = 2 -> [[3,3],[-2,4]]\n\n"
            "Return type: list[list[int]]\n"
            "Constraints: 0 <= k <= len(points) <= 10^4, -10^4 <= x, y <= 10^4"
        ),
        "func": "k_closest",
        "starter": "def k_closest(points, k):\n    # write your code here\n    pass\n",
        "compare": "exact",
        "tests": [
            {"args": [[[1, 3], [-2, 2]], 1], "expected": [[-2, 2]], "sample": True},
            {"args": [[[3, 3], [5, -1], [-2, 4]], 2], "expected": [[3, 3], [-2, 4]], "sample": True},
            {"args": [[[1, 1]], 0], "expected": [], "sample": False},
            {"args": [[[0, 0]], 1], "expected": [[0, 0]], "sample": False},
            {"args": [[[1, 0], [0, 1], [-1, 0], [0, -1]], 2], "expected": [[-1, 0], [0, -1]], "sample": False},
            {"args": [[[2, 2], [1, 1], [3, 3]], 3], "expected": [[1, 1], [2, 2], [3, 3]], "sample": False},
            {"args": [[[5, 5], [-5, -5], [1, 7]], 1], "expected": [[-5, -5]], "sample": False},
            {"args": [[[10, 0], [0, 10], [6, 8], [8, 6], [1, 1]], 3], "expected": [[1, 1], [0, 10], [6, 8]], "sample": False},
        ],
        "solution": (
            "import heapq\n"
            "def k_closest(points, k):\n"
            "    keyed = [(x * x + y * y, x, y) for x, y in points]\n"
            "    return [[x, y] for _, x, y in heapq.nsmallest(k, keyed)]\n"
        ),
        "approach": "Key each point by (squared distance, x, y) and take the k smallest with a heap. O(n log k) time.",
    },
    {
        "company": "Amazon",
        "title": "Sliding Window Maximum",
        "level": "Hard",
        "topics": ["Deque", "Sliding Window"],
        "statement": (
            "Given a list nums and a window size k, a window of size k slides from the left of nums\n"
            "to the right, one step at a time. Return a list with the maximum of each window.\n\n"
            "Example 1: nums = [1,3,-1,-3,5,3,6,7], k = 3 -> [3,3,5,5,6,7]\n"
            "Example 2: nums = [4], k = 1 -> [4]\n\n"
            "Return type: list[int] (length len(nums) - k + 1; empty if nums is empty)\n"
            "Constraints: 0 <= len(nums) <= 10^5, 1 <= k <= max(1, len(nums))"
        ),
        "func": "window_max",
        "starter": "def window_max(nums, k):\n    # write your code here\n    pass\n",
        "compare": "exact",
        "tests": [
            {"args": [[1, 3, -1, -3, 5, 3, 6, 7], 3], "expected": [3, 3, 5, 5, 6, 7], "sample": True},
            {"args": [[4], 1], "expected": [4], "sample": True},
            {"args": [[], 1], "expected": [], "sample": False},
            {"args": [[9, 8, 7, 6], 2], "expected": [9, 8, 7], "sample": False},
            {"args": [[1, 2, 3, 4], 4], "expected": [4], "sample": False},
            {"args": [[2, 2, 2], 2], "expected": [2, 2], "sample": False},
            {"args": [[-5, -1, -3, -2], 2], "expected": [-1, -1, -2], "sample": False},
            {"args": [[1, -1], 1], "expected": [1, -1], "sample": False},
            {"args": [[7, 2, 4, 9, 1, 3, 8, 5], 3], "expected": [7, 9, 9, 9, 8, 8], "sample": False},
        ],
        "solution": (
            "from collections import deque\n"
            "def window_max(nums, k):\n"
            "    dq = deque()\n"
            "    out = []\n"
            "    for i, x in enumerate(nums):\n"
            "        while dq and nums[dq[-1]] <= x:\n"
            "            dq.pop()\n"
            "        dq.append(i)\n"
            "        if dq[0] <= i - k:\n"
            "            dq.popleft()\n"
            "        if i >= k - 1:\n"
            "            out.append(nums[dq[0]])\n"
            "    return out\n"
        ),
        "approach": "Monotonic deque of indices with decreasing values; the front is always the window max. Each index enters and leaves once: O(n) time.",
    },

    # -------------------------------------------------------------- Microsoft
    {
        "company": "Microsoft",
        "title": "Spiral Matrix Order",
        "level": "Medium",
        "topics": ["Matrices", "Simulation"],
        "statement": (
            "Given an m x n matrix (list of rows), return all of its elements in spiral order:\n"
            "right along the top row, down the right column, left along the bottom, up the left,\n"
            "and so on inward.\n\n"
            "Example 1: matrix = [[1,2,3],[4,5,6],[7,8,9]] -> [1,2,3,6,9,8,7,4,5]\n"
            "Example 2: matrix = [[1,2,3,4],[5,6,7,8],[9,10,11,12]] -> [1,2,3,4,8,12,11,10,9,5,6,7]\n\n"
            "Return type: list[int] (empty for an empty matrix)\n"
            "Constraints: 0 <= m, n <= 100"
        ),
        "func": "spiral_order",
        "starter": "def spiral_order(matrix):\n    # write your code here\n    pass\n",
        "compare": "exact",
        "tests": [
            {"args": [[[1, 2, 3], [4, 5, 6], [7, 8, 9]]], "expected": [1, 2, 3, 6, 9, 8, 7, 4, 5], "sample": True},
            {"args": [[[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12]]], "expected": [1, 2, 3, 4, 8, 12, 11, 10, 9, 5, 6, 7], "sample": True},
            {"args": [[]], "expected": [], "sample": False},
            {"args": [[[7]]], "expected": [7], "sample": False},
            {"args": [[[1, 2, 3]]], "expected": [1, 2, 3], "sample": False},
            {"args": [[[1], [2], [3]]], "expected": [1, 2, 3], "sample": False},
            {"args": [[[1, 2], [3, 4]]], "expected": [1, 2, 4, 3], "sample": False},
            {"args": [[[1, 2], [3, 4], [5, 6]]], "expected": [1, 2, 4, 6, 5, 3], "sample": False},
        ],
        "solution": (
            "def spiral_order(matrix):\n"
            "    out = []\n"
            "    if not matrix or not matrix[0]:\n"
            "        return out\n"
            "    top, bottom, left, right = 0, len(matrix) - 1, 0, len(matrix[0]) - 1\n"
            "    while top <= bottom and left <= right:\n"
            "        for c in range(left, right + 1):\n"
            "            out.append(matrix[top][c])\n"
            "        for r in range(top + 1, bottom + 1):\n"
            "            out.append(matrix[r][right])\n"
            "        if top < bottom:\n"
            "            for c in range(right - 1, left - 1, -1):\n"
            "                out.append(matrix[bottom][c])\n"
            "        if left < right:\n"
            "            for r in range(bottom - 1, top, -1):\n"
            "                out.append(matrix[r][left])\n"
            "        top, bottom, left, right = top + 1, bottom - 1, left + 1, right - 1\n"
            "    return out\n"
        ),
        "approach": "Peel the matrix layer by layer with four shrinking boundaries, guarding single-row/column layers. O(m*n) time.",
    },
    {
        "company": "Microsoft",
        "title": "Edit Distance",
        "level": "Medium",
        "topics": ["Dynamic Programming", "Strings"],
        "statement": (
            "Given two strings a and b, return the minimum number of single-character operations\n"
            "(insert, delete, or replace) needed to turn a into b.\n\n"
            "Example 1: a = \"horse\", b = \"ros\" -> 3  (horse -> rorse -> rose -> ros)\n"
            "Example 2: a = \"intention\", b = \"execution\" -> 5\n\n"
            "Return type: int\n"
            "Constraints: 0 <= len(a), len(b) <= 500"
        ),
        "func": "edit_distance",
        "starter": "def edit_distance(a, b):\n    # write your code here\n    pass\n",
        "compare": "exact",
        "tests": [
            {"args": ["horse", "ros"], "expected": 3, "sample": True},
            {"args": ["intention", "execution"], "expected": 5, "sample": True},
            {"args": ["", ""], "expected": 0, "sample": False},
            {"args": ["", "abc"], "expected": 3, "sample": False},
            {"args": ["abc", ""], "expected": 3, "sample": False},
            {"args": ["same", "same"], "expected": 0, "sample": False},
            {"args": ["kitten", "sitting"], "expected": 3, "sample": False},
            {"args": ["abc", "yabd"], "expected": 2, "sample": False},
        ],
        "solution": (
            "def edit_distance(a, b):\n"
            "    prev = list(range(len(b) + 1))\n"
            "    for i in range(1, len(a) + 1):\n"
            "        cur = [i] + [0] * len(b)\n"
            "        for j in range(1, len(b) + 1):\n"
            "            if a[i - 1] == b[j - 1]:\n"
            "                cur[j] = prev[j - 1]\n"
            "            else:\n"
            "                cur[j] = 1 + min(prev[j], cur[j - 1], prev[j - 1])\n"
            "        prev = cur\n"
            "    return prev[len(b)]\n"
        ),
        "approach": "Classic Levenshtein DP over prefixes, keeping only the previous row: O(len(a)*len(b)) time, O(len(b)) space.",
    },
    {
        "company": "Microsoft",
        "title": "Minimum Window Containing All Characters",
        "level": "Hard",
        "topics": ["Strings", "Sliding Window", "Hashing"],
        "statement": (
            "Given strings s and t, return the shortest substring of s that contains every character\n"
            "of t (including duplicates). If there are several of the same length, return the one\n"
            "that starts EARLIEST. If none exists, return the empty string.\n\n"
            "Example 1: s = \"ADOBECODEBANC\", t = \"ABC\" -> \"BANC\"\n"
            "Example 2: s = \"a\", t = \"aa\" -> \"\"\n\n"
            "Return type: str\n"
            "Constraints: 0 <= len(s), len(t) <= 10^5 (if t is empty, return \"\")"
        ),
        "func": "min_window",
        "starter": "def min_window(s, t):\n    # write your code here\n    pass\n",
        "compare": "exact",
        "tests": [
            {"args": ["ADOBECODEBANC", "ABC"], "expected": "BANC", "sample": True},
            {"args": ["a", "aa"], "expected": "", "sample": True},
            {"args": ["a", "a"], "expected": "a", "sample": False},
            {"args": ["", "a"], "expected": "", "sample": False},
            {"args": ["abc", ""], "expected": "", "sample": False},
            {"args": ["aaflslflsldkalskaaa", "aaa"], "expected": "aaa", "sample": False},
            {"args": ["abcabdebac", "cda"], "expected": "cabd", "sample": False},
            {"args": ["bba", "ab"], "expected": "ba", "sample": False},
            {"args": ["xyzzyx", "xz"], "expected": "xyz", "sample": False},
        ],
        "solution": (
            "def min_window(s, t):\n"
            "    if not t or not s:\n"
            "        return ''\n"
            "    need = {}\n"
            "    for ch in t:\n"
            "        need[ch] = need.get(ch, 0) + 1\n"
            "    missing = len(t)\n"
            "    best_start, best_len = 0, float('inf')\n"
            "    left = 0\n"
            "    for right, ch in enumerate(s):\n"
            "        if need.get(ch, 0) > 0:\n"
            "            missing -= 1\n"
            "        need[ch] = need.get(ch, 0) - 1\n"
            "        while missing == 0:\n"
            "            if right - left + 1 < best_len:\n"
            "                best_start, best_len = left, right - left + 1\n"
            "            need[s[left]] += 1\n"
            "            if need[s[left]] > 0:\n"
            "                missing += 1\n"
            "            left += 1\n"
            "    return '' if best_len == float('inf') else s[best_start:best_start + best_len]\n"
        ),
        "approach": "Expand the right edge until the window covers t, then shrink from the left while it still does, recording the shortest. Strict '<' keeps the earliest on ties. O(len(s) + len(t)) time.",
    },

    # ----------------------------------------------------------------- Google
    {
        "company": "Google",
        "title": "Count Islands",
        "level": "Medium",
        "topics": ["Graphs", "BFS/DFS"],
        "statement": (
            "grid is a list of equal-length strings made of '1' (land) and '0' (water). An island is\n"
            "a group of land cells connected horizontally or vertically (not diagonally).\n"
            "Return the number of islands.\n\n"
            "Example 1: grid = [\"11000\", \"11000\", \"00100\", \"00011\"] -> 3\n"
            "Example 2: grid = [\"111\", \"010\", \"111\"] -> 1\n\n"
            "Return type: int\n"
            "Constraints: 0 <= rows, cols <= 300"
        ),
        "func": "count_islands",
        "starter": "def count_islands(grid):\n    # write your code here\n    pass\n",
        "compare": "exact",
        "tests": [
            {"args": [["11000", "11000", "00100", "00011"]], "expected": 3, "sample": True},
            {"args": [["111", "010", "111"]], "expected": 1, "sample": True},
            {"args": [[]], "expected": 0, "sample": False},
            {"args": [["0"]], "expected": 0, "sample": False},
            {"args": [["1"]], "expected": 1, "sample": False},
            {"args": [["101", "010", "101"]], "expected": 5, "sample": False},
            {"args": [["11111", "10001", "10101", "10001", "11111"]], "expected": 2, "sample": False},
            {"args": [["1001", "0000", "1001"]], "expected": 4, "sample": False},
        ],
        "solution": (
            "def count_islands(grid):\n"
            "    if not grid:\n"
            "        return 0\n"
            "    rows, cols = len(grid), len(grid[0])\n"
            "    seen = set()\n"
            "    count = 0\n"
            "    for r in range(rows):\n"
            "        for c in range(cols):\n"
            "            if grid[r][c] == '1' and (r, c) not in seen:\n"
            "                count += 1\n"
            "                stack = [(r, c)]\n"
            "                seen.add((r, c))\n"
            "                while stack:\n"
            "                    y, x = stack.pop()\n"
            "                    for ny, nx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):\n"
            "                        if 0 <= ny < rows and 0 <= nx < cols and grid[ny][nx] == '1' and (ny, nx) not in seen:\n"
            "                            seen.add((ny, nx))\n"
            "                            stack.append((ny, nx))\n"
            "    return count\n"
        ),
        "approach": "Scan the grid; each unvisited land cell starts a new island, flood-filled with an iterative DFS. O(rows*cols) time.",
    },
    {
        "company": "Google",
        "title": "Minimum Daily Shipping Capacity",
        "level": "Hard",
        "topics": ["Binary Search on Answer", "Greedy"],
        "statement": (
            "Packages with weights[i] must ship IN ORDER within days days. Each day you load packages\n"
            "in order onto a truck without exceeding its capacity. Return the smallest capacity that\n"
            "ships everything within days days.\n\n"
            "Example 1: weights = [1,2,3,4,5,6,7,8,9,10], days = 5 -> 15\n"
            "  (days: [1..5], [6,7], [8], [9], [10])\n"
            "Example 2: weights = [3,2,2,4,1,4], days = 3 -> 6\n\n"
            "Return type: int (0 if weights is empty)\n"
            "Constraints: 0 <= len(weights) <= 5 * 10^4, 1 <= weights[i] <= 500, 1 <= days <= 5 * 10^4"
        ),
        "func": "ship_capacity",
        "starter": "def ship_capacity(weights, days):\n    # write your code here\n    pass\n",
        "compare": "exact",
        "tests": [
            {"args": [[1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 5], "expected": 15, "sample": True},
            {"args": [[3, 2, 2, 4, 1, 4], 3], "expected": 6, "sample": True},
            {"args": [[], 3], "expected": 0, "sample": False},
            {"args": [[7], 1], "expected": 7, "sample": False},
            {"args": [[1, 2, 3, 1, 1], 4], "expected": 3, "sample": False},
            {"args": [[5, 5, 5, 5], 1], "expected": 20, "sample": False},
            {"args": [[5, 5, 5, 5], 10], "expected": 5, "sample": False},
            {"args": [[10, 50, 100, 100, 50, 100, 100, 100], 5], "expected": 160, "sample": False},
            {"args": [[1, 1, 1, 1, 1, 1, 1, 1, 1, 1], 3], "expected": 4, "sample": False},
        ],
        "solution": (
            "def ship_capacity(weights, days):\n"
            "    if not weights:\n"
            "        return 0\n"
            "    def days_needed(cap):\n"
            "        d, load = 1, 0\n"
            "        for w in weights:\n"
            "            if load + w > cap:\n"
            "                d += 1\n"
            "                load = 0\n"
            "            load += w\n"
            "        return d\n"
            "    lo, hi = max(weights), sum(weights)\n"
            "    while lo < hi:\n"
            "        mid = (lo + hi) // 2\n"
            "        if days_needed(mid) <= days:\n"
            "            hi = mid\n"
            "        else:\n"
            "            lo = mid + 1\n"
            "    return lo\n"
        ),
        "approach": "Binary search the capacity between max(weights) and sum(weights); a greedy pass counts the days a capacity needs. O(n log(sum)) time.",
    },
    {
        "company": "Google",
        "title": "Course Schedule Order",
        "level": "Hard",
        "topics": ["Graphs", "Topological Sort"],
        "statement": (
            "There are n courses labelled 0..n-1. prereqs is a list of pairs [a, b] meaning course b\n"
            "must be taken before course a. Return an order in which all courses can be taken.\n"
            "Among all valid orders return the LEXICOGRAPHICALLY SMALLEST one (always take the\n"
            "smallest-numbered course that is currently available). If it is impossible because of\n"
            "a cycle, return an empty list.\n\n"
            "Example 1: n = 4, prereqs = [[1,0],[2,0],[3,1],[3,2]] -> [0,1,2,3]\n"
            "Example 2: n = 2, prereqs = [[0,1],[1,0]] -> []\n\n"
            "Return type: list[int]\n"
            "Constraints: 0 <= n <= 2000, 0 <= len(prereqs) <= 5000"
        ),
        "func": "course_order",
        "starter": "def course_order(n, prereqs):\n    # write your code here\n    pass\n",
        "compare": "exact",
        "tests": [
            {"args": [4, [[1, 0], [2, 0], [3, 1], [3, 2]]], "expected": [0, 1, 2, 3], "sample": True},
            {"args": [2, [[0, 1], [1, 0]]], "expected": [], "sample": True},
            {"args": [0, []], "expected": [], "sample": False},
            {"args": [1, []], "expected": [0], "sample": False},
            {"args": [3, []], "expected": [0, 1, 2], "sample": False},
            {"args": [3, [[0, 2], [1, 2]]], "expected": [2, 0, 1], "sample": False},
            {"args": [5, [[0, 4], [1, 3], [3, 4]]], "expected": [2, 4, 0, 3, 1], "sample": False},
            {"args": [3, [[1, 0], [2, 1], [0, 2]]], "expected": [], "sample": False},
            {"args": [4, [[2, 3], [0, 1]]], "expected": [1, 0, 3, 2], "sample": False},
        ],
        "solution": (
            "import heapq\n"
            "def course_order(n, prereqs):\n"
            "    indeg = [0] * n\n"
            "    graph = [[] for _ in range(n)]\n"
            "    for a, b in prereqs:\n"
            "        graph[b].append(a)\n"
            "        indeg[a] += 1\n"
            "    heap = [i for i in range(n) if indeg[i] == 0]\n"
            "    heapq.heapify(heap)\n"
            "    order = []\n"
            "    while heap:\n"
            "        c = heapq.heappop(heap)\n"
            "        order.append(c)\n"
            "        for nxt in graph[c]:\n"
            "            indeg[nxt] -= 1\n"
            "            if indeg[nxt] == 0:\n"
            "                heapq.heappush(heap, nxt)\n"
            "    return order if len(order) == n else []\n"
        ),
        "approach": "Kahn's topological sort using a min-heap of available courses, which yields the lexicographically smallest order; fewer than n courses output means a cycle. O((n + e) log n) time.",
    },
]
