import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import logtime.logtime as lt
import pytest


# ---------------------------------------------------------------------------
# parse_line
# ---------------------------------------------------------------------------


def test_parse_line_full() -> None:
    line = "08:00 12345 Fix bug"
    parsed = lt.parse_line(line)
    assert parsed == ("08:00", "12345", "Fix bug")


def test_parse_line_no_task() -> None:
    line = "09:15 Some note"
    parsed = lt.parse_line(line)
    assert parsed == ("09:15", None, "Some note")


def test_parse_line_single_digit_hour() -> None:
    line = "8:00 12345 Short hour"
    parsed = lt.parse_line(line)
    assert parsed == ("8:00", "12345", "Short hour")


def test_parse_line_no_description() -> None:
    line = "10:00 12345"
    parsed = lt.parse_line(line)
    assert parsed is not None
    time_str, task_id, desc = parsed
    assert time_str == "10:00"
    assert task_id == "12345"
    assert desc == ""


def test_parse_line_time_only_returns_none() -> None:
    # The regex requires whitespace after the time token, so bare "HH:MM" doesn't match.
    assert lt.parse_line("10:00") is None


def test_parse_line_leading_whitespace() -> None:
    line = "  08:30 12345 Indented"
    parsed = lt.parse_line(line)
    assert parsed is not None
    assert parsed[0] == "08:30"


def test_parse_line_no_match_returns_none() -> None:
    assert lt.parse_line("") is None
    assert lt.parse_line("Some random text") is None
    assert lt.parse_line("# Header line") is None


def test_parse_line_hash_desc() -> None:
    """Lines with '#' prefix in description are valid — used for free-time tracking."""
    line = "12:00 #lunch"
    parsed = lt.parse_line(line)
    assert parsed == ("12:00", None, "#lunch")


# ---------------------------------------------------------------------------
# get_path
# ---------------------------------------------------------------------------


def test_get_path_format() -> None:
    date = datetime(2026, 2, 21, tzinfo=lt.LOG_TZ)
    path = lt.get_path(date)
    assert path.name == "2026-02-21 SA.md"
    assert "2026" in str(path)
    assert "02" in str(path)


def test_get_path_weekday_names() -> None:
    # Monday = 0 = MO
    monday = datetime(2026, 2, 23, tzinfo=lt.LOG_TZ)
    assert lt.get_path(monday).name == "2026-02-23 MO.md"

    # Friday = 4 = FR
    friday = datetime(2026, 2, 27, tzinfo=lt.LOG_TZ)
    assert lt.get_path(friday).name == "2026-02-27 FR.md"


# ---------------------------------------------------------------------------
# get_lines
# ---------------------------------------------------------------------------


def test_get_lines_reads_non_empty_lines() -> None:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as fh:
        fh.write("08:00 start\n\n09:00 end\n")
        tmp_path = Path(fh.name)

    lines = lt.get_lines(tmp_path)
    assert lines == ["08:00 start", "09:00 end"]
    tmp_path.unlink()


def test_get_lines_file_not_found() -> None:
    with pytest.raises(FileNotFoundError):
        lt.get_lines(Path("/nonexistent/path/file.md"))


def test_get_lines_strips_trailing_newline() -> None:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as fh:
        fh.write("08:00 task\n")
        tmp_path = Path(fh.name)

    lines = lt.get_lines(tmp_path)
    assert lines == ["08:00 task"]
    tmp_path.unlink()


# ---------------------------------------------------------------------------
# is_already_parsed
# ---------------------------------------------------------------------------


def test_is_already_parsed_true() -> None:
    assert lt.is_already_parsed(["08:00 start", "already parsed"]) is True


def test_is_already_parsed_with_whitespace() -> None:
    assert lt.is_already_parsed(["08:00 start", "  already parsed  "]) is True


def test_is_already_parsed_false() -> None:
    assert lt.is_already_parsed(["08:00 start", "09:00 end"]) is False


def test_is_already_parsed_empty() -> None:
    assert lt.is_already_parsed([]) is False


# ---------------------------------------------------------------------------
# get_timestamps
# ---------------------------------------------------------------------------


def test_get_timestamps_and_deltas() -> None:
    today = datetime(2026, 2, 21, tzinfo=lt.LOG_TZ)
    lines = ["08:00 start", "09:30 end"]
    timestamps = lt.get_timestamps(today, lines)
    assert len(timestamps) == 2
    assert timestamps[0].hour == 8
    assert timestamps[0].minute == 0
    # deltas
    deltas = lt.get_deltas(timestamps)
    assert len(deltas) == 1
    assert int(deltas[0].total_seconds()) == 90 * 60


def test_get_timestamps_skips_non_matching_lines() -> None:
    today = datetime(2026, 2, 21, tzinfo=lt.LOG_TZ)
    lines = ["08:00 start", "Summary:", "09:00 end"]
    timestamps = lt.get_timestamps(today, lines)
    assert len(timestamps) == 2


def test_get_timestamps_single_line() -> None:
    today = datetime(2026, 2, 21, tzinfo=lt.LOG_TZ)
    timestamps = lt.get_timestamps(today, ["08:00 only"])
    assert len(timestamps) == 1
    assert timestamps[0].hour == 8


def test_get_timestamps_timezone() -> None:
    today = datetime(2026, 2, 21, tzinfo=lt.LOG_TZ)
    timestamps = lt.get_timestamps(today, ["10:15 task"])
    assert timestamps[0].tzinfo == lt.LOG_TZ
    assert timestamps[0].minute == 15


# ---------------------------------------------------------------------------
# get_deltas
# ---------------------------------------------------------------------------


def test_get_deltas_empty() -> None:
    assert lt.get_deltas([]) == []


def test_get_deltas_single_timestamp() -> None:
    ts = datetime(2026, 2, 21, 8, 0, tzinfo=lt.LOG_TZ)
    assert lt.get_deltas([ts]) == []


def test_get_deltas_multiple() -> None:
    ts1 = datetime(2026, 2, 21, 8, 0, tzinfo=lt.LOG_TZ)
    ts2 = datetime(2026, 2, 21, 9, 0, tzinfo=lt.LOG_TZ)
    ts3 = datetime(2026, 2, 21, 10, 30, tzinfo=lt.LOG_TZ)
    deltas = lt.get_deltas([ts1, ts2, ts3])
    assert len(deltas) == 2
    assert deltas[0] == timedelta(hours=1)
    assert deltas[1] == timedelta(hours=1, minutes=30)


# ---------------------------------------------------------------------------
# get_tasks_results
# ---------------------------------------------------------------------------


def test_get_tasks_results() -> None:
    today = datetime(2026, 2, 21, tzinfo=lt.LOG_TZ)
    lines = ["08:00 12345 Task A", "09:00 12345 Task A"]
    timestamps = lt.get_timestamps(today, lines)
    deltas = lt.get_deltas(timestamps)
    results = lt.get_tasks_results(deltas, lines)
    assert len(results) == 1
    tr = results[0]
    assert tr.task_id == "12345"
    assert tr.desc == "Task A"
    assert tr.delta_seconds == 3600


def test_get_tasks_results_no_task_id() -> None:
    today = datetime(2026, 2, 21, tzinfo=lt.LOG_TZ)
    lines = ["08:00 #lunch", "08:30 back"]
    timestamps = lt.get_timestamps(today, lines)
    deltas = lt.get_deltas(timestamps)
    results = lt.get_tasks_results(deltas, lines)
    assert len(results) == 1
    assert results[0].task_id is None
    assert results[0].desc == "#lunch"


def test_get_tasks_results_last_line_skipped() -> None:
    """The last line has no following delta and must be skipped."""
    today = datetime(2026, 2, 21, tzinfo=lt.LOG_TZ)
    lines = ["08:00 12345 First", "09:00 12345 Second", "10:00 end"]
    timestamps = lt.get_timestamps(today, lines)
    deltas = lt.get_deltas(timestamps)
    results = lt.get_tasks_results(deltas, lines)
    # Only first two lines produce results (last has no delta)
    assert len(results) == 2


def test_get_tasks_results_unrecognized_lines_do_not_raise() -> None:
    """Non-matching lines (e.g. headers) should be silently skipped without error."""
    today = datetime(2026, 2, 21, tzinfo=lt.LOG_TZ)
    lines = ["08:00 12345 Start", "Summary:", "09:00 end"]
    timestamps = lt.get_timestamps(today, lines)
    deltas = lt.get_deltas(timestamps)
    results = lt.get_tasks_results(deltas, lines)
    # "08:00 12345 Start" is the only line that produces a result (i=0 uses delta[0])
    assert len(results) == 1
    assert results[0].task_id == "12345"


# ---------------------------------------------------------------------------
# group_tasks
# ---------------------------------------------------------------------------


def test_group_tasks_empty() -> None:
    assert lt.group_tasks([]) == {}


def test_group_tasks_single() -> None:
    tasks = [lt.TaskResult(task_id="12345", delta_seconds=3600, desc="Coding")]
    grouped = lt.group_tasks(tasks)
    assert "12345 Coding" in grouped
    entry = grouped["12345 Coding"]
    assert entry["task_id"] == "12345"
    assert entry["task_total_mins"] == 60
    assert entry["task_total_hours"] == 1
    assert entry["task_total_rest"] == 0
    assert entry["rounded_hours"] == 1.0


def test_group_tasks_aggregates_same_key() -> None:
    tasks = [
        lt.TaskResult(task_id="12345", delta_seconds=1800, desc="Coding"),
        lt.TaskResult(task_id="12345", delta_seconds=1800, desc="Coding"),
    ]
    grouped = lt.group_tasks(tasks)
    assert len(grouped) == 1
    entry = grouped["12345 Coding"]
    assert entry["task_total_mins"] == 60


def test_group_tasks_no_task_id() -> None:
    tasks = [lt.TaskResult(task_id=None, delta_seconds=1800, desc="#lunch")]
    grouped = lt.group_tasks(tasks)
    assert "#lunch" in grouped
    assert "task_id" not in grouped["#lunch"]


def test_group_tasks_hash_prefix_is_keyed_by_desc() -> None:
    tasks = [lt.TaskResult(task_id=None, delta_seconds=900, desc="#break")]
    grouped = lt.group_tasks(tasks)
    assert "#break" in grouped


def test_group_tasks_rounded_hours() -> None:
    # 50 minutes → 0.75h (nearest quarter)
    tasks = [lt.TaskResult(task_id="11111", delta_seconds=50 * 60, desc="Work")]
    grouped = lt.group_tasks(tasks)
    assert grouped["11111 Work"]["rounded_hours"] == 0.75


# ---------------------------------------------------------------------------
# compute_totals
# ---------------------------------------------------------------------------


def test_compute_totals_work_only() -> None:
    tasks = [
        lt.TaskResult(task_id="12345", delta_seconds=3600, desc="Dev"),
        lt.TaskResult(task_id="99999", delta_seconds=1800, desc="Review"),
    ]
    work, free = lt.compute_totals(tasks)
    assert work == 5400
    assert free == 0


def test_compute_totals_free_only() -> None:
    tasks = [lt.TaskResult(task_id=None, delta_seconds=1800, desc="#lunch")]
    work, free = lt.compute_totals(tasks)
    assert work == 0
    assert free == 1800


def test_compute_totals_mixed() -> None:
    tasks = [
        lt.TaskResult(task_id="12345", delta_seconds=3600, desc="Dev"),
        lt.TaskResult(task_id=None, delta_seconds=900, desc="#break"),
    ]
    work, free = lt.compute_totals(tasks)
    assert work == 3600
    assert free == 900


def test_compute_totals_empty() -> None:
    assert lt.compute_totals([]) == (0, 0)


# ---------------------------------------------------------------------------
# apply_defaults
# ---------------------------------------------------------------------------


def test_apply_defaults_matches() -> None:
    grouped: lt.Grouped = {
        "Standup": {"delta": 15, "desc": {"Standup"}, "task_total_mins": 15},
    }
    lt.apply_defaults(grouped, {"Standup": "99999"})
    assert grouped["Standup"]["task_id"] == "99999"


def test_apply_defaults_no_match() -> None:
    grouped: lt.Grouped = {
        "Coding": {"delta": 60, "desc": {"Coding"}, "task_total_mins": 60},
    }
    lt.apply_defaults(grouped, {"Standup": "99999"})
    assert "task_id" not in grouped["Coding"]


def test_apply_defaults_prefix_match() -> None:
    grouped: lt.Grouped = {
        "Standup daily call": {"delta": 15, "desc": {"Standup daily call"}, "task_total_mins": 15},
    }
    lt.apply_defaults(grouped, {"Standup": "99999"})
    assert grouped["Standup daily call"]["task_id"] == "99999"


# ---------------------------------------------------------------------------
# append_result
# ---------------------------------------------------------------------------


def test_append_result_writes_summary() -> None:
    tasks = [
        lt.TaskResult(task_id="12345", delta_seconds=3600, desc="Dev"),
        lt.TaskResult(task_id=None, delta_seconds=900, desc="#break"),
    ]
    grouped = lt.group_tasks(tasks)
    work, free = lt.compute_totals(tasks)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as fh:
        fh.write("08:00 12345 Dev\n")
        tmp_path = Path(fh.name)

    lt.append_result(tmp_path, grouped, work, free)

    content = tmp_path.read_text(encoding="utf-8")
    assert "Summary:" in content
    assert "already parsed" in content
    assert "total:" in content
    tmp_path.unlink()


def test_append_result_ends_with_already_parsed() -> None:
    grouped = lt.group_tasks([lt.TaskResult(task_id="12345", delta_seconds=3600, desc="Task")])

    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as fh:
        tmp_path = Path(fh.name)

    lt.append_result(tmp_path, grouped, 3600, 0)
    content = tmp_path.read_text(encoding="utf-8")
    assert content.rstrip().endswith("already parsed")
    tmp_path.unlink()


# ---------------------------------------------------------------------------
# minutes_to_rounded_decimal_hours
# ---------------------------------------------------------------------------


def test_minutes_to_rounded_decimal_hours() -> None:
    assert lt.minutes_to_rounded_decimal_hours(0) == 0
    assert lt.minutes_to_rounded_decimal_hours(15) == 0.25
    assert lt.minutes_to_rounded_decimal_hours(30) == 0.5
    assert lt.minutes_to_rounded_decimal_hours(45) == 0.75
    assert lt.minutes_to_rounded_decimal_hours(60) == 1.0


def test_minutes_to_rounded_decimal_hours_rounding() -> None:
    # 7 min → 0.0h (nearest quarter)
    assert lt.minutes_to_rounded_decimal_hours(7) == 0.0
    # 8 min → 0.25h
    assert lt.minutes_to_rounded_decimal_hours(8) == 0.25
    # 22 min → 0.25h
    assert lt.minutes_to_rounded_decimal_hours(22) == 0.25
    # 23 min → 0.5h (rounds up)
    assert lt.minutes_to_rounded_decimal_hours(23) == 0.5
    # 90 min → 1.5h
    assert lt.minutes_to_rounded_decimal_hours(90) == 1.5
