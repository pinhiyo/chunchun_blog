import os
import sys
import json
import warnings
import google.generativeai as genai

# Windowsのコンソールで文字化けを防ぐ
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

API_KEY = os.environ.get("GEMINI_API_KEY")

print("🔍 診断モード：環境変数のチェックを開始します...")
if not API_KEY:
    print("❌ エラー: Gemini APIキーが見つかりません。環境変数 GEMINI_API_KEY を設定してください。")
    sys.exit(1)

# セキュリティのため最初の2文字と長さだけ表示
key_prefix = API_KEY[:2] if len(API_KEY) > 2 else "??"
print(f"✅ GEMINI_API_KEY を検出しました（先頭: {key_prefix}... / 長さ: {len(API_KEY)}文字）")

genai.configure(api_key=API_KEY)
print("✅ Gemini APIの設定に成功しました。")

PROMPT = """
あなたは、太田プロダクションに所属する若手女性ピン芸人「ちゅんちゅん」（20代）です。
普段はカフェや居酒屋でアルバイトをしながら、懸命にお笑いの道を志しています。
先輩芸人「ブラックパイナーSOS」のお二人を尊敬しており、またファンである「ぴんまるさん」にもお世話になっています。

今回、あなたがいつもライブやオーディションでやっている「渾身の勝負ネタ（ピン芸）」の台本を、最初から最後までフルコーラスで書き起こしてください。

【ネタの条件】
- ちゅんちゅんらしい、少し自虐や「売れてない若手芸人・バイトあるある」を交えた等身大のネタであること
- 明るく元気なキャラクターが伝わること
- フリップ芸、一人コント、漫談などスタイルは自由
- 観客（または審査員）の笑いどころや、ちゅんちゅんの動き・表情のト書き（※）も入れてください
- とにかく、一生懸命さが空回りしてクスッと笑えるような構成にしてください

出力形式：
Markdownなどのプレーンテキストで、台本形式（セリフとト書き）で出力してください。
"""

def generate_routine():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        print("🎙️ ちゅんちゅんの漫談/コント作成中...")
        model = genai.GenerativeModel('gemini-flash-latest')
        response = model.generate_content(PROMPT)
        print("\n================== 🐣ちゅんちゅん 渾身のネタ 🐣 ==================\n")
        print(response.text)
        print("\n=================================================================\n")
        
        # ファイルにも保存しておく
        with open("chunchun_neta.md", "w", encoding="utf-8") as f:
            f.write(response.text)
        print("✅ ネタ台本を chunchun_neta.md に保存しました！")

if __name__ == "__main__":
    generate_routine()
