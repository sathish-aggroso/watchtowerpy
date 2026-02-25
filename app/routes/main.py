from urllib.parse import urlparse

from flask import Blueprint, render_template, request, redirect, url_for, flash, session

from app.services import (
    HealthService,
    LinkService,
    ProjectService,
    CheckService,
    HistoryService,
)
from app.repositories import HistoryRepository
from app.utils import set_user_timezone

main_bp = Blueprint("main", __name__)


@main_bp.before_request
def before_request():
    tz = request.args.get("tz") or session.get("tz")
    if tz:
        set_user_timezone(tz)


@main_bp.route("/")
def index():
    project_filter = request.args.get("project", type=int)
    links = LinkService.get_all_links(project_filter)
    projects = ProjectService.get_all_projects()

    return render_template(
        "index.html",
        links=links,
        projects=projects,
        selected_project=project_filter,
        health=HealthService.get_status(),
    )


@main_bp.route("/status")
def status():
    return render_template("status.html", health=HealthService.get_status())


@main_bp.route("/add", methods=["POST"])
def add_link():
    url = request.form.get("url", "").strip()
    title = request.form.get("title", "").strip()
    project_id = request.form.get("project_id", type=int, default=1)
    tags = request.form.get("tags", "").strip()

    if not url:
        flash("URL is required", "error")
        return redirect(url_for("main.index"))

    parsed = urlparse(url)
    if not parsed.scheme:
        url = "https://" + url
        parsed = urlparse(url)

    if not parsed.scheme or not parsed.netloc:
        flash("Invalid URL format", "error")
        return redirect(url_for("main.index"))

    LinkService.create_link(url, title or url, project_id, tags)
    flash("Link added successfully", "success")
    return redirect(url_for("main.index"))


@main_bp.route("/delete/<int:link_id>")
def delete_link(link_id):
    LinkService.delete_link(link_id)
    flash("Link deleted", "success")
    return redirect(url_for("main.index"))


@main_bp.route("/check/<int:link_id>")
def check_link(link_id):
    result = CheckService.check_link_async(link_id)

    if result.get("task_id"):
        flash(
            "Scraping started. Wait a few seconds for completion. The page will update automatically.",
            "info",
        )
    elif result.get("success"):
        summary = result.get("summary", "")
        flash(f"Check completed - {summary}", "success")
    else:
        flash(f"Check failed: {result['error']}", "error")

    return redirect(url_for("main.view_link", link_id=link_id))


@main_bp.route("/link/<int:link_id>")
def view_link(link_id):
    link = LinkService.get_link(link_id)

    if not link:
        flash("Link not found", "error")
        return redirect(url_for("main.index"))

    from app.repositories import InitialPageRepository, DiffRepository

    initial = InitialPageRepository.get_by_link(link_id)
    diffs = DiffRepository.get_by_link(link_id, limit=10)

    return render_template(
        "link.html",
        link=link,
        history=diffs,
        initial=initial,
        health=HealthService.get_status(),
    )


@main_bp.route("/diff/<int:diff_id>")
def view_diff(diff_id):
    from app.repositories import InitialPageRepository, DiffRepository

    diff = DiffRepository.get_by_id(diff_id)

    if not diff or not diff.get("link_id"):
        flash("Diff entry not found", "error")
        return redirect(url_for("main.index"))

    link = LinkService.get_link(diff["link_id"])
    previous = DiffRepository.get_previous(diff_id)
    initial = InitialPageRepository.get_by_link(diff["link_id"])

    if not previous and initial:
        previous = initial

    from app.services.check_service import CheckService

    diff_content = diff.get("diff_content")
    html_diff = None
    paragraph_diff = None
    code_diff = None

    prev_full_content = previous.get("full_content", "") if previous else ""
    curr_full_content = diff.get("full_content", "")
    old_price = CheckService._extract_price(prev_full_content)
    new_price = CheckService._extract_price(curr_full_content)
    price_data = {"previous": old_price, "current": new_price}

    if previous:
        html_diff = CheckService._compute_html_diff(
            previous.get("full_content"), diff.get("full_content"), link.get("url")
        )
        from bs4 import BeautifulSoup

        old_soup = BeautifulSoup(previous.get("full_content", ""), "html.parser")
        new_soup = BeautifulSoup(diff.get("full_content", ""), "html.parser")
        old_body = old_soup.find("body")
        new_body = new_soup.find("body")
        if old_body and new_body:
            paragraph_diff = CheckService._generate_paragraph_diff(
                new_body, old_body, link.get("url")
            )
            code_diff = CheckService._generate_code_diff(
                diff.get("full_content"), previous.get("full_content")
            )

    return render_template(
        "diff.html",
        entry=diff,
        link=link,
        diff=diff_content,
        previous=previous,
        initial=initial,
        html_diff=html_diff,
        paragraph_diff=paragraph_diff,
        code_diff=code_diff,
        price_data=price_data,
        image_diff=None,
        current_screenshot=diff.get("screenshot"),
        previous_screenshot=previous.get("screenshot")
        if previous
        else (initial.get("screenshot") if initial else None),
        is_initial=False,
        health=HealthService.get_status(),
    )


@main_bp.route("/initial/<int:link_id>")
def view_initial(link_id):
    from app.repositories import InitialPageRepository

    initial = InitialPageRepository.get_by_link(link_id)

    if not initial:
        flash("Initial page not found", "error")
        return redirect(url_for("main.index"))

    link = LinkService.get_link(link_id)

    return render_template(
        "diff.html",
        entry=initial,
        link=link,
        diff=None,
        previous=None,
        initial=None,
        html_diff=None,
        paragraph_diff=None,
        code_diff=None,
        image_diff=None,
        current_screenshot=initial.get("screenshot"),
        previous_screenshot=None,
        is_initial=True,
        health=HealthService.get_status(),
    )


@main_bp.route("/project/add", methods=["POST"])
def add_project():
    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip()

    if not name:
        flash("Project name is required", "error")
        return redirect(url_for("main.index"))

    ProjectService.create_project(name, description)
    flash("Project created", "success")
    return redirect(url_for("main.index"))


@main_bp.route("/project/delete/<int:project_id>")
def delete_project(project_id):
    ProjectService.delete_project(project_id)
    flash("Project deleted", "success")
    return redirect(url_for("main.index"))


@main_bp.route("/set-timezone", methods=["POST"])
def set_timezone():
    tz = request.form.get("timezone", "UTC")
    session["tz"] = tz
    set_user_timezone(tz)
    return redirect(request.form.get("next") or url_for("main.index"))
