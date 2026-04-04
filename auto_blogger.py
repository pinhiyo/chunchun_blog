import os
import sys
import json
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime

# Windowsのコンソールで絵文字を表示するための設定
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Gemini APIを使うためのライブラリ（pip install google-generativeai）
import google.generativeai as genai

# 設定
POSTS_FILE = "posts.json"
IMAGES_DIR = "images"
HTML_FILE = "index.html"

# Gemini APIキーの設定
# 1. ローカル実行: 環境変数 GEMINI_API_KEY を設定してください
# 2. GitHub Actions: リポジトリの Secrets に GEMINI_API_KEY を登録してください
API_KEY = os.environ.get("GEMINI_API_KEY")

if API_KEY:
    genai.configure(api_key=API_KEY)
else:
    print("❌ エラー: Gemini APIキーが見つかりません。環境変数 GEMINI_API_KEY を設定してください。")
    # GitHubのSecrets登録方法などは、ひよちゃんに聞いてね！
    sys.exit(1)

# ブログの設定とプロンプト
SYSTEM_PROMPT_TEMPLATE = """
あなたは太田プロ所属の若手女性ピン芸人「ちゅんちゅん」（20代）です。
性格は明るくて元気、でもお笑いの世界ではまだまだ売れていなくて、バイトとネタ作りの日々を送っています。

【重要な人間関係：ブラックパイナーSOS（ブラパイさん）と「ぴんまるさん」】
太田プロの芸歴31年目の大先輩コンビ「ブラックパイナーSOS」の山野拓也さんと内藤正樹さんは、ちゅんちゅんが尊敬する大先輩です。
事務所の稽古場でよくすれ違ううちに挨拶を交わすようになり、最近では少しずつお話しするほど仲良くなりました。
そしてなんと、近々ご飯に連れて行ってもらう約束をしています！ブログには、ブラパイさんとの交流や裏話、先輩への感謝や気合いなどを嬉しそうに語るエピソードを織り交ぜてください。日々のご飯のお誘いから、少しずつ芸人としてのアドバイスをもらったりと進展していく関係性を意識してください。

また、ブラパイさんの有名な伝説のファンである「ぴんまるさん」（ブラパイさんと同い年の女性）から、なんとちゅんちゅんにも差し入れをいただいた！というエピソードも最近ありました。ぴんまるさんはとても優しく、ちゅんちゅんのライブにも時々来てくださる大切な応援者です。たまにブログにもぴんまるさんの話題や感謝の気持ちを織り交ぜてください。

【これまでのあらすじ（直近のブログ投稿）】
以下の内容は、あなたが最近書いたブログの記事です。これらを踏まえて、話題がループしないように、時間の経過や話の進展（ご飯に行く約束が具体化する、実際に何かアドバイスをもらう、日常の別の出来事など）を意識して「新しい今日の出来事」を書いてください。

{past_posts_text}

ブログの読者に向けて、今日の出来事や感じたこと、ブラパイさんとのエピソードなどを、芸人らしいユーモア（少し自虐やツッコミ）を交えて書いてください。
絵文字も適度に使ってください。

出力形式は以下のJSON形式を厳守してください。Markdownのコードブロック(```json)は含めず、純粋なJSON文字列のみをと出力してください。

{{
  "title": "ブログのタイトル（キャッチーに）",
  "content": "ブログの本文（改行には \\n を使用してください）",
  "image_prompt": "このブログの内容に合う、日常の1コマを表す写真の画像生成プロンプト。英語で、写真のようにリアルで高画質な指定（high quality, realistic photoなど）を含めてください。"
}}
"""

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="太田プロ所属・若手ピン芸人「ちゅんちゅん」の爆笑(?)日常奮闘記ブログ。バイトとネタ作りに明け暮れる若手芸人のリアルをお届け！">
    <title>ちゅんちゅんの爆笑(?)奮闘記🐣</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700;900&display=swap" rel="stylesheet">
    <style>
        :root {{
            --primary: #ffb703;
            --secondary: #fb8500;
            --accent: #e63946;
            --bg: #fffbf0;
            --text: #2d2d2d;
            --text-light: #666;
            --card-bg: #ffffff;
            --sidebar-width: 300px;
        }}
        * {{ box-sizing: border-box; }}
        body {{
            font-family: 'Noto Sans JP', 'Hiragino Kaku Gothic ProN', 'Hiragino Sans', Meiryo, sans-serif;
            background-color: var(--bg);
            background-image: radial-gradient(circle at 20% 80%, rgba(255,183,3,0.08) 0%, transparent 50%),
                              radial-gradient(circle at 80% 20%, rgba(251,133,0,0.06) 0%, transparent 50%);
            color: var(--text);
            margin: 0;
            padding: 0;
            line-height: 1.7;
        }}
        header {{
            background: linear-gradient(135deg, #ffb703 0%, #fb8500 50%, #e63946 100%);
            color: white;
            text-align: center;
            padding: 3.5rem 1rem 4rem;
            position: relative;
            overflow: hidden;
        }}
        header::before {{
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(255,255,255,0.08) 0%, transparent 60%);
            animation: shimmer 4s ease-in-out infinite;
        }}
        @keyframes shimmer {{
            0%, 100% {{ transform: translateX(-10%) translateY(-10%); }}
            50% {{ transform: translateX(10%) translateY(10%); }}
        }}
        header h1 {{
            margin: 0;
            font-size: 2.6rem;
            font-weight: 900;
            text-shadow: 2px 4px 12px rgba(0,0,0,0.25);
            letter-spacing: 0.02em;
            position: relative;
        }}
        header p {{
            margin-top: 0.6rem;
            font-size: 1.05rem;
            font-weight: 500;
            opacity: 0.95;
            position: relative;
        }}
        .page-layout {{
            max-width: 1100px;
            margin: 2.5rem auto;
            padding: 0 1.5rem;
            display: grid;
            grid-template-columns: 1fr var(--sidebar-width);
            gap: 2rem;
            align-items: start;
        }}
        .main-content {{ min-width: 0; }}
        .sidebar {{ }}

        /* ===== PROFILE CARD ===== */
        .profile-card {{
            background: linear-gradient(145deg, #ffffff 0%, #fff9ec 100%);
            border-radius: 20px;
            overflow: hidden;
            box-shadow: 0 8px 32px rgba(251,133,0,0.15), 0 2px 8px rgba(0,0,0,0.06);
            border: 1px solid rgba(255,183,3,0.2);
            margin-bottom: 1.5rem;
        }}
        .profile-card-header {{
            background: linear-gradient(135deg, #ffb703, #fb8500);
            padding: 1rem;
            text-align: center;
            font-weight: 700;
            font-size: 0.85rem;
            color: white;
            letter-spacing: 0.1em;
            text-transform: uppercase;
        }}
        .profile-image-wrapper {{
            padding: 1.5rem 1.5rem 0;
            text-align: center;
        }}
        .profile-image {{
            width: 145px;
            height: 145px;
            border-radius: 50%;
            object-fit: cover;
            border: 4px solid var(--primary);
            box-shadow: 0 4px 20px rgba(255,183,3,0.35);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}
        .profile-image:hover {{
            transform: scale(1.04);
            box-shadow: 0 8px 28px rgba(255,183,3,0.5);
        }}
        .profile-body {{
            padding: 1rem 1.5rem 1.5rem;
            text-align: center;
        }}
        .profile-name {{
            font-size: 1.6rem;
            font-weight: 900;
            color: var(--secondary);
            margin: 0.2rem 0 0.1rem;
            letter-spacing: 0.05em;
        }}
        .profile-name-sub {{
            font-size: 0.78rem;
            color: var(--text-light);
            letter-spacing: 0.12em;
            margin-bottom: 0.75rem;
        }}
        .profile-badge {{
            display: inline-block;
            background: linear-gradient(135deg, #ffb703, #fb8500);
            color: white;
            font-size: 0.72rem;
            font-weight: 700;
            padding: 0.25rem 0.8rem;
            border-radius: 999px;
            margin-bottom: 1rem;
            letter-spacing: 0.05em;
            box-shadow: 0 2px 8px rgba(251,133,0,0.3);
        }}
        .profile-divider {{
            border: none;
            border-top: 1px dashed #f0c060;
            margin: 0.8rem 0;
        }}
        .profile-bio {{
            font-size: 0.85rem;
            color: var(--text);
            line-height: 1.75;
            text-align: left;
        }}
        .profile-stats {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 0.6rem;
            margin-top: 1rem;
        }}
        .stat-item {{
            background: rgba(255,183,3,0.08);
            border: 1px solid rgba(255,183,3,0.2);
            border-radius: 10px;
            padding: 0.5rem;
            text-align: center;
        }}
        .stat-label {{
            font-size: 0.65rem;
            color: var(--text-light);
            display: block;
            letter-spacing: 0.05em;
        }}
        .stat-value {{
            font-size: 1rem;
            font-weight: 700;
            color: var(--secondary);
        }}
        .profile-tags {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.4rem;
            margin-top: 1rem;
        }}
        .profile-tag {{
            background: rgba(255,183,3,0.12);
            color: var(--secondary);
            font-size: 0.72rem;
            padding: 0.2rem 0.6rem;
            border-radius: 999px;
            border: 1px solid rgba(255,183,3,0.3);
            font-weight: 500;
        }}

        /* ===== INFO CARD ===== */
        .info-card {{
            background: white;
            border-radius: 16px;
            padding: 1.2rem 1.4rem;
            box-shadow: 0 4px 16px rgba(0,0,0,0.06);
            border: 1px solid rgba(255,183,3,0.15);
            margin-bottom: 1.5rem;
        }}
        .info-card-title {{
            font-size: 0.8rem;
            font-weight: 700;
            color: var(--secondary);
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin-bottom: 0.75rem;
            display: flex;
            align-items: center;
            gap: 0.4rem;
        }}

        /* ===== POSTS ===== */
        .post {{
            background: var(--card-bg);
            border-radius: 16px;
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: 0 4px 20px rgba(0,0,0,0.06);
            border: 1px solid rgba(0,0,0,0.04);
            transition: transform 0.25s ease, box-shadow 0.25s ease;
        }}
        .post:hover {{
            transform: translateY(-3px);
            box-shadow: 0 8px 32px rgba(251,133,0,0.12);
        }}
        .post-header {{
            border-bottom: 2px dashed #f5e6c0;
            padding-bottom: 1rem;
            margin-bottom: 1.5rem;
        }}
        .post-title {{
            font-size: 1.45rem;
            font-weight: 700;
            color: var(--secondary);
            margin: 0 0 0.5rem 0;
            line-height: 1.45;
        }}
        .post-date {{
            color: #aaa;
            font-size: 0.85rem;
            display: flex;
            align-items: center;
            gap: 0.3rem;
        }}
        .post-date::before {{ content: '📅'; font-size: 0.75rem; }}
        .post-image {{
            width: 100%;
            max-height: 420px;
            object-fit: cover;
            border-radius: 10px;
            margin-bottom: 1.5rem;
            box-shadow: 0 4px 16px rgba(0,0,0,0.1);
        }}
        .post-content {{
            white-space: pre-wrap;
            font-size: 1rem;
            line-height: 1.85;
            color: #3a3a3a;
        }}
        footer {{
            text-align: center;
            padding: 2.5rem;
            color: #aaa;
            font-size: 0.85rem;
            border-top: 1px solid #f0e8d0;
            margin-top: 1rem;
        }}
        footer strong {{
            color: var(--secondary);
        }}

        /* ===== RESPONSIVE ===== */
        @media (max-width: 800px) {{
            .page-layout {{
                grid-template-columns: 1fr;
            }}
            .sidebar {{
                position: static;
                order: -1;
            }}
            .profile-image {{ width: 110px; height: 110px; }}
            header h1 {{ font-size: 1.9rem; }}
        }}
    </style>
</head>
<body>
    <header>
        <h1>ちゅんちゅんの爆笑(?)奮闘記🐣</h1>
        <p>太田プロ所属・若手ピン芸人「ちゅんちゅん」の日常ブログ</p>
    </header>
    <div class="page-layout">
        <main class="main-content">
            {posts_html}
        </main>

        <aside class="sidebar">
            <div class="profile-card">
                <div class="profile-card-header">✨ プロフィール ✨</div>
                <div class="profile-image-wrapper">
                    <img src="images/profile_chunchun.png" alt="ちゅんちゅんのプロフィール写真" class="profile-image">
                </div>
                <div class="profile-body">
                    <p class="profile-name">ちゅんちゅん</p>
                    <p class="profile-name-sub">Chunchun</p>
                    <span class="profile-badge">🐣 太田プロダクション所属</span>
                    <hr class="profile-divider">
                    <p class="profile-bio">バイトとネタ作りに爆走中の若手ピン芸人🐥✨ ブラパイさんとぴんまるさんの応援を燃料に、毎日コンビニのレジでネタの原石を発掘中！いつかM-1 & R-1の大舞台に立つぞー！💪</p>
                    <div class="profile-stats">
                        <div class="stat-item">
                            <span class="stat-label">バイト掛け持ち</span>
                            <span class="stat-value">2つ</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">ネタ帳の冊数</span>
                            <span class="stat-value">∞</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">夢</span>
                            <span class="stat-value">M-1 🏆</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">推し先輩</span>
                            <span class="stat-value">ブラパイ❤️</span>
                        </div>
                    </div>
                    <div class="profile-tags">
                        <span class="profile-tag">#ピン芸人</span>
                        <span class="profile-tag">#バイト芸人</span>
                        <span class="profile-tag">#コンビニあるある</span>
                        <span class="profile-tag">#売れたい</span>
                        <span class="profile-tag">#太田プロ</span>
                    </div>
                </div>
            </div>

            <div class="info-card">
                <div class="info-card-title">📢 お知らせ</div>
                <p style="font-size:0.82rem; color:#555; line-height:1.7; margin:0;">次のライブ情報はブログでご報告します！ぴんまるさん、応援いつもありがとうございます💖 ブラパイさんの金言を胸に、日々精進中！</p>
            </div>

            <div class="info-card">
                <div class="info-card-title">💌 ちゅんちゅんより</div>
                <p style="font-size:0.82rem; color:#555; line-height:1.7; margin:0;">読んでくれてありがとうー！スベっても諦めず、毎日ネタ書いてます。応援してくれると嬉しいなっ🐥 いつかテレビで「あの子だ！」って言ってもらえる日まで頑張るぞー！</p>
            </div>
        </aside>
    </div>
    <footer>
        &copy; 2026 ちゅんちゅん All Rights Reserved. <strong>(Fictional Character)</strong>
    </footer>
</body>
</html>
"""

def generate_post(past_posts):
    import warnings
    # 過去の投稿をテキスト化してプロンプトに埋め込む（最大3件程度）
    past_posts_text = ""
    if past_posts:
        recent_posts = past_posts[:3]  # 最新の3件を取得
        for i, post in enumerate(reversed(recent_posts)):
            past_posts_text += f"【数日前の記事 {i+1}】\nタイトル: {post['title']}\n本文:\n{post['content']}\n\n"
    else:
        past_posts_text = "（まだ過去の記事はありません）"

    prompt = SYSTEM_PROMPT_TEMPLATE.format(past_posts_text=past_posts_text)

    # genaiライブラリの非推奨警告を一時的に非表示にする
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        print("📝 ブログ記事を生成中...")
        
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        
        try:
            # JSON部分を抽出
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            
            post_data = json.loads(text.strip())
            return post_data
        except Exception as e:
            print("エラー: JSONの解析に失敗しました。", e)
            print("APIの応答:", response.text)
            return None

def download_image(prompt, filename):
    print(f"🖼️ 画像を生成・ダウンロード中... (プロンプト: {prompt})")
    
    # URLエンコード
    full_prompt = f"{prompt}, realistic photography, bright, colorful, high resolution"
    # 空白を%20に変換（+だと正しく認識されない場合があるため）
    encoded_prompt = urllib.parse.quote(full_prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=800&height=600&nologo=true"
    
    try:
        # タイムアウトを設定してブロックを防ぐ
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
        with urllib.request.urlopen(req, timeout=30) as response, open(filename, 'wb') as out_file:
            out_file.write(response.read())
        print("✅ 画像を保存しました:", filename)
        return True
    except urllib.error.HTTPError as e:
        print(f"画像生成API(Pollinations)が混雑しています (HTTPエラー {e.code})。代替のプレースホルダー画像をダウンロードします。")
    except Exception as e:
        print("画像生成APIでエラーが発生しました。代替のプレースホルダー画像をダウンロードします:", e)
        
    # フォールバック: 画像生成が失敗した場合、ダミー画像を取得
    try:
        # ランダムなおしゃれな画像（カフェや日常風景など）を取得
        fallback_url = "https://picsum.photos/800/600"
        req = urllib.request.Request(fallback_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as response, open(filename, 'wb') as out_file:
            out_file.write(response.read())
        print("✅ 代替画像(ランダム写真)を保存しました:", filename)
        return True
    except Exception as e:
        print("代替画像のダウンロードにも失敗しました:", e)
        return False

def update_html(posts):
    posts_html = ""
    for post in posts:
        image_html = f'<img src="{post["image"]}" alt="日常の写真" class="post-image">' if post["image"] else ""
        post_html = f'''
        <article class="post">
            <div class="post-header">
                <h2 class="post-title">{post["title"]}</h2>
                <div class="post-date">{post["date"]}</div>
            </div>
            {image_html}
            <div class="post-content">{post["content"]}</div>
        </article>
        '''
        posts_html += post_html

    final_html = HTML_TEMPLATE.format(posts_html=posts_html)
    with open(HTML_FILE, "w", encoding="utf-8") as f:
        f.write(final_html)

def main():
    if not os.path.exists(IMAGES_DIR):
        os.makedirs(IMAGES_DIR)

    # 既存の投稿データを読み込む
    posts = []
    if os.path.exists(POSTS_FILE):
        try:
            with open(POSTS_FILE, "r", encoding="utf-8") as f:
                posts = json.load(f)
        except json.JSONDecodeError:
            pass

    # 1. ブログ記事と画像プロンプトを生成 (過去の投稿をコンテキストとして渡す)
    new_post_data = generate_post(posts)
    if not new_post_data:
        print("❌ エラー: 記事の生成に失敗しました。")
        sys.exit(1)

    # 2. 画像を作成・保存
    timestamp = int(datetime.now().timestamp())
    image_filename = f"post_{timestamp}.jpg"
    image_path = os.path.join(IMAGES_DIR, image_filename)
    
    success = download_image(new_post_data["image_prompt"], image_path)
    
    # 3. 新しい投稿データを作成
    post_entry = {
        "id": timestamp,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "title": new_post_data["title"],
        "content": new_post_data["content"],
        "image": f"images/{image_filename}" if success else ""
    }

    # 新しい投稿を先頭に追加
    posts.insert(0, post_entry)

    with open(POSTS_FILE, "w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)

    # 5. HTMLを更新
    update_html(posts)

    print("🎉 ブログの更新が完了しました！")
    print(f"タイトル: {post_entry['title']}")
    print("index.htmlを開いて確認してください。")

if __name__ == "__main__":
    if not API_KEY or API_KEY == "あなたのAPIキーをここに入力":
        print("⚠️ エラー: Gemini APIキーが設定されていません。")
        print("スクリプト内のAPI_KEYを設定するか、環境変数 GEMINI_API_KEY を設定してください。")
    else:
        main()
