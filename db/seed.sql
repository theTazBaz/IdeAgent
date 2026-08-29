-- =============================================================================
-- IdeAgent — Seed Data (5 test entities, no embeddings)
-- Purpose: verify schema + FK constraints work before running enrichment pipeline
-- Embeddings are NULL here — they get populated by the enrichment script
-- =============================================================================

-- Fixed UUIDs so FK references work across inserts
-- Movie: The Dark Knight
-- Characters: Bruce Wayne, The Joker
-- Relationship: Batman & Joker dynamic
-- Songs: 2 test songs


-- -----------------------------------------------------------------------------
-- MOVIE
-- -----------------------------------------------------------------------------
INSERT INTO movies (id, title, description, core_emotional_logic)
VALUES (
    '11111111-1111-1111-1111-111111111111',
    'The Dark Knight',
    'A crime thriller in which Batman faces the Joker, a criminal mastermind who seeks to expose the chaos beneath Gotham''s order. The film explores the tension between justice and moral compromise.',
    'A hero must decide how far to bend his own rules to stop someone who breaks all of them.'
);


-- -----------------------------------------------------------------------------
-- CHARACTERS  (individual traits only — no relational logic)
-- -----------------------------------------------------------------------------
INSERT INTO characters (id, movie_id, name, description, core_emotional_logic)
VALUES (
    '22222222-2222-2222-2222-222222222222',
    '11111111-1111-1111-1111-111111111111',
    'Bruce Wayne / Batman',
    'A billionaire vigilante operating outside the law to protect Gotham. Disciplined, principled, and haunted by loss, he holds himself to a strict moral code — he will not kill. He carries the weight of his city''s safety as a personal burden.',
    'Chooses to bear an impossible burden alone rather than let others carry the cost of his mission.'
);

INSERT INTO characters (id, movie_id, name, description, core_emotional_logic)
VALUES (
    '33333333-3333-3333-3333-333333333333',
    '11111111-1111-1111-1111-111111111111',
    'The Joker',
    'An agent of chaos with no clear origin or motive beyond disruption. Intelligent and theatrical, he believes society''s order is a fragile lie and takes pleasure in exposing it. He operates without fear because he has nothing to lose.',
    'Destroys systems and rules to prove that beneath civilization, everyone is just as chaotic as he is.'
);


-- -----------------------------------------------------------------------------
-- RELATIONSHIP  (relational logic between Batman and Joker)
-- -----------------------------------------------------------------------------
INSERT INTO relationships (id, movie_id, character_id_a, character_id_b, label, description, core_emotional_logic)
VALUES (
    '44444444-4444-4444-4444-444444444444',
    '11111111-1111-1111-1111-111111111111',
    '22222222-2222-2222-2222-222222222222',
    '33333333-3333-3333-3333-333333333333',
    'Batman & Joker',
    'The Joker deliberately engineers situations to force Batman to break his one rule — do not kill. Batman''s existence gives the Joker purpose: he is the immovable order to the Joker''s unstoppable chaos. Each defines and sustains the other.',
    'Two forces that can only exist in opposition: one holds the line, the other exists to erase it.'
);


-- -----------------------------------------------------------------------------
-- SONGS
-- -----------------------------------------------------------------------------
INSERT INTO songs (id, title, artist, description, core_emotional_logic)
VALUES (
    '55555555-5555-5555-5555-555555555555',
    'Believer',
    'Imagine Dragons',
    'An anthemic rock track about finding strength through pain and adversity. The narrator reframes suffering as the source of their identity and power rather than something to escape.',
    'Pain is not something to survive — it is the thing that makes you who you are.'
);

INSERT INTO songs (id, title, artist, description, core_emotional_logic)
VALUES (
    '66666666-6666-6666-6666-666666666666',
    'Blinding Lights',
    'The Weeknd',
    'A synth-pop track driven by desperation and longing. The narrator is lost and reckless, needing someone desperately but unable to reach them, moving through the night in a state of emotional exposure.',
    'Racing toward someone in a moment of total vulnerability, stripped of all pretense.'
);


-- -----------------------------------------------------------------------------
-- Quick sanity check — run this after seeding to verify FK integrity
-- -----------------------------------------------------------------------------
-- SELECT c.name, m.title
-- FROM characters c
-- JOIN movies m ON c.movie_id = m.id;

-- SELECT r.label, ca.name AS char_a, cb.name AS char_b
-- FROM relationships r
-- JOIN characters ca ON r.character_id_a = ca.id
-- JOIN characters cb ON r.character_id_b = cb.id;
