# Configuration and constants for Radio Transcription Tool
# Version information
VERSION = "3.7"

# Global stopwords definition - more robust and comprehensive
DUTCH_STOPWORDS = {
    'de', 'het', 'een', 'en', 'van', 'in', 'te', 'dat', 'die', 'is', 'op', 'met', 'als', 'voor', 'aan', 'er', 'door', 'om', 'tot', 'ook', 'maar', 'uit', 'bij', 'over', 'nog', 'naar', 'dan', 'of', 'je', 'ik', 'ze', 'zij', 'hij', 'wij', 'jij', 'u', 'hun', 'ons', 'mijn', 'jouw', 'zijn', 'haar', 'hun', 'dit', 'dat', 'deze', 'die',
    'niet', 'hebben', 'daar', 'heeft', 'eigenlijk', 'heel', 'gaat', 'gaan', 'toch', 'want', 'elkaar', 'even', 'waar', 'natuurlijk', 'veel', 'meer', 'moet', 'kunnen', 'wordt', 'gewoon', 'worden', 'echt', 'komen', 'komt', 'hier', 'niks', 'gevonden',
    'twee', 'drie', 'vier', 'vijf', 'zes', 'zeven', 'acht', 'negen', 'tien', 'goed', 'doen', 'moeten', 'maken', 'soort', 'onze', 'omdat', 'kwam', 'iemand', 'blijven', 'vaak', 'jaar', 'denk', 'weer', 'staat', 'waren', 'geen', 'vandaag', 'bijvoorbeeld', 'zeggen', 'grote', 'tijd', 'muziek', 'iets', 'eigen', 'vooral', 'toen', 'eerste', 'tweede', 'derde', 'vierde', 'vijfde',
    'zesde', 'zevende', 'achtste', 'negende', 'tiende', 'vind', 'laten', 'altijd', 'andere', 'alle', 'woord', 'gebruiken', 'moment', 'woord', 'zelf', 'zien', 'jullie', 'terug', 'kijken', 'hebt', 'weet', 'hele', 'dingen', 'helemaal', 'verschillende', 'inderdaad', 'beter', 'misschien', 'manier', 'dacht', 'uiteindelijk',
    'beetje', 'ging', 'gemaakt', 'vanuit', 'werd', 'vond', 'best', 'alleen', 'groep', 'honderd', 'iedereen', 'weken', 'groot', 'allemaal', 'gedaan', 'lang', 'zeker', 'meter', 'dagen', 'gegeven', 'leuk', 'keer', 'zaten', 'mooi', 'deden', 'willen', 'begint', 'ervoor', 'minder', 'weten', 'onder', 'steeds', 'stellen',
    'anders', 'alles', 'hadden', 'zegt', 'juist', 'oude', 'bent', 'vindt', 'volgend', 'laatste', 'minuten', 'vanaf', 'tegen', 'samen', 'laag', 'zoals', 'tevoren', 'eerder', 'tegen', 'zoals', 'steeds', 'maakt', 'vorig', 'nieuwe', 'ligt', 'jonge', 'staan', 'zich', 'ziet', 'kijk', 'week', 'eens', 'klein',
    'volgende', 'lijkt', 'tussen', 'stuk', 'geworden', 'dus', 'zo', 'snel', 'elke', 'we', 'it', 'have', 'had', 'you', 'ja', 'we', 'ben', 'zo', 'kan', 'wel', 'nou', 'elke', 'waarom', 'denken', 'leren', 'paar', 'soms', 'kan', 'best', 'wat', 'was', 'er', 'wil', 'zeer', 'zeg', 'hem', 'zie', 'heb', 'liever', 'er', 'bijna',
    'heb', 'hebt', 'heeft', 'had', 'hadden', 'zou', 'zouden', 'moet', 'moeten', 'kan', 'kunnen', 'wil', 'willen', 'ga', 'gaan', 'kom', 'komen', 'doe', 'doen', 'maak', 'maken', 'zeg', 'zeggen', 'zie', 'zien', 'weet', 'weten', 'denk', 'denken', 'vind', 'vinden', 'heb', 'hebt', 'heeft', 'had', 'hadden',
    'mij', 'me', 'mijn', 'jou', 'jouw', 'hem', 'zijn', 'haar', 'ons', 'onze', 'jullie', 'hun', 'u', 'uw', 'zij', 'ze', 'hij', 'wij', 'we', 'ik', 'je', 'jij', 'dit', 'dat', 'deze', 'die', 'welke', 'welk', 'wat', 'wie', 'waar', 'wanneer', 'waarom', 'hoe', 'wel', 'niet', 'geen', 'al', 'alle', 'alleen', 'maar', 'ook',
    'toch', 'wel', 'nou', 'hoor', 'zeg', 'kijk', 'zie', 'hè', 'hé'
}

# Music filtering patterns for Dutch radio recordings
MUSIC_FILTER_PATTERNS = {
    'song_titles': [
        'intro', 'outro', 'jingle', 'theme', 'song', 'lied', 'nummer', 'hit', 'single', 'album',
        'artiest', 'zanger', 'zangeres', 'band', 'groep', 'muziek', 'melodie', 'ritme', 'beat',
        'refrein', 'couplet', 'bridge', 'solo', 'instrumentaal', 'acapella', 'karaoke'
    ],
    'music_indicators': [
        'speelt', 'zingt', 'zong', 'gezongen', 'gespeeld', 'muziek', 'melodie', 'ritme',
        'instrumenten', 'gitaar', 'piano', 'drums', 'bas', 'viool', 'trompet', 'saxofoon',
        'orkest', 'koor', 'ensemble', 'concert', 'optreden', 'festival', 'muziekwinkel'
    ],
    'radio_specific': [
        'radio', 'zender', 'frequentie', 'fm', 'am', 'uitzending', 'programma', 'show',
        'dj', 'presentator', 'omroep', 'nederlandse', 'vlaamse', 'belgische', 'hollandse'
    ]
}

# Radio station database
RADIO_STATIONS = {
    "Radio 1 (Netherlands)": "https://icecast.omroep.nl/radio1-bb-mp3",
    "Radio 2 (Netherlands)": "https://icecast.omroep.nl/radio2-bb-mp3",
    "Radio 3FM (Netherlands)": "https://icecast.omroep.nl/3fm-bb-mp3",
    "Radio 4 (Netherlands)": "https://icecast.omroep.nl/radio4-bb-mp3",
    "Radio 5 (Netherlands)": "https://icecast.omroep.nl/radio5-bb-mp3",
    "Radio 538 (Netherlands)": "https://21253.live.streamtheworld.com/RADIO538.mp3",
    "Sky Radio (Netherlands)": "https://19993.live.streamtheworld.com/SKYRADIO.mp3",
    "Qmusic (Netherlands)": "https://19993.live.streamtheworld.com/QMUSIC.mp3",
    "Veronica (Netherlands)": "https://19993.live.streamtheworld.com/VERONICA.mp3",
    "BNR Nieuwsradio (Netherlands)": "https://icecast.omroep.nl/bnr-bb-mp3",
    "Radio 10 (Netherlands)": "https://19993.live.streamtheworld.com/RADIO10.mp3",
    "Radio Decibel (Netherlands)": "https://icecast.omroep.nl/decibel-bb-mp3",
    "Radio 1 (Belgium)": "https://icecast.vrt.be/radio1_96.mp3",
    "Radio 2 (Belgium)": "https://icecast.vrt.be/radio2_96.mp3",
    "Studio Brussel (Belgium)": "https://icecast.vrt.be/stubru_96.mp3",
    "Klara (Belgium)": "https://icecast.vrt.be/klara_96.mp3",
    "VRT NWS (Belgium)": "https://icecast.vrt.be/vrtnws_96.mp3",
    "MNM (Belgium)": "https://icecast.vrt.be/mnm_96.mp3",
    "Radio Donna (Belgium)": "https://icecast.vrt.be/donna_96.mp3",
    "Qmusic (Belgium)": "https://icecast-qmusic.be-cdn.streamgate.io/qmusic_be.mp3",
    "Joe FM (Belgium)": "https://icecast-qmusic.be-cdn.streamgate.io/joefm_be.mp3",
    "Radio Contact (Belgium)": "https://icecast-qmusic.be-cdn.streamgate.io/radiocontact_be.mp3",
    "Topradio (Belgium)": "https://icecast-qmusic.be-cdn.streamgate.io/topradio_be.mp3",
    "Nostalgie (Belgium)": "https://icecast-qmusic.be-cdn.streamgate.io/nostalgie_be.mp3",
    "Radio 1 (Flanders)": "https://icecast.vrt.be/radio1_96.mp3",
    "Radio 2 (Flanders)": "https://icecast.vrt.be/radio2_96.mp3",
    "Studio Brussel (Flanders)": "https://icecast.vrt.be/stubru_96.mp3",
    "Klara (Flanders)": "https://icecast.vrt.be/klara_96.mp3",
    "VRT NWS (Flanders)": "https://icecast.vrt.be/vrtnws_96.mp3",
    "MNM (Flanders)": "https://icecast.vrt.be/mnm_96.mp3",
    "Radio Donna (Flanders)": "https://icecast.vrt.be/donna_96.mp3",
    "Qmusic (Flanders)": "https://icecast-qmusic.be-cdn.streamgate.io/qmusic_be.mp3",
    "Joe FM (Flanders)": "https://icecast-qmusic.be-cdn.streamgate.io/joefm_be.mp3",
    "Radio Contact (Flanders)": "https://icecast-qmusic.be-cdn.streamgate.io/radiocontact_be.mp3",
    "Topradio (Flanders)": "https://icecast-qmusic.be-cdn.streamgate.io/topradio_be.mp3",
    "Nostalgie (Flanders)": "https://icecast-qmusic.be-cdn.streamgate.io/nostalgie_be.mp3",
    "Radio 1 (Wallonia)": "https://icecast.rtbf.be/radio1_96.mp3",
    "Radio 2 (Wallonia)": "https://icecast.rtbf.be/radio2_96.mp3",
    "La Première (Wallonia)": "https://icecast.rtbf.be/lapremiere_96.mp3",
    "Classic 21 (Wallonia)": "https://icecast.rtbf.be/classic21_96.mp3",
    "Pure FM (Wallonia)": "https://icecast.rtbf.be/purefm_96.mp3",
    "VivaCité (Wallonia)": "https://icecast.rtbf.be/vivacite_96.mp3",
    "Musiq'3 (Wallonia)": "https://icecast.rtbf.be/musiq3_96.mp3",
    "Radio Contact (Wallonia)": "https://icecast-qmusic.be-cdn.streamgate.io/radiocontact_be.mp3",
    "Nostalgie (Wallonia)": "https://icecast-qmusic.be-cdn.streamgate.io/nostalgie_be.mp3",
    "Fun Radio (Wallonia)": "https://icecast-qmusic.be-cdn.streamgate.io/funradio_be.mp3",
    "Radio 1 (Brussels)": "https://icecast.vrt.be/radio1_96.mp3",
    "Radio 2 (Brussels)": "https://icecast.vrt.be/radio2_96.mp3",
    "Studio Brussel (Brussels)": "https://icecast.vrt.be/stubru_96.mp3",
    "Klara (Brussels)": "https://icecast.vrt.be/klara_96.mp3",
    "VRT NWS (Brussels)": "https://icecast.vrt.be/vrtnws_96.mp3",
    "MNM (Brussels)": "https://icecast.vrt.be/mnm_96.mp3",
    "Radio Donna (Brussels)": "https://icecast.vrt.be/donna_96.mp3",
    "Qmusic (Brussels)": "https://icecast-qmusic.be-cdn.streamgate.io/qmusic_be.mp3",
    "Joe FM (Brussels)": "https://icecast-qmusic.be-cdn.streamgate.io/joefm_be.mp3",
    "Radio Contact (Brussels)": "https://icecast-qmusic.be-cdn.streamgate.io/radiocontact_be.mp3",
    "Topradio (Brussels)": "https://icecast-qmusic.be-cdn.streamgate.io/topradio_be.mp3",
    "Nostalgie (Brussels)": "https://icecast-qmusic.be-cdn.streamgate.io/nostalgie_be.mp3"
}

# Audio processing settings
CHUNK_LENGTH_MS = 10 * 60 * 1000  # 10 minutes in milliseconds
SAMPLE_RATE = 44100
CHANNELS = 1  # Mono for better transcription
BITRATE = "64k"

# Transcription settings
WHISPER_MODEL = "whisper-1"
WHISPER_LANGUAGE = "nl"
WHISPER_PROMPT = "Dit is een Nederlandse radio-uitzending met nieuws, discussies, interviews en gesprekken. Focus op spraak en gesprekken, niet op muziek. De transcriptie moet alle belangrijke woorden en zinnen bevatten, maar muziekteksten en jingles kunnen worden overgeslagen."

# Keypoint extraction settings
MIN_WORDS_FOR_KEYBERT = 50
KEYBERT_PHRASE_RANGE = (2, 8)
KEYBERT_MEDIUM_RANGE = (2, 4)
KEYBERT_WORD_RANGE = (1, 1)
KEYBERT_TOP_N_PHRASES = 60
KEYBERT_TOP_N_MEDIUM = 50
KEYBERT_TOP_N_WORDS = 20

# Similarity threshold for merging segments
SIMILARITY_THRESHOLD = 0.4

# File paths
BIN_DIR = "bin"
FFMPEG_EXE = "ffmpeg.exe"
FFPLAY_EXE = "ffplay.exe"
CONFIG_FILE = "openai_config.txt"
AUDIO_CLEANUP_CONFIG = "audio_cleanup_config.txt"
PROGRAMMING_CONFIG = "programming_config.txt"
RECORDINGS_DIR = "Recordings+transcriptions"
TRANSCRIPTIONS_DIR = "Transcriptions"
LOG_FILE = "transcription.log"
