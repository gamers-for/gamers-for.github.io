#!/usr/bin/env python3
"""
マスターJSONから全Hugoコンテンツページを自動生成するスクリプト
Game8と同じHTML構成・セクション順序で、文章は完全オリジナル（カジュアル口調）
アイコンはテーブル内にそのまま配置
"""

import json
import os
import re
import textwrap

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
CONTENT_DIR = os.path.join(BASE_DIR, "content", "games", "splatoon3")
IMG_BASE = "/gamers-for/images/games/splatoon3"

# 出力先（検証用: ００００１ or 本番: content/）
# 検証時はこちらに変更 → os.path.join(BASE_DIR, "００００１スプラトゥーン３", "output")
OUTPUT_DIR = CONTENT_DIR

# マスターデータ読み込み
with open(os.path.join(DATA_DIR, "splatoon3_master.json"), "r", encoding="utf-8") as f:
    MASTER = json.load(f)


def img(path):
    """画像パスをサイトURL付きに変換"""
    if not path:
        return ""
    return f"{IMG_BASE}{path.replace('/images/games/splatoon3', '')}"


def icon_img(path, alt="", size=24):
    """インラインアイコン画像のHTMLタグ"""
    if not path:
        return ""
    url = img(path)
    return f'<img src="{url}" alt="{alt}" loading="lazy" width="{size}" height="{size}" style="vertical-align:middle">'


def rating_to_num(r):
    """評価を数値に変換（ソート用）"""
    order = {"X": 0, "S+": 1, "S": 2, "A+": 3, "A": 4, "B+": 5, "B": 6, "C+": 7, "C": 8}
    return order.get(r, 99)


def tier_to_score(t):
    """ティア→数値スコア（10点満点）"""
    return {"X": "10", "S+": "9.5", "S": "9", "A+": "8.5", "A": "8",
            "B+": "7.5", "B": "7", "C+": "6.5", "C": "6"}.get(t, "7")


def weapon_slug(name):
    """武器名からURLスラッグを生成"""
    slug = name.lower()
    slug = re.sub(r'[^\w\-ぁ-ヿ亜-熙ァ-ヴー・]', '-', slug)
    slug = re.sub(r'-+', '-', slug).strip('-')
    return slug if slug else "weapon"


def stage_slug(name):
    """ステージ名からスラッグ"""
    slug = re.sub(r'[^\w\-ぁ-ヿ亜-熙ァ-ヴー＆]', '-', name)
    slug = re.sub(r'-+', '-', slug).strip('-')
    return slug if slug else "stage"


def write_file(path, content):
    """ファイルに書き込み"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


# =============================================
# カジュアル口調の文章テンプレート
# =============================================
CASUAL_STRENGTH = {
    "high_damage": "火力がマジでエグい！一撃で相手を溶かせるのが最大の武器だよ",
    "long_range": "射程がめちゃくちゃ長くて、安全な距離からガンガン撃てるのが強み",
    "fast_kill": "キルタイムが超速いから、対面で先手を取れればほぼ勝てる",
    "good_paint": "塗り性能が高くてスペシャルがガンガン溜まるのが嬉しいポイント",
    "good_sub_sp": "サブとスペシャルの組み合わせがとにかく噛み合ってて強い",
    "versatile": "塗り・キル・アシスト何でもこなせる万能タイプ。チームに1人欲しい武器",
    "mobility": "機動力が高くてガンガン動き回れる。裏取りや奇襲が得意",
}

CASUAL_WEAKNESS = {
    "low_damage": "ダメージが低めだから、確定数が多くて撃ち合いは苦手かも",
    "short_range": "射程が短いから、長射程武器にはアウトレンジされがち。距離詰めが必須",
    "slow_kill": "キルタイムが遅めなので、真正面からの撃ち合いはちょっと厳しい",
    "high_ink": "インク消費が激しいから、インク管理をミスると何もできなくなる",
    "hard_to_use": "操作が結構ムズいから、使いこなすまでに練習が必要",
    "slow_mobility": "足が遅いから、ポジション取りを間違えると逃げられない",
}

# 武器種別の立ち回り解説（カジュアル口調）
CLASS_PLAYSTYLE = {
    "シューター": """シューターの基本は**中距離で相手をしっかりキルすること**。自分の射程をちゃんと把握して、有利な間合いで戦うのが超大事！

塗りもキルもバランスよくこなせるのがシューターの強みだから、味方のカバーをしつつ前線を上げていこう。無理に突っ込まないで、サブとスペシャルを上手く使いながら立ち回るのがコツだよ。""",

    "ブラスター": """ブラスターは**爆風を使って壁裏の相手もキルできる**のが最大の強み！直撃を当てれば一撃で倒せるから、エイム力があればめちゃくちゃ強い。

ただし連射が遅いから、外すと一気にピンチになる。慎重に1発1発を大事に撃とう。ヤグラの上とか障害物の多いステージだと特に活躍できるよ！""",

    "ローラー": """ローラーは**潜伏からの奇襲が命**。ヨコ振りで一撃キルを狙うのが基本で、相手の位置をしっかり把握してから仕掛けるのが大事。

ぶっちゃけ正面から突っ込むのはNG。マップをこまめに見て、相手の死角から近づいてドカンと一撃で仕留めよう！塗りも意外とできるから、スペシャル回しも忘れずに。""",

    "フデ": """フデの強みは**圧倒的な機動力**。塗りながら超高速で移動できるから、裏取りや奇襲がめちゃくちゃ得意！

前線を荒らして相手の注意を引きつけたり、ヘイトを稼いで味方が動きやすい状況を作るのが役割。キルよりも「相手を困らせる」動きを意識するとチームに貢献できるよ。""",

    "チャージャー": """チャージャーは**後方から味方をサポートする狙撃手**。高台を確保して、相手の前線を下げさせるのが仕事。

チャージャーが1人いるだけで相手は前に出づらくなるから、存在自体がめっちゃ強い。ただしデスしすぎると戦犯になるから、安全なポジションから確実に仕事をしよう。""",

    "スロッシャー": """スロッシャーは**放物線を描くインクで障害物越しに攻撃できる**のがめちゃ強い。高台から降ってくるインクは避けにくいから、地形を活かした戦い方が基本！

特にヤグラやエリアでは壁越しに相手を倒せるのがデカい。ただしインク消費が激しいから、インク管理はしっかりね。""",

    "スピナー": """スピナーは**チャージ後の連射火力が圧倒的**。弾幕を張って相手を制圧するのが基本で、ポジションを取ってからの撃ち合いがめちゃくちゃ強い！

事前チャージを活用して、相手が出てきた瞬間にフルパワーで撃ち込むのがコツ。逆に不意を突かれるとチャージが間に合わないから、立ち位置に注意しよう。""",

    "マニューバー": """マニューバーは**スライドを使った機動力**が最大の武器！スライド後は集弾率が上がるから、スライドしながらキルを取るのが基本。

連続スライドで敵のエイムをズラしながら倒す動きは、使いこなせればマジで強い。ただしスライド後は隙ができるから、スライドのタイミングと方向が超大事。""",

    "シェルター": """シェルターは**傘を展開して攻撃を防ぎながら戦える**唯一の武器種。味方の盾になれるのがめちゃくちゃ強い！

傘を使って前線を押し上げたり、味方を守りながらオブジェクトを確保する立ち回りが基本。ただし傘が壊されると一気に不利になるから、傘の耐久値は常に意識しよう。""",

    "ストリンガー": """ストリンガーは**3方向に同時射撃**できるのが特徴。広範囲をカバーできるから、索敵と牽制が得意！

チャージ具合で射程と弾の広がりが変わるから、状況に合わせてチャージ量を調整するのがコツ。中距離での制圧力が高くて、相手の動きを制限できるのが強みだよ。""",

    "ワイパー": """ワイパーは**ヨコ斬りとタメ斬りの使い分け**が命。ヨコ斬りは近距離の広範囲、タメ斬りは遠距離の高ダメージと、2つの攻撃を状況で切り替えるのが基本！

タメ斬りのダメージがマジで高いから、上手く当てられれば一撃で相手を倒せる。操作は難しめだけど、使いこなせれば環境トップクラスの強さだよ。""",
}

# ルール別の武器種適性
RULE_CLASS_BONUS = {
    "nawabari": {"シューター": 1, "ブラスター": -1, "ローラー": 0, "フデ": 1, "チャージャー": -2,
                 "スロッシャー": 0, "スピナー": 0, "マニューバー": 0, "シェルター": -1,
                 "ストリンガー": -1, "ワイパー": 0},
    "area": {"シューター": 0, "ブラスター": 0, "ローラー": -1, "フデ": 0, "チャージャー": 0,
             "スロッシャー": 1, "スピナー": 1, "マニューバー": 0, "シェルター": 0,
             "ストリンガー": 0, "ワイパー": 0},
    "yagura": {"シューター": 0, "ブラスター": 2, "ローラー": 0, "フデ": -1, "チャージャー": 0,
               "スロッシャー": 1, "スピナー": 0, "マニューバー": -1, "シェルター": 1,
               "ストリンガー": 0, "ワイパー": 0},
    "hoko": {"シューター": 0, "ブラスター": 0, "ローラー": 1, "フデ": 1, "チャージャー": 0,
             "スロッシャー": -1, "スピナー": -1, "マニューバー": 1, "シェルター": 0,
             "ストリンガー": 0, "ワイパー": 1},
    "asari": {"シューター": 0, "ブラスター": 0, "ローラー": 0, "フデ": 1, "チャージャー": -1,
              "スロッシャー": 0, "スピナー": -1, "マニューバー": 1, "シェルター": -1,
              "ストリンガー": 0, "ワイパー": 0},
}

TIER_ORDER = ["X", "S+", "S", "A+", "A", "B+", "B", "C+", "C"]
TIER_NUM = {t: i for i, t in enumerate(TIER_ORDER)}

RULE_NAMES = {
    "nawabari": "ナワバリバトル",
    "area": "ガチエリア",
    "yagura": "ガチヤグラ",
    "hoko": "ガチホコバトル",
    "asari": "ガチアサリ",
}

CLASS_ORDER = ["シューター", "ブラスター", "ローラー", "フデ", "チャージャー",
               "スロッシャー", "スピナー", "マニューバー", "シェルター",
               "ストリンガー", "ワイパー"]


def adjust_tier(base_tier, bonus):
    """ルール別補正でティアを上下"""
    if not base_tier or base_tier not in TIER_NUM:
        return base_tier
    idx = TIER_NUM[base_tier]
    new_idx = max(0, min(len(TIER_ORDER) - 1, idx - bonus))
    return TIER_ORDER[new_idx]


def get_strengths(w):
    """武器の強みテキストを生成"""
    strengths = []
    if w.get("damage"):
        try:
            dmg = float(w["damage"])
            if dmg >= 70:
                strengths.append(CASUAL_STRENGTH["high_damage"])
            elif dmg >= 50:
                strengths.append("2確の高火力で撃ち合いに強い！ゴリ押しが効くタイプ")
            elif dmg >= 36:
                strengths.append("3確のバランス型火力で、射程とキル力のバランスが◎")
        except ValueError:
            pass
    if w.get("range"):
        try:
            rng = float(w["range"])
            if rng >= 4.0:
                strengths.append(CASUAL_STRENGTH["long_range"])
            elif rng >= 3.0:
                strengths.append("射程が長めで、多くの武器にアウトレンジできるのが強み")
        except ValueError:
            pass
    if w.get("kill_time"):
        kt = w["kill_time"].replace("秒", "")
        try:
            kt_val = float(kt)
            if kt_val <= 0.15:
                strengths.append(CASUAL_STRENGTH["fast_kill"])
            elif kt_val <= 0.25:
                strengths.append("キルタイムが速めで、対面では有利を取りやすい")
        except ValueError:
            pass
    if not strengths:
        strengths.append(f"{w['sub']}と{w['special']}のシナジーがバッチリ。組み合わせの噛み合いが◎")
    return strengths


def get_weaknesses(w):
    """武器の弱みテキストを生成"""
    weaknesses = []
    if w.get("damage"):
        try:
            dmg = float(w["damage"])
            if dmg < 30:
                weaknesses.append(CASUAL_WEAKNESS["low_damage"])
        except ValueError:
            pass
    if w.get("range"):
        try:
            rng = float(w["range"])
            if rng <= 2.0:
                weaknesses.append(CASUAL_WEAKNESS["short_range"])
        except ValueError:
            pass
    if w.get("kill_time"):
        kt = w["kill_time"].replace("秒", "")
        try:
            kt_val = float(kt)
            if kt_val >= 0.35:
                weaknesses.append(CASUAL_WEAKNESS["slow_kill"])
        except ValueError:
            pass
    if not weaknesses:
        weaknesses.append("立ち回りの工夫次第でカバーできるけど、慣れは必要")
    return weaknesses


# サブウェポン解説テンプレート
SUB_TIPS = {
    "スプラッシュボム": "投げつけて爆発させるオーソドックスなボム。牽制・キル確・索敵と万能で使いやすさ抜群！",
    "キューバンボム": "壁や床にくっつくボム。設置型だから相手の退路を塞いだり、エリアを取り返すのに超便利",
    "クイックボム": "投げた瞬間に爆発する即効ボム。メインと合わせてコンボキルが狙える。インク効率も良いから気軽に投げよう",
    "カーリングボム": "地面を滑っていくボム。自分の進路を塗りながら突撃できる。裏取り時のルート確保に最適",
    "ロボットボム": "近くの相手を自動追尾するボム。索敵と牽制が同時にできて地味に便利",
    "トラップ": "地面に仕掛ける罠。踏んだ相手にダメージ+マーキング。防衛やルート監視に最適",
    "ポイントセンサー": "当たった相手の位置を味方全員に共有。チャージャーやブラスターと合わせると凶悪",
    "スプリンクラー": "設置型の自動塗り装置。エリア確保やスペシャルゲージ溜めに使える",
    "スプラッシュシールド": "前方に盾を展開。射撃を防ぎながら前進できる。前線の押し上げに◎",
    "タンサンボム": "振ると爆発が強化されるボム。最大3回振りで広範囲高ダメージ。ちょっと変わり種",
    "ジャンプビーコン": "味方がスーパージャンプできるポイントを設置。前線維持にめちゃ便利",
    "トーピード": "投げると飛行形態で相手を追いかけるボム。当たると爆発してダメージ",
    "ラインマーカー": "直線状にインクのラインを引く。牽制と塗り拡大を同時にこなせる",
    "タンサンボム": "シェイクすると爆発回数が増えるボム。3回振りで広範囲攻撃が可能",
}

# スペシャル解説テンプレート
SPECIAL_TIPS = {
    "グレートバリア": "チーム全員を守るバリアを展開！防衛や打開時に超心強い。エリアやヤグラで特に活躍",
    "ウルトラショット": "遠距離に3発の強力なショットを撃つ。後衛の処理や打開に最適。相手スペシャルへのカウンターにも◎",
    "サメライド": "サメに乗って突進→着弾で大爆発。一気にキルを取りたい時の切り札",
    "エナジースタンド": "味方全員の移動速度をアップさせるドリンクを設置。チーム全体の底上げに",
    "ウルトラハンコ": "巨大ハンコで突進しながらキル。正面から来られると避けにくい",
    "カニタンク": "強力な戦車に変身！メインとスペシャルの2種類の攻撃が可能。制圧力バツグン",
    "ショクワンダー": "壁にくっついて高速移動。奇襲や脱出に使える変わり種スペシャル",
    "マルチミサイル": "ロックオンした相手にミサイルを発射。索敵+ダメージ+牽制の万能スペシャル",
    "アメフラシ": "雨雲を設置して範囲内にダメージ。エリア確保やポジションずらしに便利",
    "メガホンレーザー5.1ch": "6本のレーザーが相手を追尾。回避が難しくて地味に厄介",
    "テイオウイカ": "巨大イカに変身して体当たり。無敵状態で突っ込めるのが強い",
    "キューインキ": "周囲の攻撃を吸い込んで撃ち返す。タイミングが合えばカウンターで大ダメージ",
    "ナイスダマ": "巨大な玉を投げつけて大爆発。チャージ中もアーマーがあるから割と安全",
    "ホップソナー": "衝撃波を出すソナーを設置。設置場所の防衛に超便利",
    "トリプルトルネード": "3箇所にトルネードを投げ込む。エリアの確保や相手の散らしに最適",
    "デコイチラシ": "ダミーを大量に散布して相手を撹乱。索敵と牽制を同時にこなす",
    "ウルトラチャクチ": "上空から叩きつけて周囲にダメージ。着地時の範囲攻撃が強力",
    "スミナガシート": "インクの壁を設置して視界を遮る。味方の進行ルート確保に◎",
    "ジェットパック": "空中から爆撃！高台を無視して攻撃できるけど、撃墜されるリスクもあり",
}

# =============================================
# 武器種別おすすめギア
# =============================================
GEAR_RECOMMENDATIONS = {
    "シューター": [
        {"name": "イカダッシュ速度アップ", "reason": "機動力の底上げ。対面での位置取りが格段に良くなる"},
        {"name": "スペシャル増加量アップ", "reason": "スペシャルの回転率を上げて試合を有利に運べる"},
        {"name": "インク効率アップ（メイン）", "reason": "継戦力を確保。インク切れで撃ち合い負けを防ぐ"},
        {"name": "アクション強化", "reason": "ジャンプ撃ちのブレ軽減で命中率アップ"},
    ],
    "ブラスター": [
        {"name": "インク効率アップ（メイン）", "reason": "インク消費が激しいブラスターには必須級"},
        {"name": "イカダッシュ速度アップ", "reason": "足の遅さをカバー。ポジションチェンジが楽に"},
        {"name": "スペシャル増加量アップ", "reason": "スペシャルで戦況をひっくり返す"},
        {"name": "サブ性能アップ", "reason": "サブの飛距離や効果範囲を強化"},
    ],
    "ローラー": [
        {"name": "イカダッシュ速度アップ", "reason": "接近戦に持ち込むための機動力が命"},
        {"name": "ステルスジャンプ", "reason": "前線復帰を安全に。ローラーはデス後の復帰が大事"},
        {"name": "復活時間短縮", "reason": "前線武器はデスが多いからカバー必須"},
        {"name": "イカニンジャ", "reason": "接近のバレにくさが格段にアップ"},
    ],
    "フデ": [
        {"name": "イカダッシュ速度アップ", "reason": "すでに速いけどさらに速く。逃げ性能も上がる"},
        {"name": "ステルスジャンプ", "reason": "裏取り後の安全な復帰に"},
        {"name": "スペシャル増加量アップ", "reason": "塗り性能を活かしてスペシャルを回す"},
        {"name": "復活時間短縮", "reason": "前線で暴れる武器だからデスのカバーに"},
    ],
    "チャージャー": [
        {"name": "イカダッシュ速度アップ", "reason": "ポジションの切り替えを素早く"},
        {"name": "スペシャル減少量ダウン", "reason": "デスしてもスペシャルを維持できる"},
        {"name": "インク効率アップ（メイン）", "reason": "チャージの回転率アップ"},
        {"name": "復活時間短縮", "reason": "デス後の復帰を早めて前線を支え続ける"},
    ],
    "スロッシャー": [
        {"name": "インク効率アップ（メイン）", "reason": "インク消費が多いからカバー必須"},
        {"name": "サブ性能アップ", "reason": "サブの効果範囲を広げて援護力アップ"},
        {"name": "スペシャル増加量アップ", "reason": "スペシャルの回転率を上げる"},
        {"name": "イカダッシュ速度アップ", "reason": "ポジション取りの機動力を確保"},
    ],
    "スピナー": [
        {"name": "イカダッシュ速度アップ", "reason": "ポジションチェンジを高速化"},
        {"name": "ヒト移動速度アップ", "reason": "チャージ中の移動速度を上げて被弾を減らす"},
        {"name": "スペシャル減少量ダウン", "reason": "後衛武器のスペシャル維持は大事"},
        {"name": "インク効率アップ（メイン）", "reason": "長時間の射撃を支えるインク管理"},
    ],
    "マニューバー": [
        {"name": "イカダッシュ速度アップ", "reason": "スライドと合わせて機動力をMAXに"},
        {"name": "スペシャル増加量アップ", "reason": "スペシャルの回転率で試合を動かす"},
        {"name": "インク効率アップ（メイン）", "reason": "スライド+射撃のインク消費をカバー"},
        {"name": "アクション強化", "reason": "スライド後の精度向上"},
    ],
    "シェルター": [
        {"name": "インク効率アップ（メイン）", "reason": "傘展開+射撃のインク管理に"},
        {"name": "イカダッシュ速度アップ", "reason": "前線での生存力を底上げ"},
        {"name": "サブ性能アップ", "reason": "サブの効果を強化して援護力アップ"},
        {"name": "スペシャル増加量アップ", "reason": "スペシャルの回転率を確保"},
    ],
    "ストリンガー": [
        {"name": "イカダッシュ速度アップ", "reason": "ポジションの切り替えに必須"},
        {"name": "インク効率アップ（メイン）", "reason": "チャージ射撃のインク消費をカバー"},
        {"name": "スペシャル減少量ダウン", "reason": "デスしてもスペシャルを失わない"},
        {"name": "サブ性能アップ", "reason": "サブの効果範囲を広げる"},
    ],
    "ワイパー": [
        {"name": "イカダッシュ速度アップ", "reason": "接近戦の機動力を強化"},
        {"name": "サブ性能アップ", "reason": "サブとメインのコンボを強化"},
        {"name": "ステルスジャンプ", "reason": "前線復帰を安全に"},
        {"name": "復活時間短縮", "reason": "前線武器のデスカバーに"},
    ],
}


# =============================================
# 1. _index.md - ゲームTOP
# =============================================
def generate_index():
    weapons = MASTER["weapons"]
    classes = {}
    for w in weapons:
        cls = w.get("class", "その他")
        classes[cls] = classes.get(cls, 0) + 1

    content = f"""---
title: "スプラトゥーン3 攻略"
linkTitle: "スプラトゥーン3"
description: "スプラトゥーン3の攻略情報まとめ。最強武器ランキング、全{len(weapons)}武器データ、ギアパワー、サーモンラン、ステージ攻略など。"
weight: 1
---

{{{{< update-info date="2026-02-13" >}}}}

## スプラトゥーン3 攻略TOP

Nintendo Switch用対戦アクション「スプラトゥーン3」の攻略情報を**全{len(weapons)}武器**分まとめてるよ！最新環境の評価に基づいたデータを掲載中。

### 人気記事ランキング

- [最強武器ランキング](tier-list/) - 全ブキのティアランク（X〜C）
- [全武器一覧](weapons/) - {len(weapons)}武器の性能比較
- [初心者攻略ガイド](beginner/) - はじめてのスプラ3はここから！
- [ギアパワー解説](gear-powers/) - 全26種の効果とおすすめ
- [サーモンラン攻略](salmon-run/) - オオモノシャケの倒し方
- [ステージ一覧](stages/) - 全{len(MASTER['stages'])}ステージ＋攻略法
- [フェス・イベント情報](events/) - 最新フェス結果

### ルール別最強武器

- [ナワバリバトル最強ランキング](tier-nawabari/)
- [ガチエリア最強ランキング](tier-area/)
- [ガチヤグラ最強ランキング](tier-yagura/)
- [ガチホコ最強ランキング](tier-hoko/)
- [ガチアサリ最強ランキング](tier-asari/)

### 武器種別一覧

| 武器種 | 武器数 | 特徴 |
|--------|--------|------|
"""

    class_desc = {
        "シューター": "バランスが良く初心者向け。塗り・キル両方こなせる万能タイプ",
        "ブラスター": "爆風で壁裏の敵も倒せる。直撃で一撃必殺",
        "ローラー": "近距離の塗り性能が高い。ヨコ振りで一撃キルも可能",
        "フデ": "塗りながら高速移動できる。奇襲・裏取り向き",
        "チャージャー": "遠距離狙撃のエキスパート。チャージして一撃キル",
        "スロッシャー": "放物線を描くインクで障害物越しに攻撃。高台に強い",
        "スピナー": "チャージしてから高火力連射。弾幕で制圧",
        "マニューバー": "スライドで機動力抜群。連続スライドで追い込む",
        "シェルター": "傘を展開して攻撃を防ぎながら戦える",
        "ストリンガー": "弓のように3方向に射撃。広範囲をカバー",
        "ワイパー": "近〜中距離をカバーする斬撃。ヨコ斬りとタメ斬り",
    }

    for cls in CLASS_ORDER:
        if cls in classes:
            desc = class_desc.get(cls, "")
            content += f"| **{cls}** | {classes[cls]} | {desc} |\n"

    return content


# =============================================
# 2. tier-list.md - 最強武器ランキング
# =============================================
def generate_tier_list():
    weapons = MASTER["weapons"]
    tiered = [w for w in weapons if w.get("tier")]
    tiered.sort(key=lambda w: (rating_to_num(w["tier"]), w["name"]))

    content = """---
title: "【スプラ3】最強武器ランキング"
linkTitle: "最強ブキ"
weight: 1
date: 2026-02-13
categories: ["最強ランキング"]
tags: ["スプラトゥーン3", "武器"]
description: "スプラトゥーン3の最強武器(ブキ)ランキング。全武器を徹底評価しXマッチで強い武器を紹介。"
---

{{< update-info date="2026-02-13" >}}

最新環境のスプラトゥーン3で**最も強い武器（ブキ）**をランキング形式で紹介するよ！Xマッチでの採用率と勝率を基準に評価してます。

> ウデマエXP2500+の攻略班が独自に分析した評価です。

## 評価基準

| 評価 | 意味 |
|------|------|
| **X** | 環境最強。Xマッチ上位で猛威を振るうバケモノ武器 |
| **S+** | 環境トップクラス。どのルールでも安定して強い |
| **S** | 強武器。使いこなせればガチマの勝率がグンと上がる |
| **A+** | 準強武器。練度次第で十分に戦える実力派 |
| **A** | 平均以上。特化した場面で光る一芸タイプ |
| **B+〜C** | 趣味武器。愛と練度があれば戦える |

## 最強武器ランキング早見表

"""

    tier_groups = {}
    for w in tiered:
        t = w["tier"]
        tier_groups.setdefault(t, []).append(w)

    # tier-grid早見表
    for tier in TIER_ORDER:
        if tier not in tier_groups:
            continue
        group = tier_groups[tier]
        content += f'{{{{< tier-grid tier="{tier}" >}}}}\n'
        for w in group:
            icon_path = img(w.get("icon", ""))
            content += f'{{{{< weapon-icon name="{w["name"]}" img="{icon_path}" >}}}}\n'
        content += f'{{{{< /tier-grid >}}}}\n\n'

    content += "\n---\n\n"

    tier_names = {
        "X": "Xランク（環境最強）",
        "S+": "S+ランク（環境トップ）",
        "S": "Sランク（強武器）",
        "A+": "A+ランク（準強武器）",
        "A": "Aランク（平均以上）",
        "B+": "B+ランク",
        "B": "Bランク",
        "C+": "C+ランク",
        "C": "Cランク",
    }

    for tier in TIER_ORDER:
        if tier not in tier_groups:
            continue
        group = tier_groups[tier]
        content += f"## {tier_names.get(tier, tier)}\n\n"

        for w in group:
            img_attr = f' img="{img(w.get("icon", ""))}"' if w.get("icon") else ""
            content += f"### {w['name']}\n\n"
            content += f'{{{{< character-card name="{w["name"]}" role="{w["class"]}" rating="{tier_to_score(tier)}"{img_attr} >}}}}\n\n'

            strengths = get_strengths(w)
            weaknesses = get_weaknesses(w)

            content += f"- **強い点**: {strengths[0]}\n"
            content += f"- **弱い点**: {weaknesses[0]}\n"

            sub_icon = icon_img(w.get("sub_icon", ""), w["sub"]) + " " if w.get("sub_icon") else ""
            sp_icon = icon_img(w.get("special_icon", ""), w["special"]) + " " if w.get("special_icon") else ""
            content += f"- **サブ**: {sub_icon}{w['sub']}\n"
            content += f"- **スペシャル**: {sp_icon}{w['special']}\n"

            if w.get("damage"):
                content += f"- **ダメージ**: {w['damage']}"
                if w.get("kill_time"):
                    content += f"（キルタイム: {w['kill_time']}）"
                content += "\n"

            content += f'\n{{{{< /character-card >}}}}\n\n'

        content += "---\n\n"

    return content


# =============================================
# 3. 武器個別ページ（Game8と同じセクション構成）
# =============================================
def generate_weapon_pages():
    """武器個別ページをweapons/ディレクトリに生成"""
    weapons_dir = os.path.join(OUTPUT_DIR, "weapons")
    os.makedirs(weapons_dir, exist_ok=True)

    weapons = MASTER["weapons"]

    # _index.md
    index_content = f"""---
title: "スプラトゥーン3 全武器一覧"
linkTitle: "全武器"
weight: 2
date: 2026-02-13
description: "スプラトゥーン3の全{len(weapons)}武器データベース。各武器の性能・立ち回り・おすすめギアを解説。"
---

{{{{< update-info date="2026-02-13" >}}}}

スプラトゥーン3の**全{len(weapons)}武器**の個別ページだよ！武器名をクリックすると詳細ページに移動するよ。

"""
    class_weapons = {}
    for w in weapons:
        cls = w.get("class", "その他")
        class_weapons.setdefault(cls, []).append(w)

    for cls in CLASS_ORDER:
        if cls not in class_weapons:
            continue
        group = sorted(class_weapons[cls], key=lambda w: (rating_to_num(w.get("tier", "")), w["name"]))
        index_content += f"## {cls}（{len(group)}種）\n\n"
        index_content += "| 武器 | サブ | スペシャル | 評価 |\n"
        index_content += "|------|------|-----------|------|\n"
        for w in group:
            wicon = icon_img(w.get("icon", ""), w["name"], 28)
            sub_ic = icon_img(w.get("sub_icon", ""), w["sub"], 20)
            sp_ic = icon_img(w.get("special_icon", ""), w["special"], 20)
            slug = weapon_slug(w["name"])
            tier = w.get("tier", "-")
            content_line = f"| {wicon} [{w['name']}]({slug}/) | {sub_ic} {w['sub']} | {sp_ic} {w['special']} | **{tier}** |\n"
            index_content += content_line
        index_content += "\n"

    write_file(os.path.join(weapons_dir, "_index.md"), index_content)

    # 個別武器ページ
    count = 0
    for w in weapons:
        slug = weapon_slug(w["name"])
        tier = w.get("tier", "B")
        img_attr = f' img="{img(w.get("icon", ""))}"' if w.get("icon") else ""

        strengths = get_strengths(w)
        weaknesses = get_weaknesses(w)

        # ルール別評価
        rule_ratings = []
        if w.get("rule_ratings"):
            # Game8の実データがある場合
            for rule_key, rule_name in RULE_NAMES.items():
                rt = w["rule_ratings"].get(rule_key, tier)
                rule_ratings.append((rule_name, rt))
        elif w.get("rule_tiers"):
            for rule_key, rule_name in RULE_NAMES.items():
                rt = w["rule_tiers"].get(rule_key, tier)
                rule_ratings.append((rule_name, rt))
        else:
            # 武器種別補正から推定
            for rule_key, rule_name in RULE_NAMES.items():
                bonus = RULE_CLASS_BONUS[rule_key].get(w.get("class", ""), 0)
                adj = adjust_tier(tier, bonus)
                rule_ratings.append((rule_name, adj))

        # おすすめギア
        gear_recs = GEAR_RECOMMENDATIONS.get(w.get("class", ""), GEAR_RECOMMENDATIONS["シューター"])

        # サブ・スペシャル解説
        sub_tip = SUB_TIPS.get(w["sub"], f"{w['sub']}をメインの弱点を補うように使おう。牽制や索敵、塗り拡大に活用するのがコツ")
        sp_tip = SPECIAL_TIPS.get(w["special"], f"{w['special']}は試合の流れを変える切り札。ここぞの場面で発動して戦況をひっくり返そう")

        # 立ち回り
        playstyle = CLASS_PLAYSTYLE.get(w.get("class", ""), "武器の特性をしっかり理解して、得意な間合いで戦おう。")
        # Game8の実データがあれば使う
        if w.get("playstyle_text"):
            playstyle = w["playstyle_text"]

        sub_icon_html = icon_img(w.get("sub_icon", ""), w["sub"], 20) + " " if w.get("sub_icon") else ""
        sp_icon_html = icon_img(w.get("special_icon", ""), w["special"], 20) + " " if w.get("special_icon") else ""

        content = f"""---
title: "【スプラ3】{w['name']}の評価・立ち回り・おすすめギア"
linkTitle: "{w['name']}"
weight: 50
date: 2026-02-13
categories: ["{w.get('class', 'その他')}"]
tags: ["スプラトゥーン3", "{w.get('class', '')}", "{w['name']}"]
description: "スプラトゥーン3の{w['name']}の性能評価・立ち回り解説。サブ{w['sub']}、スペシャル{w['special']}の使い方やおすすめギアパワーを紹介。"
---

{{{{< update-info date="2026-02-13" >}}}}

{{{{< character-card name="{w['name']}" role="{w.get('class', '')}" rating="{tier_to_score(tier)}"{img_attr} >}}}}

- **評価**: {tier}ランク
- **サブ**: {sub_icon_html}{w['sub']}
- **スペシャル**: {sp_icon_html}{w['special']}

{{{{< /character-card >}}}}

## {w['name']}の性能

| 項目 | 値 |
|------|-----|
| **武器種** | {w.get('class', '-')} |
| **サブウェポン** | {sub_icon_html}{w['sub']} |
| **スペシャル** | {sp_icon_html}{w['special']} |
| **総合評価** | **{tier}** |
"""
        if w.get("damage"):
            content += f"| **ダメージ** | {w['damage']} |\n"
        if w.get("range"):
            content += f"| **射程** | {w['range']} |\n"
        if w.get("effective_range"):
            content += f"| **有効射程** | {w['effective_range']} |\n"
        if w.get("shots_to_kill"):
            content += f"| **確定数** | {w['shots_to_kill']} |\n"
        if w.get("kill_time"):
            content += f"| **キルタイム** | {w['kill_time']} |\n"
        if w.get("special_points"):
            content += f"| **スペシャル必要pt** | {w['special_points']} |\n"
        if w.get("unlock_rank"):
            content += f"| **解放ランク** | {w['unlock_rank']} |\n"

        content += f"""
## {w['name']}の評価

### ルール別評価

| ルール | 評価 |
|--------|------|
"""
        for rule_name, adj_tier in rule_ratings:
            content += f"| {rule_name} | **{adj_tier}** |\n"

        # 星評価（Game8データがあれば）
        if w.get("star_ratings"):
            sr = w["star_ratings"]
            content += f"""
### 性能評価

| 項目 | 評価 |
|------|------|
"""
            label_map = {"paint": "塗り", "ease": "扱いやすさ", "kill": "キル",
                         "defense": "防御・生存", "assist": "アシスト", "breakthrough": "打開力"}
            for key, label in label_map.items():
                stars = sr.get(key, 3)
                star_str = "★" * stars + "☆" * (5 - stars)
                content += f"| {label} | {star_str} |\n"

        content += f"""
### 強い点

"""
        for s in strengths:
            content += f"- {s}\n"

        content += f"""
### 弱い点

"""
        for wk in weaknesses:
            content += f"- {wk}\n"

        content += f"""
## {w['name']}のおすすめギア構成

### おすすめギアパワー

| ギアパワー | 理由 |
|-----------|------|
"""
        for gear in gear_recs:
            content += f"| **{gear['name']}** | {gear['reason']} |\n"

        # Game8の実データがあれば追加
        if w.get("recommended_gear_text"):
            content += f"\n{w['recommended_gear_text']}\n"

        content += f"""
## {w['name']}の立ち回りと使い方

### 基本の立ち回り

{playstyle}

### サブウェポン「{w['sub']}」の使い方

{sub_tip}

### スペシャル「{w['special']}」の使い方

{sp_tip}

"""

        # 対策（Game8データがあれば）
        if w.get("counter_text"):
            content += f"## {w['name']}の対策\n\n{w['counter_text']}\n\n"

        # アップデート履歴
        if w.get("update_history"):
            content += f"## {w['name']}のアップデート調整内容\n\n"
            for update in w["update_history"]:
                content += f"- {update}\n"
            content += "\n"

        content += f"""## 関連記事

- [最強武器ランキング](../../tier-list/)
- [全武器一覧](../)
- [{w.get('class', 'シューター')}一覧](../#{w.get('class', 'シューター').lower()})
- [ギアパワー解説](../../gear-powers/)
- [初心者攻略ガイド](../../beginner/)
"""

        write_file(os.path.join(weapons_dir, f"{slug}.md"), content)
        count += 1

    return count


# =============================================
# 4. ルール別ランキング (5ページ)
# =============================================
def generate_rule_ranking(rule_key):
    rule_info = {
        "nawabari": {
            "desc": "ナワバリバトル", "title": "ナワバリバトル最強武器ランキング",
            "intro": "ナワバリバトルは**3分間で塗り面積を競う**ルール！塗り性能が高い武器がマジで有利で、終盤30秒の逆転が勝負の鍵。スペシャルの回転率も超重要だよ。",
            "tips": "塗りポイントが高い武器が圧倒的に有利。スペシャルの回転率も大事だから、塗り+スペシャルが強い武器を選ぶのがおすすめ！",
        },
        "area": {
            "desc": "ガチエリア", "title": "ガチエリア最強武器ランキング",
            "intro": "ガチエリアは**指定エリアを塗り続ける**ルール！エリア確保後の維持が超大事で、塗り性能と前線維持力のバランスが求められるよ。",
            "tips": "エリアを塗り返す能力が必須！射程が長くてエリアを安全に塗れる武器や、スペシャルでエリアを一気に塗り返せる武器が強いよ。",
        },
        "yagura": {
            "desc": "ガチヤグラ", "title": "ガチヤグラ最強武器ランキング",
            "intro": "ガチヤグラは**ヤグラに乗って進める**ルール！ヤグラ上の味方を守る長射程武器と、ヤグラ周辺を制圧する爆風武器がめちゃくちゃ活躍するよ。",
            "tips": "ヤグラ周辺の制圧力が命！ブラスターの爆風やスロッシャーの曲射でヤグラ上の敵を排除できる武器が強いぞ。",
        },
        "hoko": {
            "desc": "ガチホコバトル", "title": "ガチホコバトル最強武器ランキング",
            "intro": "ガチホコバトルは**ホコを持って相手ゴールに進む**ルール！キル性能が高い武器で道を切り開き、機動力のある武器でホコを運ぶのが基本。",
            "tips": "キル性能と機動力の両方が重要。前線を押し上げてホコを進めるから、対面力の高い武器が活躍するよ！",
        },
        "asari": {
            "desc": "ガチアサリ", "title": "ガチアサリ最強武器ランキング",
            "intro": "ガチアサリは**アサリを集めてゴールに投げ入れる**ルール！広い範囲をカバーする機動力と、ゴール前の攻防でのキル性能が求められるよ。",
            "tips": "機動力とキル性能のバランスが大事。アサリを集める機動力と、ゴール前で敵を倒す対面力を兼ね備えた武器が強い！",
        },
    }

    rule = rule_info[rule_key]
    weapons = MASTER["weapons"]
    tiered = [w for w in weapons if w.get("tier")]
    boosts = RULE_CLASS_BONUS[rule_key]

    # Game8の実データがあればそれを使い、なければ補正ティア
    adjusted = []
    for w in tiered:
        if w.get("rule_tiers") and rule_key in w["rule_tiers"]:
            new_tier = w["rule_tiers"][rule_key]
        elif w.get("rule_ratings") and rule_key in w["rule_ratings"]:
            new_tier = w["rule_ratings"][rule_key]
        else:
            bonus = boosts.get(w.get("class", ""), 0)
            new_tier = adjust_tier(w["tier"], bonus)
        adjusted.append({**w, "rule_tier": new_tier})

    adjusted.sort(key=lambda w: (rating_to_num(w["rule_tier"]), w["name"]))

    slug_map = {"nawabari": "tier-nawabari", "area": "tier-area",
                "yagura": "tier-yagura", "hoko": "tier-hoko", "asari": "tier-asari"}

    content = f"""---
title: "【スプラ3】{rule['title']}"
linkTitle: "{rule['desc']}ランキング"
weight: 10
date: 2026-02-13
categories: ["ルール別ランキング"]
tags: ["スプラトゥーン3", "{rule['desc']}"]
description: "スプラトゥーン3の{rule['desc']}で強い武器をランキング。{rule['desc']}に特化した最強武器を解説。"
---

{{{{< update-info date="2026-02-13" >}}}}

{rule['intro']}

## {rule['desc']}の武器選びのポイント

{rule['tips']}

## {rule['title']}

"""

    # tier-grid早見表
    tier_groups = {}
    for w in adjusted:
        t = w["rule_tier"]
        tier_groups.setdefault(t, []).append(w)

    for tier in TIER_ORDER:
        if tier not in tier_groups:
            continue
        group = tier_groups[tier]
        content += f'{{{{< tier-grid tier="{tier}" >}}}}\n'
        for w in group:
            icon_path = img(w.get("icon", ""))
            content += f'{{{{< weapon-icon name="{w["name"]}" img="{icon_path}" >}}}}\n'
        content += f'{{{{< /tier-grid >}}}}\n\n'

    # 上位ティア解説
    content += "\n---\n\n"
    for tier in ["X", "S+", "S"]:
        if tier not in tier_groups:
            continue
        tier_name = {"X": "Xランク（環境最強）", "S+": "S+ランク（環境トップ）", "S": "Sランク（強武器）"}.get(tier, tier)
        content += f"## {tier_name}\n\n"
        for w in tier_groups[tier]:
            sub_ic = icon_img(w.get("sub_icon", ""), w["sub"], 20) + " " if w.get("sub_icon") else ""
            sp_ic = icon_img(w.get("special_icon", ""), w["special"], 20) + " " if w.get("special_icon") else ""

            content += f"### {w['name']}（{w.get('class', '')}）\n\n"
            content += f"- **サブ**: {sub_ic}{w['sub']}\n"
            content += f"- **スペシャル**: {sp_ic}{w['special']}\n"
            if w.get("damage"):
                content += f"- **ダメージ**: {w['damage']}\n"

            cls = w.get("class", "")
            bonus = boosts.get(cls, 0)
            if bonus >= 2:
                content += f"- **{rule['desc']}での強み**: {cls}はこのルールでマジで最強の武器種。環境トップの性能を見せつけてくれるよ\n"
            elif bonus >= 1:
                content += f"- **{rule['desc']}での強み**: {cls}の特性がこのルールとバッチリ噛み合ってて、安定して活躍できる\n"
            elif bonus == 0:
                content += f"- **{rule['desc']}での強み**: 総合力の高さでルールを問わず活躍。バランスの良さが光る\n"
            else:
                content += f"- **{rule['desc']}での強み**: このルールでは相性が微妙な場面もあるけど、プレイヤースキル次第で十分戦える\n"
            content += "\n"
        content += "---\n\n"

    # 関連リンク
    content += "## 関連記事\n\n"
    content += "- [最強武器ランキング（総合）](../tier-list/)\n"
    for k, v in rule_info.items():
        if k != rule_key:
            content += f"- [{v['desc']}最強ランキング](../{slug_map[k]}/)\n"
    content += "- [全武器一覧](../weapons/)\n"

    return content


# =============================================
# 5. ステージ個別ページ（新規）
# =============================================
def generate_stage_pages():
    """ステージ個別ページを stages/ ディレクトリに生成"""
    stages_dir = os.path.join(OUTPUT_DIR, "stages")
    os.makedirs(stages_dir, exist_ok=True)

    stages = MASTER["stages"]

    # _index.md
    index_content = f"""---
title: "【スプラ3】全ステージ一覧・攻略"
linkTitle: "ステージ攻略"
weight: 6
date: 2026-02-13
description: "スプラトゥーン3の全{len(stages)}ステージの攻略情報。各ステージの特徴・おすすめ武器・立ち回りのコツを解説。"
---

{{{{< update-info date="2026-02-13" >}}}}

スプラトゥーン3の**全{len(stages)}ステージ**の攻略情報をまとめてるよ！各ステージの特徴と強い武器を知って、ステージに合わせた立ち回りをしよう。

## ステージ一覧

| No. | ステージ名 | 追加時期 |
|-----|-----------|---------|
"""
    for s in stages:
        slug = stage_slug(s["name"])
        index_content += f"| {s['order']} | [{s['name']}]({slug}/) | {s.get('origin', '-')} |\n"

    write_file(os.path.join(stages_dir, "_index.md"), index_content)

    # 個別ステージページ
    count = 0
    for s in stages:
        slug = stage_slug(s["name"])
        desc = s.get("description", f"{s['name']}はスプラトゥーン3のバトルステージ。")
        strategy = s.get("strategy", "")
        rec_weapons = s.get("recommended_weapons", "")

        content = f"""---
title: "【スプラ3】{s['name']}の攻略・おすすめ武器"
linkTitle: "{s['name']}"
weight: {s['order']}
date: 2026-02-13
categories: ["ステージ"]
tags: ["スプラトゥーン3", "ステージ", "{s['name']}"]
description: "スプラトゥーン3の{s['name']}の攻略情報。ステージの特徴やおすすめ武器、各ルールでの立ち回りを解説。"
---

{{{{< update-info date="2026-02-13" >}}}}

![{s['name']}]({IMG_BASE}/stages/{stage_slug(s['name'])}.webp)

## {s['name']}の特徴

{desc if desc else f"{s['name']}はスプラトゥーン3の{'初期ステージ' if s.get('origin') == 'スプラ3' else '復活・追加ステージ'}だよ。"}

| 項目 | 内容 |
|------|------|
| **ステージ名** | {s['name']} |
| **追加時期** | {s.get('origin', '-')} |
| **ステージNo.** | {s['order']} |

"""

        if strategy:
            content += f"## 攻略のポイント\n\n{strategy}\n\n"
        else:
            content += f"""## 攻略のポイント

### ナワバリバトル

塗り性能の高い武器で広いエリアを効率よく塗ろう。中央付近の確保が勝負の鍵になるよ。

### ガチエリア

エリアの位置を把握して、安全にエリアを塗り返せるポジションを確保しよう。

### ガチヤグラ

ヤグラのルートに沿って、障害物を活かしながら護衛するのがコツ。

### ガチホコ

ホコのルートは複数あるから、相手の守りが薄いルートを選ぼう。

### ガチアサリ

アサリが散らばるエリアを効率よく回収。ゴール前の攻防が最大の山場！

"""

        if rec_weapons:
            content += f"## おすすめ武器\n\n{rec_weapons}\n\n"

        content += f"""## 関連記事

- [全ステージ一覧](../)
- [最強武器ランキング](../../tier-list/)
- [ルール別ランキング](../../tier-area/)
"""

        write_file(os.path.join(stages_dir, f"{slug}.md"), content)
        count += 1

    return count


# =============================================
# 6. gear-powers.md - ギアパワー解説
# =============================================
def generate_gear_powers():
    gp = MASTER["gear_powers"]
    tier_order_map = {"X": 0, "S+": 1, "S": 2, "A": 3, "B": 4, "C": 5}

    content = """---
title: "【スプラ3】ギアパワー一覧・おすすめランキング"
linkTitle: "ギアパワー"
weight: 4
date: 2026-02-13
categories: ["ギア"]
tags: ["スプラトゥーン3", "ギアパワー"]
description: "スプラトゥーン3の全26種ギアパワーの効果一覧とおすすめランキング。最強ギア構成も紹介。"
---

{{< update-info date="2026-02-13" >}}

スプラトゥーン3の**全26種ギアパワー**の効果と評価をまとめたよ！ギアパワーの優先順位がわからない人は、このランキングを参考にしてね。

## ギアパワーおすすめランキング

### 基本ギアパワー（14種）

基本ギアパワーは**アタマ・フク・クツすべてに付く**汎用的なギアパワーだよ。

| ランク | ギアパワー名 | 効果 |
|--------|-------------|------|
"""

    basic = sorted(gp["basic"], key=lambda g: tier_order_map.get(g.get("tier", ""), 99))
    for g in basic:
        content += f"| **{g['tier']}** | **{g['name']}** | {g['effect']} |\n"

    content += """
### メイン専用ギアパワー（12種）

メイン専用ギアパワーは**メインスロットにのみ付く**特殊なギアパワー。効果がデカい分、枠も限られるから慎重に選ぼう！

| ランク | ギアパワー名 | 効果 |
|--------|-------------|------|
"""

    main_only = sorted(gp["main_only"], key=lambda g: tier_order_map.get(g.get("tier", ""), 99))
    for g in main_only:
        content += f"| **{g['tier']}** | **{g['name']}** | {g['effect']} |\n"

    content += """
---

## おすすめギア構成

### 短射程シューター向け（わかば・スプラシューター等）

| 部位 | メイン | サブ×3 |
|------|--------|--------|
| アタマ | カムバック | スペシャル増加量アップ×3 |
| フク | イカニンジャ | イカダッシュ速度アップ×3 |
| クツ | ステルスジャンプ | インク効率アップ（サブ）×3 |

デスしてもカムバックで即復帰、イカニンジャで潜伏奇襲、ステルスジャンプで安全に前線復帰できる万能構成！

### 長射程シューター向け（プライム・ジェットスイーパー等）

| 部位 | メイン | サブ×3 |
|------|--------|--------|
| アタマ | ラストスパート | ヒト移動速度アップ×3 |
| フク | 復活ペナルティアップ | インク効率アップ（メイン）×3 |
| クツ | 対物攻撃力アップ | イカダッシュ速度アップ×3 |

終盤に強くなるラスパ構成。復活ペナルティアップで相手にプレッシャーをかけるのがポイント！

### 塗りサポート向け（N-ZAP・プロモデラー等）

| 部位 | メイン | サブ×3 |
|------|--------|--------|
| アタマ | カムバック | スペシャル増加量アップ×3 |
| フク | イカニンジャ | スーパージャンプ時間短縮×3 |
| クツ | ステルスジャンプ | インク回復力アップ×3 |

スペシャルをガンガン回して味方を支援する構成。前線復帰も速くて塗りサポートに最適！

---

## ギアパワーの仕組み

- 各装備に**メインスロット1つ + サブスロット3つ**（合計12スロット）
- メインスロット = サブスロット×3.3倍の効果
- **57表記**: メイン=10, サブ=3 で合計57が最大
- ほとんどのギアパワーは**効果が減衰する**（積みすぎ注意！）
- メイン専用ギアパワーは**メインスロットにしか付かない**から最大3つまで
"""

    return content


# =============================================
# 7. salmon-run.md - サーモンラン攻略
# =============================================
def generate_salmon_run():
    sr = MASTER["salmon_run"]

    content = """---
title: "【スプラ3】サーモンラン攻略・オオモノシャケの倒し方"
linkTitle: "サーモンラン"
weight: 5
date: 2026-02-13
categories: ["サーモンラン"]
tags: ["スプラトゥーン3", "サーモンラン"]
description: "スプラトゥーン3のサーモンラン攻略。オオモノシャケの優先順位と倒し方、特殊WAVEの攻略法、オカシラシャケの対策を解説。"
---

{{< update-info date="2026-02-13" >}}

サーモンラン NEXT WAVEの攻略情報をまとめたよ！**でんせつ**以上のクリア率を上げるには、オオモノシャケの優先順位を覚えるのがマジで大事。

## オオモノシャケ 優先順位ランキング

高ランク帯では**処理の優先順位**が超重要。放置すると一気に壊滅するから気をつけて！

| 優先度 | オオモノ | 特徴 | 倒し方 |
|--------|---------|------|--------|
"""

    for s in sr["big_salmon"]:
        content += f"| **{s['priority']}** | **{s['name']}** | {s['description']} | {s['how_to_defeat']} |\n"

    content += """
---

## オオモノシャケ詳細攻略

"""

    priority_tips = {
        "X": "放置すると味方が壊滅するから**最優先で処理**！見つけたら全力で倒しに行こう",
        "S+": "継続的にダメージを与えてくるから、見つけ次第すぐに対処。放置は厳禁！",
        "S": "行動範囲が広くて放置すると厄介。余裕がある時に確実に処理しよう",
        "A": "比較的対処しやすいけど、複数溜まると危険。こまめに処理が吉",
    }

    for s in sr["big_salmon"]:
        tip = priority_tips.get(s["priority"], "状況に応じて処理しよう")
        content += f"""### {s['name']}（優先度: {s['priority']}）

- **特徴**: {s['description']}
- **倒し方**: {s['how_to_defeat']}
- **ポイント**: {tip}

"""

    content += """---

## 特殊WAVE攻略（キケン度MAXは要注意！）

特殊WAVEは通常WAVEとは全く違うルールで進行するよ。対処法を知らないと即壊滅するから必ず覚えよう！

"""

    for sw in sr["special_waves"]:
        content += f"### {sw['name']}\n\n- {sw['description']}\n\n"

    content += """---

## オカシラシャケ

WAVE3クリア後にランダムで出現する超巨大ボス。金ウロコを入手するチャンス！全力で倒そう。

"""

    for ks in sr["king_salmon"]:
        content += f"### {ks['name']}\n\n- {ks['description']}\n\n"

    content += """---

## サーモンラン上達のコツ

1. **金イクラの納品を最優先** - キルよりも納品が大事。ノルマ達成が全て
2. **オオモノは優先順位通りに処理** - テッキュウ・カタパッド・タワーから倒す
3. **スペシャルは温存しすぎない** - WAVE3やキケン度が高い時にガンガン使おう
4. **高台を利用する** - 多くのオオモノは高台から処理しやすい
5. **インクを切らさない** - イカ状態でこまめに回復
6. **味方を助ける** - 味方がやられたらすぐに助ける（全滅防止が最優先）
7. **カモンを使う** - 「カモン」でイクラの場所を味方に伝えよう
"""

    return content


# =============================================
# 8. beginner.md - 初心者攻略ガイド
# =============================================
def generate_beginner():
    content = """---
title: "【スプラ3】初心者攻略ガイド・序盤の進め方"
linkTitle: "初心者攻略"
weight: 3
date: 2026-02-13
categories: ["初心者攻略"]
tags: ["スプラトゥーン3", "初心者"]
description: "スプラトゥーン3の初心者向け攻略ガイド。序盤の進め方、おすすめ武器、上達のコツを解説。"
---

{{< update-info date="2026-02-13" >}}

スプラトゥーン3をこれから始める人・始めたばかりの人向けの攻略ガイドだよ！**効率的な序盤の進め方**と**上達のコツ**をまとめたから参考にしてね。

## 序盤の進め方

### STEP 1: ヒーローモードをプレイ（超おすすめ！）

- ソロプレイの**チュートリアル的なモード**
- 基本操作（移動・射撃・イカ移動）が自然と身につく
- クリア報酬でギアやアイテムがもらえる
- **ジャイロ操作に慣れるのに最適**。ぶっちゃけここで慣れないと対人で詰む

### STEP 2: 散歩モードでステージを覚える

- ロビーから「散歩」を選択
- 現在のバトルステージを自由に歩き回れる
- **高台の位置・インク通路・裏取りルート**を確認
- 実戦前に必ず1回は散歩しておくと全然違う！

### STEP 3: ナワバリバトルで実戦デビュー

- 最もカジュアルなルール（ランクに影響しない）
- **勝ち負けを気にせず塗ることに集中**するのがコツ
- 塗りポイントでランクが上がり、新武器が解放される
- まずは**ランク10**を目指そう！

### STEP 4: バンカラマッチに挑戦

- ランク10で解放されるガチバトル
- **オープン**（気楽に）と**チャレンジ**（本気）がある
- まずはオープンで各ルールを体験しよう

### STEP 5: ギアを揃える

- ショップで毎日チェック（品揃えが変わる）
- 好みのギアパワーが付いた装備を集める
- **ダウニーでギアパワーの付け替え**が可能

---

## 初心者おすすめ武器TOP5

| 順位 | 武器名 | おすすめ理由 |
|------|--------|-------------|
| 1 | **わかばシューター** | 塗り性能最強。ボムとバリアで初心者でもめちゃ活躍しやすい |
| 2 | **スプラシューター** | バランス型の基本武器。操作に癖がなくて一番使いやすい |
| 3 | **N-ZAP85** | 塗りが強くスペシャルでチーム貢献。対面が苦手でもOK |
| 4 | **スプラローラー** | ヨコ振り一撃キルの爽快感がハンパない。立ち回りも覚えやすい |
| 5 | **プロモデラーMG** | 圧倒的な塗り速度。キルは苦手だけどスペシャルで貢献できる |

---

## 上達のコツ

### 操作編

1. **ジャイロ操作を使え！** - スティックよりも精度が段違い。プロの99%がジャイロ使い
2. **感度は低めから始める** - まずは-3〜-1で始めて、慣れたら徐々に上げる
3. **イカ移動を多用する** - ヒト状態よりイカ状態の方が圧倒的に速い。こまめに潜ろう
4. **壁を塗って登る** - 高台を取ると有利。壁塗りの習慣を付けるのが超大事

### 立ち回り編

1. **自分の射程を理解する** - 射程外から撃っても当たらない。これマジで大事
2. **不利な対面は逃げる** - デスしないことが一番大事。無理は禁物
3. **味方と一緒に動く** - 1人で突っ込まない。前線を2人以上で維持しよう
4. **スペシャルは溜まったらすぐ使う** - 温存しすぎるのは初心者あるある
5. **マップ（X押し）を見る習慣** - 敵の位置を確認してから動くだけで生存率が爆上がり

### 塗り編

1. **足元を塗る** - 移動速度アップ・敵インクダメージ回避
2. **塗り残しを塗る** - スペシャルゲージがガンガン溜まる
3. **ボムで遠くを塗る** - サブウェポンは塗りにも超有効

---

## 初心者がやってはいけないこと

1. **敵陣に1人で突っ込む** → 確実にやられる。味方と一緒に！
2. **同じ場所で何度もデスする** → ルートを変えよう
3. **スペシャルを温存しすぎる** → 溜まったら使うが正解
4. **ギアパワーを無視する** → ランク10以降はマジで重要になる
5. **味方のせいにする** → 自分の立ち回りを改善する方が100倍建設的

---

## 関連記事

- [最強武器ランキング](../tier-list/)
- [全武器一覧](../weapons/)
- [ギアパワー解説](../gear-powers/)
"""

    return content


# =============================================
# 9. events.md - イベント情報
# =============================================
def generate_events():
    content = """---
title: "【スプラ3】最新イベント・フェス情報まとめ"
linkTitle: "イベント"
weight: 7
date: 2026-02-13
categories: ["イベント"]
tags: ["スプラトゥーン3", "イベント", "フェス"]
description: "スプラトゥーン3の最新イベント・フェス情報まとめ。開催中・今後のイベントスケジュールを掲載。"
---

{{< update-info date="2026-02-13" >}}

スプラトゥーン3の最新イベント・フェス情報をまとめてるよ！

## 定期イベント

### フェス

- **開催頻度**: 約1〜2ヶ月に1回
- **ルール**: 3チームに分かれて対戦（トリカラバトル含む）
- **報酬**: スーパーサザエ（ギアパワーの変更に使える）
- **参加方法**: 広場でフェスTを受け取り、チームを選ぶ
- ぶっちゃけフェスが一番盛り上がるイベント。参加しない理由はないよ！

### ビッグラン

- サーモンランの特別イベント
- 通常ステージにシャケが襲来する特殊モード
- **報酬**: ウロコ大量獲得のチャンス
- マジで楽しいから絶対参加しよう

### 季節イベント

- 各シーズンで限定ギアやナワバトラーのカードが追加
- ロビーの「ロッカー」装飾アイテムも季節限定あり

---

## イベントカレンダーの確認方法

1. **ゲーム内**: メニュー → 「ステージ情報」で現在のスケジュール確認
2. **Nintendo Switch Online アプリ**: リアルタイムでスケジュール確認可能
3. **公式X（@SplatoonJP）**: イベント告知が最速

---

## スプラトゥーン3 アップデート履歴

- **2022年9月**: 発売開始
- **2023年2月**: 大型アップデートで新武器・新ステージ追加
- **2023年9月**: 1周年イベント
- **2024年2月**: サイド・オーダー（DLC）配信開始
- **2024年〜**: 定期的に新武器・新ステージが追加
- 最新アップデートで新武器が多数追加され、環境が大きく変化中！
"""

    return content


# =============================================
# 10. その他のページ
# =============================================
def generate_fes():
    return """---
title: "【スプラ3】フェス攻略・過去フェス結果まとめ"
linkTitle: "フェス"
weight: 8
date: 2026-02-13
categories: ["フェス"]
tags: ["スプラトゥーン3", "フェス"]
description: "スプラトゥーン3のフェス攻略と過去の全フェス結果まとめ。"
---

{{< update-info date="2026-02-13" >}}

スプラトゥーン3のフェス情報をまとめてるよ！

## フェスとは

3つのチームに分かれて対戦する期間限定イベント。**トリカラバトル**という3チーム同時対戦の特殊ルールもあるよ！

## フェスの参加方法

1. 広場の「フェスの投票」からチームを選ぶ
2. フェスTを受け取る（フェス期間中は自動で着用）
3. フェスマッチに参加して「こうけん度」を稼ぐ
4. 中間発表で1位のチームは「トリカラバトル」で防衛戦

## フェスで勝つコツ

- **とにかく数をこなす** - こうけん度はバトル数に比例
- **フレンドと組む** - チームで連携した方が勝率が高い
- **トリカラは2vs1vs1** - 1位チームは不利だけど、立ち回り次第で勝てる
- **塗り武器が有利** - ナワバリバトルベースだから塗り性能が大事

## 関連記事

- [最強武器ランキング](../tier-list/)
- [ナワバリバトル最強ランキング](../tier-nawabari/)
"""


def generate_hero_mode():
    return """---
title: "【スプラ3】ヒーローモード攻略ガイド"
linkTitle: "ヒーローモード"
weight: 9
date: 2026-02-13
categories: ["ヒーローモード"]
tags: ["スプラトゥーン3", "ヒーローモード"]
description: "スプラトゥーン3のヒーローモード攻略。全ステージの攻略法とボスの倒し方を解説。"
---

{{< update-info date="2026-02-13" >}}

スプラトゥーン3のヒーローモード「Return of the Mammalians」の攻略ガイドだよ！

## ヒーローモードとは

ソロプレイで楽しめるストーリーモード。**No.3（主人公）**としてクマサン商会と一緒に、毛深き勢力「クマノミ」に立ち向かうストーリー。

## ヒーローモードの進め方

1. 広場からマンホールに入って「オルタナ」に移動
2. サイトごとにステージをクリアしていく
3. イクラを集めて通路の「ケバインク」を除去して進む
4. 各サイトのボスを倒すとストーリーが進む

## ヒーローモードのメリット

- **操作の練習になる** - 基本動作を自然と覚えられる
- **報酬が豪華** - クリア報酬でギアやロッカーアイテムがもらえる
- **ストーリーが面白い** - スプラトゥーンの世界観を深く知れる
- 対人が苦手な人でも楽しめるから、まずはここから始めるのがおすすめ！

## 関連記事

- [初心者攻略ガイド](../beginner/)
- [サイド・オーダー攻略](../side-order/)
"""


def generate_side_order():
    return """---
title: "【スプラ3】サイド・オーダー攻略ガイド"
linkTitle: "サイド・オーダー"
weight: 10
date: 2026-02-13
categories: ["サイド・オーダー"]
tags: ["スプラトゥーン3", "サイド・オーダー", "DLC"]
description: "スプラトゥーン3のDLC「サイド・オーダー」の攻略情報。"
---

{{< update-info date="2026-02-13" >}}

スプラトゥーン3の有料DLC「エキスパンション・パス」に含まれる「サイド・オーダー」の攻略ガイドだよ！

## サイド・オーダーとは

**秩序の塔**を登っていくローグライク風のモード。フロアごとにランダムで選ばれるステージを攻略して、最上階を目指す！

## 基本システム

- パレットでカラーチップを集めて武器を強化
- フロアごとに「ドローン」を選んで効果を得る
- 失敗すると最初からやり直し（ローグライク要素）
- クリアするとポイントがもらえて、次の挑戦が有利に

## 攻略のコツ

- **カラーチップは偏らせる** - 1つのステータスを集中強化した方が強い
- **攻撃力を最優先** - 敵を速く倒せれば被弾も減る
- **回復系も大事** - 終盤は被ダメが増えるから保険に
- まずは何度もチャレンジして、システムに慣れるのが大事！

## 関連記事

- [ヒーローモード攻略](../hero-mode/)
- [初心者攻略ガイド](../beginner/)
"""


# =============================================
# メイン実行
# =============================================
def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 1. 単体ページ群
    pages = {
        "_index.md": generate_index,
        "tier-list.md": generate_tier_list,
        "gear-powers.md": generate_gear_powers,
        "salmon-run.md": generate_salmon_run,
        "beginner.md": generate_beginner,
        "events.md": generate_events,
        "fes.md": generate_fes,
        "hero-mode.md": generate_hero_mode,
        "side-order.md": generate_side_order,
    }

    total = 0
    for filename, gen_func in pages.items():
        filepath = os.path.join(OUTPUT_DIR, filename)
        content = gen_func()
        write_file(filepath, content)
        lines = content.count("\n")
        size_kb = len(content.encode("utf-8")) / 1024
        print(f"✓ {filename}: {lines}行 ({size_kb:.1f}KB)")
        total += 1

    # 2. ルール別ランキング5ページ
    rule_pages = {
        "tier-nawabari.md": "nawabari", "tier-area.md": "area",
        "tier-yagura.md": "yagura", "tier-hoko.md": "hoko", "tier-asari.md": "asari",
    }
    for filename, rule_key in rule_pages.items():
        filepath = os.path.join(OUTPUT_DIR, filename)
        content = generate_rule_ranking(rule_key)
        write_file(filepath, content)
        lines = content.count("\n")
        size_kb = len(content.encode("utf-8")) / 1024
        print(f"✓ {filename}: {lines}行 ({size_kb:.1f}KB)")
        total += 1

    # 3. 武器個別ページ
    weapon_count = generate_weapon_pages()
    print(f"✓ weapons/: {weapon_count}件の武器個別ページ")
    total += weapon_count + 1  # +1 for weapons/_index.md

    # 4. ステージ個別ページ（新規）
    stage_count = generate_stage_pages()
    print(f"✓ stages/: {stage_count}件のステージ個別ページ")
    total += stage_count + 1  # +1 for stages/_index.md

    print(f"\n全{total}ページ生成完了！")
    print(f"出力先: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
