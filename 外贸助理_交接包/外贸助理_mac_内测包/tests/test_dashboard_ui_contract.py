from pathlib import Path


def _ui_html() -> str:
    ui_file = Path(__file__).resolve().parents[1] / "app" / "dashboard_ui.html"
    return ui_file.read_text(encoding="utf-8")


def test_dashboard_has_task_filter_controls() -> None:
    html = _ui_html()
    assert 'id="taskStatusFilter"' in html
    assert 'id="taskSearchInput"' in html
    assert 'id="customerSearchInput"' in html
    assert 'id="clearTaskFilters"' in html


def test_dashboard_has_filter_i18n_and_apply_logic() -> None:
    html = _ui_html()
    assert "filterStatus" in html
    assert "filterAll" in html
    assert "filterOpen" in html
    assert "taskSearchPlaceholder" in html
    assert "customerSearchPlaceholder" in html
    assert "function applyTaskFilters(" in html
    assert 'value="open"' in html


def test_dashboard_has_compact_diagnostics_flag_and_i18n_keys() -> None:
    html = _ui_html()
    assert 'id="diagFlag"' in html
    assert "diagFlagPrefix" in html
    assert "diagStatusOk" in html
    assert "diagStatusWarn" in html
    assert "diagStatusUnknown" in html


def test_dashboard_kpi_cards_support_navigation_actions() -> None:
    html = _ui_html()
    assert "data-kpi-action" in html
    assert "kpi-card" in html
    assert "function jumpToKpiTarget(" in html


def test_dashboard_has_newbie_guide_actions() -> None:
    html = _ui_html()
    assert 'id="newbieGuide"' in html
    assert 'id="newbieClose"' in html
    assert 'id="newbieStepOverdue"' in html
    assert 'id="newbieStepAlerts"' in html
    assert 'id="newbieStepFollowup"' in html
    assert "function applyEntryGuide(" in html
    assert "function dismissEntryGuide(" in html
    assert "ta_newbie_guide_dismissed" in html


def test_dashboard_alert_cards_have_detail_and_handle_actions() -> None:
    html = _ui_html()
    assert "detail-alert-customer" in html
    assert "alert-view-detail" in html
    assert "alert-go-handle" in html
    assert "alertViewDetail" in html
    assert "alertGoHandle" in html


def test_dashboard_supports_desktop_deeplink_filters() -> None:
    html = _ui_html()
    assert 'q.get("task_status")' in html
    assert 'q.get("customer_id")' in html
    assert 'q.get("task_id")' in html
    assert "function applyDeepLink(" in html
    assert "deepLinkApplied" in html
