"""Position regression tests; Tk tests use real windows and synthetic work areas."""
import copy
import threading
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from core.settings import DEFAULTS
from core.storage import AppPaths
from windows.monitors import primary_monitor, rectangle_visible, safe_position, selected_monitor
from ui.widget import IPInfoWidget

PRIMARY = dict(left=100, top=80, right=1500, bottom=980, primary=True, device='primary')
LEFT = dict(left=-1400, top=80, right=0, bottom=980, primary=False, device='left')
ABOVE = dict(left=100, top=-900, right=1500, bottom=0, primary=False, device='above')
MONITORS = [LEFT, ABOVE, PRIMARY]


class MonitorTests(unittest.TestCase):
    def test_primary_and_safe_position(self):
        self.assertEqual(primary_monitor(MONITORS), PRIMARY)
        self.assertEqual(safe_position(PRIMARY, 300, 150), (1178, 102))
        self.assertEqual(safe_position(PRIMARY, 2000, 1200), (100, 80))
        self.assertIsNone(primary_monitor([]))

    def test_exact_monitor_lookup_and_legacy_fallback(self):
        with patch('windows.monitors.list_monitors', return_value=MONITORS):
            self.assertEqual(selected_monitor('left', fallback_to_primary=False), LEFT)
            self.assertIsNone(selected_monitor('missing', fallback_to_primary=False))
            self.assertEqual(selected_monitor('missing'), PRIMARY)

    def test_visibility_thresholds_and_negative_coordinates(self):
        for x, y in [(200, 100), (-500, 150), (200, -400)]:
            self.assertTrue(rectangle_visible(x, y, 300, 150, MONITORS))
        self.assertTrue(rectangle_visible(1450, 950, 300, 150, [PRIMARY]))
        self.assertFalse(rectangle_visible(1451, 950, 300, 150, [PRIMARY]))
        self.assertFalse(rectangle_visible(1450, 951, 300, 150, [PRIMARY]))
        self.assertFalse(rectangle_visible(5000, 5000, 300, 150, MONITORS))
        self.assertFalse(rectangle_visible(200, 100, 300, 150, []))
        self.assertTrue(rectangle_visible(100, 80, 20, 20, [PRIMARY]))


class WidgetTests(unittest.TestCase):
    def make_widget(self, x=200, y=150, mode='normal', topmost=True, pin=None, saved=None):
        settings = SimpleNamespace(data={**copy.deepcopy(DEFAULTS), 'x': x, 'y': y,
                                        'display_mode': mode, 'always_on_top': topmost, 'monitor_device': pin}, save=Mock())
        if saved is not None:
            settings.data = copy.deepcopy(saved)
        settings.update = settings.data.update
        settings.save.side_effect = lambda: setattr(settings, 'persisted', copy.deepcopy(settings.data))
        # Keep native taskbar icons and network/real user storage out of tests.
        widget = IPInfoWidget(AppPaths(), settings, Mock())
        self.addCleanup(widget.root.destroy)
        widget.root.update_idletasks()
        return widget

    def setUp(self):
        for target, value in [('ui.widget.list_monitors', MONITORS),
                              ('windows.monitors.list_monitors', MONITORS)]:
            patcher = patch(target, return_value=value)
            patcher.start()
            self.addCleanup(patcher.stop)
        patcher = patch('ui.widget.TaskbarIcon')
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_saved_positions_and_all_layouts(self):
        for mode in ('compact', 'normal', 'monitoring'):
            for x, y in ((200, 150), (-500, 150), (200, -400)):
                with self.subTest(mode=mode, x=x, y=y):
                    w = self.make_widget(x, y, mode)
                    self.assertEqual((w.root.winfo_x(), w.root.winfo_y()), (x, y))
                    w.settings.save.assert_not_called()
                    for next_mode in ('compact', 'normal', 'monitoring'):
                        w.settings.data['display_mode'] = next_mode
                        w.rebuild_layout()
                        w.root.update_idletasks()
                        self.assertEqual((w.root.winfo_x(), w.root.winfo_y()), (x, y))
                    w.settings.save.assert_not_called()

    def test_offscreen_repair_changes_only_coordinates(self):
        for mode in ('compact', 'normal', 'monitoring'):
            with self.subTest(mode=mode):
                w = self.make_widget(6000, 6000, mode)
                expected = safe_position(PRIMARY, *w._widget_size())
                self.assertEqual((w.root.winfo_x(), w.root.winfo_y()), expected)
                self.assertEqual((w.settings.data['x'], w.settings.data['y']), expected)
                w.settings.save.assert_called_once()
                original = {**DEFAULTS, 'display_mode': mode}
                for key in original.keys() - {'x', 'y'}:
                    self.assertEqual(w.settings.data[key], original[key])

    def test_layout_change_repairs_using_new_size(self):
        w = self.make_widget()
        w.root.geometry('+6000+6000')
        w.root.update_idletasks()
        w.settings.data['display_mode'] = 'monitoring'
        w.rebuild_layout()
        w.root.update_idletasks()
        self.assertEqual((w.root.winfo_x(), w.root.winfo_y()), safe_position(PRIMARY, *w._widget_size()))
        w.settings.save.assert_called_once()

    def test_recovery_queue_and_topmost(self):
        for topmost in (False, True):
            with self.subTest(topmost=topmost):
                w = self.make_widget(topmost=topmost)
                w.root.withdraw()
                w.settings.data['monitor_device'] = 'left'
                # Invoke the actual tray callback from another thread.
                thread = threading.Thread(target=w.tray._callbacks['restore_primary'])
                thread.start()
                thread.join()
                self.assertEqual(w.root.state(), 'withdrawn')
                w.settings.save.assert_not_called()
                w.process_queue()
                w.root.update_idletasks()
                self.assertEqual(w.root.state(), 'normal')
                self.assertEqual(bool(w.root.attributes('-topmost')), topmost)
                self.assertIsNone(w.settings.data['monitor_device'])
                self.assertIsNone(w.settings.persisted['monitor_device'])
                self.assertEqual((w.settings.persisted['x'], w.settings.persisted['y']),
                                 (w.root.winfo_x(), w.root.winfo_y()))
                self.assertEqual((w.root.winfo_x(), w.root.winfo_y()), safe_position(PRIMARY, *w._widget_size()))
                w.settings.save.assert_called_once()
                # Cancel the poll scheduled by process_queue before destroying Tk.
                for timer in w.root.tk.call('after', 'info'):
                    w.root.after_cancel(timer)

    def test_failed_enumeration_preserves_saved_position(self):
        with patch('ui.widget.list_monitors', return_value=[]), patch('ui.widget.primary_monitor', return_value=None):
            w = self.make_widget(-500, -400)
            self.assertEqual((w.root.winfo_x(), w.root.winfo_y()), (-500, -400))
            w.settings.save.assert_not_called()

    def test_pinned_startup_overrides_saved_primary_position(self):
        for mode in ('compact', 'normal', 'monitoring'):
            with self.subTest(mode=mode):
                w = self.make_widget(mode=mode, pin='left')
                self.assertEqual((w.root.winfo_x(), w.root.winfo_y()), safe_position(LEFT, *w._widget_size()))
                self.assertEqual(w.settings.data['monitor_device'], 'left')

    def test_missing_pin_recovers_to_primary(self):
        w = self.make_widget(-6000, -6000, pin='missing')
        self.assertEqual((w.root.winfo_x(), w.root.winfo_y()), safe_position(PRIMARY, *w._widget_size()))
        self.assertEqual(w.settings.persisted['monitor_device'], 'missing')
        self.assertEqual((w.settings.persisted['x'], w.settings.persisted['y']),
                         (w.root.winfo_x(), w.root.winfo_y()))

    def test_manual_recovery_survives_restart(self):
        w = self.make_widget(pin='left')
        w.restore_to_primary_monitor()
        restarted = self.make_widget(saved=w.settings.persisted)
        self.assertIsNone(restarted.settings.data['monitor_device'])
        self.assertEqual((restarted.root.winfo_x(), restarted.root.winfo_y()),
                         (w.settings.persisted['x'], w.settings.persisted['y']))
        restarted.settings.save.assert_not_called()

    def test_settings_can_pin_again_after_recovery(self):
        w = self.make_widget(pin='left')
        w.restore_to_primary_monitor()
        # Exercise the actual Settings save handler without registry or network effects.
        with patch('ui.widget.set_autostart'), patch.object(w, 'refresh_now'), patch.object(w, 'schedule_next_refresh'):
            w.save_settings({'monitor_device': 'left'})
        w.root.update_idletasks()
        self.assertEqual(w.settings.persisted['monitor_device'], 'left')
        self.assertEqual((w.root.winfo_x(), w.root.winfo_y()), safe_position(LEFT, *w._widget_size()))
        restarted = self.make_widget(saved=w.settings.persisted)
        self.assertEqual((restarted.root.winfo_x(), restarted.root.winfo_y()), safe_position(LEFT, *restarted._widget_size()))

    def test_tray_menu_routes_recovery_callback(self):
        w = self.make_widget()
        fake = SimpleNamespace(Menu=Mock(side_effect=lambda *items: items),
                               MenuItem=lambda label, callback: (label, callback))
        fake.Menu.SEPARATOR = None
        with patch('windows.tray.pystray', fake):
            menu = w.tray._menu()
        item = next(item for item in menu if item and item[0] == 'Restore widget to primary monitor')
        item[1]()
        self.assertEqual(w._queue.get_nowait(), ('restore_primary', None))


if __name__ == '__main__':
    unittest.main()
