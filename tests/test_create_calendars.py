import importlib.util
import os
import sys
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture(scope="module")
def create_calendars():
    """Load create-calendars.py as a module with mocked MongoDB."""
    module_path = os.path.join(REPO_ROOT, "create-calendars.py")
    mock_client = MagicMock()
    with patch("pymongo.MongoClient", return_value=mock_client):
        spec = importlib.util.spec_from_file_location("create_calendars", module_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules["create_calendars"] = module
        spec.loader.exec_module(module)
    return module


@pytest.fixture
def mock_div_db(create_calendars):
    """Replace div_db with a fresh MagicMock for each test."""
    mock = MagicMock()
    create_calendars.div_db = mock
    return mock


# ── Helpers ──────────────────────────────────────────────────────────────────

def _ics_text(tmp_path, filename="all.ics"):
    return (tmp_path / filename).read_text(encoding="utf-8")


def _make_event(id=1, title="Test Event", start=None, end=None, location=None,
                meta=None, description_de=None, description_en=None):
    start = start or datetime(2024, 6, 1, 10, 0, 0)
    event = {"id": id, "title": title, "start": start}
    if end is not None:
        event["end"] = end
    if location is not None:
        event["location"] = location
    if meta is not None:
        event["meta"] = meta
    if description_de is not None:
        event["description_de"] = description_de
    if description_en is not None:
        event["description_en"] = description_en
    return event


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestGetOrganizersJson:
    def test_loads_and_returns_dict(self, create_calendars, monkeypatch):
        monkeypatch.chdir(REPO_ROOT)
        result = create_calendars.get_organizers_json()
        assert isinstance(result, dict)

    def test_contains_jules_with_jl_code(self, create_calendars, monkeypatch):
        monkeypatch.chdir(REPO_ROOT)
        result = create_calendars.get_organizers_json()
        assert result["JuLes"] == "jl"

    def test_contains_all_18_organizers(self, create_calendars, monkeypatch):
        monkeypatch.chdir(REPO_ROOT)
        result = create_calendars.get_organizers_json()
        assert len(result) == 18

    def test_file_not_found_propagates(self, create_calendars, monkeypatch, tmp_path):
        monkeypatch.chdir(tmp_path)  # no organizers.json here
        with pytest.raises(FileNotFoundError):
            create_calendars.get_organizers_json()


class TestCheckOrganizers:
    def test_no_output_when_all_organizers_present(self, create_calendars, mock_div_db, capsys):
        mock_div_db.find.return_value = [{"id": 1, "title": "JuLes"}]
        with patch.object(create_calendars, "get_organizers_json",
                          return_value={"JuLes": "jl", "Wilma": "wi"}):
            create_calendars.check_organizers()
        assert capsys.readouterr().out == ""

    def test_prints_warning_for_unknown_organizer(self, create_calendars, mock_div_db, capsys):
        mock_div_db.find.return_value = [{"id": 99, "title": "UnknownGroup"}]
        with patch.object(create_calendars, "get_organizers_json",
                          return_value={"JuLes": "jl"}):
            create_calendars.check_organizers()
        out = capsys.readouterr().out
        assert "missing in organizers.json" in out
        assert "99" in out

    def test_shows_no_title_for_organizer_without_title_field(
            self, create_calendars, mock_div_db, capsys):
        mock_div_db.find.return_value = [{"id": 100}]
        with patch.object(create_calendars, "get_organizers_json",
                          return_value={"JuLes": "jl"}):
            create_calendars.check_organizers()
        assert "No title" in capsys.readouterr().out

    def test_no_warning_when_db_is_empty(self, create_calendars, mock_div_db, capsys):
        mock_div_db.find.return_value = []
        with patch.object(create_calendars, "get_organizers_json",
                          return_value={"JuLes": "jl"}):
            create_calendars.check_organizers()
        assert capsys.readouterr().out == ""


class TestCreateCalendarsDir:
    def test_creates_directory_if_absent(self, create_calendars, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        create_calendars.create_calendars_dir()
        assert (tmp_path / "calendars").is_dir()

    def test_does_not_raise_if_directory_exists(self, create_calendars, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "calendars").mkdir()
        create_calendars.create_calendars_dir()  # should not raise


class TestGetOrganizersFromJson:
    def test_returns_list_of_tuples(self, create_calendars, monkeypatch):
        monkeypatch.chdir(REPO_ROOT)
        result = create_calendars.get_organizers_from_json()
        assert isinstance(result, list)
        assert all(isinstance(t, tuple) and len(t) == 2 for t in result)

    def test_first_element_is_code(self, create_calendars, monkeypatch):
        monkeypatch.chdir(REPO_ROOT)
        result = create_calendars.get_organizers_from_json()
        codes = [t[0] for t in result]
        assert "jl" in codes
        assert "wi" in codes
        assert "no" in codes

    def test_second_element_is_full_name(self, create_calendars, monkeypatch):
        monkeypatch.chdir(REPO_ROOT)
        result = create_calendars.get_organizers_from_json()
        full_names = [t[1] for t in result]
        assert "JuLes" in full_names
        assert "Wilma" in full_names

    def test_returns_18_organizers(self, create_calendars, monkeypatch):
        monkeypatch.chdir(REPO_ROOT)
        result = create_calendars.get_organizers_from_json()
        assert len(result) == 18

    def test_jules_maps_to_jl_code(self, create_calendars):
        with patch.object(create_calendars, "get_organizers_json",
                          return_value={"JuLes": "jl"}):
            result = create_calendars.get_organizers_from_json()
        assert result == [("jl", "JuLes")]


class TestCreateCalendar:
    def test_creates_all_ics_file(self, create_calendars, mock_div_db, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        mock_div_db.find.return_value = []
        create_calendars.create_calendar()
        assert (tmp_path / "all.ics").exists()

    def test_creates_organizer_specific_ics(self, create_calendars, mock_div_db, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        mock_div_db.find.return_value = []
        create_calendars.create_calendar(("jl", "JuLes"))
        assert (tmp_path / "calendars" / "jl.ics").exists()

    def test_event_with_valid_end_date_has_no_error(self, create_calendars, mock_div_db, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        start = datetime(2024, 6, 1, 10, 0, 0)
        end = datetime(2024, 6, 1, 12, 0, 0)
        mock_div_db.find.return_value = [_make_event(end=end)]
        create_calendars.create_calendar()
        assert "Error: The event had" not in _ics_text(tmp_path)

    def test_event_title_appears_in_ics(self, create_calendars, mock_div_db, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        mock_div_db.find.return_value = [_make_event(title="My Special Event")]
        create_calendars.create_calendar()
        assert "My Special Event" in _ics_text(tmp_path)

    def test_event_without_end_date_adds_error_description(
            self, create_calendars, mock_div_db, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        mock_div_db.find.return_value = [_make_event()]  # no end
        create_calendars.create_calendar()
        assert "Error: The event had no end date" in _ics_text(tmp_path)

    def test_event_without_end_date_uses_2h57m_duration(
            self, create_calendars, mock_div_db, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        mock_div_db.find.return_value = [_make_event()]
        create_calendars.create_calendar()
        assert "PT2H57M" in _ics_text(tmp_path)

    def test_event_with_end_more_than_7_days_after_start_adds_error(
            self, create_calendars, mock_div_db, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        start = datetime(2024, 6, 1, 10, 0, 0)
        end = datetime(2024, 6, 10, 10, 0, 0)  # 9 days later
        mock_div_db.find.return_value = [_make_event(end=end)]
        create_calendars.create_calendar()
        content = _ics_text(tmp_path)
        assert "Error: The event had an end date more than 7 days after the start date" in content

    def test_event_with_end_more_than_7_days_uses_2h56m_duration(
            self, create_calendars, mock_div_db, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        start = datetime(2024, 6, 1, 10, 0, 0)
        end = datetime(2024, 6, 10, 10, 0, 0)
        mock_div_db.find.return_value = [_make_event(end=end)]
        create_calendars.create_calendar()
        assert "PT2H56M" in _ics_text(tmp_path)

    def test_event_with_invalid_end_date_type_adds_error(
            self, create_calendars, mock_div_db, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)

        class _InvalidEndDateStub:
            def __le__(self, other):
                raise ValueError("invalid end date type")

        mock_div_db.find.return_value = [_make_event(end=_InvalidEndDateStub())]
        create_calendars.create_calendar()
        assert "Error: The event had an invalid end date" in _ics_text(tmp_path)

    def test_event_with_invalid_end_date_type_uses_2h58m_duration(
            self, create_calendars, mock_div_db, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)

        class _InvalidEndDateStub:
            def __le__(self, other):
                raise ValueError("invalid end date type")

        mock_div_db.find.return_value = [_make_event(end=_InvalidEndDateStub())]
        create_calendars.create_calendar()
        assert "PT2H58M" in _ics_text(tmp_path)

    def test_event_without_start_date_not_added_to_calendar(
            self, create_calendars, mock_div_db, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        mock_div_db.find.return_value = [{"id": 1, "title": "No Start Event"}]
        create_calendars.create_calendar()
        assert "No Start Event" not in _ics_text(tmp_path)

    def test_event_with_full_location_formatted_correctly(
            self, create_calendars, mock_div_db, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        loc = {"name": "Event Hall", "address": "Main St 1", "plz": "80333", "city": "München"}
        mock_div_db.find.return_value = [_make_event(location=loc)]
        create_calendars.create_calendar()
        content = _ics_text(tmp_path)
        assert "Event Hall" in content
        assert "Main St 1" in content
        assert "80333" in content
        assert "München" in content

    def test_none_location_fields_excluded_from_string(
            self, create_calendars, mock_div_db, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        loc = {"name": "Venue", "address": None, "plz": None, "city": "München"}
        mock_div_db.find.return_value = [_make_event(location=loc)]
        create_calendars.create_calendar()
        content = _ics_text(tmp_path)
        assert "Venue" in content
        assert "München" in content
        # None values must not appear as the literal string "None"
        assert "None" not in content

    def test_null_location_omitted(self, create_calendars, mock_div_db, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        event = _make_event()
        event["location"] = None
        mock_div_db.find.return_value = [event]
        create_calendars.create_calendar()
        # A null location produces no LOCATION: line
        assert "LOCATION:" not in _ics_text(tmp_path)

    def test_diversity_jugendzentrum_replaced_in_location(
            self, create_calendars, mock_div_db, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        loc = {"name": "diversity Jugendzentrum", "address": None, "plz": None, "city": None}
        mock_div_db.find.return_value = [_make_event(location=loc)]
        create_calendars.create_calendar()
        content = _ics_text(tmp_path)
        assert "diversity München Jugendzentrum" in content

    def test_group_name_prepended_to_title(self, create_calendars, mock_div_db, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        meta = {"parent": {"title": "JuLes"}}
        mock_div_db.find.return_value = [_make_event(title="Party Night", meta=meta)]
        create_calendars.create_calendar()
        assert "JuLes: Party Night" in _ics_text(tmp_path)

    def test_group_name_not_prepended_when_already_in_title(
            self, create_calendars, mock_div_db, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        meta = {"parent": {"title": "JuLes"}}
        mock_div_db.find.return_value = [_make_event(title="JuLes Party Night", meta=meta)]
        create_calendars.create_calendar()
        content = _ics_text(tmp_path)
        assert "JuLes: JuLes Party Night" not in content
        assert "JuLes Party Night" in content

    def test_diversity_muenchen_group_name_never_prepended(
            self, create_calendars, mock_div_db, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        meta = {"parent": {"title": "diversity München"}}
        mock_div_db.find.return_value = [_make_event(title="Community Meeting", meta=meta)]
        create_calendars.create_calendar()
        content = _ics_text(tmp_path)
        assert "diversity München: Community Meeting" not in content
        assert "Community Meeting" in content

    def test_event_without_meta_no_group_prepended(
            self, create_calendars, mock_div_db, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        mock_div_db.find.return_value = [_make_event(title="Standalone Event")]
        create_calendars.create_calendar()
        assert "SUMMARY:Standalone Event" in _ics_text(tmp_path)

    def test_description_de_used_over_en(self, create_calendars, mock_div_db, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        start = datetime(2024, 6, 1, 10, 0, 0)
        end = datetime(2024, 6, 1, 12, 0, 0)
        mock_div_db.find.return_value = [_make_event(
            end=end, description_de="Deutsch", description_en="English"
        )]
        create_calendars.create_calendar()
        content = _ics_text(tmp_path)
        assert "Deutsch" in content
        assert "English" not in content

    def test_description_en_used_when_de_is_none(
            self, create_calendars, mock_div_db, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        start = datetime(2024, 6, 1, 10, 0, 0)
        end = datetime(2024, 6, 1, 12, 0, 0)
        mock_div_db.find.return_value = [_make_event(
            end=end, description_de=None, description_en="English fallback"
        )]
        create_calendars.create_calendar()
        assert "English fallback" in _ics_text(tmp_path)

    def test_no_end_date_count_printed_for_all_ics(
            self, create_calendars, mock_div_db, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        mock_div_db.find.return_value = [_make_event(id=1), _make_event(id=2)]
        create_calendars.create_calendar()
        assert "2 of 2 events had no end date" in capsys.readouterr().out

    def test_no_end_date_count_not_printed_for_organizer_calendar(
            self, create_calendars, mock_div_db, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        mock_div_db.find.return_value = [_make_event()]
        create_calendars.create_calendar(("jl", "JuLes"))
        assert "events had no end date" not in capsys.readouterr().out

    def test_specific_organizer_query_filters_by_full_name(
            self, create_calendars, mock_div_db, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        mock_div_db.find.return_value = []
        create_calendars.create_calendar(("jl", "JuLes"))
        query = mock_div_db.find.call_args.args[0]
        assert query["meta.parent.title"] == "JuLes"

    def test_no_organizer_query_uses_or_with_missing_title(
            self, create_calendars, mock_div_db, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        mock_div_db.find.return_value = []
        mock_organizers = [("jl", "JuLes"), ("wi", "Wilma")]
        with patch.object(create_calendars, "get_organizers_from_json",
                          return_value=mock_organizers):
            create_calendars.create_calendar(("no", "Non Organizer"))
        query = mock_div_db.find.call_args.args[0]
        assert "$or" in query

    def test_no_organizer_nin_uses_full_names(
            self, create_calendars, mock_div_db, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        mock_div_db.find.return_value = []
        mock_organizers = [("jl", "JuLes"), ("wi", "Wilma")]
        with patch.object(create_calendars, "get_organizers_from_json",
                          return_value=mock_organizers):
            create_calendars.create_calendar(("no", "Non Organizer"))
        query = mock_div_db.find.call_args.args[0]
        nin_values = next(
            c["meta.parent.title"]["$nin"]
            for c in query["$or"]
            if "meta.parent.title" in c and isinstance(c["meta.parent.title"], dict)
            and "$nin" in c["meta.parent.title"]
        )
        # After the bug fix, $nin should contain full names, not codes
        assert "JuLes" in nin_values
        assert "Wilma" in nin_values
        assert "jl" not in nin_values
        assert "wi" not in nin_values

    def test_query_includes_start_date_range(self, create_calendars, mock_div_db, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        mock_div_db.find.return_value = []
        create_calendars.create_calendar()
        query = mock_div_db.find.call_args.args[0]
        assert "start" in query
        assert "$gte" in query["start"]
        assert "$lte" in query["start"]

    def test_all_ics_query_has_no_organizer_filter(
            self, create_calendars, mock_div_db, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        mock_div_db.find.return_value = []
        create_calendars.create_calendar()
        query = mock_div_db.find.call_args.args[0]
        assert "meta.parent.title" not in query


class TestCreateCalendars:
    def test_calls_create_calendar_for_all_organizers(
            self, create_calendars, mock_div_db, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)

        calls = []

        def mock_create_calendar(organizer=None):
            calls.append(organizer)

        mock_organizers = [("jl", "JuLes"), ("wi", "Wilma")]
        with patch.object(create_calendars, "create_calendar",
                          side_effect=mock_create_calendar):
            with patch.object(create_calendars, "get_organizers_from_json",
                              return_value=mock_organizers):
                create_calendars.create_calendars()

        # First call is for all.ics (organizer=None)
        assert calls[0] is None
        # Then one call per organizer
        assert ("jl", "JuLes") in calls
        assert ("wi", "Wilma") in calls

    def test_prints_creating_message(self, create_calendars, mock_div_db, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        mock_organizers = [("jl", "JuLes")]
        with patch.object(create_calendars, "create_calendar"):
            with patch.object(create_calendars, "get_organizers_from_json",
                              return_value=mock_organizers):
                create_calendars.create_calendars()
        out = capsys.readouterr().out
        assert "Creating 1 filtered calendars" in out
        assert "Calendars created" in out
