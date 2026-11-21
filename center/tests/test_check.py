# SPDX-License-Identifier: GPL-3.0-or-later
from arctiva_center import check
from arctiva_center.core.updates import Update


def test_only_new_updates_notify():
    current = [Update("linux", "1", "2"), Update("mesa", "1", "3")]
    assert check.new_since_last_notice(current, []) == ["linux 2", "mesa 3"]
    assert check.new_since_last_notice(current, ["linux 2", "mesa 3"]) == []
    # Una versión más nueva del mismo paquete vuelve a avisar.
    assert check.new_since_last_notice([Update("mesa", "1", "4")], ["mesa 3"]) == ["mesa 4"]


def test_texts_follow_language():
    assert check.texts({"LANGUAGE": "ca:es", "LANG": "es_ES.UTF-8"}) == check.TEXTS["ca"]
    assert check.texts({"LANG": "es_ES.UTF-8"}) == check.TEXTS["es"]
    assert check.texts({"LANG": "de_DE.UTF-8"}) == check.TEXTS["en"]
    assert check.texts({}) == check.TEXTS["en"]
    for title, body, action in check.TEXTS.values():
        assert "{n}" in body and title and action
