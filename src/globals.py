import os

import supervisely as sly
from supervisely.collection.str_enum import StrEnum
from dotenv import load_dotenv

if sly.is_development():
    load_dotenv("local.env")
    load_dotenv(os.path.expanduser("~/supervisely.env"))

api = sly.Api()

TEAM_ID = sly.env.team_id()
WORKSPACE_ID = sly.env.workspace_id()
PROJECT_ID = sly.env.project_id()

PROJECT_INFO = api.project.get_info_by_id(id=PROJECT_ID)
PROJECT_META = sly.ProjectMeta.from_json(data=api.project.get_meta(PROJECT_ID))

DATASETS_INFO = {}

SELECTED_DATASETS_IDS = set()


class SplitMethod(StrEnum):
    BY_PARTS = "by_parts"
    BY_ITEMS_COUNT = "by_items_count"
    BY_PERCENT = "by_percent"
    BY_RATIO = "by_ratio"
