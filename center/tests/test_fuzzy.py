# SPDX-License-Identifier: GPL-3.0-or-later
from arctiva_center.core import fuzzy


def test_tokens_and_squash_ignore_separators_case_and_accents():
    assert fuzzy.tokens("Claude-Code_v2.0  Ñandú") == ["claude", "code", "v2", "0", "nandu"]
    assert fuzzy.squash("claude code") == fuzzy.squash("claude-code") == fuzzy.squash("CLAUDE.Code") == "claudecode"


def test_distance_counts_transpositions_as_one():
    assert fuzzy.distance("claude", "cluade") == 1
    assert fuzzy.distance("claude", "claudee") == 1 and fuzzy.distance("claude", "claud") == 1
    assert fuzzy.distance("abc", "xyz") == 3 and fuzzy.distance("", "ab") == 2 and fuzzy.distance("a", "a") == 0


def test_budget_grows_with_length():
    assert [fuzzy.budget(n) for n in (1, 3, 4, 7, 8, 12)] == [0, 0, 1, 1, 2, 2]


def test_closeness_and_fuzzy_total():
    assert fuzzy.closeness("clau", "claude") == 0                    # lo escrito a medias
    assert fuzzy.closeness("cluade", "claude") == 1
    assert fuzzy.closeness("kde", "kate") is None                     # palabras cortas: sin erratas
    assert fuzzy.closeness("firefix", "firefox") == 1
    assert fuzzy.fuzzy_total(["cluade", "desktop"], {"claude", "desktop"}) == 1
    assert fuzzy.fuzzy_total(["cluade", "zzzz"], {"claude", "desktop"}) is None
