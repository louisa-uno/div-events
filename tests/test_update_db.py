import importlib.util
import os
import sys
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture(scope="module")
def update_db():
    """Load update-db.py as a module with mocked MongoDB."""
    module_path = os.path.join(REPO_ROOT, "update-db.py")
    mock_client = MagicMock()
    with patch("pymongo.MongoClient", return_value=mock_client):
        spec = importlib.util.spec_from_file_location("update_db", module_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules["update_db"] = module
        spec.loader.exec_module(module)
    return module


@pytest.fixture
def mock_div_db(update_db):
    """Replace div_db with a fresh MagicMock for each test."""
    mock = MagicMock()
    update_db.div_db = mock
    return mock


class TestConvertDates:
    def test_non_date_string_returned_as_is(self, update_db):
        assert update_db.convert_dates("hello world") == "hello world"

    def test_iso_date_string_converted_to_datetime(self, update_db):
        result = update_db.convert_dates("2024-01-15T10:30:00")
        assert isinstance(result, datetime)
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15

    def test_dict_values_recursively_converted(self, update_db):
        result = update_db.convert_dates({"start": "2024-06-01T09:00:00", "name": "My Event"})
        assert isinstance(result["start"], datetime)
        assert result["name"] == "My Event"

    def test_nested_dict_recursively_converted(self, update_db):
        result = update_db.convert_dates({"meta": {"created_at": "2023-01-01T00:00:00", "slug": "event"}})
        assert isinstance(result["meta"]["created_at"], datetime)
        assert result["meta"]["slug"] == "event"

    def test_list_items_recursively_converted(self, update_db):
        result = update_db.convert_dates(["2024-03-01T00:00:00", "plain", 99])
        assert isinstance(result[0], datetime)
        assert result[1] == "plain"
        assert result[2] == 99

    def test_integer_passthrough(self, update_db):
        assert update_db.convert_dates(42) == 42

    def test_float_passthrough(self, update_db):
        assert update_db.convert_dates(3.14) == 3.14

    def test_none_passthrough(self, update_db):
        assert update_db.convert_dates(None) is None

    def test_bool_passthrough(self, update_db):
        assert update_db.convert_dates(True) is True
        assert update_db.convert_dates(False) is False

    def test_empty_dict_passthrough(self, update_db):
        assert update_db.convert_dates({}) == {}

    def test_empty_list_passthrough(self, update_db):
        assert update_db.convert_dates([]) == []

    def test_value_error_returns_original_string(self, update_db):
        with patch("update_db.parse", side_effect=ValueError):
            result = update_db.convert_dates("unparseable-string")
        assert result == "unparseable-string"

    def test_overflow_error_returns_original_string(self, update_db):
        with patch("update_db.parse", side_effect=OverflowError):
            result = update_db.convert_dates("overflow-string")
        assert result == "overflow-string"

    def test_mixed_dict_with_non_date_values(self, update_db):
        obj = {"count": 5, "active": True, "start": "2024-01-01T00:00:00", "name": None}
        result = update_db.convert_dates(obj)
        assert result["count"] == 5
        assert result["active"] is True
        assert isinstance(result["start"], datetime)
        assert result["name"] is None

    def test_list_of_dicts_recursively_converted(self, update_db):
        obj = [{"date": "2024-06-01T10:00:00"}, {"date": "2024-07-01T10:00:00"}]
        result = update_db.convert_dates(obj)
        assert isinstance(result[0]["date"], datetime)
        assert isinstance(result[1]["date"], datetime)


class TestUpsertPage:
    def test_inserts_new_page_and_prints_message(self, update_db, mock_div_db, capsys):
        mock_result = MagicMock()
        mock_result.matched_count = 0
        mock_div_db.replace_one.return_value = mock_result

        update_db.upsert_page({"id": 1, "title": "New Event"})

        captured = capsys.readouterr()
        assert "Inserted new page with id 1" in captured.out

    def test_updates_existing_page_and_prints_message(self, update_db, mock_div_db, capsys):
        mock_result = MagicMock()
        mock_result.matched_count = 1
        mock_div_db.replace_one.return_value = mock_result

        update_db.upsert_page({"id": 2, "title": "Existing Event"})

        captured = capsys.readouterr()
        assert "Updated page with id 2" in captured.out

    def test_sets_id_field_from_page_id(self, update_db, mock_div_db):
        mock_result = MagicMock()
        mock_result.matched_count = 0
        mock_div_db.replace_one.return_value = mock_result

        update_db.upsert_page({"id": 42, "title": "Test"})

        doc = mock_div_db.replace_one.call_args.args[1]
        assert doc["_id"] == 42

    def test_filter_uses_id_as_key(self, update_db, mock_div_db):
        mock_result = MagicMock()
        mock_result.matched_count = 0
        mock_div_db.replace_one.return_value = mock_result

        update_db.upsert_page({"id": 7, "title": "Test"})

        filter_doc = mock_div_db.replace_one.call_args.args[0]
        assert filter_doc == {"_id": 7}

    def test_sets_last_fetched_to_current_time(self, update_db, mock_div_db):
        mock_result = MagicMock()
        mock_result.matched_count = 0
        mock_div_db.replace_one.return_value = mock_result

        before = datetime.now()
        update_db.upsert_page({"id": 5, "title": "Test"})
        after = datetime.now()

        doc = mock_div_db.replace_one.call_args.args[1]
        assert before <= doc["last_fetched"] <= after

    def test_uses_upsert_true(self, update_db, mock_div_db):
        mock_result = MagicMock()
        mock_result.matched_count = 0
        mock_div_db.replace_one.return_value = mock_result

        update_db.upsert_page({"id": 7, "title": "Test"})

        assert mock_div_db.replace_one.call_args.kwargs["upsert"] is True

    def test_bulk_write_error_handled_gracefully(self, update_db, mock_div_db, capsys):
        from pymongo.errors import BulkWriteError
        error_details = {
            "writeErrors": [{"code": 11000, "errmsg": "duplicate key"}],
            "writeConcernErrors": [],
            "nInserted": 0,
            "nUpserted": 0,
            "nMatched": 0,
            "nModified": 0,
            "nRemoved": 0,
            "upserted": [],
        }
        mock_div_db.replace_one.side_effect = BulkWriteError(error_details)

        # Should not raise
        update_db.upsert_page({"id": 3, "title": "Test"})

        captured = capsys.readouterr()
        assert "Bulk write error" in captured.out

    def test_date_strings_in_page_are_converted(self, update_db, mock_div_db):
        mock_result = MagicMock()
        mock_result.matched_count = 0
        mock_div_db.replace_one.return_value = mock_result

        update_db.upsert_page({"id": 10, "start": "2024-06-01T10:00:00"})

        doc = mock_div_db.replace_one.call_args.args[1]
        assert isinstance(doc["start"], datetime)


class TestGetPage:
    def test_200_response_calls_upsert_and_returns_id(self, update_db, mock_div_db):
        mock_result = MagicMock()
        mock_result.matched_count = 0
        mock_div_db.replace_one.return_value = mock_result

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": 5, "title": "Test Event"}

        with patch("requests.request", return_value=mock_response):
            result = update_db.get_page(5)

        assert result == 5
        mock_div_db.replace_one.assert_called_once()

    def test_404_response_returns_none(self, update_db, capsys):
        mock_response = MagicMock()
        mock_response.status_code = 404

        with patch("requests.request", return_value=mock_response):
            result = update_db.get_page(999)

        assert result is None
        captured = capsys.readouterr()
        assert "Page not found" in captured.out

    def test_non_200_non_404_raises_system_exit(self, update_db):
        mock_response = MagicMock()
        mock_response.status_code = 500

        with patch("requests.request", return_value=mock_response):
            with pytest.raises(SystemExit):
                update_db.get_page(1)

    def test_request_uses_correct_url(self, update_db, mock_div_db):
        mock_result = MagicMock()
        mock_result.matched_count = 0
        mock_div_db.replace_one.return_value = mock_result

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": 42, "title": "Test"}

        with patch("requests.request", return_value=mock_response) as mock_req:
            update_db.get_page(42)

        mock_req.assert_called_once_with(
            "GET", "https://diversity-muenchen.de/api/v2/pages/42/"
        )

    def test_404_prints_page_not_found(self, update_db, capsys):
        mock_response = MagicMock()
        mock_response.status_code = 404

        with patch("requests.request", return_value=mock_response):
            update_db.get_page(0)

        assert "Page not found" in capsys.readouterr().out


class TestGetPages:
    def _make_cursor(self, mock_div_db, raises_index_error=False, id_value=None):
        mock_cursor = MagicMock()
        if raises_index_error:
            mock_cursor.__getitem__ = MagicMock(side_effect=IndexError)
        else:
            mock_cursor.__getitem__ = MagicMock(return_value={"id": id_value})
        mock_div_db.find.return_value.sort.return_value.limit.return_value = mock_cursor

    def test_empty_db_starts_from_id_zero(self, update_db, mock_div_db, capsys):
        self._make_cursor(mock_div_db, raises_index_error=True)
        with patch.object(update_db, "get_page", return_value=None):
            update_db.get_pages()
        assert "Starting from id 0" in capsys.readouterr().out

    def test_starts_from_highest_id_plus_one(self, update_db, mock_div_db, capsys):
        self._make_cursor(mock_div_db, id_value=100)
        with patch.object(update_db, "get_page", return_value=None):
            update_db.get_pages()
        assert "Starting from id 101" in capsys.readouterr().out

    def test_stops_after_11_consecutive_failures(self, update_db, mock_div_db):
        self._make_cursor(mock_div_db, raises_index_error=True)
        call_ids = []

        def mock_get_page(id):
            call_ids.append(id)
            return None  # always 404

        with patch.object(update_db, "get_page", side_effect=mock_get_page):
            update_db.get_pages()

        # fails > 10 triggers break, so exactly 11 calls (fails=1..11)
        assert len(call_ids) == 11

    def test_fails_counter_resets_on_success(self, update_db, mock_div_db):
        self._make_cursor(mock_div_db, raises_index_error=True)
        # id=0 succeeds, id=1..11 fail → second batch of 11 failures after reset
        call_count = {"n": 0}

        def mock_get_page(id):
            call_count["n"] += 1
            return id if id == 0 else None

        with patch.object(update_db, "get_page", side_effect=mock_get_page):
            update_db.get_pages()

        # id=0 succeeds (resets fails), then id=1..11 all fail (11 more calls)
        assert call_count["n"] == 12

    def test_increments_id_on_each_iteration(self, update_db, mock_div_db):
        self._make_cursor(mock_div_db, raises_index_error=True)
        call_ids = []

        def mock_get_page(id):
            call_ids.append(id)
            return None

        with patch.object(update_db, "get_page", side_effect=mock_get_page):
            update_db.get_pages()

        # IDs should be sequential starting from 0
        assert call_ids == list(range(11))


class TestUpdatePages:
    def test_calls_get_page_for_each_result(self, update_db, mock_div_db):
        mock_div_db.find.return_value = [{"id": 1}, {"id": 2}, {"id": 3}]
        called_ids = []

        with patch.object(update_db, "get_page", side_effect=lambda id: called_ids.append(id) or id):
            update_db.update_pages()

        assert called_ids == [1, 2, 3]

    def test_empty_results_no_get_page_calls(self, update_db, mock_div_db):
        mock_div_db.find.return_value = []

        with patch.object(update_db, "get_page") as mock_get_page:
            update_db.update_pages()

        mock_get_page.assert_not_called()

    def test_query_includes_event_organizer_condition(self, update_db, mock_div_db):
        mock_div_db.find.return_value = []

        with patch.object(update_db, "get_page"):
            update_db.update_pages()

        query = mock_div_db.find.call_args.args[0]
        or_conditions = query["$or"]
        assert any(
            cond.get("meta.type") == "home.EventOrganizer"
            for cond in or_conditions
        )

    def test_query_includes_stale_pages_condition(self, update_db, mock_div_db):
        mock_div_db.find.return_value = []

        with patch.object(update_db, "get_page"):
            update_db.update_pages()

        query = mock_div_db.find.call_args.args[0]
        or_conditions = query["$or"]
        # At least one condition checks last_fetched
        assert any("last_fetched" in cond for cond in or_conditions)

    def test_query_includes_upcoming_events_condition(self, update_db, mock_div_db):
        mock_div_db.find.return_value = []

        with patch.object(update_db, "get_page"):
            update_db.update_pages()

        query = mock_div_db.find.call_args.args[0]
        # The query must have $or with multiple conditions
        assert "$or" in query
        assert len(query["$or"]) >= 3
