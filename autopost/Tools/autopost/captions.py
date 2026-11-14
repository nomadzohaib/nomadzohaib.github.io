"""SEO-optimised captions per concept and platform. [YT] link from YOUTUBE_VLOG_URL in .env.
Rules: keyword ('Bali') early in titles, hook first line, 5-8 targeted hashtags (IG), 3-5 (TikTok),
3 shown + tags (YouTube), CTA to the full vlog, a question to drive comments."""

BASE_TAGS = ["Bali", "Bali vlog", "Bali travel", "Indonesia", "Pakistani traveller", "Nomad Zohaib", "Urdu vlog",
             "travel vlog", "Bali shorts", "Bali 2026"]

C = {
    "finns_story": dict(
        title="Bali's Craziest Beach Club? 🤯 FINNS Canggu | Day 5",
        hook="Bali ka sab se crazy din 🌴🔥",
        text="Subah barish 🌧 → Labubu village → Rp 50,000 coconut 🥥 → FINNS sunset 🌅 → raat 2 baje toofan 🛵⛈",
        q="Aap Bali gaye ho? Sab se best jagah kaunsi lagi? 👇",
        ig=["#Bali", "#FinnsBeachClub", "#Canggu", "#BaliTravel", "#BeachClub", "#PakistaniTraveller", "#NomadZohaib", "#TravelReels"],
        tt=["#bali", "#finnsbeachclub", "#canggu", "#traveltok", "#pakistanitraveller"],
        tags=["FINNS beach club", "FINNS Bali", "Canggu beach club", "Bali beach club", "Bali nightlife", "Bali sunset"]),
    "coconut": dict(
        title="Bali Coconut Price 2026: Rp 50,000 at Kuta Beach 🥥",   # 13 Nov: search-style (old 'Price Shock!' title: 112 YT views vs 348 for 'Bali in 1 Day')
        hook="Bali mein ek coconut kitne ka? 🥥 Real price!",   # 14 Nov: prices reel hook "asal kharcha kitna? Real prices!" = IG best (1,400 views, 9.1 s, 5 shares)
        text="Kuta Beach: 50,000 ka ek, 1 lakh ke do! Aur 1 lakh wala bara coconut 😂 (~PKR 1,800)",
        q="Mehenga ya theek? Comment karo 👇",
        ig=["#Bali", "#KutaBeach", "#BaliPrices", "#BaliOnABudget", "#Coconut", "#PakistaniTraveller", "#NomadZohaib", "#TravelReels"],
        tt=["#bali", "#baliprices", "#kutabeach", "#coconut", "#pakistanitraveller"],
        tags=["Bali prices", "Kuta beach", "Bali coconut price", "Bali on a budget", "Bali food prices", "cost of Bali"]),
    "storm": dict(
        title="Bali in November: 2 AM Storm Alert ⛈ Rainy Season Reality",   # 11 Nov: search-style title ("Bali in 1 Day") got 6x the coconut title on Shorts
        hook="Raat ke 2 baje Bali mein yeh ho raha tha 😳",
        text="Tez hawa, barish, aur kal ke liye toofan ka alert ⛈ Phir bhi scooter ride 🛵",
        q="Aap is waqt bahar niklte? 👇",
        ig=["#Bali", "#BaliNights", "#Kuta", "#Storm", "#ScooterRide", "#PakistaniTraveller", "#NomadZohaib", "#TravelReels"],
        tt=["#bali", "#balinights", "#storm", "#traveltok", "#pakistanitraveller"],
        tags=["Bali at night", "Kuta at night", "Bali storm", "Bali scooter", "Bali rainy season", "Bali weather"]),
    "labubu": dict(
        title="Labubu Village in Bali 🧸 Pop Mart Christmas at Beachwalk Kuta",   # 13 Nov 22:30: fresh title for the Sun cine post (old one used by labubu bold: 1,042 YT views, 136/h); same keywords, not a duplicate
        hook="Bali mein Labubu ka poora gaon! 🧸🎄",
        text="Beachwalk Kuta mein Pop Mart ka Labubu Christmas village. Har shelf pe Labubu!",
        q="Labubu fan ho? Kaunsa wala lete? 👇",
        ig=["#Labubu", "#PopMart", "#Bali", "#BeachwalkBali", "#LabubuCollection", "#BaliShopping", "#NomadZohaib", "#TravelReels"],
        tt=["#labubu", "#popmart", "#bali", "#labubucollection", "#traveltok"],
        tags=["Labubu", "Pop Mart Bali", "Labubu Bali", "Beachwalk Kuta", "Bali shopping", "Labubu Christmas"]),
    "pakistan_beach": dict(
        title="Bali Local Asked 'Where Are You From?' 🇵🇰 Kuta Beach",
        hook="Bali local ne pucha 'Aap kahan se hain?' 🇵🇰",
        text="'Pakistan!' Phir Kuta Beach pe Bali ka special stone dikhaya 🪨❤️",
        q="Kabhi abroad mein kisi ne Pakistan pe aisa react kiya? 👇",
        ig=["#Pakistan", "#Bali", "#KutaBeach", "#PakistaniInBali", "#BaliLocals", "#PakistaniTraveller", "#NomadZohaib", "#TravelReels"],
        tt=["#pakistan", "#bali", "#pakistaniinbali", "#traveltok", "#kutabeach"],
        tags=["Pakistani in Bali", "Pakistan Bali", "Bali locals", "Kuta beach", "Pakistani reaction abroad", "Indonesia Pakistan"]),
    "sunset": dict(
        title="Bali Sunset at FINNS Beach Club, Canggu 🌅 No Filter",   # 13 Nov: question title got 4 YT views in 23 h; search-style titles win
        hook="No filter. Bas Bali ka sunset 🌅",
        text="FINNS Beach Club, Canggu. Aur phir... aasmaan ne yeh kiya.",
        q="Bali sunset ya Maldives sunset? 👇",
        ig=["#BaliSunset", "#Bali", "#Canggu", "#FinnsBeachClub", "#SunsetLovers", "#NoFilter", "#NomadZohaib", "#TravelReels"],
        tt=["#balisunset", "#bali", "#sunset", "#canggu", "#nofilter"],
        tags=["Bali sunset", "Canggu sunset", "FINNS sunset", "best sunset Bali", "Bali beach", "Bali aesthetic"]),
    "hotel_switch": dict(
        title="Where to Stay in Bali? Kuta Hotel Switch After 5 Nights 🏨",   # 12 Nov: search-style
        hook="5 raatein ek hotel mein... phir sirf 200 meter door 😂",
        text="Sunday Hotel se B Hotel & Spa, Kuta. Aur andar yeh view tha 👀",
        q="Aap ek hi hotel mein rehte ho ya switch karte ho? 👇",
        ig=["#BaliHotel", "#Bali", "#Kuta", "#HotelReview", "#BaliStay", "#PakistaniTraveller", "#NomadZohaib", "#TravelReels"],
        tt=["#balihotel", "#bali", "#hotelreview", "#traveltok", "#kuta"],
        tags=["Bali hotel", "Kuta hotel", "B Hotel Bali", "Bali hotel review", "where to stay in Bali", "Bali accommodation"]),
    "tips_prices": dict(
        title="Bali Prices 2026: What We REALLY Paid 💸 Kuta",
        hook="Bali mein asal kharcha kitna? 💸 Real prices!",
        text="Parking Rp 5,000 • Coconut Rp 50,000 (2 for 100k ~ PKR 1,800) • Bara coconut 100k. Plus 4 money tips 👇",
        q="Mehenga ya sasta? Apna best Bali tip batao 👇",
        ig=["#Bali", "#BaliPrices", "#BaliOnABudget", "#BaliTravel", "#TravelTips", "#PakistaniTraveller", "#NomadZohaib", "#TravelReels"],
        tt=["#bali", "#baliprices", "#traveltips", "#balionabudget", "#pakistanitraveller"],
        tags=["Bali prices", "Bali prices 2026", "Bali on a budget", "Bali travel tips", "cost of Bali", "Kuta prices"],
        blog="bali-prices-we-paid"),
    "tips_itinerary": dict(
        title="Bali 1 Day Itinerary: Labubu Village, Kuta Beach & FINNS 📍",   # 13 Nov 22:30: 'Labubu' is the week's best YT keyword (136 views/h vs <=8 for others); fresh title for the Sat cine post
        hook="Bali mein sirf 1 din? Yeh route save karo 📌",
        text="B Hotel › Beachwalk (Labubu) › Kuta Beach › FINNS sunset › Canggu nights. ~10 km by scooter 🛵",
        q="Aap kaunsa stop add karte? 👇",
        ig=["#Bali", "#BaliItinerary", "#Canggu", "#Kuta", "#BaliTravel", "#TravelTips", "#NomadZohaib", "#TravelReels"],
        tt=["#bali", "#baliitinerary", "#canggu", "#traveltips", "#traveltok"],
        tags=["Bali itinerary", "Bali 1 day itinerary", "Labubu Bali", "Kuta to Canggu", "Bali one day", "Bali travel tips", "things to do in Bali", "Canggu"],
        blog="kuta-to-canggu-one-day"),
}

_STORY_TAGS = ["Bali Day 5", "Bali story", "Bali vlog series"]
C.update({
    "story_p1": dict(
        title="Bali Day 5 (Part 1/5): Rain, Checkout & a Hotel Switch 🌧",
        hook="Bali Day 5, Part 1: subah ki barish 🌧",
        text="5 raatein Sunday Hotel mein... phir checkout, aur sirf 200 m door B Hotel & Spa. Aur andar yeh view tha 👀",
        q="Part 2 mein Labubu ka poora gaon 🧸 Follow karo taake miss na ho! Aap ek hotel mein rehte ho ya switch? 👇",
        ig=["#Bali", "#BaliVlog", "#Kuta", "#BaliHotel", "#TravelStory", "#PakistaniTraveller", "#NomadZohaib", "#TravelReels"],
        tt=["#bali", "#balivlog", "#storytime", "#traveltok", "#pakistanitraveller"],
        tags=["Bali hotel", "Kuta hotel", "B Hotel Bali", "Bali rainy day"] + _STORY_TAGS, blog="bali-day-5-guide"),
    "story_p2": dict(
        title="Bali Day 5 (Part 2/5): A Whole LABUBU Village 🧸 Beachwalk",
        hook="Part 2: Bali mein Labubu ka poora gaon 🧸",
        text="Beachwalk Kuta: parking Rp 5,000, sale up to 50%, aur Pop Mart ka Labubu Christmas village!",
        q="Part 3: Kuta Beach pe 'Oh, Pakistan!' 🇵🇰 Kaunsa Labubu lete aap? 👇",
        ig=["#Labubu", "#PopMart", "#Bali", "#BeachwalkBali", "#BaliVlog", "#TravelStory", "#NomadZohaib", "#TravelReels"],
        tt=["#labubu", "#popmart", "#bali", "#storytime", "#traveltok"],
        tags=["Labubu", "Pop Mart Bali", "Beachwalk Kuta", "Labubu Christmas"] + _STORY_TAGS, blog="bali-day-5-guide"),
    "story_p3": dict(
        title="Bali Day 5 (Part 3/5): 'Oh, Pakistan!' on Kuta Beach 🇵🇰",
        hook="Part 3: Kuta Beach pe 'Oh, Pakistan!' 🇵🇰",
        text="Rp 50,000 ka coconut 🥥, ek local ka pyaar bhara reaction, aur Bali ka special stone.",
        q="Part 4: FINNS ka sunset 🌅 Abroad mein Pakistan pe best reaction kya mila? 👇",
        ig=["#KutaBeach", "#Pakistan", "#Bali", "#PakistaniInBali", "#BaliVlog", "#TravelStory", "#NomadZohaib", "#TravelReels"],
        tt=["#pakistan", "#bali", "#kutabeach", "#storytime", "#traveltok"],
        tags=["Kuta beach", "Pakistani in Bali", "Bali coconut price", "Bali locals"] + _STORY_TAGS, blog="bali-prices-we-paid"),
    "story_p4": dict(
        title="Bali Day 5 (Part 4/5): Waiting for the FINNS Sunset 🌅",
        hook="Part 4: FINNS, Canggu... aur phir aasmaan ne yeh kiya 🌅",
        text="Kuta se 10 km scooter, FINNS Beach Club, aur sab ki nazrein ek taraf... sooraj ki taraf.",
        q="Poora sunset full vlog mein hai 🎬 Part 5: raat 2 baje toofan ⛈ 👇",
        ig=["#BaliSunset", "#FinnsBeachClub", "#Canggu", "#Bali", "#BaliVlog", "#TravelStory", "#NomadZohaib", "#TravelReels"],
        tt=["#balisunset", "#canggu", "#bali", "#storytime", "#traveltok"],
        tags=["FINNS Bali", "Canggu sunset", "Bali sunset", "Kuta to Canggu"] + _STORY_TAGS, blog="kuta-to-canggu-one-day"),
    "story_p5": dict(
        title="Bali Day 5 (Part 5/5): 2 AM Storm Ride ⛈ The Ending",
        hook="Part 5: raat 2 baje toofan aa raha tha ⛈",
        text="Tez hawa, barish, storm alert... aur phir bhi scooter pe wapas nikalna tha 🛵",
        q="Poori kahani ek video mein: link in bio 🎬 Aap is waqt nikalte? 👇",
        ig=["#Bali", "#BaliNights", "#Storm", "#ScooterRide", "#BaliVlog", "#TravelStory", "#NomadZohaib", "#TravelReels"],
        tt=["#bali", "#storm", "#storytime", "#traveltok", "#pakistanitraveller"],
        tags=["Bali storm", "Bali at night", "Bali scooter", "Canggu night"] + _STORY_TAGS, blog="bali-day-5-guide"),
})

SITE = "https://nomadzohaib.github.io"
BLOG_DEFAULT = "bali-day-5-guide"


def blog_url(concept):
    return f"{SITE}/blog/{C.get(concept, {}).get('blog', BLOG_DEFAULT)}.html"


# EXPERIMENT E3 (12 Nov): meme-style one-line caption on Instagram/Facebook instead of the long caption.
# The channel's best-ever posts (1.6k-2.7k views) had one-line captions. See 05_Work/autopost/experiments.json.
ONE_LINE = {"storm"}


def caption(concept, platform, yt_url):
    c = C[concept]
    link = yt_url or "YouTube @nomadzohaib (link in bio)"
    blog = blog_url(concept)
    if concept in ONE_LINE and platform == "instagram":
        return f"{c['hook']}\n🎬 Full vlog: link in bio\n\n{' '.join(c['ig'][:5])}"
    if concept in ONE_LINE and platform == "facebook":
        return f"{c['hook']}\n🎬 Full vlog 👉 {link}\n\n{' '.join(c['ig'][:4])}"
    if platform == "instagram":
        return (f"{c['hook']}\n\n{c['text']}\n\n🎬 Full Bali vlog on YouTube + 📖 travel guide on our website: link in bio\n"
                f"📌 Save for your Bali trip\n💬 {c['q']}\n\n{' '.join(c['ig'])}")
    if platform == "facebook":
        return (f"{c['hook']}\n\n{c['text']}\n\n🎬 Poori Bali vlog YouTube pe 👉 {link}\n📖 Full guide + prices 👉 {blog}\n"
                f"💬 {c['q']}\n\n{' '.join(c['ig'][:5])}")
    if platform == "tiktok":
        return f"{c['hook']} Full vlog YouTube pe 🎬 Guide: nomadzohaib.github.io {' '.join(c['tt'])}"
    if platform == "youtube":
        return (f"{c['hook']}\n{c['text']}\n\n🎬 Full Bali vlog: {link}\n📖 Travel guide: {blog}\n"
                f"🔔 Subscribe: https://www.youtube.com/@nomadzohaib?sub_confirmation=1\n"
                f"📸 Instagram: @nomadzohaib.666\n\n💬 {c['q']}\n\n#Shorts #Bali #NomadZohaib")
    raise ValueError(platform)


def yt_title(concept):
    t = C[concept]["title"]
    return (t if len(t) <= 88 else t[:88]) + " #shorts"


def yt_tags(concept):
    return C[concept]["tags"] + BASE_TAGS


def image_caption(post, platform, yt_url):
    """post = entry from 05_Work/autopost/tips_posts.json (built by tips_images.py)."""
    blog = f"{SITE}/blog/{post['blog']}.html"
    vlog = yt_url or "YouTube @nomadzohaib"
    tags = post["hashtags"] + ["#BaliTips", "#TravelGuide", "#Indonesia"]
    if platform == "instagram":
        return (f"{post['hook']}\n\n{post['title']}: swipe karo ➡️\n\n📌 Save karo apne Bali trip ke liye\n"
                f"📤 Us dost ko bhejo jo Bali ja raha hai\n🎬 Full vlog + 📖 complete guide: link in bio\n💬 {post['q']}\n\n{' '.join(tags)}")
    if platform == "facebook":
        return (f"{post['hook']}\n\n{post['title']} 👇\n\n📖 Complete guide: {blog}\n🎬 Full Bali vlog: {vlog}\n"
                f"💬 {post['q']}\n\n{' '.join(post['hashtags'][:6])}")
    raise ValueError(platform)


def pinned_comment(concept):
    return C[concept]["q"]
