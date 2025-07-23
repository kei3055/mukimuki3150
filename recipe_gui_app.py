import streamlit as st
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

# --- Streamlit UI ---
st.set_page_config(page_title="レシピ提案アプリ", layout="wide")
st.title("🍳 材料と栄養バランスからレシピを提案します")

st.markdown("### 🛒 材料（日本語・カンマ区切り）")
ingredients_input = st.text_area("例: 卵, トマト, チーズ", height=100)

st.markdown("### 📊 栄養の目安（1食分）")
col1, col2, col3, col4 = st.columns(4)
with col1:
    cal = st.number_input("エネルギー (kcal)", min_value=0.0)
with col2:
    protein = st.number_input("タンパク質 (g)", min_value=0.0)
with col3:
    fat = st.number_input("脂質 (g)", min_value=0.0)
with col4:
    carbs = st.number_input("炭水化物 (g)", min_value=0.0)

if st.button("🔍 レシピ検索"):
    if not ingredients_input.strip():
        st.warning("材料を入力してください。")
    else:
        ingredients_ja = [i.strip() for i in ingredients_input.split(",")]
        with st.spinner("翻訳中..."):
            ingredients_en = [translate_ja_to_en(i) for i in ingredients_ja]

        target = {
            "calories": cal,
            "protein": protein,
            "fat": fat,
            "carbs": carbs
        }

        with st.spinner("レシピを検索中..."):
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

        st.markdown("### 📋 提案レシピ一覧")
        for _, line in suggestions:
            st.write(line)
