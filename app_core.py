from app_funcs.init_app import __init__ as init_app
from app_funcs.setup_page import setup_page
from app_funcs.setup_ui import setup_ui
from app_funcs.toggle_theme import toggle_theme
from app_funcs.on_nav_change import on_nav_change
from app_funcs.build_profiles_view import build_profiles_view
from app_funcs.build_proxies_view import build_proxies_view
from app_funcs.build_settings_view import build_settings_view
from app_funcs.refresh_profiles import refresh_profiles
from app_funcs.refresh_proxies import refresh_proxies
from app_funcs.refresh_current_view import refresh_current_view
from app_funcs.open_dialog import open_dialog
from app_funcs.parse_open_tabs import parse_open_tabs
from app_funcs.validate_open_tabs import validate_open_tabs
from app_funcs.build_profile_launch_settings import build_profile_launch_settings
from app_funcs.close_dialog import close_dialog
from app_funcs.run_ui import run_ui
from app_funcs.toggle_proxy_selection import toggle_proxy_selection
from app_funcs.toggle_select_all_proxies import toggle_select_all_proxies
from app_funcs.check_selected_proxies import check_selected_proxies
from app_funcs.show_create_profile_dialog import show_create_profile_dialog
from app_funcs.show_edit_profile_dialog import show_edit_profile_dialog
from app_funcs.show_create_proxy_dialog import show_create_proxy_dialog
from app_funcs.show_edit_proxy_dialog import show_edit_proxy_dialog
from app_funcs.toggle_profile import toggle_profile
from app_funcs.delete_profile import delete_profile
from app_funcs.delete_proxy import delete_proxy
from app_funcs.check_proxy import check_proxy
from app_funcs.check_proxy_with_playwright import check_proxy_with_playwright
from app_funcs.check_all_proxies import check_all_proxies
from app_funcs.parse_proxy_line import parse_proxy_line
from app_funcs.import_proxies_from_file import import_proxies_from_file
from app_funcs.show_import_proxy_dialog import show_import_proxy_dialog
from app_funcs.show_success_dialog import show_success_dialog
from app_funcs.show_error_dialog import show_error_dialog


class AntyDetectBrowser:
    __init__ = init_app
    setup_page = setup_page
    setup_ui = setup_ui
    toggle_theme = toggle_theme
    on_nav_change = on_nav_change
    build_profiles_view = build_profiles_view
    build_proxies_view = build_proxies_view
    build_settings_view = build_settings_view
    refresh_profiles = refresh_profiles
    refresh_proxies = refresh_proxies
    refresh_current_view = refresh_current_view
    open_dialog = open_dialog
    parse_open_tabs = parse_open_tabs
    validate_open_tabs = validate_open_tabs
    build_profile_launch_settings = build_profile_launch_settings
    close_dialog = close_dialog
    run_ui = run_ui
    toggle_proxy_selection = toggle_proxy_selection
    toggle_select_all_proxies = toggle_select_all_proxies
    check_selected_proxies = check_selected_proxies
    show_create_profile_dialog = show_create_profile_dialog
    show_edit_profile_dialog = show_edit_profile_dialog
    show_create_proxy_dialog = show_create_proxy_dialog
    show_edit_proxy_dialog = show_edit_proxy_dialog
    toggle_profile = toggle_profile
    delete_profile = delete_profile
    delete_proxy = delete_proxy
    check_proxy = check_proxy
    check_proxy_with_playwright = check_proxy_with_playwright
    check_all_proxies = check_all_proxies
    parse_proxy_line = parse_proxy_line
    import_proxies_from_file = import_proxies_from_file
    show_import_proxy_dialog = show_import_proxy_dialog
    show_success_dialog = show_success_dialog
    show_error_dialog = show_error_dialog
