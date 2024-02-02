import supervisely as sly
from supervisely.app.widgets import Button, Progress, ProjectThumbnail, Container
import src.globals as g
import src.ui as ui
from src.split import split


start_button = Button("Start", icon="zmdi zmdi-play")
progress_bar = Progress()
result_project = ProjectThumbnail(g.PROJECT_INFO)
result_project.hide()


@start_button.click
def start_progress():
    if len(g.SELECTED_DATASETS_IDS) == 0:
        sly.app.show_dialog(
            title="Nothing to split",
            description="Please, select at least one dataset.",
            status="warning"
        )
        return
    datasets = [g.DATASETS_INFO[id] for id in g.SELECTED_DATASETS_IDS]
    total_items = sum([dataset.items_count for dataset in datasets])
    settings = ui.get_settings()
    if not validate_settings(settings):
        return
    project_info = g.PROJECT_INFO
    with progress_bar(message="Processing items...", total=total_items) as pbar:
        dest_project = split(g.api, project_info, datasets, settings, pbar)

    result_project.set(dest_project)
    result_project.show()
    ui.update_table()


def validate_settings(settings: dict):
    try:
        destination = settings["destination"]
        if destination["new"]:
            if destination["workspace_id"] is None:
                sly.app.show_dialog(
                    title="Select workspace",
                    description="Please, select workspace to save new project.",
                    status="warning"
                )
                return False
            if destination["project_name"] is None or destination["project_name"] == "":
                sly.app.show_dialog(
                    title="Enter project name",
                    description="Please, enter name for new project.",
                    status="warning"
                )
                return False
        else:
            if destination["project_id"] is None:
                sly.app.show_dialog(
                    title="Select project",
                    description="Please, select project to save new datasets.",
                    status="warning"
                )
                return False
        split = settings["split"]
        if split["method"] not in g.SplitMethod.values():
            return False
        if len(split["parameters"]) == 0:
            sly.app.show_dialog(
                title="Nothing to split",
                description="Please, set split parameters.",
                status="warning"
            )
            return False
        for p in split["parameters"]:
            if p is None or p <= 0:
                sly.app.show_dialog(
                    title="Nothing to split",
                    description="Please, set split parameters to positive numbers more than 0.",
                    status="warning"
                )
                return False
    except Exception:
        return False
    return True


start = Container(
    widgets=[start_button, progress_bar, result_project],
    direction="vertical",
)
