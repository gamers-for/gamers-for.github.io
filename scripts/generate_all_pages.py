#!/usr/bin/env python3
"""
マスターJSONから全Hugoコンテンツページを自動生成するスクリプト
全ページをraw HTMLで出力し、攻略サイトと同じセクション順序・テーブル構造で生成
アイコンはテーブル内にそのまま配置、文章はオリジナル（カジュアル口調）
"""

import json
import os
import re
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
CONTENT_DIR = os.path.join(BASE_DIR, "content", "games", "splatoon3")
IMG_BASE = "/gamers-for/images/games/splatoon3"

OUTPUT_DIR = CONTENT_DIR

# マスターデータ読み込み
with open(os.path.join(DATA_DIR, "splatoon3_master.json"), "r", encoding="utf-8") as f:
    MASTER = json.load(f)

# =============================================
# 定数・設定
# =============================================
TIER_ORDER = ["X", "S+", "S", "A+", "A", "B+", "B", "C+", "C"]
TIER_NUM = {t: i for i, t in enumerate(TIER_ORDER)}

TIER_IMG_MAP = {
    "S+": "splus", "S": "s", "A+": "aplus", "A": "a",
    "B+": "bplus", "B": "b", "C+": "cplus", "C": "c",
}

RULE_NAMES = {
    "nawabari": "ナワバリバトル",
    "area": "ガチエリア",
    "yagura": "ガチヤグラ",
    "hoko": "ガチホコバトル",
    "asari": "ガチアサリ",
}

CLASS_ORDER = [
    "シューター", "ブラスター", "ローラー", "フデ", "チャージャー",
    "スロッシャー", "スピナー", "マニューバー", "シェルター",
    "ストリンガー", "ワイパー",
]

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

# 武器種別おすすめギア
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

# 武器種別の立ち回り解説（フォールバック用）
CLASS_PLAYSTYLE = {
    "シューター": "シューターの基本は中距離で相手をしっかりキルすること。自分の射程をちゃんと把握して、有利な間合いで戦うのが超大事！塗りもキルもバランスよくこなせるのがシューターの強みだから、味方のカバーをしつつ前線を上げていこう。",
    "ブラスター": "ブラスターは爆風を使って壁裏の相手もキルできるのが最大の強み！直撃を当てれば一撃で倒せるから、エイム力があればめちゃくちゃ強い。ただし連射が遅いから、外すと一気にピンチになる。",
    "ローラー": "ローラーは潜伏からの奇襲が命。ヨコ振りで一撃キルを狙うのが基本で、相手の位置をしっかり把握してから仕掛けるのが大事。正面から突っ込むのはNG。",
    "フデ": "フデの強みは圧倒的な機動力。塗りながら超高速で移動できるから、裏取りや奇襲がめちゃくちゃ得意！前線を荒らして相手の注意を引きつけよう。",
    "チャージャー": "チャージャーは後方から味方をサポートする狙撃手。高台を確保して、相手の前線を下げさせるのが仕事。存在自体がめっちゃ強い。",
    "スロッシャー": "スロッシャーは放物線を描くインクで障害物越しに攻撃できるのがめちゃ強い。高台から降ってくるインクは避けにくいから、地形を活かした戦い方が基本！",
    "スピナー": "スピナーはチャージ後の連射火力が圧倒的。弾幕を張って相手を制圧するのが基本で、ポジションを取ってからの撃ち合いがめちゃくちゃ強い！",
    "マニューバー": "マニューバーはスライドを使った機動力が最大の武器！スライド後は集弾率が上がるから、スライドしながらキルを取るのが基本。",
    "シェルター": "シェルターは傘を展開して攻撃を防ぎながら戦える唯一の武器種。味方の盾になれるのがめちゃくちゃ強い！",
    "ストリンガー": "ストリンガーは3方向に同時射撃できるのが特徴。広範囲をカバーできるから、索敵と牽制が得意！",
    "ワイパー": "ワイパーはヨコ斬りとタメ斬りの使い分けが命。ヨコ斬りは近距離の広範囲、タメ斬りは遠距離の高ダメージと、2つの攻撃を状況で切り替えるのが基本！",
}

# 強み・弱みテンプレート
CASUAL_STRENGTH = {
    "high_damage": "火力がマジでエグい！一撃で相手を溶かせるのが最大の武器",
    "long_range": "射程がめちゃくちゃ長くて、安全な距離からガンガン撃てるのが強み",
    "fast_kill": "キルタイムが超速いから、対面で先手を取れればほぼ勝てる",
    "good_paint": "塗り性能が高くてスペシャルがガンガン溜まるのが嬉しいポイント",
    "versatile": "塗り・キル・アシスト何でもこなせる万能タイプ",
}

CASUAL_WEAKNESS = {
    "low_damage": "ダメージが低めだから、確定数が多くて撃ち合いは苦手かも",
    "short_range": "射程が短いから、長射程武器にはアウトレンジされがち",
    "slow_kill": "キルタイムが遅めなので、真正面からの撃ち合いはちょっと厳しい",
    "hard_to_use": "操作が結構ムズいから、使いこなすまでに練習が必要",
}

# サブウェポン別の強み（武器と組み合わせて使う）
SUB_STRENGTHS = {
    "スプラッシュボム": "スプラッシュボムでキルもクリアリングもこなせる。汎用性が高く、投げ得な場面が多い",
    "キューバンボム": "キューバンボムの固定力が優秀。エリア管理やヤグラ上の相手を退かすのに効果的",
    "クイックボム": "クイックボムで素早くダメージを入れられる。メインとのコンボで対面力が大幅アップ",
    "カーリングボム": "カーリングボムで道を作りながら素早く前線に行ける。奇襲ルートの開拓が得意",
    "ロボットボム": "ロボットボムが敵を追尾して索敵＆牽制。相手の位置が把握しやすくなる",
    "トラップ": "トラップで裏取りを防げる。センサー効果で敵の接近がバレバレに",
    "ポイントセンサー": "ポイントセンサーで敵の位置を味方全員に共有。索敵能力がピカイチ",
    "スプラッシュシールド": "スプラッシュシールドで撃ち合いを有利に。シールド越しに一方的に攻撃できる場面が強い",
    "スプリンクラー": "スプリンクラーで自動的に塗りが広がる。スペシャルの溜まりが早くなるのがGood",
    "タンサンボム": "タンサンボムは振れば振るほど爆発回数が増える。塗りにもキルにも使える万能ボム",
    "ジャンプビーコン": "ジャンプビーコンで味方の前線復帰をサポート。チーム全体の機動力が上がる",
    "トーピード": "トーピードは索敵しながら遠くの相手にもダメージを入れられる。追撃性能が高い",
    "ポイズンミスト": "ポイズンミストで相手の動きを鈍くできる。エリア管理や逃げる相手の足止めに有効",
    "ラインマーカー": "ラインマーカーで着弾点の相手をマーキング。壁越しでも位置がバレバレになる",
}

# サブウェポン別の弱み
SUB_WEAKNESSES = {
    "スプラッシュボム": "スプラッシュボムのインク消費が重く、ボム後のインク管理に注意が必要",
    "キューバンボム": "キューバンボムはインク消費70%とかなり重い。連投するとインク切れしやすい",
    "ロボットボム": "ロボットボムは追尾が遅くて直接キルを取りにくい。牽制向きでキル性能は低め",
    "トラップ": "トラップは設置型で即効性がない。能動的な攻めには向かないサブ",
    "ポイントセンサー": "ポイントセンサー自体にダメージがなく、直接的な火力補助にはならない",
    "スプラッシュシールド": "スプラッシュシールドは設置場所を間違えると効果が薄い。置き場の判断が重要",
    "スプリンクラー": "スプリンクラーは戦闘中のサポート力が弱め。対面の強化には直接繋がりにくい",
    "ジャンプビーコン": "ジャンプビーコンは自分の戦闘力アップには貢献しない。サポート特化型のサブ",
    "ポイズンミスト": "ポイズンミストはダメージ判定がなく、相手が避ければ効果が薄い",
}

# スペシャル別の強み
SPECIAL_STRENGTHS = {
    "ウルトラショット": "ウルトラショットで遠くの敵を確実に仕留められる。打開時の切り札として超優秀",
    "ナイスダマ": "ナイスダマの圧倒的な範囲と火力で打開力バツグン。発動中のアーマーで生存もできる",
    "カニタンク": "カニタンクに変身すると高火力＋高耐久で無双できる。打開時のエース性能が光る",
    "ウルトラチャクチ": "ウルトラチャクチで至近距離の敵を一網打尽。接近戦の切り札として心強い",
    "メガホンレーザー5.1ch": "メガホンレーザー5.1chが広範囲をカバー。牽制・キル・エリア管理なんでもこなせる",
    "ジェットパック": "ジェットパックで空中から一方的に攻撃できる。地上の敵には圧倒的に有利",
    "グレートバリア": "グレートバリアで味方ごとバリアに入れる。チームの拠点確保がめちゃくちゃ安定する",
    "エナジースタンド": "エナジースタンドでチーム全員を強化。復活短縮＋インク回復で味方全体の継戦力UP",
    "ホップソナー": "ホップソナーで広範囲の索敵＋ダメージ。設置するだけでエリア制圧力が上がる",
    "テイオウイカ": "テイオウイカの突進で高速キルを狙える。打開時の奇襲性能がピカイチ",
    "トリプルトルネード": "トリプルトルネードで3箇所同時に攻撃。エリア管理や敵の分断に効果的",
    "アメフラシ": "アメフラシで広範囲に継続ダメージ。じわじわ敵の行動範囲を狭められる",
    "サメライド": "サメライドの突進＋爆発で一気に距離を詰めてキルが取れる。意表をつく奇襲が強い",
    "ウルトラハンコ": "ウルトラハンコの連続攻撃で前線を強引にこじ開けられる。投げ飛ばしも超強力",
    "キューインキ": "キューインキで敵のインクを吸い込んで跳ね返せる。防御と攻撃を同時にこなす",
    "デコイチラシ": "デコイチラシで相手のセンサーを撹乱。味方の動きが読まれにくくなるサポート型",
    "スミナガシート": "スミナガシートで相手の視界をカット。一方的に攻撃できる状況を作れる",
    "ショクワンダー": "ショクワンダーで壁や天井を自由に移動。奇襲ルートの幅が一気に広がる",
    "マルチミサイル": "マルチミサイルで複数の敵を同時にロックオン。味方との連携キルが取りやすい",
}

# スペシャル別の弱み
SPECIAL_WEAKNESSES = {
    "カニタンク": "カニタンクは発動位置が重要。背後を取られると解除を狙われやすい",
    "ジェットパック": "ジェットパック中はチャージャーに狙われやすい。発動タイミングの見極めが大事",
    "ショクワンダー": "ショクワンダーは使いこなすのが難しい。操作に慣れるまで練習が必要",
    "ウルトラハンコ": "ウルトラハンコは発動中に横や後ろから撃たれると脆い。突っ込みすぎ注意",
    "サメライド": "サメライドは読まれると着地を狩られやすい。一直線だから避けられることも",
    "デコイチラシ": "デコイチラシは直接的なキル貢献が薄い。サポート特化で攻めには向かない",
}

# 武器種別の強み
CLASS_STRENGTHS = {
    "シューター": "シューターの安定した連射力で、塗りもキルもバランスよくこなせる",
    "ブラスター": "ブラスターの爆風で壁裏の敵にもダメージが入る。遮蔽物越しの戦いが超得意",
    "ローラー": "ローラーのヨコ振り一撃キルの脅威が絶大。潜伏からの奇襲は回避困難",
    "フデ": "フデの超高速移動で前線を荒らしまくれる。塗りスピードもトップクラス",
    "チャージャー": "チャージャーの圧倒的な射程で、存在するだけで相手の動きを制限できる",
    "スロッシャー": "スロッシャーの放物線攻撃で、高台や障害物越しに一方的に攻撃できる",
    "スピナー": "スピナーのチャージ後の圧倒的な連射力で、弾幕による制圧が可能",
    "マニューバー": "マニューバーのスライド機動力で対面を有利に運べる。回避しながら攻撃できる",
    "シェルター": "シェルターの傘展開で敵の攻撃をブロック。味方の盾にもなれるのが唯一無二",
    "ストリンガー": "ストリンガーの3方向同時射撃で広範囲をカバー。索敵と牽制の両立が可能",
    "ワイパー": "ワイパーのヨコ斬り広範囲＋タメ斬り遠距離の使い分けで、あらゆる距離に対応可能",
}

# 武器種別の弱み
CLASS_WEAKNESSES = {
    "シューター": "射程が中程度なので、長射程に一方的に撃たれる場面があるのが課題",
    "ブラスター": "連射が遅いから外すと一気にピンチ。対面の精度が求められる上級者向け武器",
    "ローラー": "射程が短くてインクの飛沫が頼り。正面切っての撃ち合いは不得意",
    "フデ": "一発のダメージが低くて正面からの撃ち合いは不利。立ち回りでカバーが必要",
    "チャージャー": "接近されると一気に不利。自衛力が低いから味方のカバーが必須",
    "スロッシャー": "連射力が低くて近距離のシューターに押し込まれると厳しい",
    "スピナー": "チャージ中は無防備。急な対面やインファイトはかなり苦手",
    "マニューバー": "スライド後の硬直中に狙われるリスクがある。インク管理もシビア",
    "シェルター": "傘の耐久値が削られると脆い。チャージャーの一撃で傘が壊れることも",
    "ストリンガー": "チャージが必要で即座に反撃しにくい。接近戦は基本不利",
    "ワイパー": "中距離が微妙に苦手。タメ斬りの隙を突かれると反撃が厳しい",
}

# バリアント武器の追加サフィックスパターン
VARIANT_SUFFIXES = r'(コラボ|ネオ|デコ|ヒュー|ベッチュー|フォイル|オルタナ|ソレーラ|ソレッラ|ツキ|耀|冥|封|艶|彩|幻|煌|燈|幕|帳|鋼|翠|極|颯|響|叡|壊|咲|凜|剛|駆|鍛|詩|律|爪|角|蹄|圧|繚|惑|箔|彗|GECK|ANGL|OWL|BRNZ|ASH|RUST|FRZN|FRST|WNTR|COBR|PYTN|SNAK|MILK|CREM|MAGM|DAWN|ROSE)$'


# =============================================
# ヘルパー関数
# =============================================
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


def tier_img_html(tier, size=40):
    """ティアの画像HTML（Xはテキスト表示）"""
    if tier == "X":
        return f'<span style="font-size:{size}px;font-weight:900;color:#e74c3c;">X</span>'
    fname = TIER_IMG_MAP.get(tier, "")
    if fname:
        return f'<img src="{IMG_BASE}/tiers/{fname}.webp" alt="{tier}" loading="lazy" width="{size}" height="{size}" style="vertical-align:middle">'
    return f'<strong>{tier}</strong>'


def tier_img_small(tier, size=24):
    """小さいティア画像"""
    return tier_img_html(tier, size)


def rating_to_num(r):
    """評価を数値に変換（ソート用）"""
    return TIER_NUM.get(r, 99)


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


def adjust_tier(base_tier, bonus):
    """ルール別補正でティアを上下"""
    if not base_tier or base_tier not in TIER_NUM:
        base_tier = "B"  # デフォルト
    idx = TIER_NUM[base_tier]
    new_idx = max(0, min(len(TIER_ORDER) - 1, idx - bonus))
    return TIER_ORDER[new_idx]


def parse_sections(text):
    """【見出し】区切りのテキストを [(見出し, 本文), ...] に分割"""
    if not text:
        return []
    parts = re.split(r'【(.+?)】', text)
    sections = []
    # parts[0]はプレフィックス（空or前置テキスト）
    i = 1
    while i < len(parts):
        heading = parts[i].strip()
        body = parts[i + 1].strip() if i + 1 < len(parts) else ""
        # Game8リンクテキストを除去
        body = re.sub(r'▶︎.+?はこちら[！!]?', '', body).strip()
        if heading and body:
            sections.append((heading, body))
        i += 2
    return sections


def stars_html(count, max_stars=5):
    """星評価を★☆テキストで生成"""
    if not isinstance(count, int):
        try:
            count = int(count)
        except (ValueError, TypeError):
            count = 3
    count = max(0, min(max_stars, count))
    return "★" * count + "☆" * (max_stars - count)


def estimate_stars(w):
    """武器データから星評価を推定"""
    stars = {}
    # 塗り
    cls = w.get("class", "")
    if cls in ("シューター", "フデ"):
        stars["paint"] = 4
    elif cls in ("チャージャー", "ブラスター"):
        stars["paint"] = 2
    else:
        stars["paint"] = 3

    # 扱いやすさ
    if cls in ("シューター",):
        stars["ease"] = 4
    elif cls in ("チャージャー", "ストリンガー", "ワイパー"):
        stars["ease"] = 2
    else:
        stars["ease"] = 3

    # キル
    dmg = 0
    try:
        dmg = float(w.get("damage", 0))
    except (ValueError, TypeError):
        pass
    if dmg >= 70:
        stars["kill"] = 5
    elif dmg >= 50:
        stars["kill"] = 4
    elif dmg >= 36:
        stars["kill"] = 3
    elif dmg >= 28:
        stars["kill"] = 2
    else:
        stars["kill"] = 3

    # 防御・生存
    if cls in ("シェルター",):
        stars["defense"] = 4
    elif cls in ("チャージャー", "スピナー"):
        stars["defense"] = 2
    else:
        stars["defense"] = 3

    # アシスト
    if cls in ("シューター", "スロッシャー"):
        stars["assist"] = 4
    elif cls in ("ローラー", "ワイパー"):
        stars["assist"] = 2
    else:
        stars["assist"] = 3

    # 打開力
    if cls in ("ブラスター", "ローラー", "ワイパー"):
        stars["breakthrough"] = 4
    elif cls in ("フデ", "シェルター"):
        stars["breakthrough"] = 2
    else:
        stars["breakthrough"] = 3

    return stars


def get_strengths(w):
    """武器の強みテキストを生成（武器種・サブ・スペシャルに基づく個別テキスト）"""
    strengths = []
    cls = w.get("class", "")
    sub = w.get("sub", "")
    special = w.get("special", "")

    # 1. ダメージ・射程・キルタイムからの強み
    if w.get("damage"):
        try:
            dmg = float(w["damage"])
            if dmg >= 70:
                strengths.append(CASUAL_STRENGTH["high_damage"])
            elif dmg >= 50:
                strengths.append("2確の高火力で撃ち合いに強い！ゴリ押しが効くタイプ")
        except ValueError:
            pass
    if w.get("range"):
        try:
            rng = float(w["range"])
            if rng >= 4.0:
                strengths.append(CASUAL_STRENGTH["long_range"])
        except ValueError:
            pass
    if w.get("kill_time"):
        kt = w["kill_time"].replace("秒", "")
        try:
            kt_val = float(kt)
            if kt_val <= 0.15:
                strengths.append(CASUAL_STRENGTH["fast_kill"])
        except ValueError:
            pass

    # 2. 武器種の強み（stats系がなかった場合のみ追加）
    if not strengths and cls in CLASS_STRENGTHS:
        strengths.append(CLASS_STRENGTHS[cls])

    # 3. サブの強み
    if sub in SUB_STRENGTHS:
        strengths.append(SUB_STRENGTHS[sub])

    # 4. スペシャルの強み（上限3つに抑える）
    if len(strengths) < 3 and special in SPECIAL_STRENGTHS:
        strengths.append(SPECIAL_STRENGTHS[special])

    # フォールバック（ここに到達することはほぼないが念のため）
    if not strengths:
        strengths.append(CLASS_STRENGTHS.get(cls, "バランスの取れた構成で堅実に戦える"))

    return strengths[:3]


def get_weaknesses(w):
    """武器の弱みテキストを生成（武器種・サブ・スペシャルに基づく個別テキスト）"""
    weaknesses = []
    cls = w.get("class", "")
    sub = w.get("sub", "")
    special = w.get("special", "")

    # 1. ダメージ・射程・キルタイムからの弱み
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

    # 2. 武器種の弱み（stats系がなかった場合のみ追加）
    if not weaknesses and cls in CLASS_WEAKNESSES:
        weaknesses.append(CLASS_WEAKNESSES[cls])

    # 3. サブ/スペシャルの弱み
    if len(weaknesses) < 2 and sub in SUB_WEAKNESSES:
        weaknesses.append(SUB_WEAKNESSES[sub])
    if len(weaknesses) < 2 and special in SPECIAL_WEAKNESSES:
        weaknesses.append(SPECIAL_WEAKNESSES[special])

    # フォールバック
    if not weaknesses:
        weaknesses.append(CLASS_WEAKNESSES.get(cls, "立ち回りの工夫でカバーが必要。慣れるまでは練度が要る"))

    return weaknesses[:2]


def find_variants(weapons, target_name):
    """同名武器のバリアントを検索"""
    base = re.sub(VARIANT_SUFFIXES, '', target_name)
    variants = [w for w in weapons if w["name"] != target_name and
                re.sub(VARIANT_SUFFIXES, '', w["name"]) == base]
    return variants


def find_base_weapon(weapons, target_name):
    """ベース武器を検索して、tier等のデータを継承するために返す"""
    base_name = re.sub(VARIANT_SUFFIXES, '', target_name)
    if base_name == target_name:
        return None
    # 完全一致で探す
    base_w = next((w for w in weapons if w['name'] == base_name and w.get('tier', '')), None)
    if base_w:
        return base_w
    # startswithで探す
    candidates = [w for w in weapons if w['name'].startswith(base_name) and w['name'] != target_name and w.get('tier', '')]
    if candidates:
        return candidates[0]
    return None


def inherit_base_data(w, all_weapons):
    """ベース武器からtier等のデータを継承（元の武器データは変更しない、新dictを返す）"""
    result = dict(w)
    if result.get('tier', ''):
        return result  # すでにデータがある

    base = find_base_weapon(all_weapons, w['name'])
    if not base:
        return result

    # tier継承（同じ武器種でサブスペが違うだけなので、1段階落として設定）
    base_tier = base.get('tier', '')
    if base_tier:
        base_idx = TIER_NUM.get(base_tier, 4)
        # バリアント武器は通常のベースより若干評価が不明なので、同じか1段階下
        new_idx = min(len(TIER_ORDER) - 1, base_idx + 1)
        result['tier'] = TIER_ORDER[new_idx]

    # rule_tiers継承（ベースから計算）
    if not result.get('rule_tiers'):
        inherited_tier = result.get('tier', 'B')
        cls = result.get('class', '')
        result['rule_tiers'] = {}
        for rk in RULE_NAMES:
            bonus = RULE_CLASS_BONUS[rk].get(cls, 0)
            result['rule_tiers'][rk] = adjust_tier(inherited_tier, bonus)

    # damage/range/kill_time継承
    for key in ['damage', 'range', 'kill_time', 'effective_range', 'special_points', 'unlock_rank']:
        if not result.get(key, '') and base.get(key, ''):
            result[key] = base[key]

    return result


def esc(text):
    """HTMLエスケープ"""
    if not text:
        return ""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


# =============================================
# 武器個別ページ生成（HTML構造）
# =============================================
def generate_weapon_page_html(w, all_weapons):
    """Game8と同じ構造のHTMLで武器ページを生成"""
    # ベース武器からデータを継承
    w = inherit_base_data(w, all_weapons)

    name = w["name"]
    cls = w.get("class", "その他")
    sub = w.get("sub", "")
    special = w.get("special", "")
    tier = w.get("tier") or "B"
    slug = weapon_slug(name)

    # アイコンパス
    w_icon = img(w.get("icon", ""))
    sub_icon = img(w.get("sub_icon", ""))
    sp_icon = img(w.get("special_icon", ""))

    # 星評価
    sr = w.get("star_ratings") or estimate_stars(w)

    # ルール別評価
    rule_tiers = {}
    rt_data = w.get("rule_tiers") or w.get("rule_ratings") or {}
    if rt_data and any(str(v).strip() for v in rt_data.values()):
        rule_tiers = rt_data
    else:
        for rk in RULE_NAMES:
            bonus = RULE_CLASS_BONUS[rk].get(cls, 0)
            rule_tiers[rk] = adjust_tier(tier, bonus)

    # テキストデータ
    eval_sections = parse_sections(w.get("evaluation_text", ""))
    playstyle_sections = parse_sections(w.get("playstyle_text", ""))
    counter_sections = parse_sections(w.get("counter_text", ""))
    gear_sections = parse_sections(w.get("recommended_gear_text", ""))

    strengths = get_strengths(w)
    weaknesses = get_weaknesses(w)

    # 評価セクションのメイン見出し（最初のセクション見出し）
    eval_heading = eval_sections[0][0] if eval_sections else f"{cls}の{name}"
    eval_body = eval_sections[0][1] if eval_sections else ""

    # ギアレコメンデーション
    gear_recs = GEAR_RECOMMENDATIONS.get(cls, GEAR_RECOMMENDATIONS["シューター"])

    html = ""

    # ----- h2: 評価と役割 -----
    html += f'<h2>{esc(name)}の評価と役割</h2>\n'

    # 武器カードテーブル（7行）
    html += '<table>\n'
    # row0: 武器画像+名前 (rowspan=4, colspan=2) | 総合評価 (th colspan=2)
    html += '<tr>\n'
    html += f'  <td rowspan="4" colspan="2" style="text-align:center;vertical-align:middle;width:40%">\n'
    if w_icon:
        html += f'    <img src="{w_icon}" alt="{esc(name)}" loading="lazy" width="90" height="90" style="display:inline-block"><br>\n'
    html += f'    <strong style="font-size:1.1em">{esc(name)}</strong>\n'
    html += f'  </td>\n'
    html += f'  <th colspan="2" style="text-align:center">総合評価</th>\n'
    html += '</tr>\n'

    # row1: 評価画像 (td colspan=2)
    html += '<tr>\n'
    html += f'  <td colspan="2" style="text-align:center;font-size:1.3em">{tier_img_html(tier, 36)} <strong>{tier}</strong></td>\n'
    html += '</tr>\n'

    # row2: サブ・スペ見出し (th colspan=2)
    html += '<tr>\n'
    html += f'  <th colspan="2" style="text-align:center">サブ・スペシャル</th>\n'
    html += '</tr>\n'

    # row3: サブアイコン+名前, スペアイコン+名前 (td colspan=2)
    sub_html = f'{icon_img(w.get("sub_icon", ""), sub, 24)} {esc(sub)}' if sub else "-"
    sp_html = f'{icon_img(w.get("special_icon", ""), special, 24)} {esc(special)}' if special else "-"
    html += '<tr>\n'
    html += f'  <td colspan="2" style="text-align:center">{sub_html} ／ {sp_html}</td>\n'
    html += '</tr>\n'

    # row4: 塗り | 星 | 扱いやすさ | 星
    html += '<tr>\n'
    html += f'  <th>塗り</th><td>{stars_html(sr.get("paint", 3))}</td>\n'
    html += f'  <th>扱いやすさ</th><td>{stars_html(sr.get("ease", 3))}</td>\n'
    html += '</tr>\n'

    # row5: キル | 星 | 防御・生存 | 星
    html += '<tr>\n'
    html += f'  <th>キル</th><td>{stars_html(sr.get("kill", 3))}</td>\n'
    html += f'  <th>防御・生存</th><td>{stars_html(sr.get("defense", 3))}</td>\n'
    html += '</tr>\n'

    # row6: アシスト | 星 | 打開力 | 星
    html += '<tr>\n'
    html += f'  <th>アシスト</th><td>{stars_html(sr.get("assist", 3))}</td>\n'
    html += f'  <th>打開力</th><td>{stars_html(sr.get("breakthrough", 3))}</td>\n'
    html += '</tr>\n'

    html += '</table>\n\n'

    # ----- h3: ルール別評価 -----
    html += '<h3>ルール別評価</h3>\n'
    html += '<table>\n<tr>\n'
    for rk, rname in RULE_NAMES.items():
        html += f'  <th style="text-align:center">{esc(rname)}</th>\n'
    html += '</tr>\n<tr>\n'
    for rk in RULE_NAMES:
        rt = rule_tiers.get(rk, tier)
        html += f'  <td style="text-align:center">{tier_img_small(rt, 24)} <strong>{rt}</strong></td>\n'
    html += '</tr>\n</table>\n\n'

    # ----- h3: 評価見出し（役割テキスト） -----
    html += f'<h3>{esc(eval_heading)}</h3>\n'

    # 強い点・弱い点テーブル（4行）
    html += '<table>\n'
    html += '<tr><th style="background:#e8f5e9;color:#2e7d32">強い点</th></tr>\n'
    html += '<tr><td>\n'
    strength_items = []
    for s in strengths:
        strength_items.append(f'<b>○ {esc(s)}</b>')
    html += '<hr>'.join(strength_items)
    html += '\n</td></tr>\n'
    html += '<tr><th style="background:#ffebee;color:#c62828">弱い点</th></tr>\n'
    html += '<tr><td>\n'
    weakness_items = []
    for wk in weaknesses:
        weakness_items.append(f'<b>✕ {esc(wk)}</b>')
    html += '<hr>'.join(weakness_items)
    html += '\n</td></tr>\n'
    html += '</table>\n'

    # 評価テキスト
    if eval_body:
        html += f'<p>{esc(eval_body)}</p>\n'
    html += '\n'

    # ----- h2: おすすめギア構成 -----
    html += f'<h2>{esc(name)}のおすすめギア構成</h2>\n'

    # h3: 迷ったらコレがおすすめ！
    html += '<h3>迷ったらコレがおすすめ！</h3>\n'

    # ギアセットテーブル（4列 × ヘッダ+3行）
    html += '<table>\n'
    html += '<tr>\n'
    html += '  <th style="width:34%;text-align:center">メイン</th>\n'
    html += '  <th style="width:22%;text-align:center">サブ①</th>\n'
    html += '  <th style="width:22%;text-align:center">サブ②</th>\n'
    html += '  <th style="width:22%;text-align:center">サブ③</th>\n'
    html += '</tr>\n'
    for i in range(3):
        if i < len(gear_recs):
            gear_name = gear_recs[i]["name"]
            html += '<tr>\n'
            html += f'  <td style="text-align:center"><strong>{esc(gear_name)}</strong></td>\n'
            # サブスロットは同じギアパワーで埋める
            html += f'  <td style="text-align:center">{esc(gear_name)}</td>\n'
            html += f'  <td style="text-align:center">{esc(gear_name)}</td>\n'
            html += f'  <td style="text-align:center">{esc(gear_name)}</td>\n'
            html += '</tr>\n'
    html += '</table>\n'

    # ギアテキスト（Game8データがあれば）
    if gear_sections:
        # 最初のセクションのボディを使用（見出しは除く）
        gear_body = gear_sections[0][1] if gear_sections else ""
        if gear_body:
            html += f'<p>{esc(gear_body)}</p>\n'
    html += '\n'

    # h3: おすすめギアパワー一覧
    html += '<h3>おすすめギアパワー一覧と付きやすいブランド</h3>\n'
    html += '<table>\n'
    html += '<tr><th>ギアパワー</th><th>おすすめ理由</th></tr>\n'
    for gear in gear_recs:
        html += f'<tr><td><strong>{esc(gear["name"])}</strong></td><td>{esc(gear["reason"])}</td></tr>\n'
    html += '</table>\n\n'

    # ----- h2: 立ち回りと使い方 -----
    html += f'<h2>{esc(name)}の立ち回りと使い方</h2>\n'

    if playstyle_sections:
        # Game8データからセクション分け
        # 最初のセクションをサマリーテーブルに
        first_heading, first_body = playstyle_sections[0]
        html += '<table>\n'
        html += f'<tr><td>{esc(first_body)}</td></tr>\n'
        html += '</table>\n'

        # 残りのセクションをh3で展開
        for heading, body in playstyle_sections[1:]:
            html += f'<h3>{esc(heading)}</h3>\n'
            html += f'<p>{esc(body)}</p>\n'
    else:
        # フォールバック
        playstyle = CLASS_PLAYSTYLE.get(cls, "武器の特性をしっかり理解して、得意な間合いで戦おう。")
        html += '<table>\n'
        html += f'<tr><td>{esc(playstyle)}</td></tr>\n'
        html += '</table>\n'
        # サブの使い方（具体的に）
        sub_desc = SUB_STRENGTHS.get(sub, f"{sub}でメインの弱点を補おう。状況に合わせて使い分けるのが大事")
        html += f'<h3>サブウェポン「{esc(sub)}」の使い方</h3>\n'
        html += f'<p>{esc(sub_desc)}。メインだけでは届かない場面で積極的に投げていこう。</p>\n'
        # スペシャルの使い方（具体的に）
        sp_desc = SPECIAL_STRENGTHS.get(special, f"{special}は使いどころが大事。味方と合わせて発動すると効果倍増")
        html += f'<h3>スペシャル「{esc(special)}」の使い方</h3>\n'
        html += f'<p>{esc(sp_desc)}。溜まったら味方の動きを見て、タイミングを合わせて発動しよう。</p>\n'
    html += '\n'

    # ----- h2: 対策 -----
    if counter_sections:
        html += f'<h2>{esc(name)}の対策</h2>\n'
        first_heading, first_body = counter_sections[0]
        html += '<table>\n'
        html += f'<tr><td>{esc(first_body)}</td></tr>\n'
        html += '</table>\n'
        for heading, body in counter_sections[1:]:
            html += f'<h3>{esc(heading)}</h3>\n'
            html += f'<p>{esc(body)}</p>\n'
        html += '\n'

    # ----- h2: 性能と射程比較 -----
    html += f'<h2>{esc(name)}の性能</h2>\n'
    html += '<h3>性能</h3>\n'
    html += '<table>\n'
    html += f'<tr><th>ブキ種</th><td>{esc(cls)}</td></tr>\n'
    if w.get("unlock_rank"):
        html += f'<tr><th>解放ランク</th><td>{esc(str(w["unlock_rank"]))}</td></tr>\n'
    if w.get("damage"):
        html += f'<tr><th>攻撃力</th><td>{esc(str(w["damage"]))}</td></tr>\n'
    if w.get("kill_time"):
        html += f'<tr><th>キルタイム</th><td>{esc(w["kill_time"])}</td></tr>\n'
    if w.get("range"):
        html += f'<tr><th>射程（試し撃ち）</th><td>{esc(str(w["range"]))}</td></tr>\n'
    if w.get("effective_range"):
        html += f'<tr><th>射程（有効）</th><td>{esc(str(w["effective_range"]))}</td></tr>\n'
    if w.get("special_points"):
        html += f'<tr><th>スペシャル必要ポイント</th><td>{esc(str(w["special_points"]))}</td></tr>\n'
    html += '</table>\n\n'

    # ----- h2: 同名武器と違い -----
    variants = find_variants(all_weapons, name)
    if variants:
        html += f'<h2>{esc(name)}の同名武器と違い</h2>\n'
        html += '<h3>サブとスペシャルが違うだけ</h3>\n'
        html += '<table>\n'
        html += '<tr><th>武器名</th><th>サブ</th><th>スペシャル</th></tr>\n'
        # 自分自身も含める
        all_variants = [w] + variants
        for v in all_variants:
            v_icon = icon_img(v.get("icon", ""), v["name"], 24)
            v_sub_icon = icon_img(v.get("sub_icon", ""), v.get("sub", ""), 20)
            v_sp_icon = icon_img(v.get("special_icon", ""), v.get("special", ""), 20)
            v_slug = weapon_slug(v["name"])
            html += f'<tr>'
            html += f'<td>{v_icon} <a href="../{v_slug}/">{esc(v["name"])}</a></td>'
            html += f'<td>{v_sub_icon} {esc(v.get("sub", ""))}</td>'
            html += f'<td>{v_sp_icon} {esc(v.get("special", ""))}</td>'
            html += f'</tr>\n'
        html += '</table>\n\n'

    # ----- h2: アップデート調整内容 -----
    if w.get("update_history"):
        html += f'<h2>{esc(name)}のアップデート調整内容</h2>\n'
        for update_entry in w["update_history"]:
            # 各エントリは "[日付のアップデート調整内容]" 形式
            match = re.match(r'\[(.+?)\]', update_entry)
            if match:
                date_str = match.group(1)
                html += f'<h3>{esc(date_str)}</h3>\n'
                # 本文があれば表示
                body = update_entry[match.end():].strip()
                if body:
                    html += '<table>\n'
                    html += f'<tr><td>{esc(body)}</td></tr>\n'
                    html += '</table>\n'
                else:
                    html += f'<p>調整内容はゲーム内のお知らせをご確認ください。</p>\n'
            else:
                html += f'<p>{esc(update_entry)}</p>\n'
        html += '\n'

    # ----- h2: 関連記事 -----
    html += '<h2>関連記事</h2>\n'
    html += '<ul>\n'
    html += f'<li><a href="../../tier-list/">最強武器ランキング</a></li>\n'
    html += f'<li><a href="../">全武器一覧</a></li>\n'
    html += f'<li><a href="../../gear-powers/">ギアパワー解説</a></li>\n'
    html += f'<li><a href="../../beginner/">初心者攻略ガイド</a></li>\n'
    html += '</ul>\n'

    return html


def generate_weapon_pages():
    """武器個別ページをweapons/ディレクトリに生成"""
    weapons_dir = os.path.join(OUTPUT_DIR, "weapons")
    os.makedirs(weapons_dir, exist_ok=True)

    weapons = MASTER["weapons"]

    # _index.md（武器一覧ページ - HTML）
    index_html = ""
    index_html += f'<p>スプラトゥーン3の<strong>全{len(weapons)}武器</strong>の個別ページだよ！武器名をクリックすると詳細ページに移動するよ。</p>\n\n'

    class_weapons = {}
    for w in weapons:
        cls = w.get("class", "その他")
        class_weapons.setdefault(cls, []).append(w)

    for cls in CLASS_ORDER:
        if cls not in class_weapons:
            continue
        # inherit_base_dataで全武器にtierを付与してからソート
        enriched_group = [inherit_base_data(w, weapons) for w in class_weapons[cls]]
        enriched_group.sort(key=lambda w: (rating_to_num(w.get("tier") or ""), w["name"]))
        index_html += f'<h2>{esc(cls)}（{len(enriched_group)}種）</h2>\n'
        index_html += '<table>\n'
        index_html += '<tr><th>武器</th><th>サブ</th><th>スペシャル</th><th>評価</th></tr>\n'
        for ew in enriched_group:
            wicon = icon_img(ew.get("icon", ""), ew["name"], 28)
            sub_ic = icon_img(ew.get("sub_icon", ""), ew.get("sub", ""), 20)
            sp_ic = icon_img(ew.get("special_icon", ""), ew.get("special", ""), 20)
            slug = weapon_slug(ew["name"])
            t = ew.get("tier") or "-"
            index_html += f'<tr>'
            index_html += f'<td>{wicon} <a href="{slug}/">{esc(ew["name"])}</a></td>'
            index_html += f'<td>{sub_ic} {esc(ew.get("sub", ""))}</td>'
            index_html += f'<td>{sp_ic} {esc(ew.get("special", ""))}</td>'
            index_html += f'<td style="text-align:center">{tier_img_small(t, 20)} <strong>{t}</strong></td>'
            index_html += f'</tr>\n'
        index_html += '</table>\n\n'

    index_content = f"""---
title: "スプラトゥーン3 全武器一覧"
linkTitle: "全武器"
weight: 2
date: 2026-02-13
description: "スプラトゥーン3の全{len(weapons)}武器データベース。各武器の性能・立ち回り・おすすめギアを解説。"
---

{index_html}"""

    write_file(os.path.join(weapons_dir, "_index.md"), index_content)

    # 個別武器ページ
    count = 0
    for w in weapons:
        slug = weapon_slug(w["name"])
        w_enriched = inherit_base_data(w, weapons)

        page_html = generate_weapon_page_html(w, weapons)

        content = f"""---
title: "【スプラ3】{w['name']}の評価・立ち回り・おすすめギア"
linkTitle: "{w['name']}"
weight: 50
date: 2026-02-13
categories: ["{w.get('class', 'その他')}"]
tags: ["スプラトゥーン3", "{w.get('class', '')}", "{w['name']}"]
description: "スプラトゥーン3の{w['name']}の性能評価・立ち回り解説。サブ{w.get('sub', '')}、スペシャル{w.get('special', '')}の使い方やおすすめギアパワーを紹介。"
---

{page_html}"""

        write_file(os.path.join(weapons_dir, f"{slug}.md"), content)
        count += 1

    return count


# =============================================
# ティアリストページ（HTML構造）
# =============================================
def generate_tier_list():
    weapons = MASTER["weapons"]
    # 全武器にベース武器からtierを継承
    enriched = [inherit_base_data(w, weapons) for w in weapons]
    tiered = [w for w in enriched if w.get("tier")]
    tiered.sort(key=lambda w: (rating_to_num(w["tier"]), w["name"]))

    tier_groups = {}
    for w in tiered:
        t = w["tier"]
        tier_groups.setdefault(t, []).append(w)

    html = ""

    # 評価基準テーブル
    html += '<h2>評価基準</h2>\n'
    html += '<table>\n'
    html += '<tr><th>評価</th><th>意味</th></tr>\n'
    tier_desc = {
        "X": "環境最強。Xマッチ上位で猛威を振るうバケモノ武器",
        "S+": "環境トップクラス。どのルールでも安定して強い",
        "S": "強武器。使いこなせればガチマの勝率がグンと上がる",
        "A+": "準強武器。練度次第で十分に戦える実力派",
        "A": "平均以上。特化した場面で光る一芸タイプ",
        "B+": "使い込み次第で活躍可能。愛がある人向け",
        "B": "趣味武器。愛と練度があれば戦える",
        "C+": "厳しめだけど独自の強みはある",
        "C": "環境的には逆風。それでも使いたい人向け",
    }
    for t in TIER_ORDER:
        html += f'<tr><td style="text-align:center">{tier_img_html(t, 28)} <strong>{t}</strong></td><td>{esc(tier_desc.get(t, ""))}</td></tr>\n'
    html += '</table>\n\n'

    # 最強武器ランキング早見表（メインテーブル）
    html += '<h2>最強武器ランキング</h2>\n'
    html += '<table>\n'
    for t in TIER_ORDER:
        if t not in tier_groups:
            continue
        group = tier_groups[t]
        html += '<tr>\n'
        html += f'  <th style="text-align:center;vertical-align:middle;width:60px">{tier_img_html(t, 32)}</th>\n'
        html += f'  <td>\n'
        # 各武器をdivで横並び
        weapon_divs = []
        for w in group:
            w_icon = img(w.get("icon", ""))
            w_slug = weapon_slug(w["name"])
            if w_icon:
                weapon_divs.append(
                    f'<div style="display:inline-block;text-align:center;margin:4px;width:68px;vertical-align:top">'
                    f'<a href="weapons/{w_slug}/" style="text-decoration:none;color:inherit">'
                    f'<img src="{w_icon}" alt="{esc(w["name"])}" loading="lazy" width="48" height="48"><br>'
                    f'<span style="font-size:.7em;line-height:1.2;display:block">{esc(w["name"])}</span>'
                    f'</a></div>'
                )
            else:
                weapon_divs.append(
                    f'<div style="display:inline-block;text-align:center;margin:4px">'
                    f'<a href="weapons/{w_slug}/">{esc(w["name"])}</a></div>'
                )
        html += '    '.join(weapon_divs)
        html += '\n  </td>\n'
        html += '</tr>\n'
    html += '</table>\n\n'

    # 各ティア解説
    tier_names = {
        "X": "Xランク（環境最強）", "S+": "S+ランク（環境トップ）",
        "S": "Sランク（強武器）", "A+": "A+ランク（準強武器）",
        "A": "Aランク（平均以上）", "B+": "B+ランク", "B": "Bランク",
        "C+": "C+ランク", "C": "Cランク",
    }

    for t in TIER_ORDER:
        if t not in tier_groups:
            continue
        group = tier_groups[t]
        html += f'<h2>{esc(tier_names.get(t, t))}</h2>\n'

        for w in group:
            w_icon = img(w.get("icon", ""))
            sub_ic = icon_img(w.get("sub_icon", ""), w.get("sub", ""), 20)
            sp_ic = icon_img(w.get("special_icon", ""), w.get("special", ""), 20)
            w_slug = weapon_slug(w["name"])
            strengths = get_strengths(w)
            weaknesses = get_weaknesses(w)

            html += f'<h3>{esc(w["name"])}</h3>\n'
            html += '<table>\n'
            html += '<tr>\n'
            if w_icon:
                html += f'  <td rowspan="3" style="text-align:center;width:80px;vertical-align:middle">'
                html += f'<a href="weapons/{w_slug}/"><img src="{w_icon}" alt="{esc(w["name"])}" loading="lazy" width="60" height="60"></a></td>\n'
            html += f'  <th>評価</th><td>{tier_img_small(t, 20)} <strong>{t}</strong></td>\n'
            html += '</tr>\n'
            html += f'<tr><th>サブ</th><td>{sub_ic} {esc(w.get("sub", ""))}</td></tr>\n'
            html += f'<tr><th>スペシャル</th><td>{sp_ic} {esc(w.get("special", ""))}</td></tr>\n'
            html += '</table>\n'
            html += f'<p><strong>強い点</strong>: {esc(strengths[0])}<br>\n'
            html += f'<strong>弱い点</strong>: {esc(weaknesses[0])}</p>\n\n'

    content = f"""---
title: "【スプラ3】最強武器ランキング"
linkTitle: "最強ブキ"
weight: 1
date: 2026-02-13
categories: ["最強ランキング"]
tags: ["スプラトゥーン3", "武器"]
description: "スプラトゥーン3の最強武器(ブキ)ランキング。全武器を徹底評価しXマッチで強い武器を紹介。"
---

<p>最新環境のスプラトゥーン3で<strong>最も強い武器（ブキ）</strong>をランキング形式で紹介するよ！Xマッチでの採用率と勝率を基準に評価してます。</p>

{html}

<h2>関連記事</h2>
<ul>
<li><a href="weapons/">全武器一覧</a></li>
<li><a href="tier-nawabari/">ナワバリバトル最強ランキング</a></li>
<li><a href="tier-area/">ガチエリア最強ランキング</a></li>
<li><a href="tier-yagura/">ガチヤグラ最強ランキング</a></li>
<li><a href="tier-hoko/">ガチホコ最強ランキング</a></li>
<li><a href="tier-asari/">ガチアサリ最強ランキング</a></li>
</ul>
"""

    return content


# =============================================
# ルール別ランキング（HTML構造）
# =============================================
def generate_rule_ranking(rule_key):
    rule_info = {
        "nawabari": {
            "desc": "ナワバリバトル", "title": "ナワバリバトル最強武器ランキング",
            "intro": "ナワバリバトルは<strong>3分間で塗り面積を競う</strong>ルール！塗り性能が高い武器がマジで有利で、終盤30秒の逆転が勝負の鍵。スペシャルの回転率も超重要だよ。",
            "tips": "塗りポイントが高い武器が圧倒的に有利。スペシャルの回転率も大事だから、塗り+スペシャルが強い武器を選ぶのがおすすめ！",
        },
        "area": {
            "desc": "ガチエリア", "title": "ガチエリア最強武器ランキング",
            "intro": "ガチエリアは<strong>指定エリアを塗り続ける</strong>ルール！エリア確保後の維持が超大事で、塗り性能と前線維持力のバランスが求められるよ。",
            "tips": "エリアを塗り返す能力が必須！射程が長くてエリアを安全に塗れる武器や、スペシャルでエリアを一気に塗り返せる武器が強いよ。",
        },
        "yagura": {
            "desc": "ガチヤグラ", "title": "ガチヤグラ最強武器ランキング",
            "intro": "ガチヤグラは<strong>ヤグラに乗って進める</strong>ルール！ヤグラ上の味方を守る長射程武器と、ヤグラ周辺を制圧する爆風武器がめちゃくちゃ活躍するよ。",
            "tips": "ヤグラ周辺の制圧力が命！ブラスターの爆風やスロッシャーの曲射でヤグラ上の敵を排除できる武器が強いぞ。",
        },
        "hoko": {
            "desc": "ガチホコバトル", "title": "ガチホコバトル最強武器ランキング",
            "intro": "ガチホコバトルは<strong>ホコを持って相手ゴールに進む</strong>ルール！キル性能が高い武器で道を切り開き、機動力のある武器でホコを運ぶのが基本。",
            "tips": "キル性能と機動力の両方が重要。前線を押し上げてホコを進めるから、対面力の高い武器が活躍するよ！",
        },
        "asari": {
            "desc": "ガチアサリ", "title": "ガチアサリ最強武器ランキング",
            "intro": "ガチアサリは<strong>アサリを集めてゴールに投げ入れる</strong>ルール！広い範囲をカバーする機動力と、ゴール前の攻防でのキル性能が求められるよ。",
            "tips": "機動力とキル性能のバランスが大事。アサリを集める機動力と、ゴール前で敵を倒す対面力を兼ね備えた武器が強い！",
        },
    }

    rule = rule_info[rule_key]
    weapons = MASTER["weapons"]
    # 全武器にベースデータを継承
    enriched = [inherit_base_data(w, weapons) for w in weapons]
    tiered = [w for w in enriched if w.get("tier")]
    boosts = RULE_CLASS_BONUS[rule_key]

    adjusted = []
    for w in tiered:
        rt = w.get("rule_tiers") or {}
        rr = w.get("rule_ratings") or {}
        if rt.get(rule_key, '').strip():
            new_tier = rt[rule_key]
        elif rr.get(rule_key, '').strip():
            new_tier = rr[rule_key]
        else:
            bonus = boosts.get(w.get("class", ""), 0)
            new_tier = adjust_tier(w["tier"], bonus)
        adjusted.append({**w, "rule_tier": new_tier})

    adjusted.sort(key=lambda w: (rating_to_num(w["rule_tier"]), w["name"]))

    tier_groups = {}
    for w in adjusted:
        t = w["rule_tier"]
        tier_groups.setdefault(t, []).append(w)

    slug_map = {"nawabari": "tier-nawabari", "area": "tier-area",
                "yagura": "tier-yagura", "hoko": "tier-hoko", "asari": "tier-asari"}

    html = ""
    html += f'<p>{rule["intro"]}</p>\n\n'

    html += f'<h2>{esc(rule["desc"])}の武器選びのポイント</h2>\n'
    html += f'<p>{esc(rule["tips"])}</p>\n\n'

    # ランキング表
    html += f'<h2>{esc(rule["title"])}</h2>\n'
    html += '<table>\n'
    for t in TIER_ORDER:
        if t not in tier_groups:
            continue
        group = tier_groups[t]
        html += '<tr>\n'
        html += f'  <th style="text-align:center;vertical-align:middle;width:60px">{tier_img_html(t, 32)}</th>\n'
        html += f'  <td>\n'
        weapon_divs = []
        for w in group:
            w_icon = img(w.get("icon", ""))
            w_slug = weapon_slug(w["name"])
            if w_icon:
                weapon_divs.append(
                    f'<div style="display:inline-block;text-align:center;margin:4px;width:68px;vertical-align:top">'
                    f'<a href="weapons/{w_slug}/" style="text-decoration:none;color:inherit">'
                    f'<img src="{w_icon}" alt="{esc(w["name"])}" loading="lazy" width="48" height="48"><br>'
                    f'<span style="font-size:.7em;line-height:1.2;display:block">{esc(w["name"])}</span>'
                    f'</a></div>'
                )
            else:
                weapon_divs.append(
                    f'<div style="display:inline-block;text-align:center;margin:4px">'
                    f'<a href="weapons/{w_slug}/">{esc(w["name"])}</a></div>'
                )
        html += '    '.join(weapon_divs)
        html += '\n  </td>\n'
        html += '</tr>\n'
    html += '</table>\n\n'

    # 上位ティア解説
    for t in ["X", "S+", "S"]:
        if t not in tier_groups:
            continue
        tier_name = {"X": "Xランク（環境最強）", "S+": "S+ランク（環境トップ）", "S": "Sランク（強武器）"}.get(t, t)
        html += f'<h2>{esc(tier_name)}</h2>\n'
        for w in tier_groups[t]:
            sub_ic = icon_img(w.get("sub_icon", ""), w.get("sub", ""), 20)
            sp_ic = icon_img(w.get("special_icon", ""), w.get("special", ""), 20)
            w_slug = weapon_slug(w["name"])

            html += f'<h3>{esc(w["name"])}（{esc(w.get("class", ""))}）</h3>\n'
            html += '<table>\n'
            html += f'<tr><th>サブ</th><td>{sub_ic} {esc(w.get("sub", ""))}</td></tr>\n'
            html += f'<tr><th>スペシャル</th><td>{sp_ic} {esc(w.get("special", ""))}</td></tr>\n'
            if w.get("damage"):
                html += f'<tr><th>ダメージ</th><td>{esc(str(w["damage"]))}</td></tr>\n'
            html += '</table>\n'

            cls = w.get("class", "")
            bonus = boosts.get(cls, 0)
            if bonus >= 2:
                tip = f"{cls}はこのルールでマジで最強の武器種。環境トップの性能を見せつけてくれるよ"
            elif bonus >= 1:
                tip = f"{cls}の特性がこのルールとバッチリ噛み合ってて、安定して活躍できる"
            elif bonus == 0:
                tip = "総合力の高さでルールを問わず活躍。バランスの良さが光る"
            else:
                tip = "このルールでは相性が微妙な場面もあるけど、プレイヤースキル次第で十分戦える"
            html += f'<p><strong>{esc(rule["desc"])}での強み</strong>: {esc(tip)}</p>\n\n'

    # 関連リンク
    html += '<h2>関連記事</h2>\n<ul>\n'
    html += '<li><a href="../tier-list/">最強武器ランキング（総合）</a></li>\n'
    for k, v in rule_info.items():
        if k != rule_key:
            html += f'<li><a href="../{slug_map[k]}/">{esc(v["desc"])}最強ランキング</a></li>\n'
    html += '<li><a href="../weapons/">全武器一覧</a></li>\n'
    html += '</ul>\n'

    content = f"""---
title: "【スプラ3】{rule['title']}"
linkTitle: "{rule['desc']}ランキング"
weight: 10
date: 2026-02-13
categories: ["ルール別ランキング"]
tags: ["スプラトゥーン3", "{rule['desc']}"]
description: "スプラトゥーン3の{rule['desc']}で強い武器をランキング。{rule['desc']}に特化した最強武器を解説。"
---

{html}"""

    return content


# =============================================
# _index.md - ゲームTOP
# =============================================
def generate_index():
    weapons = MASTER["weapons"]
    classes = {}
    for w in weapons:
        cls = w.get("class", "その他")
        classes[cls] = classes.get(cls, 0) + 1

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

    html = ""
    html += f'<h2>スプラトゥーン3 攻略TOP</h2>\n'
    html += f'<p>Nintendo Switch用対戦アクション「スプラトゥーン3」の攻略情報を<strong>全{len(weapons)}武器</strong>分まとめてるよ！最新環境の評価に基づいたデータを掲載中。</p>\n\n'

    html += '<h3>人気記事ランキング</h3>\n'
    html += '<ul>\n'
    html += f'<li><a href="tier-list/">最強武器ランキング</a> - 全ブキのティアランク（X〜C）</li>\n'
    html += f'<li><a href="weapons/">全武器一覧</a> - {len(weapons)}武器の性能比較</li>\n'
    html += '<li><a href="beginner/">初心者攻略ガイド</a> - はじめてのスプラ3はここから！</li>\n'
    html += '<li><a href="gear-powers/">ギアパワー解説</a> - 全26種の効果とおすすめ</li>\n'
    html += '<li><a href="salmon-run/">サーモンラン攻略</a> - オオモノシャケの倒し方</li>\n'
    html += f'<li><a href="stages/">ステージ一覧</a> - 全{len(MASTER["stages"])}ステージ＋攻略法</li>\n'
    html += '<li><a href="events/">フェス・イベント情報</a> - 最新フェス結果</li>\n'
    html += '</ul>\n\n'

    html += '<h3>ルール別最強武器</h3>\n'
    html += '<ul>\n'
    html += '<li><a href="tier-nawabari/">ナワバリバトル最強ランキング</a></li>\n'
    html += '<li><a href="tier-area/">ガチエリア最強ランキング</a></li>\n'
    html += '<li><a href="tier-yagura/">ガチヤグラ最強ランキング</a></li>\n'
    html += '<li><a href="tier-hoko/">ガチホコ最強ランキング</a></li>\n'
    html += '<li><a href="tier-asari/">ガチアサリ最強ランキング</a></li>\n'
    html += '</ul>\n\n'

    html += '<h3>武器種別一覧</h3>\n'
    html += '<table>\n'
    html += '<tr><th>武器種</th><th>武器数</th><th>特徴</th></tr>\n'
    for cls in CLASS_ORDER:
        if cls in classes:
            desc = class_desc.get(cls, "")
            html += f'<tr><td><strong>{esc(cls)}</strong></td><td>{classes[cls]}</td><td>{esc(desc)}</td></tr>\n'
    html += '</table>\n'

    content = f"""---
title: "スプラトゥーン3 攻略"
linkTitle: "スプラトゥーン3"
description: "スプラトゥーン3の攻略情報まとめ。最強武器ランキング、全{len(weapons)}武器データ、ギアパワー、サーモンラン、ステージ攻略など。"
weight: 1
---

{html}"""

    return content


# =============================================
# ステージ個別ページ（HTML構造）
# =============================================
def generate_stage_pages():
    """ステージ個別ページを stages/ ディレクトリに生成"""
    stages_dir = os.path.join(OUTPUT_DIR, "stages")
    os.makedirs(stages_dir, exist_ok=True)

    stages = MASTER["stages"]

    # _index.md
    index_html = ""
    index_html += f'<p>スプラトゥーン3の<strong>全{len(stages)}ステージ</strong>の攻略情報をまとめてるよ！各ステージの特徴と強い武器を知って、ステージに合わせた立ち回りをしよう。</p>\n\n'
    index_html += '<h2>ステージ一覧</h2>\n'
    index_html += '<table>\n'
    index_html += '<tr><th>No.</th><th>ステージ名</th><th>追加時期</th></tr>\n'
    for s in stages:
        slug = stage_slug(s["name"])
        index_html += f'<tr><td>{s["order"]}</td><td><a href="{slug}/">{esc(s["name"])}</a></td><td>{esc(s.get("origin", "-"))}</td></tr>\n'
    index_html += '</table>\n'

    index_content = f"""---
title: "【スプラ3】全ステージ一覧・攻略"
linkTitle: "ステージ攻略"
weight: 6
date: 2026-02-13
description: "スプラトゥーン3の全{len(stages)}ステージの攻略情報。各ステージの特徴・おすすめ武器・立ち回りのコツを解説。"
---

{index_html}"""

    write_file(os.path.join(stages_dir, "_index.md"), index_content)

    # 個別ステージページ
    count = 0
    for s in stages:
        slug = stage_slug(s["name"])
        origin = s.get("origin", "")

        html = ""

        # ステージ画像
        html += f'<h2>{esc(s["name"])}のステージ情報</h2>\n'

        # 基本情報テーブル
        html += '<table>\n'
        html += f'<tr><th>ステージ名</th><td>{esc(s["name"])}</td></tr>\n'
        html += f'<tr><th>追加時期</th><td>{esc(origin) if origin else "-"}</td></tr>\n'
        html += f'<tr><th>ステージNo.</th><td>{s["order"]}</td></tr>\n'
        html += '</table>\n\n'

        # ルール別攻略
        html += f'<h2>{esc(s["name"])}の攻略ポイント</h2>\n'

        rule_tips = {
            "ナワバリバトル": "塗り性能の高い武器で広いエリアを効率よく塗ろう。中央付近の確保が勝負の鍵になるよ。",
            "ガチエリア": "エリアの位置を把握して、安全にエリアを塗り返せるポジションを確保しよう。",
            "ガチヤグラ": "ヤグラのルートに沿って、障害物を活かしながら護衛するのがコツ。",
            "ガチホコバトル": "ホコのルートは複数あるから、相手の守りが薄いルートを選ぼう。",
            "ガチアサリ": "アサリが散らばるエリアを効率よく回収。ゴール前の攻防が最大の山場！",
        }

        for rname, tip in rule_tips.items():
            html += f'<h3>{esc(rname)}</h3>\n'
            html += f'<p>{esc(tip)}</p>\n'

        html += '\n'

        # 関連記事
        html += '<h2>関連記事</h2>\n'
        html += '<ul>\n'
        html += '<li><a href="../">全ステージ一覧</a></li>\n'
        html += '<li><a href="../../tier-list/">最強武器ランキング</a></li>\n'
        html += '<li><a href="../../weapons/">全武器一覧</a></li>\n'
        html += '</ul>\n'

        content = f"""---
title: "【スプラ3】{s['name']}の攻略・おすすめ武器"
linkTitle: "{s['name']}"
weight: {s['order']}
date: 2026-02-13
categories: ["ステージ"]
tags: ["スプラトゥーン3", "ステージ", "{s['name']}"]
description: "スプラトゥーン3の{s['name']}の攻略情報。ステージの特徴やおすすめ武器、各ルールでの立ち回りを解説。"
---

{html}"""

        write_file(os.path.join(stages_dir, f"{slug}.md"), content)
        count += 1

    return count


# =============================================
# ギアパワー解説（HTML構造）
# =============================================
def generate_gear_powers():
    gp = MASTER["gear_powers"]
    tier_order_map = {"X": 0, "S+": 1, "S": 2, "A": 3, "B": 4, "C": 5}

    html = ""
    html += '<p>スプラトゥーン3の<strong>全26種ギアパワー</strong>の効果と評価をまとめたよ！ギアパワーの優先順位がわからない人は、このランキングを参考にしてね。</p>\n\n'

    html += '<h2>ギアパワーおすすめランキング</h2>\n'

    # 基本ギアパワー
    html += '<h3>基本ギアパワー（14種）</h3>\n'
    html += '<p>基本ギアパワーは<strong>アタマ・フク・クツすべてに付く</strong>汎用的なギアパワーだよ。</p>\n'
    html += '<table>\n'
    html += '<tr><th>ランク</th><th>ギアパワー名</th><th>効果</th></tr>\n'
    basic = sorted(gp["basic"], key=lambda g: tier_order_map.get(g.get("tier", ""), 99))
    for g in basic:
        html += f'<tr><td style="text-align:center"><strong>{esc(g["tier"])}</strong></td><td><strong>{esc(g["name"])}</strong></td><td>{esc(g["effect"])}</td></tr>\n'
    html += '</table>\n\n'

    # メイン専用
    html += '<h3>メイン専用ギアパワー（12種）</h3>\n'
    html += '<p>メイン専用ギアパワーは<strong>メインスロットにのみ付く</strong>特殊なギアパワー。効果がデカい分、枠も限られるから慎重に選ぼう！</p>\n'
    html += '<table>\n'
    html += '<tr><th>ランク</th><th>ギアパワー名</th><th>効果</th></tr>\n'
    main_only = sorted(gp["main_only"], key=lambda g: tier_order_map.get(g.get("tier", ""), 99))
    for g in main_only:
        html += f'<tr><td style="text-align:center"><strong>{esc(g["tier"])}</strong></td><td><strong>{esc(g["name"])}</strong></td><td>{esc(g["effect"])}</td></tr>\n'
    html += '</table>\n\n'

    # おすすめギア構成
    html += '<h2>おすすめギア構成</h2>\n'

    gear_sets = [
        {
            "title": "短射程シューター向け（わかば・スプラシューター等）",
            "rows": [
                ("アタマ", "カムバック", "スペシャル増加量アップ×3"),
                ("フク", "イカニンジャ", "イカダッシュ速度アップ×3"),
                ("クツ", "ステルスジャンプ", "インク効率アップ（サブ）×3"),
            ],
            "desc": "デスしてもカムバックで即復帰、イカニンジャで潜伏奇襲、ステルスジャンプで安全に前線復帰できる万能構成！",
        },
        {
            "title": "長射程シューター向け（プライム・ジェットスイーパー等）",
            "rows": [
                ("アタマ", "ラストスパート", "ヒト移動速度アップ×3"),
                ("フク", "復活ペナルティアップ", "インク効率アップ（メイン）×3"),
                ("クツ", "対物攻撃力アップ", "イカダッシュ速度アップ×3"),
            ],
            "desc": "終盤に強くなるラスパ構成。復活ペナルティアップで相手にプレッシャーをかけるのがポイント！",
        },
        {
            "title": "塗りサポート向け（N-ZAP・プロモデラー等）",
            "rows": [
                ("アタマ", "カムバック", "スペシャル増加量アップ×3"),
                ("フク", "イカニンジャ", "スーパージャンプ時間短縮×3"),
                ("クツ", "ステルスジャンプ", "インク回復力アップ×3"),
            ],
            "desc": "スペシャルをガンガン回して味方を支援する構成。前線復帰も速くて塗りサポートに最適！",
        },
    ]

    for gs in gear_sets:
        html += f'<h3>{esc(gs["title"])}</h3>\n'
        html += '<table>\n'
        html += '<tr><th>部位</th><th>メイン</th><th>サブ×3</th></tr>\n'
        for part, main_g, sub_g in gs["rows"]:
            html += f'<tr><td>{esc(part)}</td><td>{esc(main_g)}</td><td>{esc(sub_g)}</td></tr>\n'
        html += '</table>\n'
        html += f'<p>{esc(gs["desc"])}</p>\n\n'

    # ギアパワーの仕組み
    html += '<h2>ギアパワーの仕組み</h2>\n'
    html += '<ul>\n'
    html += '<li>各装備に<strong>メインスロット1つ + サブスロット3つ</strong>（合計12スロット）</li>\n'
    html += '<li>メインスロット = サブスロット×3.3倍の効果</li>\n'
    html += '<li><strong>57表記</strong>: メイン=10, サブ=3 で合計57が最大</li>\n'
    html += '<li>ほとんどのギアパワーは<strong>効果が減衰する</strong>（積みすぎ注意！）</li>\n'
    html += '<li>メイン専用ギアパワーは<strong>メインスロットにしか付かない</strong>から最大3つまで</li>\n'
    html += '</ul>\n'

    content = f"""---
title: "【スプラ3】ギアパワー一覧・おすすめランキング"
linkTitle: "ギアパワー"
weight: 4
date: 2026-02-13
categories: ["ギア"]
tags: ["スプラトゥーン3", "ギアパワー"]
description: "スプラトゥーン3の全26種ギアパワーの効果一覧とおすすめランキング。最強ギア構成も紹介。"
---

{html}"""

    return content


# =============================================
# サーモンラン攻略（HTML構造）
# =============================================
def generate_salmon_run():
    sr = MASTER["salmon_run"]

    html = ""
    html += '<p>サーモンラン NEXT WAVEの攻略情報をまとめたよ！<strong>でんせつ</strong>以上のクリア率を上げるには、オオモノシャケの優先順位を覚えるのがマジで大事。</p>\n\n'

    # オオモノシャケ優先順位
    html += '<h2>オオモノシャケ 優先順位ランキング</h2>\n'
    html += '<p>高ランク帯では<strong>処理の優先順位</strong>が超重要。放置すると一気に壊滅するから気をつけて！</p>\n'
    html += '<table>\n'
    html += '<tr><th>優先度</th><th>オオモノ</th><th>特徴</th><th>倒し方</th></tr>\n'
    for s in sr["big_salmon"]:
        html += f'<tr><td style="text-align:center"><strong>{esc(s["priority"])}</strong></td><td><strong>{esc(s["name"])}</strong></td><td>{esc(s["description"])}</td><td>{esc(s["how_to_defeat"])}</td></tr>\n'
    html += '</table>\n\n'

    # 詳細攻略
    html += '<h2>オオモノシャケ詳細攻略</h2>\n'
    priority_tips = {
        "X": "放置すると味方が壊滅するから最優先で処理！見つけたら全力で倒しに行こう",
        "S+": "継続的にダメージを与えてくるから、見つけ次第すぐに対処。放置は厳禁！",
        "S": "行動範囲が広くて放置すると厄介。余裕がある時に確実に処理しよう",
        "A": "比較的対処しやすいけど、複数溜まると危険。こまめに処理が吉",
    }
    for s in sr["big_salmon"]:
        tip = priority_tips.get(s["priority"], "状況に応じて処理しよう")
        html += f'<h3>{esc(s["name"])}（優先度: {esc(s["priority"])}）</h3>\n'
        html += '<table>\n'
        html += f'<tr><th>特徴</th><td>{esc(s["description"])}</td></tr>\n'
        html += f'<tr><th>倒し方</th><td>{esc(s["how_to_defeat"])}</td></tr>\n'
        html += f'<tr><th>ポイント</th><td>{esc(tip)}</td></tr>\n'
        html += '</table>\n\n'

    # 特殊WAVE
    html += '<h2>特殊WAVE攻略</h2>\n'
    html += '<p>特殊WAVEは通常WAVEとは全く違うルールで進行するよ。対処法を知らないと即壊滅するから必ず覚えよう！</p>\n'
    for sw in sr["special_waves"]:
        html += f'<h3>{esc(sw["name"])}</h3>\n'
        html += f'<p>{esc(sw["description"])}</p>\n'

    # オカシラシャケ
    html += '<h2>オカシラシャケ</h2>\n'
    html += '<p>WAVE3クリア後にランダムで出現する超巨大ボス。金ウロコを入手するチャンス！全力で倒そう。</p>\n'
    for ks in sr["king_salmon"]:
        html += f'<h3>{esc(ks["name"])}</h3>\n'
        html += f'<p>{esc(ks["description"])}</p>\n'

    # 上達のコツ
    html += '<h2>サーモンラン上達のコツ</h2>\n'
    html += '<table>\n'
    html += '<tr><th>No.</th><th>コツ</th></tr>\n'
    tips = [
        "金イクラの納品を最優先 - キルよりも納品が大事。ノルマ達成が全て",
        "オオモノは優先順位通りに処理 - テッキュウ・カタパッド・タワーから倒す",
        "スペシャルは温存しすぎない - WAVE3やキケン度が高い時にガンガン使おう",
        "高台を利用する - 多くのオオモノは高台から処理しやすい",
        "インクを切らさない - イカ状態でこまめに回復",
        "味方を助ける - 味方がやられたらすぐに助ける（全滅防止が最優先）",
        "カモンを使う - 「カモン」でイクラの場所を味方に伝えよう",
    ]
    for i, tip in enumerate(tips, 1):
        html += f'<tr><td style="text-align:center">{i}</td><td>{esc(tip)}</td></tr>\n'
    html += '</table>\n'

    content = f"""---
title: "【スプラ3】サーモンラン攻略・オオモノシャケの倒し方"
linkTitle: "サーモンラン"
weight: 5
date: 2026-02-13
categories: ["サーモンラン"]
tags: ["スプラトゥーン3", "サーモンラン"]
description: "スプラトゥーン3のサーモンラン攻略。オオモノシャケの優先順位と倒し方、特殊WAVEの攻略法、オカシラシャケの対策を解説。"
---

{html}"""

    return content


# =============================================
# 初心者攻略ガイド（HTML構造）
# =============================================
def generate_beginner():
    html = ""
    html += '<p>スプラトゥーン3をこれから始める人・始めたばかりの人向けの攻略ガイドだよ！<strong>効率的な序盤の進め方</strong>と<strong>上達のコツ</strong>をまとめたから参考にしてね。</p>\n\n'

    html += '<h2>序盤の進め方</h2>\n'

    steps = [
        ("STEP 1: ヒーローモードをプレイ", "ソロプレイのチュートリアル的なモード。基本操作が自然と身につく。クリア報酬でギアやアイテムがもらえるよ。ジャイロ操作に慣れるのに最適！"),
        ("STEP 2: 散歩モードでステージを覚える", "ロビーから「散歩」を選択して現在のバトルステージを自由に歩き回れる。高台の位置・インク通路・裏取りルートを確認しよう。"),
        ("STEP 3: ナワバリバトルで実戦デビュー", "最もカジュアルなルール。勝ち負けを気にせず塗ることに集中するのがコツ。まずはランク10を目指そう！"),
        ("STEP 4: バンカラマッチに挑戦", "ランク10で解放されるガチバトル。まずはオープンで各ルールを体験しよう。"),
        ("STEP 5: ギアを揃える", "ショップで毎日チェック。好みのギアパワーが付いた装備を集めよう。"),
    ]
    for title, desc in steps:
        html += f'<h3>{esc(title)}</h3>\n'
        html += f'<p>{esc(desc)}</p>\n'

    # 初心者おすすめ武器
    html += '<h2>初心者おすすめ武器TOP5</h2>\n'
    html += '<table>\n'
    html += '<tr><th>順位</th><th>武器名</th><th>おすすめ理由</th></tr>\n'
    beginner_weapons = [
        ("1", "わかばシューター", "塗り性能最強。ボムとバリアで初心者でもめちゃ活躍しやすい"),
        ("2", "スプラシューター", "バランス型の基本武器。操作に癖がなくて一番使いやすい"),
        ("3", "N-ZAP85", "塗りが強くスペシャルでチーム貢献。対面が苦手でもOK"),
        ("4", "スプラローラー", "ヨコ振り一撃キルの爽快感がハンパない。立ち回りも覚えやすい"),
        ("5", "プロモデラーMG", "圧倒的な塗り速度。キルは苦手だけどスペシャルで貢献できる"),
    ]
    for rank, name, reason in beginner_weapons:
        html += f'<tr><td style="text-align:center">{rank}</td><td><strong>{esc(name)}</strong></td><td>{esc(reason)}</td></tr>\n'
    html += '</table>\n\n'

    # 上達のコツ
    html += '<h2>上達のコツ</h2>\n'

    html += '<h3>操作編</h3>\n'
    html += '<table>\n'
    html += '<tr><th>No.</th><th>コツ</th></tr>\n'
    op_tips = [
        "ジャイロ操作を使え！ - スティックよりも精度が段違い。プロの99%がジャイロ使い",
        "感度は低めから始める - まずは-3〜-1で始めて、慣れたら徐々に上げる",
        "イカ移動を多用する - ヒト状態よりイカ状態の方が圧倒的に速い",
        "壁を塗って登る - 高台を取ると有利。壁塗りの習慣を付けるのが超大事",
    ]
    for i, tip in enumerate(op_tips, 1):
        html += f'<tr><td style="text-align:center">{i}</td><td>{esc(tip)}</td></tr>\n'
    html += '</table>\n\n'

    html += '<h3>立ち回り編</h3>\n'
    html += '<table>\n'
    html += '<tr><th>No.</th><th>コツ</th></tr>\n'
    play_tips = [
        "自分の射程を理解する - 射程外から撃っても当たらない。これマジで大事",
        "不利な対面は逃げる - デスしないことが一番大事。無理は禁物",
        "味方と一緒に動く - 1人で突っ込まない。前線を2人以上で維持しよう",
        "スペシャルは溜まったらすぐ使う - 温存しすぎるのは初心者あるある",
        "マップ（X押し）を見る習慣 - 敵の位置を確認してから動くだけで生存率が爆上がり",
    ]
    for i, tip in enumerate(play_tips, 1):
        html += f'<tr><td style="text-align:center">{i}</td><td>{esc(tip)}</td></tr>\n'
    html += '</table>\n\n'

    # やってはいけないこと
    html += '<h2>初心者がやってはいけないこと</h2>\n'
    html += '<table>\n'
    html += '<tr><th>NG行動</th><th>なぜダメ？</th></tr>\n'
    ng_list = [
        ("敵陣に1人で突っ込む", "確実にやられる。味方と一緒に！"),
        ("同じ場所で何度もデスする", "ルートを変えよう"),
        ("スペシャルを温存しすぎる", "溜まったら使うが正解"),
        ("ギアパワーを無視する", "ランク10以降はマジで重要になる"),
        ("味方のせいにする", "自分の立ち回りを改善する方が100倍建設的"),
    ]
    for ng, reason in ng_list:
        html += f'<tr><td><strong>{esc(ng)}</strong></td><td>{esc(reason)}</td></tr>\n'
    html += '</table>\n\n'

    # 関連記事
    html += '<h2>関連記事</h2>\n'
    html += '<ul>\n'
    html += '<li><a href="../tier-list/">最強武器ランキング</a></li>\n'
    html += '<li><a href="../weapons/">全武器一覧</a></li>\n'
    html += '<li><a href="../gear-powers/">ギアパワー解説</a></li>\n'
    html += '</ul>\n'

    content = f"""---
title: "【スプラ3】初心者攻略ガイド・序盤の進め方"
linkTitle: "初心者攻略"
weight: 3
date: 2026-02-13
categories: ["初心者攻略"]
tags: ["スプラトゥーン3", "初心者"]
description: "スプラトゥーン3の初心者向け攻略ガイド。序盤の進め方、おすすめ武器、上達のコツを解説。"
---

{html}"""

    return content


# =============================================
# イベント情報（HTML構造）
# =============================================
def generate_events():
    html = ""
    html += '<p>スプラトゥーン3の最新イベント・フェス情報をまとめてるよ！</p>\n\n'

    html += '<h2>定期イベント</h2>\n'

    html += '<h3>フェス</h3>\n'
    html += '<table>\n'
    html += '<tr><th>項目</th><th>内容</th></tr>\n'
    html += '<tr><td>開催頻度</td><td>約1〜2ヶ月に1回</td></tr>\n'
    html += '<tr><td>ルール</td><td>3チームに分かれて対戦（トリカラバトル含む）</td></tr>\n'
    html += '<tr><td>報酬</td><td>スーパーサザエ（ギアパワーの変更に使える）</td></tr>\n'
    html += '<tr><td>参加方法</td><td>広場でフェスTを受け取り、チームを選ぶ</td></tr>\n'
    html += '</table>\n'
    html += '<p>ぶっちゃけフェスが一番盛り上がるイベント。参加しない理由はないよ！</p>\n\n'

    html += '<h3>ビッグラン</h3>\n'
    html += '<p>サーモンランの特別イベント。通常ステージにシャケが襲来する特殊モード。ウロコ大量獲得のチャンス！</p>\n\n'

    html += '<h3>季節イベント</h3>\n'
    html += '<p>各シーズンで限定ギアやナワバトラーのカードが追加。ロビーの「ロッカー」装飾アイテムも季節限定あり。</p>\n\n'

    html += '<h2>イベントカレンダーの確認方法</h2>\n'
    html += '<table>\n'
    html += '<tr><th>方法</th><th>詳細</th></tr>\n'
    html += '<tr><td>ゲーム内</td><td>メニュー → 「ステージ情報」で現在のスケジュール確認</td></tr>\n'
    html += '<tr><td>Nintendo Switch Online アプリ</td><td>リアルタイムでスケジュール確認可能</td></tr>\n'
    html += '<tr><td>公式X（@SplatoonJP）</td><td>イベント告知が最速</td></tr>\n'
    html += '</table>\n\n'

    html += '<h2>アップデート履歴</h2>\n'
    html += '<table>\n'
    html += '<tr><th>時期</th><th>内容</th></tr>\n'
    updates = [
        ("2022年9月", "発売開始"),
        ("2023年2月", "大型アップデートで新武器・新ステージ追加"),
        ("2023年9月", "1周年イベント"),
        ("2024年2月", "サイド・オーダー（DLC）配信開始"),
        ("2024年〜", "定期的に新武器・新ステージが追加"),
    ]
    for date, desc in updates:
        html += f'<tr><td>{esc(date)}</td><td>{esc(desc)}</td></tr>\n'
    html += '</table>\n'

    content = f"""---
title: "【スプラ3】最新イベント・フェス情報まとめ"
linkTitle: "イベント"
weight: 7
date: 2026-02-13
categories: ["イベント"]
tags: ["スプラトゥーン3", "イベント", "フェス"]
description: "スプラトゥーン3の最新イベント・フェス情報まとめ。開催中・今後のイベントスケジュールを掲載。"
---

{html}"""

    return content


# =============================================
# フェス情報（HTML構造）
# =============================================
def generate_fes():
    html = ""
    html += '<p>スプラトゥーン3のフェス情報をまとめてるよ！</p>\n\n'

    html += '<h2>フェスとは</h2>\n'
    html += '<p>3つのチームに分かれて対戦する期間限定イベント。<strong>トリカラバトル</strong>という3チーム同時対戦の特殊ルールもあるよ！</p>\n\n'

    html += '<h2>フェスの参加方法</h2>\n'
    html += '<table>\n'
    html += '<tr><th>手順</th><th>内容</th></tr>\n'
    html += '<tr><td>1</td><td>広場の「フェスの投票」からチームを選ぶ</td></tr>\n'
    html += '<tr><td>2</td><td>フェスTを受け取る（フェス期間中は自動で着用）</td></tr>\n'
    html += '<tr><td>3</td><td>フェスマッチに参加して「こうけん度」を稼ぐ</td></tr>\n'
    html += '<tr><td>4</td><td>中間発表で1位のチームは「トリカラバトル」で防衛戦</td></tr>\n'
    html += '</table>\n\n'

    html += '<h2>フェスで勝つコツ</h2>\n'
    html += '<table>\n'
    html += '<tr><th>コツ</th><th>理由</th></tr>\n'
    html += '<tr><td>とにかく数をこなす</td><td>こうけん度はバトル数に比例</td></tr>\n'
    html += '<tr><td>フレンドと組む</td><td>チームで連携した方が勝率が高い</td></tr>\n'
    html += '<tr><td>トリカラは2vs1vs1</td><td>1位チームは不利だけど、立ち回り次第で勝てる</td></tr>\n'
    html += '<tr><td>塗り武器が有利</td><td>ナワバリバトルベースだから塗り性能が大事</td></tr>\n'
    html += '</table>\n\n'

    html += '<h2>関連記事</h2>\n'
    html += '<ul>\n'
    html += '<li><a href="../tier-list/">最強武器ランキング</a></li>\n'
    html += '<li><a href="../tier-nawabari/">ナワバリバトル最強ランキング</a></li>\n'
    html += '</ul>\n'

    content = f"""---
title: "【スプラ3】フェス攻略・過去フェス結果まとめ"
linkTitle: "フェス"
weight: 8
date: 2026-02-13
categories: ["フェス"]
tags: ["スプラトゥーン3", "フェス"]
description: "スプラトゥーン3のフェス攻略と過去の全フェス結果まとめ。"
---

{html}"""

    return content


# =============================================
# ヒーローモード（HTML構造）
# =============================================
def generate_hero_mode():
    html = ""
    html += '<p>スプラトゥーン3のヒーローモード「Return of the Mammalians」の攻略ガイドだよ！</p>\n\n'

    html += '<h2>ヒーローモードとは</h2>\n'
    html += '<p>ソロプレイで楽しめるストーリーモード。<strong>No.3（主人公）</strong>としてクマサン商会と一緒に、毛深き勢力に立ち向かうストーリー。</p>\n\n'

    html += '<h2>ヒーローモードの進め方</h2>\n'
    html += '<table>\n'
    html += '<tr><th>手順</th><th>内容</th></tr>\n'
    html += '<tr><td>1</td><td>広場からマンホールに入って「オルタナ」に移動</td></tr>\n'
    html += '<tr><td>2</td><td>サイトごとにステージをクリアしていく</td></tr>\n'
    html += '<tr><td>3</td><td>イクラを集めて通路の「ケバインク」を除去して進む</td></tr>\n'
    html += '<tr><td>4</td><td>各サイトのボスを倒すとストーリーが進む</td></tr>\n'
    html += '</table>\n\n'

    html += '<h2>ヒーローモードのメリット</h2>\n'
    html += '<table>\n'
    html += '<tr><th>メリット</th><th>詳細</th></tr>\n'
    html += '<tr><td>操作の練習になる</td><td>基本動作を自然と覚えられる</td></tr>\n'
    html += '<tr><td>報酬が豪華</td><td>クリア報酬でギアやロッカーアイテムがもらえる</td></tr>\n'
    html += '<tr><td>ストーリーが面白い</td><td>スプラトゥーンの世界観を深く知れる</td></tr>\n'
    html += '</table>\n'
    html += '<p>対人が苦手な人でも楽しめるから、まずはここから始めるのがおすすめ！</p>\n\n'

    html += '<h2>関連記事</h2>\n'
    html += '<ul>\n'
    html += '<li><a href="../beginner/">初心者攻略ガイド</a></li>\n'
    html += '<li><a href="../side-order/">サイド・オーダー攻略</a></li>\n'
    html += '</ul>\n'

    content = f"""---
title: "【スプラ3】ヒーローモード攻略ガイド"
linkTitle: "ヒーローモード"
weight: 9
date: 2026-02-13
categories: ["ヒーローモード"]
tags: ["スプラトゥーン3", "ヒーローモード"]
description: "スプラトゥーン3のヒーローモード攻略。全ステージの攻略法とボスの倒し方を解説。"
---

{html}"""

    return content


# =============================================
# サイド・オーダー（HTML構造）
# =============================================
def generate_side_order():
    html = ""
    html += '<p>スプラトゥーン3の有料DLC「エキスパンション・パス」に含まれる「サイド・オーダー」の攻略ガイドだよ！</p>\n\n'

    html += '<h2>サイド・オーダーとは</h2>\n'
    html += '<p><strong>秩序の塔</strong>を登っていくローグライク風のモード。フロアごとにランダムで選ばれるステージを攻略して、最上階を目指す！</p>\n\n'

    html += '<h2>基本システム</h2>\n'
    html += '<table>\n'
    html += '<tr><th>要素</th><th>内容</th></tr>\n'
    html += '<tr><td>カラーチップ</td><td>パレットで集めて武器を強化</td></tr>\n'
    html += '<tr><td>ドローン</td><td>フロアごとに選んで効果を得る</td></tr>\n'
    html += '<tr><td>失敗時</td><td>最初からやり直し（ローグライク要素）</td></tr>\n'
    html += '<tr><td>クリア報酬</td><td>ポイントがもらえて、次の挑戦が有利に</td></tr>\n'
    html += '</table>\n\n'

    html += '<h2>攻略のコツ</h2>\n'
    html += '<table>\n'
    html += '<tr><th>コツ</th><th>詳細</th></tr>\n'
    html += '<tr><td>カラーチップは偏らせる</td><td>1つのステータスを集中強化した方が強い</td></tr>\n'
    html += '<tr><td>攻撃力を最優先</td><td>敵を速く倒せれば被弾も減る</td></tr>\n'
    html += '<tr><td>回復系も大事</td><td>終盤は被ダメが増えるから保険に</td></tr>\n'
    html += '</table>\n'
    html += '<p>まずは何度もチャレンジして、システムに慣れるのが大事！</p>\n\n'

    html += '<h2>関連記事</h2>\n'
    html += '<ul>\n'
    html += '<li><a href="../hero-mode/">ヒーローモード攻略</a></li>\n'
    html += '<li><a href="../beginner/">初心者攻略ガイド</a></li>\n'
    html += '</ul>\n'

    content = f"""---
title: "【スプラ3】サイド・オーダー攻略ガイド"
linkTitle: "サイド・オーダー"
weight: 10
date: 2026-02-13
categories: ["サイド・オーダー"]
tags: ["スプラトゥーン3", "サイド・オーダー", "DLC"]
description: "スプラトゥーン3のDLC「サイド・オーダー」の攻略情報。"
---

{html}"""

    return content


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
        print(f"  {filename}: {lines}行 ({size_kb:.1f}KB)")
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
        print(f"  {filename}: {lines}行 ({size_kb:.1f}KB)")
        total += 1

    # 3. 武器個別ページ
    weapon_count = generate_weapon_pages()
    print(f"  weapons/: {weapon_count}件の武器個別ページ")
    total += weapon_count + 1

    # 4. ステージ個別ページ
    stage_count = generate_stage_pages()
    print(f"  stages/: {stage_count}件のステージ個別ページ")
    total += stage_count + 1

    print(f"\n全{total}ページ生成完了！")
    print(f"出力先: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
