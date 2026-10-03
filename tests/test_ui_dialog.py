import pytest
from unittest.mock import patch, MagicMock
from types import SimpleNamespace
from datetime import datetime
from ui_dialog import get_parameters_via_dialog, _default_date_range

def _capture_button_commands():
    """Returns (side_effect, commands) for mocking ttk.Button.

    The dialog never simulates a real Tk event loop, so the "OK"/"Cancel"
    button's `command=` callback is otherwise never invoked. This captures
    each button's command by its label so a test can call it directly to
    simulate the user clicking that button.
    """
    commands = {}
    def _side_effect(*args, **kwargs):
        text = kwargs.get("text")
        command = kwargs.get("command")
        if text is not None:
            commands[text] = command
        return MagicMock()
    return _side_effect, commands

def test_default_date_range_first_week_uses_previous_full_month():
    # On the 1st-7th of the month, default to the ENTIRE previous month.
    today = datetime(2026, 9, 5)
    start, end = _default_date_range(today)
    assert (start.year, start.month, start.day) == (2026, 8, 1)
    assert (end.year, end.month, end.day) == (2026, 8, 31)

def test_default_date_range_first_week_boundary_day_7():
    today = datetime(2026, 3, 7)
    start, end = _default_date_range(today)
    assert (start.year, start.month, start.day) == (2026, 2, 1)
    assert (end.year, end.month, end.day) == (2026, 2, 28)

def test_default_date_range_after_first_week_uses_current_month_to_date():
    # On the 8th+ of the month, default to the 1st of THIS month through today.
    today = datetime(2026, 9, 17)
    start, end = _default_date_range(today)
    assert (start.year, start.month, start.day) == (2026, 9, 1)
    assert (end.year, end.month, end.day) == (2026, 9, 17)

def test_default_date_range_first_week_across_year_boundary():
    today = datetime(2026, 1, 3)
    start, end = _default_date_range(today)
    assert (start.year, start.month, start.day) == (2025, 12, 1)
    assert (end.year, end.month, end.day) == (2025, 12, 31)

def test_get_parameters_via_dialog_success():
    """Test successful dialog interaction"""
    # Mock tkinter components
    with patch('ui_dialog.tk.Tk') as mock_tk, \
         patch('ui_dialog.tk.Toplevel') as mock_toplevel, \
         patch('ui_dialog.ttk.Label') as mock_label, \
         patch('ui_dialog.ttk.Checkbutton') as mock_checkbutton, \
         patch('ui_dialog.ttk.Frame') as mock_frame, \
         patch('ui_dialog.ttk.Entry') as mock_entry, \
         patch('ui_dialog.ttk.Button') as mock_button, \
         patch('ui_dialog.DateEntry') as mock_date_entry:

        # Mock the dialog components
        mock_root = MagicMock()
        mock_tk.return_value = mock_root

        mock_top = MagicMock()
        mock_toplevel.return_value = mock_top

        # Mock date entry widgets
        mock_start_cal = MagicMock()
        mock_end_cal = MagicMock()
        mock_date_entry.side_effect = [mock_start_cal, mock_end_cal]

        # Mock the date values
        mock_start_cal.get_date.return_value = datetime(2024, 1, 1)
        mock_end_cal.get_date.return_value = datetime(2024, 1, 2)

        # Mock the customer text entry (left blank -> customer None)
        mock_entry.return_value.get.return_value = ""

        # Mock checkbox variables
        mock_simulate_var = MagicMock()
        mock_purge_var = MagicMock()
        mock_simulate_var.get.return_value = True
        mock_purge_var.get.return_value = False

        # Capture the OK/Cancel button commands and invoke "OK" when the
        # dialog would otherwise block on wait_window, simulating a click.
        button_side_effect, commands = _capture_button_commands()
        mock_button.side_effect = button_side_effect
        mock_root.wait_window.side_effect = lambda *a, **kw: commands["OK"]()

        # Mock the dialog's internal variables
        with patch('ui_dialog.tk.BooleanVar') as mock_boolean_var:
            mock_boolean_var.side_effect = [mock_simulate_var, mock_purge_var]

            # Call the function
            result = get_parameters_via_dialog()

            # Verify the result
            assert result is not None
            assert result.start == '2024-01-01'
            assert result.end == '2024-01-02'
            assert result.simulate is True
            assert result.purge is False
            assert result.customer is None

def test_get_parameters_via_dialog_cancelled():
    """Test dialog cancellation"""
    # Mock tkinter components
    with patch('ui_dialog.tk.Tk') as mock_tk, \
         patch('ui_dialog.tk.Toplevel') as mock_toplevel, \
         patch('ui_dialog.ttk.Label') as mock_label, \
         patch('ui_dialog.ttk.Checkbutton') as mock_checkbutton, \
         patch('ui_dialog.ttk.Frame') as mock_frame, \
         patch('ui_dialog.ttk.Entry') as mock_entry, \
         patch('ui_dialog.ttk.Button') as mock_button, \
         patch('ui_dialog.DateEntry') as mock_date_entry:

        # Mock the dialog components
        mock_root = MagicMock()
        mock_tk.return_value = mock_root

        mock_top = MagicMock()
        mock_toplevel.return_value = mock_top

        # Mock date entry widgets (constructed even though the user cancels
        # before ever touching them)
        mock_date_entry.side_effect = [MagicMock(), MagicMock()]

        # Capture the OK/Cancel button commands and invoke "Cancel" to
        # simulate the user dismissing the dialog.
        button_side_effect, commands = _capture_button_commands()
        mock_button.side_effect = button_side_effect
        mock_root.wait_window.side_effect = lambda *a, **kw: commands["Cancel"]()

        # Mock the dialog's internal variables (BooleanVar() needs a real
        # default root unless mocked, since tk.Tk is mocked here)
        with patch('ui_dialog.tk.BooleanVar') as mock_boolean_var:
            mock_boolean_var.side_effect = [MagicMock(), MagicMock()]

            # Call the function
            result = get_parameters_via_dialog()

            # Verify the result is None
            assert result is None

def test_get_parameters_via_dialog_invalid_date():
    """Test dialog with invalid date format"""
    # Mock tkinter components
    with patch('ui_dialog.tk.Tk') as mock_tk, \
         patch('ui_dialog.tk.Toplevel') as mock_toplevel, \
         patch('ui_dialog.ttk.Label') as mock_label, \
         patch('ui_dialog.ttk.Checkbutton') as mock_checkbutton, \
         patch('ui_dialog.ttk.Frame') as mock_frame, \
         patch('ui_dialog.ttk.Entry') as mock_entry, \
         patch('ui_dialog.ttk.Button') as mock_button, \
         patch('ui_dialog.DateEntry') as mock_date_entry, \
         patch('ui_dialog.messagebox.showerror') as mock_error:

        # Mock the dialog components
        mock_root = MagicMock()
        mock_tk.return_value = mock_root

        mock_top = MagicMock()
        mock_toplevel.return_value = mock_top

        # Mock date entry widgets
        mock_start_cal = MagicMock()
        mock_end_cal = MagicMock()
        mock_date_entry.side_effect = [mock_start_cal, mock_end_cal]

        # Mock invalid date values. get_date() on a real DateEntry always
        # returns a valid date object (the widget itself won't accept bad
        # input), so simulate a format ok() can't parse via strftime()
        # instead of get_date() itself.
        mock_start_cal.get_date.return_value.strftime.return_value = "invalid-date"
        mock_end_cal.get_date.return_value = datetime(2024, 1, 2)

        mock_entry.return_value.get.return_value = ""

        # Mock checkbox variables
        mock_simulate_var = MagicMock()
        mock_purge_var = MagicMock()
        mock_simulate_var.get.return_value = False
        mock_purge_var.get.return_value = False

        button_side_effect, commands = _capture_button_commands()
        mock_button.side_effect = button_side_effect
        mock_root.wait_window.side_effect = lambda *a, **kw: commands["OK"]()

        # Mock the dialog's internal variables
        with patch('ui_dialog.tk.BooleanVar') as mock_boolean_var:
            mock_boolean_var.side_effect = [mock_simulate_var, mock_purge_var]

            # Call the function
            result = get_parameters_via_dialog()

            # Verify error was shown and result is None
            mock_error.assert_called_with("Input Error", "Start and end dates must be in YYYY-MM-DD format.")
            assert result is None

def test_get_parameters_via_dialog_start_after_end():
    """Test dialog with start date after end date"""
    # Mock tkinter components
    with patch('ui_dialog.tk.Tk') as mock_tk, \
         patch('ui_dialog.tk.Toplevel') as mock_toplevel, \
         patch('ui_dialog.ttk.Label') as mock_label, \
         patch('ui_dialog.ttk.Checkbutton') as mock_checkbutton, \
         patch('ui_dialog.ttk.Frame') as mock_frame, \
         patch('ui_dialog.ttk.Entry') as mock_entry, \
         patch('ui_dialog.ttk.Button') as mock_button, \
         patch('ui_dialog.DateEntry') as mock_date_entry, \
         patch('ui_dialog.messagebox.showerror') as mock_error:

        # Mock the dialog components
        mock_root = MagicMock()
        mock_tk.return_value = mock_root

        mock_top = MagicMock()
        mock_toplevel.return_value = mock_top

        # Mock date entry widgets
        mock_start_cal = MagicMock()
        mock_end_cal = MagicMock()
        mock_date_entry.side_effect = [mock_start_cal, mock_end_cal]

        # Mock date values with start after end
        mock_start_cal.get_date.return_value = datetime(2024, 1, 2)
        mock_end_cal.get_date.return_value = datetime(2024, 1, 1)

        mock_entry.return_value.get.return_value = ""

        # Mock checkbox variables
        mock_simulate_var = MagicMock()
        mock_purge_var = MagicMock()
        mock_simulate_var.get.return_value = False
        mock_purge_var.get.return_value = False

        button_side_effect, commands = _capture_button_commands()
        mock_button.side_effect = button_side_effect
        mock_root.wait_window.side_effect = lambda *a, **kw: commands["OK"]()

        # Mock the dialog's internal variables
        with patch('ui_dialog.tk.BooleanVar') as mock_boolean_var:
            mock_boolean_var.side_effect = [mock_simulate_var, mock_purge_var]

            # Call the function
            result = get_parameters_via_dialog()

            # Verify error was shown and result is None
            mock_error.assert_called_with("Input Error", "Start date cannot be after end date.")
            assert result is None

def test_get_parameters_via_dialog_date_range_too_large():
    """Test dialog with date range exceeding 31 days"""
    # Mock tkinter components
    with patch('ui_dialog.tk.Tk') as mock_tk, \
         patch('ui_dialog.tk.Toplevel') as mock_toplevel, \
         patch('ui_dialog.ttk.Label') as mock_label, \
         patch('ui_dialog.ttk.Checkbutton') as mock_checkbutton, \
         patch('ui_dialog.ttk.Frame') as mock_frame, \
         patch('ui_dialog.ttk.Entry') as mock_entry, \
         patch('ui_dialog.ttk.Button') as mock_button, \
         patch('ui_dialog.DateEntry') as mock_date_entry, \
         patch('ui_dialog.messagebox.showerror') as mock_error:

        # Mock the dialog components
        mock_root = MagicMock()
        mock_tk.return_value = mock_root

        mock_top = MagicMock()
        mock_toplevel.return_value = mock_top

        # Mock date entry widgets
        mock_start_cal = MagicMock()
        mock_end_cal = MagicMock()
        mock_date_entry.side_effect = [mock_start_cal, mock_end_cal]

        # Mock date values with range > 31 days
        mock_start_cal.get_date.return_value = datetime(2024, 1, 1)
        mock_end_cal.get_date.return_value = datetime(2024, 3, 1)

        mock_entry.return_value.get.return_value = ""

        # Mock checkbox variables
        mock_simulate_var = MagicMock()
        mock_purge_var = MagicMock()
        mock_simulate_var.get.return_value = False
        mock_purge_var.get.return_value = False

        button_side_effect, commands = _capture_button_commands()
        mock_button.side_effect = button_side_effect
        mock_root.wait_window.side_effect = lambda *a, **kw: commands["OK"]()

        # Mock the dialog's internal variables
        with patch('ui_dialog.tk.BooleanVar') as mock_boolean_var:
            mock_boolean_var.side_effect = [mock_simulate_var, mock_purge_var]

            # Call the function
            result = get_parameters_via_dialog()

            # Verify error was shown and result is None
            mock_error.assert_called_with("Input Error", "Date range cannot exceed 31 days.")
            assert result is None
