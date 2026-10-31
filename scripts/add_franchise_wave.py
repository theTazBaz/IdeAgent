"""
scripts/add_franchise_wave.py
==============================
Appends the Marvel, Harry Potter, and DC franchises (29 films, 106 characters, 65 relationships)
to data/batch.json with guaranteed uniqueness and zero duplicates.
"""
import json
from pathlib import Path

BATCH_FILE = Path(__file__).resolve().parent.parent / "data" / "batch.json"

NEW_MOVIES = [
    # --- Harry Potter (8 films) ---
    {"title": "Harry Potter and the Philosopher's Stone", "placeholder": "_NEEDS_MOVIE_ID_hp1"},
    {"title": "Harry Potter and the Chamber of Secrets", "placeholder": "_NEEDS_MOVIE_ID_hp2"},
    {"title": "Harry Potter and the Prisoner of Azkaban", "placeholder": "_NEEDS_MOVIE_ID_hp3"},
    {"title": "Harry Potter and the Goblet of Fire", "placeholder": "_NEEDS_MOVIE_ID_hp4"},
    {"title": "Harry Potter and the Order of the Phoenix", "placeholder": "_NEEDS_MOVIE_ID_hp5"},
    {"title": "Harry Potter and the Half-Blood Prince", "placeholder": "_NEEDS_MOVIE_ID_hp6"},
    {"title": "Harry Potter and the Deathly Hallows: Part 1", "placeholder": "_NEEDS_MOVIE_ID_hp7"},
    {"title": "Harry Potter and the Deathly Hallows: Part 2", "placeholder": "_NEEDS_MOVIE_ID_hp8"},

    # --- Marvel Cinematic Universe & X-Men (12 films) ---
    {"title": "Iron Man", "placeholder": "_NEEDS_MOVIE_ID_ironman"},
    {"title": "The Avengers", "placeholder": "_NEEDS_MOVIE_ID_avengers"},
    {"title": "Captain America: The Winter Soldier", "placeholder": "_NEEDS_MOVIE_ID_wintersoldier"},
    {"title": "Guardians of the Galaxy", "placeholder": "_NEEDS_MOVIE_ID_gotg"},
    {"title": "Captain America: Civil War", "placeholder": "_NEEDS_MOVIE_ID_civilwar"},
    {"title": "Thor: Ragnarok", "placeholder": "_NEEDS_MOVIE_ID_ragnarok"},
    {"title": "Black Panther", "placeholder": "_NEEDS_MOVIE_ID_blackpanther"},
    {"title": "Avengers: Infinity War", "placeholder": "_NEEDS_MOVIE_ID_infinitywar"},
    {"title": "Avengers: Endgame", "placeholder": "_NEEDS_MOVIE_ID_endgame"},
    {"title": "Spider-Man: No Way Home", "placeholder": "_NEEDS_MOVIE_ID_nowayhome"},
    {"title": "Logan", "placeholder": "_NEEDS_MOVIE_ID_logan"},
    {"title": "X-Men: Days of Future Past", "placeholder": "_NEEDS_MOVIE_ID_dofp"},

    # --- DC Universe (9 films) ---
    {"title": "Batman Begins", "placeholder": "_NEEDS_MOVIE_ID_batmanbegins"},
    {"title": "The Dark Knight Rises", "placeholder": "_NEEDS_MOVIE_ID_tldr"},
    {"title": "The Batman", "placeholder": "_NEEDS_MOVIE_ID_thebatman"},
    {"title": "Joker", "placeholder": "_NEEDS_MOVIE_ID_joker"},
    {"title": "Man of Steel", "placeholder": "_NEEDS_MOVIE_ID_manofsteel"},
    {"title": "Batman v Superman: Dawn of Justice", "placeholder": "_NEEDS_MOVIE_ID_bvs"},
    {"title": "Wonder Woman", "placeholder": "_NEEDS_MOVIE_ID_wonderwoman"},
    {"title": "Watchmen", "placeholder": "_NEEDS_MOVIE_ID_watchmen"},
    {"title": "V for Vendetta", "placeholder": "_NEEDS_MOVIE_ID_vforvendetta"},
]

NEW_CHARACTERS = [
    # HP 1
    {"name": "Harry Potter", "movie_title": "Harry Potter and the Philosopher's Stone", "movie_id": "_NEEDS_MOVIE_ID_hp1", "placeholder": "_NEEDS_ID_hp1_harry", "fandom_wiki": "harrypotter", "fandom_slug": "Harry_Potter"},
    {"name": "Ron Weasley", "movie_title": "Harry Potter and the Philosopher's Stone", "movie_id": "_NEEDS_MOVIE_ID_hp1", "placeholder": "_NEEDS_ID_hp1_ron", "fandom_wiki": "harrypotter", "fandom_slug": "Ron_Weasley"},
    {"name": "Hermione Granger", "movie_title": "Harry Potter and the Philosopher's Stone", "movie_id": "_NEEDS_MOVIE_ID_hp1", "placeholder": "_NEEDS_ID_hp1_hermione", "fandom_wiki": "harrypotter", "fandom_slug": "Hermione_Granger"},
    {"name": "Albus Dumbledore", "movie_title": "Harry Potter and the Philosopher's Stone", "movie_id": "_NEEDS_MOVIE_ID_hp1", "placeholder": "_NEEDS_ID_hp1_dumbledore", "fandom_wiki": "harrypotter", "fandom_slug": "Albus_Dumbledore"},

    # HP 2
    {"name": "Harry Potter", "movie_title": "Harry Potter and the Chamber of Secrets", "movie_id": "_NEEDS_MOVIE_ID_hp2", "placeholder": "_NEEDS_ID_hp2_harry", "fandom_wiki": "harrypotter", "fandom_slug": "Harry_Potter"},
    {"name": "Tom Riddle", "movie_title": "Harry Potter and the Chamber of Secrets", "movie_id": "_NEEDS_MOVIE_ID_hp2", "placeholder": "_NEEDS_ID_hp2_tomriddle", "fandom_wiki": "harrypotter", "fandom_slug": "Tom_Riddle"},
    {"name": "Dobby", "movie_title": "Harry Potter and the Chamber of Secrets", "movie_id": "_NEEDS_MOVIE_ID_hp2", "placeholder": "_NEEDS_ID_hp2_dobby", "fandom_wiki": "harrypotter", "fandom_slug": "Dobby"},

    # HP 3
    {"name": "Harry Potter", "movie_title": "Harry Potter and the Prisoner of Azkaban", "movie_id": "_NEEDS_MOVIE_ID_hp3", "placeholder": "_NEEDS_ID_hp3_harry", "fandom_wiki": "harrypotter", "fandom_slug": "Harry_Potter"},
    {"name": "Sirius Black", "movie_title": "Harry Potter and the Prisoner of Azkaban", "movie_id": "_NEEDS_MOVIE_ID_hp3", "placeholder": "_NEEDS_ID_hp3_sirius", "fandom_wiki": "harrypotter", "fandom_slug": "Sirius_Black"},
    {"name": "Remus Lupin", "movie_title": "Harry Potter and the Prisoner of Azkaban", "movie_id": "_NEEDS_MOVIE_ID_hp3", "placeholder": "_NEEDS_ID_hp3_lupin", "fandom_wiki": "harrypotter", "fandom_slug": "Remus_Lupin"},
    {"name": "Severus Snape", "movie_title": "Harry Potter and the Prisoner of Azkaban", "movie_id": "_NEEDS_MOVIE_ID_hp3", "placeholder": "_NEEDS_ID_hp3_snape", "fandom_wiki": "harrypotter", "fandom_slug": "Severus_Snape"},

    # HP 4
    {"name": "Harry Potter", "movie_title": "Harry Potter and the Goblet of Fire", "movie_id": "_NEEDS_MOVIE_ID_hp4", "placeholder": "_NEEDS_ID_hp4_harry", "fandom_wiki": "harrypotter", "fandom_slug": "Harry_Potter"},
    {"name": "Lord Voldemort", "movie_title": "Harry Potter and the Goblet of Fire", "movie_id": "_NEEDS_MOVIE_ID_hp4", "placeholder": "_NEEDS_ID_hp4_voldemort", "fandom_wiki": "harrypotter", "fandom_slug": "Tom_Riddle"},
    {"name": "Cedric Diggory", "movie_title": "Harry Potter and the Goblet of Fire", "movie_id": "_NEEDS_MOVIE_ID_hp4", "placeholder": "_NEEDS_ID_hp4_cedric", "fandom_wiki": "harrypotter", "fandom_slug": "Cedric_Diggory"},

    # HP 5
    {"name": "Harry Potter", "movie_title": "Harry Potter and the Order of the Phoenix", "movie_id": "_NEEDS_MOVIE_ID_hp5", "placeholder": "_NEEDS_ID_hp5_harry", "fandom_wiki": "harrypotter", "fandom_slug": "Harry_Potter"},
    {"name": "Dolores Umbridge", "movie_title": "Harry Potter and the Order of the Phoenix", "movie_id": "_NEEDS_MOVIE_ID_hp5", "placeholder": "_NEEDS_ID_hp5_umbridge", "fandom_wiki": "harrypotter", "fandom_slug": "Dolores_Umbridge"},
    {"name": "Luna Lovegood", "movie_title": "Harry Potter and the Order of the Phoenix", "movie_id": "_NEEDS_MOVIE_ID_hp5", "placeholder": "_NEEDS_ID_hp5_luna", "fandom_wiki": "harrypotter", "fandom_slug": "Luna_Lovegood"},
    {"name": "Bellatrix Lestrange", "movie_title": "Harry Potter and the Order of the Phoenix", "movie_id": "_NEEDS_MOVIE_ID_hp5", "placeholder": "_NEEDS_ID_hp5_bellatrix", "fandom_wiki": "harrypotter", "fandom_slug": "Bellatrix_Lestrange"},

    # HP 6
    {"name": "Harry Potter", "movie_title": "Harry Potter and the Half-Blood Prince", "movie_id": "_NEEDS_MOVIE_ID_hp6", "placeholder": "_NEEDS_ID_hp6_harry", "fandom_wiki": "harrypotter", "fandom_slug": "Harry_Potter"},
    {"name": "Severus Snape", "movie_title": "Harry Potter and the Half-Blood Prince", "movie_id": "_NEEDS_MOVIE_ID_hp6", "placeholder": "_NEEDS_ID_hp6_snape", "fandom_wiki": "harrypotter", "fandom_slug": "Severus_Snape"},
    {"name": "Draco Malfoy", "movie_title": "Harry Potter and the Half-Blood Prince", "movie_id": "_NEEDS_MOVIE_ID_hp6", "placeholder": "_NEEDS_ID_hp6_draco", "fandom_wiki": "harrypotter", "fandom_slug": "Draco_Malfoy"},
    {"name": "Albus Dumbledore", "movie_title": "Harry Potter and the Half-Blood Prince", "movie_id": "_NEEDS_MOVIE_ID_hp6", "placeholder": "_NEEDS_ID_hp6_dumbledore", "fandom_wiki": "harrypotter", "fandom_slug": "Albus_Dumbledore"},

    # HP 7
    {"name": "Harry Potter", "movie_title": "Harry Potter and the Deathly Hallows: Part 1", "movie_id": "_NEEDS_MOVIE_ID_hp7", "placeholder": "_NEEDS_ID_hp7_harry", "fandom_wiki": "harrypotter", "fandom_slug": "Harry_Potter"},
    {"name": "Ron Weasley", "movie_title": "Harry Potter and the Deathly Hallows: Part 1", "movie_id": "_NEEDS_MOVIE_ID_hp7", "placeholder": "_NEEDS_ID_hp7_ron", "fandom_wiki": "harrypotter", "fandom_slug": "Ron_Weasley"},
    {"name": "Hermione Granger", "movie_title": "Harry Potter and the Deathly Hallows: Part 1", "movie_id": "_NEEDS_MOVIE_ID_hp7", "placeholder": "_NEEDS_ID_hp7_hermione", "fandom_wiki": "harrypotter", "fandom_slug": "Hermione_Granger"},

    # HP 8
    {"name": "Harry Potter", "movie_title": "Harry Potter and the Deathly Hallows: Part 2", "movie_id": "_NEEDS_MOVIE_ID_hp8", "placeholder": "_NEEDS_ID_hp8_harry", "fandom_wiki": "harrypotter", "fandom_slug": "Harry_Potter"},
    {"name": "Lord Voldemort", "movie_title": "Harry Potter and the Deathly Hallows: Part 2", "movie_id": "_NEEDS_MOVIE_ID_hp8", "placeholder": "_NEEDS_ID_hp8_voldemort", "fandom_wiki": "harrypotter", "fandom_slug": "Tom_Riddle"},
    {"name": "Severus Snape", "movie_title": "Harry Potter and the Deathly Hallows: Part 2", "movie_id": "_NEEDS_MOVIE_ID_hp8", "placeholder": "_NEEDS_ID_hp8_snape", "fandom_wiki": "harrypotter", "fandom_slug": "Severus_Snape"},
    {"name": "Neville Longbottom", "movie_title": "Harry Potter and the Deathly Hallows: Part 2", "movie_id": "_NEEDS_MOVIE_ID_hp8", "placeholder": "_NEEDS_ID_hp8_neville", "fandom_wiki": "harrypotter", "fandom_slug": "Neville_Longbottom"},

    # Marvel: Iron Man
    {"name": "Tony Stark / Iron Man", "movie_title": "Iron Man", "movie_id": "_NEEDS_MOVIE_ID_ironman", "placeholder": "_NEEDS_ID_im_tony", "fandom_wiki": "marvelcinematicuniverse", "fandom_slug": "Tony_Stark"},
    {"name": "Pepper Potts", "movie_title": "Iron Man", "movie_id": "_NEEDS_MOVIE_ID_ironman", "placeholder": "_NEEDS_ID_im_pepper", "fandom_wiki": "marvelcinematicuniverse", "fandom_slug": "Pepper_Potts"},
    {"name": "Obadiah Stane", "movie_title": "Iron Man", "movie_id": "_NEEDS_MOVIE_ID_ironman", "placeholder": "_NEEDS_ID_im_obadiah", "fandom_wiki": "marvelcinematicuniverse", "fandom_slug": "Obadiah_Stane"},

    # Marvel: The Avengers
    {"name": "Steve Rogers / Captain America", "movie_title": "The Avengers", "movie_id": "_NEEDS_MOVIE_ID_avengers", "placeholder": "_NEEDS_ID_av_steve", "fandom_wiki": "marvelcinematicuniverse", "fandom_slug": "Steve_Rogers"},
    {"name": "Thor", "movie_title": "The Avengers", "movie_id": "_NEEDS_MOVIE_ID_avengers", "placeholder": "_NEEDS_ID_av_thor", "fandom_wiki": "marvelcinematicuniverse", "fandom_slug": "Thor"},
    {"name": "Loki", "movie_title": "The Avengers", "movie_id": "_NEEDS_MOVIE_ID_avengers", "placeholder": "_NEEDS_ID_av_loki", "fandom_wiki": "marvelcinematicuniverse", "fandom_slug": "Loki"},
    {"name": "Natasha Romanoff / Black Widow", "movie_title": "The Avengers", "movie_id": "_NEEDS_MOVIE_ID_avengers", "placeholder": "_NEEDS_ID_av_natasha", "fandom_wiki": "marvelcinematicuniverse", "fandom_slug": "Natasha_Romanoff"},

    # Marvel: The Winter Soldier
    {"name": "Steve Rogers / Captain America", "movie_title": "Captain America: The Winter Soldier", "movie_id": "_NEEDS_MOVIE_ID_wintersoldier", "placeholder": "_NEEDS_ID_ws_steve", "fandom_wiki": "marvelcinematicuniverse", "fandom_slug": "Steve_Rogers"},
    {"name": "Bucky Barnes / The Winter Soldier", "movie_title": "Captain America: The Winter Soldier", "movie_id": "_NEEDS_MOVIE_ID_wintersoldier", "placeholder": "_NEEDS_ID_ws_bucky", "fandom_wiki": "marvelcinematicuniverse", "fandom_slug": "Bucky_Barnes"},
    {"name": "Sam Wilson / Falcon", "movie_title": "Captain America: The Winter Soldier", "movie_id": "_NEEDS_MOVIE_ID_wintersoldier", "placeholder": "_NEEDS_ID_ws_sam", "fandom_wiki": "marvelcinematicuniverse", "fandom_slug": "Sam_Wilson"},
    {"name": "Alexander Pierce", "movie_title": "Captain America: The Winter Soldier", "movie_id": "_NEEDS_MOVIE_ID_wintersoldier", "placeholder": "_NEEDS_ID_ws_pierce", "fandom_wiki": "marvelcinematicuniverse", "fandom_slug": "Alexander_Pierce"},

    # Marvel: Guardians of the Galaxy
    {"name": "Peter Quill / Star-Lord", "movie_title": "Guardians of the Galaxy", "movie_id": "_NEEDS_MOVIE_ID_gotg", "placeholder": "_NEEDS_ID_gotg_quill", "fandom_wiki": "marvelcinematicuniverse", "fandom_slug": "Peter_Quill"},
    {"name": "Gamora", "movie_title": "Guardians of the Galaxy", "movie_id": "_NEEDS_MOVIE_ID_gotg", "placeholder": "_NEEDS_ID_gotg_gamora", "fandom_wiki": "marvelcinematicuniverse", "fandom_slug": "Gamora"},
    {"name": "Rocket Raccoon", "movie_title": "Guardians of the Galaxy", "movie_id": "_NEEDS_MOVIE_ID_gotg", "placeholder": "_NEEDS_ID_gotg_rocket", "fandom_wiki": "marvelcinematicuniverse", "fandom_slug": "Rocket"},
    {"name": "Ronan the Accuser", "movie_title": "Guardians of the Galaxy", "movie_id": "_NEEDS_MOVIE_ID_gotg", "placeholder": "_NEEDS_ID_gotg_ronan", "fandom_wiki": "marvelcinematicuniverse", "fandom_slug": "Ronan"},

    # Marvel: Civil War
    {"name": "Steve Rogers / Captain America", "movie_title": "Captain America: Civil War", "movie_id": "_NEEDS_MOVIE_ID_civilwar", "placeholder": "_NEEDS_ID_cw_steve", "fandom_wiki": "marvelcinematicuniverse", "fandom_slug": "Steve_Rogers"},
    {"name": "Tony Stark / Iron Man", "movie_title": "Captain America: Civil War", "movie_id": "_NEEDS_MOVIE_ID_civilwar", "placeholder": "_NEEDS_ID_cw_tony", "fandom_wiki": "marvelcinematicuniverse", "fandom_slug": "Tony_Stark"},
    {"name": "Helmut Zemo", "movie_title": "Captain America: Civil War", "movie_id": "_NEEDS_MOVIE_ID_civilwar", "placeholder": "_NEEDS_ID_cw_zemo", "fandom_wiki": "marvelcinematicuniverse", "fandom_slug": "Helmut_Zemo"},
    {"name": "T'Challa / Black Panther", "movie_title": "Captain America: Civil War", "movie_id": "_NEEDS_MOVIE_ID_civilwar", "placeholder": "_NEEDS_ID_cw_tchalla", "fandom_wiki": "marvelcinematicuniverse", "fandom_slug": "T%27Challa"},

    # Marvel: Thor Ragnarok
    {"name": "Thor", "movie_title": "Thor: Ragnarok", "movie_id": "_NEEDS_MOVIE_ID_ragnarok", "placeholder": "_NEEDS_ID_rag_thor", "fandom_wiki": "marvelcinematicuniverse", "fandom_slug": "Thor"},
    {"name": "Loki", "movie_title": "Thor: Ragnarok", "movie_id": "_NEEDS_MOVIE_ID_ragnarok", "placeholder": "_NEEDS_ID_rag_loki", "fandom_wiki": "marvelcinematicuniverse", "fandom_slug": "Loki"},
    {"name": "Hela", "movie_title": "Thor: Ragnarok", "movie_id": "_NEEDS_MOVIE_ID_ragnarok", "placeholder": "_NEEDS_ID_rag_hela", "fandom_wiki": "marvelcinematicuniverse", "fandom_slug": "Hela"},
    {"name": "Valkyrie", "movie_title": "Thor: Ragnarok", "movie_id": "_NEEDS_MOVIE_ID_ragnarok", "placeholder": "_NEEDS_ID_rag_valkyrie", "fandom_wiki": "marvelcinematicuniverse", "fandom_slug": "Valkyrie"},

    # Marvel: Black Panther
    {"name": "T'Challa / Black Panther", "movie_title": "Black Panther", "movie_id": "_NEEDS_MOVIE_ID_blackpanther", "placeholder": "_NEEDS_ID_bp_tchalla", "fandom_wiki": "marvelcinematicuniverse", "fandom_slug": "T%27Challa"},
    {"name": "Erik Killmonger", "movie_title": "Black Panther", "movie_id": "_NEEDS_MOVIE_ID_blackpanther", "placeholder": "_NEEDS_ID_bp_killmonger", "fandom_wiki": "marvelcinematicuniverse", "fandom_slug": "Erik_Killmonger"},
    {"name": "Nakia", "movie_title": "Black Panther", "movie_id": "_NEEDS_MOVIE_ID_blackpanther", "placeholder": "_NEEDS_ID_bp_nakia", "fandom_wiki": "marvelcinematicuniverse", "fandom_slug": "Nakia"},
    {"name": "Okoye", "movie_title": "Black Panther", "movie_id": "_NEEDS_MOVIE_ID_blackpanther", "placeholder": "_NEEDS_ID_bp_okoye", "fandom_wiki": "marvelcinematicuniverse", "fandom_slug": "Okoye"},

    # Marvel: Infinity War
    {"name": "Thanos", "movie_title": "Avengers: Infinity War", "movie_id": "_NEEDS_MOVIE_ID_infinitywar", "placeholder": "_NEEDS_ID_iw_thanos", "fandom_wiki": "marvelcinematicuniverse", "fandom_slug": "Thanos"},
    {"name": "Stephen Strange / Doctor Strange", "movie_title": "Avengers: Infinity War", "movie_id": "_NEEDS_MOVIE_ID_infinitywar", "placeholder": "_NEEDS_ID_iw_strange", "fandom_wiki": "marvelcinematicuniverse", "fandom_slug": "Stephen_Strange"},
    {"name": "Gamora", "movie_title": "Avengers: Infinity War", "movie_id": "_NEEDS_MOVIE_ID_infinitywar", "placeholder": "_NEEDS_ID_iw_gamora", "fandom_wiki": "marvelcinematicuniverse", "fandom_slug": "Gamora"},
    {"name": "Tony Stark / Iron Man", "movie_title": "Avengers: Infinity War", "movie_id": "_NEEDS_MOVIE_ID_infinitywar", "placeholder": "_NEEDS_ID_iw_tony", "fandom_wiki": "marvelcinematicuniverse", "fandom_slug": "Tony_Stark"},

    # Marvel: Endgame
    {"name": "Tony Stark / Iron Man", "movie_title": "Avengers: Endgame", "movie_id": "_NEEDS_MOVIE_ID_endgame", "placeholder": "_NEEDS_ID_eg_tony", "fandom_wiki": "marvelcinematicuniverse", "fandom_slug": "Tony_Stark"},
    {"name": "Steve Rogers / Captain America", "movie_title": "Avengers: Endgame", "movie_id": "_NEEDS_MOVIE_ID_endgame", "placeholder": "_NEEDS_ID_eg_steve", "fandom_wiki": "marvelcinematicuniverse", "fandom_slug": "Steve_Rogers"},
    {"name": "Nebula", "movie_title": "Avengers: Endgame", "movie_id": "_NEEDS_MOVIE_ID_endgame", "placeholder": "_NEEDS_ID_eg_nebula", "fandom_wiki": "marvelcinematicuniverse", "fandom_slug": "Nebula"},
    {"name": "Thanos", "movie_title": "Avengers: Endgame", "movie_id": "_NEEDS_MOVIE_ID_endgame", "placeholder": "_NEEDS_ID_eg_thanos", "fandom_wiki": "marvelcinematicuniverse", "fandom_slug": "Thanos"},

    # Marvel: No Way Home
    {"name": "Peter Parker / Spider-Man", "movie_title": "Spider-Man: No Way Home", "movie_id": "_NEEDS_MOVIE_ID_nowayhome", "placeholder": "_NEEDS_ID_nwh_peter", "fandom_wiki": "marvelcinematicuniverse", "fandom_slug": "Peter_Parker"},
    {"name": "Norman Osborn / Green Goblin", "movie_title": "Spider-Man: No Way Home", "movie_id": "_NEEDS_MOVIE_ID_nowayhome", "placeholder": "_NEEDS_ID_nwh_goblin", "fandom_wiki": "marvelcinematicuniverse", "fandom_slug": "Norman_Osborn"},
    {"name": "Stephen Strange / Doctor Strange", "movie_title": "Spider-Man: No Way Home", "movie_id": "_NEEDS_MOVIE_ID_nowayhome", "placeholder": "_NEEDS_ID_nwh_strange", "fandom_wiki": "marvelcinematicuniverse", "fandom_slug": "Stephen_Strange"},

    # Marvel: Logan
    {"name": "Logan / Wolverine", "movie_title": "Logan", "movie_id": "_NEEDS_MOVIE_ID_logan", "placeholder": "_NEEDS_ID_logan_logan", "fandom_wiki": "xmenmovies", "fandom_slug": "Wolverine"},
    {"name": "Charles Xavier / Professor X", "movie_title": "Logan", "movie_id": "_NEEDS_MOVIE_ID_logan", "placeholder": "_NEEDS_ID_logan_charles", "fandom_wiki": "xmenmovies", "fandom_slug": "Professor_X"},
    {"name": "Laura / X-23", "movie_title": "Logan", "movie_id": "_NEEDS_MOVIE_ID_logan", "placeholder": "_NEEDS_ID_logan_laura", "fandom_wiki": "xmenmovies", "fandom_slug": "X-23"},

    # Marvel: Days of Future Past
    {"name": "Charles Xavier", "movie_title": "X-Men: Days of Future Past", "movie_id": "_NEEDS_MOVIE_ID_dofp", "placeholder": "_NEEDS_ID_dofp_charles", "fandom_wiki": "xmenmovies", "fandom_slug": "Professor_X"},
    {"name": "Erik Lehnsherr / Magneto", "movie_title": "X-Men: Days of Future Past", "movie_id": "_NEEDS_MOVIE_ID_dofp", "placeholder": "_NEEDS_ID_dofp_magneto", "fandom_wiki": "xmenmovies", "fandom_slug": "Magneto"},
    {"name": "Raven / Mystique", "movie_title": "X-Men: Days of Future Past", "movie_id": "_NEEDS_MOVIE_ID_dofp", "placeholder": "_NEEDS_ID_dofp_mystique", "fandom_wiki": "xmenmovies", "fandom_slug": "Mystique"},

    # DC: Batman Begins
    {"name": "Bruce Wayne / Batman", "movie_title": "Batman Begins", "movie_id": "_NEEDS_MOVIE_ID_batmanbegins", "placeholder": "_NEEDS_ID_bb_bruce", "fandom_wiki": "batman", "fandom_slug": "Bruce_Wayne"},
    {"name": "Henri Ducard / Ra's al Ghul", "movie_title": "Batman Begins", "movie_id": "_NEEDS_MOVIE_ID_batmanbegins", "placeholder": "_NEEDS_ID_bb_ras", "fandom_wiki": "batman", "fandom_slug": "Ra%27s_al_Ghul"},
    {"name": "Rachel Dawes", "movie_title": "Batman Begins", "movie_id": "_NEEDS_MOVIE_ID_batmanbegins", "placeholder": "_NEEDS_ID_bb_rachel", "fandom_wiki": "batman", "fandom_slug": "Rachel_Dawes"},
    {"name": "Dr. Jonathan Crane / Scarecrow", "movie_title": "Batman Begins", "movie_id": "_NEEDS_MOVIE_ID_batmanbegins", "placeholder": "_NEEDS_ID_bb_scarecrow", "fandom_wiki": "batman", "fandom_slug": "Jonathan_Crane"},

    # DC: The Dark Knight Rises
    {"name": "Bruce Wayne / Batman", "movie_title": "The Dark Knight Rises", "movie_id": "_NEEDS_MOVIE_ID_tldr", "placeholder": "_NEEDS_ID_tldr_bruce", "fandom_wiki": "batman", "fandom_slug": "Bruce_Wayne"},
    {"name": "Bane", "movie_title": "The Dark Knight Rises", "movie_id": "_NEEDS_MOVIE_ID_tldr", "placeholder": "_NEEDS_ID_tldr_bane", "fandom_wiki": "batman", "fandom_slug": "Bane"},
    {"name": "Selina Kyle / Catwoman", "movie_title": "The Dark Knight Rises", "movie_id": "_NEEDS_MOVIE_ID_tldr", "placeholder": "_NEEDS_ID_tldr_selina", "fandom_wiki": "batman", "fandom_slug": "Selina_Kyle"},
    {"name": "John Blake", "movie_title": "The Dark Knight Rises", "movie_id": "_NEEDS_MOVIE_ID_tldr", "placeholder": "_NEEDS_ID_tldr_blake", "fandom_wiki": "batman", "fandom_slug": "John_Blake"},

    # DC: The Batman
    {"name": "Bruce Wayne / The Batman", "movie_title": "The Batman", "movie_id": "_NEEDS_MOVIE_ID_thebatman", "placeholder": "_NEEDS_ID_tb_bruce", "fandom_wiki": "batman", "fandom_slug": "Bruce_Wayne"},
    {"name": "Edward Nashton / The Riddler", "movie_title": "The Batman", "movie_id": "_NEEDS_MOVIE_ID_thebatman", "placeholder": "_NEEDS_ID_tb_riddler", "fandom_wiki": "batman", "fandom_slug": "Riddler"},
    {"name": "Selina Kyle / Catwoman", "movie_title": "The Batman", "movie_id": "_NEEDS_MOVIE_ID_thebatman", "placeholder": "_NEEDS_ID_tb_selina", "fandom_wiki": "batman", "fandom_slug": "Selina_Kyle"},
    {"name": "Lt. James Gordon", "movie_title": "The Batman", "movie_id": "_NEEDS_MOVIE_ID_thebatman", "placeholder": "_NEEDS_ID_tb_gordon", "fandom_wiki": "batman", "fandom_slug": "James_Gordon"},

    # DC: Joker
    {"name": "Arthur Fleck / Joker", "movie_title": "Joker", "movie_id": "_NEEDS_MOVIE_ID_joker", "placeholder": "_NEEDS_ID_jk_arthur", "fandom_wiki": "batman", "fandom_slug": "Joker"},
    {"name": "Murray Franklin", "movie_title": "Joker", "movie_id": "_NEEDS_MOVIE_ID_joker", "placeholder": "_NEEDS_ID_jk_murray", "fandom_wiki": "batman", "fandom_slug": "Murray_Franklin"},
    {"name": "Penny Fleck", "movie_title": "Joker", "movie_id": "_NEEDS_MOVIE_ID_joker", "placeholder": "_NEEDS_ID_jk_penny", "fandom_wiki": "batman", "fandom_slug": "Penny_Fleck"},

    # DC: Man of Steel
    {"name": "Clark Kent / Superman", "movie_title": "Man of Steel", "movie_id": "_NEEDS_MOVIE_ID_manofsteel", "placeholder": "_NEEDS_ID_mos_clark", "fandom_wiki": "dcextendeduniverse", "fandom_slug": "Superman"},
    {"name": "General Zod", "movie_title": "Man of Steel", "movie_id": "_NEEDS_MOVIE_ID_manofsteel", "placeholder": "_NEEDS_ID_mos_zod", "fandom_wiki": "dcextendeduniverse", "fandom_slug": "Dru-Zod"},
    {"name": "Lois Lane", "movie_title": "Man of Steel", "movie_id": "_NEEDS_MOVIE_ID_manofsteel", "placeholder": "_NEEDS_ID_mos_lois", "fandom_wiki": "dcextendeduniverse", "fandom_slug": "Lois_Lane"},
    {"name": "Jor-El", "movie_title": "Man of Steel", "movie_id": "_NEEDS_MOVIE_ID_manofsteel", "placeholder": "_NEEDS_ID_mos_jorel", "fandom_wiki": "dcextendeduniverse", "fandom_slug": "Jor-El"},

    # DC: BvS
    {"name": "Bruce Wayne / Batman", "movie_title": "Batman v Superman: Dawn of Justice", "movie_id": "_NEEDS_MOVIE_ID_bvs", "placeholder": "_NEEDS_ID_bvs_bruce", "fandom_wiki": "dcextendeduniverse", "fandom_slug": "Batman"},
    {"name": "Clark Kent / Superman", "movie_title": "Batman v Superman: Dawn of Justice", "movie_id": "_NEEDS_MOVIE_ID_bvs", "placeholder": "_NEEDS_ID_bvs_clark", "fandom_wiki": "dcextendeduniverse", "fandom_slug": "Superman"},
    {"name": "Lex Luthor", "movie_title": "Batman v Superman: Dawn of Justice", "movie_id": "_NEEDS_MOVIE_ID_bvs", "placeholder": "_NEEDS_ID_bvs_lex", "fandom_wiki": "dcextendeduniverse", "fandom_slug": "Lex_Luthor"},
    {"name": "Diana Prince / Wonder Woman", "movie_title": "Batman v Superman: Dawn of Justice", "movie_id": "_NEEDS_MOVIE_ID_bvs", "placeholder": "_NEEDS_ID_bvs_diana", "fandom_wiki": "dcextendeduniverse", "fandom_slug": "Wonder_Woman"},

    # DC: Wonder Woman
    {"name": "Diana Prince / Wonder Woman", "movie_title": "Wonder Woman", "movie_id": "_NEEDS_MOVIE_ID_wonderwoman", "placeholder": "_NEEDS_ID_ww_diana", "fandom_wiki": "dcextendeduniverse", "fandom_slug": "Wonder_Woman"},
    {"name": "Steve Trevor", "movie_title": "Wonder Woman", "movie_id": "_NEEDS_MOVIE_ID_wonderwoman", "placeholder": "_NEEDS_ID_ww_steve", "fandom_wiki": "dcextendeduniverse", "fandom_slug": "Steve_Trevor"},
    {"name": "Ares / Sir Patrick Morgan", "movie_title": "Wonder Woman", "movie_id": "_NEEDS_MOVIE_ID_wonderwoman", "placeholder": "_NEEDS_ID_ww_ares", "fandom_wiki": "dcextendeduniverse", "fandom_slug": "Ares"},

    # DC: Watchmen
    {"name": "Rorschach / Walter Kovacs", "movie_title": "Watchmen", "movie_id": "_NEEDS_MOVIE_ID_watchmen", "placeholder": "_NEEDS_ID_wm_rorschach", "fandom_wiki": "watchmen", "fandom_slug": "Walter_Kovacs"},
    {"name": "Dr. Manhattan / Jon Osterman", "movie_title": "Watchmen", "movie_id": "_NEEDS_MOVIE_ID_watchmen", "placeholder": "_NEEDS_ID_wm_manhattan", "fandom_wiki": "watchmen", "fandom_slug": "Jonathan_Osterman"},
    {"name": "Adrian Veidt / Ozymandias", "movie_title": "Watchmen", "movie_id": "_NEEDS_MOVIE_ID_watchmen", "placeholder": "_NEEDS_ID_wm_veidt", "fandom_wiki": "watchmen", "fandom_slug": "Adrian_Veidt"},
    {"name": "Dan Dreiberg / Nite Owl II", "movie_title": "Watchmen", "movie_id": "_NEEDS_MOVIE_ID_watchmen", "placeholder": "_NEEDS_ID_wm_dan", "fandom_wiki": "watchmen", "fandom_slug": "Dan_Dreiberg"},

    # DC: V for Vendetta
    {"name": "V", "movie_title": "V for Vendetta", "movie_id": "_NEEDS_MOVIE_ID_vforvendetta", "placeholder": "_NEEDS_ID_v_v", "fandom_wiki": "vforvendetta", "fandom_slug": "V"},
    {"name": "Evey Hammond", "movie_title": "V for Vendetta", "movie_id": "_NEEDS_MOVIE_ID_vforvendetta", "placeholder": "_NEEDS_ID_v_evey", "fandom_wiki": "vforvendetta", "fandom_slug": "Evey_Hammond"},
    {"name": "Chief Inspector Eric Finch", "movie_title": "V for Vendetta", "movie_id": "_NEEDS_MOVIE_ID_vforvendetta", "placeholder": "_NEEDS_ID_v_finch", "fandom_wiki": "vforvendetta", "fandom_slug": "Eric_Finch"},
]

NEW_RELATIONSHIPS = [
    # HP 1
    {"label": "Harry & Ron", "movie_id": "_NEEDS_MOVIE_ID_hp1", "character_id_a": "_NEEDS_ID_hp1_harry", "character_id_b": "_NEEDS_ID_hp1_ron", "wiki_query": "Harry Potter Ron Weasley friendship Hogwarts train bond"},
    {"label": "Harry & Hermione", "movie_id": "_NEEDS_MOVIE_ID_hp1", "character_id_a": "_NEEDS_ID_hp1_harry", "character_id_b": "_NEEDS_ID_hp1_hermione", "wiki_query": "Harry Potter Hermione Granger friendship troll intellectual alliance"},
    {"label": "Harry & Dumbledore", "movie_id": "_NEEDS_MOVIE_ID_hp1", "character_id_a": "_NEEDS_ID_hp1_harry", "character_id_b": "_NEEDS_ID_hp1_dumbledore", "wiki_query": "Harry Potter Albus Dumbledore mentorship mirror of erised guidance"},

    # HP 2
    {"label": "Harry & Tom Riddle", "movie_id": "_NEEDS_MOVIE_ID_hp2", "character_id_a": "_NEEDS_ID_hp2_harry", "character_id_b": "_NEEDS_ID_hp2_tomriddle", "wiki_query": "Harry Potter Tom Riddle chamber of secrets memory confrontation basilisk"},
    {"label": "Harry & Dobby", "movie_id": "_NEEDS_MOVIE_ID_hp2", "character_id_a": "_NEEDS_ID_hp2_harry", "character_id_b": "_NEEDS_ID_hp2_dobby", "wiki_query": "Harry Potter Dobby house elf protection freedom sock"},

    # HP 3
    {"label": "Harry & Sirius Black", "movie_id": "_NEEDS_MOVIE_ID_hp3", "character_id_a": "_NEEDS_ID_hp3_harry", "character_id_b": "_NEEDS_ID_hp3_sirius", "wiki_query": "Harry Potter Sirius Black godfather truth shrieking shack innocence"},
    {"label": "Sirius & Lupin", "movie_id": "_NEEDS_MOVIE_ID_hp3", "character_id_a": "_NEEDS_ID_hp3_sirius", "character_id_b": "_NEEDS_ID_hp3_lupin", "wiki_query": "Sirius Black Remus Lupin marauders brotherhood reunion friendship"},
    {"label": "Harry & Snape", "movie_id": "_NEEDS_MOVIE_ID_hp3", "character_id_a": "_NEEDS_ID_hp3_harry", "character_id_b": "_NEEDS_ID_hp3_snape", "wiki_query": "Harry Potter Severus Snape animosity james potter resentment protection"},

    # HP 4
    {"label": "Harry & Voldemort", "movie_id": "_NEEDS_MOVIE_ID_hp4", "character_id_a": "_NEEDS_ID_hp4_harry", "character_id_b": "_NEEDS_ID_hp4_voldemort", "wiki_query": "Harry Potter Lord Voldemort graveyard duel priori incantatem resurrection"},
    {"label": "Harry & Cedric", "movie_id": "_NEEDS_MOVIE_ID_hp4", "character_id_a": "_NEEDS_ID_hp4_harry", "character_id_b": "_NEEDS_ID_hp4_cedric", "wiki_query": "Harry Potter Cedric Diggory triwizard tournament rivalry mutual respect honor"},

    # HP 5
    {"label": "Harry & Dolores Umbridge", "movie_id": "_NEEDS_MOVIE_ID_hp5", "character_id_a": "_NEEDS_ID_hp5_harry", "character_id_b": "_NEEDS_ID_hp5_umbridge", "wiki_query": "Harry Potter Dolores Umbridge detention blood quill tyranny rebellion"},
    {"label": "Harry & Luna Lovegood", "movie_id": "_NEEDS_MOVIE_ID_hp5", "character_id_a": "_NEEDS_ID_hp5_harry", "character_id_b": "_NEEDS_ID_hp5_luna", "wiki_query": "Harry Potter Luna Lovegood thestrals empathy understanding kindred spirits"},

    # HP 6
    {"label": "Harry & Draco Malfoy", "movie_id": "_NEEDS_MOVIE_ID_hp6", "character_id_a": "_NEEDS_ID_hp6_harry", "character_id_b": "_NEEDS_ID_hp6_draco", "wiki_query": "Harry Potter Draco Malfoy rivalry bathroom duel sectumsempra dark mark pressure"},
    {"label": "Dumbledore & Snape", "movie_id": "_NEEDS_MOVIE_ID_hp6", "character_id_a": "_NEEDS_ID_hp6_dumbledore", "character_id_b": "_NEEDS_ID_hp6_snape", "wiki_query": "Albus Dumbledore Severus Snape unbreakable vow astronomy tower sacrifice trust"},

    # HP 7
    {"label": "Harry & Ron", "movie_id": "_NEEDS_MOVIE_ID_hp7", "character_id_a": "_NEEDS_ID_hp7_harry", "character_id_b": "_NEEDS_ID_hp7_ron", "wiki_query": "Harry Potter Ron Weasley horcrux locket conflict departure redemption sword of gryffindor"},
    {"label": "Ron & Hermione", "movie_id": "_NEEDS_MOVIE_ID_hp7", "character_id_a": "_NEEDS_ID_hp7_ron", "character_id_b": "_NEEDS_ID_hp7_hermione", "wiki_query": "Ron Weasley Hermione Granger romance heartbreak tent dance loyalty"},

    # HP 8
    {"label": "Harry & Voldemort", "movie_id": "_NEEDS_MOVIE_ID_hp8", "character_id_a": "_NEEDS_ID_hp8_harry", "character_id_b": "_NEEDS_ID_hp8_voldemort", "wiki_query": "Harry Potter Lord Voldemort final battle battle of hogwarts elder wand destiny"},
    {"label": "Harry & Snape", "movie_id": "_NEEDS_MOVIE_ID_hp8", "character_id_a": "_NEEDS_ID_hp8_harry", "character_id_b": "_NEEDS_ID_hp8_snape", "wiki_query": "Harry Potter Severus Snape the princes tale tears memories truth lily potter"},
    {"label": "Neville & Voldemort", "movie_id": "_NEEDS_MOVIE_ID_hp8", "character_id_a": "_NEEDS_ID_hp8_neville", "character_id_b": "_NEEDS_ID_hp8_voldemort", "wiki_query": "Neville Longbottom Lord Voldemort defiance sword of gryffindor nagini courage"},

    # Marvel: Iron Man
    {"label": "Tony & Pepper", "movie_id": "_NEEDS_MOVIE_ID_ironman", "character_id_a": "_NEEDS_ID_im_tony", "character_id_b": "_NEEDS_ID_im_pepper", "wiki_query": "Tony Stark Pepper Potts romance loyalty stark industries heart arc reactor"},
    {"label": "Tony & Obadiah", "movie_id": "_NEEDS_MOVIE_ID_ironman", "character_id_a": "_NEEDS_ID_im_tony", "character_id_b": "_NEEDS_ID_im_obadiah", "wiki_query": "Tony Stark Obadiah Stane betrayal mentor iron monger corporate rivalry"},

    # Marvel: The Avengers
    {"label": "Thor & Loki", "movie_id": "_NEEDS_MOVIE_ID_avengers", "character_id_a": "_NEEDS_ID_av_thor", "character_id_b": "_NEEDS_ID_av_loki", "wiki_query": "Thor Loki brothers conflict asgard new york invasion brotherhood betrayal"},
    {"label": "Steve & Natasha", "movie_id": "_NEEDS_MOVIE_ID_avengers", "character_id_a": "_NEEDS_ID_av_steve", "character_id_b": "_NEEDS_ID_av_natasha", "wiki_query": "Captain America Black Widow Steve Rogers Natasha Romanoff mutual trust soldier spy"},

    # Marvel: The Winter Soldier
    {"label": "Steve & Bucky", "movie_id": "_NEEDS_MOVIE_ID_wintersoldier", "character_id_a": "_NEEDS_ID_ws_steve", "character_id_b": "_NEEDS_ID_ws_bucky", "wiki_query": "Steve Rogers Bucky Barnes winter soldier till the end of the line friendship memory"},
    {"label": "Steve & Sam", "movie_id": "_NEEDS_MOVIE_ID_wintersoldier", "character_id_a": "_NEEDS_ID_ws_steve", "character_id_b": "_NEEDS_ID_ws_sam", "wiki_query": "Steve Rogers Sam Wilson falcon friendship veteran partnership loyalty"},
    {"label": "Steve & Alexander Pierce", "movie_id": "_NEEDS_MOVIE_ID_wintersoldier", "character_id_a": "_NEEDS_ID_ws_steve", "character_id_b": "_NEEDS_ID_ws_pierce", "wiki_query": "Steve Rogers Alexander Pierce hydra shield betrayal order vs freedom"},

    # Marvel: Guardians of the Galaxy
    {"label": "Peter Quill & Gamora", "movie_id": "_NEEDS_MOVIE_ID_gotg", "character_id_a": "_NEEDS_ID_gotg_quill", "character_id_b": "_NEEDS_ID_gotg_gamora", "wiki_query": "Peter Quill Gamora romance outlaw assassin walkman unspoken attraction"},
    {"label": "Peter Quill & Rocket", "movie_id": "_NEEDS_MOVIE_ID_gotg", "character_id_a": "_NEEDS_ID_gotg_quill", "character_id_b": "_NEEDS_ID_gotg_rocket", "wiki_query": "Peter Quill Rocket Raccoon bantering leadership camaraderie misfit alliance"},

    # Marvel: Civil War
    {"label": "Steve Rogers & Tony Stark", "movie_id": "_NEEDS_MOVIE_ID_civilwar", "character_id_a": "_NEEDS_ID_cw_steve", "character_id_b": "_NEEDS_ID_cw_tony", "wiki_query": "Captain America Iron Man civil war sokovia accords bucky betrayal clash"},
    {"label": "T'Challa & Helmut Zemo", "movie_id": "_NEEDS_MOVIE_ID_civilwar", "character_id_a": "_NEEDS_ID_cw_tchalla", "character_id_b": "_NEEDS_ID_cw_zemo", "wiki_query": "TChalla Helmut Zemo vengeance justice letting go of revenge siberia"},

    # Marvel: Thor Ragnarok
    {"label": "Thor & Loki", "movie_id": "_NEEDS_MOVIE_ID_ragnarok", "character_id_a": "_NEEDS_ID_rag_thor", "character_id_b": "_NEEDS_ID_rag_loki", "wiki_query": "Thor Loki ragnarok comedy brotherhood trickster reconciliation your savior is here"},
    {"label": "Thor & Hela", "movie_id": "_NEEDS_MOVIE_ID_ragnarok", "character_id_a": "_NEEDS_ID_rag_thor", "character_id_b": "_NEEDS_ID_rag_hela", "wiki_query": "Thor Hela goddess of death asgard rightful heir god of thunder lightning clash"},
    {"label": "Thor & Valkyrie", "movie_id": "_NEEDS_MOVIE_ID_ragnarok", "character_id_a": "_NEEDS_ID_rag_thor", "character_id_b": "_NEEDS_ID_rag_valkyrie", "wiki_query": "Thor Valkyrie sakaar warrior redemption asgardian heritage honor"},

    # Marvel: Black Panther
    {"label": "T'Challa & Killmonger", "movie_id": "_NEEDS_MOVIE_ID_blackpanther", "character_id_a": "_NEEDS_ID_bp_tchalla", "character_id_b": "_NEEDS_ID_bp_killmonger", "wiki_query": "TChalla Erik Killmonger wakanda throne cousins ideology oppression burial at sea"},
    {"label": "T'Challa & Nakia", "movie_id": "_NEEDS_MOVIE_ID_blackpanther", "character_id_a": "_NEEDS_ID_bp_tchalla", "character_id_b": "_NEEDS_ID_bp_nakia", "wiki_query": "TChalla Nakia romance wakanda outreach values global vision love"},

    # Marvel: Infinity War
    {"label": "Thanos & Gamora", "movie_id": "_NEEDS_MOVIE_ID_infinitywar", "character_id_a": "_NEEDS_ID_iw_thanos", "character_id_b": "_NEEDS_ID_iw_gamora", "wiki_query": "Thanos Gamora father daughter soul stone vormir sacrifice twisted love"},
    {"label": "Thanos & Tony Stark", "movie_id": "_NEEDS_MOVIE_ID_infinitywar", "character_id_a": "_NEEDS_ID_iw_thanos", "character_id_b": "_NEEDS_ID_iw_tony", "wiki_query": "Thanos Tony Stark titan battle cursed with knowledge respect all that for a drop of blood"},
    {"label": "Tony Stark & Stephen Strange", "movie_id": "_NEEDS_MOVIE_ID_infinitywar", "character_id_a": "_NEEDS_ID_iw_tony", "character_id_b": "_NEEDS_ID_iw_strange", "wiki_query": "Tony Stark Doctor Strange clashing egos science magic end game sacrifice"},

    # Marvel: Endgame
    {"label": "Tony Stark & Steve Rogers", "movie_id": "_NEEDS_MOVIE_ID_endgame", "character_id_a": "_NEEDS_ID_eg_tony", "character_id_b": "_NEEDS_ID_eg_steve", "wiki_query": "Tony Stark Steve Rogers reconciliation trust shield whatever it takes endgame"},
    {"label": "Nebula & Thanos", "movie_id": "_NEEDS_MOVIE_ID_endgame", "character_id_a": "_NEEDS_ID_eg_nebula", "character_id_b": "_NEEDS_ID_eg_thanos", "wiki_query": "Nebula Thanos abuse redemption cybernetic past self confrontation"},

    # Marvel: No Way Home
    {"label": "Peter Parker & Norman Osborn", "movie_id": "_NEEDS_MOVIE_ID_nowayhome", "character_id_a": "_NEEDS_ID_nwh_peter", "character_id_b": "_NEEDS_ID_nwh_goblin", "wiki_query": "Peter Parker Norman Osborn green goblin aunt may death moral choice cure vs revenge"},
    {"label": "Peter Parker & Doctor Strange", "movie_id": "_NEEDS_MOVIE_ID_nowayhome", "character_id_a": "_NEEDS_ID_nwh_peter", "character_id_b": "_NEEDS_ID_nwh_strange", "wiki_query": "Peter Parker Doctor Strange spell multiverse consequences forget me sacrifice"},

    # Marvel: Logan
    {"label": "Logan & Charles Xavier", "movie_id": "_NEEDS_MOVIE_ID_logan", "character_id_a": "_NEEDS_ID_logan_logan", "character_id_b": "_NEEDS_ID_logan_charles", "wiki_query": "Logan Charles Xavier aging dementia father son caregiver tragedy water tank"},
    {"label": "Logan & Laura", "movie_id": "_NEEDS_MOVIE_ID_logan", "character_id_a": "_NEEDS_ID_logan_logan", "character_id_b": "_NEEDS_ID_logan_laura", "wiki_query": "Logan Laura X23 reluctant father daughter mutant sanctuary sacrifice"},

    # Marvel: Days of Future Past
    {"label": "Charles Xavier & Magneto", "movie_id": "_NEEDS_MOVIE_ID_dofp", "character_id_a": "_NEEDS_ID_dofp_charles", "character_id_b": "_NEEDS_ID_dofp_magneto", "wiki_query": "Charles Xavier Erik Lehnsherr magneto days of future past plane argument hope vs cynical survival"},
    {"label": "Charles Xavier & Mystique", "movie_id": "_NEEDS_MOVIE_ID_dofp", "character_id_a": "_NEEDS_ID_dofp_charles", "character_id_b": "_NEEDS_ID_dofp_mystique", "wiki_query": "Charles Xavier Raven Mystique trask assassination choice free will humanity"},

    # DC: Batman Begins
    {"label": "Bruce Wayne & Ra's al Ghul", "movie_id": "_NEEDS_MOVIE_ID_batmanbegins", "character_id_a": "_NEEDS_ID_bb_bruce", "character_id_b": "_NEEDS_ID_bb_ras", "wiki_query": "Bruce Wayne Henri Ducard Ras al Ghul league of shadows theatricality justice execution train"},
    {"label": "Bruce Wayne & Rachel Dawes", "movie_id": "_NEEDS_MOVIE_ID_batmanbegins", "character_id_a": "_NEEDS_ID_bb_bruce", "character_id_b": "_NEEDS_ID_bb_rachel", "wiki_query": "Bruce Wayne Rachel Dawes childhood romance morality what defines us is what we do"},

    # DC: The Dark Knight Rises
    {"label": "Batman & Bane", "movie_id": "_NEEDS_MOVIE_ID_tldr", "character_id_a": "_NEEDS_ID_tldr_bruce", "character_id_b": "_NEEDS_ID_tldr_bane", "wiki_query": "Batman Bane sewer fight breaking the bat darkness league of shadows revolution"},
    {"label": "Batman & Catwoman", "movie_id": "_NEEDS_MOVIE_ID_tldr", "character_id_a": "_NEEDS_ID_tldr_bruce", "character_id_b": "_NEEDS_ID_tldr_selina", "wiki_query": "Batman Selina Kyle catwoman clean slate betrayal redemption partnership"},
    {"label": "Bruce Wayne & John Blake", "movie_id": "_NEEDS_MOVIE_ID_tldr", "character_id_a": "_NEEDS_ID_tldr_bruce", "character_id_b": "_NEEDS_ID_tldr_blake", "wiki_query": "Bruce Wayne John Blake robin mantle successor masked hero faith"},

    # DC: The Batman
    {"label": "Batman & The Riddler", "movie_id": "_NEEDS_MOVIE_ID_thebatman", "character_id_a": "_NEEDS_ID_tb_bruce", "character_id_b": "_NEEDS_ID_tb_riddler", "wiki_query": "The Batman Edward Nashton riddler arkham interrogation vengeance mirror vigilante"},
    {"label": "Batman & Catwoman", "movie_id": "_NEEDS_MOVIE_ID_thebatman", "character_id_a": "_NEEDS_ID_tb_bruce", "character_id_b": "_NEEDS_ID_tb_selina", "wiki_query": "Batman Selina Kyle catwoman noir romance sunrise motorcycle parting paths"},
    {"label": "Batman & James Gordon", "movie_id": "_NEEDS_MOVIE_ID_thebatman", "character_id_a": "_NEEDS_ID_tb_bruce", "character_id_b": "_NEEDS_ID_tb_gordon", "wiki_query": "The Batman James Gordon detective partnership crime scene trust corruption"},

    # DC: Joker
    {"label": "Arthur Fleck & Murray Franklin", "movie_id": "_NEEDS_MOVIE_ID_joker", "character_id_a": "_NEEDS_ID_jk_arthur", "character_id_b": "_NEEDS_ID_jk_murray", "wiki_query": "Arthur Fleck Murray Franklin talk show interview live broadcast television kill you get what you deserve"},
    {"label": "Arthur Fleck & Penny Fleck", "movie_id": "_NEEDS_MOVIE_ID_joker", "character_id_a": "_NEEDS_ID_jk_arthur", "character_id_b": "_NEEDS_ID_jk_penny", "wiki_query": "Arthur Fleck Penny Fleck mother son adoption abuse revelation hospital pillow"},

    # DC: Man of Steel
    {"label": "Clark Kent & General Zod", "movie_id": "_NEEDS_MOVIE_ID_manofsteel", "character_id_a": "_NEEDS_ID_mos_clark", "character_id_b": "_NEEDS_ID_mos_zod", "wiki_query": "Clark Kent Superman General Zod krypton earth destruction final choice neck snap tragedy"},
    {"label": "Clark Kent & Lois Lane", "movie_id": "_NEEDS_MOVIE_ID_manofsteel", "character_id_a": "_NEEDS_ID_mos_clark", "character_id_b": "_NEEDS_ID_mos_lois", "wiki_query": "Clark Kent Lois Lane first contact arctic trust Pulitzer romance secret"},
    {"label": "Clark Kent & Jor-El", "movie_id": "_NEEDS_MOVIE_ID_manofsteel", "character_id_a": "_NEEDS_ID_mos_clark", "character_id_b": "_NEEDS_ID_mos_jorel", "wiki_query": "Clark Kent Jor-El hologram father son kryptonian legacy give the people of earth an ideal to strive towards"},

    # DC: BvS
    {"label": "Batman & Superman", "movie_id": "_NEEDS_MOVIE_ID_bvs", "character_id_a": "_NEEDS_ID_bvs_bruce", "character_id_b": "_NEEDS_ID_bvs_clark", "wiki_query": "Batman Superman dawn of justice gladiatorial match power god vs man martha redemption"},
    {"label": "Lex Luthor & Superman", "movie_id": "_NEEDS_MOVIE_ID_bvs", "character_id_a": "_NEEDS_ID_bvs_lex", "character_id_b": "_NEEDS_ID_bvs_clark", "wiki_query": "Lex Luthor Superman rooftop manipulation god cannot be all powerful and all good"},
    {"label": "Batman & Wonder Woman", "movie_id": "_NEEDS_MOVIE_ID_bvs", "character_id_a": "_NEEDS_ID_bvs_bruce", "character_id_b": "_NEEDS_ID_bvs_diana", "wiki_query": "Bruce Wayne Diana Prince museum sword shield alliance recruitment"},

    # DC: Wonder Woman
    {"label": "Diana Prince & Steve Trevor", "movie_id": "_NEEDS_MOVIE_ID_wonderwoman", "character_id_a": "_NEEDS_ID_ww_diana", "character_id_b": "_NEEDS_ID_ww_steve", "wiki_query": "Diana Prince Steve Trevor no mans land airplane sacrifice love I can save today you can save the world"},
    {"label": "Diana Prince & Ares", "movie_id": "_NEEDS_MOVIE_ID_wonderwoman", "character_id_a": "_NEEDS_ID_ww_diana", "character_id_b": "_NEEDS_ID_ww_ares", "wiki_query": "Diana Prince Ares god of war mankind innate evil belief in love climax"},

    # DC: Watchmen
    {"label": "Rorschach & Nite Owl", "movie_id": "_NEEDS_MOVIE_ID_watchmen", "character_id_a": "_NEEDS_ID_wm_rorschach", "character_id_b": "_NEEDS_ID_wm_dan", "wiki_query": "Rorschach Dan Dreiberg nite owl vigilante brotherhood investigation prison break"},
    {"label": "Dr. Manhattan & Ozymandias", "movie_id": "_NEEDS_MOVIE_ID_watchmen", "character_id_a": "_NEEDS_ID_wm_manhattan", "character_id_b": "_NEEDS_ID_wm_veidt", "wiki_query": "Dr Manhattan Adrian Veidt ozymandias karnak tachyon utopia pragmatic peace"},
    {"label": "Rorschach & Ozymandias", "movie_id": "_NEEDS_MOVIE_ID_watchmen", "character_id_a": "_NEEDS_ID_wm_rorschach", "character_id_b": "_NEEDS_ID_wm_veidt", "wiki_query": "Rorschach Adrian Veidt never compromise even in the face of armageddon death in snow"},

    # DC: V for Vendetta
    {"label": "V & Evey Hammond", "movie_id": "_NEEDS_MOVIE_ID_vforvendetta", "character_id_a": "_NEEDS_ID_v_v", "character_id_b": "_NEEDS_ID_v_evey", "wiki_query": "V Evey Hammond imprisonment liberation rain rooftop transformation freedom idea"},
    {"label": "V & Inspector Finch", "movie_id": "_NEEDS_MOVIE_ID_vforvendetta", "character_id_a": "_NEEDS_ID_v_v", "character_id_b": "_NEEDS_ID_v_finch", "wiki_query": "V Chief Inspector Finch larkhill investigation truth conscience underground station confrontation"},
]


def main():
    with open(BATCH_FILE, "r", encoding="utf-8") as f:
        batch = json.load(f)

    existing_movie_titles = {m["title"].lower(): m for m in batch.get("movies", [])}
    existing_char_keys = {(c["movie_title"].lower(), c["name"].lower()): c for c in batch.get("characters", [])}
    existing_rel_keys = {(r.get("movie_id"), r.get("character_id_a"), r.get("character_id_b")) for r in batch.get("relationships", [])}

    added_movies = 0
    for m in NEW_MOVIES:
        if m["title"].lower() not in existing_movie_titles:
            batch.setdefault("movies", []).append(m)
            existing_movie_titles[m["title"].lower()] = m
            added_movies += 1

    added_chars = 0
    for c in NEW_CHARACTERS:
        key = (c["movie_title"].lower(), c["name"].lower())
        if key not in existing_char_keys:
            batch.setdefault("characters", []).append(c)
            existing_char_keys[key] = c
            added_chars += 1

    added_rels = 0
    for r in NEW_RELATIONSHIPS:
        key = (r.get("movie_id"), r.get("character_id_a"), r.get("character_id_b"))
        rev_key = (r.get("movie_id"), r.get("character_id_b"), r.get("character_id_a"))
        if key not in existing_rel_keys and rev_key not in existing_rel_keys:
            batch.setdefault("relationships", []).append(r)
            existing_rel_keys.add(key)
            added_rels += 1

    with open(BATCH_FILE, "w", encoding="utf-8") as f:
        json.dump(batch, f, indent=2, ensure_ascii=False)

    print(f"Batch file updated successfully!")
    print(f"Added: {added_movies} movies, {added_chars} characters, {added_rels} relationships.")
    print(f"Total in batch: {len(batch['movies'])} movies, {len(batch['characters'])} characters, {len(batch['relationships'])} relationships, {len(batch['songs'])} songs.")


if __name__ == "__main__":
    main()
