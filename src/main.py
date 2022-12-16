import os
from dotenv import load_dotenv
import supervisely as sly
from supervisely.app.widgets import (
    Container,
    Card,
    Container,
    ProjectThumbnail,
)
from supervisely.app.widgets import ProjectThumbnail
import src.globals as g
import src.ui as ui


# for convenient debug, has no effect in production
if sly.utils.is_development():
    load_dotenv("local.env")
    load_dotenv(os.path.expanduser("~/supervisely.env"))

# input project
project_preview = ProjectThumbnail(g.PROJECT_INFO)
project_card = Card(title="1️⃣ Input project", description="", content=project_preview)

# select dataset
dataset_selector_card = ui.dataset_selector_card

# settings
settings_card = ui.settings_card

# start
start_container = ui.start

layout = Container(
    widgets=[project_card, dataset_selector_card, settings_card, start_container],
    direction="vertical",
    gap=15,
)

app = sly.Application(layout=layout)
ui.build_table()
