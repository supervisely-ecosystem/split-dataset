from supervisely.app.widgets import (
    Card,
    Container,
    Select,
    InputNumber,
    OneOf,
    Container,
    SelectProject,
    Input,
    Empty,
    Field,
)
from supervisely import ProjectType
import globals as g
from dataset_selector import selected_datasets


settings_by_percent = Field(
    InputNumber(min=1, max=100, step=1),
    title="Input percent:",
    description="Dataset will be splitted to parts with given percent of parent elements",
)

settings_by_items_count = Field(
    InputNumber(min=1, max=100_000_000_000, step=1),
    title="Input items number:",
    description="Dataset will be splitted to datasets with given number of elements",
)

settings_by_parts = Field(
    InputNumber(min=1, max=1_000_000_000, step=1),
    title="Input parts:",
    description="Dataset will be splitted equaly to given number of parts",
)

settings_by_ratio = Field(
    Input(placeholder="20:80"),
    title="Input ratio:",
    description="Dataset sill be splitted to parts, corresponding to given ratio. E.g. dataset with 200 elements and given ratio of 15:25:60 will be splitted to 3 parts with 30, 50 and 120 elements correspondingly",
)

settings = {
    str(g.SplitMethod.BY_PERCENT): (
        str(g.SplitMethod.BY_PERCENT),
        "by percent",
        settings_by_percent,
    ),
    str(g.SplitMethod.BY_ITEMS_COUNT): (
        str(g.SplitMethod.BY_ITEMS_COUNT),
        "by items count",
        settings_by_items_count,
    ),
    str(g.SplitMethod.BY_PARTS): (
        str(g.SplitMethod.BY_PARTS),
        "by parts",
        settings_by_parts,
    ),
    str(g.SplitMethod.BY_RATIO): (
        str(g.SplitMethod.BY_RATIO),
        "by ratio",
        settings_by_ratio,
    ),
}
select_method_options = Select(items=[Select.Item(*s) for s in settings.values()])
select_method = Field(select_method_options, title="How to split dataset:")
selected_settings = OneOf(select_method_options)

new_project_name_input = Input()
new_project = Field(new_project_name_input, title="Project Name")

existing_project = SelectProject(
    default_id=g.PROJECT_ID, allowed_types=[ProjectType(g.PROJECT_INFO.type)]
)

select_project_options = Select(
    items=[
        Select.Item("in_current_project", "in current project", Empty()),
        Select.Item("in_new_project", "in new project", new_project),
        Select.Item("in_existing_project", "in existing project", existing_project),
    ]
)
select_project = Field(select_project_options, title="Where to save new datasets:")
selected_project = OneOf(select_project_options)

settings_card = Card(
    title="3️⃣ Settings",
    description=f"Split settings",
    content=Container(
        widgets=[
            selected_datasets,
            Container(
                widgets=[
                    select_method,
                    selected_settings,
                ],
                gap=10,
            ),
            Container(
                widgets=[
                    select_project,
                    selected_project,
                ],
                gap=10,
            ),
        ],
        direction="vertical",
        gap=20,
    ),
)


def get_settings():
    save_project = select_project_options.get_value()
    new = save_project == "in_new_project"
    project_id = None
    team_id = None
    workspace_id = None
    project_name = None
    if new:
        workspace_id = g.WORKSPACE_ID
        project_name = new_project_name_input.get_value()
    elif save_project == "in_current_project":
        project_id = g.PROJECT_ID
    elif save_project == "in_existing_project":
        project_id = existing_project.get_selected_id()

    method = select_method_options.get_value()
    if method == str(g.SplitMethod.BY_RATIO):
        parameters = [int(x) for x in settings[method][2]._content.get_value().split(":")]
    else:
        parameters = [int(settings[method][2]._content.get_value())]
    return {
        "destination": {
            "new": new,
            "project_id": project_id,
            "team_id": team_id,
            "workspace_id": workspace_id,
            "project_name": project_name,
        },
        "split": {
            "method": method,
            "parameters": parameters,
        },
    }
