# chat_ui

This folder holds the built, static TanStack AI frontend that
`MainWindow.load_chat_ui()` points the embedded `QWebEngineView` at.

It is intentionally empty until the frontend is built. The desktop app
loads it as a local file (`file://.../chat_ui/index.html`) or from the
embedded local API server's static file route; no external web server is
required at runtime.

Build steps and the TanStack AI project source will be added in a later
implementation step.
