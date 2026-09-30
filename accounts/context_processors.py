from .navigation import build_quick_links


def quick_links(request):
    """Expose the dashboard sidebar quick links to every template."""
    return {'quick_links': build_quick_links(request.user)}
