import time


def update_statuses(page, app):
    while True:
        time.sleep(2)
        try:
            if page.window_alive:
                app.run_ui(app.refresh_profiles)
        except Exception:
            break
