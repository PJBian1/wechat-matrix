"""Markdown → 微信兼容 HTML 转换器"""

from markdown_it import MarkdownIt

# 微信图文内联样式
STYLES = {
    "h1": "font-size:22px;font-weight:bold;color:#333;margin:24px 0 16px;",
    "h2": "font-size:20px;font-weight:bold;color:#333;margin:20px 0 12px;",
    "h3": "font-size:18px;font-weight:bold;color:#333;margin:16px 0 10px;",
    "p": "font-size:16px;color:#333;line-height:1.8;margin:0 0 16px;",
    "blockquote": "border-left:3px solid #e0e0e0;padding:8px 16px;margin:16px 0;color:#666;background:#f9f9f9;",
    "code": "background:#f5f5f5;padding:2px 6px;border-radius:3px;font-size:14px;color:#c7254e;",
    "pre": "background:#f5f5f5;padding:16px;border-radius:4px;overflow-x:auto;margin:16px 0;",
    "img": "max-width:100%;height:auto;margin:12px 0;",
    "ul": "padding-left:28px;margin:12px 0;",
    "ol": "padding-left:28px;margin:12px 0;",
    "li": "font-size:16px;color:#333;line-height:1.8;margin:4px 0;",
    "strong": "font-weight:bold;color:#333;",
    "em": "font-style:italic;",
    "a": "color:#576b95;text-decoration:none;",
    "hr": "border:none;border-top:1px solid #e0e0e0;margin:24px 0;",
    "table": "width:100%;border-collapse:collapse;margin:16px 0;font-size:14px;",
    "th": "border:1px solid #ddd;padding:8px 12px;background:#f5f5f5;font-weight:bold;text-align:left;",
    "td": "border:1px solid #ddd;padding:8px 12px;",
}


def md_to_wechat_html(markdown_text: str) -> str:
    """将 Markdown 转换为微信兼容的内联样式 HTML"""
    md = MarkdownIt("commonmark", {"html": True}).enable("table")
    html = md.render(markdown_text)

    # 注入内联样式
    for tag, style in STYLES.items():
        # 自闭合标签
        if tag in ("img", "hr"):
            html = html.replace(f"<{tag}", f'<{tag} style="{style}"')
        else:
            html = html.replace(f"<{tag}>", f'<{tag} style="{style}">')
            html = html.replace(f"<{tag} ", f'<{tag} style="{style}" ')

    return html
