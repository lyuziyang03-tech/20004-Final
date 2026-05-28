import streamlit as st
import pandas as pd
from pathlib import Path
from collections import Counter
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from sudachipy import tokenizer, dictionary
import folium
from streamlit_folium import st_folium


# Find the working directory. Piece together two csv files.
# __file__: the location of the current .py file
# resolve(): turn it into the full absolute path
# parent: the directory containing the file (APP_DIR)
APP_DIR = Path(__file__).resolve().parent
DATA_DIR = APP_DIR / "output"
EXCERPTS_PATH = DATA_DIR / "excerpt.csv"
SPEECHES_PATH = DATA_DIR / "full.csv"

# Load the data
file_path = EXCERPTS_PATH
df = pd.read_csv(file_path, encoding="utf-8-sig")

# I want to build an interactive wordcloud. I need "text" by "year" and by "decade".
# csv: document_id,excerpt_id,chunk_number,speaker,date,year,decade,text,word_count,source_url

# Get columns from df: https://pandas.pydata.org/docs/getting_started/intro_tutorials/03_subset_data.html
# Drop any rows that have missing data (not used): https://pandas.pydata.org/docs/user_guide/10min.html#missing-data
ydf = df[["text", "year"]].dropna(how="any")
ddf = df[["text", "decade"]].dropna(how="any")

# Define the words to filter.
DEFAULT_EXTRA_STOPS = {"〓","〓〓", "台灣", "臺灣", "必要", "所管", "議案", "政府", "地方","それ","通り","やつ","大體","問題","只今", "こと","事","もの","物","ところ","所","ため","為","わけ","訳","はず","筈", "つもり","積り","うち","内","そと","外","ほか","よし","由","ゆえ","故", "がてら","がてらに","次第","しだい","段","だん","儀","ぎ","始末","しまつ", "趣","おもむき","有様","ありさま","以上","以下","中","内情","事情"}

# Tokenizing Japanese
tokenizer_obj = dictionary.Dictionary().create()
mode = tokenizer.Tokenizer.SplitMode.C

# Pre modern records consist of kanjis and katakanas. The tokenizer works betteer when katakanas are converted to hiraganas.
def kata_to_hira(text: str) -> str:
    result = []
    for ch in str(text):
        code = ord(ch)
        if 0x30A0 <= code <= 0x30FF:
            result.append(chr(code - 0x60))
        else:
            result.append(ch)
    return "".join(result)

# Tokenize using sudachi and only return nouns (it is assumed that topics are conveyed in nouns)
def extract_nouns(text):
    text = kata_to_hira(text)

    MAX_CHUNK = 3000  # 字元分段（穩定又不慢）

    nouns = []

    for i in range(0, len(text), MAX_CHUNK):
        chunk = text[i:i + MAX_CHUNK]

        try:
            tokens = tokenizer_obj.tokenize(chunk, mode)
        except Exception:
            continue  # 某段壞掉就跳過，不整個 crash

        for t in tokens:
            base = t.dictionary_form()
            pos = t.part_of_speech()[0]

            if "名詞" in pos and len(base) > 1:
                nouns.append(base)

    return nouns

# Build WordCloud with nouns not on the exception list only
def build_wordcloud(dataframe, width, height, top_n):
    words = []

    for text in dataframe["text"]:
        nouns = extract_nouns(text)
        nouns = [n for n in nouns if n not in DEFAULT_EXTRA_STOPS]
        words.extend(nouns)

    freq = Counter(words)

    if not freq:
        return None, None

    freq = dict(freq.most_common(top_n))

    wc = WordCloud(
        width=width,
        height=height,
        background_color="white",
        font_path="C:/Windows/Fonts/msgothic.ttc"
    ).generate_from_frequencies(freq)

    return wc, freq

# The title and caption
st.set_page_config(page_title="帝国議会会議録における台湾関連テキストの可視化(1894-1945)", layout="wide")

st.title("帝国議会会議録における台湾関連テキストの可視化(1894-1945)")
st.caption("Visualization of Taiwan-Related Texts in the Proceedings of the Imperial Diet (1894-1945)")

with st.sidebar:
    st.header("Controls")
    top_n = st.slider("Top n nouns", 5, 50, 40)
    wc_width = st.slider("Width", 400, 1200, 800)
    wc_height = st.slider("Height", 200, 800, 400)

# Sliders: https://docs.streamlit.io/develop/api-reference/widgets/st.slider
year = st.slider("Select a year:", 1894, 1945, 1894)


col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    st.subheader("WordCloud")

    wc_year, freq = build_wordcloud(
        ydf[ydf["year"] == year],
        wc_width,
        wc_height,
        top_n
    )

    if wc_year is None:
        st.warning("No data.")
    else:
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.imshow(wc_year, interpolation="bilinear")
        ax.axis("off")
        st.pyplot(fig)

timeline = {
1894: "First Sino-Japanese War begins / 日清戦争勃発",
1895: "Treaty of Shimonoseki cedes Taiwan to Japan; Taiwan Governor-General's Office established; Resistance war in Taiwan / 下関条約で台湾割譲・台湾総督府設置・乙未戦争",
1896: "Law No. 6-3 implemented; Aboriginal Affairs Office established; Taiwan–Japan shipping route opened / 六三法施行・撫墾署設置・内台航路開通",
1897: "Deadline for nationality selection for Taiwan residents; Takano incident / 国籍選択期限・高野孟矩事件",
1898: "Kodama Gentarō appointed Governor-General; Baojia system implemented; Land survey begins / 児玉源太郎総督就任・保甲制度施行・土地調査開始",
1899: "Medical school established; Bank of Taiwan opened / 医学校設立・台湾銀行開業",
1900: "Taiwan Sugar Company established / 製糖会社設立",
1901: "Irrigation regulations issued; Customary practices survey begins / 埤圳規則公布・旧慣調査開始",
1902: "Yunlin incident / 雲林事件",
1905: "Land survey completed; Census system implemented / 土地調査完了・戸口調査施行",
1906: "Chiayi earthquake; Law revision of Six-Three Law / 嘉義地震・六三法改正",
1907: "Beipu incident; Zhenzi Mountain battle / 北埔事件・枕頭山戦闘",
1908: "Western trunk railway completed / 縦貫鉄道全通",
1911: "Alishan railway opened / 阿里山鉄道開通",
1912: "Lin Qipu incident; Luo Fuxing incident / 林杞埔事件・羅福星事件",
1913: "Taipei bus service begins / 台北バス運行開始",
1914: "Indigenous conflict in southern Taiwan; Taiwan Assimilation Association established / 南蕃事件・同化会設立",
1915: "Tapani Incident; Assimilation Association dissolved / 西来庵事件・同化会解散",
1916: "Central Taiwan earthquake / 台湾中部地震",
1917: "Commercial and Industrial School established / 商工学校設立",
1918: "Cross-island highway completed / 横断道路完成",
1919: "Taiwan Education Act enacted; Taiwan Power Company established / 台湾教育令・台湾電力会社設立",
1920: "Prefectural system implemented; New People's Society established; Taiwan General History published / 州廳制施行・新民会設立・台湾通史出版",
1921: "Taiwan Cultural Association established / 台湾文化協会設立",
1922: "Public Order Police Law implemented / 治安警察法施行",
1923: "Taiwan Minpao founded; Crown Prince visits Taiwan / 台湾民報創刊・裕仁訪台",
1925: "Taoyuan irrigation canal completed; Erlin incident / 桃園大圳完成・二林事件",
1927: "Taiwan People's Party established / 台湾民衆党成立",
1928: "Taihoku Imperial University established; Taiwan Communist Party established / 台北帝国大学設立・台湾共産党設立",
1929: "Taiwan historical records published / 台湾史料刊行",
1920: "Prefectural system implemented; New People's Society established; Taiwan General History published / 州廳制施行・新民会設立・台湾通史出版",
1930: "Chianan irrigation system completed; Wushe Incident / 嘉南大圳完成・霧社事件",
1931: "Chiang Wei-shui dies / 蒋渭水死去",
1932: "Dahu incident; Suhua Highway completed / 大湖事件・蘇花公路完成",
1934: "Sun Moon Lake power plant completed; Petition Movement ends / 日月潭発電所完成・請願運動終了",
1935: "Taiwan Exposition; earthquake / 台湾博覧会・地震",
1936: "New literature magazine launched / 新文学創刊",
1937: "Second Sino-Japanese War begins; ban on Chinese writing / 日中戦争勃発・漢文廃止",
1939: "Xinkaogang port construction / 新高港建設",
1940: "Name-changing policy implemented / 創氏改名",
1941: "Imperial Subject Service Association established / 皇民奉公会設立",
1942: "Volunteer soldier system introduced / 志願兵制度",
1943: "National school system implemented; air raids begin / 国民学校制度・空襲開始",
1944: "Conscription system implemented / 徴兵制施行",
1945: "Japan surrenders; end of colonial rule in Taiwan / 日本降伏・台湾統治終了"
}

abo_timeline = {
1895: "日本開始統治台灣，理蕃政策進入初期鎮壓階段 / Japan begins ruling Taiwan; early suppression phase of Indigenous policy",  
1902: "南庄事件，促使日本重新檢討理蕃政策 / Nanzhuang Incident prompts policy reassessment",
1905: "首次全面推行理蕃政策 / First comprehensive implementation of Indigenous policy",
1907: "開始第一次五年理蕃計畫（以武力討伐為主） / First Five-Year Indigenous Policy Plan begins (military suppression)",
1914: "第二次五年理蕃計畫結束 / Second Five-Year Plan ends",
1919: "田健治郎推行同化政策（內地延長主義） / Den Kenjirō promotes assimilation policy (extension of mainland Japan)",
1923: "裕仁皇太子訪台，提出改稱「高砂族」與全面同化構想 / Crown Prince Hirohito visits Taiwan; proposes renaming to Takasago and full assimilation",
1930: "霧社事件爆發，原住民武裝反抗日本統治 / Wushe Incident: Indigenous uprising against Japanese rule",
1936: "正式改稱「高砂族」，並推動皇民化政策 / Official renaming to Takasago; Kominka (imperialization) begins",
1937: "盧溝橋事件後進入戰時體制，加速皇民化 / Marco Polo Bridge Incident; wartime mobilization and intensified assimilation",
1941: "皇民奉公運動開始 / Kominka service movement begins",
1942: "高砂義勇隊出征海外 / Takasago Volunteer Corps deployed overseas",
1945: "二戰結束，日本統治台灣結束 / End of WWII; Japanese rule in Taiwan ends"
}

governor_table = {
1895: ["樺山資紀"],
1896: ["樺山資紀", "桂太郎", "乃木希典"],
1897: ["乃木希典"],
1898: ["乃木希典", "児玉源太郎"],
1899: ["児玉源太郎"],
1900: ["児玉源太郎"],
1901: ["児玉源太郎"],
1902: ["児玉源太郎"],
1903: ["児玉源太郎"],
1904: ["児玉源太郎"],
1905: ["児玉源太郎"],
1906: ["児玉源太郎", "佐久間左馬太"],
1907: ["佐久間左馬太"],
1908: ["佐久間左馬太"],
1909: ["佐久間左馬太"],
1910: ["佐久間左馬太"],
1911: ["佐久間左馬太"],
1912: ["佐久間左馬太"],
1913: ["佐久間左馬太"],
1914: ["佐久間左馬太"],
1915: ["佐久間左馬太", "安東貞美"],
1916: ["安東貞美"],
1917: ["安東貞美"],
1918: ["安東貞美", "明石元二郎"],
1919: ["明石元二郎", "田健治郎"],
1920: ["田健治郎"],
1921: ["田健治郎"],
1922: ["田健治郎"],
1923: ["田健治郎", "内田嘉吉"],
1924: ["内田嘉吉", "伊沢多喜男"],
1925: ["伊沢多喜男"],
1926: ["伊沢多喜男", "上山満之進"],
1927: ["上山満之進"],
1928: ["上山満之進", "川村竹治"],
1929: ["川村竹治", "石塚英藏"],
1930: ["石塚英藏"],
1931: ["石塚英藏", "太田政弘"],
1932: ["太田政弘", "南弘", "中川健藏"],
1933: ["中川健藏"],
1934: ["中川健藏"],
1935: ["中川健藏"],
1936: ["中川健藏", "小林躋造"],
1937: ["小林躋造"],
1938: ["小林躋造"],
1939: ["小林躋造"],
1940: ["小林躋造", "長谷川清"],
1941: ["長谷川清"],
1942: ["長谷川清"],
1943: ["長谷川清"],
1944: ["長谷川清", "安藤利吉"],
1945: ["安藤利吉"]
}

vice_governor_table = {
1895: ["高島鞆之助"]
}

admin_head_table = {
1895: ['水野遵'],
1896: ['水野遵'],
1897: ['水野遵', '曾根靜夫'],
1898: ['曾根靜夫', '後藤新平'],
1899: ['後藤新平'],
1900: ['後藤新平'],
1901: ['後藤新平'],
1902: ['後藤新平'],
1903: ['後藤新平'],
1904: ['後藤新平'],
1905: ['後藤新平'],
1906: ['後藤新平', '祝辰巳'],
1907: ['祝辰巳'],
1908: ['祝辰巳', '大島久滿次'],
1909: ['大島久滿次'],
1910: ['大島久滿次', '宮尾舜治', '內田嘉吉'],
1911: ['內田嘉吉'],
1912: ['內田嘉吉'],
1913: ['內田嘉吉'],
1914: ['內田嘉吉'],
1915: ['內田嘉吉', '下村宏'],
1916: ['下村宏'],
1917: ['下村宏'],
1918: ['下村宏'],
1919: ['下村宏'],
1920: ['下村宏'],
1921: ['下村宏', '賀來佐賀太郎'],
1922: ['賀來佐賀太郎'],
1923: ['賀來佐賀太郎'],
1924: ['賀來佐賀太郎', '後藤文夫'],
1925: ['後藤文夫'],
1926: ['後藤文夫'],
1927: ['後藤文夫'],
1928: ['後藤文夫', '河原田稼吉'],
1929: ['河原田稼吉', '人見次郎'],
1930: ['人見次郎'],
1931: ['人見次郎', '高橋守雄', '木下信'],
1932: ['木下信', '平塚廣義'],
1933: ['平塚廣義'],
1934: ['平塚廣義'],
1935: ['平塚廣義'],
1936: ['平塚廣義', '森岡二朗'],
1937: ['森岡二朗'],
1938: ['森岡二朗'],
1939: ['森岡二朗'],
1940: ['森岡二朗', '齋藤樹'],
1941: ['齋藤樹'],
1942: ['齋藤樹'],
1943: ['齋藤樹'],
1944: ['齋藤樹'],
1945: ['齋藤樹', '成田一郎']
}

with col2:
    st.subheader(f"{year}")

    event = timeline.get(year)
    if event:
        st.write(event)
    
    gov = governor_table.get(year)
    if gov:
        for g in gov:
            st.write(f"総督 Governor General: {g}")

    vice_gov = vice_governor_table.get(year)
    if vice_gov:
        for vg in vice_gov:
            st.write(f"副総督 Vice Governor General: {vg}")

    adm =  admin_head_table.get(year)
    if adm:
        for a in adm:
            st.write(f"総務長官 Chief Administrator: {a}")
            
with col3:
    abo_event = abo_timeline.get(year)
    if abo_event:
        st.subheader("Frontier Events")
        st.write(abo_event)

# Document distribution line chart
st.divider()

st.subheader("Document distribution")

col1, col2 = st.columns(2)
with col1:
    st.caption("By Year")
    st.line_chart(ydf.groupby("year").size())
with col2:
    st.caption("By Decade")
    st.bar_chart(ddf.groupby("decade").size())
    
# Map
st.divider()

import streamlit as st
import folium
from streamlit_folium import st_folium

min_x = 119.97857674956322
max_x = 122.02203378081325
min_y = 21.867446379787584
max_y = 25.32002866855441

m = folium.Map()

bounds = [[min_y, min_x], [max_y, max_x]]

m.fit_bounds(bounds)

st_data = st_folium(m, width=700, height=500)

# Historical Maps (to be added in future)

#st.divider()
#import cartopy.crs as ccrs
#from cartopy.io.shapereader import Reader
#shp_path = r"C:\Users\Dell\Desktop\帝國議會台灣文本可視化\map1920\1920d_1.shp" 
#fig = plt.figure(figsize=(8, 6)) 
#ax = plt.axes(projection=ccrs.PlateCarree()) 
#reader = Reader(shp_path) 
#ax.add_geometries( reader.geometries(), crs=ccrs.PlateCarree(), facecolor="none", edgecolor="black", linewidth=0.5 ) 
#ax.set_extent([119.9785, 122.0220, 21.8674, 25.3200]) 
#ax.coastlines() 
#st.pyplot(fig)