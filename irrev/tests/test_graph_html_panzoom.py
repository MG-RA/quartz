from irrev.commands.graph_cmd import _wrap_html


def test_graph_html_includes_panzoom_script() -> None:
    html = _wrap_html("<svg viewBox=\"0 0 10 10\"></svg>", title="t")
    assert "<svg" in html
    assert "Drag to pan" in html
    assert "wheel" in html

