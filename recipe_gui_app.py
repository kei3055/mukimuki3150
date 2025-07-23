import tkinter as tk
from tkinter import ttk, scrolledtext
import requests

# --- APIキーを設定 ---
DEEPL_API_KEY = "c58a046e-653d-4d91-a5f8-561a5ce4c988:fx"
SPOONACULAR_API_KEY = "00d7cdc9144a4c88a04564128c5ef8ce"

# --- DeepL翻訳関数（日本語→英語） ---
def translate_ja_to_en(text):
    url = "https://api-free.deepl.com/v2/translate"
    params = {
        "auth_key": DEEPL_API_KEY,
        "text": text,
        "source_lang": "JA",
        "target_lang": "EN"
    }
    res = requests.post(url, data=params)
    return res.json()["translations"][0]["text"] if res.status_code == 200 else text

# --- DeepL翻訳関数（英語→日本語） ---
def translate_en_to_ja(text):
    url = "https://api-free.deepl.com/v2/translate"
    params = {
        "auth_key": DEEPL_API_KEY,
        "text": text,
        "source_lang": "EN",
        "target_lang": "JA"
    }
    res = requests.post(url, data=params)
    return res.json()["translations"][0]["text"] if res.status_code == 200 else text

# --- Spoonacularで材料検索 ---
def search_recipes(ingredients_en):
    url = "https://api.spoonacular.com/recipes/findByIngredients"
    params = {
        "apiKey": SPOONACULAR_API_KEY,
        "ingredients": ",".join(ingredients_en),
        "number": 5,
        "ranking": 1,
        "ignorePantry": True
    }
    res = requests.get(url, params=params)
    return res.json()

# --- 栄養情報取得 ---
def get_nutrition(recipe_id):
    url = f"https://api.spoonacular.com/recipes/{recipe_id}/nutritionWidget.json"
    params = {"apiKey": SPOONACULAR_API_KEY}
    res = requests.get(url, params=params)
    return res.json() if res.status_code == 200 else None

# --- 栄養スコア計算 ---
def calc_score(nutrition, target):
    try:
        def clean(v): return float(v.replace("g", "").replace("kcal", "").strip())
        return sum(abs(clean(nutrition[k]) - target[k]) for k in ["calories", "protein", "fat", "carbs"])
    except:
        return float("inf")

# --- レシピ提案 ---
def suggest_recipes():
    ingredients_ja = ingredients_entry.get("1.0", tk.END).strip().split(",")
    ingredients_en = [translate_ja_to_en(i.strip()) for i in ingredients_ja]

    target = {
        "calories": float(entry_cal.get()),
        "protein": float(entry_protein.get()),
        "fat": float(entry_fat.get()),
        "carbs": float(entry_carbs.get())
    }

    results = search_recipes(ingredients_en)
    suggestions = []

    for recipe in results:
        nutrition = get_nutrition(recipe["id"])
        if not nutrition:
            continue

        score = calc_score(nutrition, target)
        title_ja = translate_en_to_ja(recipe["title"])
        missed_ja = [translate_en_to_ja(i['name']) for i in recipe.get("missedIngredients", [])]

        if not missed_ja:
            suggestions.append((score, f"✅ {title_ja}（材料すべて揃っています）"))
        else:
            suggestions.append((score, f"🟡 {title_ja}（あと {', '.join(missed_ja)} があれば作成可能）"))

    suggestions.sort(key=lambda x: x[0])
    result_box.delete("1.0", tk.END)
    result_box.insert(tk.END, "📋 提案レシピ一覧:\n\n")
    for _, line in suggestions:
        result_box.insert(tk.END, line + "\n")

# --- GUIセットアップ ---
root = tk.Tk()
root.title("レシピ提案アプリ")
root.state("zoomed")  # 画面いっぱいに表示

# --- フレームとラベル ---
frame = ttk.Frame(root, padding=20)
frame.pack(fill=tk.BOTH, expand=True)

ttk.Label(frame, text="🛒 材料（日本語・カンマ区切り）:").grid(column=0, row=0, sticky=tk.W)
ingredients_entry = scrolledtext.ScrolledText(frame, width=80, height=3)
ingredients_entry.grid(column=0, row=1, columnspan=4, pady=5)

ttk.Label(frame, text="📊 栄養の目安（1食分）").grid(column=0, row=2, sticky=tk.W, pady=(10, 2))
ttk.Label(frame, text="エネルギー(kcal):").grid(column=0, row=3, sticky=tk.E)
entry_cal = ttk.Entry(frame, width=10)
entry_cal.grid(column=1, row=3)

ttk.Label(frame, text="タンパク質(g):").grid(column=2, row=3, sticky=tk.E)
entry_protein = ttk.Entry(frame, width=10)
entry_protein.grid(column=3, row=3)

ttk.Label(frame, text="脂質(g):").grid(column=0, row=4, sticky=tk.E)
entry_fat = ttk.Entry(frame, width=10)
entry_fat.grid(column=1, row=4)

ttk.Label(frame, text="炭水化物(g):").grid(column=2, row=4, sticky=tk.E)
entry_carbs = ttk.Entry(frame, width=10)
entry_carbs.grid(column=3, row=4)

search_button = ttk.Button(frame, text="🔍 レシピ検索", command=suggest_recipes)
search_button.grid(column=0, row=5, columnspan=4, pady=10)

result_box = scrolledtext.ScrolledText(frame, width=100, height=20)
result_box.grid(column=0, row=6, columnspan=4, pady=10)

root.mainloop()
