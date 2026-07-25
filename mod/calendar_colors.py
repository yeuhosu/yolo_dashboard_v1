from collections import Counter

# 部位ごとに視覚的な識別用のカラーコード（HEX）を定義
PART_COLOR_MAP = {
    "胸": "#F59E0B",        # オレンジ
    "背中": "#FBBF24",      # 黄色
    "脚": "#EF4444",        # 赤
    "肩": "#8B5A2B",        # 茶色
    "上腕2頭": "#10B981",   # 緑
    "上腕3頭": "#84CC16",   # 黄緑
    "腹筋": "#8B5CF6",      # 紫
    "有酸素": "#3B82F6",    # 青
}

# 同回数登場する部位がある場合に、どれを優先してメイン部位とするかの順位を定義
PART_PRIORITY = {
    "胸": 0,
    "背中": 1,
    "脚": 2,
    "肩": 3,
    "上腕2頭": 4,
    "上腕3頭": 5,
    "腹筋": 6,
    "有酸素": 7,
}

def parse_parts(value):
    """
    カンマ区切りの文字列を分割し、前後の空白を取り除いたリストを返す関数
    Parameters:
        value (str, int, など): 分割対象の値（文字列や数値など）
    Returns:
        list: 空白を除去した要素のリスト（値が空の場合は空リスト）
    """
    # value が空（None、空文字、空のリストなど）の場合は、空のリストを返す
    if not value:
        return []
    # value を文字列に変換し、カンマ(,)で分割する
    # 各要素の前後の空白を strip() で削除し、空文字でないものだけをリストに含める
    return [p.strip() for p in str(value).split(",") if p.strip()]

# 指定された部位のカラーコードを取得（未定義の部位はデフォルトのグレー #D1D5DB を返す）
def get_part_color(part):
    return PART_COLOR_MAP.get(part, "#D1D5DB")

# 渡された部位リストの中で最も登場回数が多い「メインの部位」を判定。同点の場合は PART_PRIORITY に従って決定
def get_dominant_part(parts):
    if not parts:
        return None
    counts = Counter(parts)
    max_count = max(counts.values())
    candidates = [p for p, c in counts.items() if c == max_count]
    return sorted(candidates, key=lambda p: PART_PRIORITY.get(p, 99))[0]

# メイン部位の色を決定する
def get_day_color(parts):
    dominant = get_dominant_part(parts)
    return get_part_color(dominant) if dominant else "#E5E7EB"