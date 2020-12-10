#encoding=utf-8
import django
django.setup()
from sefaria.model import *

# root = library.get_toc_tree().get_root()

def moveIndexInto(index, category):
    assert isinstance(index, Index)
    assert isinstance(category, Category)

    index.categories = category.path[:]
    print("Moving - " + index.get_title() + " to " + str(index.categories) + " (moveIndexInto)")
    index.save(override_dependencies=True)

def moveCategoryInto(category, parent):
    """
    c = Category().load({'path': ["Tanaitic", "Minor Tractates"]})
    p = Category().load({"path": ["Talmud", "Bavli"]})
    moveCategoryInto(c, p)

    if parent is None, move to root.

    :param category:
    :param parent:
    :return:
    """
    assert isinstance(category, Category)
    assert isinstance(parent, Category) or parent is None

    old_category_path = category.path[:]
    old_parent_path = category.path[:-1]
    new_parent_path = parent.path[:] if parent else []

    # move all matching categories
    clauses = [{"path." + str(i): cname} for i, cname in enumerate(old_category_path)]
    query = {"$and": clauses}
    old_parent_length = len(old_parent_path)
    for cat in CategorySet(query):
        # replace old_parent_path with new_parent_path
        cat.path = new_parent_path + cat.path[old_parent_length:]
        print("Saving moved category - " + str(cat.path))
        cat.save(override_dependencies=True)

    # move all matching Indexes
    clauses = [{"categories." + str(i): cname} for i, cname in enumerate(old_category_path)]
    query = {"$and": clauses}
    for ind in IndexSet(query):
        assert isinstance(ind, Index)
        ind.categories = new_parent_path + ind.categories[old_parent_length:]
        print("Moving - " + ind.get_title() + " to " + str(ind.categories)  + " (moveCategoryInto)")
        ind.save(override_dependencies=True)

    """
     Handle commentary on parallel trees separately.
     "title": "Commentary of Chida on Tractate Gerim",
     "categories": [
     "Tanaitic",
     "Commentary",
     "Commentary of Chida",
     "Minor Tractates"
     ],
    """

def create_category(path, en=None, he=None):
    c = Category()
    if not Term().load({"name": path[-1]}):
        if en is None or he is None:
            raise Exception("Need term names for {}".format(path[-1]))
        print("adding term for " + en)
        term = Term()
        term.name = en
        term.add_primary_titles(en, he)
        term.scheme = "toc_categories"
        term.save()
    c.add_shared_term(path[-1])
    c.path = path
    c.lastPath = path[-1]
    print("Creating - {}".format(" / ".join(c.path)))
    c.save(override_dependencies=True)
    return c


def change_term_hebrew(en_primary, new_he):
    t = Term().load({"name": en_primary})
    assert t
    old_primary = t.get_primary_title("he")
    t.add_title(new_he, "he", True, True)
    t.remove_title(old_primary, "he")
    t.save()


# Change Hebrew primaries for categories
for k, he in [
    ("Aggadic Midrash", 'מדרשי אגדה'),
    ("Halachic Midrash", 'מדרשי הלכה'),
    ("Reference", "מילונים וספרי יעץ")
]:
    change_term_hebrew(k, he)

i = library.get_index("Zohar")
i.nodes.add_title("ספר הזהר", "he", True, True)
i.save()

### Avot D'Rabbi Natan, "Seder Olam Zutta"  -> Midrash Aggadic Midrash
for n in ["Seder Olam Zutta", "Avot D'Rabbi Natan"]:
    i = library.get_index(n)
    p = Category().load({"path": ["Midrash", "Aggadic Midrash"]})
    moveIndexInto(i, p)

### Commentaries of ADRN
# e.g:
# ["Tanaitic", "Commentary", "Kisse Rahamim", "Minor Tractates"]
# -> ["Midrash", "Commentary", "Kisse Rahamim"]

adrn_comms = ["Binyan Yehoshua on Avot D'Rabbi Natan",
"Gra's Nuschah on Avot D'Rabbi Natan",
"Haggahot R' Yeshaya Berlin on Avot D'Rabbi Natan",
"Haggahot Ya'avetz on Avot D'Rabbi Natan",
"Kisse Rahamim on Avot D'Rabbi Natan",
"Mitzpeh Etan on Avot D'Rabbi Natan",
"Rishon Letzion on Avot D'Rabbi Natan",
"Tumat Yesharim on Avot D'Rabbi Natan"]

for comm in adrn_comms:
    i = library.get_index(comm)
    name = i.categories[2]
    c = create_category(["Midrash", "Commentary", name])
    moveIndexInto(i, c)

library.rebuild(include_toc=True)
# remove empty categories that had been just ADRN
for p in [
    ["Tanaitic", "Commentary", "Binyan Yehoshua", "Minor Tractates" ],
    ["Tanaitic", "Commentary", "Mitzpeh Etan", "Minor Tractates" ],
    ["Tanaitic", "Commentary", "Tumat Yesharim", "Minor Tractates" ],
    ]:
    c = Category().load({"path": p})
    c.delete()

### The rest of the minor tractates -> Talmud/Bavli
c = Category().load({'path': ["Tanaitic", "Minor Tractates"]})
p = Category().load({"path": ["Talmud", "Bavli"]})
moveCategoryInto(c, p)

### Commentary on minor tractates -> Talmud/Bavli
#        "Tanaitic",         "Commentary",         "Nahalat Yaakov",         "Minor Tractates"
#   =>   "Talmud",      "Bavli",    "Commentary",     "Nahalat Yaakov",  "Minor Tractates",
p = Category().load({"path": ["Talmud", "Bavli", "Commentary"]})
for kid in Category().load({'path': ["Tanaitic", "Commentary"]}).get_toc_object().children:
        c = kid.get_category_object()
        moveCategoryInto(c, p)

### 	Megillat Taanit -> Midrash
i = library.get_index("Megillat Taanit")
c = Category().load({"path": ["Midrash"]})
moveIndexInto(i, c)

### Tosefta -> New top level category
c = Category().load({"path": ["Tanaitic", "Tosefta"]})
moveCategoryInto(c, None)

### Remove Tanaitic
library.rebuild(include_toc=True)
c = Category().load({"path": ["Tanaitic"]})
c.delete()


# Click Talmud -> Commentary of Chida (crash)


# Remove Modern Works
c = Category().load({"path": ["Modern Works", "English Explanation of Mishnah"]})
p = Category().load({"path": ["Mishnah", "Commentary"]})
moveCategoryInto(c, p)


# Shoel uMeshiv to subcat
c = create_category(["Responsa", "Shoel uMeshiv"], en="Shoel uMeshiv", he="שואל ומשיב")
ts = ["Shoel uMeshiv Mahadura I",
"Shoel uMeshiv Mahadura II",
"Shoel uMeshiv Mahadura III",
"Shoel uMeshiv Mahadura IV",
"Shoel uMeshiv Mahadura V",
"Shoel uMeshiv Mahadura VI"]

for t in ts:
    i = library.get_index(t)
    moveIndexInto(i, c)

# Contemporary .. into Halacha
c = create_category(["Halakhah", "Contemporary Halakhic Problems"], en="Contemporary Halakhic Problems", he='בעיות הלכתיות עכשוויות')
ts = [
'Contemporary Halakhic Problems, Vol I',
'Contemporary Halakhic Problems, Vol II',
'Contemporary Halakhic Problems, Vol III',
'Contemporary Halakhic Problems, Vol IV',
'Contemporary Halakhic Problems, Vol V',
'Contemporary Halakhic Problems, Vol VI']
for t in ts:
    i = library.get_index(t)
    moveIndexInto(i, c)

# Gray Matter into Halacha
c = create_category(["Halakhah", "Gray Matter"], en="Gray Matter", he='גריי מאטר')
ts = [
'Gray Matter I',
'Gray Matter II',
'Gray Matter III',
'Gray Matter IV',
]
for t in ts:
    i = library.get_index(t)
    moveIndexInto(i, c)

# Marei HaBazak to subcat
c = create_category(["Responsa", "B'Mareh HaBazak"], en="B'Mareh HaBazak", he='שו"ת במראה הבזק')
mb = {"B'Mareh HaBazak Volume I": 1,
    "B'Mareh HaBazak Volume III": 3,
    "B'Mareh HaBazak Volume IV": 4,
    "B'Mareh HaBazak Volume IX": 9,
    "B'Mareh HaBazak Volume V": 5,
    "B'Mareh HaBazak Volume VI": 6,
    "B'Mareh HaBazak Volume VII": 7,
    "B'Mareh HaBazak Volume VIII": 8}

for t, o in mb.items():
    i = library.get_index(t)
    i.order = [o]
    moveIndexInto(i, c)  #saves i

# Daf Shevui -> Talmud Commentary
c = create_category(["Talmud", "Bavli", "Commentary", "Daf Shevui"], en="Daf Shevui", he="דף שבועי")
ts = ["Daf Shevui to Avodah Zarah",
 "Daf Shevui to Ketubot",
 "Daf Shevui to Kiddushin",
 "Daf Shevui to Megillah",
 "Daf Shevui to Sukkah"]

for t in ts:
    i = library.get_index(t)
    moveIndexInto(i, c)

#
i = library.get_index("A New Israeli Commentary on Pirkei Avot")
c = Category().load({"path": ["Mishnah", "Commentary"]})   # deeper cat?
moveIndexInto(i, c)

c = create_category(["Reference", "Grammar"])
ts = ["Sefer haBachur", "Mahberet Menachem", "Sefat Yeter"]
for t in ts:
    i = library.get_index(t)
    moveIndexInto(i, c)

# Jastrow, Klein Dictionary, Otzar Laazei Rashi  => Reference, Dictionary
c = create_category(["Reference", "Dictionary"])
ts = ['Jastrow', 'Klein Dictionary', 'Otzar Laazei Rashi']
for t in ts:
    i = library.get_index(t)
    moveIndexInto(i, c)

# Into reference
c = Category().load({"path": "Reference"})
ts = ["The Jewish Spiritual Heroes", "Ein Zocher", "Devash Lefi", "Midbar Kedemot"]
for t in ts:
    i = library.get_index(t)
    moveIndexInto(i, c)


# Rename Philosophy -> Jewish Thought
ph = Term().load({"name": "Philosophy"})
ph.remove_title("מחשבת ישראל", "he")
ph.add_title("פילוסופיה", "he", True, True)
ph.save()

jt = Term().load({"name": "Jewish Thought"})
jt.remove_title("מחשבה יהודית", "he")
jt.add_title("מחשבת ישראל", "he", True, True)
jt.save()

# Change the philo cat itself
phc = Category().load({"path": ["Philosophy"]})
phc.change_key_name("Jewish Thought")
phc.save()


# move all matching categories
for cat in CategorySet({"path.0": "Philosophy"}):
    # replace old_parent_path with new_parent_path
    cat.path = ["Jewish Thought"] + cat.path[1:]
    print("Saving moved category - " + str(cat.path))
    cat.save(override_dependencies=True)

# move all matching Indexes
for ind in IndexSet({"categories.0": "Philosophy"}):
    assert isinstance(ind, Index)
    ind.categories = ["Jewish Thought"] + ind.categories[1:]
    print("Moving - " + ind.get_title() + " to " + str(ind.categories))
    ind.save(override_dependencies=True)


# Move Works of Eliezer Berkovits -> Jewish Thought
c = Category().load({"path": ["Modern Works", "Works of Eliezer Berkovits"]})
p = Category().load({"path": ["Jewish Thought"]})
moveCategoryInto(c, p)

cat_ancient = create_category(["Jewish Thought", "Ancient"], "Ancient", "ספרות קדומה")
books_ancient = ['The Midrash of Philo',
      'Against Apion',
      'The Antiquities of the Jews',
      'The War of the Jews',
                 'On the Life of Moses']

cat_rishonim = create_category(["Jewish Thought", "Rishonim"], "Rishonim","ראשונים")
books_rishonim = [  "HaEmunot veHaDeot", "Eight Chapters",
    "Guide for the Perplexed",
    "Treatise on Logic",
    "Duties of the Heart",
    "Duties of the Heart (abridged)",
    "Darashos HaRan",
    "Ma'amar al Yishmael",
    "Akeidat Yitzchak",
    "Sefer Kuzari",
    "Sefer HaIkkarim",
    "Ohr Hashem",
    "The Wars of the Lord",
    "Minhat Kenaot",
    "Yesod Mora"]

cat_acharonim = create_category(["Jewish Thought", "Acharonim"], "Acharonim","אחרונים")
books_acharonim = ["Derech Hashem",
    "Essay on Fundamentals",
    "Vilna Gaon's students letter to the Lost Tribes of Israel",
    "Nefesh HaChayim",
    "Kol HaTor",
    "Torat HaOlah",
    "Derush Chidushei HaLevana",
    "The Third Beit HaMikdash"]

cat_kook = create_category(["Jewish Thought", "Rav Kook"], "Rav Kook","כתבי הרב קוק")
books_kook = ["Orot",
    "Orot HaKodesh",
    "Orot HaTorah",
    "For the Perplexed of the Generation",
    "Maamar Hador",
    "Shmonah Kvatzim",
    "Midbar Shur"]

cat_modern = create_category(["Jewish Thought", "Modern"], "Modern", "ספרות מודרני")
books_modern = ["Nineteen Letters",
    "Sefer Yesodei HaTorah",
    "Gan Naul",
    "Words of Peace and Truth",
    "Imrei Binah",
    "Kol Dodi Dofek",
    "Hegyonei Uziel",
    "Revealment and Concealment in Language",
    "Halacha and Aggadah"]

for cat, books in [
    (cat_ancient, books_ancient),
    (cat_kook, books_kook),
    (cat_rishonim, books_rishonim),
    (cat_acharonim, books_acharonim),
    (cat_modern, books_modern)
]:
    for book in books:
        i = library.get_index(book)
        moveIndexInto(i, cat)


p = Category().load({"path": ["Jewish Thought", "Commentary"]})
ts = ["Ali Be'er on Revealment and Concealment in Language",
'Bein HaShitin on Halacha and Aggadah',
'Commentaries on Revealment and Concealment in Language']

for t in ts:
    i = library.get_index(t)
    moveIndexInto(i, p)

p = Category().load({"path": ["Chasidut"]})
ts = ["Flames of Faith"]
for t in ts:
    i = library.get_index(t)
    moveIndexInto(i, p)

#    "Ein Ayah",
i = library.get_index("Ein Ayah")
c = Category().load({"path": ["Talmud", "Bavli", "Commentary"]})
moveIndexInto(i, c)

# Tanakh > Parshanut
p = create_category(["Tanakh", "Parshanut"], "Parshanut", "פרשנות")
ts = ['Depths of Yonah',
 'From David to Destruction']
for t in ts:
    i = library.get_index(t)
    moveIndexInto(i, p)

p = create_category(["Tanakh", "Parshanut", "Redeeming Relevance"], "Redeeming Relevance", "פדיון הרלוונטיות")
ts = ['Redeeming Relevance; Deuteronomy',
 'Redeeming Relevance; Exodus',
 'Redeeming Relevance; Genesis',
 'Redeeming Relevance; Numbers']
for t in ts:
    i = library.get_index(t)
    moveIndexInto(i, p)

p = Category().load({"path": ["Tanakh", "Commentary"]})
ts = ['Birkat Asher on Torah',
'Chibbah Yeteirah on Torah',
'Footnotes to Kohelet by Bruce Heitler']
for t in ts:
    i = library.get_index(t)
    moveIndexInto(i, p)

p = Category().load({"path": ["Talmud", "Bavli", "Commentary"]})
ts = ['Abraham Cohen Footnotes to the English Translation of Masechet Berakhot']
for t in ts:
    i = library.get_index(t)
    moveIndexInto(i, p)



# Reorg Halacha
cat_ivh = create_category(["Halakhah", "Issur v'Heter"], "Issur v'Heter", "איסור והיתר")
books_ivh = ["Issur V'Heter L'Rabbeinu Yerucham",
'Issur veHeter leRashi',
'Torat HaBayit HaAroch',
'Torat HaBayit HaKatzar']

cat_mitzvot = create_category(["Halakhah", "Sifrei Mitzvot"], "Sifrei Mitzvot", "ספרי מצוות")
books_mitzvot = ['Sefer Hamitzvot of Rasag',
'Sefer Mitzvot Gadol',
'Sefer Mitzvot Katan',
'Sefer HaMitzvot',
'Sefer HaMitzvot HaKatzar',
'Sefer HaChinukh',
'Minchat Chinukh',
'Sefer Yereim',
'Kitzur Sefer Haredim of Rabbi Elazar Azcari']

cat_mono = create_category(["Halakhah", "Monographs"], "Monographs", "ספרי מונוגרפיה")
books_mono = ['Chofetz Chaim',
'The Sabbath Epistle',
'Treasures Hidden in the Sand',
'Bedikat HaSakin',
"Dina d'Garmei",
'Ein HaTekhelet',
'Gevurat Anashim',
'Hilchos Talmud Torah',
'Keset HaSofer',
'Piskei Challah',
'Ptil Tekhelet',
"Sha'ar HaMayim HaAroch",
"Sha'ar HaMayim HaKatzar",
'Shulchan Shel Arba',
'Care of the Critically Ill', 'Simla Chadasha']

cat_other_r = create_category(["Halakhah", "Other Rishonim"], "Other Rishonim", "ראשונים נוספים")
books_other_r = ['Ohr Zarua',
'Kol Bo',
'Abudarham',
'Avodat HaKodesh',
'Machzor Vitry',
'Sefer Chasidim',
'Sefer HaParnas',
"Sheiltot d'Rav Achai Gaon",
                 ]

cat_other_a = create_category(["Halakhah", "Other Acharonim"], "Other Acharonim", "אחרונים נוספים")
books_other_a =  ['Maaseh Rav',
'Mateh Efrayim',
'Nehar Misrayim',
"Shev Shmat'ta",
'Shulchan Aruch HaRav']


for cat, books in [
    (cat_mono, books_mono),
    (cat_mitzvot, books_mitzvot),
    (cat_ivh, books_ivh),
    (cat_other_r, books_other_r),
    (cat_other_a, books_other_a),
]:
    for book in books:
        i = library.get_index(book)
        moveIndexInto(i, cat)

# Change 'Tur and Commentaries' -> 'Tur'
c = Category().load({"path": ["Halakhah", "Tur and Commentaries"]})
c.change_key_name("Tur")
c.save()

for ind in IndexSet({"categories": ["Halakhah", "Tur and Commentaries"]}):
    assert isinstance(ind, Index)
    ind.categories = ["Halakhah", "Tur"]
    print("Moving - " + ind.get_title() + " to " + str(ind.categories))
    ind.save(override_dependencies=True)


# Move into Shulchan Arukh / Mishneh Torah subcats


c = Category().load({"path": ["Halakhah", "Shulchan Arukh", "Commentary", "Siftei Kohen"]})
i = library.get_index("Summary of Shakh on Shulchan Arukh, Yoreh De'ah")
moveIndexInto(i, c)

c = Category().load({"path": ["Halakhah", "Shulchan Arukh", "Commentary", "Turei Zahav"]})
i = library.get_index("Summary of Taz on Shulchan Arukh, Yoreh De'ah")
moveIndexInto(i, c)

c = Category().load({"path":  ["Halakhah", "Shulchan Arukh", "Commentary", "Mishnah Berurah"]})
i = library.get_index("Biur Halacha")
moveIndexInto(i, c)

# Move categories of Kesef Mishnah to correct place
new_parent = create_category(["Halakhah", "Mishneh Torah", "Commentary", "Kessef Mishneh"] )
cs = CategorySet({"$and": [{"path.0": "Halakhah"}, {"path.1": "Commentary"}, {"path.2": "Kessef Mishneh"}, {"path.3": "Mishneh Torah"}]})
for c in cs:
    if len(c.path) == 4:
        continue
    moveCategoryInto(c, new_parent)


# Musar
r_cat = create_category(["Musar", "Rishonim"], "Rishonim", "ראשונים")
a_cat = create_category(["Musar", "Acharonim"], "Acharonim", "אחרונים")
m_cat = create_category(["Musar", "Modern"], "Modern", "ספרות מודרני")

r_books = [
    'Mivchar HaPeninim',
    'The Improvement of the Moral Qualities',
    'Shekel HaKodesh',
    'Letter from Ramban to his Son',
    'Shaarei Teshuvah',
    "Sha'ar Ha'Gemul of the Ramban",
    'Iggeret HaRamban',
    'Kad HaKemach',
    "Orchot Chaim L'HaRosh",
    'Sefer HaYashar',
    'Bechinat Olam',
    'Orchot Tzadikim',
    'Yesod HaYirah',
    'Sefer Tomer Devorah']

a_books = [
    'Kav HaYashar',
    'Shenei Luchot HaBerit',
    'Yaarot Devash I',
    'Shevet Musar',
    'Ahavat David',
    'Iggeret HaGra',
    'Messilat Yesharim',
    'Ohr Yisrael',
    'Pele Yoetz',
    'Shemirat HaLashon']
m_books = [
    "Tzipita L'Yeshuah",
    'Sichot Avodat Levi',
    'Shuvah Yisrael',
    'Maamar Mezake HaRabim'
]

for cat, books in [
    (r_cat, r_books),
    (a_cat, a_books),
    (m_cat, m_books)
]:
    for book in books:
        i = library.get_index(book)
        moveIndexInto(i, cat)


# Chassidut
c = Category().load({"path": ["Chasidut", "R' Tzadok HaKohen"]})
i = library.get_index("Pri Tzadik")
moveIndexInto(i, c)

c = create_category(["Chasidut", "Izhbitz"], "Izhbitz", "איזביצה")
for t in [
    "Tiferet Yosef",
    "Sod Yesharim",
    "Mei HaShiloach",
    "Beit Yaakov on Torah",
    "Shaar HaEmunah Ve'Yesod HaChassidut"
    ]:
    i = library.get_index(t)
    moveIndexInto(i, c)

i = library.get_index("Be'er Mayim Chaim")
del i.dependence
del i.base_text_titles
i.save()

# Kabbalah
c = create_category(["Kabbalah", "Zohar"], None, None)
for t in ["Zohar", "Tikkunei Zohar", "Zohar Chadash", "Baal HaSulam's Introduction to Zohar"]:
    i = library.get_index(t)
    moveIndexInto(i, c)


# Responsa
rashba = {
'Teshuvot haRashba part I':1,
'Teshuvot haRashba part IV':4,
'Teshuvot haRashba part V':5,
'Teshuvot haRashba part VI':6,
'Teshuvot haRashba part VII':7,
'Teshuvot haRashba Meyuchas LehaRamban':10,
'Footnotes to Teshuvot haRashba part IV':14,
'Footnotes to Teshuvot haRashba part V':15,
'Footnotes to Teshuvot haRashba part VI':16,
'Footnotes to Teshuvot haRashba part VII':17,
}
for t, o in rashba.items():
    i = library.get_index(t)
    i.order = [o]
    i.save(override_dependencies=True)

c = Category().load({"path": ["Responsa", "Rambam"]})
i = library.get_index("Pe'er HaDor Teshuvot HaRambam")
moveIndexInto(i, c)



cat_geonim = create_category(["Responsa", "Geonim"], "Geonim", "גאונים")
books_geonim = [
    'Epistle of Rav Sherira Gaon',
    "Musafia Teshuvot HaGeonim",
    'Teshuvot HaGeonim',
    'Toratan shel Rishonim'
]
cat_other_r = create_category(["Responsa", "Other Rishonim"], "Other Rishonim", "ראשונים נוספים")
books_other_r = [
    'Teshuvot Rashi',
    'Teshuvot HaRi Migash',
    'Teshuvot Maharam',
    'Maharach Or Zarua Responsa',
    'Teshuvot HaRitva',
    'Teshuvot HaRosh',
    'Teshuvot HaRivash',
    'Teshuvot Maharil',
    'Sefer HaTashbetz',
    'Mahari Weil',
    'Terumat HaDeshen',
    'Teshuvot HaRashbash',
    'Teshuvot Maharik',
    'Mahari Bruna'
]

cat_other_a = create_category(["Responsa", "Other Acharonim"], "Other Acharonim", "אחרונים נוספים")
books_other_a =  [
    'Shut min haShamayim',
    'Chazeh Hatenufa',
    'Responsa of Remah',
    'Teshuvot Maharshal',
    'Responsa Maharashdam',
    'Teshuvot Maharit',
    'Havot Yair',
    'Hakham Tzvi',
    'Torat Netanel',
    'Noda BiYhudah I',
    'Noda BiYhudah II',
    'Teshuva MeAhava Part I',
    'Responsa Chatam Sofer',
    'Binyan Tziyon',
    'HaElef Lekha Shlomo',
    'Responsa Rav Pealim',
    'Mateh Levi',
    "Melamed Leho'il Part II",
]

cat_other_m = create_category(["Responsa", "Other Modern"], "Other Modern", "שו”תים מודרניים נוספים")
books_other_m = ['Responsa Benei Banim',
'Mishpetei Uziel',
'Collected Responsa in Wartime',
'Collected Responsa to Chaplains']

for cat, books in [
    (cat_geonim, books_geonim),
    (cat_other_m, books_other_m),
    (cat_other_r, books_other_r),
    (cat_other_a, books_other_a)
]:
    for book in books:
        i = library.get_index(book)
        moveIndexInto(i, cat)

g = Group().load({"name": "Lindenbaum Center at YCT Rabbinical School"})
g.toc["categories"] = ["Responsa", "Other Modern"]
g.save()

"""
Now an empty cat, because single text is hidden
i = library.get_index("Footnotes on Teshuvot haRashba Meyuchas LehaRamban"),
 currently: 
"categories": [
"Responsa",
"Commentary",
"Footnotes",
"Rashba"
],
"""

# The Jewish Spiritual Heroes
# -> Reference

#Hide
tohide = [
    "Abraham Cohen Footnotes to the English Translation of Masechet Berakhot",
    "Footnotes on Teshuvot haRashba Meyuchas LehaRamban",
    "Footnotes on Orot",
    "Footnotes on Mekhilta DeRabbi Shimon Bar Yochai",
    "Footnotes to Kohelet by Bruce Heitler",
    "Footnotes to Teshuvot haRashba part IV",
    "Footnotes to Teshuvot haRashba part V",
    "Footnotes to Teshuvot haRashba part VI",
    "Footnotes to Teshuvot haRashba part VII",
    "Footnotes and Annotations on Derech Chaim",
    "Footnotes and Annotations on Be'er HaGolah",
    "Footnotes and Annotations on Ner Mitzvah",
    "Footnotes and Annotations on Ohr Chadash",
    "Nishmat Adam",
    "Binat Adam",
    "Commentary on Selected Paragraphs of Arpilei Tohar",
    "Ali Be'er on Revealment and Concealment in Language",
    "Bein HaShitin on Halacha and Aggadah",
    "Commentaries on Revealment and Concealment in Language",
    "Mekor Mayim Chayim on Baal Shem Tov",
    "Publisher's Haggahot on Sefer HaParnas"
]
for t in tohide:
    i = library.get_index(t)
    i.hidden = True
    i.save(override_dependencies=True)


# remove empty categories
"""
library.rebuild(include_toc=True)
for c in CategorySet({"$and": [{"path.0":"Halakhah"},{"path.1":"Commentary"},{"path.2":"Kessef Mishneh"}]}):
    if len(c.path) == 3:
        continue
    c.delete()
"""

for p in [
        ["Halakhah", "Commentary", "Summary of Taz", "Shulchan Arukh"],
        ["Halakhah", "Commentary", "Summary of Shakh", "Shulchan Arukh"],
        ["Halakhah", "Commentary", "Kessef Mishneh"],
        ["Other", "Grammar"],
        ["Other", "Dictionary"],
        ["Modern Works", "Commentary"],
        ["Tanaitic", "Commentary"],
        ["Responsa", "Commentary", "Footnotes", "Rashba"],
    ]:
    c = Category().load({"path": p})
    c.delete()

library.rebuild(include_toc=True)
for p in [
        ["Other"],
        ["Modern Works"],
        ["Tanaitic"],
        ["Responsa", "Commentary", "Footnotes"],
]:
    c = Category().load({"path": p})
    c.delete()

library.rebuild(include_toc=True)
for p in [
    ["Responsa", "Commentary"],
]:
    c = Category().load({"path": p})
    c.delete()


# Get rid of "modern commentary" on the sidebar.
# Pin major commentaries on Mishnah,


# Tanakh Commentary
# Talmud Commentary
#	Alphabetical  (? really?  not crono?)
