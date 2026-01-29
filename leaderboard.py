import os
import csv

# Configuration
leader_board_file = "leaderboard.csv"
max_len = 10
csv_header = ["name", "score", "level"]


def bubble_sort(rows):
   
    #rows = list of dicts: {"name": str, "score": int, "level": int}
    #Sort by:
    # score DESC
    # level DESC
   
    arr = rows[:]
    n = len(arr)
    for i in range(n):
        for j in range(0, n - i - 1):
            a, b = arr[j], arr[j + 1]
            if (
                a["score"] < b["score"]
                or (a["score"] == b["score"] and a["level"] < b["level"])
            ):
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr


def ensure_file_exists():
    if not os.path.exists(leader_board_file):
        with open(leader_board_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(csv_header)


def load_leaderboard():
    ensure_file_exists()
    rows = []
    try:
        with open(leader_board_file, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                try:
                    rows.append({
                        "name": str(r.get("name", ""))[:max_len] or "PLAYER",
                        "score": int(r.get("score", 0)),
                        "level": int(r.get("level", 1)),
                    })
                except Exception:
                    continue
    except Exception:
        return []
    return rows


def save_leaderboard(rows):
    ensure_file_exists()
    with open(leader_board_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=csv_header)
        writer.writeheader()
        for r in rows:
            writer.writerow({
                "name": r["name"][:max_len],
                "score": int(r["score"]),
                "level": int(r["level"]),
            })


def get_top_score():
    rows = bubble_sort(load_leaderboard())
    if not rows:
        return None
    return rows[0]


def add_score(name, score, level_reached):
    
    #Adds a new entry, sorts with bubble sort, saves to file
    #Returns: (sorted_rows, is_new_highscore)
    
    name = (name.strip() or "PLAYER")[:max_len]
    score = int(score)
    level_reached = int(level_reached)

    before_top = get_top_score()

    rows = load_leaderboard()
    rows.append({
        "name": name,
        "score": score,
        "level": level_reached
    })

    rows = bubble_sort(rows)
    save_leaderboard(rows)

    # Highscore detection
    is_new_highscore = False
    if before_top is None:
        is_new_highscore = True
    else:
        top = rows[0]
        if (
            top["score"] > before_top["score"]
            or (top["score"] == before_top["score"] and top["level"] > before_top["level"])
        ):
            is_new_highscore = True

    return rows, is_new_highscore


def get_menu_rows(limit=6):
    
    #Returns list of tuples for menu UI:
    #[(name, 'score (LV X)'), ...]
    
    rows = bubble_sort(load_leaderboard())[:limit]
    out = []
    for r in rows:
        out.append((r["name"], f'{r["score"]}  (LV {r["level"]})'))
    return out
