import json

from ha_theme_kit.inventory.local_theme_selection import LocalThemeSelection

ANTHROPIC_DARK = {"theme": "Anthropic", "dark": True}
DEFAULT_LIGHT = {"theme": "default", "dark": False}


def command(request_id: int, command_type: str, **fields) -> str:
    return json.dumps({"id": request_id, "type": f"frontend/{command_type}", **fields})


def event(request_id: int, value) -> str:
    return json.dumps({"id": request_id, "type": "event", "event": {"value": value}})


def test_theme_writes_are_answered_in_the_page_and_pushed_to_its_subscriptions():
    selection = LocalThemeSelection()
    tracked: dict[int, str | None] = {}
    subscribe = command(3, "subscribe_user_data", key="theme")
    assert selection.handle_page_message(subscribe, tracked) == (subscribe, [])

    forwarded, replies = selection.handle_page_message(
        command(4, "set_user_data", key="theme", value=ANTHROPIC_DARK), tracked
    )

    assert forwarded is None
    assert [json.loads(reply) for reply in replies] == [
        {"id": 4, "type": "result", "success": True, "result": None},
        {"id": 3, "type": "event", "event": {"value": ANTHROPIC_DARK}},
    ]
    assert selection.selection == ANTHROPIC_DARK


def test_selection_pushed_by_other_sessions_is_replaced_with_the_local_one():
    selection = LocalThemeSelection()
    selection.selection = DEFAULT_LIGHT
    tracked: dict[int, str | None] = {3: "theme", 5: None}
    coalesced = json.dumps(
        [
            json.loads(event(3, ANTHROPIC_DARK)),
            json.loads(event(5, {"theme": ANTHROPIC_DARK, "sidebar": {"order": []}})),
            json.loads(event(9, {"unrelated": True})),
        ]
    )

    rewritten = json.loads(selection.handle_server_message(coalesced, tracked))

    assert [reply["event"]["value"] for reply in rewritten] == [
        DEFAULT_LIGHT,
        {"theme": DEFAULT_LIGHT, "sidebar": {"order": []}},
        {"unrelated": True},
    ]


def test_theme_reads_are_answered_locally_once_a_theme_is_selected():
    selection = LocalThemeSelection()
    tracked: dict[int, str | None] = {}
    read = command(6, "get_user_data", key="theme")
    assert selection.handle_page_message(read, tracked) == (read, [])

    selection.selection = DEFAULT_LIGHT
    forwarded, replies = selection.handle_page_message(read, tracked)

    assert forwarded is None
    assert json.loads(replies[0])["result"] == {"value": DEFAULT_LIGHT}


def test_whole_profile_reads_carry_the_local_theme_and_are_forgotten_after_the_result():
    selection = LocalThemeSelection()
    selection.selection = ANTHROPIC_DARK
    tracked: dict[int, str | None] = {}
    selection.handle_page_message(command(7, "get_user_data"), tracked)
    result = json.dumps(
        {"id": 7, "type": "result", "success": True, "result": {"value": {"theme": None}}}
    )

    rewritten = json.loads(selection.handle_server_message(result, tracked))

    assert rewritten["result"]["value"] == {"theme": ANTHROPIC_DARK}
    assert tracked == {}


def test_other_messages_pass_through_untouched():
    selection = LocalThemeSelection()
    selection.selection = ANTHROPIC_DARK
    tracked: dict[int, str | None] = {3: "theme"}
    other_key = command(8, "set_user_data", key="sidebar", value={})
    subscribe_result = json.dumps({"id": 3, "type": "result", "success": True, "result": None})

    assert selection.handle_page_message(other_key, tracked) == (other_key, [])
    assert selection.handle_page_message(b"\x00", tracked) == (b"\x00", [])
    assert selection.handle_server_message(subscribe_result, tracked) == subscribe_result
    assert selection.handle_server_message(event(9, {}), tracked) == event(9, {})


def test_persisting_hands_the_selection_back_to_the_server():
    selection = LocalThemeSelection()
    selection.selection = ANTHROPIC_DARK
    selection.persist = True
    write = command(4, "set_user_data", key="theme", value={"theme": "Anthropic"})
    pushed = event(3, DEFAULT_LIGHT)

    assert selection.handle_page_message(write, {}) == (write, [])
    assert selection.handle_server_message(pushed, {3: "theme"}) == pushed
