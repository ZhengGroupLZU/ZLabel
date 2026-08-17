def test_main_window_constructs(main_window):
    win = main_window
    assert win.canvas is not None
    assert win.undo_stack is not None
    assert win.backend is not None
    assert not win.backend.needs_login
    # all four docks exist
    for dock in (win.dock_files, win.dock_labels, win.dock_annos, win.dock_infos):
        assert dock is not None


def test_populated_project_sets_canvas_items(populated_project):
    win, proj, anno, rebuild = populated_project
    assert proj.crt_anno is anno
    assert proj.crt_task is not None
    assert win.canvas.showing_items == {}
