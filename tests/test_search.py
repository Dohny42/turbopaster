from turbopaster.search import filter_snippet_names


def test_filter_snippet_names_matches_case_insensitive_substrings() -> None:
    snippets = {
        "My Email": "email text",
        "email footer": "footer text",
        "pin": "1234",
    }

    assert filter_snippet_names(snippets, "EMAIL") == ["email footer", "My Email"]


def test_filter_snippet_names_returns_all_names_for_empty_query() -> None:
    snippets = {"zeta": "z", "Alpha": "a", "beta": "b"}

    assert filter_snippet_names(snippets, "") == ["Alpha", "beta", "zeta"]


def test_filter_snippet_names_returns_no_names_without_match() -> None:
    snippets = {"email": "email text"}

    assert filter_snippet_names(snippets, "signature") == []


def test_filter_snippet_names_sorts_results_alphabetically() -> None:
    snippets = {"zeta-email": "z", "Alpha-email": "a", "beta-email": "b"}

    assert filter_snippet_names(snippets, "email") == [
        "Alpha-email",
        "beta-email",
        "zeta-email",
    ]
