# styles.py  ← put this in your project and import from it

PURPLE_TABLE_STYLE = {
    "style_header": {
        "backgroundColor": "#59058d",
        "color": "#EEEDFE",
        "fontWeight": "500",
        "fontSize": "13px",
        "padding": "10px 14px",
        "textAlign": "left",
        "border": "none",
    },
    "style_cell": {
        "padding": "10px 14px",
        "fontSize": "14px",
        "textAlign": "left",
        "borderBottom": "0.5px solid #e0e0e0",
        "color": "#1a1a1a",
        "backgroundColor": "white",
        "whiteSpace": "normal",
        "height": "auto",
        "wordWrap": "break-word",
        "maxWidth": "300px",
    },
    "style_data_conditional": [
        {
            "if": {"row_index": "odd"},
            "backgroundColor": "#f9f9f9",
        }
    ],
}

STATUS_BADGE_STYLE = {
    "Approved":  {"background": "#EAF3DE", "color": "#3B6D11"},
    "Pending":   {"background": "#FAEEDA", "color": "#854F0B"},
    "Rejected":  {"background": "#FCEBEB", "color": "#A32D2D"},
    "In Review": {"background": "#E6F1FB", "color": "#185FA5"},
}
