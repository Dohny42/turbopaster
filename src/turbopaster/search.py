"""Standalone Tkinter search window for snippet names."""

from collections.abc import Mapping


def filter_snippet_names(snippets: Mapping[str, str], query: str) -> list[str]:
    needle = query.casefold()
    return sorted(
        (name for name in snippets if needle in name.casefold()),
        key=str.casefold,
    )


def run_search_window(snippets: Mapping[str, str]) -> str | None:
    import tkinter as tk
    from tkinter import ttk

    background = "#171a21"
    surface = "#242a35"
    foreground = "#f1f5f9"
    muted = "#9aa4b2"
    accent = "#3b82f6"

    root = tk.Tk()
    root.title("TurboPaster")
    root.configure(background=background)
    root.geometry("600x360")
    root.minsize(420, 260)

    style = ttk.Style(root)
    if "clam" in style.theme_names():
        style.theme_use("clam")
    style.configure("TP.TFrame", background=background)
    style.configure(
        "TP.Title.TLabel",
        background=background,
        foreground=foreground,
        font=("Segoe UI", 17, "bold"),
    )
    style.configure(
        "TP.Hint.TLabel",
        background=background,
        foreground=muted,
        font=("Segoe UI", 9),
    )
    style.configure(
        "TP.Search.TEntry",
        fieldbackground=surface,
        foreground=foreground,
        insertcolor=foreground,
        padding=11,
        font=("Segoe UI", 13),
    )

    content = ttk.Frame(root, style="TP.TFrame", padding=24)
    content.pack(fill="both", expand=True)
    ttk.Label(content, text="TurboPaster", style="TP.Title.TLabel").pack(anchor="w")
    ttk.Label(
        content,
        text="Search your saved snippets",
        style="TP.Hint.TLabel",
    ).pack(anchor="w", pady=(3, 16))

    query = tk.StringVar(root)
    entry = ttk.Entry(content, textvariable=query, style="TP.Search.TEntry")
    entry.pack(fill="x", pady=(0, 12))

    results_frame = ttk.Frame(content, style="TP.TFrame")
    results_frame.pack(fill="both", expand=True)
    results = tk.Listbox(
        results_frame,
        background=surface,
        foreground=foreground,
        selectbackground=accent,
        selectforeground="#ffffff",
        activestyle="none",
        borderwidth=0,
        highlightthickness=0,
        font=("Segoe UI", 11),
        height=8,
    )
    results.pack(side="left", fill="both", expand=True)
    scrollbar = ttk.Scrollbar(results_frame, orient="vertical", command=results.yview)
    scrollbar.pack(side="right", fill="y")
    results.configure(yscrollcommand=scrollbar.set)

    status = tk.StringVar(root)
    ttk.Label(content, textvariable=status, style="TP.Hint.TLabel").pack(
        anchor="w",
        pady=(10, 0),
    )

    def refresh(*_args: str) -> None:
        names = filter_snippet_names(snippets, query.get())
        results.delete(0, tk.END)
        for name in names:
            results.insert(tk.END, name)
        if names:
            results.selection_set(0)
            results.activate(0)
            status.set(f"{len(names)} matching snippet(s)")
        else:
            status.set("No matching snippets")

    def move_selection(offset: int) -> str:
        last = results.size() - 1
        if last < 0:
            return "break"
        selection = results.curselection()
        current = selection[0] if selection else 0
        index = min(max(current + offset, 0), last)
        results.selection_clear(0, tk.END)
        results.selection_set(index)
        results.activate(index)
        results.see(index)
        return "break"

    selected: list[str] = []

    def choose() -> str:
        selection = results.curselection()
        if selection:
            selected.append(results.get(selection[0]))
            root.destroy()
        return "break"

    query.trace_add("write", refresh)
    root.bind("<Down>", lambda _event: move_selection(1))
    root.bind("<Up>", lambda _event: move_selection(-1))
    root.bind("<Return>", lambda _event: choose())
    root.bind("<Escape>", lambda _event: root.destroy())
    results.bind("<Double-Button-1>", lambda _event: choose())

    refresh()
    root.update_idletasks()
    x = (root.winfo_screenwidth() - root.winfo_width()) // 2
    y = (root.winfo_screenheight() - root.winfo_height()) // 2
    root.geometry(f"+{x}+{y}")
    entry.focus_set()
    root.mainloop()
    return selected[0] if selected else None
