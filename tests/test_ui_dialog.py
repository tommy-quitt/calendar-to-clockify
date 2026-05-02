import pytest
from unittest.mock import patch, MagicMock
from types import SimpleNamespace
from datetime import datetime
pfrom ui_dialog import get_parameters_via_dialog

def test_get_parameters_via_dialog_success():
    """Test successful dialog interaction"""
    # Mock tkinter components
    with patch('ui_dialog.tk.Tk') as mock_tk, \
         patch('ui_dialog.tk.Toplevel') as mock_toplevel, \
         patch('ui_dialog.ttk.Label') as mock_label, \
         patch('ui_dialog.ttk.Checkbutton') as mock_checkbutton, \
         patch('ui_dialog.ttk.Frame') as mock_frame, \
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
        
        # Mock checkbox variables
        mock_simulate_var = MagicMock()
        mock_purge_var = MagicMock()
        mock_simulate_var.get.return_value = True
        mock_purge_var.get.return_value = False
        
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

def test_get_parameters_via_dialog_cancelled():
    """Test dialog cancellation"""
    # Mock tkinter components
    with patch('ui_dialog.tk.Tk') as mock_tk, \
         patch('ui_dialog.tk.Toplevel') as mock_toplevel, \
         patch('ui_dialog.ttk.Label') as mock_label, \
         patch('ui_dialog.ttk.Checkbutton') as mock_checkbutton, \
         patch('ui_dialog.ttk.Frame') as mock_frame, \
         patch('ui_dialog.ttk.Button') as mock_button, \
         patch('ui_dialog.DateEntry') as mock_date_entry:
        
        # Mock the dialog components
        mock_root = MagicMock()
        mock_tk.return_value = mock_root
        
        mock_top = MagicMock()
        mock_toplevel.return_value = mock_top
        
        # Mock the dialog to return None (cancelled)
        mock_top.wait_window.side_effect = lambda: setattr(mock_top, 'result', None)
        
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
        
        # Mock invalid date values
        mock_start_cal.get_date.return_value = "invalid-date"
        mock_end_cal.get_date.return_value = datetime(2024, 1, 2)
        
        # Mock checkbox variables
        mock_simulate_var = MagicMock()
        mock_purge_var = MagicMock()
        mock_simulate_var.get.return_value = False
        mock_purge_var.get.return_value = False
        
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
        
        # Mock checkbox variables
        mock_simulate_var = MagicMock()
        mock_purge_var = MagicMock()
        mock_simulate_var.get.return_value = False
        mock_purge_var.get.return_value = False
        
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
        
        # Mock checkbox variables
        mock_simulate_var = MagicMock()
        mock_purge_var = MagicMock()
        mock_simulate_var.get.return_value = False
        mock_purge_var.get.return_value = False
        
        # Mock the dialog's internal variables
        with patch('ui_dialog.tk.BooleanVar') as mock_boolean_var:
            mock_boolean_var.side_effect = [mock_simulate_var, mock_purge_var]
            
            # Call the function
            result = get_parameters_via_dialog()
            
            # Verify error was shown and result is None
            mock_error.assert_called_with("Input Error", "Date range cannot exceed 31 days.")
            assert result is None 