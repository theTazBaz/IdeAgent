"""
IdeAgent/scripts/add_wave2.py
Adds Wave 2 movies, characters, and relationships to data/batch.json
without creating any duplicates.
"""
import json
from pathlib import Path

BATCH_PATH = Path(__file__).parent.parent / "data" / "batch.json"

with open(BATCH_PATH, "r", encoding="utf-8") as f:
    batch = json.load(f)

existing_movie_titles = {m["title"].lower() for m in batch.get("movies", [])}
existing_char_keys = {(c["movie_title"].lower(), c["name"].lower()) for c in batch.get("characters", [])}
existing_rel_labels = {(r.get("movie_id"), r["label"].lower()) for r in batch.get("relationships", [])}

new_movies = [
    {"title": "Blade Runner", "placeholder": "_NEEDS_MOVIE_ID_bladerunner"},
    {"title": "2001: A Space Odyssey", "placeholder": "_NEEDS_MOVIE_ID_2001aspaceodyssey"},
    {"title": "Apocalypse Now", "placeholder": "_NEEDS_MOVIE_ID_apocalypsenow"},
    {"title": "The Silence of the Lambs", "placeholder": "_NEEDS_MOVIE_ID_thesilenceofthelambs"},
    {"title": "Oldboy", "placeholder": "_NEEDS_MOVIE_ID_oldboy"},
    {"title": "12 Angry Men", "placeholder": "_NEEDS_MOVIE_ID_12angrymen"},
    {"title": "The Shining", "placeholder": "_NEEDS_MOVIE_ID_theshining"},
    {"title": "Drive", "placeholder": "_NEEDS_MOVIE_ID_drive"},
    {"title": "Casablanca", "placeholder": "_NEEDS_MOVIE_ID_casablanca"},
    {"title": "Memories of Murder", "placeholder": "_NEEDS_MOVIE_ID_memoriesofmurder"},
    {"title": "Children of Men", "placeholder": "_NEEDS_MOVIE_ID_childrenofmen"},
    {"title": "Mad Max: Fury Road", "placeholder": "_NEEDS_MOVIE_ID_madmaxfuryroad"},
    {"title": "Pan's Labyrinth", "placeholder": "_NEEDS_MOVIE_ID_panslabyrinth"},
    {"title": "Princess Mononoke", "placeholder": "_NEEDS_MOVIE_ID_princessmononoke"},
    {"title": "Catch Me If You Can", "placeholder": "_NEEDS_MOVIE_ID_catchmeifyoucan"},
    {"title": "Zodiac", "placeholder": "_NEEDS_MOVIE_ID_zodiac"},
    {"title": "The Wolf of Wall Street", "placeholder": "_NEEDS_MOVIE_ID_thewolfofwallstreet"},
    {"title": "Requiem for a Dream", "placeholder": "_NEEDS_MOVIE_ID_requiemforadream"},
    {"title": "Schindler's List", "placeholder": "_NEEDS_MOVIE_ID_schindlerslist"},
    {"title": "Trainspotting", "placeholder": "_NEEDS_MOVIE_ID_trainspotting"},
]

new_characters = [
    # Blade Runner
    {"name": "Rick Deckard", "movie_id": "_NEEDS_MOVIE_ID_bladerunner", "movie_title": "Blade Runner", "placeholder": "_NEEDS_ID_deckard1982"},
    {"name": "Roy Batty", "movie_id": "_NEEDS_MOVIE_ID_bladerunner", "movie_title": "Blade Runner", "placeholder": "_NEEDS_ID_roybatty"},
    {"name": "Rachael", "movie_id": "_NEEDS_MOVIE_ID_bladerunner", "movie_title": "Blade Runner", "placeholder": "_NEEDS_ID_rachael"},
    # 2001: A Space Odyssey
    {"name": "Dr. David Bowman", "movie_id": "_NEEDS_MOVIE_ID_2001aspaceodyssey", "movie_title": "2001: A Space Odyssey", "placeholder": "_NEEDS_ID_davidbowman"},
    {"name": "HAL 9000", "movie_id": "_NEEDS_MOVIE_ID_2001aspaceodyssey", "movie_title": "2001: A Space Odyssey", "placeholder": "_NEEDS_ID_hal9000"},
    # Apocalypse Now
    {"name": "Captain Benjamin Willard", "movie_id": "_NEEDS_MOVIE_ID_apocalypsenow", "movie_title": "Apocalypse Now", "placeholder": "_NEEDS_ID_benjaminwillard"},
    {"name": "Colonel Walter E. Kurtz", "movie_id": "_NEEDS_MOVIE_ID_apocalypsenow", "movie_title": "Apocalypse Now", "placeholder": "_NEEDS_ID_walterkurtz"},
    {"name": "Lieutenant Colonel Bill Kilgore", "movie_id": "_NEEDS_MOVIE_ID_apocalypsenow", "movie_title": "Apocalypse Now", "placeholder": "_NEEDS_ID_billkilgore"},
    # The Silence of the Lambs
    {"name": "Clarice Starling", "movie_id": "_NEEDS_MOVIE_ID_thesilenceofthelambs", "movie_title": "The Silence of the Lambs", "placeholder": "_NEEDS_ID_claricestarling"},
    {"name": "Dr. Hannibal Lecter", "movie_id": "_NEEDS_MOVIE_ID_thesilenceofthelambs", "movie_title": "The Silence of the Lambs", "placeholder": "_NEEDS_ID_hanniballecter"},
    {"name": "Jack Crawford", "movie_id": "_NEEDS_MOVIE_ID_thesilenceofthelambs", "movie_title": "The Silence of the Lambs", "placeholder": "_NEEDS_ID_jackcrawford"},
    # Oldboy
    {"name": "Oh Dae-su", "movie_id": "_NEEDS_MOVIE_ID_oldboy", "movie_title": "Oldboy", "placeholder": "_NEEDS_ID_ohdaesu"},
    {"name": "Lee Woo-jin", "movie_id": "_NEEDS_MOVIE_ID_oldboy", "movie_title": "Oldboy", "placeholder": "_NEEDS_ID_leewoojin"},
    {"name": "Mi-do", "movie_id": "_NEEDS_MOVIE_ID_oldboy", "movie_title": "Oldboy", "placeholder": "_NEEDS_ID_mido"},
    # 12 Angry Men
    {"name": "Juror 8", "movie_id": "_NEEDS_MOVIE_ID_12angrymen", "movie_title": "12 Angry Men", "placeholder": "_NEEDS_ID_juror8"},
    {"name": "Juror 3", "movie_id": "_NEEDS_MOVIE_ID_12angrymen", "movie_title": "12 Angry Men", "placeholder": "_NEEDS_ID_juror3"},
    # The Shining
    {"name": "Jack Torrance", "movie_id": "_NEEDS_MOVIE_ID_theshining", "movie_title": "The Shining", "placeholder": "_NEEDS_ID_jacktorrance"},
    {"name": "Wendy Torrance", "movie_id": "_NEEDS_MOVIE_ID_theshining", "movie_title": "The Shining", "placeholder": "_NEEDS_ID_wendytorrance"},
    {"name": "Danny Torrance", "movie_id": "_NEEDS_MOVIE_ID_theshining", "movie_title": "The Shining", "placeholder": "_NEEDS_ID_dannytorrance"},
    # Drive
    {"name": "Driver", "movie_id": "_NEEDS_MOVIE_ID_drive", "movie_title": "Drive", "placeholder": "_NEEDS_ID_driver"},
    {"name": "Irene", "movie_id": "_NEEDS_MOVIE_ID_drive", "movie_title": "Drive", "placeholder": "_NEEDS_ID_irene"},
    {"name": "Bernie Rose", "movie_id": "_NEEDS_MOVIE_ID_drive", "movie_title": "Drive", "placeholder": "_NEEDS_ID_bernierose"},
    # Casablanca
    {"name": "Rick Blaine", "movie_id": "_NEEDS_MOVIE_ID_casablanca", "movie_title": "Casablanca", "placeholder": "_NEEDS_ID_rickblaine"},
    {"name": "Ilsa Lund", "movie_id": "_NEEDS_MOVIE_ID_casablanca", "movie_title": "Casablanca", "placeholder": "_NEEDS_ID_ilsalund"},
    {"name": "Victor Laszlo", "movie_id": "_NEEDS_MOVIE_ID_casablanca", "movie_title": "Casablanca", "placeholder": "_NEEDS_ID_victorlaszlo"},
    # Memories of Murder
    {"name": "Park Doo-man", "movie_id": "_NEEDS_MOVIE_ID_memoriesofmurder", "movie_title": "Memories of Murder", "placeholder": "_NEEDS_ID_parkdooman"},
    {"name": "Seo Tae-yoon", "movie_id": "_NEEDS_MOVIE_ID_memoriesofmurder", "movie_title": "Memories of Murder", "placeholder": "_NEEDS_ID_seotaeyoon"},
    # Children of Men
    {"name": "Theo Faron", "movie_id": "_NEEDS_MOVIE_ID_childrenofmen", "movie_title": "Children of Men", "placeholder": "_NEEDS_ID_theofaron"},
    {"name": "Kee", "movie_id": "_NEEDS_MOVIE_ID_childrenofmen", "movie_title": "Children of Men", "placeholder": "_NEEDS_ID_kee"},
    {"name": "Julian Taylor", "movie_id": "_NEEDS_MOVIE_ID_childrenofmen", "movie_title": "Children of Men", "placeholder": "_NEEDS_ID_juliantaylor"},
    # Mad Max: Fury Road
    {"name": "Max Rockatansky", "movie_id": "_NEEDS_MOVIE_ID_madmaxfuryroad", "movie_title": "Mad Max: Fury Road", "placeholder": "_NEEDS_ID_maxrockatansky"},
    {"name": "Imperator Furiosa", "movie_id": "_NEEDS_MOVIE_ID_madmaxfuryroad", "movie_title": "Mad Max: Fury Road", "placeholder": "_NEEDS_ID_imperatorfuriosa"},
    {"name": "Immortan Joe", "movie_id": "_NEEDS_MOVIE_ID_madmaxfuryroad", "movie_title": "Mad Max: Fury Road", "placeholder": "_NEEDS_ID_immortanjoe"},
    # Pan's Labyrinth
    {"name": "Ofelia", "movie_id": "_NEEDS_MOVIE_ID_panslabyrinth", "movie_title": "Pan's Labyrinth", "placeholder": "_NEEDS_ID_ofelia"},
    {"name": "Captain Vidal", "movie_id": "_NEEDS_MOVIE_ID_panslabyrinth", "movie_title": "Pan's Labyrinth", "placeholder": "_NEEDS_ID_captainvidal"},
    {"name": "Mercedes", "movie_id": "_NEEDS_MOVIE_ID_panslabyrinth", "movie_title": "Pan's Labyrinth", "placeholder": "_NEEDS_ID_mercedes"},
    # Princess Mononoke
    {"name": "Prince Ashitaka", "movie_id": "_NEEDS_MOVIE_ID_princessmononoke", "movie_title": "Princess Mononoke", "placeholder": "_NEEDS_ID_princeashitaka"},
    {"name": "San", "movie_id": "_NEEDS_MOVIE_ID_princessmononoke", "movie_title": "Princess Mononoke", "placeholder": "_NEEDS_ID_sanmononoke"},
    {"name": "Lady Eboshi", "movie_id": "_NEEDS_MOVIE_ID_princessmononoke", "movie_title": "Princess Mononoke", "placeholder": "_NEEDS_ID_ladyeboshi"},
    # Catch Me If You Can
    {"name": "Frank Abagnale Jr.", "movie_id": "_NEEDS_MOVIE_ID_catchmeifyoucan", "movie_title": "Catch Me If You Can", "placeholder": "_NEEDS_ID_frankabagnale"},
    {"name": "Carl Hanratty", "movie_id": "_NEEDS_MOVIE_ID_catchmeifyoucan", "movie_title": "Catch Me If You Can", "placeholder": "_NEEDS_ID_carlhanratty"},
    # Zodiac
    {"name": "Robert Graysmith", "movie_id": "_NEEDS_MOVIE_ID_zodiac", "movie_title": "Zodiac", "placeholder": "_NEEDS_ID_robertgraysmith"},
    {"name": "Inspector Dave Toschi", "movie_id": "_NEEDS_MOVIE_ID_zodiac", "movie_title": "Zodiac", "placeholder": "_NEEDS_ID_davetoschi"},
    {"name": "Paul Avery", "movie_id": "_NEEDS_MOVIE_ID_zodiac", "movie_title": "Zodiac", "placeholder": "_NEEDS_ID_paulavery"},
    # The Wolf of Wall Street
    {"name": "Jordan Belfort", "movie_id": "_NEEDS_MOVIE_ID_thewolfofwallstreet", "movie_title": "The Wolf of Wall Street", "placeholder": "_NEEDS_ID_jordanbelfort"},
    {"name": "Donnie Azoff", "movie_id": "_NEEDS_MOVIE_ID_thewolfofwallstreet", "movie_title": "The Wolf of Wall Street", "placeholder": "_NEEDS_ID_donnieazoff"},
    {"name": "Patrick Denham", "movie_id": "_NEEDS_MOVIE_ID_thewolfofwallstreet", "movie_title": "The Wolf of Wall Street", "placeholder": "_NEEDS_ID_patrickdenham"},
    # Requiem for a Dream
    {"name": "Harry Goldfarb", "movie_id": "_NEEDS_MOVIE_ID_requiemforadream", "movie_title": "Requiem for a Dream", "placeholder": "_NEEDS_ID_harrygoldfarb"},
    {"name": "Marion Silver", "movie_id": "_NEEDS_MOVIE_ID_requiemforadream", "movie_title": "Requiem for a Dream", "placeholder": "_NEEDS_ID_marionsilver"},
    {"name": "Sara Goldfarb", "movie_id": "_NEEDS_MOVIE_ID_requiemforadream", "movie_title": "Requiem for a Dream", "placeholder": "_NEEDS_ID_saragoldfarb"},
    # Schindler's List
    {"name": "Oskar Schindler", "movie_id": "_NEEDS_MOVIE_ID_schindlerslist", "movie_title": "Schindler's List", "placeholder": "_NEEDS_ID_oskarschindler"},
    {"name": "Amon Göth", "movie_id": "_NEEDS_MOVIE_ID_schindlerslist", "movie_title": "Schindler's List", "placeholder": "_NEEDS_ID_amongoth"},
    {"name": "Itzhak Stern", "movie_id": "_NEEDS_MOVIE_ID_schindlerslist", "movie_title": "Schindler's List", "placeholder": "_NEEDS_ID_itzhakstern"},
    # Trainspotting
    {"name": "Mark Renton", "movie_id": "_NEEDS_MOVIE_ID_trainspotting", "movie_title": "Trainspotting", "placeholder": "_NEEDS_ID_markrenton"},
    {"name": "Francis Begbie", "movie_id": "_NEEDS_MOVIE_ID_trainspotting", "movie_title": "Trainspotting", "placeholder": "_NEEDS_ID_francisbegbie"},
    {"name": "Sick Boy", "movie_id": "_NEEDS_MOVIE_ID_trainspotting", "movie_title": "Trainspotting", "placeholder": "_NEEDS_ID_sickboy"},
]

new_relationships = [
    # Blade Runner
    {"character_id_a": "_NEEDS_ID_deckard1982", "character_id_b": "_NEEDS_ID_roybatty", "movie_id": "_NEEDS_MOVIE_ID_bladerunner", "label": "Deckard & Roy Batty", "search_query": "Blade Runner Rick Deckard Roy Batty confrontation tears in rain"},
    {"character_id_a": "_NEEDS_ID_deckard1982", "character_id_b": "_NEEDS_ID_rachael", "movie_id": "_NEEDS_MOVIE_ID_bladerunner", "label": "Deckard & Rachael", "search_query": "Blade Runner Rick Deckard Rachael love empathy replicant"},
    # 2001: A Space Odyssey
    {"character_id_a": "_NEEDS_ID_davidbowman", "character_id_b": "_NEEDS_ID_hal9000", "movie_id": "_NEEDS_MOVIE_ID_2001aspaceodyssey", "label": "Bowman & HAL 9000", "search_query": "2001 A Space Odyssey David Bowman HAL 9000 confrontation disconnect"},
    # Apocalypse Now
    {"character_id_a": "_NEEDS_ID_benjaminwillard", "character_id_b": "_NEEDS_ID_walterkurtz", "movie_id": "_NEEDS_MOVIE_ID_apocalypsenow", "label": "Willard & Kurtz", "search_query": "Apocalypse Now Willard Kurtz confrontation philosophical madness"},
    {"character_id_a": "_NEEDS_ID_benjaminwillard", "character_id_b": "_NEEDS_ID_billkilgore", "movie_id": "_NEEDS_MOVIE_ID_apocalypsenow", "label": "Willard & Kilgore", "search_query": "Apocalypse Now Willard Kilgore contrast war absurdity"},
    # The Silence of the Lambs
    {"character_id_a": "_NEEDS_ID_claricestarling", "character_id_b": "_NEEDS_ID_hanniballecter", "movie_id": "_NEEDS_MOVIE_ID_thesilenceofthelambs", "label": "Clarice & Lecter", "search_query": "The Silence of the Lambs Clarice Starling Hannibal Lecter quid pro quo dynamic"},
    {"character_id_a": "_NEEDS_ID_claricestarling", "character_id_b": "_NEEDS_ID_jackcrawford", "movie_id": "_NEEDS_MOVIE_ID_thesilenceofthelambs", "label": "Clarice & Crawford", "search_query": "The Silence of the Lambs Clarice Starling Jack Crawford mentor relationship"},
    # Oldboy
    {"character_id_a": "_NEEDS_ID_ohdaesu", "character_id_b": "_NEEDS_ID_leewoojin", "movie_id": "_NEEDS_MOVIE_ID_oldboy", "label": "Dae-su & Woo-jin", "search_query": "Oldboy Oh Dae-su Lee Woo-jin revenge rivalry twist"},
    {"character_id_a": "_NEEDS_ID_ohdaesu", "character_id_b": "_NEEDS_ID_mido", "movie_id": "_NEEDS_MOVIE_ID_oldboy", "label": "Dae-su & Mi-do", "search_query": "Oldboy Oh Dae-su Mi-do relationship tragic bond"},
    # 12 Angry Men
    {"character_id_a": "_NEEDS_ID_juror8", "character_id_b": "_NEEDS_ID_juror3", "movie_id": "_NEEDS_MOVIE_ID_12angrymen", "label": "Juror 8 & Juror 3", "search_query": "12 Angry Men Juror 8 Juror 3 debate reasonable doubt conflict"},
    # The Shining
    {"character_id_a": "_NEEDS_ID_jacktorrance", "character_id_b": "_NEEDS_ID_wendytorrance", "movie_id": "_NEEDS_MOVIE_ID_theshining", "label": "Jack & Wendy", "search_query": "The Shining Jack Torrance Wendy Torrance marriage breakdown terror"},
    {"character_id_a": "_NEEDS_ID_jacktorrance", "character_id_b": "_NEEDS_ID_dannytorrance", "movie_id": "_NEEDS_MOVIE_ID_theshining", "label": "Jack & Danny", "search_query": "The Shining Jack Torrance Danny Torrance psychological threat father son"},
    # Drive
    {"character_id_a": "_NEEDS_ID_driver", "character_id_b": "_NEEDS_ID_irene", "movie_id": "_NEEDS_MOVIE_ID_drive", "label": "Driver & Irene", "search_query": "Drive film Driver Irene romance protector elevator"},
    {"character_id_a": "_NEEDS_ID_driver", "character_id_b": "_NEEDS_ID_bernierose", "movie_id": "_NEEDS_MOVIE_ID_drive", "label": "Driver & Bernie Rose", "search_query": "Drive film Driver Bernie Rose mob conflict confrontation"},
    # Casablanca
    {"character_id_a": "_NEEDS_ID_rickblaine", "character_id_b": "_NEEDS_ID_ilsalund", "movie_id": "_NEEDS_MOVIE_ID_casablanca", "label": "Rick & Ilsa", "search_query": "Casablanca Rick Blaine Ilsa Lund love story Paris sacrifice"},
    {"character_id_a": "_NEEDS_ID_rickblaine", "character_id_b": "_NEEDS_ID_victorlaszlo", "movie_id": "_NEEDS_MOVIE_ID_casablanca", "label": "Rick & Victor", "search_query": "Casablanca Rick Blaine Victor Laszlo antifascist alliance respect"},
    # Memories of Murder
    {"character_id_a": "_NEEDS_ID_parkdooman", "character_id_b": "_NEEDS_ID_seotaeyoon", "movie_id": "_NEEDS_MOVIE_ID_memoriesofmurder", "label": "Doo-man & Tae-yoon", "search_query": "Memories of Murder Park Doo-man Seo Tae-yoon detective partnership contrast"},
    # Children of Men
    {"character_id_a": "_NEEDS_ID_theofaron", "character_id_b": "_NEEDS_ID_kee", "movie_id": "_NEEDS_MOVIE_ID_childrenofmen", "label": "Theo & Kee", "search_query": "Children of Men Theo Faron Kee refugee miraculous pregnancy protection"},
    {"character_id_a": "_NEEDS_ID_theofaron", "character_id_b": "_NEEDS_ID_juliantaylor", "movie_id": "_NEEDS_MOVIE_ID_childrenofmen", "label": "Theo & Julian", "search_query": "Children of Men Theo Faron Julian Taylor past relationship Fishes"},
    # Mad Max: Fury Road
    {"character_id_a": "_NEEDS_ID_maxrockatansky", "character_id_b": "_NEEDS_ID_imperatorfuriosa", "movie_id": "_NEEDS_MOVIE_ID_madmaxfuryroad", "label": "Max & Furiosa", "search_query": "Mad Max Fury Road Max Rockatansky Imperator Furiosa alliance redemption"},
    {"character_id_a": "_NEEDS_ID_imperatorfuriosa", "character_id_b": "_NEEDS_ID_immortanjoe", "movie_id": "_NEEDS_MOVIE_ID_madmaxfuryroad", "label": "Furiosa & Immortan Joe", "search_query": "Mad Max Fury Road Imperator Furiosa Immortan Joe rebellion tyranny"},
    # Pan's Labyrinth
    {"character_id_a": "_NEEDS_ID_ofelia", "character_id_b": "_NEEDS_ID_captainvidal", "movie_id": "_NEEDS_MOVIE_ID_panslabyrinth", "label": "Ofelia & Vidal", "search_query": "Pan's Labyrinth Ofelia Captain Vidal terror stepdaughter fascist"},
    {"character_id_a": "_NEEDS_ID_mercedes", "character_id_b": "_NEEDS_ID_captainvidal", "movie_id": "_NEEDS_MOVIE_ID_panslabyrinth", "label": "Mercedes & Vidal", "search_query": "Pan's Labyrinth Mercedes Captain Vidal housekeeper knife resistance"},
    # Princess Mononoke
    {"character_id_a": "_NEEDS_ID_princeashitaka", "character_id_b": "_NEEDS_ID_sanmononoke", "movie_id": "_NEEDS_MOVIE_ID_princessmononoke", "label": "Ashitaka & San", "search_query": "Princess Mononoke Ashitaka San love bridge nature humans"},
    {"character_id_a": "_NEEDS_ID_sanmononoke", "character_id_b": "_NEEDS_ID_ladyeboshi", "movie_id": "_NEEDS_MOVIE_ID_princessmononoke", "label": "San & Eboshi", "search_query": "Princess Mononoke San Lady Eboshi forest spirit Iron Town conflict"},
    # Catch Me If You Can
    {"character_id_a": "_NEEDS_ID_frankabagnale", "character_id_b": "_NEEDS_ID_carlhanratty", "movie_id": "_NEEDS_MOVIE_ID_catchmeifyoucan", "label": "Frank & Hanratty", "search_query": "Catch Me If You Can Frank Abagnale Carl Hanratty cat and mouse Christmas phone call"},
    # Zodiac
    {"character_id_a": "_NEEDS_ID_robertgraysmith", "character_id_b": "_NEEDS_ID_davetoschi", "movie_id": "_NEEDS_MOVIE_ID_zodiac", "label": "Graysmith & Toschi", "search_query": "Zodiac Robert Graysmith Dave Toschi investigation obsession"},
    {"character_id_a": "_NEEDS_ID_robertgraysmith", "character_id_b": "_NEEDS_ID_paulavery", "movie_id": "_NEEDS_MOVIE_ID_zodiac", "label": "Graysmith & Avery", "search_query": "Zodiac Robert Graysmith Paul Avery San Francisco Chronicle ciphers"},
    # The Wolf of Wall Street
    {"character_id_a": "_NEEDS_ID_jordanbelfort", "character_id_b": "_NEEDS_ID_donnieazoff", "movie_id": "_NEEDS_MOVIE_ID_thewolfofwallstreet", "label": "Jordan & Donnie", "search_query": "The Wolf of Wall Street Jordan Belfort Donnie Azoff Stratton Oakmont partnership"},
    {"character_id_a": "_NEEDS_ID_jordanbelfort", "character_id_b": "_NEEDS_ID_patrickdenham", "movie_id": "_NEEDS_MOVIE_ID_thewolfofwallstreet", "label": "Jordan & Denham", "search_query": "The Wolf of Wall Street Jordan Belfort Patrick Denham FBI yacht scene"},
    # Requiem for a Dream
    {"character_id_a": "_NEEDS_ID_harrygoldfarb", "character_id_b": "_NEEDS_ID_marionsilver", "movie_id": "_NEEDS_MOVIE_ID_requiemforadream", "label": "Harry & Marion", "search_query": "Requiem for a Dream Harry Marion love addiction tragic collapse"},
    {"character_id_a": "_NEEDS_ID_harrygoldfarb", "character_id_b": "_NEEDS_ID_saragoldfarb", "movie_id": "_NEEDS_MOVIE_ID_requiemforadream", "label": "Harry & Sara", "search_query": "Requiem for a Dream Harry Sara mother son red dress tragedy"},
    # Schindler's List
    {"character_id_a": "_NEEDS_ID_oskarschindler", "character_id_b": "_NEEDS_ID_amongoth", "movie_id": "_NEEDS_MOVIE_ID_schindlerslist", "label": "Schindler & Göth", "search_query": "Schindler's List Oskar Schindler Amon Goth relationship power pardon"},
    {"character_id_a": "_NEEDS_ID_oskarschindler", "character_id_b": "_NEEDS_ID_itzhakstern", "movie_id": "_NEEDS_MOVIE_ID_schindlerslist", "label": "Schindler & Stern", "search_query": "Schindler's List Oskar Schindler Itzhak Stern friendship list who saves one life"},
    # Trainspotting
    {"character_id_a": "_NEEDS_ID_markrenton", "character_id_b": "_NEEDS_ID_francisbegbie", "movie_id": "_NEEDS_MOVIE_ID_trainspotting", "label": "Renton & Begbie", "search_query": "Trainspotting Mark Renton Francis Begbie psychotic friend violence betrayal"},
    {"character_id_a": "_NEEDS_ID_markrenton", "character_id_b": "_NEEDS_ID_sickboy", "movie_id": "_NEEDS_MOVIE_ID_trainspotting", "label": "Renton & Sick Boy", "search_query": "Trainspotting Mark Renton Sick Boy friendship Sean Connery cynicism"},
]

# Append only unique items
added_movies = 0
for m in new_movies:
    if m["title"].lower() not in existing_movie_titles:
        batch.setdefault("movies", []).append(m)
        existing_movie_titles.add(m["title"].lower())
        added_movies += 1

added_chars = 0
for c in new_characters:
    key = (c["movie_title"].lower(), c["name"].lower())
    if key not in existing_char_keys:
        batch.setdefault("characters", []).append(c)
        existing_char_keys.add(key)
        added_chars += 1

added_rels = 0
for r in new_relationships:
    key = (r.get("movie_id"), r["label"].lower())
    if key not in existing_rel_labels:
        batch.setdefault("relationships", []).append(r)
        existing_rel_labels.add(key)
        added_rels += 1

with open(BATCH_PATH, "w", encoding="utf-8") as f:
    json.dump(batch, f, indent=2, ensure_ascii=False)

print(f"Successfully added {added_movies} movies, {added_chars} characters, {added_rels} relationships to batch.json!")
print(f"Total movies now: {len(batch['movies'])}")
print(f"Total characters now: {len(batch['characters'])}")
print(f"Total relationships now: {len(batch['relationships'])}")

