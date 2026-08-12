from pathlib import Path

import markdown

from django.conf import settings
from django.http import Http404
from django.shortcuts import render


DOC_PAGES = {
    "collectors": {
        "title": "Collectors",
        "filename": "collectors.md",
        "description": (
            "CPU, memory, disk, network and process "
            "data collection using psutil."
        ),
    },

    "monitoring": {
        "title": "Monitoring",
        "filename": "monitoring.md",
        "description": (
            "Sampling, rate calculations, state, "
            "rolling history and timing."
        ),
    },

    "architecture": {
        "title": "Architecture",
        "filename": "architecture.md",
        "description": (
            "System layers, module boundaries and "
            "end-to-end data flow."
        ),
    },

    "api": {
        "title": "API",
        "filename": "api.md",
        "description": (
            "The current Django monitoring API and "
            "JSON response structure."
        ),
    },

    "frontend": {
        "title": "Frontend",
        "filename": "frontend.md",
        "description": (
            "Django templates, JavaScript, polling, "
            "DOM updates and Chart.js."
        ),
    },

    "concepts": {
        "title": "Concepts",
        "filename": "concepts.md",
        "description": (
            "Quick reference for the computer science "
            "and programming concepts learned so far."
        ),
    },
}


def get_navigation():
    return [
        {
            "slug": slug,
            **page,
        }
        for slug, page in DOC_PAGES.items()
    ]


def docs_index(request):
    return render(
        request,
        "documentation/index.html",
        {
            "docs_pages": get_navigation(),
        },
    )


def docs_page(request, slug):
    page = DOC_PAGES.get(slug)

    if page is None:
        raise Http404("Documentation page not found.")

    docs_path = Path(settings.DOCS_DIR)
    markdown_path = docs_path / page["filename"]

    if not markdown_path.is_file():
        raise Http404(
            f"Documentation file '{page['filename']}' was not found."
        )

    markdown_text = markdown_path.read_text(
        encoding="utf-8"
    )

    renderer = markdown.Markdown(
        extensions=[
            "extra",
            "toc",
            "sane_lists",
        ]
    )

    content_html = renderer.convert(
        markdown_text
    )

    return render(
        request,
        "documentation/page.html",
        {
            "page": {
                "slug": slug,
                **page,
            },

            "docs_pages": get_navigation(),

            "content_html": content_html,

            "toc_html": renderer.toc,
        },
    )